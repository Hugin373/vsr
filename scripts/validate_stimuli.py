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

ARTEFACT checks (added at M3's retro-audit — this script used to validate the JSON against
ITSELF and never opened a single PNG, so it would have reported ALL GREEN with a missing,
truncated or overwritten image):
  files         every image and mask referenced actually exists on disk
  ids           ids are unique, and no two images are byte-identical (a colliding id silently
                OVERWRITES an image — this is the exact bug that hit M2)
  mask_matches  bbox_px / retinal_size_px / mask_area_px RECOMPUTED from the mask PNG must
                equal the stored annotation (catches a stale or mismatched mask)
  clipping      no mask may touch the image border (a clipped object corrupts retinal_size_px
                and mask_area_px — i.e. the very quantities the congruence checks read)
  occlusion     the two target masks may not overlap, and target visible masks must
                match amodal masks. Distractor occlusion is reported but is allowed:
                distractors are nuisance clutter, not the measured target pair.
  semantics     category/colour must NOT predict the near/far depth role, and the best
                shape-only constant strategy must not beat chance (a probe could otherwise
                read depth off object IDENTITY)

MARGINS, not just pass/fail (CLAUDE.md rule 6): a check that passes tells you nothing about
whether it survives a different seed. Every congruence check also reports its worst case.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from sbind.stimuli import geometry
from sbind.utils.io import read_jsonl


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a rendered stimulus set.")
    ap.add_argument("--set", required=True, help="path to the stimulus set dir")
    ap.add_argument("--retinal-lo", type=float, default=60.0)
    ap.add_argument("--retinal-hi", type=float, default=120.0)
    ap.add_argument("--max-shape-prior-acc", type=float, default=0.53)
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

    # --- margins (rule 6): how close did each "structural" property come to breaking? ---
    margins: dict[str, float] = {
        "retinal_congruence": np.inf,  # near_height / far_height, must stay > 1
        "area_congruence": np.inf,  # near_area   / far_area,   must stay > 1
        "depth_ratio": np.inf,  # far_depth   / near_depth
        "bbox_bottom": np.inf,  # near_bottom - far_bottom (px), must stay > 0
    }
    # --- artefact-level integrity (this script never used to open a single file) ---
    ids: Counter = Counter()
    img_hashes: dict[str, list[str]] = {}
    role_cat: Counter = Counter()  # (role, category)
    role_col: Counter = Counter()  # (role, colour)
    shape_wins: Counter = Counter()
    n_mixed = 0

    for ann in anns:
        ids[ann["id"]] += 1
        img_path = set_dir / ann["image"]
        if not img_path.exists():
            fails["files_missing"] += 1
        else:
            h = hashlib.sha256(img_path.read_bytes()).hexdigest()
            img_hashes.setdefault(h, []).append(ann["id"])

    # a colliding id silently OVERWRITES an image: two ids, one picture (M2's 1541 -> 949 bug)
    fails["ids_duplicate"] = sum(v - 1 for v in ids.values() if v > 1)
    fails["images_identical"] = sum(len(v) - 1 for v in img_hashes.values() if len(v) > 1)

    for ann in anns:
        K = np.array(ann["camera"]["K"])
        R = np.array(ann["camera"]["R"])
        t = np.array(ann["camera"]["t"])
        objs = ann["objects"]

        mask_bools: list[np.ndarray] = []
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

            # --- OPEN THE MASK. The stored geometry must match the actual pixels. ---
            mpath = set_dir / o["mask"]
            if not mpath.exists():
                fails["files_missing"] += 1
                continue
            m = np.array(Image.open(mpath).convert("L")) > 127
            mask_bools.append(m)
            if not m.any():
                fails["masks"] += 1
                continue
            ys, xs = np.nonzero(m)
            bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
            # recomputed vs stored — a stale/overwritten mask is invisible to a JSON-only check.
            # NB bbox_px stores x1/y1 EXCLUSIVE (max + 1), matching retinal_size_px = y1 - y0.
            if [bx0, by0, bx1 + 1, by1 + 1] != [int(round(c)) for c in o["bbox_px"]]:
                fails["mask_bbox_mismatch"] += 1
            if abs((by1 - by0 + 1) - o["retinal_size_px"]) > 1e-6:
                fails["mask_height_mismatch"] += 1
            if abs(int(m.sum()) - o["mask_area_px"]) > 0:
                fails["mask_area_mismatch"] += 1

            # M4a/M4.5 prerequisite: every object has a SOLO-ID amodal mask. Target
            # visible masks must match amodal masks in M4a; distractors may be partly
            # hidden because they are nuisance clutter rather than measured objects.
            amodal_rel = o.get("mask_amodal")
            if not amodal_rel:
                fails["amodal_missing"] += 1
            else:
                apath = set_dir / amodal_rel
                if not apath.exists():
                    fails["files_missing"] += 1
                else:
                    am = np.array(Image.open(apath).convert("L")) > 127
                    if not am.any():
                        fails["amodal_empty"] += 1
                    else:
                        ays, axs = np.nonzero(am)
                        abx0, abx1 = int(axs.min()), int(axs.max())
                        aby0, aby1 = int(ays.min()), int(ays.max())
                        stored_abox = o.get("bbox_px_amodal") or []
                        if [abx0, aby0, abx1 + 1, aby1 + 1] != [int(round(c)) for c in stored_abox]:
                            fails["amodal_bbox_mismatch"] += 1
                        if abs((aby1 - aby0 + 1) - o.get("retinal_size_px_amodal", 0.0)) > 1e-6:
                            fails["amodal_height_mismatch"] += 1
                        if abs(int(am.sum()) - o.get("mask_area_px_amodal", 0)) > 0:
                            fails["amodal_area_mismatch"] += 1
                        if (m & ~am).any():
                            fails["amodal_not_superset"] += 1
                        expected_occ = max(0.0, 1.0 - int(m.sum()) / max(int(am.sum()), 1))
                        if abs(expected_occ - o.get("occlusion_ratio", 0.0)) > 1e-9:
                            fails["occlusion_ratio_mismatch"] += 1
                        if o.get("occlusion_ratio", 0.0) > 1e-6:
                            if len(mask_bools) <= 2:
                                fails["target_occlusion_ratio_nonzero"] += 1
                            else:
                                fails["distractor_occlusion_ratio_nonzero"] += 1
            # a clipped object's apparent size is a lie — and apparent size is what we measure
            if by0 == 0 or bx0 == 0 or by1 == m.shape[0] - 1 or bx1 == m.shape[1] - 1:
                fails["mask_clipped"] += 1

        # target occlusion corrupts the apparent-size quantities we measure.
        if len(mask_bools) >= 2 and (mask_bools[0] & mask_bools[1]).any():
            fails["mask_overlap"] += 1

        if len(objs) < 2:
            continue
        # The first two objects are the target pair; later objects are distractors.
        objs = objs[:2]
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

        # CUE CONGRUENCE: only a natural-congruent set claims the nearer target must
        # look bigger by every apparent-size cue. Counterbalanced/conflict regimes are
        # supposed to decorrelate or invert these cues, so validating them with the v0
        # congruence rule would be a false alarm. Artifact checks above still apply.
        near_c = 0 if d0 < d1 else 1
        far_c = 1 - near_c
        regime = ann.get("factors", {}).get("regime", "natural_congruent")
        size_condition = ann.get("factors", {}).get("size_condition", "congruent")
        check_size_congruence = regime == "natural_congruent" and size_condition == "congruent"
        if (
            check_size_congruence
            and objs[near_c]["retinal_size_px"] <= objs[far_c]["retinal_size_px"]
        ):
            fails["retinal_congruence"] += 1
        if check_size_congruence and objs[near_c]["mask_area_px"] <= objs[far_c]["mask_area_px"]:
            fails["area_congruence"] += 1

        # MARGINS (rule 6): 0 violations proves nothing about the next seed. Record how close
        # each structural property came to breaking. Area-congruence twice reported 0/500 while
        # the true worst-case margin was 0.6% — it was passing by luck, not by construction.
        margins["retinal_congruence"] = min(
            margins["retinal_congruence"],
            objs[near_c]["retinal_size_px"] / max(objs[far_c]["retinal_size_px"], 1e-9),
        )
        margins["area_congruence"] = min(
            margins["area_congruence"],
            objs[near_c]["mask_area_px"] / max(objs[far_c]["mask_area_px"], 1e-9),
        )
        margins["depth_ratio"] = min(margins["depth_ratio"], max(d0, d1) / min(d0, d1))
        margins["bbox_bottom"] = min(
            margins["bbox_bottom"],
            objs[near_by_surface]["bbox_px"][3] - objs[far_by_surface]["bbox_px"][3],
        )

        # SEMANTICS MUST NOT PREDICT DEPTH ROLE. If category correlates with near/far, a probe
        # can read depth off object IDENTITY and a language-only model gets free accuracy on
        # "which is closer?" — in the very set built to decorrelate semantics from geometry.
        role_cat[("near", objs[near_c]["category"])] += 1
        role_cat[("far", objs[far_c]["category"])] += 1
        role_col[("near", objs[near_c]["name"])] += 1
        role_col[("far", objs[far_c]["name"])] += 1
        if objs[near_c]["category"] != objs[far_c]["category"]:
            n_mixed += 1
            pair = frozenset((objs[near_c]["category"], objs[far_c]["category"]))
            shape_wins[(pair, objs[near_c]["category"])] += 1

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
    per_object = {
        "geometry",
        "masks",
        "surface_sanity",
        "mask_bbox_mismatch",
        "mask_height_mismatch",
        "mask_area_mismatch",
        "mask_clipped",
        "files_missing",
        "amodal_missing",
        "amodal_empty",
        "amodal_bbox_mismatch",
        "amodal_height_mismatch",
        "amodal_area_mismatch",
        "amodal_not_superset",
        "occlusion_ratio_mismatch",
        "target_occlusion_ratio_nonzero",
    }
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
        # artefact-level: this script used to never open a file
        "files_missing",
        "ids_duplicate",
        "images_identical",
        "mask_bbox_mismatch",
        "mask_height_mismatch",
        "mask_area_mismatch",
        "mask_clipped",
        "mask_overlap",
        "amodal_missing",
        "amodal_empty",
        "amodal_bbox_mismatch",
        "amodal_height_mismatch",
        "amodal_area_mismatch",
        "amodal_not_superset",
        "occlusion_ratio_mismatch",
        "target_occlusion_ratio_nonzero",
    ):
        status = "OK " if fails[key] == 0 else "FAIL"
        denom = n_objects if key in per_object else n
        print(f"  [{status}] {key:22s} {fails[key]}/{denom}")
    if cat_base:
        print(f"  calibrated base size_m: { ({c: round(v, 4) for c, v in cat_base.items()}) }")

    # --- MARGINS: how close did each structural property come to breaking? ---
    print("--- margins (rule 6: measure the margin, not the pass/fail) ---")
    regimes = {ann.get("factors", {}).get("regime", "natural_congruent") for ann in anns}
    size_note = "(>1 required only for natural_congruent/congruent)"
    if regimes == {"natural_congruent"}:
        size_note = "(>1)"
    print(
        f"  worst near/far retinal-height ratio : "
        f"{margins['retinal_congruence']:.4f}  {size_note}"
    )
    print(
        f"  worst near/far mask-area ratio      : "
        f"{margins['area_congruence']:.4f}  {size_note}"
    )
    print(f"  min far/near depth ratio            : {margins['depth_ratio']:.4f}")
    print(f"  min bbox-bottom gap (px)            : {margins['bbox_bottom']:.1f}  (>0)")

    # --- SEMANTIC PRIOR: category/colour must not predict the depth role ---
    print("--- semantic prior (must be ~chance: a probe could read depth off identity) ---")
    cats = sorted({c for _, c in role_cat})
    print(f"  near-role category: { ({c: role_cat[('near', c)] for c in cats}) }")
    print(f"  far-role  category: { ({c: role_cat[('far', c)] for c in cats}) }")
    best = 0
    for pair in {p for p, _ in shape_wins}:
        best += max(shape_wins.get((pair, c), 0) for c in pair)
    if n_mixed:
        acc = 100 * best / n_mixed
        # Sampled/statistical quantity: gate on uncertainty, not the noisiest draw.
        # Wilson 95% CI for the strategy's success rate; fail only if the lower bound
        # clears the tolerated prior by itself. Tiny smoke renders are still reported.
        p = best / n_mixed
        z = 1.96
        denom = 1.0 + z * z / n_mixed
        centre = (p + z * z / (2 * n_mixed)) / denom
        half = z * math.sqrt((p * (1.0 - p) / n_mixed) + (z * z / (4 * n_mixed * n_mixed))) / denom
        lo = max(0.0, centre - half)
        hi = min(1.0, centre + half)
        if n_mixed < 30:
            print(
                f"  [INFO] best shape-only constant strategy: "
                f"{best}/{n_mixed} = {acc:.1f}%  "
                f"(95% CI [{100 * lo:.1f},{100 * hi:.1f}], too few mixed pairs to gate)"
            )
        else:
            ok = lo <= args.max_shape_prior_acc
            fails["semantic_prior"] = 0 if ok else 1
            print(
                f"  [{'OK ' if ok else 'FAIL'}] best shape-only constant strategy: "
                f"{best}/{n_mixed} = {acc:.1f}%  "
                f"(95% CI [{100 * lo:.1f},{100 * hi:.1f}], "
                f"fail if lower > {100 * args.max_shape_prior_acc:.1f}%)"
            )

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
    if fails["distractor_occlusion_ratio_nonzero"]:
        print(
            "  distractor occlusion: "
            f"{fails['distractor_occlusion_ratio_nonzero']}/{n_objects} objects "
            "(reported, not a hard failure)"
        )

    informational = {"distractor_occlusion_ratio_nonzero"}
    total_fail = sum(v for k, v in fails.items() if k not in informational)
    print(f"\n{'ALL CHECKS GREEN' if total_fail == 0 else f'{total_fail} VIOLATIONS'}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
