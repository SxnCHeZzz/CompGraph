"""Общая панель просмотра для лабораторных №8 и №9."""

import tkinter as tk
from tkinter import font, ttk

from member2_zbuffer import BACKGROUND


def workspace(root, title):
    root.geometry('1160x780')
    root.minsize(980, 680)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)

    heading_font = font.nametofont('TkDefaultFont', root=root).copy()
    heading_font.configure(size=17, weight='bold')
    heading = ttk.Label(root, text=title, font=heading_font)
    heading.font = heading_font
    heading.grid(row=0, sticky='w', padx=16, pady=(12, 5))
    toolbar = ttk.Frame(root, padding=(16, 0, 16, 10))
    toolbar.grid(row=1, sticky='ew')
    body = ttk.Frame(root, padding=(16, 0, 16, 10))
    body.grid(row=2, sticky='nsew')
    return toolbar, body


def view_buttons(toolbar, fit, reset):
    ttk.Button(toolbar, text='Сбросить вид', command=reset).pack(side='right')
    ttk.Button(toolbar, text='Вписать', command=fit).pack(side='right', padx=(8, 6))


class Viewport(ttk.Frame):
    def __init__(self, parent, status, redraw, rotate, zoom, fit):
        super().__init__(parent)
        self.rotate = rotate
        self.zoom = zoom
        self.fit = fit
        self.drag_position = None

        self.canvas = tk.Canvas(self, background='#%02x%02x%02x' % BACKGROUND,
                                highlightthickness=1, highlightbackground='#c7d3df',
                                highlightcolor='#527c9c', takefocus=True)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', redraw)
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.end_drag)
        self.canvas.bind('<MouseWheel>', self.wheel)
        self.canvas.bind('<Button-4>', lambda _: self.zoom(1.1))
        self.canvas.bind('<Button-5>', lambda _: self.zoom(1 / 1.1))
        self.canvas.bind('<Home>', lambda _: self.fit())
        for key, dx, dy in (('Left', -18, 0), ('Right', 18, 0), ('Up', 0, -18), ('Down', 0, 18)):
            self.canvas.bind(f'<{key}>', lambda _, x=dx, y=dy: self.rotate(x, y))
        ttk.Label(self, textvariable=status, padding=(0, 6)).pack(fill='x')
        ttk.Label(self, text='ЛКМ или стрелки — вращение   ·   Колесо — масштаб   ·   Home — вписать').pack(anchor='w')

    def start_drag(self, event):
        self.canvas.focus_set()
        self.drag_position = event.x, event.y

    def drag(self, event):
        if self.drag_position is None:
            return
        x, y = self.drag_position
        self.drag_position = event.x, event.y
        self.rotate(event.x - x, event.y - y)

    def end_drag(self, event):
        self.drag_position = None

    def wheel(self, event):
        # На macOS трекпад присылает мелкие дельты, у обычного колеса шаг равен 120.
        steps = event.delta / 120 if abs(event.delta) >= 120 else event.delta / 4
        self.zoom(1.1 ** max(-4, min(4, steps)))
        return 'break'

    def draw_axes(self, view):
        canvas = self.canvas
        canvas.delete('view_axes')
        if canvas.winfo_width() < 110 or canvas.winfo_height() < 90:
            return
        x, y, radius = canvas.winfo_width() - 48, 47, 21
        tag = 'view_axes'
        canvas.create_oval(x - 34, y - 34, x + 34, y + 34,
                           fill='#eef3f8', outline='#c7d3df', tags=tag)
        axes = view.view_matrix()[:3, :3]
        colors = ('#a72d43', '#216e51', '#235994')
        for index in sorted(range(3), key=lambda i: -axes[i, 2]):
            ax, ay = axes[index, :2] * radius
            canvas.create_line(x, y, x + ax, y - ay, width=2, fill=colors[index],
                               arrow=tk.LAST, tags=tag)
            canvas.create_text(x + ax * 1.33, y - ay * 1.33,
                               text='XYZ'[index], fill=colors[index], tags=tag)
        canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill='#465972', outline='', tags=tag)
