"""Verified ZIP snapshots and defensive export to an empty directory."""
from pathlib import Path, PurePosixPath
from datetime import datetime
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
import zipfile
from discovery import is_link

def reject_link_chain(path):
    for part in (path,*path.parents):
        if part.exists() and is_link(part): raise ValueError(f'路径包含链接：{part}')

def inventory(source,progress):
    files=[]
    def fail(error):raise error
    for root,dirs,names in os.walk(source,followlinks=False,onerror=fail):
        base=Path(root)
        skipped=[d for d in dirs if is_link(base/d)]
        dirs[:]=sorted(d for d in dirs if d not in skipped)
        for d in skipped:progress(f'跳过链接：{base/d}')
        for name in sorted(names):
            p=base/name
            if is_link(p):progress(f'跳过链接：{p}'); continue
            s=p.stat(); files.append((p,s.st_size,s.st_mtime_ns))
    return files

def create_backup(source: Path, backup_root: Path, game_id: str, progress) -> Path:
    reject_link_chain(source); reject_link_chain(backup_root)
    source=source.resolve(); backup_root=backup_root.resolve()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',game_id): raise ValueError('无效卡片 ID')
    if not source.is_dir(): raise ValueError('请选择已有存档目录')
    if source==backup_root or source in backup_root.parents or backup_root in source.parents:
        raise ValueError('存档与备份目录不能互相包含')
    if is_link(source): raise ValueError('不能备份目录链接')
    files=inventory(source,progress)
    folder=backup_root/game_id; folder.mkdir(parents=True,exist_ok=True)
    final=folder/(datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.zip')
    temp=final.with_suffix('.tmp'); manifest={}
    try:
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            for index,(p,size,mtime) in enumerate(files):
                progress(f'备份 {index+1}/{len(files)}：{p.name}')
                if is_link(p): raise OSError(f'源文件变成链接：{p}')
                relative=p.relative_to(source).as_posix(); digest=hashlib.sha256()
                with p.open('rb') as reader,z.open('files/'+relative,'w',force_zip64=True) as writer:
                    while chunk:=reader.read(1024*1024): writer.write(chunk); digest.update(chunk)
                after=p.stat()
                if (after.st_size,after.st_mtime_ns)!=(size,mtime): raise OSError(f'备份期间文件发生变化：{p}')
                manifest[relative]={'sha256':digest.hexdigest(),'size':size}
            z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
        with zipfile.ZipFile(temp) as z:
            if z.testzip(): raise OSError('备份校验失败')
        if files!=inventory(source,lambda _:None): raise OSError('备份期间存档文件集合或内容发生变化，请关闭游戏后重试')
        os.replace(temp,final); return final
    finally: temp.unlink(missing_ok=True)

def list_backups(backup_root: Path, game_id: str) -> list[Path]:
    if not re.fullmatch(r'[A-Za-z0-9_-]+',game_id): raise ValueError('无效卡片 ID')
    return sorted((backup_root/game_id).glob('*.zip'),reverse=True)

def safe_name(name):
    p=PurePosixPath(name)
    if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or any(part.endswith((' ','.')) for part in p.parts):
        raise ValueError('备份包含不安全路径')
    if any(re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',part) for part in p.parts):
        raise ValueError('备份包含保留设备名')
    return p

def export_backup(archive: Path, destination: Path) -> None:
    reject_link_chain(destination)
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('请选择新的空目录')
    if destination.exists() and is_link(destination): raise ValueError('不能导出到目录链接')
    with zipfile.ZipFile(archive) as z:
        seen=set()
        for info in z.infolist():
            safe_name(info.filename)
            if stat.S_ISLNK(info.external_attr>>16): raise ValueError('备份含符号链接')
            key=info.filename.casefold()
            if key in seen: raise ValueError('备份含重名路径')
            seen.add(key)
            if info.filename!='manifest.json' and not info.filename.startswith('files/'):
                raise ValueError('不是本软件的备份')
        manifest=json.loads(z.read('manifest.json'))
        if not isinstance(manifest,dict): raise ValueError('无效备份清单')
        expected={'files/'+name for name in manifest}
        if expected!={i.filename for i in z.infolist() if i.filename!='manifest.json'}:
            raise ValueError('备份内容与清单不一致')
        for name,record in manifest.items():
            safe_name(name)
            if not isinstance(record,dict) or not isinstance(record.get('size'),int) or not isinstance(record.get('sha256'),str): raise ValueError('无效校验记录')
        destination.mkdir(parents=True,exist_ok=True)
        created=[]
        try:
            for name,record in manifest.items():
                target=destination.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                digest=hashlib.sha256(); count=0
                with z.open('files/'+name) as reader,target.open('xb') as writer:
                    created.append(target)
                    while chunk:=reader.read(1024*1024): writer.write(chunk); digest.update(chunk); count+=len(chunk)
                if count!=record['size'] or digest.hexdigest()!=record['sha256']: raise ValueError('备份文件校验失败')
        except Exception:
            for target in reversed(created): target.unlink(missing_ok=True)
            for folder in sorted(destination.rglob('*'),key=lambda p:len(p.parts),reverse=True):
                if folder.is_dir() and not any(folder.iterdir()): folder.rmdir()
            raise
