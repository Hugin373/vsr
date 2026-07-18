"""Rejection-sampling bias audit for the target-placement guard (advisor ruling 2). [CPU]

    uv run --extra analysis scripts/rejection_bias.py --config configs/m4a_v1_..._pilot.yaml

The placement guard retries object positions until the targets fit in frame and don't overlap. It
is therefore a SELECTION OPERATOR: the camera pose is fixed per image and only positions that fit
GIVEN that pose are accepted. Under camera translation, an extreme pose can make positions on one
side un-placeable, so the accepted positions can correlate with the pose — quietly re-introducing
the very pose↔position correlation the jitter was added to remove (leak-ceiling ruling 1/2).

This runs the placement loop WITHOUT rendering (fast) and logs every proposal (accepted + rejected).
  * ACCEPTED corr(pose, position) — one row per image (the winning proposal). THIS is what gets
    rendered and what a probe could exploit, so it is the PRIMARY measurement.
  * PROPOSED corr — over ALL attempts. A DIAGNOSTIC of the guard's selection pressure only, NOT a
    null: attempt-count varies with pose (hard-to-place extreme poses generate many rejected rows),
    so the proposed stream is over-weighted toward extreme poses and its correlation is inflated.

PREREGISTERED CRITERION: the accepted set is the estimand. A pose↔position correlation is flagged
SIGNIFICANT when |corr_accepted| exceeds 2/√n_images (≈ the 95% band of a zero-correlation null at
this sample size). A significant accepted correlation is a rendered-set bias regardless of its
source; the proposed column then says whether the GUARD introduced it (proposed much smaller) or it
was already in the independent draws (small-sample noise — must re-audit at gate scale).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from sbind.stimuli.sampler import build_scene_specs
from sbind.utils.config import load_config
from sbind.utils.io import write_json
from sbind.utils.logging import get_logger

log = get_logger("sbind.rejbias")

POSE = ["camera_x_delta_m", "camera_y_delta_m", "camera_yaw_delta_deg"]
POSITION = ["near_x", "far_x"]
GUARD_INTRODUCED_GAP = 0.15  # accepted significant AND |proposed| this much smaller ⇒ guard's doing


def _corr(rows: list[dict], a: str, b: str) -> float:
    x = np.array([r[a] for r in rows], dtype=float)
    y = np.array([r[b] for r in rows], dtype=float)
    if x.std() < 1e-9 or y.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    ap = argparse.ArgumentParser(description="Rejection-sampling bias audit (ruling 2).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    config = load_config(args.config)
    seed = int(config["seed"])
    proposals: list[dict] = []
    build_scene_specs(config, seed, proposal_log=proposals)  # no rendering

    accepted = [p for p in proposals if p["accepted"]]
    n_img = len(accepted)
    rate = n_img / len(proposals) if proposals else 0.0
    sig = 2.0 / np.sqrt(n_img) if n_img else 1.0  # ~95% band of a zero-correlation null
    print(f"config: {args.config}")
    print(f"  images={n_img}  proposals={len(proposals)}  acceptance rate={rate:.3f} "
          f"(mean {len(proposals) / max(n_img, 1):.1f} attempts/image)")
    print(f"  significance band |r| > 2/√n = {sig:.3f}\n")

    print(f"  {'pose × position':38s} {'ACCEPTED':>10s} {'proposed':>10s}  flag")
    flagged, guard = [], []
    result = {"acceptance_rate": rate, "sig_threshold": sig, "correlations": {}}
    for pf in POSE:
        for xf in POSITION:
            ca = _corr(accepted, pf, xf)
            cp = _corr(proposals, pf, xf)
            significant = abs(ca) > sig
            guard_introduced = significant and abs(ca) - abs(cp) > GUARD_INTRODUCED_GAP
            if significant:
                flagged.append((pf, xf, ca))
            if guard_introduced:
                guard.append((pf, xf))
            flag = ""
            if significant:
                flag = "  ⚠ SIGNIF" + (" (guard)" if guard_introduced else " (in-draws)")
            print(f"  {pf + ' × ' + xf:38s} {ca:>+10.3f} {cp:>+10.3f}{flag}")
            result["correlations"][f"{pf}__{xf}"] = {
                "accepted": ca, "proposed": cp,
                "significant": significant, "guard_introduced": guard_introduced,
            }

    verdict = "BIASED" if flagged else "CLEAN"
    result["verdict"] = verdict
    print(f"\n  ⇒ rejection-sampling VERDICT: {verdict}"
          + ("" if flagged else " — no significant pose↔position correlation in the rendered set"))
    if flagged:
        worst = max(flagged, key=lambda t: abs(t[2]))
        src = ("GUARD introduced (widen frame / reduce translation)" if guard else
               "in the independent draws too → likely SMALL-SAMPLE noise; re-audit at scale")
        print(f"  ⚠ {len(flagged)} signif; worst {worst[0]}×{worst[1]}={worst[2]:+.3f}. {src}.")
    if args.out:
        write_json(result, Path(args.out))
        log.info("wrote -> %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
