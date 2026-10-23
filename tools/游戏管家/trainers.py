"""Local trainer grouping and editable bilingual names."""
from pathlib import Path
from dataclasses import replace
from datetime import datetime
import os,re,uuid
from discovery import is_link
from library import Game

# Display suggestions, editable in the UI. No online lookup is required.
NAMES={
 'Against the Storm':('风暴之城','1336490'),
 'Cult of the Lamb':('咩咩启示录','1313140'),
 'Deep Rock Galactic Survivor':('深岩银河：幸存者','2321470'),
 'Devil May Cry 5':('鬼泣5','601150'),
 'Gunfire Reborn':('枪火重生','1217060'),
 'Hades':('哈迪斯','1145360'),
 'Hollow Knight Silksong':('空洞骑士：丝之歌','1030300'),
 'Monster Hunter Rise':('怪物猎人：崛起','1446780'),
 'Monster Hunter World':('怪物猎人：世界','582010'),
 'Risk of Rain 2':('雨中冒险2','632360'),
 'Skul The Hero Slayer':('小骨：英雄杀手','1147560'),
 'Valheim':('英灵神殿','892970'),
 'Warm Snow':('暖雪','1296830'),
}
def normal(text):return re.sub(r'[^\w\u4e00-\u9fff]','',text.casefold())
def excluded(path):
    value=normal(str(path))
    return 'cheatengine' in value or 'wemod' in value
def trainer_name(path):return re.split(r'\s+(?:v\d|Early Access|Plus\s+\d)',Path(path).stem,flags=re.I)[0].strip()
def scan_trainers(roots):
    found={};warnings=[]
    for root in map(Path,roots):
        if not root.is_dir():warnings.append(f'目录不存在：{root}');continue
        def error(exc):warnings.append(str(exc))
        for folder,dirs,files in os.walk(root,followlinks=False,onerror=error):
            dirs[:]=[d for d in dirs if not excluded(Path(folder)/d) and not is_link(Path(folder)/d)]
            if excluded(folder):continue
            for name in files:
                path=Path(folder)/name
                if excluded(path) or path.suffix.lower()!='.exe' or not re.search(r'trainer|修改器',name,re.I):continue
                if re.search(r'修复|安装|卸载|setup|installer|unins',name,re.I):continue
                if is_link(path):continue
                found[str(path.resolve()).casefold()]=path.resolve()
    return sorted(found.values(),key=lambda p:str(p).casefold()),warnings
def merge_trainers(games,paths,steam):
    result=[replace(g,tool_paths=list(g.tool_paths),aliases=list(g.aliases)) for g in games]
    for path in paths:
        path=Path(path)
        if excluded(path):continue
        english=trainer_name(path);canonical=next((n for n in NAMES if normal(n)==normal(english)),english)
        chinese,appid=NAMES.get(canonical,(canonical,''))
        g=next((g for g in result if any(str(Path(p)).casefold()==str(path).casefold() for p in g.tool_paths)),None)
        if g is None:
            names={normal(canonical),normal(chinese)}
            matches=[g for g in result if any(normal(value) in names for value in [g.name,g.english_name]+g.aliases if value)]
            if len(matches)==1:g=matches[0]
        if g is None:g=Game(uuid.uuid4().hex,chinese,english_name=canonical);result.append(g)
        if normal(g.name)==normal(canonical):g.name=chinese
        if not g.english_name:g.english_name=canonical
        if all(str(Path(p)).casefold()!=str(path).casefold() for p in g.tool_paths):g.tool_paths.append(str(path))
        if not g.preferred_tool:g.preferred_tool=str(path)
        if chinese!=g.name and chinese not in g.aliases:g.aliases.append(chinese)
    for g in result:
        canonical=next((n for n in NAMES if normal(n)==normal(g.english_name or g.name)),None)
        appid=NAMES[canonical][1] if canonical else ''
        match=next((a for a in steam if (appid and a['appid']==appid) or normal(a['name'])==normal(g.english_name or g.name)),None)
        if match:g.steam_appid=match['appid'];g.steam_install=match['install']
    return result
def ordered_games(games):
    # Stable three-pass sort: Chinese display name, recent activity, favorites.
    result=sorted(games,key=lambda g:g.name.casefold())
    result.sort(key=lambda g:g.last_used,reverse=True);result.sort(key=lambda g:g.favorite,reverse=True);return result
def tool_info(path):
    p=Path(path);match=re.search(r'\bv\d[^\s]*|Early Access',p.stem,re.I)
    try:modified=datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    except OSError:modified='文件缺失'
    return {'name':p.name,'version':match.group(0) if match else '未标注版本','modified':modified}
