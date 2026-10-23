from pathlib import Path
from copy import deepcopy
import queue,threading,logging
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from shortcut_model import ShortcutService
from pokemon_assets import find_collection,load_preview
from playful_layout import size_window
from icon_cards import IconCards
from card_images import CardImages
from soft_background import SoftHeader,apply_palette,tint_cards

class ShortcutWindow:
    def __init__(self,parent,base):
        self.base=Path(base);self.service=ShortcutService(base);self.busy=False;self.working=False;self.closed=False;self.timer=None;self.items={};self.images=[]
        self.window=tk.Toplevel(parent);self.window.title('桌面宝可梦换装台');size_window(self.window,1050,750,910,680);self.window.protocol('WM_DELETE_WINDOW',self.close)
        icon=self.base/'assets/app.ico'
        if icon.is_file():self.window.iconbitmap(str(icon))
        body=ttk.Frame(self.window,padding=22);body.pack(fill='both',expand=True)
        SoftHeader(body,'icons','给桌面，换一位伙伴','选择软件和宝可梦，预览后再应用。仅修改桌面直接显示的普通软件快捷方式。').pack(fill='x',pady=(0,12))
        main=ttk.Frame(body);main.pack(fill='both',expand=True);main.columnconfigure(0,weight=3);main.columnconfigure(1,weight=2);main.rowconfigure(0,weight=1)
        left=ttk.Frame(main);left.grid(row=0,column=0,sticky='nsew',padx=(0,20));left.rowconfigure(1,weight=1);left.columnconfigure(0,weight=1)
        ttk.Label(left,text='桌面软件',font=('Microsoft YaHei UI',13,'bold')).grid(row=0,column=0,sticky='w',pady=(0,8))
        self.cards=IconCards(left);self.cards.grid(row=1,column=0,sticky='nsew');self.cards.bind('<<CardSelected>>',lambda _:self.preview())
        self.card_loader=CardImages(self.cards,self.read_card_image)
        right=ttk.Frame(main,padding=14,style='Card.TFrame');right.grid(row=0,column=1,sticky='nsew');right.columnconfigure(0,weight=1)
        ttk.Label(right,text='伙伴素材',style='Card.TLabel',font=('Microsoft YaHei UI',13,'bold')).pack(anchor='w')
        self.collection=find_collection(base);self.icons={};self.selection=tk.StringVar()
        self.combo=ttk.Combobox(right,textvariable=self.selection,state='readonly',width=27);self.combo.pack(fill='x',pady=10);self.combo.bind('<<ComboboxSelected>>',lambda _:self.preview())
        current_box=tk.Frame(right,height=120,bg='#f1f3f7');current_box.pack(fill='x');current_box.pack_propagate(False)
        self.current=tk.Label(current_box,text='当前图标',bg='#f1f3f7');self.current.pack(fill='both',expand=True)
        ttk.Label(right,text='↓ 换成 ↓',style='Card.TLabel').pack(pady=8)
        proposed_box=tk.Frame(right,height=120,bg='#f0f3e9');proposed_box.pack(fill='x');proposed_box.pack_propagate(False)
        self.proposed=tk.Label(proposed_box,text='选择宝可梦',bg='#f0f3e9');self.proposed.pack(fill='both',expand=True)
        ttk.Button(right,text='选择其他素材文件夹',command=self.choose_collection).pack(fill='x',pady=12)
        self.detail=tk.StringVar(value='先从左侧选择一个软件。');ttk.Label(right,textvariable=self.detail,style='Muted.Card.TLabel',wraplength=300).pack(fill='x')
        controls=ttk.Frame(body);controls.pack(fill='x',pady=(16,0));self.buttons=[]
        for text,fn in [('刷新软件',self.refresh),('应用图标',self.apply),('还原选中项',self.restore),('还原本工具修改的全部',self.restore_all)]:
            button=ttk.Button(controls,text=text,command=fn,style='Primary.TButton' if text=='应用图标' else 'TButton');button.pack(side='left',padx=(0,9));self.buttons.append(button)
        self.note=tk.StringVar(value='读取桌面软件中…');ttk.Label(body,textvariable=self.note,wraplength=970,foreground='#52647c').pack(fill='x',pady=(12,0))
        apply_palette(self.window,'icons');tint_cards(self.cards,'icons')
        self.load_collection();self.window.bind('<Destroy>',self.cleanup,add='+');self.refresh()
    def update_actions(self):
        ready=not self.working and self.cards.selected() is not None
        self.buttons[1].state(['!disabled'] if ready and self.icons.get(self.selection.get()) else ['disabled'])
        self.buttons[2].state(['!disabled'] if ready else ['disabled'])
    def load_collection(self):
        self.icons={p.stem:p for p in sorted(self.collection.glob('*.ico'))} if self.collection else {}
        self.combo.configure(values=list(self.icons))
        self.selection.set(next(iter(self.icons),''))
    def choose_collection(self):
        if self.working:return
        value=filedialog.askdirectory(parent=self.window,title='选择宝可梦ICO素材文件夹')
        if value:self.collection=Path(value);self.load_collection();self.preview()
    def selected(self):
        key=self.cards.selected()
        if key is None:raise ValueError('请先选择一张软件卡片。')
        return self.items[key]
    def read_card_image(self,item):
        from win_icons import shortcut_image
        return shortcut_image(self.items.get(item['path'],item),self.cards.icon_size)
    def run(self,action,done,mutating=False):
        if self.working:return
        self.working=True;self.busy=mutating
        self.cards.set_enabled(not mutating)
        for button in self.buttons:button.state(['disabled'])
        self.combo.state(['disabled']);events=queue.SimpleQueue()
        def worker():
            try:events.put((True,action()))
            except Exception as exc:
                logging.getLogger('icon-studio').exception('Icon operation failed')
                events.put((False,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
        def poll():
            self.timer=None
            if self.closed:return
            try:okay,value=events.get_nowait()
            except queue.Empty:self.timer=self.window.after(150,poll);return
            self.busy=False;self.working=False
            self.cards.set_enabled(True)
            for button in self.buttons:button.state(['!disabled'])
            self.combo.state(['!disabled','readonly'])
            if okay:
                try:done(value)
                except Exception as exc:self.note.set(str(exc))
            else:self.note.set('未完成：'+value)
            self.update_actions()
        self.timer=self.window.after(100,poll)
    def refresh(self,message=''):
        if self.working:return
        self.note.set('读取用户桌面和公共桌面；不打开任何目标软件…')
        def finish(items):
            self.items={};cards=[]
            for item in items:
                key=item['path'];self.items[key]=item;cards.append(dict(id=key,name=Path(item['path']).stem,path=item['path'],icon_key=item['path']+'\n'+item.get('icon','')))
            self.cards.set_items(cards)
            self.note.set(message or f'找到 {len(items)} 个普通软件快捷方式。子文件夹、目录入口和特殊入口不在此列表。')
            if self.cards.selected():self.preview()
        self.run(self.service.scan,finish)
    def preview(self):
        if self.working:return
        self.update_actions()
        self.images=[];self.current.configure(image='',height=7,text='当前图标');self.proposed.configure(image='',height=7,text='选择宝可梦')
        icon=self.icons.get(self.selection.get())
        try:
            if icon:
                png=icon.with_suffix('.png');picture=load_preview(png if png.is_file() else icon,(110,110));self.images.append(picture);self.proposed.configure(image=picture,height=120,text='')
            item=self.selected();self.detail.set(Path(item['path']).stem+'\n'+item['path'])
        except ValueError:return
        except Exception as exc:self.note.set('素材预览失败：'+str(exc));return
        path=item['path']
        def read_image():
            from win_icons import shortcut_image
            return shortcut_image(item,110)
        def finish(image):
            if self.cards.selected() is None or self.selected()['path']!=path:
                self.preview();return
            if image is not None:
                from PIL import ImageTk
                picture=ImageTk.PhotoImage(image);self.images.append(picture);self.current.configure(image=picture,height=120,text='')
        self.run(read_image,finish)
    def apply(self):
        if self.working:return
        try:
            item=deepcopy(self.selected());icon=self.icons.get(self.selection.get())
            if not icon:raise ValueError('先选择一张宝可梦素材。')
        except ValueError as exc:self.note.set(str(exc));return
        self.note.set('正在备份、应用和核对，请稍候…')
        def finish(_):self.refresh('已应用并保留备份。重新选中此软件后，可点击“还原选中项”恢复。')
        self.run(lambda:self.service.apply(item['path'],icon,item),finish,mutating=True)
    def restore(self):
        if self.working:return
        try:item=self.selected()
        except ValueError as exc:self.note.set(str(exc));return
        self.note.set('正在还原并核对…')
        self.run(lambda:self.service.restore(item['path']),lambda _:self.after_restore(),mutating=True)
    def after_restore(self):
        self.refresh('还原完成。')
    def restore_all(self):
        if self.working:return
        if not messagebox.askyesno('还原换装台的修改','还原本换装台修改过的全部桌面软件图标？\n其他工具的历史备份不会被处理。',parent=self.window):return
        self.note.set('正在逐项检查与还原…')
        def finish(results):
            errors=[x for x in results if x['status']=='failed']
            report=f'还原完成 {len(results)-len(errors)} 项，未完成 {len(errors)} 项。'
            if errors:
                report+='\n'+'\n'.join(Path(x['path']).stem+'：'+x['message'] for x in errors)
                messagebox.showwarning('还原结果',report,parent=self.window)
            self.note.set(report)
        self.run(self.service.restore_all,finish,mutating=True)
    def close(self):
        if self.busy:self.note.set('正在保存图标与还原记录，完成后再关闭。');return False
        self.closed=True;self.window.destroy();return True
    def cleanup(self,event):
        if event.widget==self.window:
            self.closed=True
            if self.timer:self.window.after_cancel(self.timer);self.timer=None
