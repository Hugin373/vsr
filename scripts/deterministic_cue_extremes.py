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
from sbind.stimuli.sampler import (
    _box_in_frame,
    _projected_box,
    _resolve_sizes,
    _rest_height,
    build_scene_specs,
)
from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec
from sbind.utils.config import load_config

N_DEPTH_GRID = 6          # boundaries + interior; constants are non-monotone in depth
LATERAL_LEVELS = 2        # boundaries of |lateral|

# R = sqrt(max C_a[far] / min C_a[near]). ONLY these two extrema enter it. A violation anywhere
# else is a coverage defect worth fixing but is NOT an error bound on R — which is exactly why the
# x1.02283 shortcut was rejected: it was measured on the near-role MAXIMUM, which R never reads.
LOAD_BEARING = (("area", "near", "min"), ("area", "far", "max"))
DEPTH_MARGIN = 0.02       # expand the measured reachable depth range by 2%, outward


def reachable_ranges(config: dict, n: int = 4000) -> dict[str, dict[str, tuple[float, float]]]:
    """Camera-frame DEPTH and world-Y range each ROLE can reach, from the sampler, expanded outward.

    Measured then EXPANDED rather than taken as-is: the observed range is itself a random-sample
    extreme and therefore biased inward, which is the whole failure mode this instrument exists to
    avoid. The margin is applied outward so the swept envelope is a superset of the reachable one.
    """
    acc = {"near": {"depth": [], "y": []}, "far": {"depth": [], "y": []}}
    for seed in (7001, 7002):
        cfg = dict(config)
        cfg["n_images"] = n // 2
        for spec in build_scene_specs(cfg, seed, raise_on_placement_failure=False):
            _, R, t, _ = geometry.camera_frame(
                spec.camera.pos_world, spec.camera.target_world, spec.camera.f_mm,
                spec.camera.sensor_width_mm, spec.camera.res_x, spec.camera.res_y,
            )
            d = [float((R @ np.asarray(o.pos_world) + t)[2]) for o in spec.objects[:2]]
            y = [float(o.pos_world[1]) for o in spec.objects[:2]]
            i = int(spec.factors["closer_object"])
            acc["near"]["depth"].append(d[i])
            acc["near"]["y"].append(y[i])
            acc["far"]["depth"].append(d[1 - i])
            acc["far"]["y"].append(y[1 - i])
    out = {}
    for role, d in acc.items():
        out[role] = {}
        for key, vals in d.items():
            lo, hi = min(vals), max(vals)
            span = hi - lo
            out[role][key] = (lo - DEPTH_MARGIN * span, hi + DEPTH_MARGIN * span)
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


def sweep(
    config: dict, out_dir: Path, depth_grid_n: int = N_DEPTH_GRID,
    lateral_levels: int = LATERAL_LEVELS,
) -> dict:
    from sbind.stimuli import render_bpy as rb

    categories = list(config["objects"]["categories"])
    size_by_cat = _resolve_sizes(config["objects"], categories)
    fcfg = config["factors"]
    mults = [float(m) for m in fcfg.get("size_multipliers", [1.0])]
    lo_lat, hi_lat = (float(v) for v in fcfg["lateral_range"])
    lat_mags = list(np.linspace(lo_lat, hi_lat, lateral_levels))
    ranges = reachable_ranges(config)
    depths = {r: v["depth"] for r, v in ranges.items()}
    union_lo = min(d[0] for d in depths.values())
    union_hi = max(d[1] for d in depths.values())
    bbox_margin = float(config["condition"]["target_bbox_margin_px"])
    frame_margin = float(config["condition"]["target_frame_margin_px"])
    depth_grid = list(np.linspace(union_lo, union_hi, depth_grid_n))
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
                # ⚠ REACHABILITY, fixed 2026-07-20. The first version admitted any pose whose
                # projected CENTRE was on-screen. Measured: 712/9216 (7.7%) of those poses are
                # REJECTED by the real placement guard — they are edge-clipped, so their
                # silhouettes are truncated, C_a is deflated, and the required ratio is inflated.
                # That produced R = 1.4314 against ~1.18 from random sampling. Apply the SAMPLER'S
                # OWN guard instead: bbox expanded by target_bbox_margin_px must sit inside the
                # frame with target_frame_margin_px.
                candidate = ObjectSpec(f"o_{cat}", cat, [0.8, 0.05, 0.05], size, [x, y, z])
                gbox = _projected_box(cam, candidate, margin_px=bbox_margin)
                if gbox is None or not _box_in_frame(
                    gbox, cam.res_x, cam.res_y, frame_margin
                ):
                    continue
                # role-wise reachability: BOTH the camera-frame depth and the world-y must be
                # inside that role's measured envelope
                roles_ok = [
                    r for r, v in ranges.items()
                    if v["depth"][0] <= depth <= v["depth"][1] and v["y"][0] <= y <= v["y"][1]
                ]
                if not roles_ok:
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
                records.append({
                    "category": cat, "depth": float(depth), "x": x, "mult": mult,
                    "roles_ok": roles_ok, "world_y": float(y),
                    "C_h": height * depth / mult,
                    "C_a": area * depth**2 / mult**2,
                    **{f"cam_{k}": v for k, v in cam_rec.items()},
                })
                done += 1
                if done % 500 == 0:
                    print(f"    {done}/{total}")

    const = {"height": {}, "area": {}}
    for cat in categories:
        for role in ranges:
            rows = [
                r for r in records if r["category"] == cat and role in r["roles_ok"]
            ]
            if not rows:
                continue
            const["height"][(cat, role)] = [r["C_h"] for r in rows]
            const["area"][(cat, role)] = [r["C_a"] for r in rows]
    return {"constants": const, "records": records, "depths": depths, "ranges": ranges}


