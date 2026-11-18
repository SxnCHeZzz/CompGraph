
import math
import numpy as np
from lab6_base import Polyhedron


FUNCTIONS = {
    'sin(x) · cos(y)': lambda x, y: math.sin(x) * math.cos(y),
    'x² + y²': lambda x, y: x*x + y*y,
    'x² − y²': lambda x, y: x*x - y*y,
    'sin(√(x² + y²))': lambda x, y: math.sin(math.hypot(x, y)),
    'exp(−(x² + y²))': lambda x, y: math.exp(-(x*x + y*y)),
}


def generate_surface(function, x0=-5, x1=5, y0=-5, y1=5, nx=30, ny=30):
    if function not in FUNCTIONS:
        raise ValueError('Выберите функцию из списка.')
    if not all(math.isfinite(value) for value in (x0, x1, y0, y1)):
        raise ValueError('Границы диапазонов должны быть конечными числами.')
    if not x0 < x1 or not y0 < y1:
        raise ValueError('Минимальная граница должна быть меньше максимальной по обеим осям.')
    if not all(isinstance(n, int) and 1 <= n <= 200 for n in (nx, ny)):
        raise ValueError('Количество разбиений по X и Y: целые числа от 1 до 200.')
    vertices = []
    calculate = FUNCTIONS[function]
    for x in np.linspace(x0, x1, nx + 1):
        for y in np.linspace(y0, y1, ny + 1):
            try:
                z = calculate(float(x), float(y))
            except (ValueError, OverflowError) as error:
                raise ValueError('Функция не определена или переполняется в выбранном диапазоне.') from error
            if not np.isfinite([x, y, z]).all() or max(abs(x), abs(y), abs(z)) > 1e8:
                raise ValueError('Получены недопустимые координаты. Уменьшите диапазон.')
            vertices.append((float(x), float(y), z))
    faces = []
    # Каждая ячейка сетки — грань из четырёх соседних вершин.
    for i in range(nx):
        for j in range(ny):
            a = i * (ny + 1) + j
            b = (i + 1) * (ny + 1) + j
            faces.append((a, b, b + 1, a + 1))
    return Polyhedron(vertices, faces, f'z = {function}')
