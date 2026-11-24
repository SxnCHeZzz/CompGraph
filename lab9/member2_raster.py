"""Участник 2. Преобразования, отсечение, растеризация и проверка глубины."""

import math

import numpy as np

from member1_lighting import lighting_inputs, transform_normals
from member3_texture import Surface  # Загружает общие модули ЛР6–8.

from lab6_base import matrices
from member2_zbuffer import BACKGROUND, ZBuffer
from member3_projection import SceneView, camera_points, project_camera


def model_matrix(offset, angles, scale, center):
    rotation = matrices.rotation('X', angles[0]) @ matrices.rotation('Y', angles[1])
    rotation = rotation @ matrices.rotation('Z', angles[2])
    local = matrices.scaling(*scale) @ rotation
    return matrices.around(local, center) @ matrices.translation(*offset)


def clip_face(vertices, near, far):
    """Первые три столбца — координаты камеры. Остальные интерполируются вместе с ними."""
    if np.all((near <= vertices[:, 2]) & (vertices[:, 2] <= far)):
        return vertices
    for plane, sign in ((near, 1), (far, -1)):
        if len(vertices) == 0:
            break
        result = []
        previous = vertices[-1]
        previous_inside = sign * (previous[2] - plane) >= 0
        for current in vertices:
            inside = sign * (current[2] - plane) >= 0
            if inside != previous_inside:
                fraction = (plane - previous[2]) / (current[2] - previous[2])
                intersection = previous + fraction * (current - previous)
                intersection[2] = plane
                result.append(intersection)
            if inside:
                result.append(current)
            previous, previous_inside = current, inside
        vertices = np.asarray(result).reshape(-1, vertices.shape[1])
    return vertices


def rasterize(vertices, buffer, shade):
    """Линейная интерполяция вдоль рёбер и затем между пересечениями строки."""
    start_row = max(0, math.ceil(vertices[:, 1].min() - 0.5))
    end_row = min(buffer.height, math.ceil(vertices[:, 1].max() - 0.5))
    start_col = max(0, math.ceil(vertices[:, 0].min() - 0.5))
    end_col = min(buffer.width, math.ceil(vertices[:, 0].max() - 0.5))
    if start_row >= end_row or start_col >= end_col:
        return

    rows = np.arange(start_row, end_row)
    columns = np.arange(start_col, end_col)
    y = rows + 0.5
    crossings = []
    for start, end in zip(vertices, np.roll(vertices, -1, axis=0)):
        if start[1] == end[1]:
            continue
        fraction = (y - start[1]) / (end[1] - start[1])
        on_edge = (min(start[1], end[1]) <= y) & (y < max(start[1], end[1]))
        edge = start + fraction[:, None] * (end - start)
        edge[~on_edge, 0] = np.inf
        crossings.append(edge)

    if len(crossings) < 2:
        return
    edges = np.stack(crossings, axis=1)
    sorted_edges = np.argsort(edges[:, :, 0], axis=1)
    edges = edges[np.arange(len(rows))[:, None], sorted_edges]
    x = columns + 0.5
    # Правило чётности: вогнутая грань может иметь несколько интервалов в одной строке.
    for left, right in zip(edges[:, ::2].swapaxes(0, 1), edges[:, 1::2].swapaxes(0, 1)):
        valid = np.isfinite(right[:, 0])
        row_indices, col_indices = np.nonzero(
            valid[:, None] & (left[:, 0, None] <= x) & (x < right[:, 0, None])
        )
        left_values, right_values = left[row_indices], right[row_indices]
        fraction = (x[col_indices] - left_values[:, 0]) / (right_values[:, 0] - left_values[:, 0])
        values = left_values + fraction[:, None] * (right_values - left_values)
        py, px = rows[row_indices], columns[col_indices]
        closer = values[:, 2] < buffer.depth[py, px]
        if not closer.any():
            continue
        py, px, values = py[closer], px[closer], values[closer]
        # Перспектива: интерполируем A/w и 1/w, затем восстанавливаем A.
        colors = shade(values[:, 4:] / values[:, 3:4])
        buffer.rgb[py, px] = np.clip(np.rint(colors), 0, 255).astype(np.uint8)
        buffer.depth[py, px] = values[:, 2]


def render(surface: Surface, matrix, view, width, height, mode, light, color, texture):
    buffer = ZBuffer(width, height)
    linear = matrix[:3, :3]
    world = surface.points @ linear + matrix[3, :3]
    camera = camera_points(world, view)
    perspective = view.kind == 'perspective'
    face_normals = transform_normals(surface.face_normals, linear) @ view.view_matrix()[:3, :3]

    for i, face in enumerate(surface.mesh.faces):
        indices = list(face.indices)
        points = camera[indices]
        normal = face_normals[i]
        facing = np.dot(normal, -points[0]) if perspective else -normal[2]
        if facing <= 0:
            continue

        if mode == 'texture':
            attributes, shade = surface.uv[i], texture.sample
        else:
            normals = transform_normals(surface.normals[i], linear)
            attributes, shade = lighting_inputs(mode, world[indices], normals, light, color)

        clipped = clip_face(np.column_stack((points, attributes)), view.near, view.far)
        if len(clipped) >= 3:
            screen = project_camera(clipped[:, :3], view, width, height)
            reciprocal = 1 / clipped[:, 2] if perspective else np.ones(len(clipped))
            values = np.column_stack((screen, reciprocal, clipped[:, 3:] * reciprocal[:, None]))
            rasterize(values, buffer, shade)

    return buffer