VERIFY_SEEDS = (6001, 6002)   # dedicated; never used for calibration or bound-setting


def verify_random(config: dict, const: dict, n: int, out_dir: Path) -> dict:
    """Draw REAL sampler configurations and check none exceeds the deterministic envelope.

    This is the falsification test for the boundary-extremal assumption. Corner evaluation finds
    the extreme of a function over a box only if that function is monotone in each axis between
    corners; if a constant turns over in the interior, the true extreme is missed and the envelope
    is too narrow. A random draw from the real sampler is an independent probe of exactly that.

    It is meant to be able to FAIL. A pass is evidence the envelope covers the reachable set; a
    failure means the deterministic R is an underestimate and the sweep needs interior grid points
    on whichever axis was violated.
    """
    from sbind.stimuli import render_bpy as rb

    tmp = out_dir / ".verify_id.png"
    exceed: list[dict] = []
    checked = 0
    for seed in VERIFY_SEEDS:
        cfg = dict(config)
        cfg["n_images"] = n // len(VERIFY_SEEDS)
        for spec in build_scene_specs(cfg, seed, raise_on_placement_failure=False):
            scene = rb._reset_scene()
            ground = rb._add_ground(spec.ground_color)
            objs = [rb._add_object(o, i) for i, o in enumerate(spec.objects)]
            K, R, t = rb._add_camera(scene, spec)
            sun = rb._add_sun(scene, spec)
            rb._configure_beauty(scene, cfg["render"])
            masks = rb._render_id_pass(scene, objs, ground, [sun], tmp)
            if tmp.exists():
                tmp.unlink()
            near_i = int(spec.factors["closer_object"])
            mult = float(spec.factors["size_multiplier"])
            for i, o in enumerate(spec.objects[:2]):
                role = "near" if i == near_i else "far"
                depth = float(geometry.project(K, R, t, np.asarray(o.pos_world))[2])
                mg = rb._mask_geometry(masks[i])
                if mg is None:
                    continue
                _, height = mg
                vals = {
                    "height": height * depth / mult,
                    "area": int(masks[i].sum()) * depth**2 / mult**2,
                }
                for name, v in vals.items():
                    env = const[name].get((o.category, role))
                    if env is None:
                        continue
                    lo, hi = min(env), max(env)
                    if v < lo or v > hi:
                        exceed.append({
                            "id": spec.id, "category": o.category, "role": role,
                            "constant": name, "value": float(v),
                            "envelope": [float(lo), float(hi)],
                            "excess_pct": float(
                                100 * (v - hi) / hi if v > hi else 100 * (lo - v) / lo
                            ),
                        })
                checked += 1
    load_bearing = [
        e for e in exceed
        if any(
            e["constant"] == c and e["role"] == r
            and ((side == "max" and e["value"] > max(e["envelope"]))
                 or (side == "min" and e["value"] < min(e["envelope"])))
            for c, r, side in LOAD_BEARING
        )
    ]
    # localize to cells so a refinement can target the axis that failed, not the whole grid
    cells: dict[str, int] = {}
    for e in exceed:
        key = f"{e['constant']}:{e['category']}:{e['role']}"
        cells[key] = cells.get(key, 0) + 1
    return {
        "n_objects_checked": checked,
        "n_exceeding": len(exceed),
        "n_exceeding_load_bearing": len(load_bearing),
        "load_bearing_exceedances": load_bearing[:40],
        "cells": cells,
        "exceedances": exceed[:40],
    }


