"""M3.2 — Wang & Gao pattern reproduction on OUR v0 stimuli. [GPU extract + CPU probe]

    uv run --extra extract scripts/wanggao_repro.py --config configs/m3_wanggao.yaml --gpu 3

Mask-pooled object tokens at LM decoder layers -> ridge probes for x / z / pairwise distance,
with COLOUR and SHAPE as the semantic controls.

Pass bar (IMPLEMENTATION_PLAN M3) is a PATTERN match, not a number match:
    semantics >> metric  ;  x ~ chance  ;  z modest
Their reported values (Qwen2.5-VL-7B / InternVL3-8B, their SynSpat3D):
    x R2 = -0.09 | z R2 = +0.28 | pairwise-distance RSA rho ~ 0.01 | shape R2 = 1.00
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from sbind.utils.config import load_config, run_metadata
from sbind.utils.io import ensure_dir, read_jsonl, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.wanggao")

PAPER = {"x_r2": -0.09, "z_r2": 0.28, "dist_rsa": 0.01, "shape_r2": 1.00}

PROMPT = "Describe the spatial layout of the objects in this image."


def extract(config: dict, model_cfg: dict) -> dict:
    """GPU stage: mask-pooled object features at every scanned LM layer."""
    from PIL import Image

    from sbind.extract.pooling import (
        check_grid_registration,
        image_token_positions,
        mask_pool,
        mask_to_token_weights,
        token_grid,
    )
    from sbind.extract.vlm import load_vlm

    set_dir = Path(config["stimuli"]["set_dir"])
    anns = list(read_jsonl(set_dir / "annotations.jsonl"))
    if not anns:
        raise RuntimeError(f"no annotations in {set_dir}")

    vlm = load_vlm(model_cfg["checkpoint"], dtype=model_cfg.get("dtype", "bfloat16"))
    layers = list(range(0, vlm.n_layers, int(config["analysis"]["layer_stride"])))
    log.info("%s: %d layers, scanning %s", model_cfg["name"], vlm.n_layers, layers)

    feats: dict[int, list[np.ndarray]] = {L: [] for L in layers}
    meta: list[dict] = []
    reg_errors: list[float] = []

    for n, ann in enumerate(anns):
        img = Image.open(set_dir / ann["image"]).convert("RGB")
        inputs = vlm.build_inputs(img, PROMPT)
        img_pos = image_token_positions(vlm, inputs)
        rows, cols = token_grid(vlm, inputs)
        _, caps = vlm.forward(inputs, capture_layers=layers)

        for oi, obj in enumerate(ann["objects"]):
            mask = np.array(Image.open(set_dir / obj["mask"]).convert("L")) > 127

            # INVARIANT: the tokens this mask weights must lie where the object actually is.
            # A transposed or flipped grid still has the right token COUNT — only this catches it.
            reg = check_grid_registration(vlm, inputs, mask, obj["bbox_px"])
            reg_errors.append(max(reg["err_x"], reg["err_y"]))

            w = mask_to_token_weights(mask, rows, cols)
            for L in layers:
                feats[L].append(mask_pool(caps[L][0], img_pos, w))

            meta.append(
                {
                    "image_id": ann["id"],
                    "object_index": oi,
                    "x": obj["pos_cam"][0],  # lateral  (Wang & Gao's 'x')
                    "z": obj["depth_m"],  # depth     (their 'z')
                    "shape": obj["category"],
                    "color": obj["name"].split("_")[0],
                    "size_m": obj["size_m"],
                }
            )
        if (n + 1) % 100 == 0:
            log.info("extract: %d/%d images", n + 1, len(anns))

    worst_reg = float(np.max(reg_errors))
    log.info(
        "grid registration: worst |token-centroid - bbox-centre| = %.3f (normalised grid units)",
        worst_reg,
    )
    if worst_reg > 0.20:
        raise RuntimeError(
            f"mask->token registration is off by {worst_reg:.3f} of the grid — the pooled "
            f"tokens are not where the object is, so every probe number would be meaningless."
        )

    out_dir = ensure_dir(Path(config["output"]["root"]) / model_cfg["name"])
    np.savez_compressed(
        out_dir / "features.npz",
        **{f"L{L}": np.stack(v).astype(np.float16) for L, v in feats.items()},
    )
    write_json(meta, out_dir / "meta.json")
    write_json({"worst_grid_registration_err": worst_reg, "layers": layers},
               out_dir / "extract_meta.json")
    log.info("cached %d object features x %d layers -> %s", len(meta), len(layers), out_dir)
    return {"layers": layers, "n_objects": len(meta)}


def probe(config: dict, model_cfg: dict) -> list[dict]:
    """CPU stage: ridge/logistic probes per layer, each with its shuffled-label control."""
    from sbind.probes.ridge import probe_layer

    a = config["analysis"]
    out_dir = Path(config["output"]["root"]) / model_cfg["name"]
    data = np.load(out_dir / "features.npz")
    with open(out_dir / "meta.json", encoding="utf-8") as f:
        meta = json.load(f)

    targets = {
        # the METRIC quantities (Wang & Gao's x and z)
        "x_lateral": ("reg", np.array([m["x"] for m in meta], dtype=np.float64)),
        "z_depth": ("reg", np.array([m["z"] for m in meta], dtype=np.float64)),
        # the SEMANTIC controls — the contrast the whole claim rests on
        "shape": ("cls", np.array([m["shape"] for m in meta])),
        "color": ("cls", np.array([m["color"] for m in meta])),
    }

    rows = []
    for key in sorted(data.files, key=lambda k: int(k[1:])):
        L = int(key[1:])
        X = data[key].astype(np.float64)
        res = probe_layer(
            X, targets, seeds=tuple(a.get("seeds", (0, 1, 2, 3, 4))),
            n_folds=int(a.get("n_folds", 5)),
        )
        by = {r.target: r for r in res}
        for r in res:
            rows.append({"model": model_cfg["name"], "layer": L, **r.to_dict()})
        log.info(
            "L%-2d  x R2=%+.3f (ctrl %+.3f)  z R2=%+.3f (ctrl %+.3f)  "
            "shape acc=%.3f (ctrl %.3f)  colour acc=%.3f (ctrl %.3f)",
            L,
            by["x_lateral"].value, by["x_lateral"].control,
            by["z_depth"].value, by["z_depth"].control,
            by["shape"].value, by["shape"].control,
            by["color"].value, by["color"].control,
        )
    write_json(rows, out_dir / "probes.json")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Wang & Gao pattern reproduction (M3.2).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--gpu", type=int)
    ap.add_argument("--stage", choices=["extract", "probe", "all"], default="all")
    ap.add_argument("--model")
    args = ap.parse_args()

    config = load_config(args.config)
    out_root = ensure_dir(Path(config["output"]["root"]))
    write_json(run_metadata(config, int(config["seed"])), out_root / "run_metadata.json")

    models = [m for m in config["models"] if not args.model or m["name"] == args.model]
    if not models:
        raise SystemExit(f"no model named {args.model!r}")

    if args.stage in ("extract", "all"):
        if args.gpu is None:
            print("--gpu N is REQUIRED for extraction (shared server).", file=sys.stderr)
            return 2
        from sbind.utils.gpu import claim_gpu

        claim_gpu(args.gpu, mem_threshold_mib=int(config["gpu"]["mem_threshold_mib"]))
        log.info("claimed GPU %d", args.gpu)
        for mc in models:
            log.info("=== extract %s ===", mc["name"])
            extract(config, mc)

    if args.stage in ("probe", "all"):
        allrows = []
        for mc in models:
            log.info("=== probe %s ===", mc["name"])
            allrows += probe(config, mc)
        write_json(allrows, out_root / "probes_all.json")

        print(f"\n{'=' * 80}\nM3.2 Wang & Gao pattern reproduction — ours vs paper\n{'=' * 80}")
        print("Pass bar is a PATTERN: semantics >> metric ; x ~ chance ; z modest\n")
        print(f"{'':22s} {'x (lateral)':>12s} {'z (depth)':>12s} {'shape':>10s} {'colour':>10s}")
        print(f"{'PAPER (Wang & Gao)':22s} {PAPER['x_r2']:>12.2f} {PAPER['z_r2']:>12.2f} "
              f"{PAPER['shape_r2']:>10.2f} {'—':>10s}")
        for mc in models:
            rows = [r for r in allrows if r["model"] == mc["name"]]
            best = {}
            for t in ("x_lateral", "z_depth", "shape", "color"):
                cand = [r for r in rows if r["target"] == t]
                best[t] = max(cand, key=lambda r: r["value"]) if cand else None
            print(f"{mc['name']:22s} {best['x_lateral']['value']:>12.2f} "
                  f"{best['z_depth']['value']:>12.2f} {best['shape']['value']:>10.2f} "
                  f"{best['color']['value']:>10.2f}")
        print(f"\nwrote {out_root}/probes_all.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
