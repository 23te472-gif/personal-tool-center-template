import unittest
import tempfile
import json
import zipfile
from pathlib import Path
from unittest.mock import patch
from library import Game, load_library, save_library
from discovery import scan_candidates
from actions import open_path
from snapshots import create_backup, export_backup, list_backups

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_library_roundtrip_and_delete(self):
        p = self.root/'中文 文件.json'
        external = self.root/'游戏.exe'; external.write_text('keep')
        g = Game('a', '游戏', str(external), ['甲.lnk','乙.exe'], '', '备注')
        save_library(p, [g]); self.assertEqual(load_library(p), [g])
        save_library(p, []); self.assertTrue(external.exists())

    def test_corrupt_and_duplicate(self):
        p=self.root/'library.json'; p.write_text('{')
        with self.assertRaises(ValueError): load_library(p)
        g=Game('a','名字','','','','')
        with self.assertRaises(ValueError): save_library(p,[g,g])
        self.assertEqual(p.read_text(),'{')

    def test_atomic_failure(self):
        p=self.root/'library.json'; save_library(p,[]); before=p.read_bytes()
        with patch('library.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError): save_library(p,[])
        self.assertEqual(before,p.read_bytes())

    def test_scan_preserves_sources(self):
        a=self.root/'a'; b=self.root/'b'; a.mkdir(); b.mkdir()
        for d in (a,b): (d/'Hades Plus 15 Trainer.exe').write_text('')
        with patch('os.startfile',create=True) as start:
            found=scan_candidates([a,b]); start.assert_not_called()
        self.assertEqual(len(found),2)
        self.assertTrue(all(c.kind=='工具' for c in found))
        with self.assertRaises(FileNotFoundError): scan_candidates([self.root/'missing'])

    def test_missing_launch(self):
        with self.assertRaises(FileNotFoundError): open_path(self.root/'absent')

    def test_backup_export_and_unique(self):
        src=self.root/'存档'; src.mkdir(); (src/'中文.txt').write_text('进度')
        backups=self.root/'backups'
        a=create_backup(src,backups,'game',lambda x:None)
        b=create_backup(src,backups,'game',lambda x:None)
        self.assertNotEqual(a,b); self.assertEqual(len(list_backups(backups,'game')),2)
        target=self.root/'export'; export_backup(a,target)
        self.assertEqual((target/'中文.txt').read_text(),'进度')
        with self.assertRaises(ValueError): export_backup(b,target)

    def test_overlap_and_bad_id(self):
        src=self.root/'save'; src.mkdir()
        for backup in (src,src/'backups',self.root):
            with self.assertRaises(ValueError): create_backup(src,backup,'game',print)
        with self.assertRaises(ValueError): create_backup(src,self.root/'b','../escape',print)

    def test_write_failure_cleanup(self):
        src=self.root/'save'; src.mkdir(); (src/'a').write_text('x')
        with patch('snapshots.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError): create_backup(src,self.root/'b','game',print)
        self.assertEqual(list((self.root/'b').rglob('*.zip')),[])
        self.assertEqual(list((self.root/'b').rglob('*.tmp')),[])

    def test_unsafe_archives(self):
        for i,name in enumerate(('../escape','/absolute','C:/drive','a/../../escape','a\\..\\escape')):
            p=self.root/f'{i}.zip'
            with zipfile.ZipFile(p,'w') as z: z.writestr(name,'bad')
            with self.assertRaises(ValueError): export_backup(p,self.root/f'out{i}')

    def test_source_changes(self):
        src=self.root/'save'; src.mkdir(); p=src/'a'; p.write_text('x')
        def changed(message): p.write_text('changed')
        with self.assertRaises(OSError): create_backup(src,self.root/'b','game',changed)
        self.assertEqual(list((self.root/'b').rglob('*.zip')),[])

    def test_root_link_rejected_before_resolve(self):
        src=self.root/'save'; src.mkdir()
        relative=src.relative_to(Path.cwd())
        with patch('snapshots.is_link',side_effect=lambda p: p==relative):
            with self.assertRaises(ValueError): create_backup(relative,self.root/'b','game',lambda _:None)

    def test_walk_error_is_failure(self):
        src=self.root/'save'; src.mkdir()
        def broken_walk(*args,**kwargs):
            if kwargs.get('onerror'): kwargs['onerror'](PermissionError('unreadable'))
            return iter([])
        with patch('snapshots.os.walk',side_effect=broken_walk):
            with self.assertRaises(PermissionError):create_backup(src,self.root/'b','game',lambda _:None)

    def test_late_change_and_new_file(self):
        for mode in ('late','new'):
            src=self.root/mode; src.mkdir(); (src/'a').write_text('first'); (src/'b').write_text('second')
            calls=[]
            def progress(message):
                calls.append(message)
                if len(calls)==2:
                    if mode=='late':(src/'a').write_text('modified')
                    else:(src/'new').write_text('new')
            with self.assertRaises(OSError): create_backup(src,self.root/'backups','game',progress)

    def test_zip_symlink_and_checksum_cleanup(self):
        p=self.root/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:
            info=zipfile.ZipInfo('files/link'); info.create_system=3; info.external_attr=(0o120777<<16)
            z.writestr(info,'target'); z.writestr('manifest.json','{}')
        with self.assertRaises(ValueError): export_backup(p,self.root/'out')
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('files/a','wrong'); z.writestr('manifest.json',json.dumps({'a':{'size':5,'sha256':'bad'}}))
        with self.assertRaises(ValueError): export_backup(p,self.root/'out')
        self.assertEqual(list((self.root/'out').rglob('*')),[])

if __name__=='__main__': unittest.main()
