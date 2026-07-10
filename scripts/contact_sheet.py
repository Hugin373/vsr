"""Contact-sheet sanity PDF for a rendered stimulus set.

Usage:
    uv run --extra analysis scripts/contact_sheet.py \
        --set $DATA_ROOT/stimuli/v0_congruent --n 48 --out contact_sheet.pdf

Tiles a sample of rendered images with their depth/ordinal annotations overlaid, so a
human can eyeball that geometry and rendering agree (nearer object lower + larger).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from sbind.utils.io import read_jsonl  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Contact-sheet PDF for a rendered set.")
    ap.add_argument("--set", required=True, help="path to the stimulus set dir")
    ap.add_argument("--n", type=int, default=48, help="number of images to tile")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument(
        "--out", default=None, help="output PDF path (default: <set>/contact_sheet.pdf)"
    )
    args = ap.parse_args()

    set_dir = Path(args.set)
    anns = list(read_jsonl(set_dir / "annotations.jsonl"))
    if not anns:
        print(f"no annotations in {set_dir}", file=sys.stderr)
        return 1
    anns = anns[: args.n]

    cols = args.cols
    rows = (len(anns) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.4, rows * 2.4))
    axes = axes.reshape(-1) if hasattr(axes, "reshape") else [axes]

    for ax in axes:
        ax.axis("off")

    for ax, ann in zip(axes, anns, strict=False):
        img_path = set_dir / ann["image"]
        if img_path.exists():
            ax.imshow(plt.imread(img_path))
        depths = [round(o["depth_m"], 2) for o in ann["objects"]]
        rel = next(iter(ann.get("pair_relations", {}).values()), {})
        ordinal = rel.get("ordinal_depth", "?")
        ax.set_title(f"{ann['id'].split('_')[-1]}  d={depths}\n{ordinal}", fontsize=6)

    out = Path(args.out) if args.out else set_dir / "contact_sheet.pdf"
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"wrote {out} ({len(anns)} images)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
