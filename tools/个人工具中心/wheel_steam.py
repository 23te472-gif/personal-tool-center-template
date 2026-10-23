"""Explicit import from local manifests; never starts Steam."""
from pathlib import Path
import json
import steam_reader

def import_installed(base,existing):
    games,warnings=steam_reader.read_steam_games(steam_reader.detect_steam_roots())
    aliases={};english={}
    library=Path(base).parent/'游戏管家/data/library.json'
    try:
        if library.is_file():
            data=json.loads(library.read_text(encoding='utf-8'))
            if not isinstance(data,list):raise ValueError('不是游戏列表')
            for item in data:
                if not isinstance(item,dict) or not isinstance(item.get('name'),str):continue
                if item.get('steam_appid'):aliases[str(item['steam_appid'])]=item['name']
                if isinstance(item.get('english_name'),str):english[item['english_name'].casefold()]=item['name']
    except (ValueError,OSError) as exc:warnings.append('中文名称读取失败：'+str(exc))
    entries=[dict(x) for x in existing];known={x['appid'] for x in entries if x['appid']}
    for game in games:
        if not game['installed'] or game['appid'] in known:continue
        entries.append(dict(id='steam-'+game['appid'],name=aliases.get(game['appid'],english.get(game['name'].casefold(),game['name'])),appid=game['appid'],enabled=True));known.add(game['appid'])
    return entries,warnings
