from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec3") -> "Vec3":
        return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, k: float) -> "Vec3":
        return Vec3(self.x * k, self.y * k, self.z * k)

    @property
    def length(self) -> float:
        return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> "Vec3":
        L = self.length
        return Vec3(self.x / L, self.y / L, self.z / L) if L > 0 else self

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def perpendicular_basis(self) -> tuple["Vec3", "Vec3"]:
        ref = Vec3(0, 0, 1) if abs(self.z) < 0.9 else Vec3(1, 0, 0)
        u = self.cross(ref).normalized()
        v = self.cross(u).normalized()
        return u, v
