"""Лабораторная №8. Грани, Z-буфер и перспективная камера."""

from dataclasses import replace
import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT / 'lab 7'))

from lab6_base import Polyhedron, SOLIDS, make_solid, matrices
from member1_obj import load_obj
from member2_revolution import generate_revolution
from member3_camera import OrbitView
from member3_projection import camera_points, clip_depth, project_camera, projected_segments

from rendering import OrbitCamera, clip_polygon, face_visibility, orient_closed_mesh, render_scene
from viewport import Viewport, view_buttons, workspace


class App:
    def __init__(self, root):
        self.root = root
        root.title('Лабораторная №8. Видимость и камера')

        self.mesh = make_solid('cube')
        self.mesh_title = 'Гексаэдр (куб)'
        self.radius = 100
        self.object_angle = 0
        self.orbit = OrbitView()
        self.camera = OrbitCamera()
        self.scene_view = OrbitView()
        self.models = []
        self.model_names = []
        self.pending_draw = None
        self.image = None

        self.projection = tk.StringVar(value='Параллельная')
        self.cull_faces = tk.BooleanVar(value=True)
        self.cull_camera = tk.BooleanVar(value=True)
        self.wire_camera = tk.BooleanVar(value=False)
        self.show_normals = tk.BooleanVar(value=True)
        self.spin_faces = tk.BooleanVar(value=False)
        self.spin_camera = tk.BooleanVar(value=False)
        self.depth_test = tk.BooleanVar(value=True)
        self.show_depth = tk.BooleanVar(value=False)
        self.reverse_order = tk.BooleanVar(value=False)
        self.yaw = tk.DoubleVar(value=-45)
        self.pitch = tk.DoubleVar(value=35)
        self.distance = tk.DoubleVar(value=3.7)
        self.fov = tk.DoubleVar(value=45)
        self.status = tk.StringVar()

        toolbar, body = workspace(root, 'Удаление невидимых граней')
        ttk.Label(toolbar, text='Модель').pack(side='left', padx=(0, 6))
        self.shape = ttk.Combobox(toolbar, values=(*SOLIDS, 'Шар'), state='readonly', width=22)
        self.shape.set(self.mesh_title)
        self.shape.pack(side='left')
        self.shape.bind('<<ComboboxSelected>>', self.select_solid)
        ttk.Button(toolbar, text='Открыть OBJ…', command=self.open_obj).pack(side='left', padx=6)
        view_buttons(toolbar, self.fit_view, self.reset_view)

        self.tabs = ttk.Notebook(body, width=310)
        self.tabs.pack(side='left', fill='y', padx=(0, 8))
        for title, build in [('Грани', self.build_faces_tab),
                             ('Z-буфер', self.build_depth_tab),
                             ('Камера', self.build_camera_tab)]:
            panel = ttk.Frame(self.tabs, padding=8)
            self.tabs.add(panel, text=title)
            build(panel)
        self.tabs.bind('<<NotebookTabChanged>>', self.schedule_draw)

        self.viewport = Viewport(body, self.status, self.schedule_draw, self.rotate_view,
                                 self.zoom_view, self.fit_view)
        self.viewport.pack(fill='both', expand=True)
        self.canvas = self.viewport.canvas
        self.reset_scene()
        root.after(40, self.animate)

    @property
    def mode(self):
        return self.tabs.index(self.tabs.select())

    def checkbutton(self, panel, text, variable):
        ttk.Checkbutton(panel, text=text, variable=variable,
                        command=self.schedule_draw).pack(anchor='w', pady=2)

    def slider(self, panel, title, variable, start, end, step=1, *, digits=0):
        tk.Scale(panel, label=title, variable=variable, from_=start, to=end,
                 resolution=step, digits=digits, orient='horizontal', highlightthickness=0,
                 command=self.schedule_draw).pack(fill='x', pady=2)

    def angles(self, panel):
        self.slider(panel, 'Азимут, °', self.yaw, -180, 180, -1, digits=8)
        self.slider(panel, 'Наклон, °', self.pitch, -180, 180, -1, digits=8)

    def build_faces_tab(self, panel):
        ttk.Label(panel, text='Проекция').pack(anchor='w')
        selection = ttk.Combobox(panel, textvariable=self.projection, state='readonly',
                                 values=('Параллельная', 'Перспективная'))
        selection.pack(fill='x', pady=(2, 8))
        selection.bind('<<ComboboxSelected>>', self.schedule_draw)
        self.angles(panel)
        self.checkbutton(panel, 'Отсекать нелицевые грани', self.cull_faces)
        self.checkbutton(panel, 'Показывать нормали', self.show_normals)
        self.checkbutton(panel, 'Вращать объект', self.spin_faces)
        ttk.Button(panel, text='Сбросить поворот объекта',
                   command=self.reset_object_rotation).pack(fill='x', pady=(8, 0))

    def build_depth_tab(self, panel):
        ttk.Label(panel, text='Объект сцены').pack(anchor='w')
        self.object_box = ttk.Combobox(panel, state='readonly', width=23)
        self.object_box.pack(fill='x', pady=(2, 4))
        ttk.Button(panel, text='Добавить многогранник', command=self.add_solid).pack(fill='x')
        buttons = ttk.Frame(panel)
        buttons.pack(fill='x', pady=(3, 8))
        ttk.Button(buttons, text='Удалить', command=self.remove_model).pack(side='left', expand=True, fill='x')
        ttk.Button(buttons, text='Демо-сцена', command=self.reset_scene).pack(side='left', expand=True, fill='x')
        self.checkbutton(panel, 'Проверять глубину', self.depth_test)
        self.checkbutton(panel, 'Карта глубины', self.show_depth)
        self.checkbutton(panel, 'Обратный порядок отрисовки', self.reverse_order)
        self.transform_controls(panel, 'Перенос', (20, 0, 0), self.translation)
        self.transform_controls(panel, 'Поворот X → Y → Z, °', (0, 15, 0), self.rotation)
        self.transform_controls(panel, 'Масштабирование', (1.2, 1.2, 1.2), self.scaling)

    def transform_controls(self, panel, title, defaults, operation):
        group = ttk.LabelFrame(panel, text=title, padding=5)
        group.pack(fill='x', pady=(6, 0))
        row = ttk.Frame(group)
        row.pack(fill='x')
        entries = []
        for axis, default in zip('XYZ', defaults):
            ttk.Label(row, text=axis).pack(side='left', padx=(0, 2))
            field = ttk.Entry(row, width=5)
            field.insert(0, str(default))
            field.pack(side='left', padx=(0, 4))
            entries.append(field)
        ttk.Button(group, text='Применить',
                   command=lambda: self.transform_selected(operation, entries)).pack(fill='x', pady=(4, 0))

    def build_camera_tab(self, panel):
        self.angles(panel)
        self.slider(panel, 'Дистанция, в радиусах модели', self.distance, 0.3, 12, 0.1)
        self.slider(panel, 'Поле зрения, °', self.fov, 20, 120)
        self.checkbutton(panel, 'Скрывать нелицевые грани', self.cull_camera)
        self.checkbutton(panel, 'Каркас', self.wire_camera)
        self.checkbutton(panel, 'Автовращение камеры', self.spin_camera)

    @staticmethod
    def translation(values, center):
        return matrices.translation(*values)

    @staticmethod
    def rotation(values, center):
        transform = matrices.rotation('X', values[0]) @ matrices.rotation('Y', values[1])
        return matrices.around(transform @ matrices.rotation('Z', values[2]), center)

    @staticmethod
    def scaling(values, center):
        return matrices.around(matrices.scaling(*values), center)

    def transform_selected(self, operation, entries):
        selected = self.object_box.current()
        if selected == -1:
            self.status.set('Выберите объект сцены.')
            return
        try:
            values = tuple(float(field.get().replace(',', '.')) for field in entries)
            if not np.isfinite(values).all():
                raise ValueError
            mesh = self.models[selected]
            result = mesh.transformed(operation(values, mesh.center.as_array()))
            if np.max(np.abs(result.coordinates())) > 1e8:
                raise ValueError
        except (ValueError, OverflowError, np.linalg.LinAlgError):
            self.status.set('Проверьте значения преобразования.')
            return
        self.models[selected] = result
        self.schedule_draw()

    def select_solid(self, event=None):
        if self.mode != 1:
            title = self.shape.get()
            self.set_mesh(self.make_selected_shape(title), title)

    @staticmethod
    def make_selected_shape(title):
        if title != 'Шар':
            return make_solid(SOLIDS[title])
        profile = [(100 * math.sin(angle), -100 * math.cos(angle), 0)
                   for angle in np.linspace(0, math.pi, 13)]
        return generate_revolution(profile, 'Y', 20)

    def open_obj(self):
        path = filedialog.askopenfilename(parent=self.root, initialdir=PROJECT / 'lab 7' / 'models',
                                          filetypes=[('Wavefront OBJ', '*.obj'), ('Все файлы', '*')])
        if not path:
            return
        try:
            mesh = load_obj(path)
        except (OSError, UnicodeError, ValueError) as error:
            self.status.set(f'Не удалось открыть OBJ. {error}')
            return
        if self.mode == 1:
            self.add_model(mesh, Path(path).name)
        else:
            self.set_mesh(orient_closed_mesh(mesh), Path(path).name)

    def set_mesh(self, mesh, title):
        self.mesh, self.mesh_title = mesh, title
        self.object_angle = 0
        self.radius = float(np.linalg.norm(mesh.coordinates() - mesh.center.as_array(), axis=1).max())
        self.fit_view()

    def add_solid(self):
        title = self.shape.get()
        self.add_model(self.make_selected_shape(title), title)

    def add_model(self, mesh, title):
        self.models.append(mesh)
        self.model_names.append(title)
        self.update_objects(len(self.models) - 1)
        self.fit_scene()
        self.schedule_draw()

    def remove_model(self):
        selected = self.object_box.current()
        if selected != -1:
            del self.models[selected]
            del self.model_names[selected]
            self.update_objects(min(selected, len(self.models) - 1))
            self.schedule_draw()

    def update_objects(self, selected):
        self.object_box.configure(values=[f'{i}. {name}' for i, name in enumerate(self.model_names, 1)])
        if selected >= 0:
            self.object_box.current(selected)
        else:
            self.object_box.set('')

    def reset_scene(self):
        cube = make_solid('cube')
        self.models = [
            cube.transformed(matrices.scaling(1.4, 0.54, 0.65)
                             @ matrices.rotation('Y', 21) @ matrices.translation(-60, 2, -18)),
            cube.transformed(matrices.scaling(0.65, 1.25, 0.55)
                             @ matrices.rotation('Z', -18) @ matrices.translation(48, 15, -5)),
            cube.transformed(matrices.scaling(0.82, 0.7, 0.8)
                             @ matrices.rotation('X', 13) @ matrices.translation(1, -58, 91)),
        ]
        self.model_names = ['Синий блок', 'Оранжевый блок', 'Зелёный блок']
        self.update_objects(0)
        self.fit_scene()
        self.schedule_draw()

    def fit_scene(self):
        if self.models:
            vertices = np.concatenate([mesh.coordinates() for mesh in self.models])
            self.scene_view.fit(Polyhedron(vertices, []), self.canvas.winfo_width(), self.canvas.winfo_height())

    def fit_view(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if self.mode == 1:
            self.fit_scene()
        else:
            self.orbit.fit(self.mesh, width, height)
            aspect = max(1, width) / max(1, height)
            half_fov = math.tan(math.radians(self.fov.get() / 2))
            self.distance.set(max(3.7, 1 + 1.15 / (half_fov * min(1, aspect))))
        self.schedule_draw()

    def reset_view(self):
        if self.mode == 1:
            self.scene_view = OrbitView()
        else:
            self.orbit = OrbitView()
            self.yaw.set(self.orbit.yaw)
            self.pitch.set(self.orbit.pitch)
        self.fit_view()

    def zoom_view(self, factor):
        view = self.scene_view if self.mode == 1 else self.orbit
        view.zoom = max(0.2, min(5, view.zoom * factor))
        self.schedule_draw()

    def rotate_view(self, dx, dy):
        if self.mode == 1:
            self.scene_view.drag(dx, dy)
        else:
            self.orbit.yaw, self.orbit.pitch = self.yaw.get(), self.pitch.get()
            self.orbit.drag(dx, dy)
            self.yaw.set(self.orbit.yaw)
            self.pitch.set(self.orbit.pitch)
        self.schedule_draw()

    def reset_object_rotation(self):
        self.object_angle = 0
        self.schedule_draw()

    def animate(self):
        if self.mode == 0 and self.spin_faces.get():
            self.object_angle = (self.object_angle + 1.5) % 360
            self.schedule_draw()
        if self.mode == 2 and self.spin_camera.get():
            self.yaw.set((self.yaw.get() + 1.5 + 180) % 360 - 180)
            self.schedule_draw()
        self.root.after(40, self.animate)

    def schedule_draw(self, event=None):
        if self.pending_draw is None:
            self.pending_draw = self.root.after_idle(self.draw)

    def draw(self):
        self.pending_draw = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if min(width, height) < 2:
            return
        self.canvas.delete('all')
        if self.mode == 1:
            self.draw_depth(width, height)
            self.viewport.draw_axes(self.scene_view)
            return
        view = replace(self.orbit, yaw=self.yaw.get(), pitch=self.pitch.get())
        if self.mode == 0:
            if self.projection.get() == 'Перспективная':
                view.kind = 'perspective'
            self.draw_faces(view, width, height)
        else:
            self.camera.target = view.target
            self.camera.yaw, self.camera.pitch, self.camera.roll = view.yaw, view.pitch, view.roll
            self.camera.distance = self.radius * self.distance.get()
            self.camera.near, self.camera.far = 0.04 * self.radius, 30 * self.radius
            self.camera.fov = self.fov.get()
            self.camera.zoom = view.zoom
            self.draw_camera(self.camera, width, height)
            view = self.camera
        self.viewport.draw_axes(view)

    def draw_depth(self, width, height):
        enabled = self.depth_test.get()
        frame = render_scene(self.models, self.scene_view, width, height,
                             depth_test=enabled, reverse=self.reverse_order.get())
        self.show_frame(frame, show_depth=self.show_depth.get())
        label = 'Z-буфер включён' if enabled else 'Последняя грань перекрывает предыдущие'
        self.status.set(f'{label}  ·  Объектов {len(self.models)}')

    def draw_faces(self, view, width, height):
        mesh = self.mesh
        if self.object_angle:
            rotation = matrices.around(matrices.rotation('Y', self.object_angle), mesh.center.as_array())
            mesh = mesh.transformed(rotation)
        points = camera_points(mesh.coordinates(), view)
        centers, normals, front = face_visibility(mesh, points, view)
        cull = self.cull_faces.get()
        visible = []
        for index, face in enumerate(mesh.faces):
            if not cull or front[index]:
                polygon = clip_polygon(points[list(face.indices)], view.near, view.far)
                if len(polygon) >= 3:
                    visible.append((index, polygon))
        # Для заливки в этой демонстрации дальние грани рисуются первыми.
        for index, polygon in sorted(visible, key=lambda pair: -centers[pair[0], 2]):
            screen = project_camera(polygon, view, width, height)
            light = 0.62 + 0.38 * max(0, -normals[index, 2])
            fill = '#%02x%02x%02x' % tuple(round(channel * light) for channel in (136, 189, 235))
            self.canvas.create_polygon(*screen[:, :2].ravel(), outline='#254b71',
                                       fill=fill if cull else '', width=2)
        if self.show_normals.get():
            for index, _ in visible:
                start = centers[index]
                end = start + normals[index] * (self.radius * 0.38)
                segment = clip_depth(start, end, view.near, view.far)
                if segment is not None:
                    screen = project_camera(segment, view, width, height)
                    self.canvas.create_line(*screen[:, :2].ravel(), fill='#ca4949', width=2, arrow=tk.LAST)
        self.status.set(f'{self.mesh_title}  ·  Граней показано {len(visible)} из {len(self.mesh.faces)}')

    def show_frame(self, frame, *, show_depth=False):
        self.image = tk.PhotoImage(master=self.root, data=frame.ppm(show_depth), format='PPM')
        self.canvas.create_image(0, 0, image=self.image, anchor='nw')

    def draw_camera(self, view, width, height):
        mesh = self.mesh
        vertices = mesh.coordinates()
        if self.cull_camera.get():
            _, _, front = face_visibility(mesh, camera_points(vertices, view), view)
            mesh = Polyhedron(mesh.vertices, [face for face, visible in zip(mesh.faces, front) if visible])
        if self.wire_camera.get():
            for _, _, screen in projected_segments(vertices, mesh.edges(), view, width, height):
                self.canvas.create_line(*screen[:, :2].ravel(), fill='#254b71', width=2)
        else:
            self.show_frame(render_scene([mesh], view, width, height))

        pos_text = ', '.join(f'{value:.1f}' for value in view.position)
        dir_text = ', '.join(f'{value:.2f}' for value in view.direction)
        self.status.set(f'{self.mesh_title}  ·  Камера ({pos_text})  ·  Направление ({dir_text})')


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
