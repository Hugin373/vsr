"""Cumulative extrema ledger — the operative R, monotone non-decreasing by construction.

    uv run --extra analysis scripts/cumulative_extrema_ledger.py \
        --json reports/m4a_cumulative_ledger.json

WHY PER-PASS R WAS WRONG (ruled 2026-07-21, supersedes the per-pass numbers)

The reported sequence R = 1.2072 -> 1.2060 -> 1.2026 looked like convergence from above. It is
not: it is an artifact of NON-NESTED GRIDS. Pass 2 sampled depth x lateral at 10 x 4 where pass 0
sampled 6 x 2, and those point sets barely overlap — so each pass RE-ROLLS the extrema from
scratch and can easily miss a pose an earlier pass happened to hit. A per-pass extremum is the max
over that pass's sample, and the max over a *different* sample is free to be lower.

Over the UNION of all admitted evaluated poses, the extrema can only widen, so

    R_cumulative is MONOTONE NON-DECREASING.

That is the quantity with a defensible interpretation: a lower bound on the true worst case that
improves as evidence accumulates. A decreasing R was never evidence of convergence; it was
evidence of forgetting.

Two consequences the ledger implements:

1. **Every evaluation counts** — grid sweeps, random verification, targeted adversarial probes,
   and (later) optimizer calls all deposit into the same extrema set.
2. **Verification VIOLATIONS ARE DATA, not just failures.** The ten load-bearing exceedances are
   guard-admitted, measured poses; their C_a values belong in the extrema set with provenance.
   Counting them only as "10 failures" throws away the very measurements that prove the envelope
   too narrow.

Extrema of a union are the min/max of the per-source extrema, so per-pass summaries suffice for
sweeps whose per-pose records were not retained.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# Every source that has ever evaluated an admitted pose. Adding a pass means adding a line here.
SOURCES = [
    ("pass0_grid_d6_l2", "reports/m4a_deterministic_extremes.json"),
    ("pass1_grid_d8_l3", "reports/m4a_deterministic_extremes_refine1.json"),
    ("pass2_grid_d10_l4", "reports/m4a_deterministic_extremes_pass2.json"),
    ("pass3_perrole_n21_f12", "reports/m4a_deterministic_extremes_pass3.json"),
]


def _fold(ledger: dict, key: str, lo: float, hi: float, n: int, source: str) -> None:
    cur = ledger.setdefault(
        key, {"min": math.inf, "max": -math.inf, "n": 0, "min_source": None, "max_source": None}
    )
    if lo < cur["min"]:
        cur["min"], cur["min_source"] = lo, source
    if hi > cur["max"]:
        cur["max"], cur["max_source"] = hi, source
    cur["n"] += n


def build_ledger() -> dict:
    ledger: dict[str, dict] = {}
    provenance: list[dict] = []

    for name, path in SOURCES:
        p = Path(path)
        if not p.exists():
            continue
        rep = json.loads(p.read_text(encoding="utf-8"))
        for key, (lo, hi, n) in rep["extremes"].items():
            _fold(ledger, key, float(lo), float(hi), int(n), name)
        provenance.append({"source": name, "path": path, "kind": "grid sweep",
                           "per_pass_R": rep.get("deterministic_R")})

        # VIOLATIONS ARE EVIDENCE. Each exceedance is a measured, guard-admitted pose whose value
        # fell outside the swept envelope — precisely the datum that widens it.
        for vname in ("targeted_verification", "random_verification"):
            v = rep.get(vname) or {}
            for e in v.get("exceedances", []) + v.get("load_bearing_exceedances", []):
                key = f"{e['constant']}_{e['category']}_{e['role']}"
                val = float(e["value"])
                _fold(ledger, key, val, val, 1, f"{name}:{vname}")
            if v:
                provenance.append({
                    "source": f"{name}:{vname}", "kind": "verification",
                    "n_objects_checked": v.get("n_objects_checked"),
                    "n_exceeding": v.get("n_exceeding"),
                    "n_load_bearing": v.get("n_exceeding_load_bearing"),
                })
    return {"ledger": ledger, "provenance": provenance}


# Raw per-pose records that can be RE-BUCKETED under corrected role logic (they carry depth +
# world_y). Passes 0/1 are summary-only and were bucketed under the buggy predicate, so they
# cannot be re-classified; they are coarser and subsumed by pass 3 over the same region, so the
# corrected baseline EXCLUDES them — dropping possibly-misclassified extrema rather than trusting
# them (conservative in the safe direction).
RAW_RECORD_SOURCES = [
    ("pass2_records", "pass2_records.jsonl"),
    ("pass3_records", "pass3_records.jsonl"),
]


def _corrected_roles(depth: float, world_y: float, ranges: dict, tol: float) -> list[str]:
    """The FIXED role predicate: boundary tolerance absorbs grid-endpoint rounding."""
    return [
        r for r, v in ranges.items()
        if v["depth"][0] - tol <= depth <= v["depth"][1] + tol
        and v["y"][0] - tol <= world_y <= v["y"][1] + tol
    ]


def rebuild_from_raw(data_root, config) -> dict:
    """Rebuild the extrema ledger from RAW poses under corrected role classification.

    The bug was a bucketing bug, not a renderer bug: C_a was measured correctly and mis-filed.
    So the whole ledger must be re-derived by re-applying the corrected predicate to every raw
    pose — the current R = 1.2167 is not trusted until it reproduces here (advisor, 2026-07-21).
    """
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, "scripts")
    from deterministic_cue_extremes import ROLE_BOUNDARY_TOL, reachable_ranges

    ranges = reachable_ranges(config)
    ledger: dict[str, dict] = {}
    reclassified = 0
    total = 0
    for name, fname in RAW_RECORD_SOURCES:
        path = _Path(data_root) / "measurements" / fname
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                total += 1
                roles = _corrected_roles(rec["depth"], rec["world_y"], ranges, ROLE_BOUNDARY_TOL)
                if roles != rec.get("roles_ok"):
                    reclassified += 1
                for role in roles:
                    key = f"area_{rec['category']}_{role}"
                    ca = float(rec["C_a"])
                    _fold(ledger, key, ca, ca, 1, name)
                    hk = f"height_{rec['category']}_{role}"
                    ch = float(rec["C_h"])
                    _fold(ledger, hk, ch, ch, 1, name)
    return {"ledger": ledger, "n_poses": total, "n_reclassified": reclassified, "ranges": ranges}


def required_ratio_from_ledger(ledger: dict) -> tuple[float, str, dict]:
    """R = max over pairings of sqrt(C_a[far]^max / C_a[near]^min), on the cumulative extrema."""
    cats = sorted({k.split("_")[1] for k in ledger if k.startswith("area_")})
    best, best_key, table = 0.0, "", {}
    for near in cats:
        nk = f"area_{near}_near"
        if nk not in ledger:
            continue
        for far in cats:
            fk = f"area_{far}_far"
            if fk not in ledger:
                continue
            r = math.sqrt(ledger[fk]["max"] / ledger[nk]["min"])
            table[f"near_{near}_far_{far}"] = r
            if r > best:
                best, best_key = r, f"near_{near}_far_{far}"
    return best, best_key, table


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json")
    ap.add_argument("--from-raw", action="store_true",
                    help="rebuild from RAW poses under corrected role classification (baseline)")
    args = ap.parse_args()

    if args.from_raw:
        import os

        from sbind.utils.config import load_config
        cfg = load_config("configs/m4a_v1_natural_congruent_pilot.yaml")
        rb = rebuild_from_raw(os.environ["DATA_ROOT"], cfg)
        led = rb["ledger"]
        # fold in verification exceedances (role fixed a priori, full coords) from the pass JSONs
        for _name, path in SOURCES:
            pp = Path(path)
            if not pp.exists():
                continue
            rep = json.loads(pp.read_text(encoding="utf-8"))
            for vname in ("targeted_verification", "random_verification"):
                v = rep.get(vname) or {}
                for e in v.get("exceedances", []) + v.get("load_bearing_exceedances", []):
                    k = f"{e['constant']}_{e['category']}_{e['role']}"
                    _fold(led, k, float(e["value"]), float(e["value"]), 1, f"{_name}:{vname}")
        R, binding, table = required_ratio_from_ledger(led)
        print("CORRECTED-BASELINE LEDGER (raw poses re-bucketed, tol applied)")
        print(f"  poses re-bucketed: {rb['n_reclassified']} of {rb['n_poses']} changed role")
        for key in sorted(led):
            if key.startswith("area_"):
                e = led[key]
                print(f"  {key:22s} {e['min']:12.1f} {e['max']:12.1f}  n={e['n']}")
        print(f"\n  CORRECTED-BASELINE R = {R:.4f}  (binding {binding})")
        out = {"corrected_baseline_R": R, "binding_pairing": binding,
               "n_poses": rb["n_poses"], "n_reclassified": rb["n_reclassified"],
               "ledger": {k: v for k, v in sorted(led.items())},
               "required_ratio_by_pairing": table}
        if args.json:
            Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
            print(f"\nwrote {args.json}")
        return 0

    built = build_ledger()
    ledger = built["ledger"]
    R, binding, table = required_ratio_from_ledger(ledger)

    print("CUMULATIVE EXTREMA LEDGER — union of every admitted evaluated pose\n")
    print(f"  {'cell':22s} {'min':>12s} {'max':>12s} {'n':>8s}  {'min from':>28s}")
    for key in sorted(ledger):
        if not key.startswith("area_"):
            continue
        e = ledger[key]
        print(f"  {key:22s} {e['min']:12.1f} {e['max']:12.1f} {e['n']:8d}  {e['min_source']:>28s}")

    print(f"\n  CUMULATIVE R = {R:.4f}   (binding pairing: {binding})")
    print("  monotone non-decreasing by construction — a LOWER BOUND on the true worst case\n")

    print("  per-pass R, for contrast (each a max over its OWN sample, hence non-monotone):")
    for p in built["provenance"]:
        if p.get("per_pass_R"):
            print(f"    {p['source']:24s} {p['per_pass_R']:.4f}")

    out = {
        "cumulative_R": R,
        "binding_pairing": binding,
        "ledger": {k: v for k, v in sorted(ledger.items())},
        "required_ratio_by_pairing": table,
        "provenance": built["provenance"],
        "note": (
            "Per-pass R is superseded. Non-nested grids re-roll extrema each pass, so a falling "
            "per-pass R reflects forgetting, not convergence. eps_R applies to THIS sequence."
        ),
    }
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
