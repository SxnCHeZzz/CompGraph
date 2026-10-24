from math import isfinite


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def quickhull(points):
    points = sorted(set(tuple(point) for point in points))
    if any(len(point) != 2 or not all(isfinite(value) for value in point) for point in points):
        raise ValueError('Точки должны иметь две конечные координаты.')
    if len(points) <= 2:
        return points
    left, right = points[0], points[-1]

    def build(a, b, candidates):
        if not candidates:
            return []
        # Для одной прямой площадь пропорциональна расстоянию до неё.
        farthest = max(candidates, key=lambda p: cross(a, b, p))
        first = [p for p in candidates if cross(a, farthest, p) > 0]
        second = [p for p in candidates if cross(farthest, b, p) > 0]
        # Точки внутри треугольника больше не рассматриваем.
        return build(a, farthest, first) + [farthest] + build(farthest, b, second)

    above = [p for p in points if cross(left, right, p) > 0]
    below = [p for p in points if cross(right, left, p) > 0]
    return [left] + build(left, right, above) + [right] + build(right, left, below)
