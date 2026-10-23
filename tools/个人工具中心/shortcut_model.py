"""Desktop-only icon changes, with recoverable intent saved before mutation."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,os,shutil,subprocess,tempfile,threading,uuid
from playful_store import load_json,save_json

FIELDS=('target','arguments','working_directory','window_style','hotkey','description','icon')
EXTENSIONS={'.exe','.com','.bat','.cmd','.ps1','.py','.pyw','.msc'}

def properties(value):return {key:value[key] for key in FIELDS}
def validate_properties(value):
    if not isinstance(value,dict) or any(not isinstance(value.get(key),str) for key in FIELDS if key!='window_style') or type(value.get('window_style')) is not int:
        raise ValueError('快捷方式属性格式错误')
def linked(path):return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&0x400)

class ShortcutBackend:
    def __init__(self,base):self.base=Path(base)
    def request(self,value):
        scratch=self.base/'data/icon_studio/requests';scratch.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(suffix='.json',dir=scratch)
        try:
            with os.fdopen(fd,'w',encoding='utf-8-sig') as stream:json.dump(value,stream,ensure_ascii=False)
            command=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('shortcut_bridge.ps1')),'-RequestFile',name]
            result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:response=json.loads(result.stdout.decode('utf-8-sig'))
            except (ValueError,UnicodeError) as exc:raise OSError('快捷方式接口未返回结果：'+result.stderr.decode('utf-8',errors='replace')[:300]) from exc
            if not response.get('ok'):raise PermissionError(response.get('error','无法修改此快捷方式；未自动提权。'))
            return response.get('result')
        finally:Path(name).unlink(missing_ok=True)
    def desktop_dirs(self):
        value=self.request(dict(action='dirs'))
        return [Path(x) for x in (value if isinstance(value,list) else [value]) if x]
    def read(self,path):
        result=self.request(dict(action='read',path=str(path)));validate_properties(result);return properties(result)
    def read_many(self,paths):
        if not paths:return []
        result=self.request(dict(action='read_many',paths=[str(x) for x in paths]));return result if isinstance(result,list) else [result]
    def write_icon(self,path,icon,expected=None):
        result=self.request(dict(action='write',path=str(path),icon=icon,expected=expected));validate_properties(result);return properties(result)
    def refresh_icon(self,path):return self.request(dict(action='refresh',path=str(path)))
    def verify_icon(self,path):
        from shell_icon_check import icon_location
        return icon_location(path)

def validate_records(data):
    if not isinstance(data,dict) or not isinstance(data.get('records'),dict):raise ValueError('换装记录格式错误，原记录保留')
    for key,record in data['records'].items():
        if (not isinstance(key,str) or not isinstance(record,dict)
            or any(not isinstance(record.get(k),str) for k in ('path','original_icon','applied_icon','prior_icon','target','backup','backup_sha'))
            or record.get('state') not in ('pending','applied','restored')):raise ValueError('换装记录格式错误，原记录保留')

class ShortcutService:
    def __init__(self,base,backend=None,asset_root=None):
        self.base=Path(base).resolve();self.backend=backend or ShortcutBackend(base);self.root=self.base/'data/icon_studio';self.path=self.root/'records.json'
        self.lock=threading.RLock();self._dirs=None
        self.asset_root=Path(asset_root) if asset_root else self.base/'data/icon_studio/assets'
    def records(self):return load_json(self.path,{'records':{}},validate_records)
    def save(self,data):save_json(self.path,data,{'records':{}},validate_records)
    def dirs(self):
        if self._dirs is None:self._dirs=[Path(x).resolve() for x in self.backend.desktop_dirs() if Path(x).is_dir()]
        return self._dirs
    def allowed(self,path):
        path=Path(path).absolute()
        if path.suffix.lower()!='.lnk' or path.parent.resolve() not in self.dirs() or not path.is_file() or linked(path):raise ValueError('只支持桌面直接显示的普通软件快捷方式，不处理子文件夹或特殊入口。')
        return path
    def scan(self):
        paths=[]
        for folder in self.dirs():
            for path in sorted(folder.glob('*.lnk')):
                try:
                    if path.is_file() and not linked(path):paths.append(path)
                except OSError:continue
        result=[]
        for item in self.backend.read_many(paths):
            try:
                validate_properties(item);target=Path(item['target'])
                if target.suffix.lower() not in EXTENSIONS or target.is_dir():continue
                result.append(dict(path=item['path'],**properties(item)))
            except (ValueError,OSError,KeyError):continue
        return result
    def key(self,path):return str(Path(path).resolve()).casefold()
    def _write(self,path,icon,expected):
        if isinstance(self.backend,ShortcutBackend):after=self.backend.write_icon(path,icon,expected)
        else:
            if self.backend.read(path)!=expected:raise ValueError('快捷方式在操作期间发生变化')
            after=self.backend.write_icon(path,icon)
        intended=dict(expected,icon=icon)
        if after!=intended or self.backend.read(path)!=intended:raise OSError('保存后核对未通过，备份已保留')
        return after
    def _asset(self,source):
        source=Path(source)
        if source.suffix.lower()!='.ico' or not source.is_file() or linked(source):raise ValueError('请选择素材库中的普通ICO文件')
        content=source.read_bytes()
        if len(content)>16*1024*1024 or content[:4]!=b'\0\0\1\0':raise ValueError('图标格式不正确')
        digest=hashlib.sha256(content).hexdigest();folder=self.asset_root;folder.mkdir(parents=True,exist_ok=True)
        copy=folder/(digest+'.ico')
        if copy.exists():
            if copy.read_bytes()!=content:raise ValueError('稳定图标副本不一致，请先修复')
        else:
            with copy.open('xb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
        if copy.read_bytes()!=content:raise OSError('图标副本核对失败')
        return str(copy)+',0'
    def apply(self,path,source_icon,expected):
        with self.lock:
            path=self.allowed(path);validate_properties(expected);expected=properties(expected)
            current=self.backend.read(path)
            if current!=expected:raise ValueError('快捷方式已经变化，请刷新后重新选择。')
            if Path(current['target']).suffix.lower() not in EXTENSIONS or Path(current['target']).is_dir():raise ValueError('此入口不是普通软件快捷方式')
            data=self.records();key=self.key(path);previous=deepcopy(data['records'].get(key))
            if previous and previous['state']!='restored' and previous['target'].casefold()!=current['target'].casefold():raise ValueError('快捷方式目标已变，请先处理已有换装记录。')
            icon=self._asset(source_icon)
            if not previous or previous['state']=='restored':
                backups=self.root/'backups';backups.mkdir(parents=True,exist_ok=True);backup=backups/(uuid.uuid4().hex+'.lnk');shutil.copy2(path,backup)
                sha=hashlib.sha256(path.read_bytes()).hexdigest()
                if hashlib.sha256(backup.read_bytes()).hexdigest()!=sha:raise OSError('快捷方式备份核对失败，未修改图标')
                record=dict(path=str(path),original_icon=current['icon'],target=current['target'],backup=str(backup),backup_sha=sha)
            else:record=deepcopy(previous)
            record.update(applied_icon=icon,prior_icon=current['icon'],state='pending');data['records'][key]=record;self.save(data)
            try:
                # Repeat checks immediately before crossing into COM.
                self.allowed(path);self._write(path,icon,current)
                if isinstance(self.backend,ShortcutBackend):
                    verified=self.backend.verify_icon(path)
                    if verified['index']!=0 or Path(verified['path']).resolve()!=Path(icon.rsplit(',',1)[0]).resolve():
                        raise OSError('Windows 解析出的图标与选定素材不一致，备份已保留')
                record['state']='applied';self.save(data)
            except Exception:
                try:
                    now=self.backend.read(path)
                    if now['target'].casefold()==current['target'].casefold() and now['icon']==icon:
                        self._write(path,current['icon'],now)
                        data['records'][key]=previous if previous else dict(record,state='restored')
                        self.save(data)
                except Exception:pass  # The pre-saved pending record remains recoverable.
                raise
            return dict(path=str(path),status='applied')
    def restore(self,path):
        with self.lock:
            path=self.allowed(path);data=self.records();key=self.key(path);record=data['records'].get(key)
            if not record:raise ValueError('此快捷方式没有本换装台的记录')
            if record['state']=='restored':return dict(path=str(path),status='already_restored')
            backup=Path(record['backup'])
            if backup.parent.resolve()!=(self.root/'backups').resolve() or not backup.is_file() or linked(backup) or hashlib.sha256(backup.read_bytes()).hexdigest()!=record['backup_sha']:raise ValueError('备份缺失或已变化，停止还原')
            current=self.backend.read(path)
            if current['target'].casefold()!=record['target'].casefold():raise ValueError('冲突：快捷方式已指向另一个软件，未覆盖')
            accepted={record['applied_icon'],record['original_icon']}
            if record['state']=='pending':accepted.add(record['prior_icon'])
            if current['icon'] not in accepted:raise ValueError('冲突：图标已由其他操作更改，未覆盖')
            if current['icon']!=record['original_icon']:self._write(path,record['original_icon'],current)
            record['state']='restored';self.save(data)
            return dict(path=str(path),status='restored')
    def restore_all(self):
        results=[]
        for record in list(self.records()['records'].values()):
            if record['state']=='restored':continue
            try:results.append(self.restore(record['path']))
            except Exception as exc:results.append(dict(path=record['path'],status='failed',message=str(exc)))
        return results
