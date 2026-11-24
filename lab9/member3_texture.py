"""Участник 3. UV-развёртка, атрибуты OBJ и выборка цвета из текстуры."""

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from member1_lighting import corner_normals, normalize

PROJECT = Path(__file__).resolve().parent.parent
for directory in ('lab 7', 'lab 8'):
    path = str(PROJECT / directory)
    if path not in sys.path:
        sys.path.append(path)

from lab6_base import Polyhedron, make_solid
from member1_obj import load_obj
from member2_revolution import generate_revolution
from rendering import orient_closed_mesh


@dataclass
class Surface:
    mesh: Polyhedron
    points: np.ndarray
    face_normals: np.ndarray
    normals: tuple
    uv: tuple

    @classmethod
    def from_mesh(cls, mesh, obj_corners=None):
        points = mesh.coordinates()
        face_normals = mesh.face_normals()
        uv = []
        for i, (face, face_normal) in enumerate(zip(mesh.faces, face_normals)):
            face_uv = planar_uv(points[list(face.indices)], face_normal)
            if obj_corners is not None:
                for j, index in enumerate(face.indices):
                    texcoord, _ = obj_corners[i][index]
                    if texcoord is not None:
                        face_uv[j] = texcoord
            uv.append(face_uv)
        normals = corner_normals(mesh, face_normals, obj_corners)
        return cls(mesh, points, face_normals, normals, tuple(uv))


def planar_uv(points, normal):
    """Локальная плоская развёртка. На швах UV задаются для углов каждой грани."""
    local = points - points[0]
    horizontal = normalize(local[1])
    vertical = np.cross(normal, horizontal)
    axes = np.column_stack((horizontal, vertical))
    uv = local @ axes
    extent = np.ptp(uv, axis=0)
    return (uv - uv.min(axis=0)) / np.where(extent > 1e-12, extent, 1)


def make_surface(kind):
    if kind == 'sphere':
        angles = np.linspace(0, np.pi, 15)
        profile = [(100 * np.sin(a), -100 * np.cos(a), 0) for a in angles]
        mesh = orient_closed_mesh(generate_revolution(profile, 'Y', 24))
    else:
        mesh = make_solid(kind)
    return Surface.from_mesh(mesh)


def obj_index(field, count):
    index = int(field)
    if index == 0 or index < -count:
        raise ValueError('Индекс OBJ выходит за границы списка.')
    return index - 1 if index > 0 else count + index


def load_surface(filename):
    # ЛР7 читает и проверяет геометрию. Здесь забираем два оставшихся индекса угла.
    mesh = orient_closed_mesh(load_obj(filename))
    texcoords, normals, face_records = [], [], []
    vertex_count = 0
    with open(filename, encoding='utf-8-sig') as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.split('#', 1)[0].split()
            if not fields:
                continue
            kind, *values = fields
            try:
                if kind == 'v':
                    vertex_count += 1
                elif kind == 'vt':
                    if not 1 <= len(values) <= 3:
                        raise ValueError('Ожидаются координаты текстуры vt.')
                    uv = [float(value) for value in values[:2]]
                    if not np.isfinite(uv).all():
                        raise ValueError('Координаты vt должны быть конечными.')
                    texcoords.append((uv + [0])[:2])
                elif kind == 'vn':
                    if len(values) != 3:
                        raise ValueError('Ожидаются три компоненты нормали vn.')
                    normal = np.array(values, dtype=float)
                    if not np.isfinite(normal).all() or not np.any(normal):
                        raise ValueError('Нормаль vn должна быть конечной и ненулевой.')
                    normals.append(normalize(normal / np.max(np.abs(normal))))
                elif kind == 'f':
                    record = {}
                    for corner in values:
                        fields = (corner.split('/') + ['', ''])[:3]
                        point = obj_index(fields[0], vertex_count)
                        uv = obj_index(fields[1], len(texcoords)) if fields[1] else None
                        normal = obj_index(fields[2], len(normals)) if fields[2] else None
                        record[point] = (uv, normal)
                    face_records.append((line_number, record))
            except ValueError as error:
                raise ValueError(f'Строка {line_number}: {error}') from error

    corners = []
    for line_number, record in face_records:
        try:
            corners.append({
                point: (texcoords[uv] if uv is not None else None,
                        normals[normal] if normal is not None else None)
                for point, (uv, normal) in record.items()
            })
        except IndexError as error:
            raise ValueError(f'Строка {line_number}: отсутствует указанная vt или vn.') from error
    return Surface.from_mesh(mesh, corners)


@dataclass
class Texture:
    pixels: np.ndarray

    @classmethod
    def checker(cls):
        y, x = np.indices((192, 192))
        colors = np.array([[32, 102, 152], [23, 133, 115], [190, 112, 37], [121, 73, 155]])
        pixels = colors[(x >= 96).astype(int) + 2 * (y >= 96)]
        pixels[(x // 24 + y // 24) % 2 == 0] = [238, 236, 218]
        pixels[(x == 95) | (y == 95)] = [46, 52, 60]
        return cls(pixels.astype(np.uint8))

    @classmethod
    def from_file(cls, filename):
        with Image.open(filename) as image:
            image.thumbnail((2048, 2048))
            return cls(np.array(image.convert('RGB')))

    def sample(self, uv):
        """Билинейная фильтрация четырёх текселей. V в OBJ растёт снизу вверх."""
        height, width = self.pixels.shape[:2]
        u, v = np.clip(uv, 0, 1).T
        x, y = u * (width - 1), (1 - v) * (height - 1)
        left, top = x.astype(int), y.astype(int)
        right, bottom = np.minimum(left + 1, width - 1), np.minimum(top + 1, height - 1)
        dx, dy = (x - left)[:, None], (y - top)[:, None]
        above = self.pixels[top, left] * (1 - dx) + self.pixels[top, right] * dx
        below = self.pixels[bottom, left] * (1 - dx) + self.pixels[bottom, right] * dx
        return above * (1 - dy) + below * dy
