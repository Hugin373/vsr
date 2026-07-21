"""Solo camera-envelope calibration — which envelope breaks the position<->depth coupling?

    uv run --extra stimuli scripts/solo_camera_calibration.py --n 300 \
        --json reports/m4a_solo_camera_calibration.json

Targets are PRE-COMMITTED in docs/M4A_SOLO_PROTOCOL.md (commit 3c44222, before any candidate ran):
    HARD      R2(B0_position)      <= 0.60
    DESIRABLE R2(B0 u B2)          <= 0.70
    DESIRABLE R2(B0 u B1 u B2)     <= 0.90

Judged on RENDERED silhouettes, never an analytic proxy: the proxy was wrong twice
(r(z,retinal) -0.575 -> -0.705 rendered; r(z,elevation) -0.747 -> -0.882).

Uses the ID-pass-only measurement path (~0.17 s/scene vs ~3 s for a beauty render) — the B0/B1
features are all silhouette geometry, and elevation is the projected ground-contact point, computed
exactly from the camera matrices rather than measured.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import cross_val_score

from sbind.stimuli import geometry
from sbind.stimuli.sampler import build_solo_scene_specs
from sbind.utils.config import load_config

CANDIDATES = {
    "current":            {"height_m": [-0.16, 0.16], "pitch_deg": [-3.0, 3.0]},
    "wider_pitch":        {"height_m": [-0.16, 0.16], "pitch_deg": [-9.0, 9.0]},
    "wider_height":       {"height_m": [-0.60, 0.60], "pitch_deg": [-3.0, 3.0]},
    "wider_pitch_height": {"height_m": [-0.60, 0.60], "pitch_deg": [-9.0, 9.0]},
}
HARD_B0 = 0.60
DESIRABLE_B0B2 = 0.70
DESIRABLE_ALL = 0.90


def measure(config: dict, n: int, seed: int = 420) -> dict:
    from sbind.stimuli import render_bpy as rb

    cfg = copy.deepcopy(config)
    cfg["n_images"] = n
    fails: list[dict] = []
    specs = build_solo_scene_specs(cfg, seed, raise_on_placement_failure=False,
                                   placement_failures=fails)
    tmp = Path("/tmp/solo_calib_id.png")
    rows, trunc = [], 0
    for s in specs:
        scene = rb._reset_scene()
        ground = rb._add_ground(s.ground_color)
        objs = [rb._add_object(o, 0) for o in s.objects]
        K, R, t = rb._add_camera(scene, s)
        sun = rb._add_sun(scene, s)
        rb._configure_beauty(scene, cfg["render"])
        masks = rb._render_id_pass(scene, objs, ground, [sun], tmp)
        if tmp.exists():
            tmp.unlink()
        mg = rb._mask_geometry(masks[0])
        if mg is None:
            continue
        bbox, height = mg
        o = s.objects[0]
        p = np.asarray(o.pos_world, dtype=float)
        depth = float(geometry.project(K, R, t, p)[2])
        # elevation = projected GROUND-CONTACT point (the strong cue; exact from the matrices)
        elev = float(geometry.project(K, R, t, np.array([p[0], p[1], 0.0]))[1])
        res_x, res_y = s.camera.res_x, s.camera.res_y
        if bbox[0] <= 0 or bbox[1] <= 0 or bbox[2] >= res_x or bbox[3] >= res_y:
            trunc += 1
        rows.append({
            "z": depth, "cat": o.category, "size_m": o.size_m,
            "mult": float(s.factors["size_multiplier"]),
            "u": (bbox[0] + bbox[2]) / 2, "v": (bbox[1] + bbox[3]) / 2,
            "bl": bbox[0], "bt": bbox[1], "br": res_x - bbox[2], "bb": res_y - bbox[3],
            "elev": elev, "retinal": height, "area": int(masks[0].sum()),
            "w": bbox[2] - bbox[0], "h": bbox[3] - bbox[1],
        })
    return {"rows": rows, "placement_failures": len(fails), "truncated": trunc}


def r2(rows: list[dict], keys: list[str], onehot: np.ndarray | None = None) -> float:
    z = np.array([r["z"] for r in rows])
    parts = []
    if keys:
        parts.append(np.array([[r[k] for k in keys] for r in rows], dtype=float))
    if onehot is not None:
        parts.append(onehot)
    X = np.hstack(parts)
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    return float(
        cross_val_score(RidgeCV(alphas=np.logspace(-3, 3, 13)), X, z, cv=5, scoring="r2").mean()
    )


# ⚠ B0 must be PURE position. Border distances are NOT position-only: bl = bbox_x0 and
# br = res_x - bbox_x1, so bl + br determines the bbox WIDTH, and bt + bb the height. Including
# all four smuggles apparent size into the "position" baseline and inflates R2(B0). Caught
# 2026-07-21 while reading the first calibration result. Centroid + ground-contact elevation are
# the position information; extent belongs to B1.
B0 = ["u", "v", "elev"]                              # projected POSITION only
B1 = ["retinal", "area", "w", "h"]                   # appearance / apparent size (extent)
B2 = ["size_m", "mult"]                              # semantic priors (+ category one-hot)
B0_CONTAMINATED = ["u", "v", "bl", "bt", "br", "bb", "elev"]   # kept to report the inflation


def overlap_p_v_given_z(rows: list[dict], n_bins: int = 5) -> float:
    """Min pairwise overlap of p(image v | depth bin). Low => bins separable by v alone."""
    z = np.array([r["z"] for r in rows])
    v = np.array([r["v"] for r in rows])
    edges = np.quantile(z, np.linspace(0, 1, n_bins + 1))
    groups = [v[(z >= edges[i]) & (z <= edges[i + 1])] for i in range(n_bins)]
    grid = np.linspace(v.min(), v.max(), 40)
    ov = []
    for i in range(n_bins):
        for j in range(i + 1, n_bins):
            a, b = groups[i], groups[j]
            if a.size < 5 or b.size < 5:
                continue
            ha, _ = np.histogram(a, bins=grid, density=True)
            hb, _ = np.histogram(b, bins=grid, density=True)
            ov.append(float(np.minimum(ha, hb) @ np.diff(grid)))
    return float(min(ov)) if ov else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--json")
    args = ap.parse_args()

    base = load_config("configs/m4a_v1_solo.yaml")
    print(f"SOLO CAMERA CALIBRATION — n={args.n} per candidate, RENDERED measurements")
    print(f"  pre-committed: R2(B0)<={HARD_B0} HARD, R2(B0uB2)<={DESIRABLE_B0B2}, "
          f"R2(all)<={DESIRABLE_ALL}\n")
    print(f"  {'candidate':20s} {'R2(B0)':>8s} {'R2(B1)':>8s} {'B0uB2':>8s} {'all':>8s} "
          f"{'r(z,ret)':>9s} {'r(z,v)':>8s} {'ovlp':>6s} {'trunc':>6s} {'fail':>5s}")
    out = {}
    for name, jitter in CANDIDATES.items():
        cfg = copy.deepcopy(base)
        cfg["camera"]["jitter"].update(jitter)
        m = measure(cfg, args.n)
        rows = m["rows"]
        cats = sorted({r["cat"] for r in rows})
        onehot = np.array([[r["cat"] == c for c in cats] for r in rows], dtype=float)
        z = np.array([r["z"] for r in rows])
        rec = {
            "jitter": jitter,
            "R2_B0_position": r2(rows, B0),
            "R2_B0_contaminated": r2(rows, B0_CONTAMINATED),
            "R2_B1_appearance": r2(rows, B1),
            "R2_B0_B2": r2(rows, B0 + B2, onehot),
            "R2_all": r2(rows, B0 + B1 + B2, onehot),
            "r_z_retinal": float(np.corrcoef(z, [r["retinal"] for r in rows])[0, 1]),
            "r_z_v": float(np.corrcoef(z, [r["v"] for r in rows])[0, 1]),
            "overlap_p_v_given_z": overlap_p_v_given_z(rows),
            "truncated": m["truncated"], "placement_failures": m["placement_failures"],
            "n": len(rows), "depth_range": [float(z.min()), float(z.max())],
        }
        out[name] = rec
        print(f"  {name:20s} {rec['R2_B0_position']:8.3f} {rec['R2_B0_contaminated']:8.3f} "
              f"{rec['R2_B1_appearance']:8.3f} {rec['R2_B0_B2']:8.3f} {rec['R2_all']:8.3f} "
              f"{rec['r_z_v']:8.3f} {rec['overlap_p_v_given_z']:6.3f} {rec['truncated']:6d}")

    print("\n  verdict vs PRE-COMMITTED targets:")
    for name, rec in out.items():
        ok = rec["R2_B0_position"] <= HARD_B0
        print(f"    {name:20s} R2(B0)={rec['R2_B0_position']:.3f} "
              f"{'PASS' if ok else 'FAIL'} (hard <= {HARD_B0})")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
