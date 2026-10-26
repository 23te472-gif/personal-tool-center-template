import sys,unittest,ctypes
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import legacy_runner

class DisplayTests(unittest.TestCase):
    def test_system_dpi_before_tk(self):
        api=Mock();api.shcore.SetProcessDpiAwareness.return_value=0
        legacy_runner.enable_dpi(api)
        api.shcore.SetProcessDpiAwareness.assert_called_once_with(1)
        api.user32.SetProcessDPIAware.assert_not_called()
    def test_missing_new_api_uses_older_windows_api(self):
        api=Mock();api.shcore.SetProcessDpiAwareness.side_effect=AttributeError('unavailable')
        legacy_runner.enable_dpi(api)
        api.user32.SetProcessDPIAware.assert_called_once_with()
    def test_native_awareness_and_chinese_fonts(self):
        legacy_runner.enable_dpi()
        current=ctypes.c_int()
        result=ctypes.windll.shcore.GetProcessDpiAwareness(None,ctypes.byref(current))
        self.assertEqual(result,0);self.assertGreaterEqual(current.value,1)
        import tkinter as tk
        from tkinter import font,ttk
        root=tk.Tk();root.withdraw()
        try:
            legacy_runner.configure_fonts(root)
            self.assertEqual(font.nametofont('TkDefaultFont',root=root).actual('family'),'Microsoft YaHei UI')
            self.assertEqual(font.nametofont('TkDefaultFont',root=root).actual('size'),11)
            label=ttk.Label(root,text='桌面软件 伙伴素材');label.pack();root.update_idletasks()
            self.assertGreater(label.winfo_reqheight(),15)
        finally:root.destroy()

if __name__=='__main__':unittest.main()
