from cqutil.models import Vec3


def project(points, axes: str = "xy") -> list[tuple[float, float]]:
    a, b = axes
    result: list[tuple[float, float]] = []
    for p in points:
        v = p if isinstance(p, Vec3) else p.center
        result.append((getattr(v, a), getattr(v, b)))
    return result
