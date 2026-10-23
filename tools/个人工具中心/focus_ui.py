from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from focus_model import FocusSession,default_focus,validate_focus,SHOP,DURATIONS
from playful_store import load_json,save_json
from pokemon_assets import choices,load_preview
from playful_layout import size_window
from soft_background import SoftHeader,apply_palette

class FocusWindow:
    def __init__(self,parent,base):
        self.base=Path(base);self.path=self.base/'data/focus.json';self.timer=None;self.error='';self.image=None
        self.window=tk.Toplevel(parent);self.window.title('宝可梦专注小屋');size_window(self.window,780,760,700,690)
        self.window.configure(bg='#eef5ef');self.window.protocol('WM_DELETE_WINDOW',self.close)
        try:data=load_json(self.path,default_focus(),validate_focus)
        except (OSError,ValueError) as exc:self.error=str(exc);data=default_focus()
        self.session=FocusSession(data);self.pictures=choices(base)
        body=ttk.Frame(self.window,padding=22);body.pack(fill='both',expand=True)
        SoftHeader(body,'focus','把专注，种进小屋里','完成一段专注，收获一枚树果。关窗自动暂停，随时回来。').pack(fill='x',pady=(0,12))
        self.canvas=tk.Canvas(body,height=265,bg='#e8f0e7',highlightthickness=0);self.canvas.pack(fill='x')
        self.canvas.bind('<Configure>',lambda _:self.draw_room())
        row=ttk.Frame(body);row.pack(fill='x',pady=12)
        ttk.Label(row,text='小屋伙伴').pack(side='left')
        self.partner=tk.StringVar(value=data['partner']);combo=ttk.Combobox(row,textvariable=self.partner,values=list(self.pictures),state='readonly',width=23)
        combo.pack(side='left',padx=8);combo.bind('<<ComboboxSelected>>',lambda _:self.guard(self.change_partner))
        self.task=tk.StringVar(value=data['task']);ttk.Entry(body,textvariable=self.task).pack(fill='x')
        settings=ttk.Frame(body);settings.pack(fill='x',pady=10)
        self.minutes=tk.StringVar(value=str(data['duration']))
        ttk.Label(settings,text='专注分钟').pack(side='left');ttk.Combobox(settings,textvariable=self.minutes,values=DURATIONS,state='readonly',width=5).pack(side='left',padx=8)
        self.time_text=tk.StringVar();ttk.Label(settings,textvariable=self.time_text,font=('Microsoft YaHei UI',28,'bold'),foreground='#346a54').pack(side='right')
        buttons=ttk.Frame(body);buttons.pack(fill='x')
        for text,fn in [('开始新任务',self.start),('暂停 / 继续',self.toggle),('提前结束',self.end)]:
            ttk.Button(buttons,text=text,command=lambda fn=fn:self.guard(fn)).pack(side='left',padx=(0,8))
        shop=ttk.Frame(body);shop.pack(fill='x',pady=14)
        self.balance=tk.StringVar();ttk.Label(shop,textvariable=self.balance).pack(side='left',padx=(0,10))
        for item,cost in SHOP.items():ttk.Button(shop,text=f'{item} · {cost}树果',command=lambda item=item:self.guard(lambda:self.buy(item))).pack(side='left',padx=3)
        self.note=tk.StringVar(value=self.error or ('已为你保留暂停进度，点击“暂停 / 继续”恢复。' if data['active'] else '写下一个小任务，再开始。'))
        ttk.Label(body,textvariable=self.note,wraplength=690,foreground='#496855').pack(fill='x',pady=(5,0))
        apply_palette(self.window,'focus')
        self.window.bind('<Destroy>',self.cleanup,add='+');self.render()
    def guard(self,fn):
        try:
            if self.error:raise ValueError(self.error)
            fn()
        except Exception as exc:self.note.set(str(exc))
    def persist(self):save_json(self.path,self.session.snapshot(),default_focus(),validate_focus)
    def commit(self,action):
        old=self.session.snapshot();running=self.session.running
        try:action();self.persist()
        except Exception:
            self.session=FocusSession(old)
            if running:self.session.resume()
            raise
        self.render()
    def start(self):
        if self.session.data['active']:
            self.note.set('已有任务在进行，先继续或“提前结束”后再开始新任务。');return
        self.commit(lambda:self.session.start(self.task.get(),int(self.minutes.get())))
        self.note.set('专注进行中，让伙伴陪你一会儿。');self.schedule()
    def toggle(self):
        self.commit(self.session.pause if self.session.running else self.session.resume)
        self.note.set('专注进行中。' if self.session.running else '已暂停。');self.schedule()
    def end(self):
        self.commit(self.session.finish_early);self.note.set('已结束本次任务，提前结束不发树果。');self.schedule()
    def change_partner(self):
        self.commit(lambda:self.session.data.update(partner=self.partner.get()))
    def buy(self,item):
        self.commit(lambda:self.session.buy(item));self.note.set('装饰已摆进小屋。')
    def schedule(self):
        if self.timer:self.window.after_cancel(self.timer);self.timer=None
        if self.session.running:self.timer=self.window.after(1000,self.tick)
    def tick(self):
        self.timer=None
        old=self.session.snapshot()
        try:
            if self.session.tick():self.persist();self.note.set('专注完成！收获 1 枚树果。')
        except Exception as exc:
            self.session=FocusSession(old);self.note.set('保存失败，已暂停：'+str(exc))
        self.render();self.schedule()
    def render(self):
        seconds=self.session.remaining;self.time_text.set(f'{seconds//60:02d}:{seconds%60:02d}')
        self.balance.set(f'树果 {self.session.berries}');self.draw_room()
    def draw_room(self):
        c=self.canvas;c.delete('all');w=max(680,c.winfo_width());h=265
        c.create_rectangle(0,0,w,h,fill='#e7eee2',outline='');c.create_rectangle(0,196,w,h,fill='#d6bb96',outline='')
        c.create_rectangle(44,28,174,139,fill='#c2e1e5',outline='#fff8e9',width=9)
        c.create_oval(118,42,153,77,fill='#ffdb89',outline='');c.create_line(109,30,109,136,fill='#fff8e9',width=6)
        c.create_line(45,83,172,83,fill='#fff8e9',width=6)
        owned=self.session.data['owned']
        if '地毯' in owned:c.create_oval(w*.3,203,w*.76,252,fill='#a6bd9f',outline='#8aab85',width=3)
        if '盆栽' in owned:
            c.create_polygon(w-100,218,w-62,218,w-69,247,w-93,247,fill='#b4795c',outline='')
            for x,y in [(w-92,195),(w-66,193),(w-80,176)]:c.create_oval(x-14,y-17,x+14,y+17,fill='#699574',outline='')
        if '书架' in owned:
            c.create_rectangle(w-220,79,w-118,194,fill='#b18863',outline='')
            for y in (90,138):
                for i,color in enumerate(('#86a6bb','#b68b8e','#d8bf84','#7a9c91')):c.create_rectangle(w-210+i*21,y,w-194+i*21,y+40,fill=color,outline='')
        path=self.pictures.get(self.session.data['partner'])
        try:
            if path:
                if getattr(self,'image_path',None)!=path:self.image=load_preview(path,(170,174));self.image_path=path
                c.create_image(w*.51,164,image=self.image)
            else:c.create_text(w*.51,155,text='选择一位小屋伙伴',fill='#526b5c',font=('Microsoft YaHei UI',16))
        except (OSError,tk.TclError):c.create_text(w*.5,150,text='伙伴素材暂不可用',fill='#526b5c')
    def close(self):
        if not self.error:
            self.session.pause()
            try:self.persist()
            except (OSError,ValueError) as exc:self.note.set('保存失败，窗口已保留：'+str(exc));return False
        self.window.destroy();return True
    def cleanup(self,event):
        if event.widget==self.window and self.timer:self.window.after_cancel(self.timer);self.timer=None
