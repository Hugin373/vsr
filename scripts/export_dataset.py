"""Materialize a dataset into an inspectable, uniform on-disk layout.

    $DATA_ROOT/external/<name>/
        items.jsonl     <- one JSON line per item, the uniform Item schema
        images/         <- ALL embedded images extracted (parquet-embedded datasets)

Why this exists: adapters extract parquet-embedded images LAZILY, as a side effect of
iteration. That meant what was on disk depended on which script you last ran — CausalSpatial
had images for `collision` and nothing for the other four subsets. This script makes the
on-disk state explicit, complete and reproducible, and gives every external dataset the same
shape as our own stimuli sets (images/ + a jsonl manifest).

items.jsonl is the browsable index: id, question, answer, image paths, and meta. Grep it,
open it in pandas, or eyeball it — no Python adapter needed to see what is in a dataset.

Video datasets (ReVSI) record the video path + frame indices instead of images; frames stay
lazily decoded (materialising ~6k clips' frames would be enormous and pointless).

Usage:
    uv run --extra analysis scripts/export_dataset.py --name causalspatial
    uv run --extra analysis scripts/export_dataset.py --all
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

from sbind.datasets import load
from sbind.utils.config import load_config
from sbind.utils.io import write_jsonl
from sbind.utils.logging import get_logger

log = get_logger("sbind.export")

ALL = ["cvbench", "mindcube", "causalspatial", "depthcues", "revsi", "whatsup"]


def export(name: str, config: dict) -> dict:
    root = Path(config["root"]) / name
    out = root / "items.jsonl"

    t0 = time.time()
    records = []
    subsets: Counter = Counter()
    n_images = 0
    n_video = 0
    for item in load(name, config):  # full pass -> forces every embedded image to disk
        d = item.to_dict()
        records.append(d)
        key = item.meta.get("subset") or item.meta.get("cue") or item.meta.get("type") or "-"
        subsets[str(key)] += 1
        n_images += len(item.images)
        n_video += 1 if item.video else 0

    write_jsonl(records, out)
    dt = time.time() - t0
    log.info(
        "%s: %d items, %d image files, %d video items -> %s (%.1fs)",
        name,
        len(records),
        n_images,
        n_video,
        out,
        dt,
    )
    return {"name": name, "items": len(records), "images": n_images, "video": n_video,
            "subsets": dict(subsets), "path": str(out)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Materialize datasets to items.jsonl + images/.")
    ap.add_argument("--config", default="configs/datasets.yaml")
    ap.add_argument("--name")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    config = load_config(args.config)
    names = ALL if args.all else ([args.name] if args.name else [])
    if not names:
        ap.error("pass --name X or --all")

    summaries = [export(n, config) for n in names]

    print(f"\n{'dataset':16s} {'items':>7s} {'imgs':>7s} {'video':>6s}  subsets")
    for s in summaries:
        subs = ", ".join(f"{k}={v}" for k, v in sorted(s["subsets"].items()))
        print(f"{s['name']:16s} {s['items']:7d} {s['images']:7d} {s['video']:6d}  {subs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
