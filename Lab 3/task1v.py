from collections import deque
import numpy as np


# Нумерация направлений со слайда 14: 0 — вправо, 6 — вниз.
DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, -1),
              (-1, 0), (-1, 1), (0, 1), (1, 1)]


def trace_boundary(pixels, x, y, boundary_color=(0, 0, 0), tolerance=80):
    height, width = pixels.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return []
    # Допуск объединяет близкие оттенки сглаженной границы.
    difference = np.abs(pixels.astype(np.int16) - np.asarray(boundary_color, dtype=np.int16))
    boundary = np.max(difference, axis=2) <= tolerance
    if boundary[y, x]:
        raise ValueError("point_on_boundary")
    inside = np.zeros((height, width), dtype=bool)
    inside[y, x] = True
    queue = deque([(x, y)])
    while queue:
        px, py = queue.popleft()
        if px in (0, width - 1) or py in (0, height - 1):
            raise ValueError("open_region")
        for dx, dy in DIRECTIONS[::2]:
            nx, ny = px + dx, py + dy
            if not boundary[ny, nx] and not inside[ny, nx]:
                inside[ny, nx] = True
                queue.append((nx, ny))

    # Из толстой границы нужны только пиксели, соседние с внутренностью.
    adjacent = np.zeros_like(inside)
    adjacent[1:] |= inside[:-1]
    adjacent[:-1] |= inside[1:]
    adjacent[:, 1:] |= inside[:, :-1]
    adjacent[:, :-1] |= inside[:, 1:]
    edge = boundary & adjacent

    # Начинаем справа от последнего внутреннего пикселя строки.
    start_x = int(np.flatnonzero(inside[y])[-1]) + 1
    start = (start_x, y)
    current = start
    search_direction = 6
    first_next = None
    contour = []
    states = set()
    while True:
        state = (current, search_direction)
        following = None
        for step in range(8):
            direction = (search_direction + step) % 8
            dx, dy = DIRECTIONS[direction]
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < width and 0 <= ny < height and edge[ny, nx]:
                following = (nx, ny)
                break
        if following is None:
            raise ValueError("disconnected_boundary")
        if current == start and following == first_next:
            # На экране положительная площадь означает обход по часовой.
            area = sum(p[0] * q[1] - q[0] * p[1]
                       for p, q in zip(contour, contour[1:] + contour[:1]))
            if area < 0:
                contour = contour[:1] + contour[:0:-1]
            return contour
        if state in states:
            raise ValueError("boundary_cycle")
        states.add(state)
        contour.append(current)
        if first_next is None:
            first_next = following
        current = following
        # Сначала поворот на 90° по часовой, затем поиск против часовой.
        search_direction = (direction - 2) % 8
