import tempfile,time,unittest,subprocess,sys,threading
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from playful_tools import PlayfulTools

class PlayfulUITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.base=Path(self.temp.name)
        self.root=tk.Tk();self.root.withdraw();self.manager=PlayfulTools(self.root,self.base)
    def tearDown(self):
        self.root.update_idletasks();self.root.destroy();self.temp.cleanup()
    def test_lazy_import_on_center_import(self):
        result=subprocess.run([sys.executable,'-c',"import app,sys; assert all(x not in sys.modules for x in ('focus_ui','wheel_ui','shortcut_ui','PIL'))"],cwd=Path(__file__).parents[1],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
    def test_focus_reuse_close_pauses_and_failure_keeps_window(self):
        app=self.manager.open('focus');self.assertIs(app,self.manager.open('focus'))
        app.session.start('测试',5);app.session.deadline-=300;app.tick()
        self.assertEqual(app.session.berries,1);app.tick();self.assertEqual(app.session.berries,1)
        app.start();self.assertTrue(app.session.running)
        with patch('focus_ui.save_json',side_effect=OSError('磁盘不可写')):
            self.assertFalse(self.manager.close_all());self.assertTrue(app.window.winfo_exists())
        self.assertTrue(self.manager.close_all())
        from playful_store import load_json
        from focus_model import default_focus,validate_focus
        data=load_json(self.base/'data/focus.json',default_focus(),validate_focus);self.assertTrue(data['active']);self.assertGreater(data['remaining'],0)
    def test_wheel_result_only_launches_on_button_and_close_cancels(self):
        with patch('wheel_ui.import_installed') as imported,patch('wheel_ui.os.startfile',create=True) as launch:
            app=self.manager.open('wheel');imported.assert_not_called();launch.assert_not_called()
            app.data['entries']=[dict(id='steam-123',name='测试游戏',appid='123',enabled=True)]
            app.spin();self.assertTrue(app.busy)
            deadline=time.monotonic()+5
            while app.busy and time.monotonic()<deadline:self.root.update();time.sleep(.02)
            self.assertFalse(app.busy);self.assertEqual(app.result['name'],'测试游戏');launch.assert_not_called()
            app.launch();launch.assert_called_once_with('steam://rungameid/123')
            app.spin();self.assertTrue(app.timer);app.close();self.assertIsNone(app.timer)
    def test_icons_no_selection_no_apply_and_busy_prevents_center_close(self):
        with patch('shortcut_ui.ShortcutService') as service:
            service.return_value.scan.return_value=[]
            app=self.manager.open('icons');deadline=time.monotonic()+3
            while app.working and time.monotonic()<deadline:self.root.update();time.sleep(.01)
            service.return_value.apply.assert_not_called()
            app.busy=True;self.assertFalse(self.manager.close_all());self.assertTrue(app.window.winfo_exists())
            app.busy=False;self.assertTrue(self.manager.close_all())
    def test_icon_preview_follows_latest_selection(self):
        first_started=threading.Event();release=threading.Event();paths=[]
        def image(item,size):
            path=item['path']
            paths.append(path)
            if len(paths)==1:first_started.set();release.wait(3)
            return None
        with patch('shortcut_ui.ShortcutService') as service,patch('shortcut_ui.CardImages'),patch('win_icons.shortcut_image',side_effect=image):
            service.return_value.scan.return_value=[dict(path='C:/fake/A.lnk'),dict(path='C:/fake/B.lnk')]
            app=self.manager.open('icons');deadline=time.monotonic()+3
            while app.working and time.monotonic()<deadline:self.root.update();time.sleep(.01)
            app.cards.select('C:/fake/A.lnk');self.root.update()
            self.assertTrue(first_started.wait(1))
            app.cards.select('C:/fake/B.lnk');self.root.update();release.set()
            deadline=time.monotonic()+4
            while app.working and time.monotonic()<deadline:self.root.update();time.sleep(.01)
            self.assertEqual(app.selected()['path'],'C:/fake/B.lnk')
            self.assertTrue(app.detail.get().startswith('B\n'),app.detail.get())
            self.assertEqual(paths[-1],'C:/fake/B.lnk')
            service.return_value.apply.assert_not_called()

if __name__=='__main__':unittest.main()
