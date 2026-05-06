# cqutil

CadQuery で読み込んだ STEP モデルから、設計値 (面の位置・穴の中心と直径・長孔の長さや幅・深さなど) を **数値として直接抽出** するユーティリティ。図面を読み解く代わりに 3D モデルから寸法を取り出す用途。

## 必要環境

- Python >= 3.10
- `cadquery` (本ライブラリの依存には含めていません。事前に conda または pip で別途インストールしてください)

## インストール

```bash
pip install git+https://github.com/Inga-sunga-sun/cqutil.git
```

cadquery を再インストールされたくない場合も普通にこれで OK です (`dependencies` に cadquery を入れていないため、pip は cadquery に触りません)。

## クイックスタート

```python
import cadquery as cq
import cqutil as cu
from ocp_vscode import show

plate = cq.importers.importStep("plate.stp")

# Part (wrapper) を組み立てる: 底面 + 上面 + bbox
plate_part = (cu.scan(plate)
    .face("-Z")
    .face("+Z")
    .bbox()
    .build())

# 数値をテキストツリーで確認
cu.dump(plate_part)

# 可視化 (Face を渡すだけ)
face0 = plate_part.faces[0]
show(
    plate_part.workplane,
    cu.markers.holes(face0),
    cu.markers.slots(face0),
    cu.markers.corners(face0),
)
```

`cu.dump` の出力例:
```
plate_part
├─ bbox  min=(...,...,...)  max=(...,...,...)
│       size=(  200.000,  100.000,    5.000)
└─ faces (2)
   ├─ Face[0]  -Z  center=( 100.000,   50.000,    0.000)  size=( 200.000,  100.000,    0.000)
   │  ├─ holes (3)
   │  │  ├─ #0  ⌀5.000  depth=5.000  c=( -90.000,  -40.000,    0.000)
   │  │  └─ ...
   │  └─ slots (1)
   │     └─ #0  L=30.000  W=10.000  depth=5.000  axis=+X  c=(  50.000,    0.000,    0.000)
   └─ Face[1]  +Z  ...
```

## 部品の積み重ね (アセンブリ位置決め)

回転は事前に済ませて、`Part.move_to` で平行移動だけかける。

```python
base_part  = cu.scan(base ).face("+Z").build()
plate_part = cu.scan(plate).face("-Z").face("+Z").build()

plate_at = plate_part.move_to(
    source=plate_part.faces[0].holes[0].center,    # plate の底面 hole #0
    target=base_part.faces[0].holes[0].center,     # base の天面 hole #0
)

# plate_at は新しい Part (wrapper)
plate_at.workplane                              # 移動済みの cq.Workplane
plate_at.faces[0].holes[0].center               # delta シフト後の Vec3 (= base_part.faces[0].holes[0].center に一致)

# 上に更に積む例
bracket_part = cu.scan(bracket).face("-Z").build()
bracket_at = bracket_part.move_to(
    source=bracket_part.faces[0].holes[0].center,
    target=plate_at.faces[1].holes[0].center,    # plate_at の上面 hole #0 に
)

show(plate_at.workplane, bracket_at.workplane)
```

`Part.move_to(source, target)` は内部で `data` (数値) と `workplane` (cadquery 幾何) を**同じ delta で同時シフト**します。再 scan 不要。

### オフセット (隙間・浮き上がり)

`target` に `Vec3` を足すか、`.shifted(...)` を続ける:

```python
# A: target にオフセットを足す (合わせ先をずらす)
offset = Vec3(0, 0, 5)
plate_at = plate_part.move_to(
    source=plate_part.faces[0].holes[0].center,
    target=base_part.faces[0].holes[0].center + offset,
)

# B: move_to の後に shifted を続ける (重ねたあとに浮かせる)
plate_at = (
    plate_part
    .move_to(plate_part.faces[0].holes[0].center, base_part.faces[0].holes[0].center)
    .shifted(Vec3(0, 0, 5))
)
```

`move_to` / `shifted` は新しい `Part` を返すので、戻り値を変数で受けないと結果が捨てられる。

## 「STEP 原点を Part の角に合わせる」ような用途も

`source` / `target` は任意の Vec3 を取れるので:

```python
# bbox 角を世界原点に
plate_at_origin = plate_part.move_to(
    source=plate_part.bbox.min,
    target=Vec3(0, 0, 0),
)

# 中心を世界原点に
plate_centered = plate_part.move_to(
    source=plate_part.bbox.center,
    target=Vec3(0, 0, 0),
)

# 面の特定の角を任意の点に
plate_corner_at = plate_part.move_to(
    source=plate_part.faces[0].corners[0],   # 底面の左下角
    target=Vec3(10, 20, 0),
)
```

## API 概要

### 抽出

