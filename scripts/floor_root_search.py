"""Minimal self-consistent congruence floor r* — PRE-COMMITTED root-search protocol.

    uv run --extra stimuli scripts/floor_root_search.py \
        --config configs/m4a_v1_natural_congruent_pilot.yaml \
        --json reports/m4a_floor_root_search.json

⚠ THIS FILE IS COMMITTED BEFORE IT IS RUN. Git history is the ordering proof. Every constant
below — grid, seeds, tolerance, margin — is fixed in advance so that r* cannot be chosen after
seeing which value happens to look good.

WHY A ROOT SEARCH AT ALL
The congruence requirement is a function of the floor: R = R(F). A higher floor pushes the far
object deeper, where perspective is less extreme and the area constants vary less, so R falls as
F rises. A floor is valid only if it clears its OWN re-derived requirement, i.e. F >= R(F) — a
fixed-point condition, not a one-shot derivation. Measured so far:

    R(1.1707) = 1.1761   (floor SHORT by 0.46%)
    R(1.2320) = 1.1601   (floor clears, +6.20%)

Interpolating the fixed point gives r* ~ 1.175. 1.2320 was REJECTED (2026-07-20): it is the fixed
point plus a margin policy inherited from the now-dead six-category envelope, and it demonstrably
destroys sampling semantics — r(ratio, gap) 0.73 -> 0.50, weakest stratum 0.64 -> 0.18,
clamp 0.48 -> 0.72. The minimal self-consistent floor is what is wanted, not a comfortable one.

ACCEPTANCE IS JOINT (ruled). A candidate floor must satisfy BOTH:
  (a) AREA validity     — F >= R(F), re-derived at F itself;
  (b) SAMPLING validity — the check A-C bounds established as design-selection evidence;
Placement is deliberately NOT one of them — see AMENDMENT v1.2 in placement_failure_counts:
the failure rate is a floor-independent ~0.02% background, so gating on it would make r* depend
on a coin-flip. It is a real but SEPARATE operational defect.
Neither of the two is sufficient alone. Expect a genuine test: interpolation puts weakest-stratum r
and the clamp rate both near their bounds.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config

# ---------------------------------------------------------------------------------------------
# PRE-COMMITTED ROOT-SEARCH PROTOCOL — fixed before the first evaluation.
# ---------------------------------------------------------------------------------------------
PROTOCOL_VERSION = "1.2"   # see AMENDMENT history below

# Calibration seeds. Disjoint from BOUND_SETTING (9009-9016) and from the superseded development
# seeds (9001-9008): the floor is SELECTED here, so it may not also be JUDGED here.
CALIBRATION_SEEDS = (8001, 8002)

GRID_START = 1.165          # below the interpolated r* ~ 1.175
GRID_STOP = 1.200           # above it, with room to fail upward
GRID_STEP = 0.005           # search resolution == tolerance on r*
N_PER_EVALUATION = 1200     # scenes per calibration seed per grid point

# r* is the SMALLEST grid point satisfying F >= R(F). Tolerance is one grid step.
TOLERANCE = GRID_STEP

# Operating margin above the root, ruled 2026-07-20. Deliberately small: the point of the root
# search is the MINIMAL self-consistent floor, so the margin covers grid resolution, not comfort.
MARGIN_ABS = 0.005
MARGIN_ROUND_DP = 3         # rounded OUTWARD (up, it is a lower bound)


def r_operating(r_star: float) -> float:
    """r_op = r* + 0.005, rounded outward (up) to 3 dp."""
    factor = 10**MARGIN_ROUND_DP
    return math.ceil((r_star + MARGIN_ABS) * factor) / factor


def grid() -> list[float]:
    n = int(round((GRID_STOP - GRID_START) / GRID_STEP)) + 1
    return [round(GRID_START + i * GRID_STEP, 4) for i in range(n)]


def _write_probe_config(base: dict, floor: float, seed: int, path: Path) -> None:
    cfg = copy.deepcopy(base)
    cfg.pop("cue_constants", None)
    cfg["experiment"] = f"rootsearch_F{floor:.4f}_s{seed}"
    cfg["output"]["set_name"] = f"rootsearch_F{floor:.4f}_s{seed}"
    cfg["seed"] = seed
    cfg["render"]["cycles_seed"] = seed
    cfg["constraints"]["min_depth_ratio"] = floor
    path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")


def placement_failure_counts(base: dict, floor: float) -> dict:
    """Placement failures per calibration seed at this floor. RECORDED, not a gate.

    AMENDMENT HISTORY — both steps kept visible, because the first one was wrong.

    v1.1 (superseded): after F = 1.1650 / seed 8002 crashed the search on an un-placeable image, I
    made any placement failure mark a grid point INFEASIBLE, arguing it could only push r* upward
    and so could not bias the result favourably.

    v1.2 (current): that rule is WRONG, and measuring it said so. The feasibility map came out
    NON-MONOTONE (1.165 fail, 1.170 ok, 1.175 fail, 1.180 ok, 1.185 fail), which is not how a
    property of F behaves. Measured rate over 6 seeds x 1200 per floor:

        F=1.1650  0.028%    F=1.1950  0.000%
        F=1.1750  0.028%    F=1.2320  0.014%
        F=1.1850  0.014%    F=1.8500  0.028%

    Flat across the whole range INCLUDING the old six-category floor 1.85 — a background rate of
    ~0.02%, independent of the floor. Gating on a 1-in-2400 event would make r* depend on a
    placement coin-flip rather than on the design. So placement is NOT a floor-selection criterion;
    calibration runs tolerate a skipped image and the counts are recorded.

    ⚠ The failures are still a REAL operational defect, just a separate one — see
    `reports/m4a_placement_background_rate.md`. More attempts does not fix them (500 -> 2 failures,
    2000 -> 1, 8000 -> 1): like the dropped 0.2 m bin, specific factor combinations are structurally
    un-placeable rather than unlucky.
    """
    out = {}
    for seed in CALIBRATION_SEEDS:
        cfg = copy.deepcopy(base)
        cfg.pop("cue_constants", None)
        cfg["n_images"] = N_PER_EVALUATION
        cfg["constraints"]["min_depth_ratio"] = floor
        failures: list[dict] = []
        build_scene_specs(
            cfg, seed, raise_on_placement_failure=False, placement_failures=failures
        )
        out[seed] = len(failures)
    return out


def requirement_at(base: dict, floor: float, work: Path, data_root: Path) -> dict:
    """R(F) = worst-case derived area requirement at floor F, WORST CASE over calibration seeds.

    Worst case over seeds, not mean: this is a constructed quantity (AGENTS.md rule 7 clause 1).
    """
    failures = placement_failure_counts(base, floor)   # recorded, NOT a gate (see v1.2)
    per_seed = {}
    for seed in CALIBRATION_SEEDS:
        cfg_path = work / f"rs_F{floor:.4f}_s{seed}.yaml"
        _write_probe_config(base, floor, seed, cfg_path)
        out_dir = data_root / "measurements" / f"rootsearch_F{floor:.4f}_s{seed}"
        if not (out_dir / "annotations.jsonl").exists():
            subprocess.run(
                [
                    "uv", "run", "--extra", "stimuli", "scripts/measure_silhouettes.py",
                    "--config", str(cfg_path), "--n", str(N_PER_EVALUATION),
                    "--out", str(out_dir), "--allow-placement-failures",
                ],
                check=True, capture_output=True,
            )
        report_path = work / f"rs_F{floor:.4f}_s{seed}.json"
        subprocess.run(
            [
                "uv", "run", "--extra", "analysis", "scripts/derive_cue_constants.py",
                "--set", str(out_dir), "--json", str(report_path),
            ],
            check=True, capture_output=True,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        per_seed[seed] = float(report["pooled"]["worst_case_binding_ratio"])
    return {
        "floor": floor,
        "requirement": max(per_seed.values()),   # WORST case over calibration seeds
        "per_seed": per_seed,
        "self_consistent": floor >= max(per_seed.values()),
        "placement_failures": failures,
        "infeasible_reason": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--json")
    ap.add_argument("--work", default=None, help="scratch dir for probe configs/reports")
    args = ap.parse_args()

    import os

    data_root = Path(os.environ["DATA_ROOT"])
    work = Path(args.work) if args.work else Path("/tmp/sbind_rootsearch")
    work.mkdir(parents=True, exist_ok=True)
    base = load_config(args.config)

    print(f"ROOT SEARCH protocol v{PROTOCOL_VERSION}")
    print(f"  calibration seeds : {CALIBRATION_SEEDS}   n = {N_PER_EVALUATION} each")
    print(f"  grid              : {GRID_START} .. {GRID_STOP} step {GRID_STEP}")
    print(f"  tolerance on r*   : {TOLERANCE}")
    print(f"  margin            : r_op = r* + {MARGIN_ABS}, rounded up to {MARGIN_ROUND_DP} dp\n")
    print(f"  {'floor F':>9s} {'R(F)':>9s} {'F - R(F)':>10s}  self-consistent")

    evaluations = []
    r_star = None
    for floor in grid():
        ev = requirement_at(base, floor, work, data_root)
        evaluations.append(ev)
        print(
            f"  {floor:9.4f} {ev['requirement']:9.4f} {floor - ev['requirement']:+10.4f}  "
            f"{'YES' if ev['self_consistent'] else 'no':>15s}  "
            f"placement-skips {sum(ev['placement_failures'].values())}"
        )
        if ev["self_consistent"] and r_star is None:
            r_star = floor
            break   # grid ascends, so the first self-consistent point IS the minimal one

    if r_star is None:
        print("\n  *** NO self-consistent floor in the grid — widen GRID_STOP and re-run")
        result = {"r_star": None, "evaluations": evaluations}
    else:
        r_op = r_operating(r_star)
        print(f"\n  r*   (minimal self-consistent, +/- {TOLERANCE}) : {r_star:.4f}")
        print(f"  r_op (= r* + {MARGIN_ABS}, rounded up)          : {r_op:.4f}")
        print("\n  NEXT: the joint acceptance test — r_op must ALSO clear its own re-derived")
        print("  requirement AND satisfy the check A-C design-selection bounds.")
        result = {"r_star": r_star, "r_operating": r_op, "evaluations": evaluations}

    result["protocol"] = {
        "version": PROTOCOL_VERSION,
        "calibration_seeds": list(CALIBRATION_SEEDS),
        "grid": [GRID_START, GRID_STOP, GRID_STEP],
        "tolerance": TOLERANCE,
        "n_per_evaluation": N_PER_EVALUATION,
        "margin_abs": MARGIN_ABS,
        "margin_round_dp": MARGIN_ROUND_DP,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
