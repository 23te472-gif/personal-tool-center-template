import tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk,font as tkfont
from app import ToolCenter

class Manager:
    def poll(self):return {}

class ListRowsTests(unittest.TestCase):
    def test_both_lazy_lists_fit_font_at_each_scaling_and_size(self):
        for scale in (96/72,144/72,192/72):
            with self.subTest(scale=scale),tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
                root=tk.Tk();root.tk.call('tk','scaling',scale);root.withdraw()
                try:
                    app=ToolCenter(root,Path(folder),manager=Manager())
                    with patch('shortcut_ui.ShortcutService') as service:
                        service.return_value.scan.return_value=[]
                        windows=[app.playful.open('wheel'),app.playful.open('icons')]
                        root.deiconify();deadline=time.monotonic()+3
                        while windows[1].working and time.monotonic()<deadline:root.update();time.sleep(.01)
                        for child in windows:
                            child.cards.set_items([dict(id='row-test-a',name='怪物猎人 · 崛起',appid='',checked=True),dict(id='row-test-b',name='Warhammer 40,000: Space Marine 2',appid='',checked=True)])
                        for size in ('standard','large','small','standard'):
                            app.ui_preferences.set_size(size);root.update()
                            for child in windows:
                                cards=child.cards;first=cards.widgets['row-test-a'];second=cards.widgets['row-test-b']
                                line=tkfont.Font(root=root,font=first['label'].cget('font')).metrics('linespace')
                                self.assertGreaterEqual(first['label'].winfo_height(),line*2,(scale,size,child.window.title()))
                                a=first['frame'];b=second['frame']
                                self.assertTrue(a.winfo_x()+a.winfo_width()<=b.winfo_x() or a.winfo_y()+a.winfo_height()<=b.winfo_y())
                finally:
                    root.update_idletasks();root.destroy()

if __name__=='__main__':unittest.main()
