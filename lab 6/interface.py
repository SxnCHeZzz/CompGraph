import math
import tkinter as tk
from tkinter import ttk
import numpy as np
import member2_transforms as matrices
from member1_models import SOLIDS
from member2_transforms import make_solid
from member3_projection import SceneView, camera_points, project_camera, projected_segments


ERRORS = {
    'zero_scale': 'Коэффициенты масштаба должны быть ненулевыми (по модулю не меньше 1e-8).',
    'same_axis_points': 'Точки A и B должны различаться: они задают прямую вращения.',
    'nonfinite': 'Преобразование дало слишком большие координаты.',
}


class App:
    def __init__(self, root):
        self.root = root
        root.title('Лабораторная №6. Многогранники и преобразования в 3D')
        root.geometry('1250x870'); root.minsize(1080, 760)
        self.mesh = make_solid('cube')
        self.view = SceneView()
        self.fields = {}
        self.last_matrix = np.eye(4)
        self.draw_axis_line = None
        self.drag_position = None
        self.center_rotation = tk.BooleanVar(value=True)
        self.center_scaling = tk.BooleanVar(value=True)
        self.axes_visible = tk.BooleanVar(value=True)
        self.vertices_visible = tk.BooleanVar(value=True)
        self.projection_kind = tk.StringVar(value='axonometric')
        bar = ttk.Frame(root, padding=8); bar.pack(fill='x')
        ttk.Label(bar, text='Многогранник:').pack(side='left')
        self.shape = ttk.Combobox(bar, values=list(SOLIDS), state='readonly', width=22)
        self.shape.set('Гексаэдр (куб)'); self.shape.pack(side='left', padx=5)
        self.shape.bind('<<ComboboxSelected>>', lambda _: self.reset_model())
        ttk.Button(bar, text='Сбросить фигуру', command=self.reset_model).pack(side='left')
        ttk.Radiobutton(bar, text='Аксонометрия', variable=self.projection_kind, value='axonometric',
                        command=self.change_projection).pack(side='left', padx=(15, 5))
        ttk.Radiobutton(bar, text='Перспектива', variable=self.projection_kind, value='perspective',
                        command=self.change_projection).pack(side='left')
        ttk.Button(bar, text='Вписать в окно', command=self.fit_view).pack(side='right')
        body = ttk.Frame(root); body.pack(fill='both', expand=True)
        controls = ttk.Notebook(body, width=350); controls.pack(side='left', fill='y', padx=(7, 4))
        transform_tab = ttk.Frame(controls, padding=8)
        view_tab = ttk.Frame(controls, padding=8)
        controls.add(transform_tab, text='Преобразования'); controls.add(view_tab, text='Обзор / матрица')
        group = self.group(transform_tab, 'Смещение')
        self.add_fields(group, [('dx', 'dx', 40), ('dy', 'dy', 0), ('dz', 'dz', 0)])
        ttk.Button(group, text='Сместить', command=lambda: self.transform('move')).pack(fill='x')
        group = self.group(transform_tab, 'Вращение вокруг координатной оси')
        row = self.add_fields(group, [('angle', 'Угол °', 30)])
        self.axis = ttk.Combobox(row, values=['X', 'Y', 'Z'], state='readonly', width=5)
        self.axis.set('Y'); self.axis.pack(side='left', padx=8)
        ttk.Checkbutton(group, text='Ось проходит через центр фигуры', variable=self.center_rotation).pack(anchor='w')
        ttk.Label(group, text='Без отметки — ось через начало координат.').pack(anchor='w')
        ttk.Button(group, text='Повернуть', command=lambda: self.transform('rotate')).pack(fill='x')
        group = self.group(transform_tab, 'Масштабирование')
        self.add_fields(group, [('kx', 'kx', 1.2), ('ky', 'ky', 1.2), ('kz', 'kz', 1.2)])
        ttk.Checkbutton(group, text='Относительно своего центра', variable=self.center_scaling).pack(anchor='w')
        ttk.Button(group, text='Масштабировать', command=lambda: self.transform('scale')).pack(fill='x')
        group = self.group(transform_tab, 'Отражение относительно плоскости')
        row = ttk.Frame(group); row.pack(fill='x')
        for plane in ['XY', 'XZ', 'YZ']:
            ttk.Button(row, text=plane, width=9, command=lambda p=plane: self.reflect(p)).pack(side='left', padx=2)
        group = self.group(transform_tab, 'Вращение вокруг произвольной прямой A → B')
        self.add_fields(group, [('ax', 'Ax', 0), ('ay', 'Ay', 0), ('az', 'Az', 0)])
        self.add_fields(group, [('bx', 'Bx', 1), ('by', 'By', 1), ('bz', 'Bz', 1)])
        self.add_fields(group, [('line_angle', 'Угол °', 30)])
        ttk.Button(group, text='Повернуть вокруг A → B', command=lambda: self.transform('line')).pack(fill='x')
        ttk.Label(transform_tab, text='Углы — в градусах, положительное направление — по правилу правой руки. '
                  'Центр — среднее координат вершин.', wraplength=315).pack(anchor='w', pady=6)
        group = self.group(view_tab, 'Параметры обзора')
        self.add_fields(group, [('yaw', 'Поворот Y °', self.view.yaw)], width=9)
        self.add_fields(group, [('pitch', 'Поворот X °', self.view.pitch)], width=9)
        self.add_fields(group, [('distance', 'Дистанция', self.view.distance)], width=9)
        ttk.Button(group, text='Применить обзор', command=self.apply_view).pack(fill='x')
        ttk.Button(group, text='Изометрический обзор', command=self.reset_view).pack(fill='x', pady=3)
        ttk.Label(view_tab, text='Увеличение изображения:').pack(anchor='w', pady=(6, 0))
        self.zoom = tk.DoubleVar(value=1)
        ttk.Scale(view_tab, from_=0.2, to=3, variable=self.zoom, command=self.change_zoom).pack(fill='x')
        ttk.Checkbutton(view_tab, text='Оси координат', variable=self.axes_visible, command=self.draw).pack(anchor='w')
        ttk.Checkbutton(view_tab, text='Вершины и центр', variable=self.vertices_visible, command=self.draw).pack(anchor='w')
        ttk.Label(view_tab, text='ЛКМ + движение по холсту — изменить обзор. '
                  'Это не меняет координаты модели. Зелёная точка — центр, оранжевая линия — последняя произвольная ось.',
                  wraplength=315).pack(anchor='w', pady=10)
        ttk.Label(view_tab, text='Последняя матрица преобразования:').pack(anchor='w')
        self.matrix_text = tk.Text(view_tab, height=6, width=35, font=('Menlo', 9), state='disabled')
        self.matrix_text.pack(fill='x', pady=4)
        ttk.Label(view_tab, text='[x y z 1] × M. Все геометрические преобразования и обе проекции — матрицы 4×4. '
                  'При перспективе после проекции выполняется деление на w.', wraplength=315).pack(anchor='w', pady=6)
        display = ttk.Frame(body); display.pack(side='right', fill='both', expand=True)
        self.info = ttk.Label(display, padding=6); self.info.pack(side='top', fill='x')
        self.status = ttk.Label(display, text='Выберите преобразование и задайте параметры.', wraplength=800, padding=8)
        self.status.pack(side='bottom', fill='x')
        self.canvas = tk.Canvas(display, bg='#f8fafc', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda _: self.draw())
        self.canvas.bind('<Button-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag_view)
        self.canvas.bind('<ButtonRelease-1>', lambda _: self.end_drag())
        self.update_matrix()
        self.root.after_idle(self.draw)

    def group(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=6)
        frame.pack(fill='x', pady=(0, 8))
        return frame

    def add_fields(self, parent, values, width=6):
        row = ttk.Frame(parent); row.pack(fill='x', pady=3)
        for key, title, value in values:
            ttk.Label(row, text=title).pack(side='left', padx=(0, 3))
            field = ttk.Entry(row, width=width); field.insert(0, str(value)); field.pack(side='left', padx=(0, 5))
            self.fields[key] = field
        return row

    def number(self, key):
        value = float(self.fields[key].get().replace(',', '.'))
        if not math.isfinite(value): raise ValueError('nonfinite')
        return value

    def values(self, *keys):
        return tuple(self.number(key) for key in keys)

    def update_matrix(self):
        text = '\n'.join(' '.join(f'{value:9.3f}' for value in row) for row in self.last_matrix)
        self.matrix_text.config(state='normal'); self.matrix_text.delete('1.0', 'end')
        self.matrix_text.insert('1.0', text); self.matrix_text.config(state='disabled')

    def apply_matrix(self, matrix, message):
        result = self.mesh.transformed(matrix)
        if np.max(np.abs(result.coordinates())) > 1e8:
            raise ValueError('nonfinite')
        self.mesh = result; self.last_matrix = matrix
        self.update_matrix(); self.status.config(text=message); self.draw()

    def transform(self, action):
        try:
            if action == 'move':
                matrix = matrices.translation(*self.values('dx', 'dy', 'dz'))
            elif action == 'rotate':
                matrix = matrices.rotation(self.axis.get(), self.number('angle'))
                if self.center_rotation.get(): matrix = matrices.around(matrix, self.mesh.center.as_array())
            elif action == 'scale':
                matrix = matrices.scaling(*self.values('kx', 'ky', 'kz'))
                if self.center_scaling.get(): matrix = matrices.around(matrix, self.mesh.center.as_array())
            else:
                a, b = self.values('ax', 'ay', 'az'), self.values('bx', 'by', 'bz')
                matrix = matrices.rotation_line(a, b, self.number('line_angle'))
            self.apply_matrix(matrix, 'Преобразование применено. Масштаб обзора сохранён.')
            if action == 'line':
                self.draw_axis_line = (a, b); self.draw()
        except (ValueError, OverflowError, np.linalg.LinAlgError) as error:
            self.status.config(text=ERRORS.get(str(error), 'Проверьте числовые параметры преобразования.'))

    def reflect(self, plane):
        try: self.apply_matrix(matrices.reflection(plane), f'Выполнено отражение относительно {plane}.')
        except ValueError as error: self.status.config(text=ERRORS.get(str(error), str(error)))

    def reset_model(self):
        self.mesh = make_solid(SOLIDS[self.shape.get()]); self.draw_axis_line = None
        self.last_matrix = np.eye(4); self.update_matrix()
        self.status.config(text='Создан исходный многогранник радиуса 100.'); self.reset_view()

    def change_projection(self):
        self.view.kind = self.projection_kind.get(); self.draw()

    def change_zoom(self, _=None):
        self.view.zoom = self.zoom.get(); self.draw()

    def sync_view_fields(self):
        for name in ['yaw', 'pitch', 'distance']:
            self.fields[name].delete(0, 'end'); self.fields[name].insert(0, f'{getattr(self.view, name):.6g}')
        self.zoom.set(self.view.zoom)

    def apply_view(self):
        try:
            yaw, pitch, distance = self.values('yaw', 'pitch', 'distance')
            if not 2 <= distance <= 100000000: raise ValueError
        except (ValueError, OverflowError):
            self.status.config(text='Введите конечные углы и дистанцию от 2 до 100 000 000.'); return
        self.view.yaw, self.view.pitch, self.view.distance = yaw, pitch, distance
        self.view.far = max(1000000, distance*3)
        self.draw()

    def reset_view(self):
        self.view = SceneView(kind=self.projection_kind.get())
        self.sync_view_fields(); self.draw()

    def fit_view(self):
        self.view.fit(self.mesh, self.canvas.winfo_width(), self.canvas.winfo_height())
        self.sync_view_fields(); self.draw()
        self.status.config(text='Обзор центрирован на модели; её координаты не изменены.')

    def start_drag(self, event): self.drag_position = (event.x, event.y)

    def end_drag(self): self.drag_position = None

    def drag_view(self, event):
        if self.drag_position is None: return
        dx, dy = event.x-self.drag_position[0], event.y-self.drag_position[1]
        self.view.yaw += dx*0.4; self.view.pitch += dy*0.4
        self.drag_position = (event.x, event.y); self.sync_view_fields(); self.draw()

    def draw_lines(self, vertices, pairs, color, width=1, dash=None):
        for _, _, screen in projected_segments(vertices, pairs, self.view, self.canvas.winfo_width(), self.canvas.winfo_height()):
            self.canvas.create_line(*screen[0, :2], *screen[1, :2], fill=color, width=width, dash=dash)

    def dot(self, screen, color, radius):
        x, y = screen[:2]
        if -10 <= x <= self.canvas.winfo_width()+10 and -10 <= y <= self.canvas.winfo_height()+10:
            self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=color, outline='white')

    def draw(self):
        self.canvas.delete('all')
        width, height = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        if self.axes_visible.get():
            for axis, color in enumerate(['#cc5454', '#40935c', '#5589c8']):
                a, b = np.zeros(3), np.zeros(3); a[axis], b[axis] = -150, 150
                self.draw_lines([a, b], [(0, 1)], color, 1)
                point = camera_points([b], self.view)[0]
                if self.view.near <= point[2] <= self.view.far:
                    screen = project_camera([point], self.view, width, height)[0]
                    if 0 <= screen[0] <= width and 0 <= screen[1] <= height:
                        self.canvas.create_text(screen[0]+10, screen[1], text='XYZ'[axis], fill=color)
        vertices = self.mesh.coordinates()
        segments = projected_segments(vertices, self.mesh.edges(), self.view, width, height)
        for _, _, screen in segments:
            self.canvas.create_line(*screen[0, :2], *screen[1, :2], fill='#234d7c', width=2)
        if self.draw_axis_line is not None:
            a, b = map(np.asarray, self.draw_axis_line)
            direction = (b-a) / np.linalg.norm(b-a)
            center = self.mesh.center.as_array()
            closest = a + np.dot(center-a, direction)*direction
            radius = max(150, max(np.linalg.norm(vertices-center, axis=1))*1.5)
            self.draw_lines([closest-radius*direction, closest+radius*direction], [(0, 1)], '#cf7c19', 2, (5, 3))
        if self.vertices_visible.get():
            points = camera_points(np.vstack([vertices, self.mesh.center.as_array()]), self.view)
            for index, point in enumerate(points):
                if self.view.near <= point[2] <= self.view.far:
                    screen = project_camera([point], self.view, width, height)[0]
                    self.dot(screen, '#228351' if index == len(vertices) else '#234d7c', 5 if index == len(vertices) else 3)
        center = self.mesh.center
        self.info.config(text=f'Вершин: {len(vertices)}; рёбер: {len(self.mesh.edges())}; граней: {len(self.mesh.faces)}. '
                         f'Центр: ({center.x:.2f}, {center.y:.2f}, {center.z:.2f}).')
        if not segments:
            self.canvas.create_text(width/2, height/2, text='Модель вне диапазона обзора. Нажмите «Вписать в окно».', fill='#8b4a33')


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
