"""Independent local tool launch and window activation, without shared app imports."""
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import ctypes
from ctypes import wintypes
import json,os,subprocess,sys,tempfile,uuid

@dataclass(frozen=True)
class Tool:
    id:str
    name:str
    description:str
    script:Path
    title:str
    color:str
    symbol:str

def tools_for(base):
    parent=Path(base).resolve().parent
    return [
        Tool('games','游戏管家','中文查找修改器，管理常用版本与游戏存档。',parent/'游戏管家/app.py','游戏管家 · 修改器管理','#6c56a5','游'),
        Tool('delivery','快速文件打包','选择几个文件，直接生成 ZIP；支持再次打包上次文件。',parent/'论文交付助手/app.py','论文交付助手 · 快速打包','#347a71','包'),
        Tool('town','宝可梦小镇','布置家园、和伙伴互动，顺手专注赚树果。',parent/'宝可梦小镇/app.py','宝可梦小镇','#66845d','镇'),
        Tool('status','桌面状态卡片','CPU、内存、网速与磁盘空间；Ctrl＋Alt＋F9 打开，关卡片即停止采样。',parent/'桌面状态卡片/HotkeyLauncher.exe','桌面状态卡片','#337b77','状'),
    ]

def load_recent(path):
    path=Path(path)
    if not path.exists():return {}
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in value.items()):raise ValueError('最近使用记录格式错误')
        return value
    except json.JSONDecodeError as exc:raise ValueError('最近使用记录损坏，原文件保持不变') from exc

def save_recent(path,records):
    if not isinstance(records,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in records.items()):raise ValueError('最近使用记录格式错误')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(records,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:Path(temporary).unlink(missing_ok=True)

class WindowsWindows:
    def __init__(self):
        self.api=ctypes.WinDLL('user32',use_last_error=True) if os.name=='nt' else None
        if self.api:
            self.api.FindWindowW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR];self.api.FindWindowW.restype=wintypes.HWND
            self.api.IsWindow.argtypes=[wintypes.HWND];self.api.IsWindow.restype=wintypes.BOOL
            self.api.IsWindowVisible.argtypes=[wintypes.HWND];self.api.IsWindowVisible.restype=wintypes.BOOL
            self.api.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];self.api.ShowWindow.restype=wintypes.BOOL
            self.api.SetForegroundWindow.argtypes=[wintypes.HWND];self.api.SetForegroundWindow.restype=wintypes.BOOL
            self.api.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)];self.api.GetWindowThreadProcessId.restype=wintypes.DWORD
    def find(self,title,pid=None):
        if not self.api:return None
        hwnd=self.api.FindWindowW('TkTopLevel',title) or self.api.FindWindowW('CodexDesktopStatusCardNative',title)
        if hwnd and self.api.IsWindow(hwnd):
            owner=wintypes.DWORD();self.api.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
            if pid is None or owner.value==pid:return hwnd
        return None
    def focus(self,hwnd):
        if not self.api or not self.api.IsWindow(hwnd):return False
        self.api.ShowWindow(hwnd,9)
        return bool(self.api.SetForegroundWindow(hwnd))

class ToolManager:
    def __init__(self,base,tools=None,windows=None,spawn=None):
        self.base=Path(base);self.tools={t.id:t for t in (tools or tools_for(base))}
        self.windows=windows or WindowsWindows();self.spawn=spawn or subprocess.Popen
        self.processes={};self.logs={};self.finished={}
    def open(self,tool_id):
        tool=self.tools[tool_id]
        hwnd=self.windows.find(tool.title)
        if hwnd:
            focused=self.windows.focus(hwnd)
            return {'action':'focused','message':'已唤起窗口' if focused else '窗口已打开，请从任务栏选择；未重复启动'}
        process=self.processes.get(tool_id)
        if process is not None and process.poll() is None:return {'action':'pending','message':'正在启动，请稍候；未重复启动'}
        if not tool.script.is_file():raise FileNotFoundError(f'找不到工具入口：{tool.script}\n请保留工具中心与各个工具的相邻目录结构。')
        log_dir=self.base/'logs';log_dir.mkdir(parents=True,exist_ok=True)
        log=log_dir/(tool.id+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.log')
        with log.open('wb') as stream:
            argv=[str(tool.script)] if tool.script.suffix.lower()=='.exe' else [sys.executable,str(tool.script)]
            process=self.spawn(argv,cwd=str(tool.script.parent),stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.processes[tool_id]=process;self.logs[tool_id]=log
        self.finished.pop(tool_id,None)
        return {'action':'started','message':'正在启动 '+tool.name}
    def poll(self):
        states={}
        for key,tool in self.tools.items():
            process=self.processes.get(key)
            hwnd=self.windows.find(tool.title)
            if hwnd:states[key]={'state':'running','message':'窗口已打开'}
            elif process is None:states[key]=self.finished.get(key,{'state':'idle','message':'尚未打开'})
            elif process.poll() is None:states[key]={'state':'starting','message':'启动中，请稍候'}
            elif process.poll()==0:
                states[key]={'state':'exited','message':'已关闭'};self.finished[key]=states[key];self.processes.pop(key,None)
            else:
                log=self.logs[key]
                try:
                    with log.open('rb') as stream:
                        stream.seek(0,os.SEEK_END);stream.seek(max(0,stream.tell()-2000));detail=stream.read(2000).decode('utf-8',errors='replace').strip()
                except OSError:detail='无法读取启动日志'
                states[key]={'state':'failed','message':f'工具异常退出（{process.poll()}）。日志：{log}\n{detail}'}
                self.finished[key]=states[key];self.processes.pop(key,None)
        return states
