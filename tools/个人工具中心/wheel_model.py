"""Only explicitly enabled entries can be drawn."""
import random

def default_wheel():return dict(entries=[],recent=[],exclude_recent=False,challenge=True)

def validate_wheel(data):
    if not isinstance(data,dict) or not isinstance(data.get('entries'),list) or len(data['entries'])>3000:raise ValueError('转盘配置格式错误')
    ids=set()
    for item in data['entries']:
        if (not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'] or item['id'] in ids
            or not isinstance(item.get('name'),str) or not item['name'].strip() or len(item['name'])>200
            or not isinstance(item.get('appid'),str) or (item['appid'] and (not item['appid'].isascii() or not item['appid'].isdigit()))
            or type(item.get('enabled')) is not bool):raise ValueError('转盘条目格式错误')
        ids.add(item['id'])
    if (not isinstance(data.get('recent'),list) or len(data['recent'])>3 or any(not isinstance(x,str) for x in data['recent'])
        or type(data.get('exclude_recent')) is not bool or type(data.get('challenge')) is not bool):raise ValueError('转盘设置格式错误')

def candidates(entries,recent,exclude_recent):
    return [x for x in entries if x['enabled'] and (not exclude_recent or x['id'] not in recent[-3:])]

def draw(entries,recent,exclude_recent,rng=random):
    choices=candidates(entries,recent,exclude_recent)
    if not choices:raise ValueError('没有可抽取的游戏，请勾选候选或取消“排除最近三项”。')
    return dict(rng.choice(choices))
