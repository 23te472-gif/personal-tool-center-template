import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
from app import App
from library import Game,load_library

class WindowTests(unittest.TestCase):
    def test_open_game_directory_only(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy);base=Path(directory);app=App(root,base)
            app.persist([Game('demo','游戏',steam_install=str(base))]);root.update()
            with patch('app.open_path') as opened:app.open_game_folder();opened.assert_called_once_with(base)
            app.persist([Game('demo','游戏')]);root.update()
            with self.assertRaises(ValueError):app.open_game_folder()
    def test_trainer_open_recent_favorite_and_exclusion(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            base=Path(directory);tool=base/'Gunfire Reborn v1.0 Trainer.exe';tool.write_text('test only')
            root=tk.Tk();root.withdraw();self.addCleanup(root.destroy);app=App(root,base)
            app.persist([Game('gunfire','枪火重生',tool_paths=[str(tool)],english_name='Gunfire Reborn',preferred_tool=str(tool))]);root.update()
            app.query.set('gunfire');root.update();self.assertEqual(len(app.list.get_children()),1)
            with patch('app.open_path') as opened:app.open_preferred();opened.assert_called_once_with(tool)
            self.assertTrue(load_library(app.library)[0].last_used)
            app.toggle_favorite();self.assertTrue(load_library(app.library)[0].favorite)
            with patch('app.open_path') as opened:
                with self.assertRaises(ValueError):app.launch_tool('WeMod.exe')
                opened.assert_not_called()
    def test_edit_out_of_filter_and_worker_error(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root=tk.Tk(); root.withdraw(); self.addCleanup(lambda:root.destroy() if root.winfo_exists() else None)
            app=App(root,Path(directory)); app.persist([Game('id','before')]); app.query.set('before'); root.update()
            app.editor(app.games[0]); root.update()
            win=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
            def descendants(w):
                for child in w.winfo_children():yield child; yield from descendants(child)
            widgets=list(descendants(win)); entry=next(w for w in widgets if isinstance(w,ttk.Entry)); entry.delete(0,'end'); entry.insert(0,'after')
            with patch('app.messagebox.showerror') as error:
                next(w for w in widgets if isinstance(w,ttk.Button) and w.cget('text')=='保存卡片').invoke()
                error.assert_not_called()
            self.assertFalse(win.winfo_exists()); self.assertEqual(load_library(app.library)[0].name,'after')
            app.state.start()
            for b in app.buttons:b.state(['disabled'])
            app.events.put(('done',False,'disk failed')); app.poll()
            self.assertFalse(app.state.busy); self.assertIn('disk failed',app.status.get())
            self.assertTrue(all('disabled' not in b.state() for b in app.buttons))
