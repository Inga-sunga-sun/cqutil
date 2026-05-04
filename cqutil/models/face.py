from dataclasses import dataclass, field

from cqutil.models.hole import Hole
from cqutil.models.slot import Slot
from cqutil.models.vec3 import Vec3


@dataclass
class Face:
    direction: Vec3
    center: Vec3
    size: Vec3
    holes: list[Hole] = field(default_factory=list)
    slots: list[Slot] = field(default_factory=list)
