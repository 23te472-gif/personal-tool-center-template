from copy import deepcopy
import math,time,uuid
from town_state import validate_focus,DURATIONS,require

class FocusClock:
    def __init__(self,focus,clock=time.monotonic):
        validate_focus(focus);self.value=deepcopy(focus);self.clock=clock;self.running=False;self.deadline=0
    @property
    def remaining(self):return max(0,math.ceil(self.deadline-self.clock())) if self.running else self.value['remaining']
    def start(self,task,minutes):
        require(not self.value['active'],'先继续或结束已有任务，再开始新任务。')
        require(isinstance(task,str) and len(task)<=500 and type(minutes) is int and minutes in DURATIONS,'请选择有效时长，任务文字不超过500字。')
        self.value.update(task=task.strip(),duration=minutes,remaining=minutes*60,active=True,session_id=uuid.uuid4().hex);self.running=True;self.deadline=self.clock()+minutes*60
    def pause(self):self.value['remaining']=self.remaining;self.running=False
    def resume(self):
        require(self.value['active'],'请先开始一个专注任务。')
        if not self.running:self.deadline=self.clock()+self.value['remaining'];self.running=True
    def end(self):self.pause();self.value['active']=False
    def snapshot(self):
        data=deepcopy(self.value);data['remaining']=self.remaining;return data
