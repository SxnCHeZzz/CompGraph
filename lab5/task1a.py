import math
import random


MAX_COMMANDS = 250000
MAX_SEGMENTS = 40000


def parse_lsystem(text):
    lines = [line.split('#', 1)[0].strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise ValueError('empty_system')
    header = lines[0].split()
    if len(header) != 3:
        raise ValueError('bad_header')
    axiom, angle, direction = header
    angle, direction = float(angle), float(direction)
    if not math.isfinite(angle) or not math.isfinite(direction):
        raise ValueError('bad_number')
    rules = {}
    for line in lines[1:]:
        line = line.replace('→', '->').replace('−', '-')
        if '->' not in line:
            raise ValueError('bad_rule')
        symbol, replacement = line.split('->', 1)
        symbol = symbol.strip()
        if len(symbol) != 1 or symbol in '+-[]':
            raise ValueError('bad_rule')
        rules.setdefault(symbol, []).append(''.join(replacement.split()))
    return axiom.replace('−', '-'), angle, direction, rules


def generate(axiom, rules, iterations, seed=0):
    if not 0 <= iterations <= 15:
        raise ValueError('iterations_limit')
    rng = random.Random(seed)
    current = axiom
    if len(current) > MAX_COMMANDS:
        raise ValueError('system_limit')
    for _ in range(iterations):
        parts = []
        size = 0
        for symbol in current:
            variants = rules.get(symbol)
            replacement = rng.choice(variants) if variants else symbol
            size += len(replacement)
            if size > MAX_COMMANDS:
                raise ValueError('system_limit')
            parts.append(replacement)
        current = ''.join(parts)
    return current


def calculate_segments(commands, angle, direction, randomness=0, seed=0):
    if randomness < 0 or not all(math.isfinite(v) for v in (angle, direction, randomness)):
        raise ValueError('bad_number')
    x = y = distance = 0.0
    heading = direction
    depth = 0
    stack, segments = [], []
    rng = random.Random(seed)
    for symbol in commands:
        if symbol in 'FGf':
            radians = math.radians(heading)
            nx, ny = x + math.cos(radians), y + math.sin(radians)
            if symbol != 'f':
                if len(segments) >= MAX_SEGMENTS:
                    raise ValueError('segments_limit')
                segments.append(((x, y), (nx, ny), depth, distance))
            x, y = nx, ny
            distance += 1
        elif symbol in '+-':
            turn = angle + rng.uniform(-randomness, randomness)
            heading += turn if symbol == '+' else -turn
        elif symbol == '[':
            # Сохраняем состояние черепашки перед ответвлением.
            stack.append((x, y, heading, depth, distance))
            depth += 1
        elif symbol == ']':
            if not stack:
                raise ValueError('brackets')
            x, y, heading, depth, distance = stack.pop()
    if stack:
        raise ValueError('brackets')
    return segments


def fit_points(points, width, height, padding=30, bounds=None):
    if not points:
        return []
    if bounds is None:
        xs, ys = zip(*points)
        bounds = min(xs), min(ys), max(xs), max(ys)
    x0, y0, x1, y1 = bounds
    scale = min(max(1, width - 2 * padding) / max(x1 - x0, 1e-9),
                max(1, height - 2 * padding) / max(y1 - y0, 1e-9))
    return [(width / 2 + (x - (x0 + x1) / 2) * scale,
             height / 2 - (y - (y0 + y1) / 2) * scale) for x, y in points]
