"""M3.1 — Kang et al. reproduction (reimplemented). [GPU]

    uv run --extra extract scripts/kang_repro.py --config configs/m3_kang.yaml --gpu 2
    ... --stage scenes        # build the grid scenes only (no GPU)
    ... --model qwen2.5-vl-7b # one model
    ... --resume              # skip stages whose output already exists

Produces $DATA_ROOT/m3_kang/<model>/{spatial_ids.npz, steering.json, patching.json, rank.json}
and prints a numbers-vs-paper table. GPU etiquette per CLAUDE.md: explicit --gpu, guard first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.utils.config import load_config, run_metadata
from sbind.utils.io import ensure_dir, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.kang")

# The paper's reported values — the bar this reproduction is measured against.
PAPER = {
    "swap_spatial_id": 0.644,  # median binary belief swap, spatial-ID steering
    "swap_noise": 0.295,  # norm-matched noise control
    "rank3_r2": 0.85,  # rank-3 explains >= 85% of the spatial-ID structure
}


def build_scenes(config: dict) -> list:
    """Stage 1 (CPU): tile the two-object grid scenes and CHECK the invariant they must obey."""
    from sbind.stimuli.grid_scenes import (
        assert_position_identity_decorrelated,
        build_grid_scenes,
        coco_cutouts,
        iter_scenes,
    )

    g = config["grid"]
    out_dir = Path(config["output"]["root"]) / "grid"
    manifest = out_dir.parent / "grid_scenes.jsonl"
    if manifest.exists():
        scenes = list(iter_scenes(manifest))
        log.info("reusing %d grid scenes from %s", len(scenes), manifest)
    else:
        coco_root = Path(config["output"]["root"]).parent / "external" / "coco"
        objects = coco_cutouts(
            coco_root,
            n_objects=int(g["n_objects"]),
            split=g["coco_split"],
            min_area=int(g["min_instance_area"]),
            seed=int(config["seed"]),
        )
        scenes = build_grid_scenes(
            objects,
            out_dir=ensure_dir(out_dir),
            grid_m=int(g["grid_m"]),
            repeats_per_cell=int(g["repeats_per_cell"]),
            resolution=int(g["resolution"]),
            pad=float(g["pad"]),
            seed=int(config["seed"]),
        )

    # THE invariant: if identity predicts position, the spatial-ID derivation is circular.
    stats = assert_position_identity_decorrelated(scenes)
    log.info("decorrelation check: %s", stats)
    return scenes


def run_model(config: dict, model_cfg: dict, scenes: list, gpu: int) -> dict:
    """Stages 2-4 (GPU): derive spatial IDs, steer, patch, rank-sweep."""
    from sbind.extract.vlm import load_vlm
    from sbind.interventions.spatial_id import (
        derive_spatial_ids,
        mirror_swap_patch_profile,
        positional_basis_rank_r2,
        steer_belief_swap,
    )

    a = config["analysis"]
    out_dir = ensure_dir(Path(config["output"]["root"]) / model_cfg["name"])

    vlm = load_vlm(model_cfg["checkpoint"], dtype=model_cfg.get("dtype", "bfloat16"))
    layers = list(range(0, vlm.n_layers, int(a["layer_stride"])))
    log.info("%s: %d layers, scanning %s", model_cfg["name"], vlm.n_layers, layers)

    # --- spatial IDs, every scanned layer ---
    sids = derive_spatial_ids(vlm, scenes, layers=layers, grid_m=int(config["grid"]["grid_m"]))
    np.savez_compressed(
        out_dir / "spatial_ids.npz", **{f"L{L}": s.ids for L, s in sids.items()}
    )

    # --- low-rank structure of the position code, per layer ---
    rank = {
        str(L): positional_basis_rank_r2(s, max_rank=int(a["rank_max"]))
        for L, s in sids.items()
    }
    write_json(rank, out_dir / "rank.json")

    # --- steering, at EVERY scanned layer ---
    # Kang locate binding in the middle third, so that is where the headline number is taken
    # from. But we steer across the whole depth rather than only there: a pilot showed the
    # object-word token's causal influence on this model/prompt is concentrated EARLY (mean
    # |ΔP| under zero-ablation: 0.112 at layer 0, decaying to 0.004 by layer 21). Steering
    # only the middle third would have reported "no effect" without revealing that the
    # profile itself differs. The profile IS the result.
    mid = [L for L in layers if vlm.n_layers // 3 <= L < 2 * vlm.n_layers // 3]
    steer_scenes = scenes[: int(a["n_steer_scenes"])]
    steering = [
        steer_belief_swap(
            vlm, steer_scenes, sids, layer=L, alpha=float(a["steering_alpha"]),
            seed=int(config["seed"]),
        )
        for L in layers
    ]
    write_json(steering, out_dir / "steering.json")
    for r in steering:
        log.info(
            "  L%-2d  spatial-ID %.1f%%  noise %.1f%%  (acc before %.1f%%)",
            r["layer"], 100 * r["swap_spatial_id"], 100 * r["swap_noise"],
            100 * r["acc_before"],
        )

    # --- mirror-swap patching profile across depth ---
    patching = mirror_swap_patch_profile(
        vlm, scenes[: int(a["n_patch_scenes"])], layers=layers
    )
    write_json(patching, out_dir / "patching.json")

    # Report BOTH: the middle third (where the paper locates binding — this is the honest
    # like-for-like number) and the best layer anywhere (a best case FOR the paper's claim,
    # selected post hoc, so it must be labelled as such and never quoted as the headline).
    mid_rows = [r for r in steering if r["layer"] in mid]
    best = max(steering, key=lambda r: r["swap_spatial_id"])
    return {
        "model": model_cfg["name"],
        "checkpoint": model_cfg["checkpoint"],
        "n_layers": vlm.n_layers,
        "mid_layers": mid,
        "mid_swap_spatial_id": float(np.mean([r["swap_spatial_id"] for r in mid_rows])),
        "mid_swap_noise": float(np.mean([r["swap_noise"] for r in mid_rows])),
        "best_steer_layer": best["layer"],
        "best_swap_spatial_id": best["swap_spatial_id"],
        "best_swap_noise": best["swap_noise"],
        "acc_before": float(np.mean([r["acc_before"] for r in steering])),
        "rank3_r2": float(
            np.mean([r[2]["r2"] for L, r in rank.items() if len(r) >= 3 and int(L) in mid])
        ),
        "steering": steering,
        "patching": patching,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Kang et al. reproduction (M3.1).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--gpu", type=int, help="REQUIRED for GPU stages (shared server)")
    ap.add_argument("--stage", choices=["scenes", "all"], default="all")
    ap.add_argument("--model", help="run only this model by name")
    args = ap.parse_args()

    config = load_config(args.config)
    out_root = ensure_dir(Path(config["output"]["root"]))
    write_json(run_metadata(config, int(config["seed"])), out_root / "run_metadata.json")

    scenes = build_scenes(config)
    if args.stage == "scenes":
        print(f"built/verified {len(scenes)} grid scenes")
        return 0

    if args.gpu is None:
        print("--gpu N is REQUIRED for the GPU stages (shared server).", file=sys.stderr)
        return 2

    # GPU guard BEFORE torch touches CUDA (CLAUDE.md hard rule)
    from sbind.utils.gpu import claim_gpu

    claim_gpu(args.gpu, mem_threshold_mib=int(config["gpu"]["mem_threshold_mib"]))
    log.info("claimed GPU %d", args.gpu)

    models = [m for m in config["models"] if not args.model or m["name"] == args.model]
    if not models:
        raise SystemExit(f"no model named {args.model!r} in the config")

    results = []
    for mc in models:
        log.info("=== %s ===", mc["name"])
        results.append(run_model(config, mc, scenes, args.gpu))
        write_json(results, out_root / "summary.json")

    # --- numbers vs paper ---
    print(f"\n{'=' * 86}\nM3.1 Kang reproduction — ours vs paper\n{'=' * 86}")
    hdr = (
        f"{'model':15s} {'task acc':>8s} | {'MIDDLE THIRD (paper location)':^29s} | "
        f"{'best layer (post hoc)':^23s} | {'rank3':>6s}"
    )
    print(hdr)
    print(f"{'':15s} {'':8s} | {'spatial-ID':>10s} {'noise':>8s} {'gap':>8s} | "
          f"{'L':>3s} {'spatial-ID':>10s} {'noise':>7s} | {'R2':>6s}")
    print("-" * 86)
    print(f"{'PAPER':15s} {'—':>8s} | {PAPER['swap_spatial_id']:>10.1%} "
          f"{PAPER['swap_noise']:>8.1%} "
          f"{PAPER['swap_spatial_id'] - PAPER['swap_noise']:>8.1%} | "
          f"{'mid':>3s} {'—':>10s} {'—':>7s} | {PAPER['rank3_r2']:>6.2f}")
    for r in results:
        print(f"{r['model']:15s} {r['acc_before']:>8.1%} | {r['mid_swap_spatial_id']:>10.1%} "
              f"{r['mid_swap_noise']:>8.1%} "
              f"{r['mid_swap_spatial_id'] - r['mid_swap_noise']:>8.1%} | "
              f"{r['best_steer_layer']:>3d} {r['best_swap_spatial_id']:>10.1%} "
              f"{r['best_swap_noise']:>7.1%} | {r['rank3_r2']:>6.2f}")
    print(f"\nwrote {out_root}/summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
