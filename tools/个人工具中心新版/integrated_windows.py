"""Recognize the new WebView tool only when its authenticated instance PID owns it."""
from pathlib import Path
import ctypes,json
from ctypes import wintypes
import center

class IntegratedWindows(center.WindowsWindows):
    def __init__(self,root):
        super().__init__();self.root=Path(root)
    def find(self,title,pid=None):
        found=super().find(title,pid)
        if found or title!='宝可梦小镇与专注' or not self.api:return found
        try:
            value=json.loads((self.root/'宝可梦小镇新版/data/instance.json').read_text(encoding='utf-8'))
            expected=value.get('pid')
            if type(expected) is not int or expected<=0 or (pid is not None and pid!=expected):return None
            hwnd=self.api.FindWindowW(None,title)
            if not hwnd or not self.api.IsWindow(hwnd):return None
            owner=wintypes.DWORD();self.api.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
            return hwnd if owner.value==expected else None
        except (OSError,ValueError,TypeError,AttributeError):return None
