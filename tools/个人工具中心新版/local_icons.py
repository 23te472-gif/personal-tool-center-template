"""Bounded thumbnails from existing Steam cache only; never downloads artwork."""
from pathlib import Path
import base64,io,re
from PIL import Image,ImageOps
import game_icons,steam_reader

class SteamIcons:
    def __init__(self,roots=None):self._roots=roots;self._cache={}
    def get(self,appid):
        if not isinstance(appid,str) or not re.fullmatch(r'[0-9]{1,12}',appid):return ''
        if appid in self._cache:return self._cache[appid]
        result=''
        try:
            if self._roots is None:self._roots=steam_reader.detect_steam_roots()
            path=game_icons.find_game_icon(appid,self._roots)
            if path and Path(path).stat().st_size<=4*1024*1024:
                with Image.open(path) as original:
                    if max(original.size)<=4096:
                        image=ImageOps.fit(original.convert('RGBA'),(80,80),method=Image.Resampling.LANCZOS)
                        output=io.BytesIO();image.save(output,format='PNG');raw=output.getvalue()
                        if len(raw)<=65536:result='data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
        except (OSError,ValueError,Image.DecompressionBombError):pass
        self._cache[appid]=result;return result
