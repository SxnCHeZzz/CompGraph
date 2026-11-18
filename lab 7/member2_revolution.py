# Участник 2: фигура вращения, замыкание колец и точки на оси.
import numpy as np
from lab6_base import Polyhedron, matrices


DEFAULT_PROFILE = [(0, -100, 0), (45, -85, 0), (70, -40, 0),
                   (45, 10, 0), (60, 65, 0), (25, 100, 0)]


def generate_revolution(profile, axis='Y', subdivisions=24):
    points = np.asarray(profile, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2:
        raise ValueError('Образующая должна содержать хотя бы две точки X Y Z.')
    if not np.isfinite(points).all() or np.max(np.abs(points)) > 1e8:
        raise ValueError('Координаты образующей должны быть конечными, по модулю не больше 1e8.')
    if axis not in ('X', 'Y', 'Z'):
        raise ValueError('Выберите ось X, Y или Z.')
    if not isinstance(subdivisions, int) or not 3 <= subdivisions <= 360:
        raise ValueError('Количество угловых разбиений должно быть целым числом от 3 до 360.')
    if len(points) * subdivisions > 50000:
        raise ValueError('Слишком большая модель. Уменьшите количество точек или разбиений.')
    axis_index = 'XYZ'.index(axis)
    vertices, rings = [], []
    rotations = [matrices.rotation(axis, j * 360 / subdivisions) for j in range(subdivisions)]
    for point in points:
        radial = np.delete(point, axis_index)
        if np.linalg.norm(radial) < 1e-10:
            # На оси вместо N совпадающих вершин оставляем одну общую вершину.
            index = len(vertices)
            vertices.append(tuple(point))
            rings.append([index] * subdivisions)
        else:
            ring = []
            for matrix in rotations:
                ring.append(len(vertices))
                vertices.append(tuple((np.append(point, 1) @ matrix)[:3]))
            rings.append(ring)
    coordinates = np.asarray(vertices)
    faces = []
    for first, second in zip(rings, rings[1:]):
        for j in range(subdivisions):
            following = (j + 1) % subdivisions
            candidate = (first[j], first[following], second[following], second[j])
            indices = []
            for index in candidate:
                if not indices or index != indices[-1]:
                    indices.append(index)
            if len(indices) > 1 and indices[-1] == indices[0]:
                indices.pop()
            if len(indices) < 3 or len(set(indices)) != len(indices):
                continue
            local = coordinates[indices] - coordinates[indices[0]]
            scale = np.max(np.abs(local))
            if scale == 0:
                continue
            local /= scale
            area = sum((np.cross(local[k], local[k+1]) for k in range(1, len(local)-1)), np.zeros(3))
            if np.linalg.norm(area) > 1e-12:
                faces.append(tuple(indices))
    if not faces:
        raise ValueError('Образующая не создаёт поверхность: все участки вырождены или лежат на оси.')
    return Polyhedron(vertices, faces, 'Фигура вращения')
