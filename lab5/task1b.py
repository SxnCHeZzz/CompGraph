from task1a import generate, calculate_segments


def branch_styles(segments, base_width=12, thinning=0.72):
    if base_width <= 0 or not 0 < thinning < 1:
        raise ValueError('tree_parameters')
    max_depth = max((s[2] for s in segments), default=1)
    max_distance = max((s[3] for s in segments), default=1)
    brown, green = (110, 65, 30), (40, 155, 55)
    styles = []
    for _, _, depth, distance in segments:
        progress = max(depth / max(1, max_depth), distance / max(1, max_distance))
        # К вершинам ветки становятся тоньше и зеленее.
        width = max(0.6, base_width * thinning ** depth * (1 - 0.7 * progress))
        color = tuple(round(a + (b - a) * progress) for a, b in zip(brown, green))
        styles.append((width, color))
    return styles


def build_tree(axiom, rules, iterations, angle, direction=90, randomness=8,
               seed=0, base_width=12, thinning=0.72):
    commands = generate(axiom, rules, iterations, seed)
    segments = calculate_segments(commands, angle, direction, randomness, seed)
    return segments, branch_styles(segments, base_width, thinning)
