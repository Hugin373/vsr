"""Kang et al. synthetic two-object grid scenes — REIMPLEMENTED from the paper.

⚠ LICENSE: `Raphoo/linear-mech-vlms` has NO LICENSE (all rights reserved). This module is
written from the paper's description only. No code was copied. (CLAUDE.md hard rule.)

Recipe (arXiv 2601.12626): two objects are tiled at distinct cells of an m x m grid (m=4) on
a blank canvas; the model is asked a binary spatial relation ("Is the X to the left or right
of the Y?"). Object identity is crossed with grid position, so averaging the object-word-token
activation over objects and mean-centering per object isolates a POSITION code — the "spatial
ID". The scene set must therefore satisfy one non-negotiable invariant:

    **object identity must be decorrelated from grid position.**

If it is not, the "spatial ID" is partly an object code and the whole derivation is circular.
Enforced by construction (each object appears equally often in every cell) and CHECKED by
`assert_position_identity_decorrelated`.

DEVIATION FROM THE PAPER, stated plainly: Kang tile *Objaverse* renders. We do not have
Objaverse, so we tile **COCO instance-mask cutouts** (clean object crops on a white canvas).
This keeps a real, nameable object vocabulary — and it is the SAME vocabulary as the
COCO-Spatial arm, so the two halves of the reproduction share their object names. Object
appearance is not part of the mechanism under test (the spatial ID is what survives
mean-centering ACROSS objects), but it is a deviation and is reported as one.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..utils.logging import get_logger

log = get_logger("sbind.grid_scenes")


@dataclass(frozen=True)
class GridScene:
    """One tiled two-object scene."""

    id: str
    image: str  # path on disk
    obj_a: str  # object name (the SUBJECT of the question)
    obj_b: str  # object name (the REFERENT)
    cell_a: tuple[int, int]  # (col, row) — col is the HORIZONTAL index
    cell_b: tuple[int, int]
    grid_m: int

    @property
    def relation_lr(self) -> str:
        """Ground-truth left/right relation of A with respect to B."""
        return "left" if self.cell_a[0] < self.cell_b[0] else "right"

    @property
    def relation_ab(self) -> str:
        """Ground-truth above/below relation of A with respect to B."""
        return "above" if self.cell_a[1] < self.cell_b[1] else "below"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "image": self.image,
            "obj_a": self.obj_a,
            "obj_b": self.obj_b,
            "cell_a": list(self.cell_a),
            "cell_b": list(self.cell_b),
            "grid_m": self.grid_m,
            "relation_lr": self.relation_lr,
            "relation_ab": self.relation_ab,
        }


# --- object source: COCO instance cutouts ------------------------------------------------


def coco_cutouts(
    coco_root: Path,
    n_objects: int,
    split: str = "val2017",
    min_area: int = 40_000,
    seed: int = 0,
) -> list[tuple[str, Image.Image]]:
    """Cut out one large, unoccluded instance per COCO category -> [(name, RGBA image)].

    One cutout per CATEGORY (not per instance), so the object vocabulary is exactly the set of
    category names the question text uses. Largest-area instances are preferred because a
    small crop upscaled into a grid cell is mostly interpolation artefact.
    """
    from pycocotools.coco import COCO

    ann_file = coco_root / "annotations" / f"instances_{split}.json"
    if not ann_file.exists():
        raise FileNotFoundError(
            f"{ann_file} missing — COCO annotations are required for the object source."
        )
    coco = COCO(str(ann_file))
    cats = coco.loadCats(coco.getCatIds())
    rng = np.random.default_rng(seed)

    out: list[tuple[str, Image.Image]] = []
    skipped: list[str] = []
    for cat in sorted(cats, key=lambda c: c["id"]):
        ann_ids = coco.getAnnIds(catIds=[cat["id"]], iscrowd=False)
        anns = [a for a in coco.loadAnns(ann_ids) if a["area"] >= min_area]
        if not anns:
            skipped.append(cat["name"])
            continue
        ann = max(anns, key=lambda a: a["area"])  # the cleanest, largest exemplar
        img_info = coco.loadImgs([ann["image_id"]])[0]
        img_path = coco_root / split / img_info["file_name"]
        if not img_path.exists():
            skipped.append(cat["name"])
            continue

        img = Image.open(img_path).convert("RGB")
        mask = coco.annToMask(ann).astype(bool)
        arr = np.array(img)
        rgba = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
        rgba[..., :3] = arr
        rgba[..., 3] = mask * 255
        ys, xs = np.nonzero(mask)
        crop = Image.fromarray(rgba).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        out.append((cat["name"], crop))
        if len(out) >= n_objects:
            break

    if len(out) < n_objects:
        raise RuntimeError(
            f"only {len(out)} COCO categories yielded a cutout with area >= {min_area} "
            f"(wanted {n_objects}). Lower min_area or use a different split. "
            f"Skipped: {', '.join(skipped[:10])}"
        )
    rng.shuffle(out)  # not sorted by category id -> pair sampling is not category-ordered
    log.info("coco_cutouts: %d objects from %s (skipped %d)", len(out), split, len(skipped))
    return out[:n_objects]


# --- the tiling engine --------------------------------------------------------------------


def _paste(canvas: Image.Image, obj: Image.Image, cell: tuple[int, int], m: int, pad: float):
    """Paste an object, aspect-preserved and centred, into grid cell (col, row)."""
    W, H = canvas.size
    cw, ch = W // m, H // m
    box = int(cw * (1 - pad)), int(ch * (1 - pad))
    o = obj.copy()
    o.thumbnail(box, Image.LANCZOS)
    col, row = cell
    x = col * cw + (cw - o.width) // 2
    y = row * ch + (ch - o.height) // 2
    canvas.paste(o, (x, y), o)


def build_grid_scenes(
    objects: list[tuple[str, Image.Image]],
    out_dir: Path,
    grid_m: int = 4,
    n_scenes: int = 800,
    resolution: int = 672,
    pad: float = 0.15,
    seed: int = 0,
) -> list[GridScene]:
    """Render ``n_scenes`` two-object grid scenes with identity decorrelated from position.

    Construction (not luck): scenes are generated by cycling object PAIRS against a shuffled
    enumeration of ordered cell pairs, so across the set each object lands in each cell an
    equal number of times (up to the remainder). Verified afterwards by
    ``assert_position_identity_decorrelated``.
    """
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    cells = [(c, r) for c in range(grid_m) for r in range(grid_m)]
    cell_pairs = [(a, b) for a in cells for b in cells if a != b]  # m^2 * (m^2-1) ordered pairs
    obj_pairs = [(i, j) for i in range(len(objects)) for j in range(len(objects)) if i != j]
    rng.shuffle(cell_pairs)
    rng.shuffle(obj_pairs)

    scenes: list[GridScene] = []
    for k in range(n_scenes):
        ca, cb = cell_pairs[k % len(cell_pairs)]
        ia, ib = obj_pairs[k % len(obj_pairs)]
        name_a, img_a = objects[ia]
        name_b, img_b = objects[ib]

        canvas = Image.new("RGBA", (resolution, resolution), (255, 255, 255, 255))
        _paste(canvas, img_a, ca, grid_m, pad)
        _paste(canvas, img_b, cb, grid_m, pad)

        sid = f"grid_{k:05d}"
        path = out_dir / f"{sid}.png"
        canvas.convert("RGB").save(path)
        scenes.append(
            GridScene(
                id=sid,
                image=str(path),
                obj_a=name_a,
                obj_b=name_b,
                cell_a=ca,
                cell_b=cb,
                grid_m=grid_m,
            )
        )

    with open(out_dir.parent / "grid_scenes.jsonl", "w", encoding="utf-8") as f:
        for s in scenes:
            f.write(json.dumps(s.to_dict()) + "\n")
    log.info("built %d grid scenes -> %s", len(scenes), out_dir)
    return scenes


def assert_position_identity_decorrelated(scenes: list[GridScene], tol: float = 0.35) -> dict:
    """THE invariant this dataset exists to satisfy: object identity must not predict cell.

    If an object is over-represented in some cells, mean-centering per object does NOT isolate
    position, and every "spatial ID" downstream is contaminated by object identity — the whole
    derivation becomes circular. So this is checked, not assumed.

    Measures, for each object, the total-variation distance between its cell distribution and
    uniform. Raises if the worst object exceeds ``tol``. Returns the measured stats.
    """
    m = scenes[0].grid_m
    n_cells = m * m
    counts: dict[str, np.ndarray] = {}
    for s in scenes:
        for name, cell in ((s.obj_a, s.cell_a), (s.obj_b, s.cell_b)):
            arr = counts.setdefault(name, np.zeros(n_cells))
            arr[cell[1] * m + cell[0]] += 1

    worst_name, worst_tv = "", 0.0
    for name, arr in counts.items():
        if arr.sum() == 0:
            continue
        p = arr / arr.sum()
        tv = 0.5 * float(np.abs(p - 1.0 / n_cells).sum())  # total variation vs uniform
        if tv > worst_tv:
            worst_name, worst_tv = name, tv

    stats = {
        "n_objects": len(counts),
        "worst_object": worst_name,
        "worst_tv_from_uniform": worst_tv,
        "min_placements": int(min(a.sum() for a in counts.values())),
    }
    if worst_tv > tol:
        raise RuntimeError(
            f"object identity PREDICTS grid position (worst: {worst_name!r}, "
            f"TV={worst_tv:.3f} > {tol}). Mean-centering per object would not isolate a "
            f"position code, so the spatial-ID derivation would be circular. Increase n_scenes."
        )
    log.info(
        "position/identity decorrelation OK: worst TV=%.3f (%s), min placements=%d",
        worst_tv, worst_name, stats["min_placements"],
    )
    return stats


def iter_scenes(path: Path) -> Iterator[GridScene]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            yield GridScene(
                id=d["id"],
                image=d["image"],
                obj_a=d["obj_a"],
                obj_b=d["obj_b"],
                cell_a=tuple(d["cell_a"]),
                cell_b=tuple(d["cell_b"]),
                grid_m=d["grid_m"],
            )
