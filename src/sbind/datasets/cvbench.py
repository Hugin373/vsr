"""CV-Bench (nyu-visionx/CV-Bench, Apache-2.0) — real-image validation layer.

2,638 MCQ items over 2D (Count / Relation) and 3D (Depth / Distance) tasks. Images are
embedded as bytes in the parquet, so they are extracted to <root>/images/ on first access
and the Item carries a path like every other adapter.

Answers ship as option letters ("(C)"); we keep the letter as ``answer`` and resolve the
option text into ``meta.answer_text``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from .base import Item, dataset_root, materialize_image, register

_LETTERS = "ABCDEFGH"


def _letter_to_index(ans: str) -> int | None:
    s = ans.strip().strip("()").strip()
    if len(s) == 1 and s.upper() in _LETTERS:
        return _LETTERS.index(s.upper())
    return None


@register("cvbench")
def load_cvbench(config: dict, split: str = "both") -> Iterator[Item]:
    """Yield CV-Bench items. ``split`` is '2d', '3d' or 'both'."""
    import pyarrow.parquet as pq

    root = dataset_root(config, "cvbench")
    img_dir = root / "images"

    files = []
    if split in ("2d", "both"):
        files.append(root / "test_2d.parquet")
    if split in ("3d", "both"):
        files.append(root / "test_3d.parquet")

    for path in files:
        if not Path(path).exists():
            raise FileNotFoundError(
                f"{path} missing. Run: uv run --extra analysis "
                f"scripts/download_dataset.py --name cvbench"
            )
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                kind = str(row["type"]).lower()  # '2d' | '3d'
                idx = row["idx"]
                item_id = f"cvbench/{kind}/{idx}"
                img_path = materialize_image(
                    row["image"]["bytes"], img_dir / kind / f"{idx:05d}.png"
                )
                choices = list(row.get("choices") or [])
                ai = _letter_to_index(row["answer"] or "")
                yield Item(
                    id=item_id,
                    images=[img_path],
                    question=row["question"],
                    answer=row["answer"],
                    meta={
                        "dataset_name": "cvbench",
                        "answer_type": "mcq",
                        "options": choices,
                        "answer_text": (
                            choices[ai] if ai is not None and ai < len(choices) else None
                        ),
                        "prompt": row.get("prompt"),
                        "task": row.get("task"),  # Count | Relation | Depth | Distance
                        "type": row.get("type"),
                        "source": row.get("source"),
                        "source_dataset": row.get("source_dataset"),
                        "source_filename": row.get("source_filename"),
                        "original_index": idx,
                    },
                )
