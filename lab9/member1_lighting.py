"""Участник 1. Нормали, диффузное отражение и два способа закраски."""

import numpy as np


def normalize(vectors):
    vectors = np.asarray(vectors, dtype=float)
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return np.divide(vectors, lengths, out=np.zeros_like(vectors), where=lengths > 1e-12)


def vertex_normals(mesh, face_normals):
    """Усредняет единичные нормали граней, смежных с каждой вершиной."""
    normals = np.zeros((len(mesh.vertices), 3))
    for face, normal in zip(mesh.faces, face_normals):
        normals[list(face.indices)] += normal
    return normalize(normals)


def transform_normals(normals, linear):
    """В ЛР6 векторы-строки умножаются на матрицу справа."""
    return normalize(normals @ np.linalg.inv(linear).T)


def diffuse(points, normals, light):
    light_directions = normalize(light - points)
    return np.clip(np.sum(normals * light_directions, axis=-1), 0, 1)


def lambert(points, normals, light, color):
    """Для Гуро вычисляется в вершинах, до растеризации."""
    intensity = diffuse(points, normalize(normals), light)
    return intensity[:, None] * color


def toon(points, normals, light, color):
    """Для Фонга вычисляется на пиксель после интерполяции нормали."""
    intensity = 0.2 + diffuse(points, normalize(normals), light)
    levels = np.select([intensity < 0.4, intensity < 0.7], [0.3, 1.0], default=1.3)
    return levels[:, None] * color


def corner_normals(mesh, face_normals, obj_corners):
    """Сохраняет отдельные нормали OBJ на швах и вычисляет недостающие."""
    smooth = vertex_normals(mesh, face_normals)
    result = []
    for i, (face, face_normal) in enumerate(zip(mesh.faces, face_normals)):
        normals = smooth[list(face.indices)].copy()
        normals[~np.any(normals, axis=1)] = face_normal
        if obj_corners is not None:
            for j, index in enumerate(face.indices):
                _, normal = obj_corners[i][index]
                if normal is not None:
                    normals[j] = normal
        result.append(normals)
    return tuple(result)


def lighting_inputs(mode, positions, normals, light, color):
    """Возвращает атрибуты вершин и функцию определения цвета пикселя."""
    if mode == 'gouraud':
        def shade(attributes):
            return attributes

        return lambert(positions, normals, light, color), shade

    def shade(attributes):
        return toon(attributes[:, :3], attributes[:, 3:], light, color)

    return np.column_stack((positions, normals)), shade
