# Участник 3: создание полигонов и принадлежность точки.
from member2_edges import EPS, edges, intersection, on_segment, orientation


def is_simple(vertices):
    if len(vertices) < 3:
        return True
    sides = edges(vertices)
    for i, (a, b) in enumerate(sides):
        for j in range(i + 1, len(sides)):
            kind, points = intersection(a, b, *sides[j])
            adjacent = j == i + 1 or (i == 0 and j == len(sides) - 1)
            if (adjacent and kind == "overlap") or (not adjacent and kind != "none"):
                return False
    return True


def make_polygon(points):
    vertices = []
    for point in points:
        if not vertices or point != vertices[-1]:
            vertices.append(tuple(point))
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices.pop()
    if not vertices:
        raise ValueError("empty")
    if len(vertices) >= 3:
        if not is_simple(vertices):
            raise ValueError("self_intersection")
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in edges(vertices))
        if abs(area) <= EPS:
            raise ValueError("zero_area")
    return vertices


def is_convex(vertices):
    if len(vertices) < 3:
        return False
    turns = [orientation(vertices[i - 1], vertices[i], vertices[(i + 1) % len(vertices)])
             for i in range(len(vertices))]
    return (any(abs(value) > EPS for value in turns)
            and (all(value >= -EPS for value in turns) or all(value <= EPS for value in turns)))


def contains_point(vertices, point):
    if not vertices:
        return "outside"
    if len(vertices) == 1:
        return "boundary" if on_segment(vertices[0], vertices[0], point) else "outside"
    sides = edges(vertices)
    if any(on_segment(a, b, point) for a, b in sides):
        return "boundary"
    if len(vertices) == 2:
        return "outside"
    if is_convex(vertices):
        # Для выпуклого полигона точка с одной стороны всех рёбер.
        values = [orientation(a, b, point) for a, b in sides]
        return "inside" if all(v >= -EPS for v in values) or all(v <= EPS for v in values) else "outside"

    # Для невыпуклого — луч вправо. Вершину учитываем только один раз.
    inside = False
    x, y = point
    for a, b in sides:
        if (a[1] > y) != (b[1] > y):
            crossing = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if crossing > x:
                inside = not inside
    return "inside" if inside else "outside"
