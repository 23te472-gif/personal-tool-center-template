"""Responsive icon cards, bounded to 60 widgets per page."""
import math
import tkinter as tk
from tkinter import ttk,font as tkfont

def short_name(font,text,width):
    lines=['']
    for char in text.replace('\n',' '):
        if font.measure(lines[-1]+char)>width:
            if len(lines)==2:
                while lines[-1] and font.measure(lines[-1]+'…')>width:lines[-1]=lines[-1][:-1]
                return '\n'.join(lines[:-1]+[lines[-1]+'…'])
            lines.append('')
        lines[-1]+=char
    return '\n'.join(lines)

class IconCards(ttk.Frame):
    PAGE=60
    def __init__(self,parent,checkable=False,on_toggle=None):
        super().__init__(parent)
        self.checkable=checkable;self.on_toggle=on_toggle;self.on_visible=None;self.on_activate=None
        self.items={};self.order=[];self.widgets={};self.page=0;self.selected_id=None;self.enabled=True;self.layout_timer=None
        self.icon_size=round(48*max(1,float(self.tk.call('tk','scaling'))/(96/72)))
        nav=ttk.Frame(self);nav.pack(side='bottom',fill='x',pady=(5,0));self.page_text=tk.StringVar()
        self.previous=ttk.Button(nav,text='上一页',command=lambda:self.change_page(-1));self.previous.pack(side='left')
        ttk.Label(nav,textvariable=self.page_text).pack(side='left',padx=12)
        self.next=ttk.Button(nav,text='下一页',command=lambda:self.change_page(1));self.next.pack(side='left')
        self.canvas=tk.Canvas(self,bg='#edf1f6',highlightthickness=0,height=210)
        bar=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview);bar.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=bar.set)
        self.inner=tk.Frame(self.canvas,bg='#edf1f6');self.inner_id=self.canvas.create_window((0,0),window=self.inner,anchor='nw')
        self.canvas.bind('<Configure>',self.queue_layout);self.inner.bind('<Configure>',self.queue_layout)
        self.bind('<Destroy>',self.cleanup,add='+');self.canvas.bind('<MouseWheel>',self.wheel)
    def visible_ids(self):return self.order[self.page*self.PAGE:(self.page+1)*self.PAGE]
    def set_items(self,items):
        previous=self.items
        self.items={item['id']:dict(item,image=previous.get(item['id'],{}).get('image') if previous.get(item['id'],{}).get('icon_key')==item.get('icon_key') else None) for item in items}
        self.order=list(self.items);self.page=min(self.page,max(0,(len(self.order)-1)//self.PAGE))
        if self.selected_id not in self.items:self.selected_id=None
        self.render()
    def render(self):
        visible=self.visible_ids()
        for key in list(self.widgets):
            if key not in visible:
                self.widgets.pop(key)['frame'].destroy()
                if key in self.items:self.items[key]['image']=None
        for key in visible:
            item=self.items[key]
            if key not in self.widgets:
                frame=tk.Frame(self.inner,bg='#ffffff',highlightthickness=2,highlightbackground='#dce3ed',padx=9,pady=8)
                slot=tk.Frame(frame,width=self.icon_size,height=self.icon_size,bg='#f1f3f7');slot.pack();slot.pack_propagate(False)
                icon=tk.Label(slot,bg='#f1f3f7',fg='#62728b',font='TkDefaultFont');icon.pack(fill='both',expand=True)
                label=tk.Label(frame,bg='#ffffff',fg='#263b56',font='TkDefaultFont',height=2,justify='center');label.pack(fill='x',pady=(7,3))
                record=dict(frame=frame,icon=icon,label=label)
                if self.checkable:
                    var=tk.BooleanVar(value=item.get('checked',False));check=tk.Checkbutton(frame,text='参与抽签',variable=var,command=lambda key=key:self.toggle(key),bg='#ffffff',activebackground='#e8eef8',font='TkDefaultFont')
                    check.pack();record.update(check=check,var=var)
                self.widgets[key]=record
                for child in (frame,slot,icon,label):
                    child.bind('<Button-1>',lambda _,key=key:self.select(key));child.bind('<Double-1>',lambda _,key=key:self.activate(key));child.bind('<MouseWheel>',self.wheel)
                label.bind('<Configure>',self.queue_layout)
            record=self.widgets[key]
            if 'var' in record:record['var'].set(item.get('checked',False));record['check'].configure(state='normal' if self.enabled else 'disabled')
            self.show_image(key,item.get('image'));self.highlight(key)
        total=max(1,math.ceil(len(self.order)/self.PAGE));self.page_text.set(f'{self.page+1} / {total} 页 · {len(self.order)} 项')
        self.previous.state(['!disabled'] if self.page and self.enabled else ['disabled']);self.next.state(['!disabled'] if self.page+1<total and self.enabled else ['disabled'])
        self.queue_layout()
        if self.on_visible:self.on_visible()
    def queue_layout(self,event=None):
        if self.layout_timer is None:self.layout_timer=self.after_idle(self.layout)
    def layout(self):
        self.layout_timer=None;width=self.canvas.winfo_width()
        if width<2:return
        if int(float(self.canvas.itemcget(self.inner_id,'width')))!=width:self.canvas.itemconfigure(self.inner_id,width=width)
        font=tkfont.nametofont('TkDefaultFont',root=self);desired=max(168,font.measure('游戏软件候选卡片')+32)
        columns=max(1,width//desired);cell=max(90,width//columns)
        for index,key in enumerate(self.visible_ids()):
            record=self.widgets[key];record['frame'].grid(row=index//columns,column=index%columns,sticky='nsew',padx=5,pady=5)
            # An explicit cell width keeps long titles from forcing columns wider.
            text=short_name(font,self.items[key]['name'],max(40,cell-42))
            if record['label'].cget('text')!=text:record['label'].configure(text=text,width=1)
            self.inner.columnconfigure(index%columns,weight=1,uniform='cards',minsize=cell)
        for column in range(columns,max(1,len(self.widgets))):self.inner.columnconfigure(column,weight=0,minsize=0,uniform='')
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    def selected(self):return self.selected_id
    def select(self,key):
        if not self.enabled or key not in self.items:return
        old=self.selected_id;self.selected_id=key
        if old:self.highlight(old)
        self.highlight(key)
        if old!=key:self.event_generate('<<CardSelected>>')
    def highlight(self,key):
        if key in self.widgets:self.widgets[key]['frame'].configure(highlightbackground='#4c79a8' if key==self.selected_id else '#dce3ed')
    def activate(self,key):
        self.select(key)
        if self.enabled and self.on_activate:self.on_activate()
    def toggle(self,key):
        self.select(key)
        if self.enabled and self.on_toggle:self.on_toggle(key)
        if key in self.widgets:self.widgets[key]['var'].set(self.items[key].get('checked',False))
    def wheel(self,event):
        self.canvas.yview_scroll(int(-event.delta/120),'units');return 'break'
    def set_enabled(self,value):self.enabled=value;self.render()
    def change_page(self,delta):
        page=self.page+delta
        if not self.enabled or not 0<=page<max(1,math.ceil(len(self.order)/self.PAGE)):return
        self.page=page;self.selected_id=None;self.canvas.yview_moveto(0);self.render();self.event_generate('<<CardSelected>>')
    def show_image(self,key,image):
        if key not in self.items:return
        self.items[key]['image']=image
        if key in self.widgets:
            label=self.widgets[key]['icon'];label.configure(image=image or '',text='' if image else self.items[key]['name'][:2])
    def cleanup(self,event):
        if event.widget==self and self.layout_timer:
            self.after_cancel(self.layout_timer);self.layout_timer=None
