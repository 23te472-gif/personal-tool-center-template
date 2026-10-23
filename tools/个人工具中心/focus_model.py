"""Focus time and rewards; no UI or background timers."""
from copy import deepcopy
import math, time

DURATIONS=(5,15,25,45)
SHOP={'盆栽':2,'地毯':3,'书架':5}

def default_focus():
    return dict(task='',duration=25,remaining=1500,active=False,berries=0,owned=[],partner='02-妙蛙种子')

def validate_focus(data):
    if not isinstance(data,dict):raise ValueError('小屋配置格式错误')
    if (type(data.get('duration')) is not int or data['duration'] not in DURATIONS
        or type(data.get('remaining')) is not int or not 0<=data['remaining']<=data['duration']*60
        or type(data.get('active')) is not bool or type(data.get('berries')) is not int or not 0<=data['berries']<=1000000
        or not isinstance(data.get('task'),str) or len(data['task'])>500
        or not isinstance(data.get('partner'),str) or len(data['partner'])>200
        or not isinstance(data.get('owned'),list) or any(not isinstance(x,str) or x not in SHOP for x in data['owned'])
        or len(data['owned'])!=len(set(data['owned']))):raise ValueError('小屋配置格式错误，原文件保留')

class FocusSession:
    def __init__(self,data,clock=time.monotonic):
        validate_focus(data);self.data=deepcopy(data);self.clock=clock;self.running=False;self.deadline=0
    @property
    def remaining(self):
        return max(0,math.ceil(self.deadline-self.clock())) if self.running else self.data['remaining']
    @property
    def berries(self):return self.data['berries']
    def start(self,task,minutes):
        if type(minutes) is not int or minutes not in DURATIONS:raise ValueError('请选择5、15、25或45分钟')
        if not isinstance(task,str) or len(task)>500:raise ValueError('任务文字请控制在500字以内')
        self.data.update(task=task.strip(),duration=minutes,remaining=minutes*60,active=True)
        self.deadline=self.clock()+minutes*60;self.running=True
    def pause(self):
        self.data['remaining']=self.remaining;self.running=False
    def resume(self):
        if not self.data['active']:raise ValueError('请先开始一个专注任务')
        if not self.running:self.deadline=self.clock()+self.data['remaining'];self.running=True
    def finish_early(self):
        self.pause();self.data['active']=False
    def tick(self):
        if self.running and self.remaining==0 and self.data['active']:
            self.pause();self.data['active']=False;self.data['berries']+=1;return True
        return False
    def snapshot(self):
        data=deepcopy(self.data);data['remaining']=self.remaining;return data
    def buy(self,decoration):
        if decoration not in SHOP:raise ValueError('未知装饰')
        if decoration in self.data['owned']:return
        if self.berries<SHOP[decoration]:raise ValueError('树果还不够，完成专注后再来吧')
        self.data['berries']-=SHOP[decoration];self.data['owned'].append(decoration)
