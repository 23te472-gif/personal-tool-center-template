"""Versioned town state; no file IO or UI dependencies."""
from datetime import date
import uuid

AREAS={'home':'家园','plaza':'广场','orchard':'果园'}
SHOP={'plant':('盆栽',2),'rug':('地毯',3),'bookshelf':('书架',5),'bench':('长椅',4),'flowerbed':('花圃',4),'lamp':('路灯',6)}
PARTNERS=('01-派拉斯特','02-妙蛙种子','03-喷火龙','04-杰尼龟','05-小海狮','06-袋兽','07-百变怪','08-快龙','09-猫老大（阿罗拉）','10-多边兽Ⅱ','11-水跃鱼','12-沙奈朵','13-玛力露丽','14-煤炭龟','15-雷吉斯奇鲁','16-波加曼','17-音箱蟀','18-帕奇利兹','19-洛托姆（加热形态）','20-风妖精')
ACHIEVEMENTS={'place':'安家啦','friend':'新朋友','focus':'专注萌芽'}
DURATIONS=(5,15,25,45)

def require(condition,message='存档格式不正确'):
    if not condition:raise ValueError(message)
def integer(value,low=0,high=1000000000):return type(value) is int and low<=value<=high
def day_key(value):
    try:return isinstance(value,str) and date.fromisoformat(value).isoformat()==value
    except ValueError:return False
def default_day():return dict(greeted=[],watered=False,arranged=False,claimed=[],harvested=False)
def fresh_focus():return dict(task='',duration=25,remaining=1500,active=False,session_id=uuid.uuid4().hex)
def validate_focus(focus):
    require(isinstance(focus,dict),'专注状态格式错误')
    require(isinstance(focus.get('task'),str) and len(focus['task'])<=500)
    require(type(focus.get('duration')) is int and focus['duration'] in DURATIONS)
    require(integer(focus.get('remaining'),0,focus['duration']*60) and type(focus.get('active')) is bool)
    require(isinstance(focus.get('session_id'),str) and 1<=len(focus['session_id'])<=80)
def validate_legacy(data):
    require(isinstance(data,dict),'原小屋存档格式错误')
    validate_focus(dict(data,session_id='legacy'))
    require(integer(data.get('berries')) and data.get('partner') in PARTNERS)
    require(isinstance(data.get('owned'),list) and all(isinstance(x,str) and x in ('盆栽','地毯','书架') for x in data['owned']))

def new_town(legacy=None):
    data=dict(version=1,berries=20,areas=['home','plaza'],inventory={},placements={k:{} for k in AREAS},partner='02-妙蛙种子',affinity={},daily={},achievements=[],focus=fresh_focus(),stats={},origin='new')
    for kind in ('bench','plant'):data['inventory'][uuid.uuid4().hex]=kind
    if legacy is not None:
        validate_legacy(legacy);data.update(berries=20+legacy['berries'],partner=legacy['partner'],origin='legacy')
        for label in legacy['owned']:
            kind={'盆栽':'plant','地毯':'rug','书架':'bookshelf'}[label];data['inventory'][uuid.uuid4().hex]=kind
        data['focus'].update({k:legacy[k] for k in ('task','duration','remaining','active')})
    validate_town(data);return data

def validate_town(data):
    require(isinstance(data,dict) and type(data.get('version')) is int and data['version']==1,'不支持的存档版本')
    require(integer(data.get('berries')))
    areas=data.get('areas');require(isinstance(areas,list) and all(isinstance(x,str) and x in AREAS for x in areas) and len(areas)==len(set(areas)) and {'home','plaza'}<=set(areas))
    inventory=data.get('inventory');require(isinstance(inventory,dict) and len(inventory)<=1000)
    require(all(isinstance(k,str) and 1<=len(k)<=80 and isinstance(v,str) and v in SHOP for k,v in inventory.items()))
    require(data.get('partner') in PARTNERS and data.get('origin') in ('new','legacy'))
    affinity=data.get('affinity');require(isinstance(affinity,dict) and all(k in PARTNERS and integer(v,0,100) for k,v in affinity.items()))
    achievements=data.get('achievements');require(isinstance(achievements,list) and all(isinstance(x,str) and x in ACHIEVEMENTS for x in achievements) and len(achievements)==len(set(achievements)))
    places=data.get('placements');require(isinstance(places,dict) and set(places)==set(AREAS));seen=set()
    for area,items in places.items():
        require(isinstance(items,dict) and (not items or area in areas))
        for item,position in items.items():
            require(item in inventory and item not in seen and isinstance(position,list) and len(position)==2)
            require(integer(position[0],0,15) and integer(position[1],0,9));seen.add(item)
    daily=data.get('daily');require(isinstance(daily,dict))
    for day,value in daily.items():
        require(day_key(day) and isinstance(value,dict))
        require(all(type(value.get(k)) is bool for k in ('watered','arranged','harvested')))
        greeted=value.get('greeted');claimed=value.get('claimed')
        require(isinstance(greeted,list) and all(isinstance(p,str) and p in PARTNERS for p in greeted) and len(greeted)==len(set(greeted)))
        require(isinstance(claimed,list) and all(isinstance(k,str) and k in ('greet','water','arrange') for k in claimed) and len(claimed)==len(set(claimed)))
        require(('greet' not in claimed or bool(greeted)) and ('water' not in claimed or value['watered']) and ('arrange' not in claimed or value['arranged']))
    stats=data.get('stats');require(isinstance(stats,dict))
    require(all(day_key(k) and isinstance(v,dict) and integer(v.get('sessions')) and integer(v.get('minutes')) for k,v in stats.items()))
    validate_focus(data.get('focus'))
    if seen:
        from town_map import can_place
        for area,items in places.items():
            for item,(x,y) in items.items():require(can_place(data,area,inventory[item],x,y,ignore_id=item),'家具布局存在重叠或非法位置')
