from pathlib import Path
import json,sys,tempfile,time,unittest,zipfile
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import Bridge

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.old=self.root/'outputs';self.app=self.old/'个人工具中心新版';self.app.mkdir(parents=True)
        (self.old/'个人工具中心/data').mkdir(parents=True);(self.old/'游戏管家/data').mkdir(parents=True)
        self.bridge=Bridge(self.app,self.old,opener=Mock());self.addCleanup(self.bridge._shutdown)
    def call(self,action,payload=None):
        value=self.bridge.call(action,payload or {});self.assertTrue(value['ok'],value);return value['data']
    def test_unknown_actions_do_not_execute(self):
        self.assertEqual([name for name in dir(self.bridge) if not name.startswith('_')],['call'])
        self.assertFalse(self.bridge.call('__class__',{})['ok'])
        self.assertFalse(self.bridge.call('open_folder',{'kind':'C:/Windows'})['ok'])
        self.bridge._opener.assert_not_called()
    def test_missing_file_fails_without_false_completion(self):
        self.call('game_add',{'name':'游戏'})
        game=self.call('game_list')['games'][0]
        self.assertFalse(self.bridge.call('game_open',{'id':game['id'],'kind':'tool','tool_index':0})['ok'])
        self.assertFalse(self.bridge.call('materials_open',{'id':'thesis'})['ok'])
    def test_bootstrap_does_not_launch_and_preserves_legacy(self):
        data=self.call('bootstrap');self.assertEqual(data['app']['version'],'2.0.0')
        self.assertEqual(data['games'],[]);self.assertIn('town',[t['id'] for t in data['tools']])
        self.bridge._opener.assert_not_called()
    def test_migrated_tools_route_to_new_pages_without_spawning_legacy_windows(self):
        self.bridge._manager.open=Mock(side_effect=AssertionError('Old window must not launch'))
        for key,page in [('games','games'),('delivery','pack')]:
            result=self.call('launch_tool',{'id':key})
            self.assertEqual(result['action'],'internal');self.assertEqual(result['page'],page)
        self.bridge._manager.open.assert_not_called()
        self.assertNotIn('games',self.bridge._manager.tools);self.assertNotIn('delivery',self.bridge._manager.tools)
        tools={t['id']:t for t in self.call('bootstrap')['tools']}
        self.assertEqual(tools['games']['launch_mode'],'internal')
        self.assertEqual(tools['delivery']['launch_mode'],'internal')
    def test_missing_external_entry_is_explained_before_launch(self):
        tools={t['id']:t for t in self.call('bootstrap')['tools']}
        self.assertFalse(tools['agent']['available'])
        self.assertEqual(tools['agent']['status'],'failed')
        self.assertIn('入口文件',tools['agent']['message'])
        self.assertTrue(tools['games']['available'])
    def test_corrupt_legacy_never_overwritten(self):
        path=self.old/'游戏管家/data/library.json';path.write_text('{',encoding='utf-8')
        self.assertTrue(self.call('bootstrap')['warnings'])
        self.assertFalse(self.bridge.call('game_add',{'name':'测试'})['ok']);self.assertEqual(path.read_text(),'{')
    def test_games_changes_and_steam_validation(self):
        self.call('game_add',{'name':'深岩银河','english_name':'Deep Rock Galactic','steam_appid':'548430'})
        game=self.call('game_list')['games'][0]
        self.call('game_favorite',{'id':game['id'],'favorite':True})
        self.assertTrue(self.call('game_list')['games'][0]['favorite'])
        self.assertFalse(self.bridge.call('steam_open',{'appid':'../../cmd'})['ok'])
        self.assertFalse(self.bridge.call('steam_open',{'appid':'123'})['ok'])
        self.call('steam_open',{'appid':'548430'});self.bridge._opener.assert_called_once_with('steam://rungameid/548430')
    def test_game_recent_updates_only_after_successful_launch(self):
        self.call('game_add',{'name':'测试游戏','steam_appid':'548430'})
        self.bridge._opener.side_effect=OSError('启动失败')
        self.assertFalse(self.bridge.call('steam_open',{'appid':'548430'})['ok'])
        self.assertEqual(self.call('bootstrap')['recent'],[])
        self.bridge._opener.side_effect=None
        self.call('steam_open',{'appid':'548430'})
        self.assertEqual(self.call('bootstrap')['recent'][0]['name'],'测试游戏')
        self.assertTrue(self.call('game_list')['games'][0]['last_used'])
    def test_atomic_settings_and_validation(self):
        self.call('settings_save',{'theme':'dark','font_scale':1.15})
        self.assertEqual(self.call('bootstrap')['settings']['theme'],'dark')
        self.assertFalse(self.bridge.call('settings_save',{'theme':'<script>','font_scale':99})['ok'])
        p=self.app/'data/settings.json';p.write_text('{',encoding='utf-8')
        self.assertFalse(self.bridge.call('settings_save',{'theme':'light','font_scale':1})['ok']);self.assertEqual(p.read_text(),'{')
    def test_picker_cancel_and_known_file_enforcement(self):
        self.bridge._window=Mock();self.bridge._window.create_file_dialog.return_value=None
        self.assertTrue(self.call('pick_files')['cancelled'])
        f=self.root/'x.txt';f.write_text('hello')
        self.assertFalse(self.bridge.call('pack_start',{'files':[str(f)]})['ok'])
    def test_real_zip_async_and_duplicate_names(self):
        paths=[]
        for folder,content in (('a','first'),('b','second')):
            p=self.root/folder/'论文.txt';p.parent.mkdir();p.write_text(content,encoding='utf-8');paths.append(str(p))
        self.bridge._allowed_files.update(str(Path(p).resolve()) for p in paths)
        job=self.call('pack_start',{'files':paths})['job'];limit=time.monotonic()+5
        while time.monotonic()<limit:
            job=self.call('job_status',{'id':job['id']})['job']
            if job['status'] in ('completed','failed'):break
            time.sleep(.02)
        self.assertEqual(job['status'],'completed',job)
        with zipfile.ZipFile(job['result_path']) as archive:self.assertEqual(len(set(archive.namelist())),2);self.assertIsNone(archive.testzip())
    def test_wheel_draw_only_enabled_and_persistent_history(self):
        self.call('wheel_add',{'name':'测试游戏'})
        wheel=self.call('wheel_get')['wheel'];wheel['entries'][0]['enabled']=False
        self.call('wheel_save',{'wheel':wheel});self.assertFalse(self.bridge.call('wheel_draw',{})['ok'])
        wheel['entries'][0]['enabled']=True;self.call('wheel_save',{'wheel':wheel})
        result=self.call('wheel_draw');self.assertEqual(result['entry']['name'],'测试游戏');self.assertEqual(len(result['recent']),1)
    def test_draw_attaches_only_winner_icon_without_persisting_art(self):
        self.call('wheel_add',{'name':'测试游戏'})
        wheel=self.call('wheel_get')['wheel'];wheel['entries'][0]['appid']='548430'
        self.call('wheel_save',{'wheel':wheel})
        self.bridge._icons=Mock();self.bridge._icons.get.return_value='data:image/png;base64,dGVzdA=='
        result=self.call('wheel_draw')
        self.assertEqual(result['entry']['icon'],'data:image/png;base64,dGVzdA==')
        self.bridge._icons.get.assert_called_once_with('548430')
        self.assertNotIn('icon',self.call('wheel_get')['wheel']['entries'][0])
        self.bridge._opener.assert_not_called()
    def test_custom_draw_has_empty_icon(self):
        self.call('wheel_add',{'name':'随便玩点什么'})
        self.assertEqual(self.call('wheel_draw')['entry']['icon'],'')
    def test_reject_cheat_engine_and_bad_game_fields(self):
        self.assertFalse(self.bridge.call('game_add',{'name':'','steam_appid':'1'})['ok'])
        self.assertFalse(self.bridge.call('game_add',{'name':'test','steam_appid':'steam://bad'})['ok'])

if __name__=='__main__':unittest.main()
