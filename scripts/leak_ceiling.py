"""The DUMB-FEATURES CEILING: what a probe gets with NO model at all. [CPU]

    uv run --extra analysis scripts/leak_ceiling.py --set $DATA_ROOT/stimuli/v0_congruent

Standing methodology (CLAUDE.md rule 12, IMPLEMENTATION_PLAN M5). A shuffled-label control
catches a probe fitting *noise*; it cannot catch a probe reading a trivially available
**non-representational** feature. **Decodability only counts ABOVE this ceiling.**

Two findings that passed every shuffled-label control and died only here:
  * mask GEOMETRY alone predicts lateral position at R2 = 0.942 and depth at R2 = 0.972 on the
    v0 set — the model's activations added ~0.05. Mask-pooling *selects its tokens by the
    object's image position*, so the selection IS the answer;
  * a shape-only constant strategy scored 55.1% on "which is closer" before category was
    balanced against the near/far depth role.

Why this matters beyond bookkeeping: mask-pooled VISUAL-token probes inherit the position leak,
bound-TEXT-token probes do not. So the four-site grid's central contrast (visual high, text low)
could be manufactured by the measurement itself — which is exactly the contrast that separates
"metric survives in visual tokens and dies at binding" from "metric was never there".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.probes.ridge import logistic_probe, ridge_probe
from sbind.utils.io import read_jsonl, write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.leak")

# Everything a probe could read WITHOUT the model having represented anything.
GEOM_NAMES = [
    "centroid_u",  # where the mask sits horizontally  <- this alone nearly solves x
    "centroid_v",  # ...and vertically                 <- with size, nearly solves z
    "mask_area_px",
    "bbox_w",
    "bbox_h",
    "retinal_size_px",
    "elevation_px",
]


def _pose_bin(f: dict) -> str | None:
    """A camera-pose group key from the per-image jitter deltas, or None if the set has a
    FIXED camera (v0 has no such fields) — held-out-pose is then undefined and correctly skipped.
    Includes lateral/depth TRANSLATION deltas when present (0.3 m buckets), so held-out-pose holds
    out the camera translation, not only the pan."""
    y, p = f.get("camera_yaw_delta_deg"), f.get("camera_pitch_delta_deg")
    if y is None or p is None:
        return None
    key = f"{round(float(y) / 1.5)}|{round(float(p) / 1.5)}"  # ~1.5-deg pan buckets
    dx, dy = f.get("camera_x_delta_m"), f.get("camera_y_delta_m")
    if dx is not None:
        key += f"|{round(float(dx) / 0.3)}|{round(float(dy or 0.0) / 0.3)}"  # 0.3 m buckets
    return key


def dumb_features(
    anns: list[dict],
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Flatten objects -> (geometry matrix, targets, structured-split group keys).

    Groups are built in the SAME iteration order as the rows, so they stay aligned. A group key
    that cannot be derived for a set (e.g. camera pose on the fixed-camera v0) is dropped from the
    returned dict, so a held-out split is only offered where it is actually defined."""
    G, x, z, shape, color = [], [], [], [], []
    g_obj, g_depth, g_pose = [], [], []
    pose_ok = True
    for a in anns:
        f = a.get("factors", {})
        for o in a["objects"]:
            x0, y0, x1, y1 = o["bbox_px"]
            G.append(
                [(x0 + x1) / 2, (y0 + y1) / 2, o["mask_area_px"], x1 - x0, y1 - y0,
                 o["retinal_size_px"], o["elevation_px"]]
            )
            x.append(o["pos_cam"][0])
            z.append(o["depth_m"])
            shape.append(o["category"])
            color.append(o["name"].split("_")[0])
            g_obj.append(o["category"])  # held-out OBJECT IDENTITY
            g_depth.append(int(o["depth_m"] // 0.5))  # held-out DEPTH RANGE (0.5 m bins)
            pb = _pose_bin(f)  # held-out CAMERA POSE (v1 only)
            pose_ok = pose_ok and pb is not None
            g_pose.append(pb)
    targets = {
        "x_lateral": np.asarray(x),
        "z_depth": np.asarray(z),
        "shape": np.asarray(shape),
        "color": np.asarray(color),
    }
    groups = {
        "heldout_object_identity": np.asarray(g_obj, dtype=object),
        "heldout_depth_range": np.asarray(g_depth, dtype=object),
    }
    if pose_ok:
        groups["heldout_camera_pose"] = np.asarray(g_pose, dtype=object)
    return np.asarray(G, dtype=float), targets, groups


def main() -> int:
    ap = argparse.ArgumentParser(description="Dumb-features (leak) ceiling for a stimulus set.")
    ap.add_argument("--set", required=True, help="path to a rendered stimulus set dir")
    ap.add_argument(
        "--out", help="write the ceiling JSON (for M5's Delta = probe - ceiling)"
    )
    args = ap.parse_args()

    anns = list(read_jsonl(Path(args.set) / "annotations.jsonl"))
    if not anns:
        print(f"no annotations in {args.set}", file=sys.stderr)
        return 1
    G, targets, groups = dumb_features(anns)
    print(f"set: {args.set}  objects={len(G)}  dumb features={GEOM_NAMES}\n")

    out: dict[str, dict] = {"random": {}, "structured": {}}

    # (1) RANDOM split — the historical baseline. ⚠ an OVERESTIMATE on a factorial battery: a
    # random fold leaks every factor into training. Kept only for the v0 comparison / as an
    # upper bound. The GATE reads the STRUCTURED numbers below (§2.7 / evaluation-law clause 2).
    print("--- RANDOM-split ceiling (upper bound; NOT the gate — see structured below) ---")
    for name, y in targets.items():
        if name in ("shape", "color"):
            r = logistic_probe(G, y, name)
            print(f"  {name:10s} acc = {r.value:.4f}   (shuffled ctrl {r.control:.3f})")
        else:
            r = ridge_probe(G, y.astype(float), name)
            print(f"  {name:10s} R2  = {r.value:+.4f}   (shuffled ctrl {r.control:+.3f})")
        out["random"][name] = r.value

    # (2) STRUCTURED held-out splits — the gate measurement. Hold out whole object identities /
    # depth ranges / camera poses so the ceiling cannot be reached by memorising a leaked factor.
    print("\n--- STRUCTURED held-out ceiling (THE GATE: does the leak survive decorrelation?) ---")
    for gname, g in groups.items():
        print(f"  [{gname}]  ({len(np.unique(g))} groups)")
        out["structured"][gname] = {}
        for name in ("x_lateral", "z_depth"):
            try:
                r = ridge_probe(G, targets[name].astype(float), name, groups=g)
                print(f"     {name:10s} R2 = {r.value:+.4f}   (shuffled ctrl {r.control:+.3f})")
                out["structured"][gname][name] = r.value
            except ValueError as e:
                print(f"     {name:10s} SKIP ({e})")
                out["structured"][gname][name] = None

    print("\nThe STRUCTURED numbers are the leak floor a model probe must EXCEED to show the "
          "quantity is in the REPRESENTATION, not the mask. If they stay near ceiling in the "
          "counterbalanced regime, the decorrelation failed (§2.7 — fix the generator first).")
    if args.out:
        write_json(out, Path(args.out))
        log.info("wrote ceiling -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
