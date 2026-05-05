from dataclasses import dataclass

from cqutil.models.vec3 import Vec3


@dataclass
class Hole:
    center: Vec3
    diameter: float | None = None
    depth: float | None = None
    index: int = 0

    @property
    def radius(self) -> float | None:
        return self.diameter / 2 if self.diameter is not None else None

    def shifted(self, delta: Vec3) -> "Hole":
        return Hole(
            center=self.center + delta,
            diameter=self.diameter,
            depth=self.depth,
            index=self.index,
        )
