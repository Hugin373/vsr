"""The DUMB-FEATURES CEILING: what a probe gets with NO model at all. [CPU]

    uv run --extra analysis scripts/leak_ceiling.py --set $DATA_ROOT/stimuli/v0_congruent

Standing methodology (CLAUDE.md rule 12, IMPLEMENTATION_PLAN M5). A shuffled-label control
catches a probe fitting *noise*; it cannot catch a probe reading a trivially available
**non-representational** feature. **Decodability only counts ABOVE this ceiling.**

Two findings that passed every shuffled-label control and died only here:
  * mask GEOMETRY alone predicts lateral position at R2 = 0.942 and depth at R2 = 0.972 on the
    v0 set — the model's activations added ~0.05. Mask-pooling *selects its tokens by the
    object's image position*, so the selection IS the answer;
  * a shape-only constant strategy scored 55.1% on "which is closer" before category was
    balanced against the near/far depth role.

Why this matters beyond bookkeeping: mask-pooled VISUAL-token probes inherit the position leak,
bound-TEXT-token probes do not. So the four-site grid's central contrast (visual high, text low)
could be manufactured by the measurement itself — which is exactly the contrast that separates
"metric survives in visual tokens and dies at binding" from "metric was never there".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.probes.ridge import logistic_probe, ridge_probe
from sbind.utils.io import read_jsonl, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.leak")

# Everything a probe could read WITHOUT the model having represented anything.
GEOM_NAMES = [
    "centroid_u",  # where the mask sits horizontally  <- this alone nearly solves x
    "centroid_v",  # ...and vertically                 <- with size, nearly solves z
    "mask_area_px",
    "bbox_w",
    "bbox_h",
    "retinal_size_px",
    "elevation_px",
]


def dumb_features(anns: list[dict]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    G, x, z, shape, color = [], [], [], [], []
    for a in anns:
        for o in a["objects"]:
            x0, y0, x1, y1 = o["bbox_px"]
            G.append(
                [
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    o["mask_area_px"],
                    x1 - x0,
                    y1 - y0,
                    o["retinal_size_px"],
                    o["elevation_px"],
                ]
            )
            x.append(o["pos_cam"][0])
            z.append(o["depth_m"])
            shape.append(o["category"])
            color.append(o["name"].split("_")[0])
    return np.asarray(G, dtype=float), {
        "x_lateral": np.asarray(x),
        "z_depth": np.asarray(z),
        "shape": np.asarray(shape),
        "color": np.asarray(color),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Dumb-features (leak) ceiling for a stimulus set.")
    ap.add_argument("--set", required=True, help="path to a rendered stimulus set dir")
    ap.add_argument(
        "--out", help="write the ceiling JSON (for M5's Delta = probe - ceiling)"
    )
    args = ap.parse_args()

    anns = list(read_jsonl(Path(args.set) / "annotations.jsonl"))
    if not anns:
        print(f"no annotations in {args.set}", file=sys.stderr)
        return 1
    G, targets = dumb_features(anns)
    print(f"set: {args.set}  objects={len(G)}  dumb features={GEOM_NAMES}\n")

    ceiling: dict[str, float] = {}
    print("--- CEILING: what mask geometry ALONE gives you (no activations, no model) ---")
    for name, y in targets.items():
        if name in ("shape", "color"):
            r = logistic_probe(G, y, name)
            print(f"  {name:10s} acc = {r.value:.4f}   (shuffled ctrl {r.control:.3f})")
        else:
            r = ridge_probe(G, y.astype(float), name)
            print(f"  {name:10s} R2  = {r.value:+.4f}   (shuffled ctrl {r.control:+.3f})")
        ceiling[name] = r.value

    print("\n--- the single most damning slices ---")
    u = ridge_probe(G[:, [0]], targets["x_lateral"].astype(float), "x", seeds=(0, 1, 2))
    print(f"  x from the mask centroid u ALONE (one number):        R2 = {u.value:+.4f}")
    ev = ridge_probe(G[:, [1, 5]], targets["z_depth"].astype(float), "z", seeds=(0, 1, 2))
    print(f"  z from (elevation v, retinal height) ALONE:           R2 = {ev.value:+.4f}")

    print(
        "\nAny probe on model activations must EXCEED these numbers to be evidence that the "
        "quantity is in the REPRESENTATION rather than in the mask."
    )
    if args.out:
        write_json(ceiling, Path(args.out))
        log.info("wrote ceiling -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
