"""Small previews from the existing local collection; no network access."""
from pathlib import Path

def find_collection(base):
    for folder in (Path(base)/'assets/pokemon',):
        if folder.is_dir() and any(folder.glob('*.ico')):return folder
    return None

def load_preview(path,size):
    from PIL import Image,ImageTk
    with Image.open(path) as source:
        picture=source.convert('RGBA');picture.thumbnail(size,Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(picture)

def choices(base):
    folder=find_collection(base)
    return {p.stem:p for p in sorted(folder.glob('*.png'))} if folder else {}
