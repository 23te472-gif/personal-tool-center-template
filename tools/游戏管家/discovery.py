"""Read-only candidate discovery. No process execution."""
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class Candidate:
    name: str
    path: str
    kind: str

def is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&0x400)

def scan_candidates(roots: list[Path]) -> list[Candidate]:
    result=[]; seen=set()
    for root in roots:
        if not root.is_dir(): raise FileNotFoundError(f'目录不存在：{root}')
        for p in sorted(root.iterdir(),key=lambda x:x.name.casefold()):
            if is_link(p): continue
            if p.is_file() and p.suffix.lower() not in ('.exe','.lnk','.url'): continue
            absolute=str(p.resolve())
            if absolute.casefold() in seen: continue
            seen.add(absolute.casefold())
            tool=bool(re.search(r'trainer|wemod|mod manager|加速|launcher|connect|throttlestop',p.stem,re.I))
            name=re.split(r'\s+(?:v\d|Early Access|Plus\s+\d)',p.stem,flags=re.I)[0]
            result.append(Candidate(name,absolute,'目录' if p.is_dir() else '工具' if tool else '入口'))
    return result
