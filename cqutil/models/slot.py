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

    def shifted(self, delta: Vec3) -> "Slot":
        return Slot(
            center=self.center + delta,
            length=self.length,
            width=self.width,
            long_axis=self.long_axis,
            depth=self.depth,
            index=self.index,
        )
