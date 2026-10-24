import random
import tkinter as tk
from tkinter import ttk
from quickhull import quickhull


class App:
    def __init__(self, root):
        root.title('QuickHull — построение выпуклой оболочки')
        root.geometry('1050x760')
        root.minsize(850, 550)
        self.points = []
        self.hull = []
        self.selected = None
        self.dragging = None
        self.automatic = tk.BooleanVar(value=True)
        self.numbers = tk.BooleanVar(value=False)
        toolbar = ttk.Frame(root, padding=8)
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text='Построить оболочку', command=self.build).pack(side='left')
        ttk.Button(toolbar, text='Очистить', command=self.clear).pack(side='left', padx=5)
        ttk.Label(toolbar, text='Случайных точек:').pack(side='left', padx=(8, 3))
        self.count = ttk.Entry(toolbar, width=6)
        self.count.insert(0, '50')
        self.count.pack(side='left')
        ttk.Button(toolbar, text='Создать', command=self.random_points).pack(side='left', padx=5)
        ttk.Checkbutton(toolbar, text='Автопостроение', variable=self.automatic,
                        command=self.changed).pack(side='left', padx=5)
        ttk.Checkbutton(toolbar, text='Номера точек', variable=self.numbers,
                        command=self.draw).pack(side='left')
        ttk.Label(root, text='ЛКМ на пустом месте — добавить точку; перетаскивание — переместить. '
                  'ПКМ / Ctrl+ЛКМ или Delete — удалить выбранную точку.', padding=(8, 3)).pack(anchor='w')
        self.status = ttk.Label(root, text='Добавьте точки или создайте случайный набор.', padding=8)
        self.status.pack(side='bottom', fill='x')
        self.canvas = tk.Canvas(root, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<Button-3>', self.remove)
        self.canvas.bind('<Control-Button-1>', self.remove)
        self.canvas.bind('<Delete>', lambda _: self.delete_selected())
        self.canvas.bind('<BackSpace>', lambda _: self.delete_selected())
        self.canvas.bind('<Configure>', lambda _: self.draw())

    def nearest(self, x, y):
        if not self.points:
            return None
        index = min(range(len(self.points)), key=lambda i: (self.points[i][0]-x)**2 + (self.points[i][1]-y)**2)
        px, py = self.points[index]
        return index if (px-x)**2 + (py-y)**2 <= 10**2 else None

    def position(self, event):
        return (max(0, min(self.canvas.winfo_width()-1, event.x)),
                max(0, min(self.canvas.winfo_height()-1, event.y)))

    def press(self, event):
        self.canvas.focus_set()
        index = self.nearest(event.x, event.y)
        if index is None:
            self.points.append(self.position(event))
            index = len(self.points)-1
        self.selected = self.dragging = index
        self.changed()

    def drag(self, event):
        if self.dragging is not None:
            self.points[self.dragging] = self.position(event)
            self.changed()

    def release(self, event):
        self.dragging = None

    def remove(self, event):
        index = self.nearest(event.x, event.y)
        if index is not None:
            self.selected = index
            self.delete_selected()
        return 'break'

    def delete_selected(self):
        if self.selected is not None and self.selected < len(self.points):
            self.points.pop(self.selected)
        self.selected = self.dragging = None
        self.changed()

    def changed(self):
        if self.automatic.get():
            self.build()
        else:
            self.hull = []
            self.status.config(text=f'Точек: {len(self.points)}. Нажмите «Построить оболочку».')
            self.draw()

    def build(self):
        self.hull = quickhull(self.points)
        if len(self.hull) == 0:
            message = 'Набор точек пуст.'
        elif len(self.hull) == 1:
            message = 'Оболочка — одна точка.'
        elif len(self.hull) == 2:
            message = 'Оболочка — отрезок: все точки лежат на одной прямой.'
        else:
            message = 'Оболочка построена. Красные точки — вершины, синие — остальные точки.'
        self.status.config(text=f'Точек: {len(self.points)}; уникальных: {len(set(self.points))}; '
                           f'вершин оболочки: {len(self.hull)}. {message}')
        self.draw()

    def clear(self):
        self.points = []
        self.hull = []
        self.selected = self.dragging = None
        self.status.config(text='Сцена очищена. Добавьте новые точки.')
        self.draw()

    def random_points(self):
        try:
            count = int(self.count.get())
            if not 1 <= count <= 2000:
                raise ValueError
        except ValueError:
            self.status.config(text='Введите целое количество точек от 1 до 2000.')
            return
        width = max(1, self.canvas.winfo_width()-60)
        height = max(1, self.canvas.winfo_height()-60)
        self.points = [(30+random.randrange(width), 30+random.randrange(height)) for _ in range(count)]
        self.selected = self.dragging = None
        self.changed()

    def draw(self):
        self.canvas.delete('all')
        if len(self.hull) >= 3:
            self.canvas.create_polygon([c for p in self.hull for c in p],
                                       fill='#e8f2fc', outline='#d12d38', width=2)
        elif len(self.hull) == 2:
            self.canvas.create_line(*self.hull[0], *self.hull[1], fill='#d12d38', width=2)
        hull_set = set(self.hull)
        for index, (x, y) in enumerate(self.points):
            color = '#d12d38' if (x,y) in hull_set else '#205e9a'
            self.canvas.create_oval(x-4,y-4,x+4,y+4,fill=color,outline='white')
            if index == self.selected:
                self.canvas.create_oval(x-8,y-8,x+8,y+8,outline='#db8b14',width=2)
            if self.numbers.get():
                self.canvas.create_text(x+10,y-10,text=str(index+1),fill=color)


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
