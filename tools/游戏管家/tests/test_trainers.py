import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from library import Game,load_library,save_library
from trainers import merge_trainers,scan_trainers,ordered_games,tool_info,excluded
from steam_library import parse_vdf,read_steam_games
from app import filter_games

class TrainerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
    def test_old_config_and_new_fields(self):
        p=self.root/'old.json';p.write_text(json.dumps([{'id':'old','name':'before','tool_paths':[]}]))
        g=load_library(p)[0];self.assertFalse(g.favorite);self.assertEqual(g.aliases,[])
        g.english_name='Gunfire Reborn';g.aliases=['枪火'];g.favorite=True
        save_library(p,[g]);self.assertEqual(load_library(p),[g])
    def test_scan_exclusions_and_no_execution(self):
        (self.root/'Gunfire Reborn v1.0 Plus 8 Trainer.exe').write_text('')
        ce=self.root/'Cheat Engine';ce.mkdir();(ce/'fake Trainer.exe').write_text('')
        (self.root/'WeMod.exe').write_text('');(self.root/'random.exe').write_text('')
        (self.root/'修改器修复插件（安装完重启）.exe').write_text('')
        with patch('os.startfile',create=True) as opened:
            found,warnings=scan_trainers([self.root]);opened.assert_not_called()
        self.assertEqual(len(found),1);self.assertTrue(excluded('WeMod.lnk'))
    def test_merge_search_and_preservation(self):
        p=self.root/'Gunfire Reborn v1.0 Plus 8 Trainer.exe';p.write_text('')
        old=Game('old','Gunfire Reborn',tool_paths=[str(p)],save_dir='my-save',notes='my-note')
        games=merge_trainers([old],[p],[])
        self.assertEqual(len(games),1);g=games[0]
        self.assertEqual(g.name,'枪火重生');self.assertEqual(g.id,'old');self.assertEqual(g.save_dir,'my-save');self.assertEqual(g.notes,'my-note')
        self.assertEqual(filter_games(games,'gunfire'),games);self.assertEqual(filter_games(games,'枪火'),games)
        self.assertEqual(merge_trainers(games,[p],[]),games)
    def test_two_versions_and_preferred(self):
        a=self.root/'Hades v1.0 Plus 15 Trainer.exe';b=self.root/'Hades v1.2 Plus 15 Trainer.exe'
        for p in (a,b):p.write_text('')
        games=merge_trainers([],[a,b],[]);self.assertEqual(len(games),1)
        self.assertEqual(len(games[0].tool_paths),2);self.assertIn('v1.0',tool_info(a)['version'])
    def test_existing_chinese_card_keeps_id(self):
        p=self.root/'Hades v1.0 Trainer.exe';p.write_text('')
        old=Game('existing','哈迪斯',save_dir='my-save',notes='my-note')
        games=merge_trainers([old],[p],[])
        self.assertEqual(len(games),1);self.assertEqual(games[0].id,'existing');self.assertEqual(games[0].notes,'my-note')
    def test_favorites_recent_sort(self):
        a=Game('a','甲',last_used='2026-01-01');b=Game('b','乙',favorite=True);c=Game('c','丙',last_used='2026-02-01')
        self.assertEqual([g.id for g in ordered_games([a,b,c])],['b','c','a'])
    def test_steam_multilibrary_and_match(self):
        client=self.root/'Steam';other=self.root/'OtherLibrary'
        for folder in (client,other):(folder/'steamapps/common/Gunfire').mkdir(parents=True)
        def quote(path):return str(path).replace('\\','\\\\')
        (client/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "0" { "path" "'+quote(client)+'" } "1" { "path" "'+quote(other)+'" } }',encoding='utf-8')
        (other/'steamapps/appmanifest_1217060.acf').write_text('"AppState" {"appid" "1217060" "name" "Gunfire Reborn" "installdir" "Gunfire" "StateFlags" "4"}')
        apps,warnings=read_steam_games([client]);self.assertEqual(len(apps),1)
        p=self.root/'Gunfire Reborn v1.0 Trainer.exe';p.write_text('')
        g=merge_trainers([],[p],apps)[0];self.assertEqual(g.steam_appid,'1217060');self.assertEqual(g.steam_install,str(other/'steamapps/common/Gunfire'))
    def test_vdf_malformed_and_escapes(self):
        self.assertEqual(parse_vdf('"name" "a\\\"b" //comment')['name'],'a"b')
        with self.assertRaises(ValueError):parse_vdf('"a" { "b"')

if __name__=='__main__':unittest.main()
