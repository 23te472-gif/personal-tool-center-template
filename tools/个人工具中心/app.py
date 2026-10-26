"""Common materials and independent launchers for the active local tools."""
from pathlib import Path
from datetime import datetime
import ctypes,os,sys,tempfile
import tkinter as tk
from tkinter import ttk,font as tkfont,messagebox
from center import tools_for,ToolManager,WindowsWindows,load_recent,save_recent
from ui_preferences import UIPreferences
from materials_ui import MaterialsPanel
from playful_tools import PlayfulTools

class ToolCenter:
    def __init__(self,root,base,manager=None):
        self.root=root;self.base=Path(base);self.tools=tools_for(base);self.manager=manager or ToolManager(base,self.tools)
        self.playful=PlayfulTools(root,self.base)
        self.recent_path=self.base/'data/recent.json';self.recent={};self.recent_error='';self.pending=set();self.last_states={};self.cards={};self.timer=None
        try:self.recent=load_recent(self.recent_path)
        except (OSError,ValueError) as exc:self.recent_error=str(exc)
        root.title('个人工具中心');root.configure(bg='#eef2f7')
        scale=max(1.0,float(root.tk.call('tk','scaling'))/(96/72))
        width=min(round(1030*scale),max(820,root.winfo_screenwidth()-80));height=min(round(790*scale),max(600,root.winfo_screenheight()-110))
        root.geometry(f'{width}x{height}');root.minsize(min(width,850),min(height,620))
        icon=self.base/'assets/app.ico'
        if icon.is_file():root.iconbitmap(str(icon))
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkIconFont','TkTooltipFont'):tkfont.nametofont(name,root=root).configure(family='Microsoft YaHei UI',size=11)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('.',font=('Microsoft YaHei UI',11),background='#eef2f7',foreground='#24334b')
        style.configure('Card.TFrame',background='#ffffff',bordercolor='#dce3ee',relief='solid',borderwidth=1)
        style.configure('Card.TLabel',background='#ffffff',foreground='#24334b')
        style.configure('Muted.Card.TLabel',background='#ffffff',foreground='#52647c',font=('Microsoft YaHei UI',10))
        style.configure('TButton',padding=(12,8),background='#ffffff',bordercolor='#cbd7e6',foreground='#24416a')
        style.map('TButton',background=[('active','#e5edf8'),('pressed','#d7e4f5')])
        style.configure('Primary.TButton',background='#315e93',foreground='#ffffff',font=('Microsoft YaHei UI',11,'bold'))
        style.map('Primary.TButton',background=[('active','#3e71ab'),('pressed','#244b78')])
        root.columnconfigure(0,weight=1);root.rowconfigure(1,weight=1)
        header=ttk.Frame(root,padding=(24,20));header.grid(row=0,column=0,sticky='ew')
        ttk.Label(header,text='个人工具中心',font=('Microsoft YaHei UI',24,'bold')).pack(anchor='w')
        ttk.Label(header,text='常用资料随手打开，也给专注与游戏留一点乐趣。',foreground='#52647c').pack(anchor='w',pady=(5,0))
        middle=ttk.Frame(root);middle.grid(row=1,column=0,sticky='nsew',padx=24)
        self.canvas=tk.Canvas(middle,bg='#eef2f7',highlightthickness=0);scroll=ttk.Scrollbar(middle,orient='vertical',command=self.canvas.yview);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=scroll.set)
        body=ttk.Frame(self.canvas);window=self.canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda event:self.canvas.itemconfigure(window,width=event.width))
        self.descriptions=[]
        fun=ttk.Frame(body,style='Card.TFrame',padding=18);fun.pack(fill='x',pady=(0,12))
        ttk.Label(fun,text='给日常一点乐趣',style='Card.TLabel',font=('Microsoft YaHei UI',17,'bold')).pack(anchor='w')
        ttk.Label(fun,text='按需打开，进度留在本机。',style='Muted.Card.TLabel').pack(anchor='w',pady=(4,12))
        tiles=ttk.Frame(fun,style='Card.TFrame',padding=0);tiles.pack(fill='x');self.fun_buttons={}
        for column,(key,title,note,color) in enumerate((('town','宝可梦小镇','布置家园 · 伙伴互动','#e6eee1'),('wheel','游戏转盘','今天玩什么 · 转一下','#eee7f5'),('icons','图标换装台','桌面伙伴 · 预览还原','#e4edf3'))):
            tiles.columnconfigure(column,weight=1,uniform='fun')
            tile=tk.Frame(tiles,bg=color,padx=12,pady=14);tile.grid(row=0,column=column,sticky='nsew',padx=(0,8) if column<2 else 0)
            button=ttk.Button(tile,text=title,command=lambda key=key:self.guard(lambda:self.open_tool(key) if key=='town' else self.playful.open(key)));button.pack(fill='x');self.fun_buttons[key]=button
            tk.Label(tile,text=note,bg=color,fg='#53647a',font=('Microsoft YaHei UI',10)).pack(pady=(8,0))
        self.materials=MaterialsPanel(body,self.base,lambda text:self.status.set(text))
        for tool in self.tools:
            if tool.id=='town':continue
            card=ttk.Frame(body,style='Card.TFrame',padding=18);card.pack(fill='x',pady=(0,12));card.columnconfigure(1,weight=1)
            badge=tk.Label(card,text=tool.symbol,font=('Microsoft YaHei UI',22,'bold'),bg=tool.color,fg='white',width=2,padx=7,pady=13)
            badge.grid(row=0,column=0,rowspan=3,padx=(0,18),sticky='n')
            ttk.Label(card,text=tool.name,style='Card.TLabel',font=('Microsoft YaHei UI',16,'bold')).grid(row=0,column=1,sticky='w')
            description=ttk.Label(card,text=tool.description,style='Muted.Card.TLabel',wraplength=500,justify='left');description.grid(row=1,column=1,sticky='ew',pady=7);self.descriptions.append(description)
            recent=tk.StringVar();ttk.Label(card,textvariable=recent,style='Muted.Card.TLabel').grid(row=2,column=1,sticky='w')
            actions=ttk.Frame(card,style='Card.TFrame',padding=0);actions.grid(row=0,column=2,rowspan=3,sticky='ne',padx=(15,0))
            open_button=ttk.Button(actions,text='打开工具',style='Primary.TButton',command=lambda key=tool.id:self.guard(lambda:self.open_tool(key)));open_button.pack(fill='x')
            ttk.Button(actions,text='打开所在目录',command=lambda key=tool.id:self.guard(lambda:self.open_folder(key))).pack(fill='x',pady=(7,0))
            state=tk.StringVar(value='尚未打开');ttk.Label(card,textvariable=state,style='Muted.Card.TLabel').grid(row=3,column=1,columnspan=2,sticky='w',pady=(8,0))
            self.cards[tool.id]={'frame':card,'recent':recent,'state':state,'button':open_button}
        def resize(event):
            for label in self.descriptions:label.configure(wraplength=max(160,event.width-350))
        self.canvas.bind('<Configure>',resize,add='+')
        root.bind('<MouseWheel>',lambda event:self.canvas.yview_scroll(int(-event.delta/120),'units'),add='+')
        footer=ttk.Frame(root,padding=(24,12));footer.grid(row=2,column=0,sticky='ew');footer.columnconfigure(0,weight=1)
        self.summary=tk.StringVar();ttk.Label(footer,textvariable=self.summary,wraplength=740,foreground='#52647c').grid(row=0,column=0,sticky='w')
        ttk.Button(footer,text='打开启动日志',command=lambda:self.guard(self.open_logs)).grid(row=0,column=1,padx=(12,0))
        self.status=tk.StringVar(value=self.recent_error or '关闭中心时，内置趣味窗口一并关闭；已打开的小镇、游戏管家和快速打包窗口继续运行。')
        ttk.Label(root,textvariable=self.status,wraplength=960,padding=(24,0,24,18),foreground='#344d6d').grid(row=3,column=0,sticky='ew')
        self.refresh_recent();root.protocol('WM_DELETE_WINDOW',self.close)
        def cleanup(event):
            if event.widget==root and self.timer:root.after_cancel(self.timer);self.timer=None
        root.bind('<Destroy>',cleanup,add='+');self.timer=root.after(300,self.poll)
        self.ui_preferences=UIPreferences(root,self.base,self.status.set)
    def guard(self,fn):
        try:return fn()
        except Exception as exc:self.status.set(str(exc));messagebox.showerror('操作未完成',str(exc),parent=self.root)
    def mark_recent(self,key):
        self.recent[key]=datetime.now().isoformat(timespec='seconds');self.refresh_recent()
        try:
            if self.recent_error:raise ValueError(self.recent_error)
            save_recent(self.recent_path,self.recent)
            return True
        except (OSError,ValueError) as exc:self.status.set(f'工具已打开，最近使用未保存：{exc}');return False
    def refresh_recent(self):
        names={t.id:t.name for t in self.tools}
        for key,card in self.cards.items():card['recent'].set('最近使用：'+self.recent.get(key,'暂无记录').replace('T',' '))
        ordered=sorted((k for k in self.recent if k in names),key=lambda k:self.recent[k],reverse=True)
        self.summary.set('最近使用：'+('  /  '.join(names[k] for k in ordered) if ordered else '打开任意工具后会显示在这里'))
    def open_tool(self,key):
        result=self.manager.open(key);self.status.set(result['message'])
        if result['action']=='started':self.pending.add(key)
        elif result['action']=='focused':self.mark_recent(key)
    def open_folder(self,key):
        tool=next(t for t in self.tools if t.id==key)
        if not tool.script.parent.is_dir():raise FileNotFoundError(f'工具目录不存在：{tool.script.parent}')
        os.startfile(str(tool.script.parent))
    def open_logs(self):
        folder=self.base/'logs'
        if not folder.exists():self.status.set('暂无启动日志。首次打开工具后会创建。');return
        os.startfile(str(folder))
    def poll(self):
        if self.timer:self.root.after_cancel(self.timer);self.timer=None
        try:
            for key,value in self.manager.poll().items():
                short={'idle':'尚未打开','starting':'启动中…','running':'已打开，可点击唤起','exited':'已关闭','failed':'启动或运行失败，查看启动日志'}[value['state']]
                if key in self.cards:self.cards[key]['state'].set(short)
                if value['state']=='running' and key in self.pending:self.pending.discard(key);self.mark_recent(key)
                if value['state']=='failed':
                    self.pending.discard(key)
                    if self.last_states.get(key)!='failed':self.status.set(next(t.name for t in self.tools if t.id==key)+'运行失败，请点击“打开启动日志”查看详情。')
                self.last_states[key]=value['state']
        except Exception as exc:self.status.set('状态读取失败：'+str(exc))
        interval=250 if self.pending else (5000 if self.root.state()=='iconic' else 2000)
        self.timer=self.root.after(interval,self.poll)
    def close(self):
        if self.materials.busy:
            self.status.set('资料正在打包，请完成后再关闭工具中心。');return
        if not self.playful.close_all():
            self.status.set('新功能仍在保存或更换图标，请查看子窗口提示后再关闭。');return
        self.root.destroy()

def main():
    smoke='--smoke-test' in sys.argv
    if os.name=='nt':
        try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (OSError,AttributeError):pass
    if not smoke:
        windows=WindowsWindows();existing=windows.find('个人工具中心')
        if existing:windows.focus(existing);return
    root=tk.Tk()
    if smoke:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            ToolCenter(root,Path(directory));root.after(350,root.destroy);root.mainloop()
        print('Tool center isolated smoke test passed; no tools launched')
    else:ToolCenter(root,Path(__file__).resolve().parent);root.mainloop()

if __name__=='__main__':
    raise SystemExit('旧窗口入口已停用，请运行根目录 start.cmd。')
