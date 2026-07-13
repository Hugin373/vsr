"""Backfill mask_area_px into an existing set's annotations.jsonl — no re-render.

Reads each object's already-rendered mask PNG and counts its pixels. The renderer now
computes the same field at render time, so a freshly rendered set and a backfilled set
agree; this exists only to avoid re-rendering an existing set.

Usage:
    uv run --extra analysis scripts/backfill_mask_area.py --set $DATA_ROOT/stimuli/v0_congruent
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from sbind.utils.io import read_jsonl, write_jsonl


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill mask_area_px from rendered masks.")
    ap.add_argument("--set", required=True, help="path to the stimulus set dir")
    args = ap.parse_args()

    set_dir = Path(args.set)
    ann_path = set_dir / "annotations.jsonl"
    records = list(read_jsonl(ann_path))
    if not records:
        print(f"no annotations in {set_dir}", file=sys.stderr)
        return 1

    n_obj = 0
    missing = 0
    for rec in records:
        for o in rec["objects"]:
            if not o.get("mask"):
                o["mask_area_px"] = 0
                missing += 1
                continue
            mask_path = set_dir / o["mask"]
            if not mask_path.exists():
                o["mask_area_px"] = 0
                missing += 1
                continue
            arr = np.asarray(Image.open(mask_path).convert("L"))
            o["mask_area_px"] = int((arr > 127).sum())
            n_obj += 1

    write_jsonl(records, ann_path)
    print(f"backfilled mask_area_px for {n_obj} objects in {len(records)} images -> {ann_path}")
    if missing:
        print(f"warning: {missing} objects had no readable mask", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
