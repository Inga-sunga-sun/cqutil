# cqutil

CadQuery で読み込んだ STEP モデルから、設計値 (面の位置・穴の中心と直径・長孔の長さや幅・深さなど) を **数値として直接抽出** するユーティリティ。図面を読み解く代わりに 3D モデルから寸法を取り出す用途。

## 必要環境

- Python >= 3.10
- `cadquery` (本ライブラリの依存には含めていません。事前に conda または pip で別途インストールしてください)

## インストール

```bash
pip install git+https://github.com/Inga-sunga-sun/cqutil.git
```

cadquery を再インストールされたくない場合は普通にこれで OK です (`dependencies` に cadquery を入れていないため、pip は cadquery に触りません)。

## クイックスタート

```python
import cadquery as cq
import cqutil as cu
from ocp_vscode import show

plate = cq.importers.importStep("plate.stp")

# Part を組み立てる: 底面 + 上面 + bbox
plate_part = (cu.scan(plate)
    .face("-Z")
    .face("+Z")
    .bbox()
    .build())

# 数値をテキストツリーで確認
cu.dump(plate_part)

# 可視化
markers = cu.markers.holes(plate_part)   # 穴・長孔の位置に円柱マーカー
show(plate, markers)
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

回転は事前に済ませて、`cu.align` で平行移動だけかける。

```python
base_anchor  = cu.scan(base ).face("+Z").build().faces[0].holes[0].center
plate_anchor = cu.scan(plate).face("-Z").build().faces[0].holes[0].center

plate_pos = cu.align(plate, source=plate_anchor, target=base_anchor)
# plate の底面 hole #0 が base の上面 hole #0 に重なるように plate 全体を平行移動した新 Workplane
```

返り値は新しい `cq.Workplane` なので、そのまま `cu.scan(plate_pos).face("+Z").build()` で次の層のアンカー取得に使える (積み重ね可能)。

## API 概要

### 抽出

| シグネチャ | 役割 |
|---|---|
| `cu.scan(wp: cq.Workplane) -> PartBuilder` | チェインビルダのエントリ |
| `PartBuilder.face(direction) -> PartBuilder` | 指定方向の最端面を Part に追加 |
| `PartBuilder.bbox() -> PartBuilder` | 部品全体の BoundingBox を計算 |
| `PartBuilder.build() -> Part` | Part を確定 |
| `cu.select_extreme_faces(wp, direction, tol=1e-6) -> cq.Workplane` | 低レベル: 方向指定で最端面を選択 |

`direction` は `"+X" / "-X" / "+Y" / "-Y" / "+Z" / "-Z"`。

### 表示

| シグネチャ | 役割 |
|---|---|
| `cu.dump(part: Part, name: str \| None = None)` | Part をツリー出力。`name` 省略時は変数名を自動検出 |

### 可視化マーカー

| シグネチャ | 役割 |
|---|---|
| `cu.markers.holes(face_or_part) -> list[cq.Assembly]` | 穴・長孔の中心に円柱 + 番号ラベル。Hole/Slot 両方含む |
| `cu.markers.faces(wp: cq.Workplane) -> list[cq.Assembly]` | Workplane 内の各面をハイライト |

### 操作

| シグネチャ | 役割 |
|---|---|
| `cu.align(part: cq.Workplane, source: Vec3, target: Vec3) -> cq.Workplane` | `source` 点が `target` 点に重なるよう平行移動 (回転は呼び出し側で済ませる) |

### データモデル (`cqutil.models`)

| 型 | 主なフィールド |
|---|---|
| `Vec3(x, y, z)` | 3D ベクトル。`+`, `-`, `*`, `length`, `normalized()` 等 |
| `BoundingBox(min, max)` | `.size`, `.center` |
| `Hole` | `center`, `diameter`, `depth`, `index` |
| `Slot` | `center`, `length`, `width`, `long_axis`, `depth`, `index` |
| `Face` | `direction`, `center`, `size`, `holes`, `slots` |
| `Part` | `bbox`, `faces` |
| `Direction` | `Literal["+X" \| "-X" \| "+Y" \| "-Y" \| "+Z" \| "-Z"]` |

## 設計メモ

- `cqutil.models` は cadquery 非依存の純 dataclass
- 抽出 (`extract.py`) のみ cadquery / OCP を直接利用
- 自動全件スキャンはせず、`scan().face("-Z")` のように **面を明示選択** するチェイン API
- 数値抽出が主目的。SVG 等の装飾系は提供しない
