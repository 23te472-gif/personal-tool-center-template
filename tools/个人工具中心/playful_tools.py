"""Lazy window registry: importing the center does not load these tools."""
import importlib
import tkinter as tk

TOOLS={'focus':('focus_ui','FocusWindow'),'wheel':('wheel_ui','WheelWindow'),'icons':('shortcut_ui','ShortcutWindow')}

class PlayfulTools:
    def __init__(self,root,base):self.root=root;self.base=base;self.windows={}
    def open(self,key):
        existing=self.windows.get(key)
        try:
            if existing and existing.window.winfo_exists():
                existing.window.deiconify();existing.window.lift();existing.window.focus_set();return existing
        except tk.TclError:pass
        module,name=TOOLS[key];factory=getattr(importlib.import_module(module),name)
        app=factory(self.root,self.base);self.windows[key]=app;return app
    def close_all(self):
        active=[app for app in self.windows.values() if app.window.winfo_exists()]
        if any(getattr(app,'busy',False) and app.__class__.__name__=='ShortcutWindow' for app in active):return False
        # Persist focus progress before destroying any unrelated window.
        active.sort(key=lambda app:0 if app.__class__.__name__=='FocusWindow' else 1)
        for app in active:
            if not app.close():return False
        return True
