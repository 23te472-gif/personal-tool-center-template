from pathlib import Path
from copy import deepcopy
import os,queue,random,threading,uuid,math
import tkinter as tk
from tkinter import ttk,simpledialog
from playful_store import load_json,save_json
from wheel_model import default_wheel,validate_wheel,draw,candidates
from wheel_steam import import_installed
from playful_layout import size_window
from icon_cards import IconCards
from card_images import CardImages
from game_icons import GameImages
from soft_background import SoftHeader,apply_palette,tint_cards,motifs

CHALLENGES=('先体验20分钟，再决定要不要继续。','试试一个平常不常用的玩法。','给今天的游戏时刻留一张截图。','今天只追一个小目标，轻松玩。')

class WheelWindow:
    def __init__(self,parent,base):
        self.base=Path(base);self.path=self.base/'data/wheel.json';self.timer=None;self.busy=False;self.closed=False;self.error='';self.result=None
        self.window=tk.Toplevel(parent);self.window.title('今天玩什么 · 游戏转盘');size_window(self.window,900,780,760,670)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        try:self.data=load_json(self.path,default_wheel(),validate_wheel)
        except (OSError,ValueError) as exc:self.error=str(exc);self.data=default_wheel()
        body=ttk.Frame(self.window,padding=22);body.pack(fill='both',expand=True)
        SoftHeader(body,'wheel','把选择交给一点运气','只抽你勾选的候选；抽中后，由你决定是否启动。').pack(fill='x',pady=(0,12))
        self.canvas=tk.Canvas(body,height=210,bg='#ece9f5',highlightthickness=0);self.canvas.pack(fill='x')
        self.disc_entries=[];self.disc_angle=0
        self.result_text=self.canvas.create_text(410,90,text='今天，玩点什么？',font=('Microsoft YaHei UI',24,'bold'),fill='#5e4f80',width=680)
        self.hint_text=self.canvas.create_text(410,163,text='勾选候选，然后转一下',font=('Microsoft YaHei UI',11),fill='#776a91')
        self.canvas.bind('<Configure>',self.resize)
        row=ttk.Frame(body);row.pack(fill='x',pady=12);self.controls=[]
        for text,fn in [('导入已安装 Steam 游戏',self.import_games),('添加自定义',self.add),('改名',self.rename),('移除',self.remove),('勾选 / 取消',self.toggle)]:
            button=ttk.Button(row,text=text,command=lambda fn=fn:self.guard(fn));button.pack(side='left',padx=(0,5));self.controls.append(button)
        self.cards=IconCards(body,checkable=True,on_toggle=lambda key:self.guard(self.toggle));self.cards.pack(fill='both',expand=True)
        self.card_loader=CardImages(self.cards,GameImages());self.cards.on_activate=lambda:self.guard(self.toggle)
        self.cards.bind('<<CardSelected>>',lambda _:self.show_selected_name())
        options=ttk.Frame(body);options.pack(fill='x',pady=10)
        self.exclude=tk.BooleanVar(value=self.data['exclude_recent']);self.challenge=tk.BooleanVar(value=self.data['challenge'])
        for text,var in [('排除最近抽中的三项',self.exclude),('附一个轻量挑战',self.challenge)]:
            button=ttk.Checkbutton(options,text=text,variable=var,command=lambda:self.guard(self.settings));button.pack(side='left',padx=(0,15));self.controls.append(button)
        actions=ttk.Frame(body);actions.pack(fill='x')
        self.spin_button=ttk.Button(actions,text='转一下',style='Primary.TButton',command=lambda:self.guard(self.spin));self.spin_button.pack(side='left')
        self.launch_button=ttk.Button(actions,text='启动抽中的游戏',command=lambda:self.guard(self.launch),state='disabled');self.launch_button.pack(side='left',padx=10)
        self.note=tk.StringVar(value=self.error or '首次使用请导入 Steam 游戏，或者添加自己的候选。')
        note_label=ttk.Label(body,textvariable=self.note,wraplength=800,foreground='#665880')
        # Reserve the action/status area before giving remaining height to cards.
        self.cards.pack_forget();options.pack_forget();actions.pack_forget()
        note_label.pack(side='bottom',fill='x',pady=(10,0))
        actions.pack(side='bottom',fill='x');options.pack(side='bottom',fill='x',pady=10)
        self.cards.pack(fill='both',expand=True);self.refresh()
        apply_palette(self.window,'wheel');tint_cards(self.cards,'wheel')
        self.window.bind('<Destroy>',self.cleanup,add='+')
    def resize(self,event):
        motifs(self.canvas,'wheel',event.width,event.height)
        for item in (self.result_text,self.hint_text):
            self.canvas.coords(item,220+max(150,event.width-220)/2,self.canvas.coords(item)[1]);self.canvas.itemconfigure(item,width=max(150,event.width-250))
        self.draw_disc()
    def draw_disc(self):
        c=self.canvas;c.delete('disc');names=[item['name'] for item in self.disc_entries] or ['?']*6
        colors=('#c6b7de','#b0cfca','#e0c2c3','#c6d3e4','#dfcf9f','#c2d4b0','#d6bed5','#b9cdd6');extent=360/len(names)
        for index,name in enumerate(names):
            angle=self.disc_angle+index*extent
            c.create_arc(24,16,204,196,start=angle,extent=extent,fill=colors[index%len(colors)],outline='#faf8ff',width=2,tags='disc')
            middle=math.radians(angle+extent/2)
            c.create_text(114+59*math.cos(middle),106-59*math.sin(middle),text=name[:4],font=('Microsoft YaHei UI',8),fill='#49536a',tags='disc')
        c.create_oval(85,77,143,135,fill='#faf8ff',outline='',tags='disc')
        c.create_text(114,106,text='好运',font=('Microsoft YaHei UI',10,'bold'),fill='#6a5884',tags='disc')
        c.create_polygon(105,5,123,5,114,27,fill='#71598f',outline='',tags='disc')
    def guard(self,fn):
        try:
            if self.error:raise ValueError(self.error)
            return fn()
        except Exception as exc:self.note.set(str(exc))
    def save(self,value):
        save_json(self.path,value,default_wheel(),validate_wheel);self.data=value
    def refresh(self):
        self.cards.set_items([dict(id=item['id'],name=item['name'],appid=item['appid'],checked=item['enabled'],icon_key='steam-'+item['appid'] if item['appid'] else item['id']) for item in self.data['entries']])
    def show_selected_name(self):
        key=self.cards.selected()
        if key in self.cards.items:self.note.set('已选中：'+self.cards.items[key]['name']+'。勾选卡片下方的“参与抽签”调整候选。')
    def selected(self):
        key=self.cards.selected()
        if not key:raise ValueError('先选择一张游戏卡片。')
        return key
    def edit(self,fn):
        if self.busy:return
        value=deepcopy(self.data);fn(value);self.save(value);self.refresh();self.result=None;self.launch_button.state(['disabled'])
    def add(self):
        if self.busy:return
        name=simpledialog.askstring('添加候选','填写游戏或想做的事情：',parent=self.window)
        if name and name.strip():self.edit(lambda data:data['entries'].append(dict(id='custom-'+uuid.uuid4().hex,name=name.strip(),appid='',enabled=True)))
    def rename(self):
        if self.busy:return
        key=self.selected();name=simpledialog.askstring('改名','填写显示名称：',parent=self.window)
        if name and name.strip():self.edit(lambda data:next(x for x in data['entries'] if x['id']==key).update(name=name.strip()))
    def remove(self):
        key=self.selected();self.edit(lambda data:data.update(entries=[x for x in data['entries'] if x['id']!=key]))
    def toggle(self):
        key=self.selected()
        def change(data):
            item=next(x for x in data['entries'] if x['id']==key);item['enabled']=not item['enabled']
        self.edit(change)
    def settings(self):
        if self.busy:return
        try:self.edit(lambda data:data.update(exclude_recent=self.exclude.get(),challenge=self.challenge.get()))
        except Exception:
            self.exclude.set(self.data['exclude_recent']);self.challenge.set(self.data['challenge']);raise
    def set_busy(self,busy):
        self.busy=busy
        self.cards.set_enabled(not busy)
        for control in self.controls+[self.spin_button]:control.state(['disabled'] if busy else ['!disabled'])
        self.launch_button.state(['disabled'])
    def import_games(self):
        if self.busy:return
        self.set_busy(True);self.note.set('正在读取本地 Steam 安装清单…');events=queue.SimpleQueue();existing=deepcopy(self.data['entries'])
        def worker():
            try:events.put((True,import_installed(self.base,existing)))
            except Exception as exc:events.put((False,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
        def poll():
            self.timer=None
            if self.closed:return
            try:okay,value=events.get_nowait()
            except queue.Empty:self.timer=self.window.after(150,poll);return
            self.set_busy(False)
            def apply():
                if not okay:raise ValueError(value)
                entries,warnings=value;updated=deepcopy(self.data);updated['entries']=entries;self.save(updated);self.refresh()
                self.note.set(f'现在有 {len(entries)} 个候选。'+((' 部分清单不可读：'+'；'.join(warnings)[:400]) if warnings else '勾选卡片下方的“参与抽签”调整候选。'))
            self.guard(apply)
        self.timer=self.window.after(100,poll)
    def spin(self):
        if self.busy:return
        chosen=draw(self.data['entries'],self.data['recent'],self.data['exclude_recent']);pool=candidates(self.data['entries'],self.data['recent'],self.data['exclude_recent'])
        self.disc_entries=[chosen]+[x for x in pool if x['id']!=chosen['id']][:7]
        self.canvas.itemconfigure(self.hint_text,text='扇区仅展示部分候选，全部勾选项均参与抽签。' if len(pool)>8 else '指针停下的，就是今天的候选。')
        start=self.disc_angle;target=start+1080+((90-180/len(self.disc_entries)-start)%360)
        self.result=None;self.set_busy(True);self.note.set('转动中…');frame=[0]
        def animate():
            self.timer=None
            if self.closed:return
            frame[0]+=1
            fraction=min(1,frame[0]/45);self.disc_angle=start+(target-start)*(1-(1-fraction)**3);self.draw_disc()
            if frame[0]<45:
                self.canvas.itemconfigure(self.result_text,text=random.choice(pool)['name']);self.timer=self.window.after(45,animate);return
            self.set_busy(False)
            def finish():
                value=deepcopy(self.data);value['recent']=(value['recent']+[chosen['id']])[-3:];self.save(value)
                self.result=chosen;self.canvas.itemconfigure(self.result_text,text=chosen['name'])
                self.note.set(random.choice(CHALLENGES) if self.data['challenge'] else '抽签完成，祝你玩得开心。')
                if chosen['appid']:self.launch_button.state(['!disabled'])
            self.guard(finish)
        animate()
    def launch(self):
        if self.busy or not self.result or not self.result['appid']:raise ValueError('当前结果没有关联可启动的 Steam 游戏。')
        appid=self.result['appid']
        if not appid.isascii() or not appid.isdigit():raise ValueError('无效Steam标识')
        os.startfile('steam://rungameid/'+appid)
    def close(self):
        self.closed=True;self.window.destroy();return True
    def cleanup(self,event):
        if event.widget==self.window:
            self.closed=True
            if self.timer:self.window.after_cancel(self.timer);self.timer=None
