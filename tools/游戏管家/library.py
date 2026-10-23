"""Validated, atomic local library storage."""
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import os
import tempfile
import hashlib
import time
import msvcrt
from contextlib import contextmanager

class LibraryRows(list):
    """A loaded snapshot carries its revision through in-place edits."""
    pass

def library_revision(path):
    try:return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:return None

@contextmanager
def _write_lock(path):
    lock_path=Path(str(path)+'.lock')
    with lock_path.open('a+b') as handle:
        handle.seek(0,2)
        if handle.tell()==0:handle.write(b'0');handle.flush()
        deadline=time.monotonic()+5
        while True:
            try:handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1);break
            except OSError:
                if time.monotonic()>=deadline:raise OSError('资料库正在由其他窗口保存，请稍后再试')
                time.sleep(.025)
        try:yield
        finally:handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)

_UNSPECIFIED=object()

@dataclass
class Game:
    id: str
    name: str
    launch_path: str = ''
    tool_paths: list[str] = None
    save_dir: str = ''
    notes: str = ''
    english_name: str = ''
    aliases: list[str] = field(default_factory=list)
    favorite: bool = False
    last_used: str = ''
    preferred_tool: str = ''
    steam_appid: str = ''
    steam_install: str = ''

    def __post_init__(self):
        if self.tool_paths is None: self.tool_paths = []

def validate(games):
    ids=set()
    for g in games:
        if not isinstance(g,Game) or not all(isinstance(getattr(g,k),str) for k in ('id','name','launch_path','save_dir','notes')):
            raise ValueError('卡片字段格式错误')
        if not g.id or not g.name.strip() or g.id in ids: raise ValueError('卡片名称为空或 ID 重复')
        if not isinstance(g.tool_paths,list) or not all(isinstance(p,str) for p in g.tool_paths): raise ValueError('工具列表格式错误')
        if not isinstance(g.aliases,list) or not all(isinstance(p,str) for p in g.aliases):raise ValueError('别名格式错误')
        if type(g.favorite) is not bool or not all(isinstance(getattr(g,k),str) for k in ('english_name','last_used','preferred_tool','steam_appid','steam_install')):raise ValueError('修改器管理字段格式错误')
        if g.steam_appid and not g.steam_appid.isdecimal():raise ValueError('Steam AppID 必须是数字')
        ids.add(g.id)

def load_library(path: Path) -> list[Game]:
    if not path.exists():
        games=LibraryRows();games.revision=None;return games
    try:
        raw=path.read_bytes();data=json.loads(raw.decode('utf-8'))
        if not isinstance(data,list): raise ValueError('根节点必须为列表')
        games=LibraryRows(Game(**row) for row in data);validate(games)
        games.revision=hashlib.sha256(raw).hexdigest();return games
    except (TypeError,KeyError,json.JSONDecodeError) as exc:
        raise ValueError('资料库损坏，请先保留原文件并检查') from exc

def save_library(path: Path, games: list[Game], *, expected_revision=_UNSPECIFIED) -> None:
    validate(games); path.parent.mkdir(parents=True,exist_ok=True)
    if expected_revision is _UNSPECIFIED:expected_revision=getattr(games,'revision',_UNSPECIFIED)
    with _write_lock(path):
        if expected_revision is not _UNSPECIFIED and library_revision(path)!=expected_revision:
            raise ValueError('资料库已由其他窗口更新，本次更改未保存；请刷新后重试')
        _save_atomic(path,games)
        if isinstance(games,LibraryRows):games.revision=library_revision(path)

def _save_atomic(path,games):
    fd,temp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump([asdict(g) for g in games],f,ensure_ascii=False,indent=2)
            f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        Path(temp).unlink(missing_ok=True)
