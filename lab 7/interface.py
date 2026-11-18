from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from lab6_base import BaseApp, copy_mesh, make_solid, SOLIDS
from member1_obj import load_obj, save_obj
from member2_revolution import DEFAULT_PROFILE, generate_revolution
from member3_surface import FUNCTIONS, generate_surface


class App(BaseApp):
    def __init__(self, root):
        super().__init__(root, compact=True)
        root.title('Лабораторная №7. Построение трёхмерных моделей')
        root.geometry('1200x800')
        root.minsize(960, 700)
        self.vertices_visible.set(False)
        self.original_mesh = copy_mesh(self.mesh)
        self.model_name = tk.StringVar(value='Исходный куб')
        self.shape.bind('<<ComboboxSelected>>', lambda _: self.select_solid())
        revolution_tab = ttk.Frame(self.controls, padding=8)
        surface_tab = ttk.Frame(self.controls, padding=8)
        self.controls.add(revolution_tab, text='Вращение')
        self.controls.add(surface_tab, text='График')
        self.create_revolution_tab(revolution_tab)
        self.create_surface_tab(surface_tab)

        actions = ttk.Frame(self.canvas.master, padding=(0, 0, 6, 4))
        actions.pack(fill='x', before=self.info)
        ttk.Button(actions, text='Открыть OBJ', command=self.open_model).pack(side='left')
        ttk.Button(actions, text='Сохранить OBJ', command=self.save_current).pack(side='left', padx=4)
        ttk.Button(actions, text='Сбросить модель', command=self.reset_model).pack(side='left')
        ttk.Label(actions, textvariable=self.model_name).pack(side='left', fill='x', expand=True, padx=(8, 0))
        self.info.configure(padding=(6, 2))
        self.info.pack_configure(side='bottom', after=self.status)
        self.status.configure(text='', padding=(6, 2), wraplength=560)

    def create_revolution_tab(self, parent):
        profile_group = self.group(parent, 'Точки образующей')
        table_frame = ttk.Frame(profile_group)
        table_frame.pack(fill='x')
        self.profile = ttk.Treeview(table_frame, columns=('X', 'Y', 'Z'), show='headings',
                                   selectmode='browse', height=6)
        for axis in ('X', 'Y', 'Z'):
            self.profile.heading(axis, text=axis)
            self.profile.column(axis, width=70, anchor='center')
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.profile.yview)
        self.profile.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.profile.pack(fill='x', expand=True)
        for point in DEFAULT_PROFILE:
            self.profile.insert('', 'end', values=point)
        self.profile.bind('<<TreeviewSelect>>', self.select_profile_point)
        self.add_fields(profile_group, [('profile_x', 'X', 45), ('profile_y', 'Y', 0), ('profile_z', 'Z', 0)])
        row = ttk.Frame(profile_group)
        row.pack(fill='x')
        for title, command in [('Добавить', self.add_profile_point),
                               ('Изменить', self.edit_profile_point),
                               ('Удалить', self.delete_profile_point)]:
            ttk.Button(row, text=title, width=5, command=command).pack(side='left', fill='x', expand=True)

        rotation_group = self.group(parent, 'Ось и разбиения')
        row = self.add_fields(rotation_group, [('revolution_n', 'Разбиений', 24)])
        ttk.Label(row, text='Ось').pack(side='left', padx=(4, 3))
        self.revolution_axis = ttk.Combobox(row, values=['X', 'Y', 'Z'], state='readonly', width=4)
        self.revolution_axis.set('Y')
        self.revolution_axis.pack(side='left')
        ttk.Button(parent, text='Построить фигуру', command=self.build_revolution).pack(fill='x')

    def create_surface_tab(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=(0, 8))
        ttk.Label(row, text='z =').pack(side='left')
        self.function = ttk.Combobox(row, values=list(FUNCTIONS), state='readonly', width=22)
        self.function.current(0)
        self.function.pack(side='left', fill='x', expand=True, padx=(5, 0))

        bounds = self.group(parent, 'Диапазоны')
        self.add_fields(bounds, [('x0', 'X от', -5), ('x1', 'до', 5)])
        self.add_fields(bounds, [('y0', 'Y от', -5), ('y1', 'до', 5)])
        divisions = self.group(parent, 'Количество разбиений')
        self.add_fields(divisions, [('surface_nx', 'X', 30), ('surface_ny', 'Y', 30)])
        ttk.Button(parent, text='Построить график', command=self.build_surface).pack(fill='x')

    def activate_mesh(self, mesh, title):
        self.original_mesh = copy_mesh(mesh)
        self.mesh = copy_mesh(mesh)
        self.last_matrix = np.eye(4); self.draw_axis_line = None
        self.model_name.set(title)
        self.update_matrix()
        self.view.fit(self.mesh, max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height()))
        self.sync_view_fields(); self.draw()
        self.status.config(text='')

    def select_solid(self):
        self.activate_mesh(make_solid(SOLIDS[self.shape.get()]), self.shape.get())

    def reset_model(self):
        self.mesh = copy_mesh(self.original_mesh)
        self.last_matrix = np.eye(4); self.draw_axis_line = None
        self.update_matrix(); self.fit_view()
        self.status.config(text='Преобразования сброшены.')

    def open_model(self):
        path = filedialog.askopenfilename(
            parent=self.root,
            initialdir=Path(__file__).resolve().parent / 'models',
            filetypes=[('Wavefront OBJ', '*.obj'), ('Все файлы', '*')],
        )
        if path: self.load_path(path)

    def load_path(self, path):
        try: mesh = load_obj(path)
        except (OSError, UnicodeError, ValueError) as error:
            self.status.config(text=f'Не удалось открыть OBJ: {error}'); return
        self.activate_mesh(mesh, f'OBJ: {Path(path).name}')

    def save_current(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension='.obj', filetypes=[('Wavefront OBJ', '*.obj')]
        )
        if path:
            try: save_obj(self.mesh, path)
            except (OSError, ValueError) as error:
                self.status.config(text=f'Не удалось сохранить OBJ: {error}')
            else: self.status.config(text=f'Сохранено: {Path(path).name}')

    def select_profile_point(self, event=None):
        selected = self.profile.selection()
        if selected:
            for key, value in zip(('profile_x', 'profile_y', 'profile_z'), self.profile.item(selected[0], 'values')):
                self.fields[key].delete(0, 'end'); self.fields[key].insert(0, str(value))

    def profile_coordinates(self):
        return self.values('profile_x', 'profile_y', 'profile_z')

    def add_profile_point(self):
        try: point = self.profile_coordinates()
        except (ValueError, OverflowError):
            self.status.config(text='Координаты точки должны быть конечными числами.'); return
        item = self.profile.insert('', 'end', values=point)
        self.profile.selection_set(item); self.profile.see(item)

    def edit_profile_point(self):
        selected = self.profile.selection()
        if not selected:
            self.status.config(text='Выберите строку образующей для изменения.'); return
        try: point = self.profile_coordinates()
        except (ValueError, OverflowError):
            self.status.config(text='Координаты точки должны быть конечными числами.'); return
        self.profile.item(selected[0], values=point)

    def delete_profile_point(self):
        for item in self.profile.selection(): self.profile.delete(item)

    def integer(self, key):
        try: return int(self.fields[key].get())
        except ValueError as error: raise ValueError('Количество разбиений должно быть целым числом.') from error

    def build_revolution(self):
        try:
            profile = [tuple(float(value) for value in self.profile.item(item, 'values'))
                       for item in self.profile.get_children()]
            mesh = generate_revolution(profile, self.revolution_axis.get(), self.integer('revolution_n'))
        except (ValueError, OverflowError) as error:
            self.status.config(text=f'Не удалось построить фигуру вращения: {error}'); return
        self.activate_mesh(mesh, f'Фигура вращения, ось {self.revolution_axis.get()}')

    def build_surface(self):
        try:
            mesh = generate_surface(self.function.get(), *self.values('x0', 'x1', 'y0', 'y1'),
                                    self.integer('surface_nx'), self.integer('surface_ny'))
        except (ValueError, OverflowError) as error:
            self.status.config(text=f'Не удалось построить поверхность: {error}'); return
        self.activate_mesh(mesh, f'z = {self.function.get()}')


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
