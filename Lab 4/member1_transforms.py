# Участник 1: матрицы преобразований и центр фигуры.
import math
import numpy as np


def translation(dx, dy):
    return np.array([[1, 0, 0], [0, 1, 0], [dx, dy, 1]], dtype=float)


def rotation(angle):
    angle = math.radians(angle)
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


def scaling(kx, ky):
    if kx == 0 or ky == 0:
        raise ValueError("zero_scale")
    return np.array([[kx, 0, 0], [0, ky, 0], [0, 0, 1]], dtype=float)


def around(matrix, point):
    x, y = point
    # Как в лекции: точки — строки, сначала перенос в начало, затем обратно.
    return translation(-x, -y) @ matrix @ translation(x, y)


def apply(vertices, matrix):
    if not vertices:
        return []
    points = np.column_stack((np.asarray(vertices, dtype=float), np.ones(len(vertices))))
    with np.errstate(over="ignore", invalid="ignore"):
        result = points @ matrix
    if not np.isfinite(result).all():
        raise ValueError("nonfinite")
    return [tuple(point) for point in result[:, :2]]


def center(vertices):
    if not vertices:
        raise ValueError("empty")
    if len(vertices) < 3:
        return tuple(np.mean(vertices, axis=0))
    # Центр площади; для вырожденной фигуры — среднее вершин.
    twice_area = sx = sy = 0.0
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        cross = a[0] * b[1] - b[0] * a[1]
        twice_area += cross
        sx += (a[0] + b[0]) * cross
        sy += (a[1] + b[1]) * cross
    if abs(twice_area) < 1e-9:
        return tuple(np.mean(vertices, axis=0))
    return sx / (3 * twice_area), sy / (3 * twice_area)


def move(vertices, dx, dy):
    return apply(vertices, translation(dx, dy))


def rotate(vertices, angle, pivot=None):
    if pivot is None:
        pivot = center(vertices)
    return apply(vertices, around(rotation(angle), pivot))


def scale(vertices, kx, ky, pivot=None):
    if pivot is None:
        pivot = center(vertices)
    return apply(vertices, around(scaling(kx, ky), pivot))
