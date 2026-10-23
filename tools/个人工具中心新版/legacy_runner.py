"""Run only the chosen existing playful window without opening the old center."""
from pathlib import Path
import importlib,sys,ctypes

def enable_dpi(api=None):
    """Request native system-DPI rendering before Tk creates any window."""
    if api is None:api=getattr(ctypes,'windll',None)
    if api is None:return
    try:
        api.shcore.SetProcessDpiAwareness(1)
    except (OSError,AttributeError):
        try:api.user32.SetProcessDPIAware()
        except (OSError,AttributeError):pass

def configure_fonts(root):
    from tkinter import ttk,font
    for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkIconFont','TkTooltipFont'):
        font.nametofont(name,root=root).configure(family='Microsoft YaHei UI',size=11)
    style=ttk.Style(root)
    style.configure('.',font=('Microsoft YaHei UI',11))
    style.configure('Card.TFrame',background='#ffffff')
    style.configure('Card.TLabel',background='#ffffff',foreground='#24334b')
    style.configure('Muted.Card.TLabel',background='#ffffff',foreground='#52647c')
    style.configure('TButton',padding=(12,8))
    style.configure('Primary.TButton',font=('Microsoft YaHei UI',11,'bold'))

def main(key):
    base=Path(__file__).resolve().parent.parent/'个人工具中心';sys.path.insert(0,str(base))
    enable_dpi()
    import tkinter as tk
    module,name={'focus':('focus_ui','FocusWindow'),'icons':('shortcut_ui','ShortcutWindow')}[key]
    root=tk.Tk();root.withdraw();configure_fonts(root);app=getattr(importlib.import_module(module),name)(root,base)
    def close():
        if app.close():root.destroy()
    app.window.protocol('WM_DELETE_WINDOW',close);root.mainloop()
