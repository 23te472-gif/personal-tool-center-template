"""Validated, atomic JSON files. Corrupt prior files are never overwritten."""
from pathlib import Path
from copy import deepcopy
import json, os, tempfile

def load_json(path, default, validate):
    path=Path(path)
    if not path.exists():
        value=deepcopy(default)
    else:
        try:
            if path.stat().st_size>4*1024*1024:raise ValueError('配置文件过大')
            value=json.loads(path.read_text(encoding='utf-8'))
        except (ValueError,UnicodeError) as exc:
            raise ValueError(f'配置损坏，已保留原文件：{path}') from exc
    validate(value)
    return value

def save_json(path, value, default, validate):
    path=Path(path);validate(value);load_json(path,default,validate)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.保存中-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2)
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)
