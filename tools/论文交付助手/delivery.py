"""Local delivery project, preflight and atomically published verified bundles."""
from dataclasses import dataclass,asdict,field
from datetime import datetime
from pathlib import Path
import hashlib,json,os,re,shutil,tempfile,uuid,zipfile

SCENES={'中间发表':('汇报',),'最终答辩':('论文','汇报'),'论文提交':('论文',)}
ROLES={'论文':'论文','汇报':'答辩PPT','图表':'图表','附件':'附件'}

@dataclass
class Material:
    path:str
    role:str='附件'
    selected:bool=True

@dataclass
class Project:
    name:str='毕业论文'
    scene:str='论文提交'
    output:str=''
    require_pdf:bool=False
    materials:list[Material]=field(default_factory=list)
    notes:str=''

def validate(project):
    if not isinstance(project,Project):raise ValueError('项目格式错误')
    if not all(isinstance(getattr(project,k),str) for k in ('name','scene','output','notes')):raise ValueError('项目字段格式错误')
    if project.scene not in SCENES or type(project.require_pdf) is not bool:raise ValueError('提交场景格式错误')
    if not isinstance(project.materials,list):raise ValueError('文件列表格式错误')
    for m in project.materials:
        if not isinstance(m,Material) or not isinstance(m.path,str) or m.role not in ROLES or type(m.selected) is not bool:raise ValueError('材料字段格式错误')

def save_project(path,project):
    validate(project);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(asdict(project),stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)

def load_project(path):
    try:
        row=json.loads(Path(path).read_text(encoding='utf-8'))
        row['materials']=[Material(**m) for m in row['materials']]
        project=Project(**row);validate(project);return project
    except (TypeError,KeyError,json.JSONDecodeError) as exc:raise ValueError('项目文件格式错误，原文件保持不变') from exc

def linked(path):
    for p in (path,*path.parents):
        if p.exists() and (p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400):return True
    return False

def signature(path):
    s=path.stat();return (s.st_size,s.st_mtime_ns)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def check_project(project):
    validate(project);errors=[];warnings=[];planned=[];seen=set();used=set()
    if not project.name.strip() or re.search(r'[<>:"/\\|?*\x00-\x1f]',project.name) or project.name.endswith((' ','.')) or project.name in ('.','..'):
        errors.append('项目名称为空或含不允许的路径字符')
    if re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',project.name):errors.append('项目名称不能是 Windows 保留设备名')
    if not project.output.strip():errors.append('请选择输出目录')
    else:
        output=Path(project.output)
        if output.exists() and not output.is_dir():errors.append('输出位置必须是目录')
        if linked(output):errors.append('输出目录不能包含文件系统链接')
    selected=[m for m in project.materials if m.selected]
    if not selected:errors.append('尚未选择本次提交的文件')
    for role in SCENES[project.scene]:
        files=[m for m in selected if m.role==role]
        if not files:errors.append(f'{project.scene}缺少必需材料：{role}')
        if project.require_pdf and not any(Path(m.path).suffix.lower()=='.pdf' for m in files):errors.append(f'{role}需要 PDF 版本（不会自动转换）')
    for material in selected:
        p=Path(material.path)
        try:
            if not material.path or not p.is_absolute():raise ValueError('请选择完整文件路径')
            if linked(p):raise ValueError('不能提交文件系统链接')
            if not p.is_file():raise ValueError('文件不存在或不是普通文件')
            if p.name.startswith('~$'):raise ValueError('不能提交 Office 临时锁文件')
            source_stat=p.stat()
            if source_stat.st_size==0:raise ValueError('文件为空')
            key=str(p.resolve()).casefold()
            if key in seen:raise ValueError('同一文件重复选择')
            seen.add(key)
            relative=Path(ROLES[material.role])/p.name
            n=1
            while relative.as_posix().casefold() in used:
                n+=1;relative=Path(ROLES[material.role])/(p.stem+f' ({n})'+p.suffix)
            if n>1:warnings.append(f'同名文件已区分：{p.name} → {relative}')
            used.add(relative.as_posix().casefold())
            planned.append({'source':str(p.resolve()),'relative':relative.as_posix(),'role':material.role,'size':source_stat.st_size,'mtime_ns':source_stat.st_mtime_ns,'modified':datetime.fromtimestamp(source_stat.st_mtime).isoformat(timespec='seconds')})
        except (OSError,ValueError) as exc:errors.append(f'{p}：{exc}')
    return {'errors':errors,'warnings':warnings,'files':planned}

