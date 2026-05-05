from dataclasses import dataclass, field

from cqutil.models.bounding_box import BoundingBox
from cqutil.models.face import Face
from cqutil.models.vec3 import Vec3


@dataclass
class PartData:
    bbox: BoundingBox | None = None
    faces: list[Face] = field(default_factory=list)

    def shifted(self, delta: Vec3) -> "PartData":
        return PartData(
            bbox=self.bbox.shifted(delta) if self.bbox is not None else None,
            faces=[f.shifted(delta) for f in self.faces],
        )
