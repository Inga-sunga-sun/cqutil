from dataclasses import dataclass, field

from cqutil.models.hole import Hole
from cqutil.models.slot import Slot
from cqutil.models.vec3 import Vec3


@dataclass
class Face:
    direction: Vec3
    center: Vec3
    size: Vec3
    corners: list[Vec3] = field(default_factory=list)
    holes: list[Hole] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)

    def corner_at(self, x: str, y: str, z: str) -> Vec3:
        funcs = {"+": max, "-": min}
        return Vec3(
            funcs[x](c.x for c in self.corners),
            funcs[y](c.y for c in self.corners),
            funcs[z](c.z for c in self.corners),
        )

    @property
    def corners_max(self) -> Vec3:
        return self.corner_at("+", "+", "+")

    @property
    def corners_min(self) -> Vec3:
        return self.corner_at("-", "-", "-")

    def shifted(self, delta: Vec3) -> "Face":
        return Face(
            direction=self.direction,
            center=self.center + delta,
            size=self.size,
            corners=[c + delta for c in self.corners],
            holes=[h.shifted(delta) for h in self.holes],
            slots=[s.shifted(delta) for s in self.slots],
        )
