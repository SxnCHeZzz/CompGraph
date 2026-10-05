import math


def bresenham(x0, y0, x1, y1):
    points = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    # Слайд 31: целочисленная ошибка для всех направлений.
    error = dx + dy
    while True:
        points.append((x0, y0, 1.0))
        if x0 == x1 and y0 == y1:
            return points
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def wu(x0, y0, x1, y1):
    if x0 == x1 and y0 == y1:
        return [(x0, y0, 1.0)]
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0, x1, y1 = y0, x0, y1, x1
    if x0 > x1:
        x0, x1, y0, y1 = x1, x0, y1, y0
    gradient = (y1 - y0) / (x1 - x0)
    points = []

    def plot(x, y, intensity):
        if intensity > 0:
            points.append((y, x, intensity) if steep else (x, y, intensity))

    # Слайд 34: концы целиком, внутри — два пикселя с весами 1-f и f.
    plot(x0, y0, 1.0)
    y = float(y0)
    for x in range(x0 + 1, x1):
        y += gradient
        lower = math.floor(y)
        fraction = y - lower
        plot(x, lower, 1 - fraction)
        plot(x, lower + 1, fraction)
    plot(x1, y1, 1.0)
    return points
