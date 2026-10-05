import numpy as np


def doubled_area(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])


def rasterize_triangle(vertices, colors, width=800, height=550):
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    a, b, c = np.asarray(vertices, dtype=float)
    colors = np.asarray(colors, dtype=float)
    denominator = doubled_area(a, b, c)
    if abs(denominator) < 1e-10:
        raise ValueError("degenerate_triangle")
    left = max(0, int(np.floor(min(a[0], b[0], c[0]))))
    right = min(width - 1, int(np.ceil(max(a[0], b[0], c[0]))))
    top = max(0, int(np.floor(min(a[1], b[1], c[1]))))
    bottom = min(height - 1, int(np.ceil(max(a[1], b[1], c[1]))))
    x = np.arange(left, right + 1)
    # Слайды 42–44: веса через знаковые площади, затем смешивание цветов.
    for y in range(top, bottom + 1):
        first = doubled_area(b, c, (x, y)) / denominator
        second = doubled_area(c, a, (x, y)) / denominator
        third = 1 - first - second
        inside = (first >= -1e-10) & (second >= -1e-10) & (third >= -1e-10)
        weights = np.stack([first[inside], second[inside], third[inside]], axis=-1)
        image[y, x[inside]] = np.floor(np.clip(weights @ colors, 0, 255) + 0.5 + 1e-9).astype(np.uint8)
    return image
