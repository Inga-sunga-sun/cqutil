import cadquery as cq

from cqutil.models import Vec3


def align(
    part: cq.Workplane,
    source: Vec3,
    target: Vec3,
) -> cq.Workplane:
    delta = target - source
    return part.translate((delta.x, delta.y, delta.z))
