from pathlib import Path
import os

def open_path(path: Path) -> None:
    if not path.exists(): raise FileNotFoundError(f'路径已失效，请重新选择：{path}')
    os.startfile(str(path.resolve()))
