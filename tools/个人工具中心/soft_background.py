"""Static, code-drawn accents. No image assets or animation loop."""
import tkinter as tk
from tkinter import ttk

PALETTES={
    'focus':dict(base='#f0f5ed',panel='#e7eee2',ink='#355c49',soft='#dce8d4',line='#c9dbc0'),
    'wheel':dict(base='#f3f0f8',panel='#eae4f3',ink='#61507f',soft='#e4dcef',line='#d5c7e5'),
    'icons':dict(base='#eef4f8',panel='#e3edf4',ink='#385f7d',soft='#dce9f2',line='#c5dbe9'),
}

def motifs(canvas,kind,width,height):
    """Decorate the quiet right-hand side; text remains on top."""
    p=PALETTES[kind];canvas.delete('decor')
    x=max(60,width-92);y=height/2
    if kind=='focus':
        canvas.create_oval(x-49,y-42,x+45,y+52,fill=p['soft'],outline='',tags='decor')
        canvas.create_line(x-12,y+36,x+18,y-29,fill=p['line'],width=2,tags='decor')
        canvas.create_oval(x-39,y-8,x+1,y+9,fill=p['line'],outline='',tags='decor')
        canvas.create_oval(x+1,y-30,x+39,y-12,fill=p['line'],outline='',tags='decor')
        canvas.create_oval(x-79,y-29,x-69,y-19,fill=p['soft'],outline='',tags='decor')
        canvas.create_line(x-190,4,x-144,height,fill='#e5eddf',width=21,tags='decor')
    elif kind=='wheel':
        canvas.create_oval(x-47,y-46,x+48,y+49,outline=p['soft'],width=15,tags='decor')
        canvas.create_oval(x-71,y-61,x+72,y+63,outline=p['line'],width=1,tags='decor')
        for px,py,size in ((x-105,y-24,7),(x-79,y+32,4),(x+53,y-30,5)):
            canvas.create_polygon(px,py-size,px+size/3,py-size/3,px+size,py,px+size/3,py+size/3,px,py+size,px-size/3,py+size/3,px-size,py,px-size/3,py-size/3,fill=p['line'],outline='',tags='decor')
    else:
        canvas.create_rectangle(x-64,y-30,x+12,y+25,fill=p['soft'],outline='',tags='decor')
        canvas.create_rectangle(x-33,y-12,x+46,y+44,outline=p['line'],width=2,tags='decor')
        canvas.create_oval(x+11,y-37,x+52,y+4,fill=p['line'],outline='',tags='decor')
        for i in range(3):canvas.create_oval(x-97+i*12,y+32,x-93+i*12,y+36,fill=p['line'],outline='',tags='decor')
    canvas.tag_lower('decor')

class SoftHeader(tk.Frame):
    def __init__(self,parent,kind,title,subtitle):
        p=PALETTES[kind];super().__init__(parent,bg=p['panel'])
        self.kind=kind
        self.art=tk.Canvas(self,bg=p['panel'],highlightthickness=0,takefocus=False)
        self.art.place(x=0,y=0,relwidth=1,relheight=1)
        self.tk.call('lower',self.art._w)
        tk.Label(self,text=title,bg=p['panel'],fg=p['ink'],font=('Microsoft YaHei UI',22,'bold')).pack(anchor='w',padx=15,pady=(9,3))
        self.subtitle=tk.Label(self,text=subtitle,bg=p['panel'],fg='#53647a',font='TkDefaultFont',justify='left')
        self.subtitle.pack(anchor='w',padx=15,pady=(0,10))
        self.bind('<Configure>',self.redraw)
    def redraw(self,event):
        self.subtitle.configure(wraplength=max(180,event.width-30))
        motifs(self.art,self.kind,event.width,event.height)

def apply_palette(window,kind):
    """Window-specific ttk styles avoid recoloring other open tools."""
    p=PALETTES[kind];window.configure(bg=p['base']);style=ttk.Style(window)
    frame_style=kind+'.Backdrop.TFrame';label_style=kind+'.Backdrop.TLabel'
    style.configure(frame_style,background=p['base']);style.configure(label_style,background=p['base'])
    def walk(widget):
        for child in widget.winfo_children():
            if isinstance(child,ttk.Frame) and child.cget('style') in ('','TFrame'):child.configure(style=frame_style)
            elif isinstance(child,ttk.Label) and child.cget('style') in ('','TLabel'):child.configure(style=label_style)
            walk(child)
    walk(window)

def tint_cards(cards,kind):
    color=PALETTES[kind]['panel'];cards.canvas.configure(bg=color);cards.inner.configure(bg=color)
