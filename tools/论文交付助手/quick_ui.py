from pathlib import Path
import json,os,queue,tempfile,threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,font
from quickpack import create_zip
from ui_preferences import UIPreferences

class QuickPackApp:
    def __init__(self,root,base):
        self.root=root;self.base=Path(base);self.config=self.base/'data/quick_pack.json';self.files=[];self.last_zip=None;self.busy=False;self.events=queue.Queue();self.timer=None;self.config_error=''
        root.title('论文交付助手 · 快速打包');root.geometry('780x560');root.minsize(650,470);root.configure(bg='#f1f4f8')
        icon=self.base/'assets/app.ico'
        if icon.exists():root.iconbitmap(str(icon))
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont'):font.nametofont(name,root=root).configure(family='Microsoft YaHei UI',size=11)
        style=ttk.Style(root);style.theme_use('clam');style.configure('.',font=('Microsoft YaHei UI',11),background='#f1f4f8',foreground='#25334a');style.configure('TButton',padding=(14,9));style.configure('Primary.TButton',background='#315e93',foreground='white',font=('Microsoft YaHei UI',13,'bold'),padding=(18,18));style.map('Primary.TButton',background=[('active','#4175ad'),('disabled','#8093ac')])
        output=str(self.base/'压缩包')
        try:
            if self.config.exists():
                data=json.loads(self.config.read_text(encoding='utf-8'))
                if not isinstance(data,dict) or not isinstance(data.get('output'),str) or not isinstance(data.get('files'),list) or not all(isinstance(p,str) for p in data['files']):raise ValueError('快速打包设置格式错误')
                output=data['output'];self.files=data['files']
        except (OSError,ValueError) as exc:self.config_error=str(exc)
        self.output=tk.StringVar(value=output)
        panel=ttk.Frame(root,padding=(24,22));panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='快速文件打包',font=('Microsoft YaHei UI',22,'bold')).pack(anchor='w')
        ttk.Label(panel,text='选几个文件，直接得到一个 ZIP。',foreground='#52647c').pack(anchor='w',pady=(8,22))
        self.choose=ttk.Button(panel,text='选择文件并打包',style='Primary.TButton',command=lambda:self.guard(self.choose_and_pack));self.choose.pack(fill='x')
        row=ttk.Frame(panel);row.pack(fill='x',pady=12)
        self.repeat=ttk.Button(row,text='再次打包上次文件',command=lambda:self.guard(self.pack_last));self.repeat.pack(side='left')
        self.folder=ttk.Button(row,text='打开压缩包文件夹',command=lambda:self.guard(self.open_folder));self.folder.pack(side='left',padx=8)
        self.last_files=tk.StringVar();ttk.Label(panel,textvariable=self.last_files,wraplength=700,foreground='#52647c').pack(anchor='w',pady=(0,12))
        ttk.Label(panel,text='保存位置').pack(anchor='w')
        row=ttk.Frame(panel);row.pack(fill='x',pady=6);ttk.Entry(row,textvariable=self.output,state='readonly').pack(side='left',fill='x',expand=True)
        self.change=ttk.Button(row,text='更改…',command=lambda:self.guard(self.change_output));self.change.pack(side='left',padx=(8,0))
        self.bar=ttk.Progressbar(panel,mode='indeterminate');self.bar.pack(fill='x',pady=(12,8))
        self.status=tk.StringVar(value=self.config_error or '不要求分类、PDF或填写提交清单；原文件保持不变。')
        ttk.Label(panel,textvariable=self.status,wraplength=700).pack(anchor='w',fill='x')
        self.controls=[self.choose,self.repeat,self.change];self.refresh_files()
        root.protocol('WM_DELETE_WINDOW',self.close);self.timer=root.after(200,self.poll)
        def cleanup(event):
            if event.widget==root and self.timer:root.after_cancel(self.timer);self.timer=None
        root.bind('<Destroy>',cleanup,add='+');self.ui_preferences=UIPreferences(root,self.base,self.status.set)
    def guard(self,fn):
        if self.busy:return
        try:fn()
        except Exception as exc:self.status.set(str(exc));messagebox.showerror('未能打包',str(exc),parent=self.root)
    def refresh_files(self):
        names=[Path(p).name for p in self.files]
        self.last_files.set('上次选择：'+('、'.join(names[:4])+('…' if len(names)>4 else '')+f'（共 {len(names)} 个）' if names else '暂无'))
        self.repeat.configure(state='normal' if self.files and not self.busy else 'disabled')
    def choose_and_pack(self):
        files=filedialog.askopenfilenames(parent=self.root,title='选好文件后直接开始打包')
        if files:self.start_pack(list(files))
    def pack_last(self):
        if not self.files:raise ValueError('请先选择文件打包一次')
        self.start_pack(list(self.files))
    def start_pack(self,files):
        if self.busy:return
        output=self.output.get().strip()
        if not output:raise ValueError('请选择保存位置')
        self.busy=True
        for b in self.controls:b.configure(state='disabled')
        self.bar.start(50)
        def worker():
            try:self.events.put(('done',str(create_zip(files,Path(output),lambda m:self.events.put(('progress',m)))),files))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=False).start()
    def save(self):
        if self.config_error:self.status.set('设置未保存，原设置文件保持不变：'+self.config_error);return
        temporary=None
        try:
            self.config.parent.mkdir(parents=True,exist_ok=True);fd,temporary=tempfile.mkstemp(dir=self.config.parent,suffix='.tmp')
            with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump({'output':self.output.get(),'files':self.files},stream,ensure_ascii=False,indent=2)
            os.replace(temporary,self.config)
        except OSError as exc:self.status.set('操作已完成；设置未保存：'+str(exc))
        finally:
            if temporary:Path(temporary).unlink(missing_ok=True)
    def change_output(self):
        path=filedialog.askdirectory(parent=self.root,title='选择保存压缩包的文件夹')
        if path:self.output.set(path);self.save()
    def open_folder(self):
        path=self.last_zip.parent if self.last_zip else Path(self.output.get())
        if not path.is_dir():raise ValueError('还没有压缩包，请先打包一次')
        os.startfile(str(path))
    def poll(self):
        if self.timer:self.root.after_cancel(self.timer);self.timer=None
        try:
            for _ in range(50):
                event=self.events.get_nowait()
                if event[0]=='progress':self.status.set(event[1]);continue
                self.busy=False;self.bar.stop()
                for b in self.controls:b.configure(state='normal')
                if event[0]=='done':
                    self.last_zip=Path(event[1]);self.files=event[2];self.status.set('已生成：'+str(self.last_zip));self.save()
                else:self.status.set('打包失败：'+event[1])
                self.refresh_files()
        except queue.Empty:pass
        self.timer=self.root.after(100 if self.busy else 1200,self.poll)
    def close(self):
        if self.busy:messagebox.showinfo('正在打包','请等待压缩完成后再关闭。',parent=self.root)
        else:self.root.destroy()
