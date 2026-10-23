"""Local game library. Worker threads never access Tk widgets."""
from pathlib import Path
from dataclasses import replace
from datetime import datetime
import os
import ctypes
import queue
import sys
import tempfile
import threading
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from library import Game, load_library, save_library, library_revision
from discovery import scan_candidates
from actions import open_path
from snapshots import create_backup, list_backups, export_backup
from trainers import ordered_games,excluded,tool_info,scan_trainers,merge_trainers
from steam_library import detect_steam_roots,read_steam_games
from ui_preferences import UIPreferences

def filter_games(games, query):
    q=query.strip().casefold()
    return [g for g in games if q in (' '.join([g.name,g.english_name,g.notes]+g.aliases+[Path(p).name for p in g.tool_paths])).casefold()]

def confirm_candidate(candidate, confirmed):
    if not confirmed or candidate.kind=='目录': return None
    return Game(uuid.uuid4().hex,candidate.name,
                candidate.path if candidate.kind=='入口' else '',
                [candidate.path] if candidate.kind=='工具' else [])

class TaskState:
    def __init__(self): self.busy=False; self.message='准备就绪'
    @property
    def can_close(self): return not self.busy
    def start(self):
        if self.busy: raise RuntimeError('请等待当前任务完成')
        self.busy=True
    def finish(self, success, message): self.busy=False; self.message=message

def desktop_path():
    buffer=ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None,0x10,None,0,buffer)!=0:
        raise OSError('无法取得桌面目录')
    return Path(buffer.value)

