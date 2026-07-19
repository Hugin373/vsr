"""Decision table for the natural-congruent congruence-vs-ratio conflict (advisor item 1).

    uv run --extra analysis scripts/natural_congruent_options.py \
        --constants reports/m4a_cue_constants/natural_congruent.json \
        --config configs/m4a_v1_natural_congruent_pilot.yaml --n 1200 \
        --json reports/m4a_natural_congruent_options.json

The problem (measured, `reports/m4a_cue_constants.md` §4): area congruence over the full
six-category set requires a far/near depth ratio of 1.7661 worst case, while the design produces
at most ~1.474. So every image is clamped to the floor and the ratio target becomes an
independent uniform draw — which is what oracle R2 = -0.252 was.

The ruled default is RESTRICTED CATEGORY PAIRINGS: keep hard area congruence, use the per-pair
derived requirements, and drop the pairings that cannot be satisfied. This script supplies the
numbers that ruling has to be confirmed against.

⚠ TWO CONSTRAINTS THAT ARE EASY TO MISS, both enforced here:

1. **A retained pairing set must be SYMMETRIC.** The `cat_pair` balancing is what gives each
   category an exact 0.500 near/far split, and that split is what closes B2->z (identity priors
   predicting depth). Retaining (bottle, cube) but not (cube, bottle) makes bottle preferentially
   NEAR, which reintroduces the confound the balancing exists to kill. So candidate sets are built
   from a category SUBSET C and retain C x C.
2. **A per-pair floor makes shape predict the ratio distribution** — v0 rejected exactly this, and
   the objection still stands. The safeguard is measured, not argued: the overlap of the
   category-conditioned ratio distributions, plus eta^2 (the fraction of ratio variance explained
   by the pairing). A uniform floor over the retained set has zero coupling by construction; a
   per-pair floor buys range and must pay for it in coupling.
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config

# Below this the ratio target has too little spread to be a regression target at all: the passing
# regimes demonstrate 1.29-1.32x retained dynamic range per pairing, and natural-congruent's
# floor-clamped 1.07x is the failure being fixed.
USABLE_DYNAMIC_RANGE = 1.20


def _available_ratios(config: dict, n: int) -> list[dict]:
    """Ratios the design produces with the floor made non-binding, per (near, far) pairing."""
    cfg = copy.deepcopy(config)
    cfg["n_images"] = n
    cfg.setdefault("constraints", {})["min_depth_ratio"] = 1.000001
    from sbind.stimuli import geometry

    rows = []
    for spec in build_scene_specs(cfg, int(cfg["seed"]), raise_on_placement_failure=False):
        _, R, t, _ = geometry.camera_frame(
            spec.camera.pos_world,
            spec.camera.target_world,
            spec.camera.f_mm,
            spec.camera.sensor_width_mm,
            spec.camera.res_x,
            spec.camera.res_y,
        )
        depths = [
            float((R @ np.asarray(o.pos_world, dtype=float) + t)[2]) for o in spec.objects[:2]
        ]
        near_i = int(spec.factors["closer_object"])
        rows.append(
            {
                "near_category": spec.factors["near_category"],
                "far_category": spec.factors["far_category"],
                "depth_near": depths[near_i],
                "depth_far": depths[1 - near_i],
                "ratio": depths[1 - near_i] / depths[near_i],
            }
        )
    return rows


def _overlap(a: np.ndarray, b: np.ndarray, bins: np.ndarray) -> float:
    """Histogram overlap coefficient of two distributions on a shared grid (1.0 = identical)."""
    ha, _ = np.histogram(a, bins=bins, density=True)
    hb, _ = np.histogram(b, bins=bins, density=True)
    width = np.diff(bins)
    return float(np.minimum(ha, hb) @ width)


def _coupling(rows: list[dict], floors: dict[str, float]) -> dict:
    """Does the PAIRING predict the ratio? eta^2 plus the worst pairwise distribution overlap.

    Simulates the accepted distribution under the given per-pairing floors by clamping each
    available ratio up to its pairing's floor — the same operation the sampler performs.
    """
    by_pair: dict[str, list[float]] = {}
    for r in rows:
        key = f"near_{r['near_category']}_far_{r['far_category']}"
        if key not in floors:
            continue
        by_pair.setdefault(key, []).append(max(r["ratio"], floors[key]))
    if len(by_pair) < 2:
        return {}
    groups = {k: np.asarray(v) for k, v in by_pair.items() if len(v) >= 5}
    allv = np.concatenate(list(groups.values()))
    grand = allv.mean()
    ss_between = sum(g.size * (g.mean() - grand) ** 2 for g in groups.values())
    ss_total = float(((allv - grand) ** 2).sum())
    eta2 = float(ss_between / ss_total) if ss_total > 0 else float("nan")

    bins = np.linspace(allv.min(), allv.max(), 40)
    overlaps = [
        _overlap(groups[a], groups[b], bins) for a, b in itertools.combinations(sorted(groups), 2)
    ]
    return {
        "eta2_pairing_explains_ratio": eta2,
        "min_pairwise_overlap": float(np.min(overlaps)),
        "median_pairwise_overlap": float(np.median(overlaps)),
        "n_pairings": len(groups),
    }


def _six_category_control(
    rows: list[dict], required: dict[str, float], margin: float, avail_max: float
) -> dict:
    """Can natural-congruent keep all six categories if only four are analysis-ELIGIBLE?

    The tempting arrangement: generate six categories, apply each pairing's own derived floor, and
    restrict only the ANALYSIS to the feasible four. This measures what that actually produces.

    The failure mode it is testing for: a pairing whose floor exceeds the available maximum is
    clamped for EVERY image, so its ratios collapse into a band around its own floor, disjoint from
    the band of the feasible pairings. Ratio then reveals the pairing deterministically, and the
    depth pushed into the far object is a function of the category pair — which is the category
    <-> depth coupling the whole battery is built to eliminate.
    """
    floors = {k: max(required[k] * margin, 1.1707) for k in required}
    eligible = {"cube", "cylinder", "mug", "sphere"}

    realized: dict[str, np.ndarray] = {}
    far_depth_proxy: dict[str, list[float]] = {}
    for r in rows:
        key = f"near_{r['near_category']}_far_{r['far_category']}"
        if key not in floors:
            continue
        realized.setdefault(key, [])
        realized[key].append(max(r["ratio"], floors[key]))
        far_depth_proxy.setdefault(r["far_category"], []).append(max(r["ratio"], floors[key]))
    realized = {k: np.asarray(v) for k, v in realized.items()}

    clamped_always = [k for k in realized if floors[k] >= avail_max]

    # ⚠ TWO DIFFERENT SPLITS, and only the second separates. Reporting the first alone would
    # understate the confound; reporting only the second would overstate which pairings are
    # affected. Both are printed.
    #   eligible/ineligible — the 16 analysis-eligible pairings vs the other 20. This does NOT
    #     separate cleanly, because most bottle/chair pairings (e.g. near_cube_far_bottle,
    #     required 1.054) have LOW requirements and sit in the same band as the eligible four.
    #   clamped-always/rest — the pairings whose floor exceeds the available maximum, so every
    #     image is pushed to the floor. THIS is the disjoint band.
    inside = [k for k in realized if set(k[len("near_") :].split("_far_")) <= eligible]
    outside = [k for k in realized if k not in inside]
    inside_v = np.concatenate([realized[k] for k in inside])
    outside_v = np.concatenate([realized[k] for k in outside])
    bins = np.linspace(
        min(inside_v.min(), outside_v.min()), max(inside_v.max(), outside_v.max()), 60
    )
    band_overlap = _overlap(inside_v, outside_v, bins)

    clamped_v = np.concatenate([realized[k] for k in clamped_always])
    rest_v = np.concatenate([realized[k] for k in realized if k not in clamped_always])
    cbins = np.linspace(
        min(clamped_v.min(), rest_v.min()), max(clamped_v.max(), rest_v.max()), 60
    )
    clamped_band_overlap = _overlap(clamped_v, rest_v, cbins)

    allv = np.concatenate(list(realized.values()))
    grand = allv.mean()
    ss_between = sum(g.size * (g.mean() - grand) ** 2 for g in realized.values())
    eta2_pairing = float(ss_between / ((allv - grand) ** 2).sum())

    # role-category -> realized depth-ratio coupling (the B15-shaped confound)
    def _eta2_by(groups: dict[str, list[float]]) -> float:
        g = {k: np.asarray(v) for k, v in groups.items()}
        allv = np.concatenate(list(g.values()))
        return float(
            sum(x.size * (x.mean() - allv.mean()) ** 2 for x in g.values())
            / ((allv - allv.mean()) ** 2).sum()
        )

    near_groups: dict[str, list[float]] = {}
    for r in rows:
        key = f"near_{r['near_category']}_far_{r['far_category']}"
        if key in floors:
            near_groups.setdefault(r["near_category"], []).append(max(r["ratio"], floors[key]))
    eta2_far_cat = _eta2_by(far_depth_proxy)
    eta2_near_cat = _eta2_by(near_groups)

    # ⚠ The ratio is a PROXY. The claim under test is category <-> DEPTH coupling, and depth is
    # the primary target variable, so measure the realized far-object depth itself: clamping the
    # ratio pushes the far object back to depth_near * clamped_ratio.
    far_depth_by_far: dict[str, list[float]] = {}
    far_depth_by_near: dict[str, list[float]] = {}
    for r in rows:
        key = f"near_{r['near_category']}_far_{r['far_category']}"
        if key not in floors:
            continue
        realized_far_depth = r["depth_near"] * max(r["ratio"], floors[key])
        far_depth_by_far.setdefault(r["far_category"], []).append(realized_far_depth)
        far_depth_by_near.setdefault(r["near_category"], []).append(realized_far_depth)
    eta2_fardepth_far_cat = _eta2_by(far_depth_by_far)
    eta2_fardepth_near_cat = _eta2_by(far_depth_by_near)

    print(
        f"  pairings clamped on EVERY image (floor >= available max): "
        f"{len(clamped_always)}/{len(realized)}"
    )
    print(
        f"  eligible-4 band {inside_v.min():.3f}..{inside_v.max():.3f}  vs other-20 "
        f"{outside_v.min():.3f}..{outside_v.max():.3f}   overlap {band_overlap:.3f}  "
        f"(does NOT separate — most bottle/chair pairings have LOW requirements)"
    )
    print(
        f"  ALWAYS-CLAMPED band {clamped_v.min():.3f}..{clamped_v.max():.3f}  vs rest "
        f"{rest_v.min():.3f}..{rest_v.max():.3f}   overlap {clamped_band_overlap:.3f}"
        f"   <-- the split"
    )
    print(f"  eta2(pairing  -> realized ratio)     : {eta2_pairing:.3f}")
    print(f"  eta2(NEAR category -> realized ratio): {eta2_near_cat:.3f}")
    print(f"  eta2(FAR  category -> realized ratio): {eta2_far_cat:.3f}")
    print(
        f"  eta2(NEAR category -> realized FAR DEPTH m): {eta2_fardepth_near_cat:.3f}   "
        f"eta2(FAR category -> realized FAR DEPTH m): {eta2_fardepth_far_cat:.3f}"
    )
    verdict = (
        "NOT REALIZABLE — the always-clamped pairings occupy a disjoint ratio band and the "
        "pairing determines the ratio"
        if clamped_band_overlap < 0.05 or eta2_pairing > 0.5
        else "no separation detected"
    )
    print(f"  => {verdict}")
    return {
        "n_pairings_clamped_on_every_image": len(clamped_always),
        "pairings_clamped_on_every_image": sorted(clamped_always),
        "eligible_band": [float(inside_v.min()), float(inside_v.max())],
        "ineligible_band": [float(outside_v.min()), float(outside_v.max())],
        "eligible_vs_other_band_overlap": band_overlap,
        "always_clamped_band": [float(clamped_v.min()), float(clamped_v.max())],
        "always_clamped_vs_rest_band_overlap": clamped_band_overlap,
        "eta2_near_category_explains_ratio": eta2_near_cat,
        "eta2_near_category_explains_far_depth": eta2_fardepth_near_cat,
        "eta2_far_category_explains_far_depth": eta2_fardepth_far_cat,
        "eta2_pairing_explains_ratio": eta2_pairing,
        "eta2_far_category_explains_ratio": eta2_far_cat,
        "verdict": verdict,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--constants", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--json")
    ap.add_argument(
        "--margin-pct",
        type=float,
        default=4.75,
        help="headroom over the derived requirement, matching the current 1.85-over-1.7661 margin",
    )
    args = ap.parse_args()

    report = json.loads(Path(args.constants).read_text(encoding="utf-8"))
    required = {
        k: v["binding"] for k, v in report["pooled"]["required_ratio_by_pairing"].items()
    }
    config = load_config(args.config)
    categories = sorted(config["objects"]["categories"])
    margin = 1.0 + args.margin_pct / 100.0

    rows = _available_ratios(config, args.n)
    available = np.array([r["ratio"] for r in rows])
    avail_max = float(available.max())
    print(f"available ratio range (floor non-binding): {available.min():.4f} .. {avail_max:.4f}")
    print(f"per-pair floors carry the same +{args.margin_pct:.2f}% margin the 1.85 floor has\n")

    # ---- enumerate symmetric category subsets -------------------------------------------------
    results = []
    for size in range(2, len(categories) + 1):
        for subset in itertools.combinations(categories, size):
            pairings = [f"near_{a}_far_{b}" for a in subset for b in subset]
            if any(p not in required for p in pairings):
                continue
            uniform_floor = max(required[p] for p in pairings) * margin
            retained = available[
                np.array(
                    [
                        r["near_category"] in subset and r["far_category"] in subset
                        for r in rows
                    ]
                )
            ]
            usable = retained[retained >= uniform_floor]
            results.append(
                {
                    "categories": list(subset),
                    "n_categories": len(subset),
                    "n_pairings": len(pairings),
                    "worst_required": max(required[p] for p in pairings),
                    "uniform_floor": uniform_floor,
                    "uniform_feasible": bool(uniform_floor < avail_max),
                    "uniform_retained_range": (
                        [float(usable.min()), avail_max] if usable.size else None
                    ),
                    "uniform_dynamic_range": (
                        float(avail_max / usable.min()) if usable.size else 1.0
                    ),
                    "uniform_acceptance_fraction": (
                        float(usable.size / retained.size) if retained.size else 0.0
                    ),
                    "image_retention_fraction": float(retained.size / available.size),
                }
            )

    feasible = [r for r in results if r["uniform_dynamic_range"] >= USABLE_DYNAMIC_RANGE]
    feasible.sort(key=lambda r: (-r["n_categories"], -r["uniform_dynamic_range"]))

    print("--- OPTION A1: restricted categories + UNIFORM floor (zero pairing-ratio coupling) ---")
    print(
        f"  {'categories':44s} {'#pair':>5s} {'req':>7s} {'floor':>7s} {'range':>15s} "
        f"{'dyn':>5s} {'acc':>5s} {'imgs':>5s}"
    )
    if not feasible:
        print(f"  NONE reach a {USABLE_DYNAMIC_RANGE:.2f}x retained dynamic range.")
    for r in feasible[:12]:
        rng_s = (
            f"{r['uniform_retained_range'][0]:.3f}..{r['uniform_retained_range'][1]:.3f}"
            if r["uniform_retained_range"]
            else "-"
        )
        print(
            f"  {','.join(r['categories']):44s} {r['n_pairings']:5d} {r['worst_required']:7.4f} "
            f"{r['uniform_floor']:7.4f} {rng_s:>15s} {r['uniform_dynamic_range']:5.2f} "
            f"{r['uniform_acceptance_fraction']:5.2f} {r['image_retention_fraction']:5.2f}"
        )

    # ---- option A2: all 36 pairings, PER-PAIR floors, coupling measured ----------------------
    print("\n--- OPTION A2: all six categories + PER-PAIR floors (coupling must be measured) ---")
    per_pair_floors = {k: v * margin for k, v in required.items()}
    infeasible = {k: v for k, v in per_pair_floors.items() if v >= avail_max}
    coupling_all = _coupling(rows, per_pair_floors)
    print(
        f"  pairings whose per-pair floor still exceeds the available max: "
        f"{len(infeasible)}/{len(per_pair_floors)}"
    )
    for k, v in sorted(infeasible.items(), key=lambda kv: -kv[1])[:6]:
        print(f"    {k:30s} floor {v:.4f} > available max {avail_max:.4f}")
    if coupling_all:
        print(
            f"  coupling: eta2(pairing -> ratio) = "
            f"{coupling_all['eta2_pairing_explains_ratio']:.3f}   "
            f"worst pairwise overlap {coupling_all['min_pairwise_overlap']:.3f}   "
            f"median {coupling_all['median_pairwise_overlap']:.3f}"
        )

    # ---- the same coupling check on the best A1 subset, with per-pair floors -----------------
    best = feasible[0] if feasible else None
    coupling_best = {}
    if best:
        subset = set(best["categories"])
        sub_floors = {
            k: v
            for k, v in per_pair_floors.items()
            if k[len("near_") :].split("_far_")[0] in subset
            and k[len("near_") :].split("_far_")[1] in subset
        }
        coupling_best = _coupling(rows, sub_floors)
        print(
            f"\n  same check on the largest feasible subset ({','.join(best['categories'])}) "
            f"under PER-PAIR floors:"
        )
        print(
            f"    eta2 = {coupling_best['eta2_pairing_explains_ratio']:.3f}   "
            f"worst overlap {coupling_best['min_pairwise_overlap']:.3f}   "
            f"median {coupling_best['median_pairwise_overlap']:.3f}"
        )
        print(
            "    (a UNIFORM floor over the same subset has eta2 = 0 by construction — the floor "
            "no longer depends on the pairing)"
        )

    # ---- is a SIX-category control realizable at all? (binding disambiguation, 2026-07-19) ----
    print("\n--- SIX-CATEGORY CONTROL: realizable, or does it rebuild the confound? ---")
    six_cat = _six_category_control(rows, required, margin, avail_max)

    out = {
        "six_category_control": six_cat,
        "available_ratio_min": float(available.min()),
        "available_ratio_max": avail_max,
        "margin_pct": args.margin_pct,
        "usable_dynamic_range_threshold": USABLE_DYNAMIC_RANGE,
        "all_subsets": results,
        "feasible_uniform_floor_subsets": feasible,
        "per_pair_infeasible": infeasible,
        "coupling_all_six_per_pair_floors": coupling_all,
        "coupling_best_subset_per_pair_floors": coupling_best,
        "best_subset": best,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
