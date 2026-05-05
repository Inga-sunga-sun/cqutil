import ast
import inspect

from cqutil.models import Face, Hole, PartData, Slot, Vec3
from cqutil.part import Part

_FLOAT_FMT = "{:>9.3f}"
_AXIS_TOL = 1e-6


def _fmt_float(x: float) -> str:
    return _FLOAT_FMT.format(x)


def _fmt_vec(v: Vec3) -> str:
    return f"({_fmt_float(v.x)}, {_fmt_float(v.y)}, {_fmt_float(v.z)})"


def _axis_label(v: Vec3) -> str:
    components = [("X", v.x), ("Y", v.y), ("Z", v.z)]
    nonzero = [(name, val) for name, val in components if abs(val) > _AXIS_TOL]
    if len(nonzero) == 1:
        name, val = nonzero[0]
        if abs(abs(val) - 1.0) < _AXIS_TOL:
            return f"{'+' if val > 0 else '-'}{name}"
    return _fmt_vec(v)


def _detect_argname(depth: int = 2) -> str | None:
    frame = inspect.currentframe()
    for _ in range(depth):
        if frame is None:
            return None
        frame = frame.f_back
    if frame is None:
        return None
    info = inspect.getframeinfo(frame)
    if not info.code_context:
        return None
    src = info.code_context[0].strip()
    try:
        tree = ast.parse(src, mode="exec")
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_dump_call = (
                (isinstance(func, ast.Attribute) and func.attr == "dump")
                or (isinstance(func, ast.Name) and func.id == "dump")
            )
            if is_dump_call and node.args and isinstance(node.args[0], ast.Name):
                return node.args[0].id
    return None


def _hole_line(hole: Hole) -> str:
    d = f"{hole.diameter:.3f}" if hole.diameter is not None else "-"
    depth = f"  depth={hole.depth:.3f}" if hole.depth is not None else ""
    return f"#{hole.index}  ⌀{d}{depth}  c={_fmt_vec(hole.center)}"


def _slot_line(slot: Slot) -> str:
    depth = f"  depth={slot.depth:.3f}" if slot.depth is not None else ""
    return (
        f"#{slot.index}  L={slot.length:.3f}  W={slot.width:.3f}{depth}"
        f"  axis={_axis_label(slot.long_axis)}  c={_fmt_vec(slot.center)}"
    )


def _face_lines(face: Face, idx: int, last: bool) -> list[str]:
    branch = "└─" if last else "├─"
    cont = "  " if last else "│ "
    header = (
        f"{branch} Face[{idx}]  {_axis_label(face.direction)}"
        f"  center={_fmt_vec(face.center)}  size={_fmt_vec(face.size)}"
    )
    lines = [header]

    sections: list[tuple[str, list, callable]] = []
    if face.corners:
        sections.append(("corners", face.corners,
                         lambda c, i: f"[{i}] {_fmt_vec(c)}"))
    if face.holes:
        sections.append(("holes", face.holes,
                         lambda h, _i: _hole_line(h)))
    if face.slots:
        sections.append(("slots", face.slots,
                         lambda s, _i: _slot_line(s)))

    for sec_idx, (name, items, fmt) in enumerate(sections):
        is_last_sec = sec_idx == len(sections) - 1
        sec_branch = "└─" if is_last_sec else "├─"
        sec_cont = "  " if is_last_sec else "│ "
        lines.append(f"{cont} {sec_branch} {name} ({len(items)})")
        for i, item in enumerate(items):
            leaf = "└─" if i == len(items) - 1 else "├─"
            lines.append(f"{cont} {sec_cont} {leaf} {fmt(item, i)}")

    return lines


def _part_lines(part: Part | PartData, name: str) -> list[str]:
    lines = [name]

    has_faces = bool(part.faces)
    if part.bbox is not None:
        bbox_branch = "├─" if has_faces else "└─"
        lines.append(
            f"{bbox_branch} bbox  min={_fmt_vec(part.bbox.min)}"
            f"  max={_fmt_vec(part.bbox.max)}"
        )
        lines.append(
            f"{'│ ' if has_faces else '  '}      size={_fmt_vec(part.bbox.size)}"
        )

    if has_faces:
        lines.append(f"└─ faces ({len(part.faces)})")
        for i, face in enumerate(part.faces):
            face_lines = _face_lines(face, i, last=(i == len(part.faces) - 1))
            for fl in face_lines:
                lines.append(f"   {fl}")

    return lines


def dump(part: Part | PartData, name: str | None = None) -> None:
    if name is None:
        name = _detect_argname() or type(part).__name__
    print("\n".join(_part_lines(part, name)))
