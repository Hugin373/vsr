"""M3.1 diagnostic: steering dose-response over alpha. [GPU]

    uv run --extra extract scripts/kang_dose_response.py --config configs/m3_kang.yaml --gpu 2

WHY THIS EXISTS, and what it is NOT.

At the paper's alpha=5 our spatial-ID steering flips 13-31% of beliefs against a ~0% noise
control, versus their 64.4% vs 29.5%. The SELECTIVITY is far cleaner than theirs; the
MAGNITUDE is well below. Before calling that a failure we owe the claim an honest check of
the one free parameter: alpha is a scale constant that Kang grid-searched *for their setup*,
and our models are far more confident on this task (95-98% accuracy) than a flip-prone model
would be — a bigger nudge may simply be needed to move a more certain belief.

This is a DOSE-RESPONSE CURVE, not a search for a number that matches the paper. The headline
result stays fixed at the paper's alpha=5. What this can legitimately establish:

  * if spatial-ID steering rises with alpha while norm-matched noise stays flat, the MECHANISM
    is reproduced and only the scale constant differs -> report as such;
  * if spatial-ID steering never separates from noise at any dose, the mechanism does not
    reproduce here, and no choice of alpha rescues it.

Either way the curve is reported in full, including the doses that look bad.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.utils.config import load_config
from sbind.utils.io import ensure_dir, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.dose")

ALPHAS = [1.0, 2.0, 5.0, 10.0, 20.0, 40.0]


def main() -> int:
    ap = argparse.ArgumentParser(description="Steering dose-response over alpha (M3.1).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--gpu", type=int, required=True)
    ap.add_argument("--n-scenes", type=int, default=150)
    ap.add_argument("--model", help="run only this model")
    ap.add_argument(
        "--layer",
        type=int,
        help="steer at this layer instead of the summary's best. Use the best MIDDLE-THIRD "
        "layer: the global best can be layer 0, where the 'object-word token' is still just "
        "the word EMBEDDING — steering it there corrupts word identity rather than a bound "
        "spatial ID, which is not the claim under test.",
    )
    args = ap.parse_args()

    config = load_config(args.config)
    from sbind.utils.gpu import claim_gpu

    claim_gpu(args.gpu, mem_threshold_mib=int(config["gpu"]["mem_threshold_mib"]))

    from sbind.extract.vlm import load_vlm
    from sbind.interventions.spatial_id import SpatialIDs, derive_spatial_ids, steer_belief_swap
    from sbind.stimuli.grid_scenes import iter_scenes

    root = Path(config["output"]["root"])
    scenes = list(iter_scenes(root / "grid_scenes.jsonl"))
    grid_m = int(config["grid"]["grid_m"])
    out: list[dict] = []

    import json as _json

    models = [m for m in config["models"] if not args.model or m["name"] == args.model]
    summary = _json.load(open(root / "summary.json", encoding="utf-8"))

    for mc in models:
        mdir = root / mc["name"]
        entry = next((s for s in summary if s["model"] == mc["name"]), None)
        if entry is None:
            log.warning("no summary entry for %s — skipping", mc["name"])
            continue
        if args.layer is not None:
            layer = args.layer
        else:
            # the most responsive MIDDLE-THIRD layer — the paper's claimed binding band
            mid = set(entry["mid_layers"])
            cand = [r for r in entry["steering"] if r["layer"] in mid]
            layer = max(cand, key=lambda r: r["swap_spatial_id"])["layer"]

        vlm = load_vlm(mc["checkpoint"], dtype=mc.get("dtype", "bfloat16"))

        # reuse the cached spatial IDs rather than re-deriving them
        npz = np.load(mdir / "spatial_ids.npz")
        key = f"L{layer}"
        if key in npz:
            sids = {
                layer: SpatialIDs(
                    layer=layer, ids=npz[key], grid_m=grid_m,
                    n_objects=0, counts=np.zeros((grid_m, grid_m)),
                )
            }
        else:
            sids = derive_spatial_ids(vlm, scenes, [layer], grid_m=grid_m)

        for a in ALPHAS:
            r = steer_belief_swap(
                vlm, scenes[: args.n_scenes], sids, layer=layer, alpha=a,
                seed=int(config["seed"]),
            )
            r["model"] = mc["name"]
            out.append(r)
            log.info(
                "%s L%d alpha=%-5.1f  spatial-ID %5.1f%%  noise %5.1f%%  gap %+5.1f pts",
                mc["name"], layer, a, 100 * r["swap_spatial_id"], 100 * r["swap_noise"],
                100 * (r["swap_spatial_id"] - r["swap_noise"]),
            )
        del vlm
        import gc

        import torch

        gc.collect()
        torch.cuda.empty_cache()

    write_json(out, ensure_dir(root) / "dose_response.json")

    print(f"\n{'=' * 72}\nM3.1 steering dose-response (paper's alpha = 5)\n{'=' * 72}")
    print(f"{'model':16s} {'alpha':>6s} {'spatial-ID':>11s} {'noise':>8s} {'gap':>8s}")
    for r in out:
        star = "  <- paper's alpha" if r["alpha"] == 5.0 else ""
        print(f"{r['model']:16s} {r['alpha']:>6.1f} {r['swap_spatial_id']:>11.1%} "
              f"{r['swap_noise']:>8.1%} "
              f"{r['swap_spatial_id'] - r['swap_noise']:>8.1%}{star}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
