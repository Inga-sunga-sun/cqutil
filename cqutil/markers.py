import cadquery as cq

from cqutil.models import Face, Vec3

_MARKER_RADIUS = 0.5
_MARKER_HEIGHT = 5.0
_MARKER_LABEL_SIZE = 11.0
_MARKER_COLOR_NAME = "pink"
_MARKER_ALPHA = 0.9
_LABEL_INPLANE_OFFSET_RATIO = 0.3

_FACE_MARKER_COLOR_NAME = "pink"
_FACE_MARKER_ALPHA = 0.5


def _to_cq_vector(v: Vec3) -> cq.Vector:
    return cq.Vector(v.x, v.y, v.z)


def _color_with_alpha(color: str, alpha: float = 1.0) -> cq.Color:
    r, g, b, _ = cq.Color(color).toTuple()
    return cq.Color(r, g, b, alpha)


def _make_label_shape(
    text: str,
    position: cq.Vector,
    fontsize: float,
    offset: cq.Vector,
) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .text(text, fontsize=fontsize, distance=fontsize * 0.2)
        .val()
        .translate(position + offset)
    )


def _point_marker(
    center: Vec3, label: str, normal: Vec3, color: cq.Color,
) -> cq.Assembly:
    u, v = normal.perpendicular_basis()
    diagonal = u + v
    label_offset = (
        normal * (_MARKER_HEIGHT + _MARKER_LABEL_SIZE * 0.5)
        + diagonal * (_MARKER_LABEL_SIZE * _LABEL_INPLANE_OFFSET_RATIO)
    )

    center_cq = _to_cq_vector(center)
    cylinder = cq.Solid.makeCylinder(
        _MARKER_RADIUS, _MARKER_HEIGHT,
        pnt=center_cq, dir=_to_cq_vector(normal),
    )
    label_shape = _make_label_shape(
        label, center_cq, _MARKER_LABEL_SIZE, _to_cq_vector(label_offset),
    )
    return cq.Assembly(
        cq.Compound.makeCompound([cylinder, label_shape]),
        color=color,
        name=label,
    )


def _markers_at(positions: list[Vec3], normal: Vec3) -> list[cq.Assembly]:
    color = _color_with_alpha(_MARKER_COLOR_NAME, _MARKER_ALPHA)
    return [_point_marker(p, str(i), normal, color) for i, p in enumerate(positions)]


def holes(face: Face) -> list[cq.Assembly]:
    return _markers_at([h.center for h in face.holes], face.direction)


def slots(face: Face) -> list[cq.Assembly]:
    return _markers_at([s.center for s in face.slots], face.direction)


def corners(face: Face) -> list[cq.Assembly]:
    return _markers_at(face.corners, face.direction)


def faces(workplane: cq.Workplane) -> list[cq.Assembly]:
    color = _color_with_alpha(_FACE_MARKER_COLOR_NAME, _FACE_MARKER_ALPHA)
    return [
        cq.Assembly(face, color=color, name=str(i))
        for i, face in enumerate(workplane.faces().vals())
    ]
