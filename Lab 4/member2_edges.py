# Участник 2: положение точки и пересечение отрезков.
EPS = 1e-9


def subtract(a, b):
    return a[0] - b[0], a[1] - b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def orientation(a, b, p):
    return cross(subtract(b, a), subtract(p, a))


def on_segment(a, b, p):
    return (abs(orientation(a, b, p)) <= EPS
            and min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS
            and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def point_side(a, b, p):
    if abs(a[0] - b[0]) <= EPS and abs(a[1] - b[1]) <= EPS:
        return "degenerate"
    value = orientation(a, b, p)
    if value > EPS:
        return "left"
    if value < -EPS:
        return "right"
    return "on_segment" if on_segment(a, b, p) else "on_line"


def intersection(a, b, c, d):
    r, s = subtract(b, a), subtract(d, c)
    denominator = cross(r, s)
    delta = subtract(c, a)
    if abs(denominator) > EPS:
        # P(t) = A + t(B-A); оба параметра должны лежать на отрезках.
        t = cross(delta, s) / denominator
        u = cross(delta, r) / denominator
        if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
            return "point", [(a[0] + t * r[0], a[1] + t * r[1])]
        return "none", []

    # Параллельные, совпадающие отрезки и отрезки-точки.
    common = []
    for point in (a, b, c, d):
        if on_segment(a, b, point) and on_segment(c, d, point):
            if not any(abs(point[0] - q[0]) <= EPS and abs(point[1] - q[1]) <= EPS for q in common):
                common.append(point)
    if not common:
        return "none", []
    if len(common) == 1:
        return "point", common
    common.sort()
    return "overlap", [common[0], common[-1]]


def edges(vertices):
    if len(vertices) == 2:
        return [(vertices[0], vertices[1])]
    if len(vertices) >= 3:
        return list(zip(vertices, vertices[1:] + vertices[:1]))
    return []
