import ast
import inspect

from cqutil.models import Face, Hole, Part, Slot, Vec3

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

    holes = face.holes
    slots = face.slots
    has_slots = bool(slots)

    if holes:
        h_branch = "├─" if has_slots else "└─"
        h_cont = "│ " if has_slots else "  "
        lines.append(f"{cont} {h_branch} holes ({len(holes)})")
        for i, h in enumerate(holes):
            leaf = "└─" if i == len(holes) - 1 else "├─"
            lines.append(f"{cont} {h_cont} {leaf} {_hole_line(h)}")

    if slots:
        lines.append(f"{cont} └─ slots ({len(slots)})")
        for i, s in enumerate(slots):
            leaf = "└─" if i == len(slots) - 1 else "├─"
            lines.append(f"{cont}    {leaf} {_slot_line(s)}")

    return lines


def _part_lines(part: Part, name: str) -> list[str]:
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


def dump(part: Part, name: str | None = None) -> None:
    if name is None:
        name = _detect_argname() or type(part).__name__
    print("\n".join(_part_lines(part, name)))
