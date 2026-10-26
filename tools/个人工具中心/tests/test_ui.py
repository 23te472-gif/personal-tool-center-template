import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from app import ToolCenter
from center import load_recent

class Manager:
    def open(self,key):return {'action':'focused','message':'已唤起窗口'}
    def poll(self):return {}

class UITests(unittest.TestCase):
    def test_town_tile_launches_external_and_poll_needs_no_card(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy)
            manager=Manager()
            with patch.object(manager,'open',return_value={'action':'started','message':'启动小镇'}) as opened:
                app=ToolCenter(root,Path(directory),manager=manager)
                opened.assert_not_called();self.assertNotIn('focus',app.fun_buttons)
                app.fun_buttons['town'].invoke();opened.assert_called_once_with('town')
            with patch.object(manager,'poll',return_value={'town':{'state':'running'}}):app.poll()
            self.assertIn('town',app.recent);self.assertNotIn('读取失败',app.status.get())
            with patch.object(app.playful,'close_all',return_value=True):app.close()
            self.assertIsNone(app.timer)
            # Closing the center has no process termination call.
            self._cleanups.pop()
    def test_active_cards_recent_and_folder(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy)
            base=Path(directory);(base/'data').mkdir()
            (base/'data/recent.json').write_text('{"files":"2026-10-22T10:00:00"}',encoding='utf-8')
            app=ToolCenter(root,base,manager=Manager())
            self.assertEqual(set(app.cards),{'games','delivery','status'})
            self.assertNotIn('个人资料工作台',app.summary.get());app.open_tool('games')
            self.assertIn('games',load_recent(base/'data/recent.json'))
            folder=app.tools[0].script.parent;folder.mkdir(exist_ok=True)
            with patch('app.os.startfile',create=True) as opened:app.open_folder('games');opened.assert_called_once_with(str(folder))
    def test_corrupt_recent_kept_and_tool_can_open(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            base=Path(directory);(base/'data').mkdir();p=base/'data/recent.json';p.write_text('{')
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy)
            app=ToolCenter(root,base,manager=Manager());app.open_tool('games')
            self.assertEqual(p.read_text(),'{');self.assertIn('未保存',app.status.get())

if __name__=='__main__':unittest.main()
