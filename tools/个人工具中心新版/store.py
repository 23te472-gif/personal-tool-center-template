"""Atomic local preferences. A corrupt prior file is always preserved."""
from copy import deepcopy
from pathlib import Path
import json,os,tempfile

DEFAULT={'theme':'light','font_scale':1,'pack_files':[],'output_dir':'','recent':[]}

def validate(value):
    if not isinstance(value,dict) or value.get('theme') not in ('light','dark') or type(value.get('font_scale')) not in (int,float) or value['font_scale'] not in (.9,1,1.15):raise ValueError('新版设置格式错误')
    if not isinstance(value.get('pack_files'),list) or len(value['pack_files'])>500 or any(not isinstance(p,str) for p in value['pack_files']):raise ValueError('上次打包记录格式错误')
    if not isinstance(value.get('output_dir'),str) or not isinstance(value.get('recent'),list) or len(value['recent'])>50:raise ValueError('最近使用记录格式错误')
    if any(not isinstance(r,dict) or any(not isinstance(r.get(k),str) for k in ('id','name','time')) for r in value['recent']):raise ValueError('最近使用记录格式错误')

def load(path):
    path=Path(path)
    if not path.exists():return deepcopy(DEFAULT)
    if path.stat().st_size>1024*1024:raise ValueError('新版设置文件过大，已保留原文件')
    try:value=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as exc:raise ValueError('新版设置损坏，已保留原文件') from exc
    validate(value);return value

def save(path,value):
    path=Path(path);validate(value);load(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.settings-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:Path(temp).unlink(missing_ok=True)
