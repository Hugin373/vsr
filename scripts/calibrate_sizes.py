"""Calibrate per-category size_m so every primitive subtends the SAME retinal extent.

A cube, a sphere and a cylinder of equal ``size_m`` do NOT project to the same pixel
extent (the cube's silhouette reaches its diagonal; the sphere only its diameter). In a
congruent set that lets a far cube out-measure a near sphere, inverting the size cue.

This script measures the shape factor empirically, using the exact metric that
``retinal_size_px`` records (the rendered mask's pixel HEIGHT) — it renders each
primitive and reads its mask back, rather than trusting a closed-form approximation.
It then solves for the ``size_m`` per category that hits a target pixel height at the
set's reference depth, refining a few times because changing size_m also changes the
object's resting height (and hence its depth) slightly.

Usage:
    uv run --extra stimuli scripts/calibrate_sizes.py \
        --config configs/stimuli_v0_congruent.yaml --target-px 90

Writes configs/size_calibration.yaml, which the stimulus config reads.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml

from sbind.stimuli import geometry
from sbind.stimuli.render_bpy import render_scene
from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec
from sbind.utils.config import load_config
from sbind.utils.logging import get_logger

log = get_logger("sbind.calibrate")


def _measure_retinal(
    cam: CameraSpec,
    category: str,
    size_m: float,
    x: float,
    depth_target: float,
    render_cfg: dict,
    tmp: Path,
) -> float:
    """Render one primitive at ``depth_target`` and return its mask pixel-height."""
    K, R, t, _ = geometry.camera_frame(
        cam.pos_world, cam.target_world, cam.f_mm, cam.sensor_width_mm, cam.res_x, cam.res_y
    )
    axis = geometry.optical_axis(R)
    z = geometry.rest_height(category, size_m)
    # solve depth(x, y, z) = depth_target for y
    y = (depth_target - float(t[2]) - float(axis[0]) * x - float(axis[2]) * z) / float(axis[1])
    spec = SceneSpec(
        id=f"cal_{category}_{x:+.2f}",
        camera=cam,
        objects=[ObjectSpec(f"cal_{category}", category, [0.8, 0.8, 0.8], size_m, [x, y, z])],
    )
    ann = render_scene(spec, tmp, render_cfg)
    return float(ann.objects[0].retinal_size_px)


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibrate per-category size_m.")
    ap.add_argument("--config", required=True)
    ap.add_argument(
        "--target-px",
        type=float,
        default=90.0,
        help="target retinal pixel-height at the reference depth",
    )
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--out", default="configs/size_calibration.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    cam_cfg, render_cfg, fcfg = cfg["camera"], cfg["render"], cfg["factors"]
    cam = CameraSpec(
        pos_world=list(cam_cfg["pos_world"]),
        target_world=list(cam_cfg["target_world"]),
        f_mm=float(cam_cfg["f_mm"]),
        sensor_width_mm=float(cam_cfg["sensor_width_mm"]),
        res_x=int(render_cfg["res_x"]),
        res_y=int(render_cfg["res_y"]),
    )
    # reference depth = the midpoint of the set's depth span, measured on the optical axis
    K, R, t, _ = geometry.camera_frame(
        cam.pos_world, cam.target_world, cam.f_mm, cam.sensor_width_mm, cam.res_x, cam.res_y
    )
    axis = geometry.optical_axis(R)
    bins = fcfg["near_depth_bins"]
    gaps = fcfg["depth_gaps"]
    y_lo, y_hi = min(bins), max(bins) + max(gaps)
    d_lo = float(axis[1]) * y_lo + float(t[2])
    d_hi = float(axis[1]) * y_hi + float(t[2])
    d_ref = 0.5 * (d_lo + d_hi)
    if "lateral_offset" in fcfg:
        lateral_positions = [-float(fcfg["lateral_offset"]), float(fcfg["lateral_offset"])]
    elif "lateral_range" in fcfg:
        lo, hi = map(float, fcfg["lateral_range"])
        lateral_positions = [-hi, -lo, lo, hi]
    else:
        lateral_positions = [0.0]
    log.info("reference depth = %.2f m (span %.2f-%.2f)", d_ref, d_lo, d_hi)

    # low-sample render is fine: the ID pass (which the mask comes from) is always 1-spp
    cal_render = {**render_cfg, "samples": 4, "denoise": False}
    categories = list(cfg["objects"]["categories"])
    existing_sizes = dict(cfg["objects"].get("size_m_by_category") or {})
    base = float(cfg["objects"].get("base_size_m", cfg["objects"].get("size_m", 0.6)))

    sizes = {c: float(existing_sizes.get(c, base)) for c in categories}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for it in range(args.iters):
            report = []
            for c in categories:
                # average over lateral placements the sampler actually uses
                heights = [
                    _measure_retinal(cam, c, sizes[c], x, d_ref, cal_render, tmp)
                    for x in lateral_positions
                ]
                h = float(np.mean(heights))
                # retinal height is ~linear in size_m -> rescale straight onto the target
                sizes[c] = sizes[c] * (args.target_px / h)
                report.append(f"{c}: measured {h:.1f}px -> size_m {sizes[c]:.4f}")
            log.info("iter %d: %s", it + 1, " | ".join(report))

        # final verification pass at the calibrated sizes
        final = {}
        for c in categories:
            heights = [
                _measure_retinal(cam, c, sizes[c], x, d_ref, cal_render, tmp)
                for x in lateral_positions
            ]
            final[c] = float(np.mean(heights))

    spread = max(final.values()) - min(final.values())
    log.info(
        "final retinal heights at d_ref: %s (spread %.2f px)",
        {c: round(v, 1) for c, v in final.items()},
        spread,
    )

    out = {
        "_generated_by": "scripts/calibrate_sizes.py",
        "_reference_depth_m": round(d_ref, 4),
        "_target_px": args.target_px,
        "_measured_px_at_ref": {c: round(v, 2) for c, v in final.items()},
        "_spread_px": round(spread, 3),
        "size_m_by_category": {c: round(v, 4) for c, v in sizes.items()},
    }
    Path(args.out).write_text(yaml.safe_dump(out, sort_keys=False), encoding="utf-8")
    print(f"wrote {args.out}")
    print(yaml.safe_dump(out, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
