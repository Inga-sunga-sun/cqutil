from dataclasses import dataclass, field

from cqutil.models.bounding_box import BoundingBox
from cqutil.models.face import Face


@dataclass
class Part:
    bbox: BoundingBox | None = None
    faces: list[Face] = field(default_factory=list)
