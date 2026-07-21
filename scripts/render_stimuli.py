"""Render a stimulus set from a config: config -> images + masks + annotations.jsonl.

Usage:
    uv run --extra stimuli scripts/render_stimuli.py --config configs/stimuli_v0_congruent.yaml
    ... --limit 5          # render only the first N (smoke test)
    ... --resume           # skip images whose annotation already exists

Deterministic: the whole set is a pure function of (config, seed). Rendering is pure
CPU (Cycles) — no GPU claimed. Writes a copy of the resolved config next to the data.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from sbind.stimuli.render_bpy import render_scene
from sbind.stimuli.sampler import build_scene_specs, build_solo_scene_specs
from sbind.utils.config import load_config, run_metadata
from sbind.utils.io import ensure_dir, read_jsonl, write_json, write_jsonl
from sbind.utils.logging import get_logger

log = get_logger("sbind.render")


def main() -> int:
    ap = argparse.ArgumentParser(description="Render a stimulus set from a config.")
    ap.add_argument("--config", required=True, help="path to a stimulus-set YAML")
    ap.add_argument("--limit", type=int, default=None, help="render only the first N images")
    ap.add_argument("--resume", action="store_true", help="skip already-rendered ids")
    args = ap.parse_args()

    config = load_config(args.config)
    seed = int(config["seed"])
    set_name = config["output"]["set_name"]
    out_dir = ensure_dir(Path(config["output"]["root"]) / set_name)

    # M4a-Solo (Stage 1) uses a different sampler: one object, no near/far roles, no congruence
    # floor. Dispatch on the declared regime rather than sniffing the factor keys.
    regime = (config.get("condition") or {}).get("regime")
    if regime == "solo":
        log.info("regime=solo -> single-object sampler (no pair/congruence machinery)")
        specs = build_solo_scene_specs(config, seed)
    else:
        specs = build_scene_specs(config, seed)
    if args.limit is not None:
        specs = specs[: args.limit]

    ann_path = out_dir / "annotations.jsonl"
    done: set[str] = set()
    existing: list[dict] = []
    if args.resume and ann_path.exists():
        existing = list(read_jsonl(ann_path))
        done = {r["id"] for r in existing}
        log.info("resume: %d annotations already present", len(done))

    # persist the resolved config + run metadata for reproducibility
    write_json(run_metadata(config, seed), out_dir / "run_metadata.json")
    (out_dir / "config.yaml").write_text(Path(args.config).read_text(), encoding="utf-8")

    records: list[dict] = list(existing)
    t0 = time.time()
    rendered = 0
    for spec in specs:
        if spec.id in done:
            continue
        ann = render_scene(spec, out_dir, config["render"])
        records.append(ann.to_dict())
        rendered += 1
        # checkpoint the jsonl every 25 images so a kill loses little work
        if rendered % 25 == 0:
            records.sort(key=lambda r: r["id"])
            write_jsonl(records, ann_path)
            dt = time.time() - t0
            log.info("%d/%d rendered (%.2f s/img)", rendered, len(specs) - len(done), dt / rendered)

    records.sort(key=lambda r: r["id"])
    write_jsonl(records, ann_path)
    log.info(
        "done: %d newly rendered, %d total -> %s (%.1f min)",
        rendered,
        len(records),
        ann_path,
        (time.time() - t0) / 60.0,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
