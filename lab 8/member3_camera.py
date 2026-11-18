"""Участник 3. Позиция, направление и матрица перспективной камеры."""

from dataclasses import dataclass
import math

from member3_projection import SceneView


@dataclass
class OrbitCamera(SceneView):
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
