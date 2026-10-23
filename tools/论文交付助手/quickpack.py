"""Plain ZIP creation: selected files only, bounded memory, no project checklist."""
from pathlib import Path
from datetime import datetime
import os,tempfile,uuid,zipfile

def signature(path):
    s=path.stat();return s.st_size,s.st_mtime_ns

def create_zip(files,output,progress):
    paths=[];seen=set()
    for value in files:
        path=Path(value)
        if not path.is_file() or path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400:raise ValueError(f'请选择存在的普通文件：{path}')
        key=str(path.resolve()).casefold()
        if key not in seen:paths.append(path.resolve());seen.add(key)
    if not paths:raise ValueError('没有选择文件')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    final=output/('文件打包_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]+'.zip')
    fd,name=tempfile.mkstemp(prefix='.打包中-',suffix='.tmp',dir=output);os.close(fd);temp=Path(name)
    try:
        before={path:signature(path) for path in paths};used=set()
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as archive:
            for i,path in enumerate(paths,1):
                progress(f'压缩 {i}/{len(paths)}：{path.name}')
                if path.is_symlink() or signature(path)!=before[path]:raise OSError(f'压缩期间文件发生变化：{path.name}')
                relative=path.name;n=1
                while relative.casefold() in used:n+=1;relative=f'{path.stem} ({n}){path.suffix}'
                used.add(relative.casefold());archive.write(path,relative)
        with zipfile.ZipFile(temp) as archive:
            if archive.testzip():raise OSError('压缩包校验失败')
        for path in paths:
            if signature(path)!=before[path]:raise OSError(f'压缩期间文件发生变化：{path.name}')
        # On Windows rename refuses an existing target; never replace a prior ZIP.
        os.rename(temp,final);return final
    finally:temp.unlink(missing_ok=True)
