"""§5 assignment-level seed sweep — checks A, B, C. NO RENDERING.

    uv run --extra analysis scripts/s5_assignment_sweep.py \
        --config configs/m4a_v1_natural_congruent_pilot.yaml --n 1200 \
        --json reports/m4a_s5_sweep_natural_congruent.json

Implements the pre-committed protocol in `docs/M4A_S5_CRITERIA.md`. The seeds, k, rounding rule,
weakest-stratum clause and spread rule are CONSTANTS below and were committed to git BEFORE any
sweep result existed (commit a6a4f7f); git history is the ordering proof. Bounds are computed
mechanically from the formula — no judgement is applied to the numbers after seeing them.

⚠ BOUNDARY (ruled, and it is not a technicality). "Realized" means PLACED, not RENDERED, so this
sweep establishes every quantity in checks A, B and C, including placed-level P(near|c). It
contributes NOTHING to check D, which is exclusively pixel-level on the frozen pilot. A sampling
correlation such as r(realized ratio, depth_gap_bin) validates generator SEMANTICS; it is not
evidence of visual recoverability and can never satisfy check D.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np

from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config

# ---------------------------------------------------------------------------------------------
# PRE-COMMITTED PROTOCOL v2 — ruled 2026-07-20, committed BEFORE any v2 result existed.
# Changing any of these invalidates the pre-registration.
#
# 🔒 FORMAL SEED ROLES (disjoint splits, the same discipline as M5's direction protocol). A seed
# used for one role may never be reused for another: reusing a calibration seed to set bounds
# would let the design be selected and judged on the same draw.
#
#   CALIBRATION   8001-8008  root search + design selection. Answers "which floor?"
#   BOUND_SETTING 9009-9016  operative bound-setting at the ratified floor. Answers "how far can
#                            it drift?" FRESH — 9001-9008 are now DEVELOPMENT EVIDENCE only.
#   FROZEN PILOT  config seed, accept/reject only. Never used to set or move a threshold.
#
# ⚠ 9001-9008 produced the provisional bounds at floor 1.1707. Those are DESIGN-SELECTION
# EVIDENCE ONLY; operative bounds recompute on BOUND_SETTING seeds at the ratified floor.
# ---------------------------------------------------------------------------------------------
PROTOCOL_VERSION = "2.0"

CALIBRATION_SEEDS = (8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008)
BOUND_SETTING_SEEDS = (9009, 9010, 9011, 9012, 9013, 9014, 9015, 9016)
DEVELOPMENT_SEEDS = (9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008)   # v1, superseded

SEEDS = BOUND_SETTING_SEEDS   # default role for this script
REFERENCE_SEED = 410          # reported, EXCLUDED from bounds (the design was developed on it)
K = 2.0
ROUND_DP = 2
SPREAD_RULE_MAX_CV = 0.25     # SD > 25% of mean -> demoted to reported-only

# --- amendment v2, ratified 2026-07-20 -------------------------------------------------------
# The CV spread rule is inapplicable to quantities that sit at zero BY INTENT: a 0.005 absolute
# spread on an eta^2 of 0.02 yields CV > 0.25 and demotes a quantity that is nowhere near its
# bound. The reductio observed on v1: placed-level role imbalance was EXACTLY 0.0000 on all eight
# seeds — the best value attainable — and CV = inf demoted it.
#
# Exemption: the spread rule does not apply when  max_s q_s <= NEAR_ZERO_EXEMPTION * criterion
# bound. Restricted to NATURAL-ZERO, lower-is-better quantities (eta^2, imbalances, clamp
# predictability). It NEVER applies to correlations or retained range: those are lower-bounded
# and far from zero, so relative spread is meaningful for them and instability there is real.
NEAR_ZERO_EXEMPTION = 0.25


def _round_out(value: float, direction: str) -> float:
    factor = 10**ROUND_DP
    return (
        math.floor(value * factor) / factor
        if direction == "down"
        else math.ceil(value * factor) / factor
    )


def _eta2(groups: dict[str, np.ndarray]) -> float:
    groups = {k: v for k, v in groups.items() if v.size > 0}
    if len(groups) < 2:
        return float("nan")
    allv = np.concatenate(list(groups.values()))
    grand = allv.mean()
    ss_total = float(((allv - grand) ** 2).sum())
    if ss_total <= 0:
        return float("nan")
    return float(sum(g.size * (g.mean() - grand) ** 2 for g in groups.values()) / ss_total)


def _overlap(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return float("nan")
    bins = np.linspace(min(a.min(), b.min()), max(a.max(), b.max()), 60)
    ha, _ = np.histogram(a, bins=bins, density=True)
    hb, _ = np.histogram(b, bins=bins, density=True)
    return float(np.minimum(ha, hb) @ np.diff(bins))


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def measure_one_seed(config: dict, n: int, seed: int) -> dict:
    """All check A/B/C quantities for one seed. Sampler only — no renderer."""
    cfg = copy.deepcopy(config)
    cfg["n_images"] = n
    log: list[dict] = []
    failures: list[dict] = []
    specs = build_scene_specs(
        cfg, seed, raise_on_placement_failure=False, placement_failures=failures, ratio_log=log
    )
    # One accepted-placement row per placed image. A mismatch means the audit hook and the output
    # disagree about what was built, which would silently corrupt every quantity below.
    if len(log) != len(specs):
        raise AssertionError(
            f"seed {seed}: ratio_log has {len(log)} rows for {len(specs)} placed specs"
        )

    ratio = np.array([r["ratio_realized"] for r in log])
    raw = np.array([r["ratio_raw"] for r in log])
    clamped = np.array([r["clamped"] for r in log], dtype=bool)
    gap_bin = np.array([r["depth_gap_bin"] for r in log], dtype=float)
    near_cat = np.array([r["near_category"] for r in log])
    far_cat = np.array([r["far_category"] for r in log])
    pairing = np.array([f"{a}->{b}" for a, b in zip(near_cat, far_cat, strict=True)])
    far_depth = np.array([r["depth_near"] * r["ratio_realized"] for r in log])

    floor = float(cfg["constraints"]["min_depth_ratio"])
    band_max = floor * (1.0 + float(cfg["constraints"].get("min_depth_ratio_jitter", 0.0)))

    def by(keys: np.ndarray, values: np.ndarray) -> dict[str, np.ndarray]:
        return {k: values[keys == k] for k in np.unique(keys)}

    # ---- check A: sampling semantics ----
    unclamped = ~clamped
    per_pairing = {
        k: {
            "n": int((pairing == k).sum()),
            "r_gap": _corr(ratio[pairing == k], gap_bin[pairing == k]),
            "range": float(ratio[pairing == k].max() / ratio[pairing == k].min()),
            "clamped_fraction": float(clamped[pairing == k].mean()),
        }
        for k in np.unique(pairing)
    }
    check_a = {
        "r_ratio_gap": _corr(ratio, gap_bin),
        "retained_range": float(ratio.max() / ratio.min()),
        "r_ratio_gap_unclamped": _corr(ratio[unclamped], gap_bin[unclamped]),
        "retained_range_unclamped": (
            float(ratio[unclamped].max() / ratio[unclamped].min())
            if unclamped.any()
            else float("nan")
        ),
        "acceptance_fraction": float(unclamped.mean()),
        "weakest_stratum_r_gap": min(v["r_gap"] for v in per_pairing.values()),
        "weakest_stratum_range": min(v["range"] for v in per_pairing.values()),
        "n_total": int(ratio.size),
        "n_per_pairing_min": min(v["n"] for v in per_pairing.values()),
        "n_per_pairing_max": max(v["n"] for v in per_pairing.values()),
        "placement_failures": len(failures),
    }

    # ---- check B: category and role independence ----
    role = {}
    for cat in np.unique(np.concatenate([near_cat, far_cat])):
        n_near = int((near_cat == cat).sum())
        n_far = int((far_cat == cat).sum())
        role[str(cat)] = n_near / (n_near + n_far)
    check_b = {
        "eta2_pairing_ratio": _eta2(by(pairing, ratio)),
        "eta2_near_cat_ratio": _eta2(by(near_cat, ratio)),
        "eta2_far_cat_ratio": _eta2(by(far_cat, ratio)),
        "eta2_near_cat_far_depth": _eta2(by(near_cat, far_depth)),
        "eta2_far_cat_far_depth": _eta2(by(far_cat, far_depth)),
        "eta2_pairing_clamp": _eta2(by(pairing, clamped.astype(float))),
        "eta2_near_cat_clamp": _eta2(by(near_cat, clamped.astype(float))),
        "eta2_far_cat_clamp": _eta2(by(far_cat, clamped.astype(float))),
        "p_near_by_category": role,
        "max_abs_role_imbalance": max(abs(v - 0.5) for v in role.values()),
    }

    # ---- check C: clamp burden and support overlap ----
    check_c = {
        # CANONICAL gating estimand (ruled 2026-07-20): the DRAWN, jittered floor.
        "clamped_fraction_drawn_floor": float(clamped.mean()),
        "accepted_in_floor_band_fraction": float((ratio <= band_max).mean()),
        "max_stratum_clamped_fraction": max(v["clamped_fraction"] for v in per_pairing.values()),
        "clamped_per_near_category": {
            str(k): float(v.mean()) for k, v in by(near_cat, clamped.astype(float)).items()
        },
        "clamped_per_far_category": {
            str(k): float(v.mean()) for k, v in by(far_cat, clamped.astype(float)).items()
        },
        "raw_ratio_range": [float(raw.min()), float(raw.max())],
        "realized_ratio_range": [float(ratio.min()), float(ratio.max())],
        "clamped_unclamped_overlap": _overlap(ratio[clamped], ratio[unclamped]),
        "n_always_clamped_pairings": sum(
            1 for v in per_pairing.values() if v["clamped_fraction"] >= 1.0
        ),
        "always_clamped_pairings": [
            k for k, v in per_pairing.items() if v["clamped_fraction"] >= 1.0
        ],
    }

    return {
        "seed": seed,
        "check_a": check_a,
        "check_b": check_b,
        "check_c": check_c,
        "per_pairing": per_pairing,
    }


# quantity -> (path, direction, natural_zero, criterion_bound).
#   direction "lower" = higher-is-better (we set a LOWER bound).
#   natural_zero      = eligible for the near-zero spread exemption (eta^2, imbalances, clamp
#                       predictability). Correlations and ranges are NEVER eligible.
#   criterion_bound   = the §5 criteria-file bound the exemption is measured against.
GATED = {
    "A.r_ratio_gap": (("check_a", "r_ratio_gap"), "lower", False, None),
    "A.retained_range": (("check_a", "retained_range"), "lower", False, None),
    "A.weakest_stratum_r_gap": (("check_a", "weakest_stratum_r_gap"), "lower", False, None),
    "A.weakest_stratum_range": (("check_a", "weakest_stratum_range"), "lower", False, None),
    "B.eta2_pairing_ratio": (("check_b", "eta2_pairing_ratio"), "upper", True, 0.10),
    "B.eta2_near_cat_ratio": (("check_b", "eta2_near_cat_ratio"), "upper", True, 0.10),
    "B.eta2_far_cat_ratio": (("check_b", "eta2_far_cat_ratio"), "upper", True, 0.10),
    "B.eta2_near_cat_far_depth": (("check_b", "eta2_near_cat_far_depth"), "upper", True, 0.05),
    "B.eta2_far_cat_far_depth": (("check_b", "eta2_far_cat_far_depth"), "upper", True, 0.05),
    "B.eta2_pairing_clamp": (("check_b", "eta2_pairing_clamp"), "upper", True, 0.10),
    "B.max_abs_role_imbalance": (("check_b", "max_abs_role_imbalance"), "upper", True, 0.02),
    "C.clamped_fraction_drawn_floor": (
        ("check_c", "clamped_fraction_drawn_floor"), "upper", False, None
    ),
    "C.max_stratum_clamped_fraction": (
        ("check_c", "max_stratum_clamped_fraction"), "upper", False, None
    ),
}


def compute_bounds(per_seed: list[dict]) -> dict:
    """Mechanical application of the pre-committed formula. No judgement after seeing values."""
    out: dict[str, dict] = {}
    for name, (path, direction, natural_zero, criterion) in GATED.items():
        values = np.array([s[path[0]][path[1]] for s in per_seed], dtype=float)
        if np.isnan(values).any():
            out[name] = {"status": "undefined", "values": values.tolist()}
            continue
        sd = float(values.std(ddof=1))
        mean = float(values.mean())
        cv = abs(sd / mean) if mean != 0 else float("inf")
        record = {
            "direction": direction,
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": mean,
            "sd": sd,
            "cv": cv,
            "values": values.tolist(),
        }
        # amendment v2: near-zero exemption, natural-zero lower-is-better quantities only
        exempt = (
            natural_zero
            and criterion is not None
            and float(values.max()) <= NEAR_ZERO_EXEMPTION * criterion
        )
        record["natural_zero"] = natural_zero
        record["criterion_bound"] = criterion
        record["near_zero_exempt"] = bool(exempt)
        if cv > SPREAD_RULE_MAX_CV and not exempt:
            record["status"] = "DEMOTED_reported_only"
            record["reason"] = f"seed-to-seed CV {cv:.3f} > {SPREAD_RULE_MAX_CV}"
        else:
            if exempt and cv > SPREAD_RULE_MAX_CV:
                record["reason"] = (
                    f"CV {cv:.3f} > {SPREAD_RULE_MAX_CV} but EXEMPT: max {values.max():.4f} "
                    f"<= {NEAR_ZERO_EXEMPTION} x criterion bound {criterion}"
                )
            record["status"] = "gated"
            record["bound"] = (
                _round_out(values.min() - K * sd, "down")
                if direction == "lower"
                else _round_out(values.max() + K * sd, "up")
            )
        out[name] = record
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--n", type=int, default=1200)
    ap.add_argument("--json")
    args = ap.parse_args()

    config = load_config(args.config)
    print(f"config: {args.config}   n={args.n} per seed")
    print(f"PRE-COMMITTED: seeds={SEEDS}  k={K}  round={ROUND_DP}dp outward  "
          f"spread-rule CV>{SPREAD_RULE_MAX_CV}\n")

    per_seed = [measure_one_seed(config, args.n, s) for s in SEEDS]
    reference = measure_one_seed(config, args.n, REFERENCE_SEED)

    print(f"  {'seed':>6s} {'r(ratio,gap)':>13s} {'range':>7s} {'clamped':>8s} "
          f"{'maxStratClamp':>14s} {'eta2 pair':>10s} {'roleImb':>8s}")
    for s in per_seed:
        print(
            f"  {s['seed']:6d} {s['check_a']['r_ratio_gap']:13.4f} "
            f"{s['check_a']['retained_range']:7.3f} "
            f"{s['check_c']['clamped_fraction_drawn_floor']:8.3f} "
            f"{s['check_c']['max_stratum_clamped_fraction']:14.3f} "
            f"{s['check_b']['eta2_pairing_ratio']:10.4f} "
            f"{s['check_b']['max_abs_role_imbalance']:8.4f}"
        )
    print(
        f"  {REFERENCE_SEED:6d} {reference['check_a']['r_ratio_gap']:13.4f} "
        f"{reference['check_a']['retained_range']:7.3f} "
        f"{reference['check_c']['clamped_fraction_drawn_floor']:8.3f} "
        f"{reference['check_c']['max_stratum_clamped_fraction']:14.3f} "
        f"{reference['check_b']['eta2_pairing_ratio']:10.4f} "
        f"{reference['check_b']['max_abs_role_imbalance']:8.4f}   <- REFERENCE, excluded"
    )

    bounds = compute_bounds(per_seed)
    print("\n--- MECHANICAL BOUNDS (pre-committed formula) ---")
    print(
        f"  {'quantity':34s} {'dir':>5s} {'min':>9s} {'max':>9s} {'sd':>8s} "
        f"{'cv':>6s} {'BOUND':>9s}"
    )
    for name, r in bounds.items():
        if r["status"] == "undefined":
            print(f"  {name:34s}     — undefined (nan present)")
            continue
        bound = f"{r['bound']:9.2f}" if r["status"] == "gated" else "  DEMOTED"
        print(
            f"  {name:34s} {r['direction']:>5s} {r['min']:9.4f} {r['max']:9.4f} "
            f"{r['sd']:8.4f} {r['cv']:6.3f} {bound}"
        )

    demoted = [k for k, v in bounds.items() if v["status"] == "DEMOTED_reported_only"]
    if demoted:
        print(f"\n  ⚠ DEMOTED to reported-only by the spread rule: {demoted}")

    # structural hard failures (check C) — these are not bounded quantities, they are binary
    hard = []
    for s in per_seed:
        if s["check_c"]["n_always_clamped_pairings"] > 0:
            hard.append(f"seed {s['seed']}: always-clamped pairings "
                        f"{s['check_c']['always_clamped_pairings']}")
        ov = s["check_c"]["clamped_unclamped_overlap"]
        if ov == ov and ov < 0.05:
            hard.append(f"seed {s['seed']}: clamped/unclamped support overlap {ov:.3f} < 0.05")
    print("\n--- CHECK C STRUCTURAL HARD FAILURES ---")
    print("  " + ("NONE" if not hard else "\n  ".join(hard)))

    report = {
        "protocol": {
            "seeds": list(SEEDS),
            "reference_seed_excluded": REFERENCE_SEED,
            "k": K,
            "round_dp": ROUND_DP,
            "spread_rule_max_cv": SPREAD_RULE_MAX_CV,
            "committed_in": "a6a4f7f",
        },
        "config": args.config,
        "n_per_seed": args.n,
        "per_seed": per_seed,
        "reference_seed": reference,
        "bounds": bounds,
        "check_c_hard_failures": hard,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
