"""§3 pre-freeze decision gate: resolve B2→depth coupling at scale (advisor finalization). [CPU]

    uv run --extra analysis scripts/dryrun_factor_coupling.py --config configs/m4a_v1_..._pilot.yaml

The pilot's B2→z ≈ 0.26 (identity priors predicting depth) could be small-sample noise (n=60) or a
real design-level imbalance — the class of the 55.1% shape-only failure. Resolve it BEFORE the
freeze by DRY-RUNNING the sampler for ~10,000 scene configs (NO rendering) and measuring on the
sampled factors:
  * B2 → depth R²  (category/colour/physical-size one-hots → camera-frame depth),
  * P(near/far role | category)  and  P(depth-bin | category),
  * the category × size_condition × depth-bin contingency.

VERDICT: ≈0 at n=10k ⇒ the pilot was small-sample; close the watch item. Nonzero ⇒ the ordered
(near,far)-pair category balancing (proposal §2.3) is not holding — fix the sampler + add a
regression test BEFORE any freeze work. Never absorb a design imbalance with B2 adjustment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.probes.ridge import ridge_probe
from sbind.stimuli import geometry
from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config
from sbind.utils.io import write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.dryrun")


def _rows(specs):
    """One row per TARGET object: category, colour, size_m, camera-frame depth, role, depth bin."""
    rows = []
    for s in specs:
        c = s.camera
        _, R, t, _ = geometry.camera_frame(
            c.pos_world, c.target_world, c.f_mm, c.sensor_width_mm, c.res_x, c.res_y
        )
        R, t = np.asarray(R, float), np.asarray(t, float).ravel()
        closer = s.factors["closer_object"]
        for idx in s.factors.get("target_object_indices", [0, 1]):
            o = s.objects[idx]
            depth = float((R @ np.asarray(o.pos_world, float) + t)[2])
            rows.append({
                "category": o.category,
                "colour": o.name.split("_")[0],
                "size_m": float(o.size_m),
                "depth": depth,
                "role": "near" if idx == closer else "far",
                "depth_bin": int(s.factors["near_depth_bin"]),
                "size_condition": s.factors.get("size_condition", "?"),
            })
    return rows


def _b2_matrix(rows):
    cats = sorted({r["category"] for r in rows})
    cols = sorted({r["colour"] for r in rows})
    X = np.array([
        [1.0 * (r["category"] == c) for c in cats]
        + [1.0 * (r["colour"] == c) for c in cols]
        + [r["size_m"]]
        for r in rows
    ])
    return X


def main() -> int:
    ap = argparse.ArgumentParser(description="§3 dry-run: B2→depth coupling at scale (no render).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--attempts", type=int, help="override target_placement_attempts (speed)")
    ap.add_argument("--out")
    args = ap.parse_args()

    config = load_config(args.config)
    config = {**config, "n_images": args.n}
    if args.attempts:
        config["condition"] = {
            **config.get("condition", {}), "target_placement_attempts": args.attempts
        }
    specs = build_scene_specs(config, int(config["seed"]), raise_on_placement_failure=False)
    rows = _rows(specs)
    depth = np.array([r["depth"] for r in rows])
    placed_rate = len(specs) / args.n
    print(f"config: {args.config}  requested={args.n}  PLACED={len(specs)} "
          f"({placed_rate:.3f})  target objects={len(rows)}")
    print(f"  depth range [{depth.min():.2f}, {depth.max():.2f}] m")
    if placed_rate < 0.99:
        print(f"  ⚠ PLACEMENT: {args.n - len(specs)} of {args.n} un-placeable at 500 attempts "
              f"({1 - placed_rate:.1%}) — a FREEZE issue (would crash the 1k render).")
    print()

    b2_r2 = ridge_probe(_b2_matrix(rows), depth, "B2->depth").value
    print(f"  B2 → depth R² (category+colour+size_m, 5-fold CV) = {b2_r2:+.4f}")

    # P(role | category) — should be ~0.5/0.5 if the ordered-pair balancing holds
    print("\n  P(near | category)   [balanced ⇒ ~0.500]")
    role_by_cat = {}
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        p_near = sum(r["role"] == "near" for r in sub) / len(sub)
        role_by_cat[cat] = p_near
        flag = "  ⚠" if abs(p_near - 0.5) > 0.05 else ""
        print(f"    {cat:10s} {p_near:.3f}  (n={len(sub)}){flag}")

    # P(depth-bin | category) spread — does category shift the depth distribution?
    depth_by_cat = {c: np.mean([r["depth"] for r in rows if r["category"] == c])
                    for c in sorted({r["category"] for r in rows})}
    spread = max(depth_by_cat.values()) - min(depth_by_cat.values())
    print(f"\n  mean depth by category spans {spread:.3f} m  "
          f"(min {min(depth_by_cat.values()):.2f} → max {max(depth_by_cat.values()):.2f})")

    worst_role = max(abs(v - 0.5) for v in role_by_cat.values())
    verdict = "CLEAN" if (b2_r2 < 0.02 and worst_role < 0.05) else "COUPLED"
    print(f"\n  ⇒ VERDICT: {verdict}"
          + (" — B2→depth ≈ 0 and roles balanced; the pilot 0.26 was small-sample. Close it."
             if verdict == "CLEAN" else
             " — real design coupling; FIX the sampler's (near,far) category balancing + test "
             "BEFORE the freeze (do NOT absorb it in analysis)."))
    if args.out:
        write_json({"b2_depth_r2": b2_r2, "p_near_by_category": role_by_cat,
                    "mean_depth_by_category": depth_by_cat, "worst_role_imbalance": worst_role,
                    "verdict": verdict, "n_images": len(specs)}, Path(args.out))
        log.info("wrote -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
