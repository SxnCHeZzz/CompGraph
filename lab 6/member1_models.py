# Участник 1: точки, грани и построение пяти правильных многогранников.
from dataclasses import dataclass
from itertools import combinations, product
import math
import numpy as np


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float

    def __post_init__(self):
        if not np.isfinite([self.x, self.y, self.z]).all():
            raise ValueError('nonfinite')

    def as_array(self):
        return np.array([self.x, self.y, self.z], dtype=float)


@dataclass(frozen=True)
class Face:
    indices: tuple

    def __post_init__(self):
        object.__setattr__(self, 'indices', tuple(self.indices))
        if len(self.indices) < 3 or len(set(self.indices)) != len(self.indices):
            raise ValueError('bad_face')
        if any(not isinstance(i, (int, np.integer)) or i < 0 for i in self.indices):
            raise ValueError('bad_face')

    def center(self, vertices):
        return np.mean(vertices[list(self.indices)], axis=0)

    def normal(self, vertices):
        points = vertices[list(self.indices)]
        normal = np.zeros(3)
        for i in range(1, len(points)-1):
            normal += np.cross(points[i]-points[0], points[i+1]-points[0])
        length = np.linalg.norm(normal)
        return normal / length if length > 1e-12 else np.zeros(3)


SOLIDS = {'Тетраэдр': 'tetrahedron', 'Гексаэдр (куб)': 'cube', 'Октаэдр': 'octahedron',
          'Икосаэдр ★': 'icosahedron', 'Додекаэдр ★': 'dodecahedron'}


def convex_faces(vertices):
    vertices = np.asarray(vertices, dtype=float)
    groups = set()
    for i, j, k in combinations(range(len(vertices)), 3):
        normal = np.cross(vertices[j]-vertices[i], vertices[k]-vertices[i])
        length = np.linalg.norm(normal)
        if length < 1e-9:
            continue
        distances = (vertices-vertices[i]) @ (normal / length)
        if np.all(distances <= 1e-8) or np.all(distances >= -1e-8):
            groups.add(tuple(np.flatnonzero(np.abs(distances) < 1e-8).tolist()))
    center = np.mean(vertices, axis=0)
    faces = []
    for indices in sorted(groups):
        points = vertices[list(indices)]
        middle = np.mean(points, axis=0)
        normal = middle-center
        normal /= np.linalg.norm(normal)
        u = points[0]-middle
        u /= np.linalg.norm(u)
        v = np.cross(normal, u)
        # Упорядочиваем вершины плоской грани вокруг её центра.
        order = sorted(indices, key=lambda index: math.atan2(np.dot(vertices[index]-middle, v),
                                                            np.dot(vertices[index]-middle, u)))
        faces.append(tuple(order))
    return faces


def solid_data(kind, radius=100):
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError('bad_radius')
    if kind == 'tetrahedron':
        vertices = np.array([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)], dtype=float)
    elif kind == 'cube':
        vertices = np.array(list(product((-1, 1), repeat=3)), dtype=float)
    elif kind == 'octahedron':
        vertices = np.concatenate((np.eye(3), -np.eye(3)))
    elif kind in ('icosahedron', 'dodecahedron'):
        phi = (1+math.sqrt(5))/2
        vertices = np.array([(0, a, b*phi) for a in (-1, 1) for b in (-1, 1)]
                          + [(a, b*phi, 0) for a in (-1, 1) for b in (-1, 1)]
                          + [(b*phi, 0, a) for a in (-1, 1) for b in (-1, 1)], dtype=float)
        if kind == 'dodecahedron':
            # Слайд 18: вершины додекаэдра — центры граней икосаэдра.
            vertices = np.array([np.mean(vertices[list(face)], axis=0) for face in convex_faces(vertices)])
    else:
        raise ValueError('unknown_solid')
    faces = convex_faces(vertices)
    vertices *= radius / np.linalg.norm(vertices[0])
    return vertices, faces
