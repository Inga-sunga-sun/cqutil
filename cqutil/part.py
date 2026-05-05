from dataclasses import dataclass

import cadquery as cq

from cqutil.models import BoundingBox, Face, PartData, Vec3


@dataclass
class Part:
    workplane: cq.Workplane
    data: PartData

    @property
    def faces(self) -> list[Face]:
        return self.data.faces

    @property
    def bbox(self) -> BoundingBox | None:
        return self.data.bbox

    def shifted(self, delta: Vec3) -> "Part":
        return Part(
            workplane=self.workplane.translate((delta.x, delta.y, delta.z)),
            data=self.data.shifted(delta),
        )

    def move_to(self, source: Vec3, target: Vec3) -> "Part":
        return self.shifted(target - source)
