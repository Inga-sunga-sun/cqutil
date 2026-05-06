from cqutil.models import Vec3


def project(
    points: list[Vec3], axes: str = "xy",
) -> list[tuple[float, float]]:
    a, b = axes
    return [(getattr(p, a), getattr(p, b)) for p in points]
