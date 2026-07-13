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
from pathlib import Path

from ..utils.logging import get_logger
from .base import LETTERS, Item, dataset_root, register, strip_option_letters

log = get_logger("sbind.revsi")

BUDGETS = ("16", "32", "64", "all")


_CLIP_LEN: dict[str, int] = {}  # video path -> real frame count (metadata read is not free)


def _clip_length(video_path: Path) -> int:
    """Real frame count of a clip, read from container metadata (no decode). Cached per file.

    ⚠ Do NOT use the parquet's ``num_frames`` column for this. It is a budget LABEL, not a
    count: in ``all_frame/`` it holds the literal string ``'all'`` for every row, so
    ``int(num_frames)`` raised ValueError and the entire 'all' budget — one of the four
    documented settings of the dataset whose whole thesis is budget-sensitivity — was dead.
    For 16/32/64 the label happens to equal the clip length; 'all' clips run 56–4,337 frames.
    Deriving the count from the artefact makes all four budgets work and removes the trust.
    """
    key = str(video_path)
    if key not in _CLIP_LEN:
        import av

        with av.open(key) as c:
            stream = c.streams.video[0]
            n = int(stream.frames or 0)
            if n <= 0:  # container did not declare it — count by demuxing packets (still cheap)
                n = sum(1 for p in c.demux(stream) if p.pts is not None)
        if n <= 0:
            raise RuntimeError(f"{video_path}: could not determine a frame count (got {n})")
        _CLIP_LEN[key] = n
    return _CLIP_LEN[key]


@register("revsi")
def load_revsi(config: dict, frame_budget: str | int | None = None) -> Iterator[Item]:
    """Yield ReVSI items. ``frame_budget`` in {16, 32, 64, 'all'} (default from config)."""
    import pyarrow.parquet as pq

    root = dataset_root(config, "revsi")
    entry = (config.get("datasets") or {}).get("revsi", {})
    explicit = frame_budget is not None
    budget = str(frame_budget or entry.get("frame_budget", 32))
    if budget not in BUDGETS:
        raise ValueError(f"frame_budget must be one of {BUDGETS}, got {budget!r}")
    # The frame budget is a SCIENTIFIC parameter, not a loader detail — ReVSI's whole point
    # is that conclusions change with it. Never let a default slip silently into a result:
    # log it, and record it in meta.frame_budget on every item.
    log.info(
        "revsi: frame_budget=%s (%s)",
        budget,
        "explicit"
        if explicit
        else "DEFAULT — set it in the experiment config for any reported result",
    )

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

    missing_video = 0
    yielded = 0
    for pfile in sorted(bdir.glob("*.parquet")):
        pf = pq.ParquetFile(pfile)
        for batch in pf.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                scene_id = row["scene_id"]
                video = bdir / f"{scene_id}.mp4"
                if not video.exists():
                    # counted + reported below, never a silent shrink
                    missing_video += 1
                    continue
                # derived from the clip itself, NOT from the parquet's num_frames label
                n_frames = _clip_length(video)
                # MCQ options ship PRE-LETTERED ("A. wall picture") and ground_truth is the
                # bare letter — so strip the markers and resolve the letter to its text,
                # like every other adapter, or a scorer cannot match an answer to an option.
                raw_options = list(row.get("options") or [])
                options = strip_option_letters(raw_options)
                gt = str(row["ground_truth"]).strip()
                letter = gt if options and gt in LETTERS[: len(options)] else None
                answer_text = options[LETTERS.index(letter)] if letter else None
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
                        "answer_letter": letter,
                        "answer_text": answer_text,
                        "options_raw": raw_options,
                        "task": row.get("question_type"),
                        "scene_id": scene_id,
                        "source_dataset": row.get("dataset"),  # ARKitScenes | ScanNet | ...
                        "frame_budget": budget,
                        "n_frames": n_frames,  # real clip length, verified against the artefact
                        "n_frames_upstream": row.get("num_frames"),  # the raw label ('all', 32…)
                        "queried_object_ids": row.get("queried_object_ids"),
                        "sampled_original_frame_idx": (
                            sampled.get(scene_id, {}).get(f"{budget}-frame")
                        ),
                        "original_index": row["id"],
                    },
                )
                yielded += 1

    # A subset that resolves nothing is a broken assumption, not an empty dataset.
    if yielded == 0:
        raise RuntimeError(
            f"revsi/{budget}: resolved 0 of {missing_video} rows to a video under {bdir}. "
            f"The on-disk layout is not what the adapter expects."
        )
    if missing_video:
        log.warning(
            "revsi/%s: %d rows skipped — their scene video is missing on disk",
            budget,
            missing_video,
        )