class App:
    def __init__(self, root, base):
        self.root=root; self.base=base; self.library=base/'data/library.json'
        self.state=TaskState(); self.events=queue.Queue(); self.games=[]; self.visible=[]; self.buttons=[]
        self.load_error=False
        try:
            self.games=load_library(self.library);self.library_revision=self.games.revision
        except Exception as exc: self.load_error=True; messagebox.showerror('资料库读取失败',str(exc),parent=root)
        root.title('游戏管家 · 修改器管理')
        display_scale=max(1.0,float(root.tk.call('tk','scaling'))/(96/72))
        width=min(round(1140*display_scale),max(900,root.winfo_screenwidth()-80));height=min(round(800*display_scale),max(640,root.winfo_screenheight()-110))
        root.geometry(f'{width}x{height}');root.minsize(min(1000,width),min(round(740*display_scale),height))
        icon=Path(__file__).parent/'assets/app.ico'
        if icon.exists():root.iconbitmap(str(icon))
        root.configure(bg='#101522')
        style=ttk.Style(root); style.theme_use('clam')
        font=('Microsoft YaHei UI',11)
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkIconFont','TkTooltipFont'):
            tkfont.nametofont(name,root=root).configure(family=font[0],size=font[1])
        root.option_add('*TCombobox*Listbox.font',font)
        root.option_add('*TCombobox*Listbox.background','#142137');root.option_add('*TCombobox*Listbox.foreground','#f2f5fc')
        style.configure('.',font=font,background='#192235',foreground='#f2f5fc')
        style.configure('TButton',font=font,padding=(12,8),background='#293b56',foreground='#f2f5fc',bordercolor='#425572',focuscolor='#91baff')
        style.map('TButton',background=[('disabled','#202c40'),('pressed','#24446b'),('active','#354f74')],foreground=[('disabled','#8e9fb8')])
        style.configure('Primary.TButton',background='#3769ad',foreground='#ffffff',font=('Microsoft YaHei UI',11,'bold'))
        style.map('Primary.TButton',background=[('disabled','#293b56'),('pressed','#234f88'),('active','#447ac0')])
        for name in ('TEntry','TCombobox'):
            style.configure(name,font=font,padding=6,fieldbackground='#101b2d',foreground='#f2f5fc',bordercolor='#425572',arrowcolor='#c6d7ee',insertcolor='#ffffff')
            style.map(name,fieldbackground=[('readonly','#142137'),('disabled','#202c40')],foreground=[('disabled','#8e9fb8'),('readonly','#f2f5fc')])
        style.configure('Treeview',font=font,background='#162136',fieldbackground='#162136',foreground='#f2f5fc',rowheight=max(36,tkfont.Font(root=root,font=font).metrics('linespace')+14),bordercolor='#354760')
        style.configure('Treeview.Heading',font=('Microsoft YaHei UI',11,'bold'),background='#293b56',foreground='#f2f5fc',padding=(8,7),bordercolor='#425572')
        style.map('Treeview',background=[('selected','#355f99')],foreground=[('selected','#ffffff')])
        style.map('Treeview.Heading',background=[('active','#354f74')])
        style.configure('Vertical.TScrollbar',background='#526983',troughcolor='#162136',arrowcolor='#e1eafa',bordercolor='#192235')
        header=ttk.Frame(root,padding=20); header.pack(fill='x')
        ttk.Label(header,text='游戏管家',font=('Microsoft YaHei UI',24,'bold')).pack(anchor='w')
        ttk.Label(header,text='中文找游戏 · 英文修改器自动归组 · 常用优先').pack(anchor='w',pady=(5,0))
        bar=ttk.Frame(root,padding=(20,10)); bar.pack(fill='x')
        self.query=tk.StringVar(); ttk.Entry(bar,textvariable=self.query,width=30).pack(side='left',fill='x',expand=True)
        self.query.trace_add('write',lambda *_:self.refresh())
        for label,action in [('扫描修改器 / Steam',self.scan),('添加游戏',self.add),('编辑',self.edit),('移除',self.remove)]: self.button(bar,label,action).pack(side='left',padx=4)
        main=ttk.Frame(root,padding=(20,5)); main.pack(fill='both',expand=True)
        self.list=ttk.Treeview(main,show='tree',selectmode='browse',height=14); self.list.column('#0',width=240)
        self.list.pack(side='left',fill='both'); scroll=ttk.Scrollbar(main,orient='vertical',command=self.list.yview);scroll.pack(side='left',fill='y');self.list.configure(yscrollcommand=scroll.set); self.list.bind('<<TreeviewSelect>>',lambda _:self.show())
        detail_shell=ttk.Frame(main);detail_shell.pack(side='left',fill='both',expand=True,padx=(12,0))
        self.detail_canvas=tk.Canvas(detail_shell,bg='#192235',highlightthickness=0);detail_scroll=ttk.Scrollbar(detail_shell,orient='vertical',command=self.detail_canvas.yview);detail_scroll.pack(side='right',fill='y');self.detail_canvas.pack(side='left',fill='both',expand=True);self.detail_canvas.configure(yscrollcommand=detail_scroll.set)
        detail=ttk.Frame(self.detail_canvas,padding=14);window=self.detail_canvas.create_window((0,0),window=detail,anchor='nw')
        detail.bind('<Configure>',lambda _:self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox('all')))
        self.detail_canvas.bind('<Configure>',lambda e:self.detail_canvas.itemconfigure(window,width=e.width))
        def wheel(event):
            x,y=self.detail_canvas.winfo_rootx(),self.detail_canvas.winfo_rooty()
            if x<=event.x_root<x+self.detail_canvas.winfo_width() and y<=event.y_root<y+self.detail_canvas.winfo_height() and event.widget!=self.tool_table:self.detail_canvas.yview_scroll(int(-event.delta/120),'units')
        root.bind('<MouseWheel>',wheel,add='+')
        self.title=ttk.Label(detail,text='选择一款游戏',font=('Microsoft YaHei UI',20,'bold')); self.title.pack(anchor='w')
        self.info=ttk.Label(detail,text='扫描修改器，建立中英文游戏列表。',wraplength=660,justify='left'); self.info.pack(fill='x',pady=10)
        row=ttk.Frame(detail); row.pack(fill='x')
        for label,action in [('打开常用修改器',self.open_preferred),('收藏 / 取消',self.toggle_favorite),('启动游戏',self.launch)]: self.button(row,label,action).pack(side='left',padx=(0,6))
        ttk.Label(detail,text='修改器版本（版本来自文件名，不自动判断兼容性）',font=('Microsoft YaHei UI',11,'bold')).pack(anchor='w',pady=(14,6))
        self.tools=ttk.Frame(detail); self.tools.pack(fill='x');self.tool_items=[]
        self.tool_table=ttk.Treeview(self.tools,columns=('version','modified','name'),show='headings',height=3,selectmode='browse')
        for col,label,width in [('version','版本',140),('modified','修改时间',135),('name','文件名',320)]:self.tool_table.heading(col,text=label);self.tool_table.column(col,width=width,minwidth=70)
        tool_scroll=ttk.Scrollbar(self.tools,orient='vertical',command=self.tool_table.yview);self.tool_table.configure(yscrollcommand=tool_scroll.set);tool_scroll.pack(side='right',fill='y');self.tool_table.pack(fill='x')
        self.tool_table.bind('<Double-1>',lambda _:self.guard(self.open_tool))
        row=ttk.Frame(detail);row.pack(fill='x',pady=7)
        for label,action in [('打开所选修改器',self.open_tool),('设为常用版本',self.set_preferred),('打开所在目录',self.open_tool_folder)]:self.button(row,label,action).pack(side='left',padx=(0,6))
        ttk.Label(detail,text='游戏目录与存档',font=('Microsoft YaHei UI',12,'bold')).pack(anchor='w',pady=(10,6))
        row=ttk.Frame(detail);row.pack(fill='x',pady=(0,6))
        for label,action in [('打开游戏目录',self.open_game_folder),('打开存档',self.open_save),('备份存档',self.backup)]:self.button(row,label,action).pack(side='left',padx=(0,6))
        self.archives=ttk.Combobox(detail,state='readonly'); self.archives.pack(fill='x')
        row=ttk.Frame(detail); row.pack(fill='x',pady=8)
        self.button(row,'导出备份到空目录',self.export).pack(side='left')
        self.button(row,'打开备份位置',self.open_backups).pack(side='left',padx=8)
        self.status=tk.StringVar(value='搜索中文、英文或别名。Cheat Engine / WeMod 已排除。常用置顶，其他按最近使用排列。')
        ttk.Label(root,textvariable=self.status,wraplength=1000,padding=15).pack(fill='x')
        self.progress=ttk.Progressbar(root,mode='indeterminate'); self.progress.pack(fill='x',padx=20,pady=(0,15))
        root.protocol('WM_DELETE_WINDOW',self.close); self._poll_timer=root.after(100,self.poll); self.refresh()
        def cleanup(event):
            if event.widget==root and self._poll_timer:
                root.after_cancel(self._poll_timer);self._poll_timer=None
        root.bind('<Destroy>',cleanup,add='+')
        self.ui_preferences=UIPreferences(root,self.base,self.status.set)

    def button(self,parent,label,action):
        b=ttk.Button(parent,text=label,command=lambda:self.guard(action),style='Primary.TButton' if label=='打开常用修改器' else 'TButton'); self.buttons.append(b); return b
    def guard(self,action):
        if self.state.busy: return
        try: action()
        except Exception as exc: self.status.set(str(exc)); messagebox.showerror('操作未完成',str(exc),parent=self.root)
    def selected(self):
        ids=self.list.selection()
        if not ids: raise ValueError('请先选择游戏')
        return next(g for g in self.games if g.id==ids[0])
    def persist(self,games):
        if self.load_error: raise ValueError('原资料库读取失败，请先备份并修复 data/library.json 后重新打开')
        try:save_library(self.library,games,expected_revision=self.library_revision)
        except ValueError:
            self.games=load_library(self.library);self.library_revision=self.games.revision;self.refresh()
            raise
        self.games=load_library(self.library);self.library_revision=self.games.revision;self.refresh()
    def refresh(self):
        current=self.list.selection(); self.list.delete(*self.list.get_children())
        self.visible=ordered_games(filter_games(self.games,self.query.get()))
        for g in self.visible: self.list.insert('', 'end',iid=g.id,text=('★ ' if g.favorite else '  ')+g.name)
        if current and self.list.exists(current[0]): self.list.selection_set(current[0])
        elif self.visible: self.list.selection_set(self.visible[0].id)
        self.show()
    def show(self):
        self.tool_table.delete(*self.tool_table.get_children());self.tool_items=[]
        self.archive_paths=[]; self.archives['values']=(); self.archives.set('')
        try: g=self.selected()
        except ValueError:
            self.title.config(text='选择一款游戏'); self.info.config(text='添加游戏，或扫描桌面上的入口和资料。'); return
        self.title.config(text=g.name)
        steam=f'Steam 已关联 · AppID {g.steam_appid} · {g.steam_install}' if g.steam_appid else 'Steam：本地未匹配（不影响使用修改器）'
        self.info.config(text=f'{g.english_name or "可编辑英文名 / 别名"}\n{steam}\n最近打开修改器：{g.last_used or "尚无记录"}\n{g.notes[:180] or "可在编辑中记录攻略、快捷键或版本备注。"}')
        self.tool_items=[p for p in g.tool_paths if not excluded(p)]
        for i,p in enumerate(self.tool_items):
            info=tool_info(p);self.tool_table.insert('','end',iid=str(i),values=(('★ ' if p==g.preferred_tool else '')+info['version'],info['modified'],info['name']))
        if self.tool_items:self.tool_table.selection_set(str(self.tool_items.index(g.preferred_tool)) if g.preferred_tool in self.tool_items else '0')
        self.archive_paths=list_backups(self.base/'backups',g.id)
        self.archives['values']=[p.stem for p in self.archive_paths]
        if self.archive_paths: self.archives.current(0)
        if self.state.busy:
            for b in self.buttons: b.state(['disabled'])
    def add(self): self.editor(Game(uuid.uuid4().hex,'新游戏'))
    def edit(self): self.editor(self.selected())
    def update_game(self,new):
        self.persist([new if g.id==new.id else g for g in self.games])
    def toggle_favorite(self):
        g=self.selected();self.update_game(replace(g,favorite=not g.favorite))
    def selected_tool(self):
        rows=self.tool_table.selection()
        if not rows:raise ValueError('请先选择修改器版本')
        return self.tool_items[int(rows[0])]
    def launch_tool(self,path):
        if excluded(path):raise ValueError('Cheat Engine / WeMod 不在本次辅助启动范围')
        g=self.selected();open_path(Path(path))
        self.update_game(replace(g,last_used=datetime.now().isoformat(timespec='seconds')))
        self.status.set(f'已请求打开修改器：{Path(path).name}')
    def open_tool(self):self.launch_tool(self.selected_tool())
    def open_preferred(self):
        g=self.selected();paths=[p for p in g.tool_paths if not excluded(p)]
        if not paths:raise ValueError('尚未关联修改器，请扫描或编辑添加')
        self.launch_tool(g.preferred_tool if g.preferred_tool in paths else paths[0])
    def set_preferred(self):
        path=self.selected_tool();g=self.selected();self.update_game(replace(g,preferred_tool=path));self.status.set('已设置常用修改器：'+Path(path).name)
    def open_tool_folder(self):open_path(Path(self.selected_tool()).parent)
    def open_game_folder(self):
        g=self.selected()
        if not g.steam_install:raise ValueError('尚未关联 Steam 安装目录，请先扫描 Steam')
        path=Path(g.steam_install)
        if not path.is_dir():raise ValueError('游戏安装目录不存在，可能已移动或卸载，请重新扫描 Steam')
        open_path(path)
    def editor(self,g):
        win=tk.Toplevel(self.root); win.title('编辑游戏')
        scale=max(1.0,float(self.root.tk.call('tk','scaling'))/(96/72))
        win.geometry(f'{min(round(780*scale),self.root.winfo_screenwidth()-80)}x{min(round(740*scale),self.root.winfo_screenheight()-100)}');win.transient(self.root);win.grab_set()
        canvas=tk.Canvas(win,bg='#192235',highlightthickness=0);scroll=ttk.Scrollbar(win,orient='vertical',command=canvas.yview);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True);canvas.configure(yscrollcommand=scroll.set)
        form=ttk.Frame(canvas,padding=20);window=canvas.create_window((0,0),window=form,anchor='nw')
        form.bind('<Configure>',lambda _:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        win.bind('<MouseWheel>',lambda e:canvas.yview_scroll(int(-e.delta/120),'units') if not isinstance(e.widget,tk.Text) else None,add='+')
        values={}
        for label,key,value in [('中文 / 显示名称','name',g.name),('英文名称','english_name',g.english_name),('游戏入口（可选，已关联 Steam 时无需填写）','launch_path',g.launch_path),('存档目录','save_dir',g.save_dir)]:
            ttk.Label(form,text=label).pack(anchor='w',pady=(8,3)); row=ttk.Frame(form); row.pack(fill='x')
            var=tk.StringVar(value=value); values[key]=var; ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
            if key in ('launch_path','save_dir'):
                def browse(k=key,v=var):
                    p=filedialog.askdirectory(parent=win) if k=='save_dir' else filedialog.askopenfilename(parent=win)
                    if p:v.set(p)
                ttk.Button(row,text='选择…',command=browse).pack(side='left')
        ttk.Label(form,text='其他别名（用英文逗号分隔，也可用于搜索）').pack(anchor='w',pady=(8,3))
        aliases=tk.StringVar(value=', '.join(g.aliases));ttk.Entry(form,textvariable=aliases).pack(fill='x')
        ttk.Label(form,text='修改器路径（每行一个；不启动 Cheat Engine / WeMod）').pack(anchor='w',pady=(12,4))
        tools=tk.Text(form,height=3,font=('Microsoft YaHei UI',11),bg='#101b2d',fg='#f2f5fc',insertbackground='#ffffff',selectbackground='#355f99',padx=7,pady=5,relief='solid',borderwidth=1); tools.pack(fill='x'); tools.insert('1.0','\n'.join(g.tool_paths))
        def tool_add():
            p=filedialog.askopenfilename(parent=win)
            if p: tools.insert('end',('\n' if tools.get('1.0','end-1c') else '')+p)
        ttk.Button(form,text='选择工具…',command=tool_add).pack(anchor='w',pady=4)
        ttk.Label(form,text='备注').pack(anchor='w'); notes=tk.Text(form,height=3,font=('Microsoft YaHei UI',11),bg='#101b2d',fg='#f2f5fc',insertbackground='#ffffff',selectbackground='#355f99',padx=7,pady=5,relief='solid',borderwidth=1); notes.pack(fill='both',expand=True); notes.insert('1.0',g.notes)
        def save():
            try:
                paths=[p.strip() for p in tools.get('1.0','end-1c').splitlines() if p.strip()]
                new=replace(g,**{k:v.get().strip() for k,v in values.items()},aliases=[a.strip() for a in aliases.get().replace('，',',').split(',') if a.strip()],tool_paths=paths,preferred_tool=g.preferred_tool if g.preferred_tool in paths else next((p for p in paths if not excluded(p)),''),notes=notes.get('1.0','end-1c'))
                self.persist([x for x in self.games if x.id!=g.id]+[new]); self.query.set(''); self.list.selection_set(new.id); win.destroy()
            except Exception as exc: messagebox.showerror('保存失败',str(exc),parent=win)
        ttk.Button(form,text='保存卡片',command=save).pack(anchor='e',pady=12)
    def remove(self):
        g=self.selected()
        if messagebox.askyesno('移除卡片',f'移除“{g.name}”的记录？原文件和备份保留。',parent=self.root): self.persist([x for x in self.games if x.id!=g.id])
    def scan(self):
        desktop=desktop_path(); roots=[desktop/'游戏入口',desktop/'游戏资料'/'修改']
        roots=[p for p in roots if p.is_dir()]
        if not roots: raise ValueError('桌面未找到游戏入口或游戏资料/修改目录')
        paths,warnings=scan_trainers(roots);steam,steam_warnings=read_steam_games(detect_steam_roots())
        candidates=merge_trainers(self.games,paths,steam)
        win=tk.Toplevel(self.root); win.title('修改器归组 · 确认后保存'); win.geometry('1000x560'); win.transient(self.root); win.grab_set()
        summary=f'发现 {len(paths)} 个修改器，读取 {len(steam)} 条 Steam 游戏记录；已排除 CE / WeMod。选择要保存或更新的游戏。'
        ttk.Label(win,text=summary,padding=12,wraplength=950).pack(fill='x')
        tree=ttk.Treeview(win,columns=('english','count','steam'),show='tree headings',selectmode='extended'); tree.heading('#0',text='中文显示名称');tree.column('#0',width=230); tree.heading('english',text='英文名');tree.column('english',width=330);tree.heading('count',text='修改器数');tree.column('count',width=80);tree.heading('steam',text='Steam 关联');tree.column('steam',width=200);tree.pack(fill='both',expand=True,padx=12)
        for c in candidates:tree.insert('','end',iid=c.id,text=c.name,values=(c.english_name,len([p for p in c.tool_paths if not excluded(p)]),c.steam_appid or '本地未匹配'))
        tree.selection_set([g.id for g in candidates if any(p in [str(path) for path in paths] for p in g.tool_paths)])
        if warnings or steam_warnings:ttk.Label(win,text='扫描提示：'+'；'.join(warnings+steam_warnings),wraplength=950,padding=8).pack(fill='x')
        def accept():
            try:
                selected=set(tree.selection());updated={g.id:g for g in candidates if g.id in selected}
                games=[updated.pop(g.id,g) for g in self.games]+list(updated.values())
                self.persist(games);self.status.set(f'已保存 / 更新 {len(selected)} 款游戏；没有运行修改器或 Steam。');win.destroy()
            except Exception as exc: messagebox.showerror('导入失败',str(exc),parent=win)
        ttk.Button(win,text='确认保存所选游戏',command=accept).pack(pady=12)
    def launch(self):
        g=self.selected()
        if g.steam_appid:
            if not g.steam_appid.isdecimal():raise ValueError('无效 Steam 游戏标识')
            os.startfile('steam://rungameid/'+g.steam_appid);return
        if not g.launch_path: raise ValueError('请编辑卡片并选择游戏入口')
        if excluded(g.launch_path):raise ValueError('Cheat Engine / WeMod 不在启动范围')
        open_path(Path(g.launch_path))
    def open_save(self):
        g=self.selected()
        if not g.save_dir: raise ValueError('请先编辑并确认存档目录')
        open_path(Path(g.save_dir))
    def open_backups(self):
        folder=self.base/'backups'/self.selected().id
        if not folder.exists(): raise ValueError('尚未创建备份')
        open_path(folder)
    def run_task(self,fn):
        self.state.start()
        for b in self.buttons:b.state(['disabled'])
        self.progress.start(50)
        def worker():
            try:self.events.put(('done',True,str(fn())))
            except Exception as exc:self.events.put(('done',False,str(exc)))
        threading.Thread(target=worker,daemon=False).start()
    def backup(self):
        g=self.selected()
        if not g.save_dir: raise ValueError('请先编辑并确认存档目录')
        if messagebox.askyesno('确认备份',f'存档来源：{g.save_dir}\n备份位置：{self.base / "backups"}\n\n建议先关闭游戏，是否开始？',parent=self.root):
            self.run_task(lambda:create_backup(Path(g.save_dir),self.base/'backups',g.id,lambda m:self.events.put(('progress',m))))
    def export(self):
        index=self.archives.current()
        if index<0:raise ValueError('请先选择备份')
        archive=self.archive_paths[index]; target=filedialog.askdirectory(title='选择空目录用于导出',parent=self.root)
        if target:self.run_task(lambda:(export_backup(archive,Path(target)) or f'已导出至 {target}'))
    def poll(self):
        if self._poll_timer:self.root.after_cancel(self._poll_timer);self._poll_timer=None
        try:
            while True:
                event=self.events.get_nowait()
                if event[0]=='progress': self.status.set(event[1])
                else:
                    self.state.finish(event[1],event[2]); self.progress.stop()
                    for b in self.buttons:b.state(['!disabled'])
                    self.status.set(('完成：' if event[1] else '失败：')+event[2]); self.show()
        except queue.Empty:pass
        self._poll_timer=self.root.after(80 if self.state.busy else 1200,self.poll)
    def close(self):
        if not self.state.can_close: messagebox.showinfo('任务进行中','请等待备份或导出完成后再关闭。',parent=self.root)
        else:self.root.destroy()

def main():
    if os.name=='nt':
        try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError,OSError):pass
    root=tk.Tk()
    if '--smoke-test' in sys.argv:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
            app=App(root,Path(temp)); root.after(300,root.destroy); root.mainloop()
        print('游戏管家隔离启动检查通过')
    else:App(root,Path(__file__).resolve().parent); root.mainloop()

if __name__=='__main__':main()
