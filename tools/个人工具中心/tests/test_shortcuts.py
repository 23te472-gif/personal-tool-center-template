from pathlib import Path
from copy import deepcopy
import tempfile,unittest
from unittest.mock import patch
from shortcut_model import ShortcutService,ShortcutBackend,FIELDS

class FakeBackend:
    def __init__(self,desktop):self.desktop=desktop;self.values={};self.fail=False
    def desktop_dirs(self):return [self.desktop]
    def read(self,path):return deepcopy(self.values[str(path)])
    def read_many(self,paths):return [dict(path=str(path),**self.read(path)) for path in paths]
    def write_icon(self,path,icon):
        if self.fail:raise PermissionError('拒绝访问')
        self.values[str(path)]['icon']=icon;return self.read(path)

class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.desktop=self.base/'Desktop';self.desktop.mkdir();self.backend=FakeBackend(self.desktop)
        self.path=self.desktop/'软件.lnk';self.path.write_bytes(b'original shortcut bytes')
        self.props=dict(target=str(self.base/'软件.exe'),arguments='--keep',working_directory=str(self.base),window_style=1,hotkey='',description='说明',icon='original.exe,0')
        self.backend.values[str(self.path)]=dict(self.props)
        self.icon=self.base/'伙伴.ico';self.icon.write_bytes(b'\0\0\1\0\1\0test')
        self.service=ShortcutService(self.base,self.backend,asset_root=self.base/'short-icons')
    def test_stable_icon_cache_is_separate_from_deep_app_folder(self):
        service=ShortcutService(self.base/'deep/app',self.backend,asset_root=self.base/'short-icons')
        service.apply(self.path,self.icon,self.props)
        icon_path=Path(self.backend.read(self.path)['icon'].rsplit(',',1)[0])
        self.assertEqual(icon_path.parent,self.base/'short-icons')
        self.assertEqual(icon_path.read_bytes(),self.icon.read_bytes())
    def test_apply_copy_preserve_restore_and_conflict(self):
        found=self.service.scan();self.assertEqual(len(found),1)
        self.service.apply(self.path,self.icon,self.props)
        current=self.backend.read(self.path)
        self.assertTrue(Path(current['icon'].rsplit(',',1)[0]).is_file())
        self.assertEqual({k:v for k,v in current.items() if k!='icon'},{k:v for k,v in self.props.items() if k!='icon'})
        self.backend.values[str(self.path)]['description']='用户新的说明'
        self.service.restore(self.path)
        self.assertEqual(self.backend.read(self.path)['icon'],'original.exe,0')
        self.assertEqual(self.backend.read(self.path)['description'],'用户新的说明')
        self.service.apply(self.path,self.icon,self.backend.read(self.path))
        self.backend.values[str(self.path)]['icon']='manually changed.ico,0'
        with self.assertRaises(ValueError):self.service.restore(self.path)
    def test_no_nested_or_stale_and_failed_write_has_backup(self):
        self.backend.values[str(self.path)]['arguments']='changed'
        with self.assertRaises(ValueError):self.service.apply(self.path,self.icon,self.props)
        self.backend.values[str(self.path)]=dict(self.props)
        self.backend.fail=True
        with self.assertRaises(PermissionError):self.service.apply(self.path,self.icon,self.props)
        backups=list((self.base/'data/icon_studio/backups').glob('*.lnk'))
        self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),self.path.read_bytes())
        nested=self.desktop/'nested';nested.mkdir();other=nested/'bad.lnk';other.write_bytes(b'test')
        with self.assertRaises(ValueError):self.service.apply(other,self.icon,self.props)
    def test_repeated_apply_restores_first_icon(self):
        self.service.apply(self.path,self.icon,self.props)
        second=self.base/'second.ico';second.write_bytes(b'\0\0\1\0\1\0second')
        self.service.apply(self.path,second,self.backend.read(self.path));self.service.restore(self.path)
        self.assertEqual(self.backend.read(self.path)['icon'],self.props['icon'])
    def test_record_save_failure_rolls_back_and_preserves_backup(self):
        save=self.service.save;calls=[0]
        def fail_second(data):
            calls[0]+=1
            if calls[0]==2:raise OSError('写入操作记录失败')
            save(data)
        with patch.object(self.service,'save',side_effect=fail_second):
            with self.assertRaises(OSError):self.service.apply(self.path,self.icon,self.props)
        self.assertEqual(self.backend.read(self.path),self.props)
        self.assertEqual(len(list((self.service.root/'backups').glob('*.lnk'))),1)
        self.assertEqual(next(iter(self.service.records()['records'].values()))['state'],'restored')
    def test_corrupt_record_or_backup_copy_failure_never_changes_icon(self):
        with patch('shortcut_model.shutil.copy2',side_effect=PermissionError('备份失败')):
            with self.assertRaises(PermissionError):self.service.apply(self.path,self.icon,self.props)
        self.assertEqual(self.backend.read(self.path),self.props)
        self.service.root.mkdir(parents=True,exist_ok=True);self.service.path.write_text('{',encoding='utf-8')
        with self.assertRaises(ValueError):self.service.apply(self.path,self.icon,self.props)
        self.assertEqual(self.service.path.read_text(),'{');self.assertEqual(self.backend.read(self.path),self.props)
    def test_restore_all_keeps_conflict_and_restores_other(self):
        other=self.desktop/'另一个软件.lnk';other.write_bytes(b'other shortcut');self.backend.values[str(other)]=dict(self.props)
        self.service.apply(self.path,self.icon,self.props);self.service.apply(other,self.icon,self.props)
        self.backend.values[str(self.path)]['icon']='manual.ico,0'
        results=self.service.restore_all()
        self.assertEqual(sorted(x['status'] for x in results),['failed','restored'])
        self.assertEqual(self.backend.read(self.path)['icon'],'manual.ico,0');self.assertEqual(self.backend.read(other)['icon'],self.props['icon'])

if __name__=='__main__':unittest.main()
