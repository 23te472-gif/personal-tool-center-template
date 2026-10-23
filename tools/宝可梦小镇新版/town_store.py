"""Atomic saves, a verified previous backup, and explicit corrupt-file recovery."""
from pathlib import Path
import hashlib,json,os,tempfile,uuid
from town_state import new_town,validate_town,validate_legacy

class LegacyImportError(ValueError):pass
class CorruptSaveError(ValueError):pass

def digest(raw):return hashlib.sha256(raw).hexdigest()
def atomic_write(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix='.town-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)
def decode(raw):
    try:
        if len(raw)>4*1024*1024:raise ValueError('存档文件过大')
        value=json.loads(raw.decode('utf-8-sig'));validate_town(value);return value
    except (ValueError,UnicodeError,TypeError,KeyError) as exc:raise CorruptSaveError('小镇存档未通过校验，原文件已保留：'+str(exc)) from exc

class TownRepository:
    def __init__(self,base,legacy_path=None):
        self.path=Path(base)/'data/town.json';self.backup=self.path.with_name('town.backup.json');self.legacy_path=Path(legacy_path) if legacy_path else None;self.revision=None
    def load(self,allow_fresh=False):
        if self.path.exists():
            raw=self.path.read_bytes();data=decode(raw);self.revision=digest(raw);return data
        legacy=None
        if self.legacy_path and self.legacy_path.is_file() and not allow_fresh:
            try:
                if self.legacy_path.stat().st_size>65536:raise ValueError('原小屋存档过大')
                legacy=json.loads(self.legacy_path.read_text(encoding='utf-8-sig'));validate_legacy(legacy)
            except (ValueError,UnicodeError,TypeError,KeyError) as exc:raise LegacyImportError('原小屋存档无法继承，原文件保留。可明确选择从新档开始。') from exc
        data=new_town(legacy);self.save(data);return data
    def save(self,data):
        validate_town(data)
        if self.path.exists():
            previous=self.path.read_bytes();decode(previous)
            if self.revision!=digest(previous):raise ValueError('存档已被其他窗口更改，请关闭并重新打开小镇，避免覆盖新进度。')
            atomic_write(self.backup,previous)
        elif self.revision is not None:raise ValueError('存档文件已在外部移走，请重新打开小镇。')
        raw=json.dumps(data,ensure_ascii=False,indent=2).encode('utf-8');atomic_write(self.path,raw);self.revision=digest(raw)
    def restore_backup(self):
        raw=self.backup.read_bytes();data=decode(raw)
        if self.path.exists():atomic_write(self.path.with_name('town.corrupt-'+uuid.uuid4().hex[:10]+'.json'),self.path.read_bytes())
        atomic_write(self.path,raw);self.revision=digest(raw);return data
