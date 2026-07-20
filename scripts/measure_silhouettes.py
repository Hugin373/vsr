"""Dense silhouette measurement for cue-constant derivation — ID pass only, no beauty render.

    # validate the instrument against a real rendered set (must be exact)
    uv run --extra stimuli scripts/measure_silhouettes.py \
        --validate-against $DATA_ROOT/stimuli/m4a_v1_natural_congruent_pilot

    # then sweep a frozen config densely
    uv run --extra stimuli scripts/measure_silhouettes.py \
        --config configs/m4a_v1_natural_congruent_pilot.yaml --n 1000 \
        --out $DATA_ROOT/measurements/cue_sweep_natural_congruent

Why this exists (AGENTS.md rule 7 clause 1 + rule 6). `min_depth_ratio` is derived from the
WORST CASE of a constructed quantity, so the derivation is only as good as its pose coverage.
The rendered pilots give ~23 samples per (category, role) cell, and a half-sample subset of the
worst cell recovers only ~48% of the measured range — i.e. the extremes had visibly not
converged, so any floor derived from them is a lower bound wearing a worst case's clothes.

The constants depend on the flat-emission ID pass ONLY (silhouette height + mask area); the
beauty pass, materials, ground colour and lighting do not enter them, and the ID pass zeroes
lights and bounces anyway. So the measurement can skip ~85% of the render cost: 0.2 s/scene
instead of ~3 s/scene, which buys ~50x the pose coverage for the same wall clock.

⚠ This writes a MEASUREMENT set, not a stimulus set: no beauty images, no masks on disk, no
questions. It is an instrument for deriving constants and must never be used as stimuli.
`--validate-against` is the rule-11 positive control for it: replay a real set's exact scenes
through this path and require `retinal_size_px` / `mask_area_px` to match the shipped
annotations, so a measurement that silently disagrees with the real renderer cannot pass.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import yaml

from sbind.stimuli import geometry
from sbind.stimuli.sampler import build_scene_specs
from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec
from sbind.utils.config import load_config, run_metadata
from sbind.utils.io import ensure_dir, read_jsonl, write_json, write_jsonl
from sbind.utils.logging import get_logger

log = get_logger("sbind.measure")


def _silhouettes(spec: SceneSpec, render_cfg: dict, tmp_path: Path) -> list[dict]:
    """Render the flat ID pass for one scene, return per-object silhouette geometry."""
    from sbind.stimuli import render_bpy as rb

    scene = rb._reset_scene()
    ground = rb._add_ground(spec.ground_color)
    objects = [rb._add_object(o, i) for i, o in enumerate(spec.objects)]
    K, R, t = rb._add_camera(scene, spec)
    sun = rb._add_sun(scene, spec)
    rb._configure_beauty(scene, render_cfg)
    masks = rb._render_id_pass(scene, objects, ground, [sun], tmp_path)
    if tmp_path.exists():
        tmp_path.unlink()

    out = []
    for i, o in enumerate(spec.objects):
        p_world = np.asarray(o.pos_world, dtype=float)
        depth_m = float(geometry.project(K, R, t, p_world)[2])
        mg = rb._mask_geometry(masks[i])
        bbox, retinal = mg if mg is not None else ([0.0, 0.0, 0.0, 0.0], 0.0)
        out.append(
            {
                "name": o.name,
                "category": o.category,
                "size_m": float(o.size_m),
                "pos_world": p_world.tolist(),
                "depth_m": depth_m,
                "bbox_px": bbox,
                "retinal_size_px": retinal,
                "mask_area_px": int(masks[i].sum()),
            }
        )
    return out


def _camera_from_annotation(record: dict, render_cfg: dict, f_mm: float, sensor_mm: float):
    """Rebuild the exact CameraSpec of a rendered record from its stored (R, t).

    `pos_world = -R^T t`; the look-at target is any point along the optical axis, since only the
    direction matters to the projection. Rebuilding from the ANNOTATION rather than re-running
    the sampler keeps the validation independent of sampler/RNG changes — the point is to test
    the measurement path, not the sampler.
    """
    R = np.asarray(record["camera"]["R"], dtype=float)
    t = np.asarray(record["camera"]["t"], dtype=float)
    pos = (-R.T @ t).tolist()
    forward = R.T @ np.array([0.0, 0.0, 1.0])
    target = (np.asarray(pos) + forward).tolist()
    return CameraSpec(
        pos_world=pos,
        target_world=target,
        f_mm=f_mm,
        sensor_width_mm=sensor_mm,
        res_x=int(render_cfg["res_x"]),
        res_y=int(render_cfg["res_y"]),
    )


def validate_against(set_dir: Path, device: str | None = None) -> int:
    """Replay a rendered set's scenes through the ID-pass-only path and compare geometry."""
    records = list(read_jsonl(set_dir / "annotations.jsonl"))
    config = yaml.safe_load((set_dir / "config.yaml").read_text(encoding="utf-8"))
    render_cfg = dict(config["render"])
    if device:
        render_cfg["device"] = device
        print(f"  ⚠ device OVERRIDE: rendering the replay on {device}")
    tmp = ensure_dir(Path("/tmp") / "sbind_measure") / "validate_id.png"

    n_objects = 0
    height_diffs: list[float] = []
    area_diffs: list[float] = []
    for record in records:
        camera = _camera_from_annotation(
            record, render_cfg, float(config["camera"]["f_mm"]),
            float(config["camera"]["sensor_width_mm"]),
        )
        spec = SceneSpec(
            id=record["id"],
            camera=camera,
            objects=[
                ObjectSpec(o["name"], o["category"], [0.5, 0.5, 0.5], o["size_m"], o["pos_world"])
                for o in record["objects"]
            ],
            ground_color=record["factors"].get("ground_color", [0.45, 0.45, 0.48]),
            sun_energy=record["factors"].get("sun_energy", 4.0),
            sun_direction=record["factors"].get("sun_direction", [5.0, -5.0, 8.0]),
            factors=record["factors"],
        )
        measured = _silhouettes(spec, render_cfg, tmp)
        for got, want in zip(measured, record["objects"], strict=True):
            height_diffs.append(abs(got["retinal_size_px"] - want["retinal_size_px"]))
            area_diffs.append(abs(got["mask_area_px"] - want["mask_area_px"]))
            n_objects += 1

    h = np.asarray(height_diffs)
    a = np.asarray(area_diffs)
    print(f"validated {len(records)} scenes / {n_objects} objects against {set_dir}")
    print(f"  retinal_size_px : max |diff| = {h.max():.3f} px   ({int((h > 0).sum())} nonzero)")
    print(f"  mask_area_px    : max |diff| = {a.max():.0f} px    ({int((a > 0).sum())} nonzero)")
    # The ID pass is 1 sample, zero bounces, near-zero BOX filter: it is point-sampled and must
    # reproduce exactly. Anything nonzero means the measurement path is not the render path.
    if h.max() > 0 or a.max() > 0:
        print("\n  *** MEASUREMENT PATH DISAGREES WITH THE RENDERER — do not derive constants")
        return 1
    print("\n  OK — the measurement path reproduces the shipped annotations exactly")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", help="stimulus config to sweep")
    ap.add_argument("--n", type=int, help="number of scenes to measure (overrides n_images)")
    ap.add_argument("--out", help="output measurement dir")
    ap.add_argument("--validate-against", help="rendered set dir to replay and compare against")
    ap.add_argument("--gpu", type=int, default=None,
                    help="claim this GPU and render on it (guarded); validates the GPU path")
    ap.add_argument("--device", choices=("CPU", "GPU"), default=None,
                    help="override render.device; use with --gpu to validate the GPU path")
    ap.add_argument(
        "--allow-placement-failures",
        action="store_true",
        help=(
            "CALIBRATION ONLY: skip un-placeable images instead of raising, and record the count. "
            "A stimulus RENDER must never use this — an un-placeable image there breaks the factor "
            "balance. For a calibration measurement a skipped image at the ~0.04%% background rate "
            "shifts no constant materially, and crashing the whole sweep over one image would make "
            "the derived quantity depend on a rare placement coin-flip."
        ),
    )
    args = ap.parse_args()

    if args.gpu is not None:
        from sbind.utils.gpu import claim_gpu
        claim_gpu(args.gpu)          # aborts if another user holds it; sets CUDA_VISIBLE_DEVICES
        log.info(
            "claimed GPU %d (CUDA_VISIBLE_DEVICES=%s)",
            args.gpu, os.environ.get("CUDA_VISIBLE_DEVICES"),
        )

    if args.validate_against:
        return validate_against(Path(args.validate_against), args.device)

    if not (args.config and args.out):
        ap.error("--config and --out are required unless --validate-against is given")

    config = load_config(args.config)
    if args.n:
        config["n_images"] = int(args.n)
    seed = int(config["seed"])
    out_dir = ensure_dir(Path(args.out))
    placement_failures: list[dict] = []
    specs = build_scene_specs(
        config,
        seed,
        raise_on_placement_failure=not args.allow_placement_failures,
        placement_failures=placement_failures,
    )
    if placement_failures:
        log.warning(
            "%d image(s) could not be placed and were SKIPPED (--allow-placement-failures). "
            "This is acceptable for a calibration measurement and NEVER for a stimulus render.",
            len(placement_failures),
        )
    log.info("measuring %d scenes from %s", len(specs), args.config)

    tmp = out_dir / ".measure_id.png"
    records = []
    t0 = time.time()
    for i, spec in enumerate(specs):
        records.append(
            {
                "id": spec.id,
                "objects": _silhouettes(spec, config["render"], tmp),
                "factors": dict(spec.factors),
            }
        )
        if (i + 1) % 200 == 0:
            log.info("%d/%d (%.3f s/scene)", i + 1, len(specs), (time.time() - t0) / (i + 1))

    write_jsonl(records, out_dir / "annotations.jsonl")
    (out_dir / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    meta = run_metadata(config, seed)
    meta["measurement_only"] = True
    meta["placement_failures_skipped"] = len(placement_failures)
    meta["allow_placement_failures"] = bool(args.allow_placement_failures)
    meta["measurement_note"] = (
        "ID-pass-only silhouette measurement for cue-constant derivation. NOT a stimulus set: "
        "no beauty images, no mask PNGs, no questions."
    )
    write_json(meta, out_dir / "run_metadata.json")
    log.info(
        "done: %d scenes -> %s (%.1f min)", len(records), out_dir, (time.time() - t0) / 60.0
    )
    print(json.dumps({"scenes": len(records), "out": str(out_dir)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
