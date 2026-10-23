from copy import deepcopy
import uuid
from town_state import validate_town,validate_focus,require,SHOP,PARTNERS,default_day,day_key
from town_map import can_place

REWARDS={'greet':2,'water':3,'arrange':2}
def command(data,action,*,day,**args):
    validate_town(data);require(day_key(day),'日期格式不正确');draft=deepcopy(data);daily=draft['daily'].setdefault(day,default_day());message='已保存。'
    def achievement(key):
        if key not in draft['achievements']:draft['achievements'].append(key)
    if action=='buy':
        kind=args.get('kind');require(isinstance(kind,str) and kind in SHOP,'未知家具');name,cost=SHOP[kind]
        require(draft['berries']>=cost,'树果不够，可以先做每日任务。');require(len(draft['inventory'])<1000,'库存已满，请先整理。')
        draft['berries']-=cost;draft['inventory'][uuid.uuid4().hex]=kind;message=f'买到了{name}，请到“家具”页选中后在地图上摆放。'
    elif action=='unlock':
        require(args.get('area')=='orchard','没有这个可解锁区域。')
        if 'orchard' in draft['areas']:message='果园已经开放，欢迎来采果。'
        else:
            require(draft['berries']>=12,'解锁果园需要12树果。');draft['berries']-=12;draft['areas'].append('orchard');message='果园开放啦！每天可以采一次果。'
    elif action in ('place','move'):
        item=args.get('item_id');area=args.get('area');x=args.get('x');y=args.get('y')
        require(isinstance(item,str) and item in draft['inventory'],'这件家具不在库存里。')
        previous=next(((a,p[item]) for a,p in draft['placements'].items() if item in p),None)
        require((action=='move')==bool(previous),'先选择库存家具摆放，或选中已摆家具移动。')
        require(can_place(draft,area,draft['inventory'][item],x,y,ignore_id=item),'这里不能摆放：请避开建筑、树木、通道和其他家具。')
        if previous==(area,[x,y]):message='家具已经在这个位置。'
        else:
            for positions in draft['placements'].values():positions.pop(item,None)
            draft['placements'][area][item]=[x,y];daily['arranged']=True;achievement('place');message='布置完成！家具可以随时移动或收回。'
    elif action=='recall':
        item=args.get('item_id');require(any(item in places for places in draft['placements'].values()),'先选择一件已摆放的家具。')
        for places in draft['placements'].values():places.pop(item,None)
        message='家具已收回库存，没有损失。'
    elif action=='set_partner':
        partner=args.get('partner');require(partner in PARTNERS,'没有找到这位伙伴。');draft['partner']=partner;message='已换好主要伙伴。'
    elif action=='greet':
        partner=args.get('partner',draft['partner']);require(partner in PARTNERS,'没有找到这位伙伴。')
        if partner not in daily['greeted']:
            daily['greeted'].append(partner);draft['affinity'][partner]=min(100,draft['affinity'].get(partner,0)+5);achievement('friend');message='伙伴很开心！亲密度 +5，任务奖励可以领取了。'
        else:message='伙伴向你挥了挥手：今天也要轻松一点呀！'
    elif action=='water':
        message='庭院树今天已经喝饱水了。' if daily['watered'] else '给庭院树浇好了水，去任务页领取奖励吧。';daily['watered']=True
    elif action=='claim':
        task=args.get('task');require(isinstance(task,str) and task in REWARDS,'未知任务')
        ready=bool(daily['greeted']) if task=='greet' else daily['watered'] if task=='water' else daily['arranged']
        require(ready,'这个任务还没完成，先去小镇转转吧。')
        if task in daily['claimed']:message='这项奖励今天已经领过了。'
        else:daily['claimed'].append(task);draft['berries']+=REWARDS[task];message=f'收到 {REWARDS[task]} 树果！'
    elif action=='harvest':
        require('orchard' in draft['areas'],'先解锁果园。')
        if daily['harvested']:message='今天的果子已经采过，明天再来吧。'
        else:daily['harvested']=True;draft['berries']+=3;message='果园收获了 3 树果！'
    elif action in ('focus_update','focus_complete'):
        incoming=deepcopy(args.get('focus'));validate_focus(incoming);current=draft['focus']
        if current['active']:
            require(incoming['session_id']==current['session_id'] and incoming['duration']==current['duration'] and incoming['task']==current['task'],'专注任务已变化，请重新打开。')
            require(incoming['remaining']<=current['remaining'],'专注进度不能倒退。')
        if action=='focus_complete':
            require(current['active'] and incoming['active'] and incoming['remaining']==0 and incoming['session_id']==current['session_id'],'这次专注已结束或还没完成。')
            incoming['active']=False;reward=incoming['duration']//5;draft['berries']+=reward
            stat=draft['stats'].setdefault(day,dict(sessions=0,minutes=0));stat['sessions']+=1;stat['minutes']+=incoming['duration'];achievement('focus');message=f'专注完成！收获 {reward} 树果。'
        else:
            if not current['active'] and incoming['active']:require(incoming['session_id']!=current['session_id'],'请新建专注任务。')
            message='专注进度已保存。'
        draft['focus']=incoming
    else:raise ValueError('暂不支持这个操作。')
    validate_town(draft);return draft,message
