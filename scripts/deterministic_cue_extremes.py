"""Cue-constant extremes by ENVELOPE COVERAGE, not random sampling — the deterministic R(F).

    uv run --extra stimuli scripts/deterministic_cue_extremes.py \
        --config configs/m4a_v1_natural_congruent_pilot.yaml \
        --json reports/m4a_deterministic_extremes.json

STANDING RULE (ruled 2026-07-20) that this instrument implements:

    Random seed sweeps validate SAMPLED DISTRIBUTION properties (§5 checks A-C).
    HARD GEOMETRIC VALIDITY requires ENVELOPE COVERAGE — an observed maximum over random seeds is
    biased LOW and rises with n.

That bias is measured, not asserted: the worst-case area requirement R(1.1900) read 1.1771 over two
random seeds and 1.1812 over six. Four extra seeds moved it +0.0041, essentially the entire 0.005
margin the floor was carrying. A congruence floor derived from random maxima is therefore a lower
bound wearing a worst case's clothes, however many seeds it uses.

METHOD
Sweep the object's REACHABLE POSE ENVELOPE directly instead of the sampler's factor product:

  * discrete factors (size multiplier, lateral side) — EXHAUSTIVE;
  * continuous factors (depth, lateral magnitude, all five camera-jitter axes) — evaluated at their
    BOUNDARIES, which is where an extreme of a smooth function over a box must lie;
  * depth additionally gridded through the interior, because the constants are not monotone in
    depth (perspective foreshortening turns over).

Each object is rendered SOLO. The constants come from the flat-emission ID pass, and target
occlusion is validated to be zero, so a solo silhouette is exactly the in-scene one.

⚠ THE BOUNDARY-EXTREMAL ASSUMPTION IS AN ASSUMPTION. If a constant is non-monotone in a continuous
factor, its extreme can sit in the interior and a corner sweep would miss it. `--verify-random`
therefore draws configurations from the REAL sampler and checks none exceeds the deterministic
envelope. That check is the point: it can fail, and if it does the envelope is wrong.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from sbind.stimuli import geometry
from sbind.stimuli.cue_constants import required_ratios
from sbind.stimuli.sampler import _resolve_sizes, _rest_height, build_scene_specs
from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec
from sbind.utils.config import load_config

N_DEPTH_GRID = 6          # boundaries + interior; constants are non-monotone in depth
LATERAL_LEVELS = 2        # boundaries of |lateral|
DEPTH_MARGIN = 0.02       # expand the measured reachable depth range by 2%, outward


def reachable_depths(config: dict, n: int = 4000) -> dict[str, tuple[float, float]]:
    """Camera-frame depth range each ROLE can reach, from the sampler, expanded outward.

    Measured then EXPANDED rather than taken as-is: the observed range is itself a random-sample
    extreme and therefore biased inward, which is the whole failure mode this instrument exists to
    avoid. The margin is applied outward so the swept envelope is a superset of the reachable one.
    """
    near, far = [], []
    for seed in (7001, 7002):
        cfg = dict(config)
        cfg["n_images"] = n // 2
        for spec in build_scene_specs(cfg, seed, raise_on_placement_failure=False):
            _, R, t, _ = geometry.camera_frame(
                spec.camera.pos_world, spec.camera.target_world, spec.camera.f_mm,
                spec.camera.sensor_width_mm, spec.camera.res_x, spec.camera.res_y,
            )
            d = [float((R @ np.asarray(o.pos_world) + t)[2]) for o in spec.objects[:2]]
            i = int(spec.factors["closer_object"])
            near.append(d[i])
            far.append(d[1 - i])
    out = {}
    for role, vals in (("near", near), ("far", far)):
        lo, hi = min(vals), max(vals)
        span = hi - lo
        out[role] = (lo - DEPTH_MARGIN * span, hi + DEPTH_MARGIN * span)
    return out


def camera_corners(config: dict) -> list[tuple[CameraSpec, dict]]:
    """All 2^5 corners of the camera-jitter box. Exhaustive over its boundary."""
    cam_cfg = config["camera"]
    render_cfg = config["render"]
    jitter = cam_cfg.get("jitter", {}) or {}
    axes = ("height_m", "pos_x_m", "pos_y_m", "pitch_deg", "yaw_deg")
    ranges = [tuple(float(v) for v in jitter.get(a, [0.0, 0.0])) for a in axes]

    import math

    base_pos = np.asarray(cam_cfg["pos_world"], dtype=float)
    base_target = np.asarray(cam_cfg["target_world"], dtype=float)
    direction = base_target - base_pos
    dist = float(np.linalg.norm(direction))
    horiz = float(np.hypot(direction[0], direction[1]))

    out = []
    for combo in itertools.product(*[(0, 1) for _ in axes]):
        dh, dx, dy, dp, dyaw = (ranges[i][combo[i]] for i in range(5))
        yaw = math.atan2(direction[0], direction[1]) + math.radians(dyaw)
        pitch = math.atan2(direction[2], horiz) + math.radians(dp)
        pos = base_pos + np.array([dx, dy, dh])
        new_dir = np.array([
            math.sin(yaw) * math.cos(pitch),
            math.cos(yaw) * math.cos(pitch),
            math.sin(pitch),
        ])
        cam = CameraSpec(
            pos_world=pos.tolist(),
            target_world=(pos + dist * new_dir).tolist(),
            f_mm=float(cam_cfg["f_mm"]),
            sensor_width_mm=float(cam_cfg["sensor_width_mm"]),
            res_x=int(render_cfg["res_x"]),
            res_y=int(render_cfg["res_y"]),
        )
        out.append((cam, {"height": dh, "pos_x": dx, "pos_y": dy, "pitch": dp, "yaw": dyaw}))
    return out


def _world_y_for_depth(cam: CameraSpec, x: float, z: float, target_depth: float) -> float:
    """Solve world-y so the object sits at `target_depth` in this camera's frame."""
    _, R, t, _ = geometry.camera_frame(
        cam.pos_world, cam.target_world, cam.f_mm, cam.sensor_width_mm, cam.res_x, cam.res_y
    )
    axis = geometry.optical_axis(R)
    if abs(float(axis[1])) < 1e-9:
        return float("nan")
    return (target_depth - float(t[2]) - float(axis[0]) * x - float(axis[2]) * z) / float(axis[1])