def build_delivery(project,progress,expected=None):
    check=expected if expected is not None else check_project(project)
    if check['errors']:raise ValueError('\n'.join(check['errors']))
    output=Path(project.output).resolve();output.mkdir(parents=True,exist_ok=True)
    batch=f'{project.name}_{project.scene}_{datetime.now():%Y%m%d-%H%M%S}_{uuid.uuid4().hex[:8]}'
    stage=Path(tempfile.mkdtemp(prefix='.打包中-',dir=output));final=output/batch
    try:
        payload=stage/'交付文件';payload.mkdir()
        sources=[(Path(row['source']),(row['size'],row['mtime_ns'])) for row in check['files']]
        for source,before in sources:
            if signature(source)!=before:raise OSError(f'检查后源文件发生变化，请重新确认版本：{source}')
        records=[]
        for i,(row,(source,before)) in enumerate(zip(check['files'],sources),1):
            progress(f'复制与校验 {i}/{len(sources)}：{source.name}')
            if linked(source):raise OSError(f'来源变成链接：{source}')
            dest=payload/row['relative'];dest.parent.mkdir(parents=True,exist_ok=True)
            with source.open('rb') as reader,dest.open('xb') as writer:shutil.copyfileobj(reader,writer,1024*1024)
            copied=digest(dest)
            if signature(source)!=before or digest(source)!=copied:raise OSError(f'打包期间文件发生变化：{source}')
            records.append(dict(row,sha256=copied))
        record={'version':1,'created':datetime.now().isoformat(timespec='seconds'),'name':project.name,'scene':project.scene,'notes':project.notes,'files':records,'warnings':check['warnings']}
        text=f'项目：{project.name}\n场景：{project.scene}\n生成时间：{record["created"]}\n备注：{project.notes}\n\n'
        for row in records:text+=f'{row["relative"]}\n  来源：{row["source"]}\n  大小：{row["size"]} 字节\n  SHA-256：{row["sha256"]}\n'
        if check['warnings']:text+='\n提示：\n'+'\n'.join(check['warnings'])
        (payload/'交付清单.txt').write_text(text,encoding='utf-8-sig')
        (stage/'交付记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        with zipfile.ZipFile(stage/'交付包.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in payload.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(payload))
        with zipfile.ZipFile(stage/'交付包.zip') as z:
            if z.testzip():raise OSError('ZIP 校验失败')
            for row in records:
                h=hashlib.sha256()
                with z.open(row['relative']) as stream:
                    for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
                if h.hexdigest()!=row['sha256']:raise OSError('ZIP 内容校验失败')
        for source,before in sources:
            if linked(source) or signature(source)!=before:raise OSError(f'打包期间源文件发生变化：{source}')
        os.replace(stage,final);return final
    finally:
        if stage.exists():shutil.rmtree(stage)

def history(output):
    result=[];output=Path(output)
    if not output.is_dir():return result
    for p in output.iterdir():
        if not p.is_dir() or p.name.startswith('.') or linked(p):continue
        record=p/'交付记录.json'
        try:
            row=json.loads(record.read_text(encoding='utf-8'))
            if row.get('version')==1 and isinstance(row.get('files'),list) and (p/'交付包.zip').is_file():result.append(dict(row,path=str(p)))
        except (OSError,ValueError,AttributeError):continue
    return sorted(result,key=lambda r:str(r.get('created','')),reverse=True)
