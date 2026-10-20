import math
import random


def midpoint_displacement(iterations=8, roughness=0.3, decay=1.0,
                          left_height=0, right_height=0, length=1000, seed=0):
    if not 0 <= iterations <= 14:
        raise ValueError('mountain_iterations')
    if not all(math.isfinite(v) for v in (roughness, decay, left_height, right_height, length)):
        raise ValueError('bad_number')
    if length <= 0 or not 0 <= roughness <= 1 or not 0 < decay <= 1:
        raise ValueError('mountain_parameters')
    points = [(0.0, float(left_height)), (float(length), float(right_height))]
    steps = [points]
    rng = random.Random(seed)
    for level in range(iterations):
        result = []
        for a, b in zip(points, points[1:]):
            # Слайд 59: h = (hL+hR)/2 + random(-R*L, R*L).
            amplitude = roughness * math.hypot(b[0] - a[0], b[1] - a[1]) * decay ** level
            middle = ((a[0] + b[0]) / 2,
                      (a[1] + b[1]) / 2 + rng.uniform(-amplitude, amplitude))
            result.extend([a, middle])
        result.append(points[-1])
        points = result
        steps.append(points)
    return steps
