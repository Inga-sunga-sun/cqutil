from typing import Literal

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

from cqutil.models import (
    BoundingBox,
    Direction,
    Face,
    Hole,
    Part,
    Slot,
    Vec3,
)


def _to_vec3(v: cq.Vector) -> Vec3:
    return Vec3(v.x, v.y, v.z)


def _face_axis_position(face: cq.Face, axis: str) -> float:
    return getattr(face.Center(), axis)


def _circle_diameter(edges: list[cq.Edge]) -> float | None:
    return next(
        (2 * edge.radius() for edge in edges if edge.geomType() == "CIRCLE"),
        None,
    )


def _wire_kind(edges: list[cq.Edge]) -> Literal["round", "slot", "other"]:
    edge_types = [edge.geomType() for edge in edges]
    n_circle = edge_types.count("CIRCLE")
    n_line = edge_types.count("LINE")
    if n_circle == len(edge_types) and n_circle >= 1:
        return "round"
    if n_circle == 2 and n_line == 2 and len(edge_types) == 4:
        return "slot"
    return "other"


def _slot_long_axis(circle_edges: list[cq.Edge]) -> Vec3:
    if len(circle_edges) < 2:
        return Vec3(0, 0, 0)
    direction = circle_edges[1].arcCenter() - circle_edges[0].arcCenter()
    return _to_vec3(direction.normalized())


def _slot_width(circle_edges: list[cq.Edge]) -> float:
    if not circle_edges:
        return 0.0
    return 2 * circle_edges[0].radius()


def _slot_length(circle_edges: list[cq.Edge]) -> float:
    if len(circle_edges) < 2:
        return 0.0
    radius = circle_edges[0].radius()
    center_dist = (circle_edges[1].arcCenter() - circle_edges[0].arcCenter()).Length
    return center_dist + 2 * radius


def _cq_face_size(coplanar_faces: list[cq.Face]) -> Vec3:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for face in coplanar_faces:
        for vert in face.outerWire().Vertices():
            p = vert.Center()
            xs.append(p.x)
            ys.append(p.y)
            zs.append(p.z)
    if not xs:
        return Vec3(0, 0, 0)
    return Vec3(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def _cq_face_center(coplanar_faces: list[cq.Face]) -> Vec3:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for f in coplanar_faces:
        for v in f.outerWire().Vertices():
            p = v.Center()
            xs.append(p.x)
            ys.append(p.y)
            zs.append(p.z)
    if not xs:
        return Vec3(0, 0, 0)
    return Vec3(sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))


def _cylinder_axial_length(cyl_face: cq.Face) -> float:
    adaptor = BRepAdaptor_Surface(cyl_face.wrapped)
    return abs(adaptor.LastVParameter() - adaptor.FirstVParameter())


def _find_cylinder_for_edge(
    candidate_faces: list[cq.Face], target_edge: cq.Edge,
) -> cq.Face | None:
    for face in candidate_faces:
        if face.geomType() != "CYLINDER":
            continue
        for edge in face.Edges():
            if edge.wrapped.IsSame(target_edge.wrapped):
                return face
    return None


def _circle_depth(
    candidate_faces: list[cq.Face], circle_edge: cq.Edge,
) -> float | None:
    cyl = _find_cylinder_for_edge(candidate_faces, circle_edge)
    return _cylinder_axial_length(cyl) if cyl else None


def _extract_holes(
    coplanar_faces: list[cq.Face], all_faces: list[cq.Face],
) -> list[Hole]:
    holes: list[Hole] = []
    for face in coplanar_faces:
        for wire in face.innerWires():
            edges = wire.Edges()
            if _wire_kind(edges) != "round":
                continue
            circle = next((e for e in edges if e.geomType() == "CIRCLE"), None)
            if circle is None:
                continue
            holes.append(Hole(
                center=_to_vec3(circle.arcCenter()),
                diameter=_circle_diameter(edges),
                depth=_circle_depth(all_faces, circle),
                index=len(holes),
            ))
    return holes


def _extract_slots(
    coplanar_faces: list[cq.Face], all_faces: list[cq.Face],
) -> list[Slot]:
    slots: list[Slot] = []
    for face in coplanar_faces:
        for wire in face.innerWires():
            edges = wire.Edges()
            if _wire_kind(edges) != "slot":
                continue
            circle_edges = [e for e in edges if e.geomType() == "CIRCLE"]
            if len(circle_edges) < 2:
                continue
            c0 = circle_edges[0].arcCenter()
            c1 = circle_edges[1].arcCenter()
            slots.append(Slot(
                center=Vec3((c0.x + c1.x) * 0.5, (c0.y + c1.y) * 0.5, (c0.z + c1.z) * 0.5),
                length=_slot_length(circle_edges),
                width=_slot_width(circle_edges),
                long_axis=_slot_long_axis(circle_edges),
                depth=_circle_depth(all_faces, circle_edges[0]),
                index=len(slots),
            ))
    return slots


def _extract_bbox(obj: cq.Workplane) -> BoundingBox:
    bb = obj.val().BoundingBox()
    return BoundingBox(
        min=Vec3(bb.xmin, bb.ymin, bb.zmin),
        max=Vec3(bb.xmax, bb.ymax, bb.zmax),
    )


def _build_face(
    coplanar_faces: list[cq.Face], all_faces: list[cq.Face],
) -> Face:
    normal = coplanar_faces[0].normalAt()
    return Face(
        direction=_to_vec3(normal),
        center=_cq_face_center(coplanar_faces),
        size=_cq_face_size(coplanar_faces),
        holes=_extract_holes(coplanar_faces, all_faces),
        slots=_extract_slots(coplanar_faces, all_faces),
    )


def select_extreme_faces(
    obj: cq.Workplane,
    direction: Direction = "-Z",
    tol: float = 1e-6,
) -> cq.Workplane:
    sign = direction[0]
    axis = direction[1].lower()

    axis_normal_planes = [
        face for face in obj.faces().vals()
        if face.geomType() == "PLANE"
        and abs(getattr(face.normalAt(), axis)) > 1 - tol
    ]

    positions = [_face_axis_position(face, axis) for face in axis_normal_planes]

    if sign == "+":
        extreme_position = max(positions)
    else:
        extreme_position = min(positions)

    selected_faces = [
        face for face, position in zip(axis_normal_planes, positions)
        if abs(position - extreme_position) <= tol
    ]
    return obj.newObject(selected_faces)


class PartBuilder:
    def __init__(self, workplane: cq.Workplane):
        self._wp = workplane
        self._all_faces: list[cq.Face] = workplane.faces().vals()
        self._part = Part()

    def face(self, direction: Direction) -> "PartBuilder":
        cqfaces: list[cq.Face] = select_extreme_faces(self._wp, direction).vals()
        if cqfaces:
            self._part.faces.append(_build_face(cqfaces, self._all_faces))
        return self

    def bbox(self) -> "PartBuilder":
        self._part.bbox = _extract_bbox(self._wp)
        return self

    def build(self) -> Part:
        return self._part


def scan(workplane: cq.Workplane) -> PartBuilder:
    return PartBuilder(workplane)
