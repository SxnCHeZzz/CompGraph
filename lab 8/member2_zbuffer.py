"""Участник 2. Растеризация граней, проверка глубины и карта Z-буфера."""

import math

import numpy as np

from member3_projection import camera_points, project_camera


BACKGROUND = (247, 249, 252)
COLORS = ((61, 125, 200), (219, 126, 61), (59, 155, 125), (144, 104, 190))


def clip_polygon(points, near, far):
    """Отсекает многоугольник между ближней и дальней плоскостями камеры."""
    if np.all((near <= points[:, 2]) & (points[:, 2] <= far)):
        return points
    for boundary, direction in ((near, 1), (far, -1)):
        if len(points) == 0:
            break
        result = []
        previous = points[-1]
        previous_inside = direction * (previous[2] - boundary) >= 0
        for point in points:
            inside = direction * (point[2] - boundary) >= 0
            if previous_inside != inside:
                weight = (boundary - previous[2]) / (point[2] - previous[2])
                result.append(previous + weight * (point - previous))
            if inside:
                result.append(point)
            previous, previous_inside = point, inside
        points = np.asarray(result).reshape(-1, 3)
    return points


class ZBuffer:
    def __init__(self, width, height, depth_test=True):
        self.width = width
        self.height = height
        self.depth_test = depth_test
        self.depth = np.full((height, width), np.inf)
        self.rgb = np.empty((height, width, 3), dtype=np.uint8)
        self.rgb[:] = BACKGROUND

    def polygon(self, polygon, color):
        if len(polygon) < 3:
            return
        # Берём тройку с наибольшей экранной площадью, чтобы устойчиво найти плоскость.
        anchor = polygon[0]
        normals = np.cross(polygon[1:-1] - anchor, polygon[2:] - anchor)
        normal = normals[np.argmax(np.abs(normals[:, 2]))]
        if abs(normal[2]) < 1e-12:
            return
        slope = -normal[:2] / normal[2]
        model_depth = anchor[2] + (polygon[:, :2] - anchor[:2]) @ slope
        if len(polygon) > 3 and not np.allclose(model_depth, polygon[:, 2], rtol=0, atol=1e-10):
            # Четырёхугольники поверхности Lab 7 могут быть неплоскими.
            for index in range(1, len(polygon) - 1):
                self.polygon(polygon[[0, index, index + 1]], color)
            return

        low = polygon[:, :2].min(axis=0) - 0.5
        high = polygon[:, :2].max(axis=0) - 0.5
        left, top = max(0, math.ceil(low[0])), max(0, math.ceil(low[1]))
        right, bottom = min(self.width, math.ceil(high[0])), min(self.height, math.ceil(high[1]))
        if left >= right or top >= bottom:
            return

        # Правило чётности для центров пикселей работает и для вогнутых граней.
        xs = np.arange(left, right)[None, :] + 0.5
        ys = np.arange(top, bottom)[:, None] + 0.5
        covered = np.zeros((bottom - top, right - left), dtype=bool)
        for start, end in zip(polygon, np.roll(polygon, -1, axis=0)):
            dx, dy = end[:2] - start[:2]
            if dy != 0:
                crosses = (start[1] > ys) != (end[1] > ys)
                covered ^= crosses & (xs < start[0] + (ys - start[1]) * dx / dy)

        depth = anchor[2] + (xs - anchor[0]) * slope[0] + (ys - anchor[1]) * slope[1]
        depth_region = self.depth[top:bottom, left:right]
        if self.depth_test:
            covered &= depth < depth_region
        depth_region[covered] = depth[covered]
        self.rgb[top:bottom, left:right][covered] = color

    def ppm(self, show_depth=False):
        pixels = self.rgb
        if show_depth:
            visible = np.isfinite(self.depth)
            pixels = np.empty_like(self.rgb)
            pixels[:] = BACKGROUND
            if visible.any():
                depths = self.depth[visible]
                spread = np.ptp(depths)
                grey = 225 - 185 * (depths - depths.min()) / (spread or 1)
                pixels[visible] = grey[:, None]
        header = f'P6\n{self.width} {self.height}\n255\n'.encode('ascii')
        return header + pixels.tobytes()


def render_scene(models, view, width, height, *, depth_test=True, reverse=False):
    buffer = ZBuffer(width, height, depth_test)
    order = range(len(models) - 1, -1, -1) if reverse else range(len(models))
    for model_index in order:
        mesh = models[model_index]
        points = camera_points(mesh.coordinates(), view)
        color = COLORS[model_index % len(COLORS)]
        faces = range(len(mesh.faces) - 1, -1, -1) if reverse else range(len(mesh.faces))
        for face_index in faces:
            points_in_face = points[list(mesh.faces[face_index].indices)]
            clipped = clip_polygon(points_in_face, view.near, view.far)
            if len(clipped) >= 3:
                screen = project_camera(clipped, view, width, height)
                shade = (1.0, 0.83, 0.69)[face_index % 3]
                buffer.polygon(screen, [round(channel * shade) for channel in color])
    return buffer
