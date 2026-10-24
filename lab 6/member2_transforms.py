# Участник 2: класс многогранника и все аффинные преобразования.
import math
import numpy as np
from member1_models import Point, Face, solid_data


class Polyhedron:
    def __init__(self, vertices, faces, name=''):
        self.vertices = [p if isinstance(p, Point) else Point(*p) for p in vertices]
        self.faces = [face if isinstance(face, Face) else Face(face) for face in faces]
        self.name = name
        if any(i >= len(self.vertices) for face in self.faces for i in face.indices):
            raise ValueError('bad_face')

    def coordinates(self):
        return np.array([p.as_array() for p in self.vertices], dtype=float).reshape(-1, 3)

    @property
    def center(self):
        if not self.vertices:
            raise ValueError('empty_model')
        return Point(*np.mean(self.coordinates(), axis=0))

    def edges(self):
        result = set()
        for face in self.faces:
            indices = face.indices
            for a, b in zip(indices, indices[1:]+indices[:1]):
                result.add(tuple(sorted((a, b))))
        return sorted(result)

    def transformed(self, matrix):
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
            raise ValueError('bad_matrix')
        if not np.allclose(matrix[:, 3], [0, 0, 0, 1]):
            raise ValueError('not_affine')
        points = np.column_stack((self.coordinates(), np.ones(len(self.vertices))))
        with np.errstate(over='ignore', invalid='ignore'):
            result = points @ matrix
        if not np.isfinite(result).all():
            raise ValueError('nonfinite')
        faces = self.faces
        # Отражение меняет ориентацию обхода, сохраняем нормали наружу.
        if np.linalg.det(matrix[:3, :3]) < 0:
            faces = [Face(face.indices[::-1]) for face in faces]
        return Polyhedron(result[:, :3], faces, self.name)

    def face_normals(self):
        vertices = self.coordinates()
        return np.array([face.normal(vertices) for face in self.faces]).reshape(-1, 3)

    def vertex_normals(self):
        normals = np.zeros((len(self.vertices), 3))
        for face, normal in zip(self.faces, self.face_normals()):
            for index in face.indices:
                normals[index] += normal
        lengths = np.linalg.norm(normals, axis=1)
        return np.divide(normals, lengths[:, None], out=np.zeros_like(normals), where=lengths[:, None] > 1e-12)


# Как в лекции: [x y z 1] умножается на матрицы слева направо.
def translation(dx, dy, dz):
    matrix = np.eye(4)
    matrix[3, :3] = [dx, dy, dz]
    return matrix


def scaling(kx, ky, kz):
    if min(abs(kx), abs(ky), abs(kz)) < 1e-8:
        raise ValueError('zero_scale')
    return np.diag([kx, ky, kz, 1.0])


def rotation(axis, angle):
    angle = math.radians(angle)
    c, s = math.cos(angle), math.sin(angle)
    matrix = np.eye(4)
    if axis == 'X':
        matrix[:3, :3] = [[1, 0, 0], [0, c, s], [0, -s, c]]
    elif axis == 'Y':
        matrix[:3, :3] = [[c, 0, -s], [0, 1, 0], [s, 0, c]]
    elif axis == 'Z':
        matrix[:3, :3] = [[c, s, 0], [-s, c, 0], [0, 0, 1]]
    else:
        raise ValueError('bad_axis')
    return matrix


def reflection(plane):
    factors = {'XY': (1, 1, -1), 'XZ': (1, -1, 1), 'YZ': (-1, 1, 1)}
    if plane not in factors:
        raise ValueError('bad_plane')
    return scaling(*factors[plane])


def around(matrix, point):
    x, y, z = point
    return translation(-x, -y, -z) @ matrix @ translation(x, y, z)


def rotation_line(a, b, angle):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    direction = b - a
    length = np.linalg.norm(direction)
    if length < 1e-10:
        raise ValueError('same_axis_points')
    l, m, n = direction / length
    psi = math.degrees(math.atan2(m, n))
    theta = math.degrees(math.atan2(-l, math.hypot(m, n)))
    # Слайды 20–28: совмещаем прямую с Z, поворачиваем и возвращаем.
    align = rotation('X', psi) @ rotation('Y', theta)
    undo = rotation('Y', -theta) @ rotation('X', -psi)
    return around(align @ rotation('Z', angle) @ undo, a)


def make_solid(kind, radius=100):
    vertices, faces = solid_data(kind, radius)
    return Polyhedron(vertices, faces, kind)
