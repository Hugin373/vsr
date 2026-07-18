"""B0/B1/B2 baseline decomposition of the dumb-feature ceiling (advisor ruling 3). [CPU]

    uv run --extra analysis scripts/baseline_decomposition.py --set $DATA_ROOT/stimuli/<set>

Ruling 3 splits the "what a probe gets with no model" baseline into THREE groups, because they are
NOT equivalent and must not be lumped:

  B0 SELECTION   — where the mask sits: centroid_u, centroid_v. The mask-pooling operator recovers
                   this trivially, so for a target that IS an image position (lateral x) it is
                   circular. THE FIXABLE ARTIFACT — must be controlled.
  B1 MONOCULAR   — apparent-size + elevation cues: mask area, bbox w/h, retinal size, elevation_px.
                   LEGITIMATE depth evidence. A genuine depth representation may BE the integration
                   of these, so requiring the model to beat B1 demands information the image does
                   not contain. NOT a competitor — preserved, not controlled.
  B2 SEMANTIC    — category, colour, physical size: identity priors. If these predict depth the set
                   is confounded (the old 55.1% shape-only failure). THE PRIOR CONFOUND, controlled.

PREREGISTERED PRIMARY CRITERION for M5 (recorded here; needs M4b activations to evaluate):
  Δ_R|B0,B2 = S(B0 ∪ B2 ∪ R) − S(B0 ∪ B2)  — the representation's gain over selection + priors,
  with legitimate monocular evidence B1 NEITHER given to the baseline NOR required to be beaten.
  Δ_R|B0,B1,B2 (gain over ALL cues) is reported DESCRIPTIVELY, never as the sole gate.

At M4a there is no R (no VLM), so this reports the baseline groups S(B0), S(B1), S(B2), S(all).
Reading: B0 high on world-x = the selection issue (why camera motion matters); B1 high on z =
the legitimate monocular ceiling; B2 near chance = the set is not identity-confounded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.probes.ridge import ridge_probe
from sbind.utils.io import read_jsonl, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.basedecomp")

B0_NAMES = ["centroid_u", "centroid_v"]
B1_NAMES = ["mask_area_px", "bbox_w", "bbox_h", "retinal_size_px", "elevation_px"]


def _pose_key(f: dict):
    if f.get("camera_yaw_delta_deg") is None:
        return None
    return (
        round(float(f.get("camera_yaw_delta_deg", 0.0)) / 1.5),
        round(float(f.get("camera_pitch_delta_deg", 0.0)) / 1.5),
        round(float(f.get("camera_x_delta_m", 0.0)) / 0.3),
        round(float(f.get("camera_y_delta_m", 0.0)) / 0.3),
    )


def _build(anns):
    """Flatten objects -> B0/B1/B2 feature matrices, targets, and structured group keys."""
    cats = sorted({o["category"] for a in anns for o in a["objects"]})
    cols = sorted({o["name"].split("_")[0] for a in anns for o in a["objects"]})
    b0, b1, b2, z, xw, g_pose, g_depth = [], [], [], [], [], [], []
    pose_ok = True
    for a in anns:
        f = a.get("factors", {})
        pk = _pose_key(f)
        pose_ok = pose_ok and pk is not None
        for o in a["objects"]:
            x0, y0, x1, y1 = o["bbox_px"]
            b0.append([(x0 + x1) / 2, (y0 + y1) / 2])
            b1.append(
                [o["mask_area_px"], x1 - x0, y1 - y0, o["retinal_size_px"], o["elevation_px"]]
            )
            col = o["name"].split("_")[0]
            b2.append(
                [1.0 * (o["category"] == c) for c in cats]
                + [1.0 * (col == c) for c in cols]
                + [float(o.get("size_m", 0.0))]
            )
            z.append(o["depth_m"])
            xw.append(o["pos_world"][0])
            g_pose.append(str(pk))
            g_depth.append(int(o["depth_m"] // 0.5))
    groups = {"heldout_depth_range": np.asarray(g_depth, dtype=object)}
    if pose_ok:
        groups["heldout_camera_pose"] = np.asarray(g_pose, dtype=object)
    feats = {
        "B0_selection": np.asarray(b0, float),
        "B1_monocular": np.asarray(b1, float),
        "B2_semantic": np.asarray(b2, float),
    }
    feats["B0B1B2_all"] = np.hstack(
        [feats["B0_selection"], feats["B1_monocular"], feats["B2_semantic"]]
    )
    targets = {"z_depth": np.asarray(z, float), "x_world": np.asarray(xw, float)}
    return feats, targets, groups


def main() -> int:
    ap = argparse.ArgumentParser(description="B0/B1/B2 baseline decomposition (ruling 3).")
    ap.add_argument("--set", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    anns = list(read_jsonl(Path(args.set) / "annotations.jsonl"))
    feats, targets, groups = _build(anns)
    gname = "heldout_camera_pose" if "heldout_camera_pose" in groups else "heldout_depth_range"
    g = groups[gname]
    print(f"set: {args.set}   objects={len(g)}   split: {gname}\n")

    result = {"split": gname, "scores": {}}
    hdr = f"  {'target':10s} {'B0 select':>11s} {'B1 monoc':>10s} {'B2 semantic':>12s} {'all':>8s}"
    print(hdr)
    for tname, y in targets.items():
        row = {}
        for gk in ("B0_selection", "B1_monocular", "B2_semantic", "B0B1B2_all"):
            row[gk] = ridge_probe(feats[gk], y, f"{tname}/{gk}", groups=g).value
        result["scores"][tname] = row
        print(f"  {tname:10s} {row['B0_selection']:>+13.3f} {row['B1_monocular']:>+13.3f} "
              f"{row['B2_semantic']:>+12.3f} {row['B0B1B2_all']:>+8.3f}")

    print("\n  Reading (ruling 3): B0 controls the SELECTION artifact; B1 is LEGITIMATE monocular "
          "evidence (not a competitor); B2 near chance ⇒ set not identity-confounded.")
    print("  Preregistered M5 gate: Δ_R|B0,B2 (gain over selection+priors, B1 preserved). "
          "Δ over all cues is descriptive only. Needs M4b activations.")
    zb2 = result["scores"]["z_depth"]["B2_semantic"]
    if zb2 > 0.15:
        print(f"  ⚠ B2→z = {zb2:+.3f} > 0.15: identity priors predict depth — possible confound.")
    if args.out:
        write_json(result, Path(args.out))
        log.info("wrote -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
