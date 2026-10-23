"""Small, on-demand bookmarks panel embedded in the tool center."""
from datetime import datetime
from pathlib import Path
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import materials
from quickpack import create_zip


class MaterialsPanel:
    def __init__(self, parent, base, status):
        self.root = parent.winfo_toplevel()
        self.base = Path(base)
        self.path = self.base / 'data/materials.json'
        self.output = self.base / '资料打包'
        self.status = status
        self.busy = False
        self.events = queue.SimpleQueue()
        self.timer = None
        self.error = ''
        try:
            self.config = materials.load(self.path)
        except (OSError, ValueError) as exc:
            self.error = str(exc)
            self.config = dict.fromkeys(materials.KEYS, '')
        card = ttk.Frame(parent, style='Card.TFrame', padding=18)
        card.pack(fill='x', pady=(0, 12)); card.columnconfigure(1, weight=1)
        self.frame = card
        ttk.Label(card, text='常用资料 · 论文', style='Card.TLabel',
                  font=('Microsoft YaHei UI', 17, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(card, text='选一次，以后直接打开；文件仍在原来的位置。',
                  style='Muted.Card.TLabel').grid(row=1, column=0, columnspan=3, sticky='w', pady=(4, 12))
        self.labels = {}
        self.controls = []
        for row, (key, title) in enumerate((('thesis', '论文'), ('presentation', '汇报 PPT'), ('charts', '图表与数据')), 2):
            button = ttk.Button(card, text='打开' + title, command=lambda key=key: self.guard(lambda: self.open(key)))
            button.grid(row=row, column=0, sticky='ew', pady=4, padx=(0, 12))
            self.controls.append(button)
            value = tk.StringVar()
            ttk.Label(card, textvariable=value, style='Muted.Card.TLabel', wraplength=380,
                      justify='left').grid(row=row, column=1, sticky='w', pady=4)
            self.labels[key] = value
            button = ttk.Button(card, text='选择…', command=lambda key=key: self.guard(lambda: self.choose(key)))
            button.grid(row=row, column=2, sticky='e', padx=(12, 0))
            self.controls.append(button)
        actions = ttk.Frame(card, style='Card.TFrame', padding=0)
        actions.grid(row=5, column=0, columnspan=3, sticky='ew', pady=(14, 0))
        for text, command, style in (
            ('打包论文 + PPT', lambda: self.guard(self.pack), 'Primary.TButton'),
            ('打开压缩包位置', lambda: self.guard(self.open_output), 'TButton'),
            ('刷新修改时间', self.refresh, 'TButton'),
        ):
            button = ttk.Button(actions, text=text, command=command, style=style)
            button.pack(side='left', padx=(0, 8)); self.controls.append(button)
        self.note = tk.StringVar(value=self.error or '只打包上面选定的论文和 PPT，图表文件夹不自动打包。')
        ttk.Label(card, textvariable=self.note, style='Muted.Card.TLabel', wraplength=650,
                  justify='left').grid(row=6, column=0, columnspan=3, sticky='w', pady=(10, 0))
        self.refresh()
        card.bind('<Destroy>', self.cleanup, add='+')

    def guard(self, action):
        try:
            return action()
        except Exception as exc:
            self.note.set(str(exc)); self.status(str(exc))
            messagebox.showerror('操作未完成', str(exc), parent=self.root)

    def refresh(self):
        for key, label in self.labels.items():
            value = self.config[key]
            if not value:
                label.set('尚未选择，点击右侧“选择…”'); continue
            path = Path(value)
            try:
                valid = path.is_dir() if key == 'charts' else path.is_file()
                if not valid:
                    raise FileNotFoundError()
                stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime('%m-%d %H:%M')
                label.set(f'{path.name}\n修改于 {stamp}')
            except OSError:
                label.set(f'{path.name}\n已移动或不可访问，请重新选择')

    def choose(self, key):
        if self.busy:
            return
        if self.error:
            raise ValueError(self.error)
        if key == 'charts':
            value = filedialog.askdirectory(parent=self.root, title='选择图表或数据所在文件夹')
        else:
            value = filedialog.askopenfilename(parent=self.root, title='选择常用论文' if key == 'thesis' else '选择汇报 PPT')
        if not value:
            return
        updated = dict(self.config, **{key: value})
        materials.save(self.path, updated)
        self.config = updated; self.refresh()
        self.note.set('已记住入口，原文件没有移动。')

    def open(self, key):
        value = self.config[key]
        if not value:
            self.choose(key); return
        path = Path(value)
        valid = path.is_dir() if key == 'charts' else path.is_file()
        if not valid:
            raise FileNotFoundError(f'文件已移动或不存在，请重新选择：{path}')
        os.startfile(str(path))

    def open_output(self):
        if not self.output.is_dir():
            self.note.set('尚未生成压缩包，打包完成后可打开这里。'); return
        os.startfile(str(self.output))

    def pack(self):
        if self.busy:
            return
        paths = materials.pack_files(self.config)
        self.busy = True
        for button in self.controls:
            button.state(['disabled'])
        self.note.set('正在打包，请稍候…')
        def worker():
            try:
                result = create_zip(paths, self.output, lambda message: None)
                self.events.put((True, str(result)))
            except Exception as exc:
                self.events.put((False, str(exc)))
        threading.Thread(target=worker, daemon=True).start()
        self.timer = self.root.after(150, self.poll)

    def poll(self):
        self.timer = None
        try:
            okay, value = self.events.get_nowait()
        except queue.Empty:
            self.timer = self.root.after(150, self.poll); return
        self.busy = False
        for button in self.controls:
            button.state(['!disabled'])
        text = ('打包完成：' if okay else '打包失败：') + value
        self.note.set(text); self.status(text)
        self.refresh()

    def cleanup(self, event):
        if event.widget == self.frame and self.timer:
            self.root.after_cancel(self.timer); self.timer = None
