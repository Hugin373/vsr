"""World-frame x IDENTIFIABILITY gate (advisor ruling 1, 2026-07-17). [CPU]

    uv run --extra analysis scripts/worldx_identifiability.py --set $DATA_ROOT/stimuli/<set>

Ruling 1 makes world-frame x (`pos_world[0]`) a SECONDARY target, valid only if it passes its own
raw-pixel identifiability under held-out camera pose — because decorrelation and identifiability
pull in OPPOSITE directions. The VLM never sees camera extrinsics, so world-x is recoverable only
by combining the object's image position with camera pose INFERRED from scene cues. Push the
camera too far and you remove the evidence a pixel model (or human) would need — a low mask
baseline on an unidentifiable target is a Gate-1 failure wearing a decorrelation success's clothes.

This measures the trade-off directly, under a held-out-camera-pose split (translation included in
the pose key, so held-out really holds out the camera move):

  * MASK-ONLY  R² — world-x from the target's image geometry alone. This is the SELECTION baseline
    (what a mask-pooled probe inherits) AND, since mask features ⊂ image features, a LOWER bound on
    identifiability.
  * MASK+POSE  R² — world-x from mask geometry PLUS the true extrinsics. An ORACLE UPPER BOUND on
    what a perfectly-pose-inferring model could recover — "the information is in principle there".
  * HEADROOM = MASK+POSE − MASK-ONLY — the room in which recovering world-x REQUIRES pose inference
    (representation), not image position (selection). Near zero ⇒ world-x ≈ image position ⇒ no
    representation claim possible (descope, like camera-frame x). Positive ⇒ translation opened
    real room.

⚠ MASK+POSE uses the TRUE extrinsics — an upper bound. Whether a real model realises that headroom
from SCENE cues is a separate (gate-scale) question; a small pilot cannot fit a pose-from-pixels
model. z is unaffected either way (depth is not position-coupled) and remains the primary axis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.probes.ridge import ridge_probe
from sbind.utils.io import read_jsonl, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.worldx")

IDENTIFIABLE_MIN = 0.20  # mask+pose above this ⇒ the image determines world-x (Gate-1 pass)
HEADROOM_MIN = 0.05  # pose contribution above this ⇒ world-x is not purely image position


def _load(set_dir: Path):
    anns = list(read_jsonl(set_dir / "annotations.jsonl"))
    mask, extr, xw, pose = [], [], [], []
    for a in anns:
        f = a.get("factors", {})
        if f.get("camera_x_delta_m") is None and f.get("camera_yaw_delta_deg") is None:
            raise SystemExit(f"{set_dir.name}: fixed camera — held-out-pose undefined")
        pose_key = str(
            (
                round(float(f.get("camera_yaw_delta_deg", 0.0)) / 1.5),
                round(float(f.get("camera_pitch_delta_deg", 0.0)) / 1.5),
                round(float(f.get("camera_x_delta_m", 0.0)) / 0.3),
                round(float(f.get("camera_y_delta_m", 0.0)) / 0.3),
            )
        )
        e = [
            f.get("camera_x_delta_m", 0.0),
            f.get("camera_y_delta_m", 0.0),
            f.get("camera_yaw_delta_deg", 0.0),
            f.get("camera_pitch_delta_deg", 0.0),
            f.get("camera_height_delta_m", 0.0),
        ]
        for o in a["objects"]:
            x0, y0, x1, y1 = o["bbox_px"]
            mask.append(
                [(x0 + x1) / 2, (y0 + y1) / 2, o["mask_area_px"], x1 - x0, y1 - y0,
                 o["retinal_size_px"], o["elevation_px"]]
            )
            extr.append(e)
            xw.append(o["pos_world"][0])
            pose.append(pose_key)
    return (
        np.asarray(mask, float),
        np.asarray(extr, float),
        np.asarray(xw),
        np.asarray(pose, dtype=object),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="World-frame x identifiability (held-out pose).")
    ap.add_argument("--set", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    mask, extr, xw, pose = _load(Path(args.set))
    n_groups = len(np.unique(pose))
    mask_only = ridge_probe(mask, xw, "wx_mask", groups=pose).value
    mask_pose = ridge_probe(np.hstack([mask, extr]), xw, "wx_maskpose", groups=pose).value
    headroom = mask_pose - mask_only

    identifiable = mask_pose >= IDENTIFIABLE_MIN
    has_headroom = headroom >= HEADROOM_MIN
    verdict = (
        "KEEP" if (identifiable and has_headroom)
        else ("DESCOPE" if not has_headroom else "FAIL-IDENT")
    )

    print(f"set: {args.set}   objects={len(xw)}   held-out-pose groups={n_groups}\n")
    print(f"  MASK-ONLY  R² = {mask_only:+.4f}   (selection baseline; lower bound on ident.)")
    print(f"  MASK+POSE  R² = {mask_pose:+.4f}   (oracle upper bound — true extrinsics)")
    print(f"  HEADROOM      = {headroom:+.4f}   (pose contribution; room for a repr. claim)")
    print(f"\n  identifiable (MASK+POSE ≥ {IDENTIFIABLE_MIN}): {identifiable}")
    print(f"  headroom     (≥ {HEADROOM_MIN}): {has_headroom}")
    print(f"  ⇒ world-x VERDICT: {verdict}")
    print("  ⚠ MASK+POSE uses TRUE extrinsics (upper bound); realising it from scene cues is a "
          "gate-scale question. z is the primary axis regardless.")

    if args.out:
        write_json(
            {
                "mask_only_r2": mask_only,
                "mask_pose_r2": mask_pose,
                "headroom": headroom,
                "identifiable": identifiable,
                "has_headroom": has_headroom,
                "verdict": verdict,
                "n_groups": n_groups,
            },
            Path(args.out),
        )
        log.info("wrote -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
