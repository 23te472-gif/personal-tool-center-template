"""Locate cached Steam art locally; do not download or scan game folders."""
from pathlib import Path
from PIL import Image

def find_game_icon(appid,roots):
    if not isinstance(appid,str) or not appid.isascii() or not appid.isdigit():return None
    fallback=None
    for root in roots:
        cache=Path(root)/'appcache/librarycache';folder=cache/appid
        paths=[cache/(appid+'_icon.jpg'),cache/(appid+'_icon.png')]
        if folder.is_dir():paths+=sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ('.jpg','.png','.ico'))[:20]
        for path in paths:
            try:
                if not path.is_file() or path.stat().st_size>4*1024*1024:continue
                with Image.open(path) as image:
                    w,h=image.size
                    if w>=24 and h>=24 and .9<=w/h<=1.1:return path
                    if fallback is None and w>=24 and h>=24:fallback=path
            except (OSError,ValueError):continue
    return fallback

class GameImages:
    def __init__(self):self.roots=None
    def __call__(self,item):
        if not item.get('appid'):return None
        if self.roots is None:
            from steam_reader import detect_steam_roots
            self.roots=detect_steam_roots()
        path=find_game_icon(item.get('appid',''),self.roots)
        if not path:return None
        with Image.open(path) as source:return source.convert('RGBA')
