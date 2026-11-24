"""Лабораторная №9. Управление сценой и вывод программного кадра через Tkinter."""

import tkinter as tk
from tkinter import colorchooser, filedialog, ttk

import numpy as np

from member2_raster import BACKGROUND, SceneView, model_matrix, render
from member3_texture import PROJECT, Texture, load_surface, make_surface


SHAPES = {'Тетраэдр': 'tetrahedron', 'Куб': 'cube', 'Октаэдр': 'octahedron', 'Шар': 'sphere'}
MODES = {'Гуро · Ламберт': 'gouraud', 'Фонг · туншейдинг': 'toon', 'Текстурирование': 'texture'}
PROJECTIONS = {'Параллельная': 'axonometric', 'Перспективная': 'perspective'}
DEFAULT_LIGHT = (-180, 160, -230)


class App:
    def __init__(self, root):
        self.root = root
        root.title('Лабораторная №9 — Освещение и текстурирование')
        root.geometry('1100x700')
        root.minsize(860, 625)

        self.surface = make_surface('sphere')
        self.model_name = 'Шар'
        self.texture = Texture.checker()
        self.color = np.array([86, 152, 217])
        self.view = SceneView()
        self.view.fit(self.surface.mesh, 720, 560)
        self.photo = None
        self.draw_job = None
        self.drag_position = None

        self.shape = tk.StringVar(value=self.model_name)
        self.mode = tk.StringVar(value=next(iter(MODES)))
        self.projection = tk.StringVar(value=next(iter(PROJECTIONS)))
        self.texture_name = tk.StringVar(value='Шахматная сетка')
        self.status = tk.StringVar()
        self.offset = self.variables((0, 0, 0))
        self.angles = self.variables((0, 0, 0))
        self.scale = self.variables((1, 1, 1))
        self.light = self.variables(DEFAULT_LIGHT)

        body = ttk.Frame(root, padding=12)
        body.pack(fill='both', expand=True)
        controls = ttk.Frame(body, width=278)
        controls.pack(side='left', fill='y', padx=(0, 12))
        display = ttk.Frame(body)
        display.pack(side='left', fill='both', expand=True)

        self.build_controls(controls)
        self.canvas = tk.Canvas(display, background='#%02x%02x%02x' % BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.image_item = self.canvas.create_image(0, 0, anchor='nw')
        self.canvas.bind('<Configure>', self.schedule)
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.end_drag)
        ttk.Label(display, textvariable=self.status, padding=(0, 8), wraplength=510).pack(fill='x')
        self.schedule()

    @staticmethod
    def variables(values):
        return tuple(tk.StringVar(value=str(value)) for value in values)

    def build_controls(self, panel):
        scene = ttk.LabelFrame(panel, text='Сцена', padding=8)
        scene.pack(fill='x', pady=(0, 9))
        self.combo(scene, self.shape, SHAPES, self.select_shape)
        ttk.Button(scene, text='Открыть OBJ…', command=self.open_obj).pack(fill='x', pady=(3, 7))
        self.combo(scene, self.mode, MODES, self.schedule)
        self.combo(scene, self.projection, PROJECTIONS, self.schedule)
        ttk.Label(scene, text='ЛКМ + движение — изменить обзор.').pack(anchor='w', pady=(4, 0))

        self.transform_controls = ttk.LabelFrame(panel, text='Преобразования объекта', padding=8)
        self.transform_controls.pack(fill='x', pady=(0, 9))
        self.fields(self.transform_controls, 'Перенос', self.offset, 10)
        self.fields(self.transform_controls, 'Поворот, °', self.angles, 5)
        self.fields(self.transform_controls, 'Масштаб', self.scale, 0.1)
        buttons = ttk.Frame(self.transform_controls)
        buttons.pack(fill='x')
        ttk.Button(buttons, text='Применить', command=self.schedule).pack(side='left', expand=True, fill='x')
        ttk.Button(buttons, text='Сбросить', command=self.reset_transform).pack(side='left', expand=True, fill='x')

        lighting = ttk.LabelFrame(panel, text='Освещение', padding=8)
        lighting.pack(fill='x', pady=(0, 9))
        self.fields(lighting, 'Источник', self.light, 20)
        color_row = ttk.Frame(lighting)
        color_row.pack(fill='x', pady=(4, 0))
        self.swatch = tk.Label(color_row, width=3, background='#5698d9')
        self.swatch.pack(side='left', padx=(0, 5))
        ttk.Button(color_row, text='Цвет объекта…', command=self.choose_color).pack(side='left', fill='x', expand=True)

        texturing = ttk.LabelFrame(panel, text='Текстура', padding=8)
        texturing.pack(fill='x')
        ttk.Label(texturing, textvariable=self.texture_name, wraplength=228).pack(anchor='w')
        ttk.Button(texturing, text='Открыть изображение…', command=self.open_texture).pack(fill='x')
        ttk.Button(texturing, text='Шахматная сетка', command=self.reset_texture).pack(fill='x')
        ttk.Label(panel, text='Enter применяет введённые значения.').pack(anchor='w', pady=(7, 0))

    @staticmethod
    def combo(parent, variable, options, callback):
        box = ttk.Combobox(parent, textvariable=variable, values=tuple(options), state='readonly', width=23)
        box.pack(fill='x', pady=(0, 4))
        box.bind('<<ComboboxSelected>>', callback)

    def fields(self, parent, label, variables, increment):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=label, width=11).pack(side='left')
        for axis, variable in zip('XYZ', variables):
            ttk.Label(row, text=axis).pack(side='left', padx=(3, 1))
            field = ttk.Spinbox(row, textvariable=variable, from_=-10000, to=10000,
                                increment=increment, width=5, command=self.schedule)
            field.pack(side='left')
            field.bind('<Return>', self.schedule)

    @staticmethod
    def numbers(variables):
        values = tuple(float(variable.get().strip().replace(',', '.')) for variable in variables)
        if not np.isfinite(values).all() or max(map(abs, values)) > 10000:
            raise ValueError
        return values

    def set_surface(self, surface, name):
        self.surface, self.model_name = surface, name
        self.view.fit(surface.mesh, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.reset_transform()

    def select_shape(self, event=None):
        name = self.shape.get()
        self.set_surface(make_surface(SHAPES[name]), name)

    def open_obj(self):
        path = filedialog.askopenfilename(parent=self.root, initialdir=PROJECT / 'lab 7' / 'models',
                                          filetypes=[('Wavefront OBJ', '*.obj'), ('Все файлы', '*')])
        if path:
            try:
                surface = load_surface(path)
            except (OSError, ValueError) as error:
                self.status.set(f'Ошибка OBJ. {error}')
            else:
                self.shape.set('')
                self.set_surface(surface, surface.mesh.name)

    def choose_color(self):
        rgb, hex_color = colorchooser.askcolor(parent=self.root, color='#%02x%02x%02x' % tuple(self.color))
        if rgb is not None:
            self.color = np.rint(rgb).astype(int)
            self.swatch.configure(background=hex_color)
            self.schedule()

    def open_texture(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[
            ('Изображения', '*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff'), ('Все файлы', '*')
        ])
        if path:
            try:
                texture = Texture.from_file(path)
            except (OSError, ValueError) as error:
                self.status.set(f'Ошибка текстуры. {error}')
            else:
                self.select_texture(texture, path.rsplit('/', 1)[-1])

    def reset_texture(self):
        self.select_texture(Texture.checker(), 'Шахматная сетка')

    def select_texture(self, texture, name):
        self.texture = texture
        self.texture_name.set(name)
        self.mode.set('Текстурирование')
        self.schedule()

    def reset_transform(self):
        for variable, value in zip(self.offset + self.angles + self.scale, (0,) * 6 + (1,) * 3):
            variable.set(str(value))
        self.schedule()

    def start_drag(self, event):
        self.drag_position = event.x, event.y

    def drag(self, event):
        if self.drag_position is None:
            return
        x, y = self.drag_position
        self.drag_position = event.x, event.y
        self.view.yaw += (event.x - x) * 0.4
        self.view.pitch += (event.y - y) * 0.4
        self.schedule()

    def end_drag(self, event):
        self.drag_position = None

    def schedule(self, event=None):
        if self.draw_job is None:
            self.draw_job = self.root.after(20, self.draw)

    def draw(self):
        self.draw_job = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if min(width, height) < 2:
            return
        try:
            matrix = model_matrix(self.numbers(self.offset), self.numbers(self.angles),
                                  self.numbers(self.scale), self.surface.points.mean(axis=0))
            light = np.array(self.numbers(self.light))
        except ValueError:
            self.status.set('Введите числа от −10000 до 10000 и ненулевой масштаб.')
            return

        self.view.kind = PROJECTIONS[self.projection.get()]
        buffer = render(self.surface, matrix, self.view, width, height,
                        MODES[self.mode.get()], light, self.color, self.texture)
        self.photo = tk.PhotoImage(master=self.root, data=buffer.ppm(), format='PPM')
        self.canvas.itemconfigure(self.image_item, image=self.photo)
        mesh = self.surface.mesh
        self.status.set(f'{self.model_name}   ·   Вершин {len(mesh.vertices)}   ·   Граней {len(mesh.faces)}')


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
