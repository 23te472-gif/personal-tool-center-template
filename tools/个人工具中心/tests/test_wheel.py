import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from wheel_model import candidates,draw,validate_wheel,default_wheel
from wheel_steam import import_installed

class WheelTests(unittest.TestCase):
    def test_filters_and_validation(self):
        entries=[dict(id=str(i),name=f'游戏{i}',appid='',enabled=True) for i in range(4)]
        self.assertEqual([x['id'] for x in candidates(entries,['0','1','2'],True)],['3'])
        entries[-1]['enabled']=False
        with self.assertRaises(ValueError):draw(entries,['0','1','2'],True)
        self.assertEqual(len(candidates(entries,[],False)),3)
        data=default_wheel();data['entries']=entries;validate_wheel(data)
        entries[0]['appid']='evil://command'
        with self.assertRaises(ValueError):validate_wheel(data)
    def test_import_local_manifests_chinese_and_existing_name(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            base=Path(folder);root=base/'Steam';apps=root/'steamapps';apps.mkdir(parents=True)
            (apps/'common/Test').mkdir(parents=True)
            (apps/'appmanifest_123.acf').write_text('"AppState" {"appid" "123" "name" "Test" "installdir" "Test"}',encoding='utf-8')
            (apps/'appmanifest_999.acf').write_text('{broken',encoding='utf-8')
            # Use a dedicated product base so this never touches the real game library.
            center=base/'个人工具中心';center.mkdir();data=base/'游戏管家/data';data.mkdir(parents=True)
            (data/'library.json').write_text(json.dumps([dict(name='中文游戏',steam_appid='123')]),encoding='utf-8')
            with patch('wheel_steam.steam_reader.detect_steam_roots',return_value=[root]):
                items,warnings=import_installed(center,[])
                self.assertEqual(items[0]['name'],'中文游戏');self.assertTrue(warnings)
                items[0]['name']='我改过的名字'
                again,_=import_installed(center,items)
                self.assertEqual(again[0]['name'],'我改过的名字');self.assertEqual(len(again),1)

if __name__=='__main__':unittest.main()
