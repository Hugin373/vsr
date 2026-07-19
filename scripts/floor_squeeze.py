"""Measure what a `min_depth_ratio` floor does to the depth-ratio target it gates.

    uv run --extra analysis scripts/floor_squeeze.py \
        --config configs/m4a_v1_natural_congruent_pilot.yaml \
        --config configs/m4a_v1_counterbalanced_pilot_j2.yaml \
        --config configs/m4a_v1_conflict_pilot.yaml \
        --n 1200 --constants reports/m4a_cue_constants.json --json reports/m4a_floor_squeeze.json

Why (AGENTS.md rule 13: measure, don't argue). The natural-congruent regime fails the ratio
gate (oracle R2 = -0.252 under a held-out depth-gap split) while counterbalanced passes at
+0.803. The two differ in `min_depth_ratio`: 1.85 versus 1.05. The 1.85 was never derived — it
was raised until congruence validation went green — so before treating "ratio is not recoverable
in the congruent regime" as a property of the stimuli, the alternative has to be excluded: that
the floor CLAMPS most of the regime's depth ratios into a narrow band whose remaining variation
is the floor's own jitter rather than scene depth structure. A target whose variance is mostly
floor jitter is unlearnable across a held-out depth-gap split BY CONSTRUCTION, and that is a
design artifact, not a finding about depth.

Method: sample the same config twice from the same seed, once with the real floor and once with
a floor that cannot bind (1.000001, keeping `min_depth_ratio_jitter` so the RNG stream still
consumes the same draws). "Available" is the ratio distribution the rest of the design produces;
"accepted" is what the floor lets through. Both are stratified by (near-category, far-category).

⚠ The two runs diverge in which images PLACE — pushing the far object back to satisfy the floor
changes projected geometry, so the placement guard accepts a different subset. Placement
failures are reported for both rather than hidden.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

from sbind.stimuli import geometry
from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config

# A floor of exactly 1.0 would skip the `rng.uniform` draw inside the sampler and shift the
# whole random stream, making the two runs incomparable. This value keeps the draw and never
# binds: the far object is always behind the near one, so every ratio already exceeds it.
NON_BINDING_FLOOR = 1.000001


def _ratios(specs) -> list[dict]:
    """Per-scene far/near depth ratio of the TARGET pair, with its factor strata."""
    out = []
    for spec in specs:
        _, R, t, _ = geometry.camera_frame(
            spec.camera.pos_world,
            spec.camera.target_world,
            spec.camera.f_mm,
            spec.camera.sensor_width_mm,
            spec.camera.res_x,
            spec.camera.res_y,
        )
        factors = spec.factors
        near_i = int(factors["closer_object"])
        far_i = 1 - near_i
        # camera-frame z of the object centre — the same quantity annotations record as depth_m
        depths = [
            float((R @ np.asarray(o.pos_world, dtype=float) + t)[2]) for o in spec.objects[:2]
        ]
        out.append(
            {
                "id": spec.id,
                "near_category": factors["near_category"],
                "far_category": factors["far_category"],
                "near_depth_bin": int(factors["near_depth_bin"]),
                "depth_gap_bin": int(factors["depth_gap_bin"]),
                "depth_near": depths[near_i],
                "depth_far": depths[far_i],
                "ratio": depths[far_i] / depths[near_i],
            }
        )
    return out


def _sample(config: dict, n: int, floor: float | None) -> tuple[list[dict], int]:
    cfg = copy.deepcopy(config)
    cfg["n_images"] = n
    if floor is not None:
        cfg.setdefault("constraints", {})["min_depth_ratio"] = floor
    failures: list[dict] = []
    specs = build_scene_specs(
        cfg, int(cfg["seed"]), raise_on_placement_failure=False, placement_failures=failures
    )
    return _ratios(specs), len(failures)


def _quantiles(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {}
    return {
        "n": int(values.size),
        "min": float(values.min()),
        "q10": float(np.quantile(values, 0.10)),
        "median": float(np.median(values)),
        "q90": float(np.quantile(values, 0.90)),
        "max": float(values.max()),
        "dynamic_range": float(values.max() / values.min()),
        "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0,
    }


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _design_ranges(rows: list[dict], config: dict) -> dict:
    """Bin-drop assessment (advisor addendum #3): what range do the targets still demonstrate?

    ⚠ Per DR3 #14 this gate is VALIDITY-ONLY. Dropping the 0.2 m bin makes several targets
    easier; "easier" is a REPORTED PROPERTY, never a failure to engineer away. What must hold is
    that the continuous/ratio targets still span enough range to be regression targets at all,
    that the ordinal margin never approaches zero, and that the near/far depth bins stay balanced.
    """
    if not rows:
        return {}
    near = np.array([r["depth_near"] for r in rows])
    far = np.array([r["depth_far"] for r in rows])
    bins = np.array([r["near_depth_bin"] for r in rows])
    margin = far - near
    counts = {int(b): int((bins == b).sum()) for b in sorted(set(bins.tolist()))}
    return {
        "near_depth_m": _quantiles(near),
        "far_depth_m": _quantiles(far),
        "all_depth_m": _quantiles(np.concatenate([near, far])),
        "ordinal_margin_m": {
            "min": float(margin.min()),
            "median": float(np.median(margin)),
            "max": float(margin.max()),
            "n_nonpositive": int((margin <= 0).sum()),
        },
        "near_depth_bin_counts": counts,
        "near_depth_bin_balance": (
            min(counts.values()) / max(counts.values()) if counts else float("nan")
        ),
        "configured_near_depth_bins": config["factors"]["near_depth_bins"],
    }


def analyse(
    config: dict,
    n: int,
    required: dict[str, dict] | None,
) -> dict:
    floor = float((config.get("constraints") or {}).get("min_depth_ratio", 1.0))
    jitter = float((config.get("constraints") or {}).get("min_depth_ratio_jitter", 0.0))
    floor_max = floor * (1.0 + jitter)

    available, avail_fail = _sample(config, n, NON_BINDING_FLOOR)
    accepted, acc_fail = _sample(config, n, None)

    avail_r = np.array([r["ratio"] for r in available])
    acc_r = np.array([r["ratio"] for r in accepted])

    # How much of the design's natural ratio range does the floor keep?
    acceptance_fraction = float((avail_r >= floor).mean()) if avail_r.size else float("nan")
    # How much of what survives is the floor's own jitter rather than scene depth structure?
    floor_determined = float((acc_r <= floor_max).mean()) if acc_r.size else float("nan")

    strata: dict[str, dict] = {}
    pairings = sorted({(r["near_category"], r["far_category"]) for r in available})
    for near_cat, far_cat in pairings:
        key = f"near_{near_cat}_far_{far_cat}"
        a = np.array(
            [
                r["ratio"]
                for r in available
                if r["near_category"] == near_cat and r["far_category"] == far_cat
            ]
        )
        b = np.array(
            [
                r["ratio"]
                for r in accepted
                if r["near_category"] == near_cat and r["far_category"] == far_cat
            ]
        )
        req = (required or {}).get(key, {}).get("binding")
        strata[key] = {
            "required_ratio_worst_case": req,
            "configured_floor": floor,
            "floor_clears_requirement": (None if req is None else bool(floor > req)),
            "floor_margin_pct": (None if req is None else 100.0 * (floor / req - 1.0)),
            "available": _quantiles(a),
            "accepted": _quantiles(b),
            "acceptance_fraction": float((a >= floor).mean()) if a.size else float("nan"),
            "floor_determined_fraction": float((b <= floor_max).mean()) if b.size else float("nan"),
        }

    def _factor_corr(rows: list[dict]) -> dict[str, float]:
        if not rows:
            return {}
        ratio = np.array([r["ratio"] for r in rows])
        return {
            "ratio_vs_depth_gap_bin": _corr(
                ratio, np.array([r["depth_gap_bin"] for r in rows], dtype=float)
            ),
            "ratio_vs_near_depth_bin": _corr(
                ratio, np.array([r["near_depth_bin"] for r in rows], dtype=float)
            ),
            "ratio_vs_depth_near": _corr(ratio, np.array([r["depth_near"] for r in rows])),
        }

    return {
        "experiment": config.get("experiment"),
        "regime": (config.get("condition") or {}).get("regime"),
        "condition": dict(config.get("condition") or {}),
        "design_ranges": _design_ranges(accepted, config),
        "n_requested": n,
        "configured_floor": floor,
        "floor_jitter": jitter,
        "floor_band": [floor, floor_max],
        "placement_failures_without_floor": avail_fail,
        "placement_failures_with_floor": acc_fail,
        "available": _quantiles(avail_r),
        "accepted": _quantiles(acc_r),
        "acceptance_fraction": acceptance_fraction,
        "floor_determined_fraction": floor_determined,
        "factor_correlations_available": _factor_corr(available),
        "factor_correlations_accepted": _factor_corr(accepted),
        "by_pairing": strata,
    }


def _print_regime(result: dict) -> None:
    print("=" * 96)
    print(
        f"{result['experiment']}  regime={result['regime']}  "
        f"floor={result['configured_floor']} (band {result['floor_band'][0]:.3f}"
        f"..{result['floor_band'][1]:.3f})  n={result['n_requested']}"
    )
    print("=" * 96)
    av, ac = result["available"], result["accepted"]
    print(
        f"  available ratio : n={av['n']:4d} [{av['min']:.3f} .. {av['max']:.3f}] "
        f"median {av['median']:.3f}  sd {av['sd']:.3f}  dyn-range {av['dynamic_range']:.2f}x"
    )
    print(
        f"  accepted  ratio : n={ac['n']:4d} [{ac['min']:.3f} .. {ac['max']:.3f}] "
        f"median {ac['median']:.3f}  sd {ac['sd']:.3f}  dyn-range {ac['dynamic_range']:.2f}x"
    )
    print(
        f"  acceptance fraction (available >= floor) : {result['acceptance_fraction']:.3f}"
    )
    print(
        f"  floor-DETERMINED fraction (accepted within the floor band) : "
        f"{result['floor_determined_fraction']:.3f}"
    )
    print(f"  placement failures: {result['placement_failures_with_floor']} with floor, "
          f"{result['placement_failures_without_floor']} without")
    fa, fc = result["factor_correlations_available"], result["factor_correlations_accepted"]
    print(
        f"  r(ratio, depth_gap_bin) : available {fa['ratio_vs_depth_gap_bin']:+.3f} -> "
        f"accepted {fc['ratio_vs_depth_gap_bin']:+.3f}"
    )
    print(
        f"  r(ratio, near_depth_bin): available {fa['ratio_vs_near_depth_bin']:+.3f} -> "
        f"accepted {fc['ratio_vs_near_depth_bin']:+.3f}"
    )
    result_condition = result.get("condition") or {}
    d = result.get("design_ranges") or {}
    if d:
        print(
            f"  depth span (accepted): near {d['near_depth_m']['min']:.2f}.."
            f"{d['near_depth_m']['max']:.2f} m  far {d['far_depth_m']['min']:.2f}.."
            f"{d['far_depth_m']['max']:.2f} m  all {d['all_depth_m']['min']:.2f}.."
            f"{d['all_depth_m']['max']:.2f} m ({d['all_depth_m']['dynamic_range']:.2f}x)"
        )
        om = d["ordinal_margin_m"]
        print(
            f"  ordinal margin (far-near): min {om['min']:.3f} m  median {om['median']:.3f} m  "
            f"max {om['max']:.3f} m  non-positive {om['n_nonpositive']}"
        )
        print(
            f"  near_depth_bin counts {d['near_depth_bin_counts']}  "
            f"balance (min/max) {d['near_depth_bin_balance']:.3f}  "
            f"bins {d['configured_near_depth_bins']}"
        )
    print()
    print(
        f"  {'pairing':28s} {'req':>7s} {'floor':>7s} {'mgn%':>7s} "
        f"{'avail range':>17s} {'acc range':>17s} {'acc frac':>8s} {'floor-det':>9s} {'dyn':>5s}"
    )
    for key in sorted(result["by_pairing"]):
        s = result["by_pairing"][key]
        a, b = s["available"], s["accepted"]
        req = s["required_ratio_worst_case"]
        margin = s["floor_margin_pct"]
        req_s = f"{req:7.4f}" if req is not None else "      -"
        margin_s = f"{margin:+7.1f}" if margin is not None else "      -"
        # Only a regime that CLAIMS size congruence can be in violation of the congruence
        # requirement. counterbalanced/conflict sit below it on purpose, so flagging them would
        # be a false alarm — the same distinction validate_stimuli.py already makes.
        claims_congruence = (
            (result_condition or {}).get("size_condition") == "congruent"
        )
        flag = (
            "  <-- FLOOR BELOW REQ"
            if (claims_congruence and req is not None and not s["floor_clears_requirement"])
            else ""
        )
        print(
            f"  {key:28s} {req_s} {s['configured_floor']:7.3f} {margin_s} "
            f"{a['min']:7.3f}..{a['max']:<8.3f} {b['min']:7.3f}..{b['max']:<8.3f} "
            f"{s['acceptance_fraction']:8.3f} {s['floor_determined_fraction']:9.3f} "
            f"{b['dynamic_range']:5.2f}{flag}"
        )
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", dest="configs", required=True, action="append")
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--constants", help="derive_cue_constants JSON, for the required ratios")
    ap.add_argument("--json", help="write the full report here")
    args = ap.parse_args()

    required = None
    if args.constants:
        report = json.loads(Path(args.constants).read_text(encoding="utf-8"))
        required = report["pooled"]["required_ratio_by_pairing"]

    results = []
    for path in args.configs:
        result = analyse(load_config(path), args.n, required)
        result["config"] = path
        _print_regime(result)
        results.append(result)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
