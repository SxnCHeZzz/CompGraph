

def tangent(points, index):
    if len(points) < 2:
        return 0.0, 0.0
    if index == 0:
        a, b, divisor = points[0], points[1], 1
    elif index == len(points) - 1:
        a, b, divisor = points[-2], points[-1], 1
    else:
        a, b, divisor = points[index - 1], points[index + 1], 2
    return (b[0] - a[0]) / divisor, (b[1] - a[1]) / divisor


def control_points(points, index):
    a, b = points[index], points[index + 1]
    ta, tb = tangent(points, index), tangent(points, index + 1)
    return (a, (a[0] + ta[0] / 3, a[1] + ta[1] / 3),
            (b[0] - tb[0] / 3, b[1] - tb[1] / 3), b)


def bezier_point(a, b, c, d, t):
    mt = 1 - t
    weights = (mt ** 3, 3 * mt ** 2 * t, 3 * mt * t ** 2, t ** 3)
    return tuple(sum(w * p[axis] for w, p in zip(weights, (a, b, c, d))) for axis in (0, 1))


def sample_spline(points, samples=60):
    if samples < 1:
        raise ValueError('samples')
    segments = []
    for index in range(len(points) - 1):
        controls = control_points(points, index)
        segments.append([bezier_point(*controls, k / samples) for k in range(samples + 1)])
    return segments


def nearest_point(points, x, y, radius=10):
    if not points:
        return None
    index = min(range(len(points)), key=lambda i: (points[i][0] - x) ** 2 + (points[i][1] - y) ** 2)
    return index if (points[index][0] - x) ** 2 + (points[index][1] - y) ** 2 <= radius ** 2 else None
