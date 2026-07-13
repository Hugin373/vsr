"""Re-derive the apparent-size cue constants from a RENDERED set, worst-case not mean.

    uv run --extra analysis scripts/derive_cue_constants.py --set $DATA_ROOT/stimuli/v0_congruent

Why this exists (CLAUDE.md rule 7): the constants in `configs/stimuli_v0_congruent.yaml` are
consumed by M4's CONFLICT designs, which must invert a cue *on purpose by a known amount*. A
constant recorded as a MEAN cannot support that, and one was:

    height_constant: {cube: 409.3, cylinder: 410.3, sphere: 405.3}   # means
    height_ratio_threshold: 1.016                                    # derived from the means

Measured per near/far ROLE from the rendered images, the cube/cylinder height constant swings
~±10% with image position (under a tilted camera a cube's silhouette HEIGHT grows as it moves
low/near in frame — its top face comes into view), while a sphere's swings ~±1.5%. So the true
worst-case required depth ratio for height congruence is ~1.088, not 1.016 — 5x larger in
excess-over-1. The set is safe only because the AREA floor (~1.156) dominates and
min_depth_ratio is 1.18.

The requirement, per cue, is the depth ratio at which the far object stops looking smaller:

    height:  ratio > max(C_h[far]) / min(C_h[near])       [C_h = height_px * depth]
    area:    ratio > sqrt(max(C_a[far]) / min(C_a[near])) [C_a = area_px * depth^2]

Extremes, split by role — never means.
"""

from __future__ import annotations

import argparse
import sys
from itertools import product
from pathlib import Path

import numpy as np

from sbind.utils.io import read_jsonl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--set", required=True, help="path to a rendered stimulus set dir")
    args = ap.parse_args()

    anns = list(read_jsonl(Path(args.set) / "annotations.jsonl"))
    if not anns:
        print(f"no annotations in {args.set}", file=sys.stderr)
        return 1

    # C_h = retinal_height * depth ; C_a = mask_area * depth^2, with the size multiplier
    # divided out so the constant is a property of the SHAPE, not of the image's scale factor.
    h: dict[tuple[str, str], list[float]] = {}
    a: dict[tuple[str, str], list[float]] = {}
    for ann in anns:
        mult = float(ann["factors"]["size_multiplier"])
        objs = ann["objects"]
        depths = [o["depth_m"] for o in objs]
        near_i = int(np.argmin(depths))
        for i, o in enumerate(objs):
            role = "near" if i == near_i else "far"
            key = (o["category"], role)
            h.setdefault(key, []).append(o["retinal_size_px"] * o["depth_m"] / mult)
            a.setdefault(key, []).append(o["mask_area_px"] * o["depth_m"] ** 2 / mult**2)

    cats = sorted({c for c, _ in h})
    print(f"set: {args.set}  images={len(anns)}\n")

    for name, const in (("height  C_h = px*depth", h), ("area    C_a = px*depth^2", a)):
        print(f"--- {name} (min .. max per role; MEANS ARE NOT SAFE TO USE) ---")
        for c in cats:
            for role in ("near", "far"):
                v = np.array(const[(c, role)])
                print(
                    f"  {c:9s} as {role:4s}: min={v.min():10.1f}  max={v.max():10.1f}  "
                    f"mean={v.mean():10.1f}  spread={100 * (v.max() / v.min() - 1):5.1f}%"
                )
        print()

    # Worst-case required far/near depth ratio, per (near_cat, far_cat) pairing.
    print("--- required min far/near depth ratio, per pairing (WORST case, not mean) ---")
    print(f"  {'near':9s} {'far':9s} {'height':>8s} {'area':>8s}")
    worst_h = worst_a = 0.0
    for nc, fc in product(cats, cats):
        req_h = max(h[(fc, "far")]) / min(h[(nc, "near")])
        req_a = float(np.sqrt(max(a[(fc, "far")]) / min(a[(nc, "near")])))
        worst_h = max(worst_h, req_h)
        worst_a = max(worst_a, req_a)
        print(f"  {nc:9s} {fc:9s} {req_h:8.4f} {req_a:8.4f}")

    required = max(worst_h, worst_a)
    print(f"\n  WORST-CASE height requirement : {worst_h:.4f}")
    print(f"  WORST-CASE area   requirement : {worst_a:.4f}")
    print(f"  => min_depth_ratio must exceed : {required:.4f}")

    # What did the set actually sample? (margin, not pass/fail)
    ratios = np.array(
        [max(o["depth_m"] for o in x["objects"]) / min(o["depth_m"] for o in x["objects"])
         for x in anns]
    )
    print(f"  min depth ratio SAMPLED        : {ratios.min():.4f}")
    headroom = 100 * (ratios.min() / required - 1)
    print(f"  headroom                       : {headroom:+.2f}%")
    if ratios.min() <= required:
        print("\n  *** THE SET VIOLATES ITS OWN CONSTRUCTION GUARANTEE — raise min_depth_ratio")
        return 1
    print("\n  OK — congruence is structural, with margin (paste these into cue_constants)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
