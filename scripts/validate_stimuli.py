"""Validate a rendered stimulus set. Prints a summary; exits non-zero on any violation.

Usage:
    uv run --extra analysis scripts/validate_stimuli.py --set $DATA_ROOT/stimuli/v0_congruent

Checks (M1 acceptance):
  geometry      projected object centre must land inside its rendered bbox
  bbox-bottom   the object with the NEARER SURFACE must have the lower bbox bottom.
                (The naive version of this rule compared against centre depth, which is
                wrong: the bbox bottom tracks the front-bottom extremity, i.e. the
                nearest surface. Shapes differ in half-extent along the viewing axis,
                so centre-order and surface-order can disagree — hence nearest_surface_m.)
  ordinal       centre-based and surface-based ordinals must agree (sampler constraint)
  ratio         dist_ratio must equal far/near centre depth
  retinal       retinal-size distribution (reported; band is advisory, not a hard fail)
  pairs         the two objects are never identical in both category and colour
  balance       the closer-object answer key is ~50/50 (no degenerate prior to exploit)
  masks         every object has a non-empty mask
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from sbind.stimuli import geometry
from sbind.utils.io import read_jsonl


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a rendered stimulus set.")
    ap.add_argument("--set", required=True, help="path to the stimulus set dir")
    ap.add_argument("--retinal-lo", type=float, default=60.0)
    ap.add_argument("--retinal-hi", type=float, default=120.0)
    args = ap.parse_args()

    set_dir = Path(args.set)
    anns = list(read_jsonl(set_dir / "annotations.jsonl"))
    if not anns:
        print(f"no annotations in {set_dir}", file=sys.stderr)
        return 1

    n = len(anns)
    fails: dict[str, int] = Counter()

    # Pre-pass: recover each category's calibrated base size (size_m / size_multiplier).
    # If the pair-shared-multiplier rule holds, this is a single constant per category.
    base_samples: dict[str, list[float]] = {}
    for ann in anns:
        mult = ann["factors"].get("size_multiplier")
        if mult is None:
            continue
        for o in ann["objects"]:
            base_samples.setdefault(o["category"], []).append(o["size_m"] / mult)
    cat_base = {c: float(np.median(v)) for c, v in base_samples.items()}

    retinal: list[float] = []
    ratios: list[float] = []
    closer_key: Counter = Counter()
    surface_key: Counter = Counter()
    near_depths: set[float] = set()
    n_objects = 0

    for ann in anns:
        K = np.array(ann["camera"]["K"])
        R = np.array(ann["camera"]["R"])
        t = np.array(ann["camera"]["t"])
        objs = ann["objects"]

        for o in objs:
            n_objects += 1
            if o.get("mask") is None or o["retinal_size_px"] <= 0:
                fails["masks"] += 1
                continue
            u, v, d = geometry.project(K, R, t, o["pos_world"])
            x0, y0, x1, y1 = o["bbox_px"]
            if not (x0 <= u <= x1 and y0 <= v <= y1):
                fails["geometry"] += 1
            # nearest surface must be nearer than the centre, and positive
            if not (0 < o["nearest_surface_m"] < o["depth_m"]):
                fails["surface_sanity"] += 1
            retinal.append(o["retinal_size_px"])

        if len(objs) != 2:
            continue
        d0, d1 = objs[0]["depth_m"], objs[1]["depth_m"]
        s0, s1 = objs[0]["nearest_surface_m"], objs[1]["nearest_surface_m"]
        rel = ann["pair_relations"]["(0,1)"]

        # corrected bbox-bottom rule: nearer SURFACE => lower bbox bottom (larger y1)
        near_by_surface = 0 if s0 < s1 else 1
        far_by_surface = 1 - near_by_surface
        if objs[near_by_surface]["bbox_px"][3] <= objs[far_by_surface]["bbox_px"][3]:
            fails["bbox_bottom"] += 1

        # centre-ordinal and surface-ordinal must agree
        if rel["ordinal_depth"] != rel["ordinal_depth_surface"]:
            fails["ordinal_disagree"] += 1
        expected_centre = f"{0 if d0 < d1 else 1}_closer"
        if rel["ordinal_depth"] != expected_centre:
            fails["ordinal_label"] += 1

        # ratio consistency
        expected_ratio = max(d0, d1) / min(d0, d1)
        if abs(rel["dist_ratio"] - expected_ratio) > 1e-6:
            fails["ratio"] += 1
        ratios.append(expected_ratio)

        # pair distinguishability
        if objs[0]["category"] == objs[1]["category"] and objs[0]["name"] == objs[1]["name"]:
            fails["identical_pair"] += 1

        # CUE CONGRUENCE: in a congruent set the nearer object MUST look bigger by EVERY
        # measured apparent-size cue. Height is made structural by the per-category size
        # calibration; area is made structural by the sampler's min_depth_ratio (the
        # calibration equalises height, not area). Any violation of either is a
        # construction bug, not an edge case.
        near_c = 0 if d0 < d1 else 1
        far_c = 1 - near_c
        if objs[near_c]["retinal_size_px"] <= objs[far_c]["retinal_size_px"]:
            fails["retinal_congruence"] += 1
        if objs[near_c]["mask_area_px"] <= objs[far_c]["mask_area_px"]:
            fails["area_congruence"] += 1

        # the pair must share ONE physical-size multiplier (no independent size jitter):
        # each object's size_m must equal its category base times the image's multiplier
        mult = ann["factors"].get("size_multiplier")
        if mult is not None and cat_base:
            for o in objs:
                expected = cat_base[o["category"]] * mult
                if not np.isclose(o["size_m"], expected, rtol=1e-6):
                    fails["size_multiplier_shared"] += 1
                    break

        closer_key[rel["ordinal_depth"]] += 1
        surface_key[rel["ordinal_depth_surface"]] += 1
        near_depths.add(round(min(d0, d1), 6))

    retinal_arr = np.array(retinal)
    ratio_arr = np.array(ratios)
    in_band = ((retinal_arr >= args.retinal_lo) & (retinal_arr <= args.retinal_hi)).mean() * 100

    print(f"set: {set_dir}  images={n}  objects={n_objects}")
    print("--- hard checks (must be 0) ---")
    for key in (
        "geometry",
        "bbox_bottom",
        "retinal_congruence",
        "area_congruence",
        "ordinal_disagree",
        "ordinal_label",
        "ratio",
        "identical_pair",
        "size_multiplier_shared",
        "masks",
        "surface_sanity",
    ):
        status = "OK " if fails[key] == 0 else "FAIL"
        denom = n_objects if key in ("geometry", "masks", "surface_sanity") else n
        print(f"  [{status}] {key:22s} {fails[key]}/{denom}")
    if cat_base:
        print(f"  calibrated base size_m: {({c: round(v, 4) for c, v in cat_base.items()})}")

    print("--- distributions ---")
    print(
        f"  retinal px: median={np.median(retinal_arr):.1f} "
        f"p10={np.percentile(retinal_arr, 10):.1f} p90={np.percentile(retinal_arr, 90):.1f} "
        f"| {in_band:.0f}% in [{args.retinal_lo:.0f},{args.retinal_hi:.0f}]"
    )
    print(
        f"  depth ratio: median={np.median(ratio_arr):.2f} "
        f"range=[{ratio_arr.min():.2f},{ratio_arr.max():.2f}]"
    )
    print(f"  depth continuity: {len(near_depths)}/{n} unique near depths")
    print(f"  answer balance (centre):  {dict(closer_key)}")
    print(f"  answer balance (surface): {dict(surface_key)}")

    total_fail = sum(fails.values())
    print(f"\n{'ALL CHECKS GREEN' if total_fail == 0 else f'{total_fail} VIOLATIONS'}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
