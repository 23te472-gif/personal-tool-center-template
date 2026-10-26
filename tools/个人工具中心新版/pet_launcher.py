"""User-configured desktop pet entry. No personal path or arbitrary command arguments."""
from pathlib import Path
import json,os,tempfile,threading,time

class PetLauncher:
    def __init__(self,config,opener,desktop=None):
        self.config=Path(config);self.opener=opener;self.desktop=Path(desktop) if desktop else Path.home()/'Desktop'
        self.lock=threading.RLock();self.last_attempt=None
    def entry(self):
        if self.config.exists():
            try:
                if self.config.stat().st_size>16384:raise ValueError()
                data=json.loads(self.config.read_text(encoding='utf-8'));value=data['entry']
                if not isinstance(value,str) or len(value)>4096:raise ValueError()
                path=Path(value)
                if not path.is_absolute() or path.suffix.lower() not in ('.lnk','.exe'):raise ValueError()
                return path
            except (ValueError,KeyError,TypeError):raise ValueError('桌宠入口配置无法读取，请右键桌宠按钮重新选择。') from None
        candidate=self.desktop/'Agent 桌宠.lnk'
        return candidate if candidate.is_file() else None
    def configure(self,entry):
        path=Path(entry).resolve()
        if not path.is_file() or path.suffix.lower() not in ('.lnk','.exe'):raise ValueError('请选择存在的桌宠快捷方式（.lnk）或程序（.exe）。')
        with self.lock:
            self.config.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(prefix='.pet-',dir=self.config.parent,suffix='.tmp')
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as stream:
                    json.dump(dict(entry=str(path)),stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
                os.replace(name,self.config)
            finally:Path(name).unlink(missing_ok=True)
            self.last_attempt=None
        return dict(cancelled=False)
    def launch(self):
        with self.lock:
            path=self.entry()
            if path is None or not path.is_file():return dict(needs_configuration=True)
            now=time.monotonic()
            if self.last_attempt is not None and now-self.last_attempt<2:return dict(action='pending',message='启动请求已发送，请稍候。')
            self.opener(str(path));self.last_attempt=now
            return dict(action='requested',message='已请求启动桌宠；是否已运行由桌宠自身的单实例机制处理。')