| シグネチャ | 役割 |
|---|---|
| `cu.scan(wp: cq.Workplane) -> PartBuilder` | チェインビルダのエントリ |
| `PartBuilder.face(direction) -> PartBuilder` | 指定方向の最端面を加える |
| `PartBuilder.face_at(direction, position) -> PartBuilder` | 指定方向・指定位置の面を加える (奥まった面用) |
| `PartBuilder.bbox() -> PartBuilder` | 部品全体の BoundingBox を計算 |
| `PartBuilder.build() -> Part` | Part (wrapper) を確定 |
| `cu.select_extreme_faces(wp, direction, tol=1e-6) -> cq.Workplane` | 低レベル: 方向指定で最端面選択 |
| `cu.select_faces_at(wp, direction, position, tol=1e-6) -> cq.Workplane` | 低レベル: 方向 + 位置で面選択 |

`direction` は `"+X" / "-X" / "+Y" / "-Y" / "+Z" / "-Z"`。

### Part (wrapper)

| メンバ | 役割 |
|---|---|
| `part.workplane` | 中身の `cq.Workplane` |
| `part.data` | 抽出データ (`PartData`) |
| `part.faces` | data のショートカット (`part.data.faces` と等価) |
| `part.bbox` | data のショートカット |
| `part.shifted(delta) -> Part` | delta シフトした新 Part |
| `part.move_to(source, target) -> Part` | source 点を target 点に重ねるよう平行移動した新 Part |

### 表示

| シグネチャ | 役割 |
|---|---|
| `cu.dump(part: Part \| PartData, name=None)` | ツリー出力。`name` 省略時は変数名を自動検出 |

### 可視化マーカー

| シグネチャ | 役割 |
|---|---|
| `cu.markers.holes(face: Face) -> list[cq.Assembly]` | face の穴中心に円柱 + 番号ラベル |
| `cu.markers.slots(face: Face) -> list[cq.Assembly]` | face のスロット中心に同上 |
| `cu.markers.corners(face: Face) -> list[cq.Assembly]` | face の各角に同上 |
| `cu.markers.faces(face: Face) -> list[cq.Assembly]` | face を corners から再構築してハイライト (長方形面のみ正確) |

すべて Face 単位。Part 全体に適用したい場合は `for face in part.faces:` でループ。

### 2D 投影 (cadquery `pushPoints` 連携)

`cu.project` は **world 軸基準** で 2 軸を抜き出す。`pushPoints` 側の workplane は
**原点が world (0, 0, _) で軸が world と一致** している前提（例:
`cq.Workplane("XY", origin=(0, 0, h))`）。`.faces(...).workplane()` で
面に乗せる流儀だと原点・向きがずれて噛み合わないので注意。

| シグネチャ | 役割 |
|---|---|
| `cu.project(points: list[Vec3], axes="xy") -> list[tuple[float, float]]` | 各点から指定 2 軸を抜いて 2D タプルにする。`axes="xy" / "xz" / "yz"` |

```python
# 既定 "xy"
xy_pts = cu.project([h.center for h in face.holes])
result = dst_wp.pushPoints(xy_pts).hole(5.0)

# 異径混在は径ごとにグルーピング (cadquery の hole は 1 径ずつ)
from collections import defaultdict
by_d = defaultdict(list)
for h in face.holes:
    by_d[h.diameter].append(h.center)

wp = dst_wp
for d, pts in by_d.items():
    wp = wp.pushPoints(cu.project(pts)).hole(d)

# corners や slots 中心も同じ流儀
dst_wp.pushPoints(cu.project(face.corners)).hole(2.0)
dst_wp.pushPoints(cu.project([s.center for s in face.slots])).hole(3.0)
```

### データモデル (`cqutil.models`)

| 型 | 主なフィールド |
|---|---|
| `Vec3(x, y, z)` | 3D ベクトル。`+`, `-`, `*`, `length`, `normalized()` 等 |
| `BoundingBox(min, max)` | `.size`, `.center`, `.shifted(delta)` |
| `Hole` | `center`, `diameter`, `depth`, `index`, `.radius`, `.shifted(delta)` |
| `Slot` | `center`, `length`, `width`, `long_axis`, `depth`, `index`, `.radius`, `.shifted(delta)` |
| `Face` | `direction`, `center`, `size`, `corners`, `holes`, `slots`, `.shifted(delta)`, `.corner_at(x, y, z)`, `.corners_max`, `.corners_min` |
| `PartData` | `bbox`, `faces`, `.shifted(delta)` |
| `Direction` | `Literal["+X" \| "-X" \| "+Y" \| "-Y" \| "+Z" \| "-Z"]` |

## 設計メモ

- `cqutil.models` は cadquery 非依存の純 dataclass
- `cqutil.part` の `Part` クラスのみが cadquery `Workplane` を保持 (= 「数値 + 幾何」の窓口)
- 抽出 (`extract.py`) は cadquery / OCP を直接利用
- 自動全件スキャンはせず、`scan().face("-Z")` のように **面を明示選択** するチェイン API
- 数値抽出が主目的。SVG 等の装飾系は提供しない
