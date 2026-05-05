from dataclasses import dataclass

from cqutil.models.vec3 import Vec3


@dataclass
class BoundingBox:
    min: Vec3
    max: Vec3

    @property
    def size(self) -> Vec3:
        return self.max - self.min

    @property
    def center(self) -> Vec3:
        return (self.min + self.max) * 0.5

    def shifted(self, delta: Vec3) -> "BoundingBox":
        return BoundingBox(min=self.min + delta, max=self.max + delta)
