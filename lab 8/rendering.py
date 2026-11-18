"""Участник 1. Ориентация нормалей и отсечение нелицевых граней."""

from collections import defaultdict

import numpy as np

from lab6_base import Polyhedron

# Интерфейс по-прежнему получает алгоритмы всех трёх пунктов через этот модуль.
from member2_zbuffer import BACKGROUND, COLORS, ZBuffer, clip_polygon, render_scene
from member3_camera import OrbitCamera


__all__ = [
    'BACKGROUND', 'COLORS', 'OrbitCamera', 'ZBuffer', 'clip_polygon',
    'face_visibility', 'orient_closed_mesh', 'render_scene',
]


def orient_closed_mesh(mesh):
    """Ориентирует замкнутые компоненты по знаку их объёма."""
    faces = [face.indices for face in mesh.faces]
    uses = defaultdict(list)
    for index, face in enumerate(faces):
        for a, b in zip(face, face[1:] + face[:1]):
            edge = min(a, b), max(a, b)
            uses[edge].append((index, 1 if a < b else -1))

    neighbours = [[] for _ in faces]
    unsealed = set()
    for edge_uses in uses.values():
        if len(edge_uses) != 2:
            unsealed.update(index for index, _ in edge_uses)
            continue
        (first, sign1), (second, sign2) = edge_uses
        relative = -sign1 * sign2
        neighbours[first].append((second, relative))
        neighbours[second].append((first, relative))

    vertices = mesh.coordinates()
    signs = {}
    for first in range(len(faces)):
        if first in signs:
            continue
        signs[first] = 1
        pending = [first]
        component = []
        closed = True
        while pending:
            index = pending.pop()
            component.append(index)
            closed &= index not in unsealed
            for neighbour, relative in neighbours[index]:
                expected = signs[index] * relative
                if neighbour in signs:
                    closed &= signs[neighbour] == expected
                else:
                    signs[neighbour] = expected
                    pending.append(neighbour)
        if not closed:
            continue

        origin = vertices[faces[first][0]]
        volume = 0.0
        for index in component:
            polygon = vertices[list(faces[index])] - origin
            cross = np.cross(polygon[1:-1], polygon[2:])
            volume += signs[index] * np.sum(cross @ polygon[0])
        if volume != 0:
            direction = 1 if volume > 0 else -1
            for index in component:
                if signs[index] != direction:
                    faces[index] = faces[index][::-1]
    return Polyhedron(mesh.vertices, faces, mesh.name)


def face_visibility(mesh, points, view):
    normals = mesh.face_normals() @ view.view_matrix()[:3, :3]
    centers = np.array([points[list(face.indices)].mean(axis=0) for face in mesh.faces])
    if view.kind == 'perspective':
        facing = np.einsum('ij,ij->i', normals, -centers)
    else:
        facing = -normals[:, 2]
    return centers, normals, facing > 0
