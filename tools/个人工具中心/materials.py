"""Explicit file bookmarks; never searches or moves source files."""
from pathlib import Path
import json
import os
import tempfile

KEYS = ('thesis', 'presentation', 'charts')


def load(path):
    path = Path(path)
    if not path.exists():
        return dict.fromkeys(KEYS, '')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or any(not isinstance(data.get(key, ''), str) for key in KEYS):
            raise ValueError('资料入口格式不正确')
        return {key: data.get(key, '') for key in KEYS}
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f'资料入口配置无法读取，请先备份并修复：{path}') from exc


def save(path, config):
    path = Path(path)
    load(path)  # Preserve damaged configuration rather than silently replacing it.
    if any(not isinstance(config.get(key), str) for key in KEYS):
        raise ValueError('资料入口格式不正确')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.materials-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def pack_files(config):
    paths = []
    for key in ('thesis', 'presentation'):
        if config.get(key):
            path = Path(config[key])
            if not path.is_file():
                raise FileNotFoundError(f'文件已移动或不存在，请重新选择：{path}')
            paths.append(path)
    if not paths:
        raise ValueError('请先选择论文或 PPT 文件。')
    return paths