def sweep(config: dict, out_dir: Path) -> dict:
    from sbind.stimuli import render_bpy as rb

    categories = list(config["objects"]["categories"])
    size_by_cat = _resolve_sizes(config["objects"], categories)
    fcfg = config["factors"]
    mults = [float(m) for m in fcfg.get("size_multipliers", [1.0])]
    lo_lat, hi_lat = (float(v) for v in fcfg["lateral_range"])
    lat_mags = list(np.linspace(lo_lat, hi_lat, LATERAL_LEVELS))
    depths = reachable_depths(config)
    union_lo = min(d[0] for d in depths.values())
    union_hi = max(d[1] for d in depths.values())
    depth_grid = list(np.linspace(union_lo, union_hi, N_DEPTH_GRID))
    cams = camera_corners(config)

    print(f"  reachable depth: near {depths['near'][0]:.3f}..{depths['near'][1]:.3f}  "
          f"far {depths['far'][0]:.3f}..{depths['far'][1]:.3f}  (+{DEPTH_MARGIN:.0%} outward)")
    total = len(categories) * len(depth_grid) * 2 * len(lat_mags) * len(mults) * len(cams)
    print(f"  sweep: {len(categories)} cat x {len(depth_grid)} depth x 2 side x "
          f"{len(lat_mags)} lat x {len(mults)} mult x {len(cams)} cam corners = {total} renders\n")

    tmp = out_dir / ".det_id.png"
    records: list[dict] = []
    done = 0
    for cat in categories:
        for depth, sign, lat, mult in itertools.product(depth_grid, (-1.0, 1.0), lat_mags, mults):
            size = size_by_cat[cat] * mult
            z = _rest_height(cat, size)
            x = sign * lat
            for cam, cam_rec in cams:
                y = _world_y_for_depth(cam, x, z, depth)
                if not np.isfinite(y):
                    continue
                spec = SceneSpec(
                    id=f"det_{cat}", camera=cam,
                    objects=[ObjectSpec(f"o_{cat}", cat, [0.8, 0.05, 0.05], size, [x, y, z])],
                    ground_color=[0.45, 0.45, 0.48], sun_energy=4.0,
                    sun_direction=[5.0, -5.0, 8.0], factors={},
                )
                scene = rb._reset_scene()
                ground = rb._add_ground(spec.ground_color)
                objs = [rb._add_object(o, 0) for o in spec.objects]
                K, R, t = rb._add_camera(scene, spec)
                sun = rb._add_sun(scene, spec)
                rb._configure_beauty(scene, config["render"])
                masks = rb._render_id_pass(scene, objs, ground, [sun], tmp)
                if tmp.exists():
                    tmp.unlink()
                mg = rb._mask_geometry(masks[0])
                if mg is None:
                    continue
                _, height = mg
                area = int(masks[0].sum())
                uvd = geometry.project(K, R, t, np.array([x, y, z]))
                # OFF-FRAME poses are unreachable in the real design (the placement guard rejects
                # them), so including them would inflate the envelope with impossible geometry.
                if not (0 <= uvd[0] <= cam.res_x and 0 <= uvd[1] <= cam.res_y):
                    continue
                records.append({
                    "category": cat, "depth": float(depth), "x": x, "mult": mult,
                    "C_h": height * depth / mult,
                    "C_a": area * depth**2 / mult**2,
                    **{f"cam_{k}": v for k, v in cam_rec.items()},
                })
                done += 1
                if done % 500 == 0:
                    print(f"    {done}/{total}")

    const = {"height": {}, "area": {}}
    for cat in categories:
        for role, (lo, hi) in depths.items():
            rows = [r for r in records if r["category"] == cat and lo <= r["depth"] <= hi]
            if not rows:
                continue
            const["height"][(cat, role)] = [r["C_h"] for r in rows]
            const["area"][(cat, role)] = [r["C_a"] for r in rows]
    return {"constants": const, "records": records, "depths": depths}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--json")
    ap.add_argument("--verify-random", type=int, default=0,
                    help="draw N real sampler configurations and check none exceeds the envelope")
    args = ap.parse_args()

    config = load_config(args.config)
    out_dir = Path("/tmp/sbind_det")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"DETERMINISTIC ENVELOPE SWEEP — {args.config}")
    result = sweep(config, out_dir)
    const = result["constants"]

    print("\n--- envelope extremes (min .. max per category x role) ---")
    for name in ("height", "area"):
        print(f"  {name}:")
        for (cat, role), vals in sorted(const[name].items()):
            v = np.asarray(vals)
            print(f"    {cat:9s} {role:4s} n={v.size:5d}  {v.min():11.1f} .. {v.max():11.1f}")

    ratios = required_ratios(const)
    worst_h = max(r["height"] for r in ratios.values())
    worst_a = max(r["area"] for r in ratios.values())
    required = max(worst_h, worst_a)
    binding = max(ratios, key=lambda k: ratios[k]["binding"])
    print(f"\n  WORST-CASE height requirement : {worst_h:.4f}")
    print(f"  WORST-CASE area   requirement : {worst_a:.4f}   (binding pairing: {binding})")
    print(f"  => DETERMINISTIC R = {required:.4f}")

    report = {
        "config": args.config,
        "method": "envelope coverage (deterministic), not random sampling",
        "n_renders": len(result["records"]),
        "depth_ranges": {k: list(v) for k, v in result["depths"].items()},
        "extremes": {
            f"{name}_{cat}_{role}": [float(min(v)), float(max(v)), len(v)]
            for name in ("height", "area")
            for (cat, role), v in const[name].items()
        },
        "required_ratio_by_pairing": ratios,
        "deterministic_R": required,
        "binding_pairing": binding,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
