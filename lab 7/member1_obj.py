from pathlib import Path
import numpy as np
from lab6_base import Polyhedron, Face


def load_obj(filename):
    vertices, faces = [], []
    face_lines = []
    with open(filename, encoding='utf-8-sig') as file:
        for line_number, line in enumerate(file, 1):
            parts = line.split('#', 1)[0].split()
            if not parts:
                continue
            try:
                if parts[0] == 'v':
                    if len(parts) not in (4, 5):
                        raise ValueError('Нужно три координаты вершины и необязательная w.')
                    point = [float(value) for value in parts[1:4]]
                    if len(parts) == 5:
                        w = float(parts[4])
                        if not np.isfinite(w) or w == 0:
                            raise ValueError('Координата w должна быть конечной и ненулевой.')
                        point = [value / w for value in point]
                    if not np.isfinite(point).all() or max(map(abs, point)) > 1e8:
                        raise ValueError('Координаты должны быть конечными, по модулю не больше 1e8.')
                    vertices.append(point)
                elif parts[0] == 'f':
                    if len(parts) < 4:
                        raise ValueError('У грани должно быть хотя бы три вершины.')
                    indices = []
                    for token in parts[1:]:
                        # В v/vt/vn нужны только индексы v. Отрицательные — от конца списка.
                        fields = token.split('/')
                        if len(fields) > 3:
                            raise ValueError('Некорректный формат индекса грани.')
                        index = int(fields[0])
                        if index == 0:
                            raise ValueError('Индексы OBJ начинаются с 1, а не с 0.')
                        index = index - 1 if index > 0 else len(vertices) + index
                        if index < 0:
                            raise ValueError('Индекс вершины выходит за границы списка.')
                        indices.append(index)
                    if len(set(indices)) != len(indices):
                        raise ValueError('В грани повторяется индекс вершины.')
                    faces.append(indices)
                    face_lines.append(line_number)
                # vt, vn, материалы и прочие записи каркасному выводу не нужны.
            except (ValueError, OverflowError) as error:
                raise ValueError(f'Строка {line_number}: некорректные данные OBJ. {error}') from error
    if not vertices or not faces:
        raise ValueError('OBJ должен содержать вершины v и грани f.')
    points = np.asarray(vertices, dtype=float)
    for indices, line_number in zip(faces, face_lines):
        if max(indices) >= len(vertices):
            raise ValueError(f'Строка {line_number}: отсутствует вершина, указанная в грани.')
        local = points[indices] - points[indices[0]]
        scale = np.max(np.abs(local))
        if scale == 0:
            raise ValueError(f'Строка {line_number}: вырожденная грань.')
        local /= scale
        area = sum((np.cross(local[i], local[i+1]) for i in range(1, len(local)-1)), np.zeros(3))
        if np.linalg.norm(area) < 1e-12:
            raise ValueError(f'Строка {line_number}: вырожденная грань.')
    return Polyhedron(vertices, [Face(indices) for indices in faces], Path(filename).stem)


def save_obj(mesh, filename):
    if not mesh.vertices or not mesh.faces:
        raise ValueError('Нельзя сохранить модель без вершин и граней.')
    with open(filename, 'w', encoding='utf-8') as file:
        file.write('# Полигональная модель. Лабораторная работа №7.\n')
        for point in mesh.vertices:
            # Сохраняем текущие мировые координаты, в том числе после преобразований.
            file.write(f'v {point.x:.17g} {point.y:.17g} {point.z:.17g}\n')
        for face in mesh.faces:
            file.write('f ' + ' '.join(str(index + 1) for index in face.indices) + '\n')
