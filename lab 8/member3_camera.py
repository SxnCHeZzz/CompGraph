"""Участник 3. Позиция, направление и матрица перспективной камеры."""

from dataclasses import dataclass
import math

from member2_transforms import rotation, rotation_line
from member3_projection import SceneView


@dataclass
class OrbitView(SceneView):
    roll: float = 0

    def view_matrix(self):
        # Крен меняет экранные оси, сохраняя центр орбиты и дистанцию.
        return super().view_matrix() @ rotation('Z', self.roll)

    def drag(self, dx, dy):
        """Поворачивает обзор по экранным осям, чтобы передняя сторона шла за мышью."""
        length = math.hypot(dx, dy)
        if not length:
            return
        # Ось перпендикулярна движению мыши в плоскости экрана.
        turn = rotation_line((0, 0, 0), (dy, dx, 0), -0.4 * length)
        basis = self.view_matrix()[:3, :3] @ turn[:3, :3]

        # Разложение матрицы поворота Y → X → Z для полей азимута и наклона.
        horizontal = math.hypot(basis[0, 2], basis[2, 2])
        self.pitch = math.degrees(math.atan2(basis[1, 2], horizontal))
        if horizontal > 1e-10:
            self.yaw = math.degrees(math.atan2(-basis[0, 2], basis[2, 2]))
            self.roll = math.degrees(math.atan2(-basis[1, 0], basis[1, 1]))
        else:
            self.yaw = math.copysign(1, self.pitch) * math.degrees(math.atan2(basis[0, 1], basis[0, 0]))
            self.roll = 0


@dataclass
class OrbitCamera(OrbitView):
    kind: str = 'perspective'
    fov: float = 45

    @property
    def position(self):
        matrix = self.view_matrix()
        return -matrix[3, :3] @ matrix[:3, :3].T

    @property
    def direction(self):
        return self.view_matrix()[:3, 2]

    def projection_matrix(self, width, height):
        matrix = super().projection_matrix(width, height)
        fov_scale = math.tan(math.radians(22.5)) / math.tan(math.radians(self.fov / 2))
        matrix[0, 0] *= fov_scale
        matrix[1, 1] *= fov_scale
        return matrix
