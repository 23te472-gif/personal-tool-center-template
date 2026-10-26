"""Focus only a window owned by the recorded sibling process, never a matching console."""
from pathlib import Path
import ctypes,json,os
from ctypes import wintypes
import center

def agent_entry(root):
    return Path(os.environ.get('AGENT_WORKBENCH_ENTRY',str(Path(root).parent.parent/'agent-workbench/app.py'))).resolve()

class IntegratedWindows(center.WindowsWindows):
    def __init__(self,root):
        super().__init__();self.root=Path(root)
    def find(self,title,pid=None):
        found=super().find(title,pid)
        folders={'宝可梦小镇与专注':self.root/'宝可梦小镇新版','Agent 工作台':agent_entry(self.root).parent}
        if found or title not in folders or not self.api:return found
        try:
            value=json.loads((folders[title]/'data/instance.json').read_text(encoding='utf-8'))
            expected=value.get('pid')
            if type(expected) is not int or expected<=0 or (pid is not None and pid!=expected):return None
            hwnd=self.api.FindWindowW(None,title)
            if not hwnd or not self.api.IsWindow(hwnd):return None
            owner=wintypes.DWORD();self.api.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
            return hwnd if owner.value==expected else None
        except (OSError,ValueError,TypeError,AttributeError):return None
