"""Native-authoritative town actions and monotonic focus clock; no OS launch API."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone,timedelta
import base64,io,json,logging,threading,time
from town_state import new_town,AREAS,SHOP,PARTNERS,DURATIONS,validate_town
from town_rules import command
from town_focus import FocusClock
from town_map import blocked,footprint
from town_store import TownRepository

BASE=Path(__file__).resolve().parent
UI_DEFAULT=dict(mode='town',theme='light',motion=True)
TOWN_ACTIONS={'buy','unlock','place','move','recall','set_partner','greet','water','claim','harvest'}
DESCRIPTIONS={'plant':'让房间多一点绿意','rug':'柔软的两格小地毯','bookshelf':'留一角给喜欢的书','bench':'坐下来歇一会儿','flowerbed':'种下一片小小花园','lamp':'傍晚也有温暖的光'}

def validate_ui(ui):
    if not isinstance(ui,dict) or ui.get('mode') not in ('town','focus') or ui.get('theme') not in ('light','dark') or type(ui.get('motion')) is not bool:raise ValueError('界面设置格式错误，原文件已保留')

class Bridge:
    def __init__(self,base=BASE,clock=time.monotonic,today=None):
        self._base=Path(base);self._clock=clock;self._today=today or (lambda:datetime.now(timezone(timedelta(hours=9))).date().isoformat())
        self._lock=threading.RLock();self._repo=TownRepository(self._base)
        self._data=self._repo.load();self._data.setdefault('ui',deepcopy(UI_DEFAULT));validate_ui(self._data['ui'])
        self._focus=FocusClock(self._data['focus'],clock);self._message='欢迎来到新的小镇。';self._catalog_value=None
        self._actions={name:getattr(self,'_'+name) for name in ('bootstrap','focus_state','town_action','focus_start','focus_pause','focus_resume','focus_end','set_mode','settings_save')}

    def call(self,action,payload=None):
        try:
            if not isinstance(action,str) or action not in self._actions:raise ValueError('不支持的操作')
            if payload is None:payload={}
            if not isinstance(payload,dict) or len(json.dumps(payload,ensure_ascii=False))>8192:raise ValueError('操作参数无效')
            with self._lock:
                self._settle();self._actions[action](payload);return dict(ok=True,data=self._snapshot())
        except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
            logging.getLogger('town').warning('Action %s failed: %s',action,exc)
            return dict(ok=False,error=str(exc) or '操作未完成，请重试。')
        except Exception:
            logging.getLogger('town').exception('Unexpected action failure')
            return dict(ok=False,error='操作未完成，详细原因已记入 logs/app.log。')

    def _clone_clock(self):
        clock=FocusClock(self._focus.snapshot(),self._clock)
        clock.running=self._focus.running;clock.deadline=self._focus.deadline
        return clock
    def _commit(self,draft,clock,message):
        draft=deepcopy(draft);draft['focus']=clock.snapshot();validate_town(draft);validate_ui(draft['ui'])
        # The deadline can cross between the initial settle check and pause/close.
        # Commit a finished active snapshot and its reward together, never paused at zero.
        if draft['focus']['active'] and draft['focus']['remaining']==0:
            draft,message=command(draft,'focus_complete',day=self._today(),focus=draft['focus'])
            clock=FocusClock(draft['focus'],self._clock)
        self._repo.save(draft)
        self._data=draft;self._focus=clock;self._message=message
    def _settle(self):
        if not (self._focus.running and self._focus.value['active'] and self._focus.remaining==0):return
        draft,message=command(self._data,'focus_complete',day=self._today(),focus=self._focus.snapshot())
        self._commit(draft,FocusClock(draft['focus'],self._clock),message)
    def _catalog(self):
        if self._catalog_value is None:
            partners=[]
            for partner in PARTNERS:
                image='';path=self._base/'assets/pokemon'/(partner+'.png')
                if path.is_file() and path.stat().st_size<=4*1024*1024:
                    try:
                        from PIL import Image
                        with Image.open(path) as source:
                            picture=source.convert('RGBA');picture.thumbnail((192,192),Image.Resampling.LANCZOS)
                            output=io.BytesIO();picture.save(output,format='PNG')
                        image='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode('ascii')
                    except (OSError,ValueError):logging.getLogger('town').warning('Partner image unreadable: %s',partner)
                partners.append(dict(id=partner,name=partner.split('-',1)[-1],image=image))
            self._catalog_value=dict(shop=[dict(id=key,name=value[0],cost=value[1],width=footprint(key)[0],height=footprint(key)[1],description=DESCRIPTIONS[key]) for key,value in SHOP.items()],partners=partners,areas=[dict(id=key,name=value,blocked=[list(cell) for cell in sorted(blocked(key))],unlock_cost=12 if key=='orchard' else 0) for key,value in AREAS.items()],durations=list(DURATIONS),map=dict(width=16,height=10))
        return self._catalog_value
    def _snapshot(self):
        town=deepcopy(self._data);town['focus']=self._focus.snapshot()
        return dict(app=dict(name='宝可梦小镇与专注',version='2.0.0'),town=town,focus=dict(self._focus.snapshot(),running=self._focus.running),catalog=self._catalog(),today=self._today(),settings=deepcopy(self._data['ui']),message=self._message)
    def _bootstrap(self,p):pass
    def _focus_state(self,p):pass
    def _town_action(self,p):
        action=p.get('action');args=p.get('args',{})
        if not isinstance(action,str) or action not in TOWN_ACTIONS or not isinstance(args,dict):raise ValueError('不支持的小镇操作')
        draft=deepcopy(self._data);clock=self._clone_clock();draft['focus']=clock.snapshot()
        draft,message=command(draft,action,day=self._today(),**args)
        self._commit(draft,clock,message)
    def _focus_start(self,p):
        clock=self._clone_clock();clock.start(p.get('task',''),p.get('minutes'))
        draft,message=command(self._data,'focus_update',day=self._today(),focus=clock.snapshot())
        self._commit(draft,clock,'专注开始，伙伴会陪着你。')
    def _focus_pause(self,p):
        if not self._focus.value['active']:return
        clock=self._clone_clock();clock.pause();self._commit(self._data,clock,'已暂停，随时可以继续。')
    def _focus_resume(self,p):
        clock=self._clone_clock();clock.resume();self._commit(self._data,clock,'继续专注。')
    def _focus_end(self,p):
        if not self._focus.value['active']:return
        clock=self._clone_clock();clock.end();self._commit(self._data,clock,'本次专注已提前结束，没有发放树果。')
    def _set_mode(self,p):
        mode=p.get('mode')
        if mode not in ('town','focus'):raise ValueError('未知界面模式')
        draft=deepcopy(self._data);draft['ui']['mode']=mode
        self._commit(draft,self._clone_clock(),'回到小镇。' if mode=='town' else '给自己一段安静的时间。')
    def _settings_save(self,p):
        draft=deepcopy(self._data);draft['ui'].update(theme=p.get('theme'),motion=p.get('motion'));validate_ui(draft['ui'])
        self._commit(draft,self._clone_clock(),'界面设置已保存。')
    def _pause_for_close(self):
        with self._lock:
            self._settle();clock=self._clone_clock();clock.pause();self._commit(self._data,clock,'已保存，欢迎下次再来。')
