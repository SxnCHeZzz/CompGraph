# Участник 3: обзор, две проекции и переход к экранным координатам.
from dataclasses import dataclass
import math
import numpy as np
from member2_transforms import translation, rotation


@dataclass
class SceneView:
    kind: str = 'axonometric'
    yaw: float = -45
    pitch: float = 35.26438968
    distance: float = 500
    zoom: float = 1
    half_height: float = 180
    near: float = 1
    far: float = 1000000
    target: tuple = (0, 0, 0)

    def view_matrix(self):
        return (translation(*(-np.asarray(self.target))) @ rotation('Y', self.yaw)
                @ rotation('X', self.pitch) @ translation(0, 0, self.distance))

    def projection_matrix(self, width, height):
        aspect = max(width, 1) / max(height, 1)
        if self.kind == 'perspective':
            focal = self.zoom / math.tan(math.radians(45) / 2)
            # w становится равным z, после умножения выполняется деление.
            return np.array([[focal/aspect, 0, 0, 0], [0, focal, 0, 0],
                             [0, 0, self.far/(self.far-self.near), 1],
                             [0, 0, -self.near*self.far/(self.far-self.near), 0]])
        if self.kind != 'axonometric':
            raise ValueError('bad_projection')
        half = self.half_height / self.zoom
        matrix = np.diag([1/(half*aspect), 1/half, 1/(self.far-self.near), 1.])
        matrix[3, 2] = -self.near/(self.far-self.near)
        return matrix

    def fit(self, mesh, width, height):
        center = mesh.center.as_array()
        radius = max(np.linalg.norm(mesh.coordinates()-center, axis=1))
        aspect = max(width, 1)/max(height, 1)
        self.target = tuple(center)
        self.zoom = 1
        self.half_height = max(radius*1.3 / min(1, aspect), 1)
        self.distance = max(radius*(1+1.3/(math.tan(math.radians(45)/2)*min(1, aspect))), 10)
        self.far = max(1000000, self.distance+radius*2)


def viewport_matrix(width, height):
    return np.array([[width/2, 0, 0, 0], [0, -height/2, 0, 0],
                     [0, 0, 1, 0], [width/2, height/2, 0, 1]], dtype=float)


def camera_points(points, view):
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    return (np.column_stack((points, np.ones(len(points)))) @ view.view_matrix())[:, :3]


def project_camera(points, view, width, height):
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    homogeneous = np.column_stack((points, np.ones(len(points))))
    clip = homogeneous @ view.projection_matrix(width, height)
    ndc = clip / clip[:, 3:4]
    return (ndc @ viewport_matrix(width, height))[:, :3]


def clip_depth(a, b, near, far):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    t0, t1 = 0., 1.
    dz = b[2]-a[2]
    if abs(dz) < 1e-12:
        return (a, b) if near <= a[2] <= far else None
    first, second = sorted(((near-a[2])/dz, (far-a[2])/dz))
    t0, t1 = max(t0, first), min(t1, second)
    if t0 > t1:
        return None
    return a+t0*(b-a), a+t1*(b-a)


def projected_segments(vertices, pairs, view, width, height):
    camera = camera_points(vertices, view)
    result = []
    for a, b in pairs:
        segment = clip_depth(camera[a], camera[b], view.near, view.far)
        if segment is not None:
            screen = project_camera(segment, view, width, height)
            result.append((a, b, screen))
    return result
