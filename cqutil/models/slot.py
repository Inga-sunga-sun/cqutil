from dataclasses import dataclass

from cqutil.models.vec3 import Vec3


@dataclass
class Slot:
    center: Vec3
    length: float
    width: float
    long_axis: Vec3
    depth: float | None = None
    index: int = 0

    @property
    def radius(self) -> float:
        return self.width / 2
