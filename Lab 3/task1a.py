import numpy as np


def fill_color(pixels, x, y, color, boundary=None):
    height, width = pixels.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return 0
    if boundary is None:
        boundary = np.all(pixels == (0, 0, 0), axis=2)
    visited = np.zeros((height, width), dtype=bool)
    count = 0

    def suitable(px, py):
        return (0 <= px < width and 0 <= py < height
                and not boundary[py, px] and not visited[py, px])

    def fill(px, py):
        nonlocal count
        if not suitable(px, py):
            return
        left = right = px
        while suitable(left - 1, py):
            left -= 1
        while suitable(right + 1, py):
            right += 1

        # Слайд 12: закрашиваем серию, не затрагивая границу.
        visited[py, left:right + 1] = True
        for column in range(left, right + 1):
            pixels[py, column] = color
        count += right - left + 1
        for column in range(left, right + 1):
            fill(column, py - 1)
        for column in range(left, right + 1):
            fill(column, py + 1)

    fill(x, y)
    return count
