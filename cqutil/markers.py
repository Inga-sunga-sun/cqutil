from functools import singledispatch

import cadquery as cq

from cqutil.models import Face, Part, Vec3

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


@singledispatch
def holes(obj) -> list[cq.Assembly]:
    raise NotImplementedError(f"holes() not supported for {type(obj).__name__}")


@holes.register
def _(face: Face) -> list[cq.Assembly]:
    color = _color_with_alpha(_MARKER_COLOR_NAME, _MARKER_ALPHA)
    items = [*face.holes, *face.slots]
    return [
        _point_marker(item.center, str(i), face.direction, color)
        for i, item in enumerate(items)
    ]


@holes.register
def _(part: Part) -> list[cq.Assembly]:
    result: list[cq.Assembly] = []
    for face in part.faces:
        result.extend(holes(face))
    return result


def faces(workplane: cq.Workplane) -> list[cq.Assembly]:
    color = _color_with_alpha(_FACE_MARKER_COLOR_NAME, _FACE_MARKER_ALPHA)
    return [
        cq.Assembly(face, color=color, name=str(i))
        for i, face in enumerate(workplane.faces().vals())
    ]
