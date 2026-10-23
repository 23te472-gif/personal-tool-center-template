from pathlib import Path
import sys,tempfile,unittest,json,ctypes
from ctypes import wintypes
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import backend
from integrated_windows import IntegratedWindows

class IntegratedWindowTests(unittest.TestCase):
    def test_console_title_cannot_impersonate_town_pid(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root=Path(folder);data=root/'宝可梦小镇新版/data';data.mkdir(parents=True)
            (data/'instance.json').write_text(json.dumps(dict(pid=123)),encoding='utf-8')
            windows=IntegratedWindows(root);windows.api=Mock()
            windows.api.FindWindowW.side_effect=lambda cls,title:80 if cls is None else None
            windows.api.IsWindow.return_value=True
            def owner(hwnd,pointer):ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD)).contents.value=777
            windows.api.GetWindowThreadProcessId.side_effect=owner
            self.assertIsNone(windows.find('宝可梦小镇与专注'))
            windows.api.GetWindowThreadProcessId.side_effect=lambda hwnd,pointer:setattr(ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD)).contents,'value',123)
            self.assertEqual(windows.find('宝可梦小镇与专注'),80)
            self.assertIsNone(windows.find('unrelated title'))
    def test_tools_have_one_unified_entry(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            bridge=backend.Bridge(Path(folder)/'outputs/个人工具中心新版',Path(folder)/'outputs',opener=Mock())
            self.addCleanup(bridge._shutdown)
            specs=bridge._tool_specs();self.assertNotIn('focus',[s.id for s in specs]);self.assertEqual(sum(s.id=='town' for s in specs),1)
            town=next(s for s in specs if s.id=='town');self.assertIn('宝可梦小镇新版',str(town.script))
