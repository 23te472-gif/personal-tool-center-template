"""Small per-window preferences. No background thread or periodic disk writes."""
from pathlib import Path
import json,os,tempfile,weakref
import tkinter as tk
from tkinter import ttk,font as tkfont

SIZES={'small':('小',10/11),'standard':('标准',1.0),'large':('大',13/11)}

def clamp_geometry(value,bounds,minimum):
    x0,y0,width,height=bounds
    w=min(width,max(minimum[0],int(value['width'])));h=min(height,max(minimum[1],int(value['height'])))
    return {'width':w,'height':h,'x':min(max(int(value['x']),x0),x0+width-w),'y':min(max(int(value['y']),y0),y0+height-h)}

def _tuple(spec,factor):
    size=int(spec['size']);scaled=round(size*factor)
    if size>0:scaled=max(8,scaled)
    flags=[spec.get('weight','normal'),spec.get('slant','roman')]
    if spec.get('underline'):flags.append('underline')
    if spec.get('overstrike'):flags.append('overstrike')
    return (spec['family'],scaled,*flags)

class UIPreferences:
    def __init__(self,root,base,warn=None):
        self.root=root;self.path=Path(base)/'ui_settings.json';self.warn=warn or (lambda message:None)
        self.error='';self.value={'font':'standard','geometry':None,'maximized':False};self.ready=False;self.map_timer=None
        self.fonts=weakref.WeakKeyDictionary();self.named={};self.styles={};self.rows={};self.style=ttk.Style(root)
        try:
            if self.path.exists():
                if self.path.stat().st_size>65536:raise ValueError('界面设置文件过大')
                data=json.loads(self.path.read_text(encoding='utf-8'))
                if not isinstance(data,dict) or not isinstance(data.get('font'),str) or data['font'] not in SIZES or type(data.get('maximized',False)) is not bool:raise ValueError('界面设置格式错误')
                geom=data.get('geometry')
                if geom is not None and (not isinstance(geom,dict) or any(type(geom.get(k)) is not int for k in ('width','height','x','y'))):raise ValueError('窗口位置格式错误')
                self.value.update(font=data['font'],geometry=geom,maximized=data.get('maximized',False))
        except (OSError,ValueError) as exc:self.error=str(exc);self._warning('界面设置未读取，原文件保留：'+self.error)
        for name in tkfont.names(root):self.named[name]=tkfont.nametofont(name,root=root).actual()
        for name in ('.','TLabel','TButton','Primary.TButton','TEntry','TCombobox','Treeview','Treeview.Heading','App.TLabel','Title.App.TLabel','Card.TLabel','Muted.Card.TLabel','Section.Card.TLabel','App.TButton','Primary.App.TButton','App.Treeview','App.Treeview.Heading','App.TEntry','App.TCombobox','Title.TLabel'):
            config=self.style.configure(name) or {}
            if config.get('font'):self.styles[name]=tkfont.Font(root=root,font=config['font']).actual()
            if config.get('rowheight'):self.rows[name]=int(config['rowheight'])
        # Theme defaults can omit rowheight/font from configure(), while still
        # inheriting a larger font. Capture effective values before any scaling
        # so lazy-created lists and later size changes use the same baseline.
        for name in ('Treeview','App.Treeview'):
            effective=self.style.lookup(name,'font') or 'TkDefaultFont'
            self.styles.setdefault(name,tkfont.Font(root=root,font=effective).actual())
            self.rows.setdefault(name,int(self.style.lookup(name,'rowheight') or 20))
        self.button=ttk.Menubutton(root,text='字号：标准')
        menu=tk.Menu(self.button,tearoff=False)
        for key,(label,_) in SIZES.items():menu.add_command(label=label,command=lambda k=key:self.set_size(k))
        self.button.configure(menu=menu);self.button.place(relx=1.0,x=-20,y=12,anchor='ne')
        root.update_idletasks()
        if self.value['geometry']:
            geom=clamp_geometry(self.value['geometry'],(0,0,root.winfo_screenwidth(),root.winfo_screenheight()-60),root.minsize())
            root.geometry(f'{geom["width"]}x{geom["height"]}+{geom["x"]}+{geom["y"]}')
        self.apply_fonts()
        if self.value['maximized']:
            try:root.state('zoomed')
            except tk.TclError:pass
        self.ready=True;root.bind('<Configure>',self.remember,add='+');root.bind('<Destroy>',self.destroy,add='+')
        root.bind_all('<Map>',self.new_widgets,add='+')
    def _warning(self,message):
        try:self.warn(message)
        except tk.TclError:pass
    def remember(self,event):
        if event.widget!=self.root or not self.ready:return
        state=self.root.state()
        if state=='normal' and self.root.winfo_width()>100:
            self.value['geometry']={'width':self.root.winfo_width(),'height':self.root.winfo_height(),'x':self.root.winfo_x(),'y':self.root.winfo_y()}
        if state in ('normal','zoomed'):self.value['maximized']=state=='zoomed'
    def capture(self,widget):
        try:
            raw=widget.cget('font')
            if str(raw) and widget not in self.fonts:self.fonts[widget]=self.named.get(str(raw)) or tkfont.Font(root=self.root,font=raw).actual()
        except (tk.TclError,AttributeError):pass
        for child in widget.winfo_children():self.capture(child)
    def apply_fonts(self):
        factor=SIZES[self.value['font']][1];self.capture(self.root)
        for name,spec in self.named.items():
            try:tkfont.nametofont(name,root=self.root).configure(size=_tuple(spec,factor)[1])
            except tk.TclError:pass
        for name,spec in self.styles.items():self.style.configure(name,font=_tuple(spec,factor))
        for widget,spec in list(self.fonts.items()):
            try:
                if widget.winfo_exists():widget.configure(font=_tuple(spec,factor))
            except tk.TclError:pass
        for name,height in self.rows.items():
            spec=self.styles.get(name,self.named.get('TkDefaultFont'))
            line=tkfont.Font(root=self.root,font=_tuple(spec,factor)).metrics('linespace')
            self.style.configure(name,rowheight=max(round(height*factor),line+12))
        default=self.named.get('TkDefaultFont')
        if default:self.root.option_add('*TCombobox*Listbox.font',_tuple(default,factor))
        self.button.configure(text='字号：'+SIZES[self.value['font']][0])
    def new_widgets(self,event):
        widget=event.widget
        if not isinstance(widget,tk.Misc):return
        count=len(self.fonts)
        try:self.capture(widget)
        except tk.TclError:return
        if len(self.fonts)==count:return
        if self.map_timer is None:
            def apply():
                self.map_timer=None
                try:self.apply_fonts()
                except tk.TclError:pass
            self.map_timer=self.root.after_idle(apply)
    def set_size(self,key):
        if key not in SIZES:raise ValueError('未知字号')
        self.value['font']=key;self.apply_fonts();self.save()
    def save(self):
        if self.error:self._warning('界面设置未保存：'+self.error);return
        temporary=None
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd,temporary=tempfile.mkstemp(dir=self.path.parent,suffix='.tmp')
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(self.value,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,self.path)
        except OSError as exc:self._warning('界面设置未保存：'+str(exc))
        finally:
            if temporary:Path(temporary).unlink(missing_ok=True)
    def destroy(self,event):
        if event.widget!=self.root:return
        if self.map_timer:
            try:self.root.after_cancel(self.map_timer)
            except tk.TclError:pass
            self.map_timer=None
        self.save()