def r_of_floor_curve(records: list[dict], ranges: dict, floors: list[float]) -> list[dict]:
    """R(F) for a range of floors, from the ONE sweep — no re-rendering.

    A floor F constrains each image by far_depth >= F * near_depth. The loosest necessary
    condition over the whole set is far_depth >= F * min(near_depth), so filtering far-role poses
    on that admits at least every far pose the floor really allows. R computed from the filtered
    set is therefore an UPPER bound on the true R(F) — conservative in the direction that matters
    for a safety floor.
    """
    near_min = ranges["near"]["depth"][0]
    out = []
    for F in floors:
        const = {"height": {}, "area": {}}
        for r in records:
            for role in r["roles_ok"]:
                if role == "far" and r["depth"] < F * near_min:
                    continue
                const["height"].setdefault((r["category"], role), []).append(r["C_h"])
                const["area"].setdefault((r["category"], role), []).append(r["C_a"])
        if not all(const[k] for k in const):
            continue
        ratios = required_ratios(const)
        if not ratios:
            continue
        req = max(max(v["height"] for v in ratios.values()),
                  max(v["area"] for v in ratios.values()))
        out.append({"floor": F, "requirement": req, "self_consistent": F >= req})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--json")
    ap.add_argument("--verify-random", type=int, default=0,
                    help="draw N real sampler configurations and check none exceeds the envelope")
    ap.add_argument("--depth-grid", type=int, default=N_DEPTH_GRID,
                    help="depth grid points (refinement knob)")
    ap.add_argument("--lateral-levels", type=int, default=LATERAL_LEVELS,
                    help="lateral magnitude levels (refinement knob)")
    ap.add_argument("--floor-curve", action="store_true",
                    help="compute R(F) across a floor grid from the same sweep (no re-render)")
    args = ap.parse_args()

    config = load_config(args.config)
    out_dir = Path("/tmp/sbind_det")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"DETERMINISTIC ENVELOPE SWEEP — {args.config}")
    result = sweep(config, out_dir, args.depth_grid, args.lateral_levels)
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

    curve = []
    if args.floor_curve:
        grid = [round(1.15 + 0.005 * i, 4) for i in range(21)]
        curve = r_of_floor_curve(result["records"], result["ranges"], grid)
        print("\n--- R(F) from the same sweep (conservative upper bound) ---")
        print(f"  {'floor F':>9s} {'R(F)':>9s} {'F - R(F)':>10s}  self-consistent")
        r_star = None
        for row in curve:
            print(f"  {row['floor']:9.4f} {row['requirement']:9.4f} "
                  f"{row['floor'] - row['requirement']:+10.4f}  "
                  f"{'YES' if row['self_consistent'] else 'no'}")
            if row["self_consistent"] and r_star is None:
                r_star = row["floor"]
        if r_star is not None:
            print(f"\n  DETERMINISTIC r* = {r_star:.4f}  ->  r_op = {r_star + 0.005:.4f}")
        else:
            print("\n  *** no self-consistent floor in the grid")

    verification = {}
    if args.verify_random:
        print(f"\n--- random verification of the boundary-extremal assumption "
              f"({args.verify_random} scenes) ---")
        verification = verify_random(config, const, args.verify_random, out_dir)
        n_bad = verification["n_exceeding"]
        n_lb = verification["n_exceeding_load_bearing"]
        print(f"  objects checked: {verification['n_objects_checked']}   "
              f"exceeding: {n_bad}   ON THE LOAD-BEARING PAIR: {n_lb}")
        print(f"  cells: {verification['cells']}")
        if n_lb:
            print("  *** LOAD-BEARING VIOLATION — R is an UNDERESTIMATE, not ratifiable")
        elif n_bad:
            print("  *** coverage defect on non-load-bearing extrema — R unaffected but the "
                  "envelope is not certified")
        if n_bad:
            print("  *** ENVELOPE VIOLATED — the deterministic R is an UNDERESTIMATE")
            for e in verification["exceedances"][:5]:
                print(f"      {e['category']:9s} {e['role']:4s} {e['constant']:6s} "
                      f"{e['value']:11.1f} vs {e['envelope'][0]:.1f}..{e['envelope'][1]:.1f} "
                      f"({e['excess_pct']:+.2f}%)")
        else:
            print("  OK — no real sample fell outside the swept envelope")

    report = {
        "config": args.config,
        "floor_curve": curve,
        "random_verification": verification,
        "method": "envelope coverage (deterministic), not random sampling",
        "n_renders": len(result["records"]),
        "reachable_ranges": {
            r: {k: list(v) for k, v in d.items()} for r, d in result["ranges"].items()
        },
        "extremes": {
            f"{name}_{cat}_{role}": [float(min(v)), float(max(v)), len(v)]
            for name in ("height", "area")
            for (cat, role), v in const[name].items()
        },
        "required_ratio_by_pairing": ratios,
        "deterministic_R": required,
        "binding_pairing": binding,
        "grid": {"depth": args.depth_grid, "lateral": args.lateral_levels},
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
