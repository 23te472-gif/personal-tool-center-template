"""Thesis delivery checklist and verified packaging window."""
from pathlib import Path
from datetime import datetime
import ctypes,os,queue,sys,tempfile,threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from delivery import Project,Material,SCENES,ROLES,load_project,save_project,check_project,build_delivery,history
from ui_preferences import UIPreferences

def desktop():
    buf=ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None,0x10,None,0,buf)==0:return Path(buf.value)
    return Path.home()

class DeliveryApp:
    def __init__(self,root,base):
        self.root=root;self.base=Path(base);self.config=self.base/'data/project.json';self.busy=False;self.controls=[];self.events=queue.Queue();self.load_error=False;self.last_bundle=None
        self.project=Project(output=str(self.base/'deliveries'))
        if self.config.exists():
            try:self.project=load_project(self.config)
            except Exception as exc:self.load_error=True;messagebox.showerror('项目读取失败',str(exc),parent=root)
        root.title('论文交付助手 · 提交前再确认一次');root.geometry('1160x850');root.minsize(950,740);root.configure(bg='#f1f4f8')
        width=min(1160,max(850,root.winfo_screenwidth()-100));height=min(850,max(640,root.winfo_screenheight()-100))
        root.geometry(f'{width}x{height}');root.minsize(min(950,width),min(740,height))
        icon=Path(__file__).parent/'assets/app.ico'
        if icon.exists():root.iconbitmap(str(icon))
        style=ttk.Style(root);style.theme_use('clam');style.configure('.',font=('Microsoft YaHei UI',10),background='#f1f4f8',foreground='#25334a')
        style.configure('TButton',padding=(12,7));style.configure('Treeview',rowheight=30,background='#ffffff',fieldbackground='#ffffff');style.configure('Title.TLabel',font=('Microsoft YaHei UI',23,'bold'));style.configure('Primary.TButton',background='#294e80',foreground='white');style.map('Primary.TButton',background=[('active','#3b6497')])
        top=ttk.Frame(root,padding=(22,10));top.pack(fill='x')
        ttk.Label(top,text='论文交付助手',style='Title.TLabel').pack(anchor='w')
        ttk.Label(top,text='选定版本 · 检查材料 · 生成独立交付包').pack(anchor='w',pady=(4,0))
        form=ttk.Frame(root,padding=(22,0));form.pack(fill='x');form.columnconfigure(1,weight=1);form.columnconfigure(3,weight=1)
        self.name=tk.StringVar(value=self.project.name);self.scene=tk.StringVar(value=self.project.scene);self.output=tk.StringVar(value=self.project.output);self.pdf=tk.BooleanVar(value=self.project.require_pdf)
        ttk.Label(form,text='项目名称').grid(row=0,column=0,padx=(0,8),pady=6)
        self.entry(form,self.name).grid(row=0,column=1,sticky='ew',padx=(0,20))
        ttk.Label(form,text='提交场景').grid(row=0,column=2,padx=(0,8))
        combo=ttk.Combobox(form,textvariable=self.scene,values=list(SCENES),state='readonly',width=15);combo.grid(row=0,column=3,sticky='ew');self.controls.append((combo,'readonly'))
        ttk.Label(form,text='输出目录').grid(row=1,column=0,padx=(0,8),pady=6)
        self.entry(form,self.output).grid(row=1,column=1,columnspan=3,sticky='ew')
        self.button(form,'选择…',self.choose_output).grid(row=1,column=4,padx=(8,0))
        pdf=ttk.Checkbutton(form,text='必需材料须包含 PDF（只检查，不转换）',variable=self.pdf);pdf.grid(row=2,column=1,columnspan=3,sticky='w',pady=6);self.controls.append((pdf,'normal'))
        toolbar=ttk.Frame(root,padding=(22,10));toolbar.pack(fill='x')
        for text,fn in [('添加文件…',self.choose_files),('切换提交勾选',self.toggle_selected),('移除条目',self.remove_selected)]:self.button(toolbar,text,fn).pack(side='left',padx=(0,6))
        self.role=tk.StringVar(value='附件');role=ttk.Combobox(toolbar,textvariable=self.role,values=list(ROLES),state='readonly',width=7);role.pack(side='left',padx=(12,5));self.controls.append((role,'readonly'))
        self.button(toolbar,'设置分类',self.set_role).pack(side='left')
        self.button(toolbar,'保存项目',self.save).pack(side='right')
        frame=ttk.Frame(root,padding=(22,0));frame.pack(fill='both',expand=True)
        self.table=ttk.Treeview(frame,columns=('selected','role','name','modified','path'),show='headings',selectmode='extended',height=5)
        for col,label,width in [('selected','提交',55),('role','分类',65),('name','文件名',230),('modified','修改时间',155),('path','原文件位置',450)]:self.table.heading(col,text=label);self.table.column(col,width=width,minwidth=45,stretch=col in ('name','path'))
        vs=ttk.Scrollbar(frame,orient='vertical',command=self.table.yview);hs=ttk.Scrollbar(frame,orient='horizontal',command=self.table.xview);self.table.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        self.table.grid(row=0,column=0,sticky='nsew');vs.grid(row=0,column=1,sticky='ns');hs.grid(row=1,column=0,sticky='ew');frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
        self.table.bind('<Double-1>',lambda _:self.guard(self.toggle_selected))
        note=ttk.Frame(root,padding=(22,8));note.pack(fill='x');ttk.Label(note,text='交付备注').pack(side='left',padx=(0,8));self.notes=tk.StringVar(value=self.project.notes);self.entry(note,self.notes).pack(fill='x',expand=True)
        actions=ttk.Frame(root,padding=(22,4));actions.pack(fill='x')
        self.button(actions,'提交前检查',self.inspect).pack(side='left')
        self.button(actions,'生成交付包',self.build,primary=True).pack(side='left',padx=8)
        self.button(actions,'打开最新交付',self.open_last).pack(side='left')
        self.status=tk.StringVar(value='先添加材料、确认分类与提交勾选。原文件不会被改动。')
        ttk.Label(root,textvariable=self.status,wraplength=1080,padding=(22,8)).pack(fill='x')
        self.progress=ttk.Progressbar(root,mode='indeterminate');self.progress.pack(fill='x',padx=22)
        lower=ttk.Panedwindow(root,orient='horizontal');lower.pack(fill='both',padx=22,pady=(10,16))
        check=ttk.Labelframe(lower,text='检查结果 / 本次文件映射',padding=8);lower.add(check,weight=2)
        self.report=tk.Text(check,height=6,wrap='word',font=('Microsoft YaHei UI',10),bg='white',relief='flat',state='disabled');self.report.pack(fill='both',expand=True)
        hist=ttk.Labelframe(lower,text='交付记录（当前输出目录）',padding=8);lower.add(hist,weight=1)
        self.hist=ttk.Combobox(hist,state='readonly');self.hist.pack(fill='x')
        history_actions=ttk.Frame(hist);history_actions.pack(fill='x',pady=4)
        self.button(history_actions,'打开所选文件夹',self.open_history).pack(side='left')
        self.button(history_actions,'刷新记录',self.refresh_history).pack(side='left',padx=5)
        root.protocol('WM_DELETE_WINDOW',self.close);self.refresh();self.refresh_history();self.root.after(100,self.poll)
        self.ui_preferences=UIPreferences(root,self.base,self.status.set)
    def entry(self,parent,var):
        widget=ttk.Entry(parent,textvariable=var);self.controls.append((widget,'normal'));return widget
    def button(self,parent,text,fn,primary=False):
        b=ttk.Button(parent,text=text,command=lambda:self.guard(fn),style='Primary.TButton' if primary else 'TButton');self.controls.append((b,'normal'));return b
    def guard(self,fn):
        if self.busy:return
        try:return fn()
        except Exception as exc:self.status.set(str(exc));messagebox.showerror('操作未完成',str(exc),parent=self.root)
    def collect(self):
        return Project(self.name.get().strip(),self.scene.get(),self.output.get().strip(),self.pdf.get(),list(self.project.materials),self.notes.get())
    def save(self):
        if self.load_error:raise ValueError('原项目读取失败，请先备份并修复 data/project.json 后重新打开')
        project=self.collect();save_project(self.config,project);self.project=project;self.status.set('项目已保存；原文件保持不变。')
    def choose_output(self):
        path=filedialog.askdirectory(parent=self.root,title='选择交付输出目录')
        if path:self.output.set(path);self.save();self.refresh_history()
    def choose_files(self):
        paths=filedialog.askopenfilenames(parent=self.root,title='选择本次候选材料',initialdir=desktop()/'毕业论文' if (desktop()/'毕业论文').is_dir() else desktop())
        if paths:self.add_paths(paths)
    def add_paths(self,paths):
        existing={str(Path(m.path).resolve()).casefold() for m in self.project.materials}
        for name in paths:
            p=Path(name)
            if str(p.resolve()).casefold() in existing:continue
            suffix=p.suffix.lower();role='汇报' if suffix in ('.ppt','.pptx') else '论文' if suffix in ('.doc','.docx','.pdf') else '图表' if suffix in ('.png','.jpg','.jpeg','.svg') else '附件'
            self.project.materials.append(Material(str(p.resolve()),role));existing.add(str(p.resolve()).casefold())
        self.save();self.refresh()
    def refresh(self):
        selected=self.table.selection()
        self.table.delete(*self.table.get_children())
        for i,m in enumerate(self.project.materials):
            p=Path(m.path)
            try:modified=datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            except OSError:modified='文件缺失'
            self.table.insert('','end',iid=str(i),values=('✓' if m.selected else '—',m.role,p.name,modified,str(p)))
        for item in selected:
            if self.table.exists(item):self.table.selection_add(item)
    def toggle_selected(self):
        if self.busy:return
        for item in self.table.selection():self.project.materials[int(item)].selected=not self.project.materials[int(item)].selected
        self.save();self.refresh()
    def remove_selected(self):
        indices={int(item) for item in self.table.selection()};self.project.materials=[m for i,m in enumerate(self.project.materials) if i not in indices];self.save();self.refresh()
    def set_role(self):
        for item in self.table.selection():self.project.materials[int(item)].role=self.role.get()
        self.save();self.refresh()
    def inspect(self):
        result=check_project(self.collect());lines=[]
        lines += ['[需处理] '+m for m in result['errors']]
        lines += ['[提示] '+m for m in result['warnings']]
        if not result['errors']:lines.append('检查通过。请核对下列版本及文件映射后生成：')
        lines += [f'{row["relative"]} ← {row["source"]}' for row in result['files']]
        self.report.configure(state='normal');self.report.delete('1.0','end');self.report.insert('1.0','\n'.join(lines));self.report.configure(state='disabled')
        self.status.set(f'已选 {len(result["files"])} 个可用文件；需处理 {len(result["errors"])} 项，提示 {len(result["warnings"])} 项。');return result
    def start_busy(self):
        if self.busy:raise RuntimeError('请等待当前交付完成')
        self.busy=True
        for control,_ in self.controls:control.configure(state='disabled')
        self.progress.start(50)
    def build(self):
        result=self.inspect()
        if result['errors']:raise ValueError('检查尚未通过，请查看下方需处理项目')
        project=self.collect()
        if not messagebox.askyesno('确认交付版本',f'项目：{project.name}\n场景：{project.scene}\n文件：{len(result["files"])} 个\n输出：{project.output}\n\n请确认已选定正确版本。现在生成？',parent=self.root):return
        self.save();self.start_busy()
        def worker():
            try:self.events.put(('done',str(build_delivery(project,lambda m:self.events.put(('progress',m)),expected=result))))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=False).start()
    def poll(self):
        try:
            for _ in range(100):
                event=self.events.get_nowait()
                if event[0]=='progress':self.status.set(event[1]);continue
                self.busy=False;self.progress.stop()
                for control,state in self.controls:control.configure(state=state)
                if event[0]=='done':self.last_bundle=Path(event[1]);self.status.set('交付完成：'+event[1]);self.refresh_history()
                else:self.status.set('生成失败：'+event[1])
        except queue.Empty:pass
        self.root.after(80 if self.busy else 1200,self.poll)
    def refresh_history(self):
        output=self.output.get().strip();self.records=history(Path(output)) if output else []
        self.hist['values']=[f'{r.get("created","")} · {r.get("name","")} · {r.get("scene","")}' for r in self.records]
        if self.records:self.hist.current(0)
        else:self.hist.set('暂无交付记录')
    def open_last(self):
        if not self.last_bundle:raise ValueError('本次尚未生成交付包，可在下方查看以前的记录')
        os.startfile(str(self.last_bundle))
    def open_history(self):
        index=self.hist.current()
        if index<0:raise ValueError('请先选择一条交付记录')
        os.startfile(self.records[index]['path'])
    def close(self):
        if self.busy:messagebox.showinfo('正在生成交付包','请等待打包完成后再关闭。',parent=self.root)
        else:
            if not self.load_error:
                try:self.save()
                except Exception as exc:
                    messagebox.showerror('项目保存失败',f'{exc}\n窗口保持打开，请先保存项目。',parent=self.root);return
            self.root.destroy()

def main():
    from quick_ui import QuickPackApp
    root=tk.Tk()
    if '--smoke-test' in sys.argv:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            QuickPackApp(root,Path(directory));root.after(300,root.destroy);root.mainloop()
        print('Thesis delivery isolated smoke test passed')
    else:QuickPackApp(root,Path(__file__).resolve().parent);root.mainloop()

if __name__=='__main__':main()
