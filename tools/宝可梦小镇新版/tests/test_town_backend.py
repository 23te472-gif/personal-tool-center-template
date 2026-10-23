from pathlib import Path
import sys,json,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from town_backend import Bridge

class TownTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.time=[0.0]
        self.bridge=Bridge(self.base,clock=lambda:self.time[0],today=lambda:'2026-10-23')
    def call(self,name,payload=None):
        result=self.bridge.call(name,payload);self.assertTrue(result['ok'],result);return result['data']
    def test_fresh_world_ignores_legacy(self):
        old=self.base/'outputs/个人工具中心/data/focus.json';old.parent.mkdir(parents=True);old.write_text('{"berries":999}',encoding='utf-8')
        fresh=Bridge(self.base/'outputs/宝可梦小镇新版',clock=lambda:self.time[0],today=lambda:'2026-10-23')
        data=fresh.call('bootstrap')['data'];self.assertEqual(data['town']['berries'],20);self.assertEqual(data['town']['origin'],'new')
        self.assertEqual(old.read_text(),'{"berries":999}')
        self.assertFalse(data['focus']['active']);self.assertEqual(len(data['town']['inventory']),2)
        self.assertEqual(data['settings']['mode'],'town');self.assertEqual(len(data['catalog']['partners']),20)
    def test_only_actions_exposed_no_frontend_reward(self):
        self.assertEqual([v for v in dir(self.bridge) if not v.startswith('_')],['call'])
        for action,payload in (('_opener',{}),('focus_complete',{}),('town_action',{'action':'focus_complete','args':{}}),('focus_start',{'minutes':True}),('bootstrap',[])):
            self.assertFalse(self.bridge.call(action,payload)['ok'])
        self.assertEqual(self.call('bootstrap')['town']['berries'],20)
    def test_shop_failure_does_not_spend_or_mutate(self):
        before=self.call('bootstrap')['town']
        with patch.object(self.bridge._repo,'save',side_effect=OSError('磁盘写入失败')):
            result=self.bridge.call('town_action',{'action':'buy','args':{'kind':'lamp'}})
        self.assertFalse(result['ok']);self.assertEqual(self.call('bootstrap')['town'],before)
        data=self.call('town_action',{'action':'buy','args':{'kind':'lamp'}})
        self.assertEqual(data['town']['berries'],14)
    def test_place_collision_and_recall(self):
        data=self.call('bootstrap');ids=list(data['town']['inventory'])
        self.call('town_action',{'action':'place','args':{'item_id':ids[0],'area':'home','x':7,'y':5}})
        self.assertFalse(self.bridge.call('town_action',{'action':'place','args':{'item_id':ids[1],'area':'home','x':7,'y':5}})['ok'])
        self.assertFalse(self.bridge.call('town_action',{'action':'place','args':{'item_id':ids[1],'area':'home','x':3,'y':2}})['ok'])
        data=self.call('town_action',{'action':'recall','args':{'item_id':ids[0]}})
        self.assertNotIn(ids[0],data['town']['placements']['home'])
    def test_daily_rewards_are_idempotent(self):
        self.call('town_action',{'action':'greet','args':{}})
        first=self.call('town_action',{'action':'claim','args':{'task':'greet'}})
        second=self.call('town_action',{'action':'claim','args':{'task':'greet'}})
        self.assertEqual(first['town']['berries'],22);self.assertEqual(second['town']['berries'],22)
    def test_focus_pause_resume_mode_and_early_end(self):
        self.call('focus_start',{'task':'阅读','minutes':5});self.time[0]=60
        data=self.call('set_mode',{'mode':'focus'});self.assertEqual(data['focus']['remaining'],240);self.assertTrue(data['focus']['running'])
        data=self.call('focus_pause');self.time[0]=200;self.assertEqual(self.call('focus_state')['focus']['remaining'],240)
        self.call('focus_resume');self.time[0]=230
        data=self.call('focus_end');self.assertEqual(data['town']['berries'],20);self.assertFalse(data['focus']['active'])
    def test_settlement_once_and_stats(self):
        self.call('focus_start',{'task':'专注','minutes':25});self.time[0]=1501
        first=self.call('focus_state');second=self.call('focus_state')
        self.assertEqual(first['town']['berries'],25);self.assertEqual(second['town']['berries'],25)
        self.assertEqual(first['town']['stats']['2026-10-23'],dict(sessions=1,minutes=25));self.assertFalse(first['focus']['running'])
    def test_failed_completion_save_is_retryable_without_double_award(self):
        self.call('focus_start',{'task':'专注','minutes':5});self.time[0]=301
        with patch.object(self.bridge._repo,'save',side_effect=OSError('暂时不可写')):
            result=self.bridge.call('focus_state')
        self.assertFalse(result['ok']);self.assertEqual(self.bridge._data['berries'],20)
        self.assertEqual(self.call('focus_state')['town']['berries'],21)
        self.assertEqual(self.call('focus_state')['town']['berries'],21)
    def test_close_pauses_and_reopen_does_not_auto_run(self):
        self.call('focus_start',{'task':'测试','minutes':5});self.time[0]=70
        self.bridge._pause_for_close();other=Bridge(self.base,clock=lambda:self.time[0],today=lambda:'2026-10-23')
        self.time[0]=200;value=other.call('bootstrap')['data']['focus'];self.assertEqual(value['remaining'],230);self.assertFalse(value['running']);self.assertTrue(value['active'])
    def test_close_at_deadline_settles(self):
        self.call('focus_start',{'task':'测试','minutes':5});self.time[0]=300
        self.bridge._pause_for_close();self.assertEqual(self.call('bootstrap')['town']['berries'],21)
    def test_deadline_crossed_during_pause_or_close_still_settles_once(self):
        for operation in ('pause','close'):
            with self.subTest(operation=operation):
                base=self.base/operation;bridge=Bridge(base,clock=lambda:0,today=lambda:'2026-10-23')
                bridge.call('focus_start',{'task':'测试','minutes':5})
                values=iter((299.99,299.99,300.01))
                clock=lambda:next(values,300.01)
                bridge._clock=clock;bridge._focus.clock=clock
                if operation=='pause':result=bridge.call('focus_pause');self.assertTrue(result['ok'])
                else:bridge._pause_for_close()
                value=bridge.call('focus_state')['data']
                self.assertFalse(value['focus']['active']);self.assertEqual(value['town']['berries'],21)
                self.assertEqual(bridge.call('focus_state')['data']['town']['berries'],21)
    def test_close_save_failure_keeps_running_clock_and_is_retryable(self):
        self.call('focus_start',{'task':'测试','minutes':5});self.time[0]=100
        with patch.object(self.bridge._repo,'save',side_effect=OSError('保存失败')):
            with self.assertRaises(OSError):self.bridge._pause_for_close()
        self.assertTrue(self.bridge._focus.running)
        self.time[0]=130;self.bridge._pause_for_close()
        self.assertEqual(self.call('bootstrap')['focus']['remaining'],170)
    def test_start_rejects_overwriting_paused_session(self):
        self.call('focus_start',{'task':'先做这件事','minutes':15});self.call('focus_pause')
        self.assertFalse(self.bridge.call('focus_start',{'task':'覆盖','minutes':5})['ok'])
        self.assertEqual(self.call('bootstrap')['focus']['task'],'先做这件事')
    def test_idle_poll_does_not_write(self):
        with patch.object(self.bridge._repo,'save') as save:
            self.call('focus_state');self.call('bootstrap');save.assert_not_called()
    def test_settings_validation_and_corrupt_save_preserved(self):
        self.assertFalse(self.bridge.call('settings_save',{'theme':'light','motion':'yes'})['ok'])
        self.call('settings_save',{'theme':'dark','motion':False});self.assertFalse(self.call('bootstrap')['settings']['motion'])
        path=self.base/'data/town.json';path.write_text('{',encoding='utf-8')
        with self.assertRaises(ValueError):Bridge(self.base)
        self.assertEqual(path.read_text(),'{')

if __name__=='__main__':unittest.main()
