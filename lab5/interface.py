import math
import random
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog

import task1a
import task1b
import task2
import task3


EXAMPLES = Path(__file__).resolve().parent / 'examples'
PRESETS = {
    'Кривая Коха': 'koch.txt', 'Снежинка Коха': 'snowflake.txt',
    'Квадратный остров Коха': 'koch_island.txt', 'Ковёр Серпинского': 'sierpinski.txt',
    'Наконечник Серпинского': 'arrowhead.txt', 'Кривая Гильберта': 'hilbert.txt',
    'Дракон': 'dragon.txt', 'Кривая Госпера': 'gosper.txt',
    'Куст 1': 'bush1.txt', 'Куст 2': 'bush2.txt', 'Куст 3': 'bush3.txt',
    'Шестиугольная мозаика': 'mosaic.txt', 'Случайное дерево': 'random_tree.txt',
}
ERRORS = {
    'empty_system': 'Описание системы пустое.',
    'bad_header': 'Первая строка: аксиома угол направление. Например: F 60 0',
    'bad_rule': 'Правило должно выглядеть как F -> F+F. Слева нужен один символ.',
    'bad_number': 'Введите конечные числовые значения.',
    'iterations_limit': 'Число итераций L-системы: от 0 до 15.',
    'system_limit': 'Система слишком большая. Уменьшите число итераций.',
    'segments_limit': 'Больше 40 000 отрезков. Уменьшите число итераций.',
    'brackets': 'Открывающие и закрывающие скобки должны быть парными.',
    'tree_parameters': 'Толщина должна быть положительной, утончение — между 0 и 1.',
    'mountain_iterations': 'Число итераций гор: от 0 до 14.',
    'mountain_parameters': 'R: от 0 до 1; затухание: больше 0 и не больше 1; длина больше 0.',
}


def error_text(error):
    return ERRORS.get(str(error), 'Проверьте формат файла и числовые параметры.')


def entry(parent, title, value, width=7):
    ttk.Label(parent, text=title).pack(side='left', padx=(8, 3))
    field = ttk.Entry(parent, width=width)
    field.insert(0, str(value))
    field.pack(side='left')
    return field


def number(field, integer=False):
    text = field.get().strip().replace(',', '.')
    value = int(text) if integer else float(text)
    if not math.isfinite(value):
        raise ValueError('bad_number')
    return value


def flatten(points):
    return [value for point in points for value in point]


class LSystemTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.segments, self.styles = [], []
        self.tree_mode = tk.BooleanVar(value=False)
        row = ttk.Frame(self); row.pack(fill='x', pady=5)
        self.preset = ttk.Combobox(row, values=list(PRESETS), state='readonly', width=29)
        self.preset.current(0); self.preset.pack(side='left', padx=5)
        ttk.Button(row, text='Взять пример', command=self.load_preset).pack(side='left')
        ttk.Button(row, text='Открыть TXT', command=self.open_file).pack(side='left', padx=5)
        ttk.Button(row, text='Сохранить TXT', command=self.save_file).pack(side='left')
        self.iterations = entry(row, 'Итерации', 3, 4)
        ttk.Checkbutton(row, text='1б: дерево', variable=self.tree_mode).pack(side='left', padx=10)
        self.text = tk.Text(self, height=5, wrap='none', undo=True, font=('Menlo', 11))
        self.text.pack(fill='x', padx=5)
        self.text.insert('1.0', (EXAMPLES / 'koch.txt').read_text())
        ttk.Label(self, text='Первая строка: аксиома угол направление (в градусах). F/G — рисовать; f — идти; +/- — поворот; [ ] — ветвление. X/Y — служебные символы.').pack(anchor='w', padx=5)
        row = ttk.Frame(self); row.pack(fill='x', pady=5)
        self.randomness = entry(row, 'Случайный угол ±°', 0, 5)
        self.seed = entry(row, 'Seed', 42, 7)
        self.width = entry(row, 'Толщина ствола', 12, 5)
        self.thinning = entry(row, 'Утончение', 0.72, 5)
        ttk.Button(row, text='Построить', command=self.build).pack(side='left', padx=8)
        ttk.Button(row, text='Новый seed', command=self.new_seed).pack(side='left')
        self.status = ttk.Label(self, text='')
        self.status.pack(side='bottom', fill='x', padx=5, pady=5)
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.after_idle(self.build)

    def load_preset(self):
        try:
            filename = PRESETS[self.preset.get()]
            text = (EXAMPLES / filename).read_text(encoding='utf-8')
        except OSError as error:
            self.status.config(text=f'Не удалось прочитать файл: {error}'); return
        self.text.delete('1.0', 'end'); self.text.insert('1.0', text)
        is_tree = filename.startswith('bush') or filename == 'random_tree.txt'
        self.tree_mode.set(is_tree)
        self.randomness.delete(0, 'end'); self.randomness.insert(0, '8' if is_tree else '0')
        self.build()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('L-системы', '*.txt'), ('Все файлы', '*')])
        if path:
            try:
                text = Path(path).read_text(encoding='utf-8-sig')
                task1a.parse_lsystem(text)
            except (OSError, UnicodeError, ValueError) as error:
                self.status.config(text=f'Не удалось загрузить файл: {error_text(error)}'); return
            self.text.delete('1.0', 'end'); self.text.insert('1.0', text)
            self.status.config(text=f'Загружен {Path(path).name}. Нажмите «Построить».')

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('L-системы', '*.txt')])
        if path:
            try: Path(path).write_text(self.text.get('1.0', 'end-1c') + '\n', encoding='utf-8')
            except OSError as error: self.status.config(text=f'Ошибка сохранения: {error}')
            else: self.status.config(text=f'Сохранено: {Path(path).name}')

    def new_seed(self):
        self.seed.delete(0, 'end'); self.seed.insert(0, str(random.randrange(1000000)))
        self.build()

    def build(self):
        try:
            axiom, angle, direction, rules = task1a.parse_lsystem(self.text.get('1.0', 'end-1c'))
            iterations, seed = number(self.iterations, True), number(self.seed, True)
            randomness = number(self.randomness)
            if self.tree_mode.get():
                segments, styles = task1b.build_tree(axiom, rules, iterations, angle, direction,
                    randomness, seed, number(self.width), number(self.thinning))
            else:
                commands = task1a.generate(axiom, rules, iterations, seed)
                segments = task1a.calculate_segments(commands, angle, direction, randomness, seed)
                styles = [(1.2, (25, 60, 100)) for _ in segments]
        except (ValueError, OverflowError) as error:
            self.status.config(text=error_text(error)); return
        self.segments, self.styles = segments, styles
        self.status.config(text=f'Итерация {iterations}; отрезков: {len(segments)}; seed: {seed}. Рисунок вписан в окно.')
        self.draw()

    def draw(self):
        self.canvas.delete('all')
        if not self.segments: return
        points = [p for segment in self.segments for p in segment[:2]]
        padding = 25 + max(width for width, _ in self.styles) / 2
        fitted = task1a.fit_points(points, self.canvas.winfo_width(), self.canvas.winfo_height(), padding)
        for i, (width, color) in enumerate(self.styles):
            self.canvas.create_line(*fitted[2*i], *fitted[2*i+1], width=width,
                fill='#%02x%02x%02x' % color, capstyle='round')


class MountainTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.steps = []
        self.bounds = None
        self.timer = None
        row = ttk.Frame(self); row.pack(fill='x', pady=6)
        self.iterations = entry(row, 'Итерации', 8, 4)
        self.roughness = entry(row, 'Шероховатость R', 0.3, 5)
        self.decay = entry(row, 'Затухание', 1.0, 5)
        self.seed = entry(row, 'Seed', 42, 7)
        ttk.Button(row, text='Построить', command=self.build).pack(side='left', padx=8)
        ttk.Button(row, text='Новый seed', command=self.new_seed).pack(side='left')
        row = ttk.Frame(self); row.pack(fill='x', pady=4)
        self.left = entry(row, 'Левая высота', 0, 6)
        self.right = entry(row, 'Правая высота', 0, 6)
        self.length = entry(row, 'Длина', 1000, 7)
        ttk.Label(self, text='Затухание 1 — формула лекции R·L. Меньшее значение дополнительно сглаживает следующие поколения.').pack(anchor='w', padx=5)
        row = ttk.Frame(self); row.pack(fill='x', pady=4)
        ttk.Button(row, text='◀ Назад', command=lambda: self.change_step(-1)).pack(side='left', padx=5)
        ttk.Button(row, text='Далее ▶', command=lambda: self.change_step(1)).pack(side='left')
        self.play_button = ttk.Button(row, text='Показать шаги', command=self.play)
        self.play_button.pack(side='left', padx=5)
        self.step = tk.IntVar(value=0)
        self.slider = tk.Scale(row, from_=0, to=8, variable=self.step, orient='horizontal',
                               label='Шаг', command=lambda _: self.draw(), length=400)
        self.slider.pack(side='left', fill='x', expand=True, padx=5)
        self.status = ttk.Label(self, text=''); self.status.pack(side='bottom', fill='x', pady=5, padx=5)
        self.canvas = tk.Canvas(self, bg='#eff6ff', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.after_idle(self.build)

    def stop(self):
        if self.timer is not None:
            self.after_cancel(self.timer); self.timer = None
        self.play_button.config(text='Показать шаги')

    def build(self):
        self.stop()
        try:
            steps = task2.midpoint_displacement(number(self.iterations, True), number(self.roughness),
                number(self.decay), number(self.left), number(self.right), number(self.length), number(self.seed, True))
        except (ValueError, OverflowError) as error:
            self.status.config(text=error_text(error)); return
        self.steps = steps
        xs, ys = zip(*steps[-1])
        self.bounds = min(xs), min(ys), max(xs), max(ys)
        self.slider.config(to=len(steps)-1); self.step.set(0); self.draw()

    def new_seed(self):
        self.seed.delete(0, 'end'); self.seed.insert(0, str(random.randrange(1000000))); self.build()

    def change_step(self, delta):
        self.stop()
        if self.steps:
            self.step.set(max(0, min(len(self.steps)-1, self.step.get()+delta))); self.draw()

    def play(self):
        if self.timer is not None:
            self.stop(); return
        if not self.steps: return
        if self.step.get() == len(self.steps)-1: self.step.set(0)
        self.play_button.config(text='Пауза')
        self.tick()

    def tick(self):
        self.draw()
        if self.step.get() >= len(self.steps)-1:
            self.stop(); return
        self.timer = self.after(450, self.advance)

    def advance(self):
        self.timer = None; self.step.set(self.step.get()+1); self.tick()

    def draw(self):
        self.canvas.delete('all')
        if not self.steps: return
        index = max(0, min(self.step.get(), len(self.steps)-1))
        points = task1a.fit_points(self.steps[index], self.canvas.winfo_width(), self.canvas.winfo_height(), 35, self.bounds)
        baseline = self.canvas.winfo_height()-15
        self.canvas.create_polygon(flatten(points)+[points[-1][0],baseline,points[0][0],baseline],
                                   fill='#a8b8cc', outline='')
        self.canvas.create_line(flatten(points), fill='#22486b', width=2)
        if len(points) <= 257:
            for x,y in points: self.canvas.create_oval(x-2,y-2,x+2,y+2,fill='#b82c3e',outline='')
        self.status.config(text=f'Шаг {index} из {len(self.steps)-1}; точек: {len(points)}. Масштаб одинаков для всех шагов.')


class BezierTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.points = []
        self.dragging = self.selected = None
        row = ttk.Frame(self); row.pack(fill='x', pady=5)
        ttk.Button(row, text='Удалить выбранную', command=self.delete_selected).pack(side='left', padx=5)
        ttk.Button(row, text='Очистить', command=self.clear).pack(side='left')
        self.show_controls = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text='Показать вычисленные контрольные точки', variable=self.show_controls,
                        command=self.draw).pack(side='left', padx=10)
        ttk.Label(self, text='ЛКМ на пустом месте — добавить точку в конец. Перетаскивание ЛКМ — переместить. ПКМ или Ctrl+ЛКМ — удалить точку.').pack(anchor='w', padx=5)
        ttk.Label(self, text='Кривая проходит через заданные точки. Контрольные точки рассчитываются автоматически и не перетаскиваются.').pack(anchor='w', padx=5)
        self.status = ttk.Label(self, text='Добавьте хотя бы две точки.')
        self.status.pack(side='bottom', fill='x', padx=5, pady=5)
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Button-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<Button-3>', self.remove)
        self.canvas.bind('<Control-Button-1>', self.remove)
        self.canvas.bind('<Delete>', lambda _: self.delete_selected())
        self.canvas.bind('<BackSpace>', lambda _: self.delete_selected())
        self.canvas.bind('<Configure>', lambda _: self.draw())

    def press(self, event):
        self.canvas.focus_set()
        index = task3.nearest_point(self.points, event.x, event.y)
        if index is None:
            self.points.append((event.x,event.y)); index = len(self.points)-1
        self.dragging = self.selected = index; self.draw()

    def drag(self, event):
        if self.dragging is not None:
            x = max(0,min(self.canvas.winfo_width()-1,event.x))
            y = max(0,min(self.canvas.winfo_height()-1,event.y))
            self.points[self.dragging] = (x,y); self.draw()

    def release(self, event):
        self.dragging = None; self.draw()

    def remove(self, event):
        index = task3.nearest_point(self.points,event.x,event.y)
        if index is not None:
            self.selected = index; self.delete_selected()
        return 'break'

    def delete_selected(self):
        if self.selected is not None and self.selected < len(self.points):
            self.points.pop(self.selected)
        self.dragging = self.selected = None; self.draw()

    def clear(self):
        self.points = []; self.dragging = self.selected = None; self.draw()

    def draw(self):
        self.canvas.delete('all')
        for i, curve in enumerate(task3.sample_spline(self.points)):
            if self.show_controls.get():
                controls = task3.control_points(self.points,i)
                self.canvas.create_line(flatten(controls),fill='#b5bcc5',dash=(3,3))
                for x,y in controls[1:3]:
                    self.canvas.create_rectangle(x-2,y-2,x+2,y+2,outline='#8f99a7')
            self.canvas.create_line(flatten(curve),fill='#165caa',width=2)
        for i,(x,y) in enumerate(self.points):
            color = '#c83939' if i==self.selected else '#273e55'
            self.canvas.create_oval(x-5,y-5,x+5,y+5,fill=color,outline='white')
            self.canvas.create_text(x+10,y-12,text=str(i+1),fill=color)
        self.status.config(text=f'Опорных точек: {len(self.points)}; кубических участков: {max(0,len(self.points)-1)}. Управление только опорными точками.')


class App:
    def __init__(self, root):
        root.title('Лабораторная №5. Фракталы и кубические сплайны Безье')
        root.geometry('1200x820'); root.minsize(1050,650)
        self.notebook = ttk.Notebook(root); self.notebook.pack(fill='both',expand=True)
        self.lsystem = LSystemTab(self.notebook)
        self.mountain = MountainTab(self.notebook)
        self.bezier = BezierTab(self.notebook)
        for tab,title in [(self.lsystem,'1а / 1б. L-системы и дерево'),
                          (self.mountain,'2. Горный массив'),(self.bezier,'3. Кубический сплайн Безье')]:
            self.notebook.add(tab,text=title)


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
