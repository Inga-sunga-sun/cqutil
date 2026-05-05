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

    def shifted(self, delta: Vec3) -> "Face":
        return Face(
            direction=self.direction,
            center=self.center + delta,
            size=self.size,
            corners=[c + delta for c in self.corners],
            holes=[h.shifted(delta) for h in self.holes],
            slots=[s.shifted(delta) for s in self.slots],
        )
