"""ReVSI (3dlg-hcvc/ReVSI, Apache-2.0) — the VSI-Bench variant we use.

Corrected VSI-Bench annotations, frame-budgeted, and it ships its OWN videos, so raw
VSI-Bench is never downloaded (that would be +5.7 GB for nothing). Use this over raw
VSI-Bench: the original benchmark's annotations are the ones ReVSI shows to be flawed.

Videos are already sub-sampled per frame budget (``<budget>_frame/<scene_id>.mp4``, e.g.
32_frame/), so a "frame index" here means an index INTO the budgeted clip. Frames are
decoded LAZILY (``base.decode_frames``) — nothing is materialised to disk.

Answers are numeric for counting/distance questions (``options`` is null) and MCQ
otherwise; ``meta.answer_type`` distinguishes them.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from .base import Item, dataset_root, register

BUDGETS = ("16", "32", "64", "all")


@register("revsi")
def load_revsi(config: dict, frame_budget: str | int | None = None) -> Iterator[Item]:
    """Yield ReVSI items. ``frame_budget`` in {16, 32, 64, 'all'} (default from config)."""
    import pyarrow.parquet as pq

    root = dataset_root(config, "revsi")
    entry = (config.get("datasets") or {}).get("revsi", {})
    budget = str(frame_budget or entry.get("frame_budget", 32))
    if budget not in BUDGETS:
        raise ValueError(f"frame_budget must be one of {BUDGETS}, got {budget!r}")

    bdir = root / f"{budget}_frame"
    if not bdir.exists():
        raise FileNotFoundError(
            f"{bdir} missing. Run: uv run --extra analysis "
            f"scripts/download_dataset.py --name revsi"
        )

    # original-video frame indices the dataset sampled (informational; the shipped clip is
    # already the sampled subset, so decoding index i of the clip gives sampled frame i)
    sampled: dict = {}
    meta_path = root / "metadata" / "sampled_video_frame_idx.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            sampled = json.load(f)

    for pfile in sorted(bdir.glob("*.parquet")):
        pf = pq.ParquetFile(pfile)
        for batch in pf.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                scene_id = row["scene_id"]
                video = bdir / f"{scene_id}.mp4"
                if not video.exists():
                    continue
                n_frames = int(row.get("num_frames") or 0)
                options = list(row.get("options") or [])
                yield Item(
                    id=f"revsi/{budget}/{row['id']}",
                    images=[],  # video item: frames are decoded on demand
                    video=str(video),
                    frame_indices=list(range(n_frames)),
                    question=row["question"],
                    answer=str(row["ground_truth"]),
                    meta={
                        "dataset_name": "revsi",
                        "answer_type": "mcq" if options else "numeric",
                        "options": options,
                        "task": row.get("question_type"),
                        "scene_id": scene_id,
                        "source_dataset": row.get("dataset"),  # ARKitScenes | ScanNet | ...
                        "frame_budget": budget,
                        "n_frames": n_frames,
                        "queried_object_ids": row.get("queried_object_ids"),
                        "sampled_original_frame_idx": (
                            sampled.get(scene_id, {}).get(f"{budget}-frame")
                        ),
                        "original_index": row["id"],
                    },
                )
