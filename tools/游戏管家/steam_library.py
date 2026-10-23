"""Read only local Steam manifests. Never launches Steam or downloads metadata."""
from pathlib import Path
import re
from discovery import is_link

def parse_vdf(text):
    tokens=[];position=0
    pattern=re.compile(r'\s+|//[^\n]*|"((?:\\.|[^"\\])*)"|([{}])')
    text=text.lstrip('\ufeff')
    while position<len(text):
        match=pattern.match(text,position)
        if not match:raise ValueError('无法解析 Steam 配置')
        position=match.end()
        if match.group(1) is not None:tokens.append(('text',re.sub(r'\\([\\"])',r'\1',match.group(1))))
        elif match.group(2):tokens.append((match.group(2),match.group(2)))
    index=0
    def obj(depth=0):
        nonlocal index
        if depth>32:raise ValueError('Steam 配置嵌套过深')
        result={}
        while index<len(tokens):
            kind,key=tokens[index];index+=1
            if kind=='}':
                if not depth:raise ValueError('多余的结束括号')
                return result
            if kind!='text' or index>=len(tokens):raise ValueError('Steam 配置缺少值')
            kind,value=tokens[index];index+=1
            if kind=='{':result[key]=obj(depth+1)
            elif kind=='text':result[key]=value
            else:raise ValueError('Steam 配置值无效')
        if depth:raise ValueError('Steam 配置未闭合')
        return result
    return obj()

def detect_steam_roots():
    roots=[Path('C:/Program Files (x86)/Steam'),Path('C:/Program Files/Steam'),Path('D:/Steam'),Path('D:/SteamLibrary')]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as key:roots.insert(0,Path(winreg.QueryValueEx(key,'SteamPath')[0]))
    except OSError:pass
    return [p for p in roots if (p/'steamapps').is_dir()]

def read_steam_games(roots):
    libraries={str(Path(p).resolve()).casefold():Path(p) for p in roots};warnings=[]
    for root in list(libraries.values()):
        config=root/'steamapps/libraryfolders.vdf'
        if not config.is_file():continue
        try:
            data=parse_vdf(config.read_text(encoding='utf-8'))['libraryfolders']
            for value in data.values():
                path=value.get('path') if isinstance(value,dict) else value
                if isinstance(path,str) and Path(path).is_absolute():libraries[str(Path(path).resolve()).casefold()]=Path(path)
        except (OSError,ValueError,KeyError,AttributeError) as exc:warnings.append(f'{config}：{exc}')
    result={}
    for root in libraries.values():
        folder=root/'steamapps'
        if not folder.is_dir():warnings.append(f'Steam 库当前不可用：{root}');continue
        for manifest in folder.glob('appmanifest_*.acf'):
            try:
                if is_link(manifest):continue
                data=parse_vdf(manifest.read_text(encoding='utf-8'))['AppState']
                appid=data['appid'];name=data['name'];install=data['installdir']
                if not isinstance(appid,str) or not appid.isdecimal() or not isinstance(name,str):raise ValueError('无效游戏标识')
                if not isinstance(install,str) or Path(install).name!=install or install in ('.','..'):raise ValueError('无效安装目录')
                target=folder/'common'/install
                result.setdefault(appid,{'appid':appid,'name':name,'install':str(target),'installed':target.is_dir(),'library':str(root)})
            except (OSError,ValueError,KeyError,TypeError) as exc:warnings.append(f'{manifest.name}：{exc}')
    return list(result.values()),warnings
