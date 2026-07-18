# v1 Leak-Ceiling — v0 → v1 comparison (M4a blocker #10)

Date: 2026-07-18. Tool: `scripts/leak_ceiling.py` (extended this session with structured
held-out splits). Raw JSON per set: `reports/leak_ceiling_v1/*.json`.

**What this measures.** The dumb-features ceiling: R² a probe on **mask geometry alone**
(`centroid_u/v, area, bbox_w/h, retinal_size, elevation`) reaches with **no model at all**. M5's
Δ_repr\|dumb must clear it. §2.7 requires **structured** held-out splits, not random — a random
fold over a factorial battery leaks every factor into training. The random column below is an
upper bound kept only for the v0 comparison; **the gate reads the structured columns.**

## The gate table — z_depth (the PRIMARY metric variable), structured R²

| set | random (UB) | heldout object | heldout depth-range | heldout camera-pose |
|---|---:|---:|---:|---:|
| v0_congruent | 0.972 | 0.375 † | 0.957 | — (fixed camera) |
| natural-congruent (control) | 0.866 | 0.753 | 0.781 | 0.871 |
| **counterbalanced (primary)** | 0.870 | 0.875 | **0.837** | 0.857 |
| conflict | 0.818 | 0.634 | 0.796 | 0.794 |

† v0's 0.375 is the **category↔depth-role confound being removed**, not a low geometric leak —
holding out object identity deletes the shape shortcut v0 had. Counterbalanced fixed that
confound, which is *why* its held-out-object z is now 0.875: the geometry leaks depth robustly
across objects. The clean, both-sets number is **held-out depth-range: v0 0.957 → counterbalanced
0.837.**

## The gate table — x_lateral (camera-frame), structured R²

| set | random (UB) | heldout object | heldout depth-range | heldout camera-pose |
|---|---:|---:|---:|---:|
| v0_congruent | 0.942 | 0.940 | 0.930 | — |
| **counterbalanced** | 0.935 | 0.928 | 0.908 | **0.940** |
| conflict | 0.958 | 0.948 | 0.937 | 0.961 |

**World-frame x (spot check, counterbalanced, held-out camera-pose): R² = 0.915** vs camera-frame
0.940 — nearly the same. So the x leak is **not** a camera-frame-target artifact; the camera
jitter genuinely fails to decorrelate image position from lateral world position.

## Reading (per §2.7 — "if mask geometry still predicts near ceiling in counterbalanced, the
## decorrelation failed; fix the generator, do not proceed")

- **z (primary): PARTIAL improvement, not collapse.** The clean v0→v1 drop is 0.957 → 0.837
  (held-out depth-range). Headroom for the model to exceed did open (v0's 0.99 left none), but the
  residual ~0.84 is high. Its source is **elevation + retinal size**, which are *legitimate
  monocular depth cues* — a physically plausible ground-plane scene cannot remove them (that is
  what the conflict regime is for). So part of this ceiling is **irreducible by construction** and
  is the honest baseline the model must beat, not a bug.
- **x (secondary / the position leak): did NOT improve** (≈0.94 → ≈0.94). World-frame x is still
  0.915 recoverable under held-out camera pose. **Diagnosis (hypothesis, to test — rule 13):
  camera jitter is too weak** (yaw ±3°, pitch ±2.5°, height ±0.12 m). It barely rotates the scene,
  so image position stays tied to lateral position. Fix is a generator parameter: widen the jitter
  ranges and/or add camera lateral translation, then re-measure (cheap).

## Verdict / recommendation (an advisor-level call, not decided here)

This is the §2.7 checkpoint and it reads **do not launch the 1 k render yet.** The decorrelation is
insufficient as configured. Concretely, before the full battery:
1. **Strengthen camera jitter** (bigger yaw/pitch/height; consider lateral translation) and
   re-run this ceiling — target: x structured ceiling drops materially below 0.9.
2. **Decide the z policy:** accept ~0.84 as the (partly irreducible) monocular-cue baseline the
   model must exceed, OR split the leak ceiling into *position/selection* features (fixable) vs
   *monocular-cue* features (inherent) so the two are not conflated in Δ_repr\|dumb.
3. Re-measure, then proceed only if the structured ceiling leaves defensible headroom.

**The blocker did its job:** it caught an insufficient decorrelation *before* the expensive render,
which is exactly why the leak ceiling runs first.

## Verification
- `uv run --extra analysis scripts/leak_ceiling.py --set $DATA_ROOT/stimuli/<set> --out reports/leak_ceiling_v1/<set>.json`
- `uv run pytest tests/test_probes.py` — includes the new grouped-split invariant
  (`test_grouped_split_kills_a_group_confounded_leak`: a group-confounded signal recovered on a
  random split must collapse under a held-out-group split).

---

## Strengthening experiment (2026-07-18) — camera translation added

Added lateral/depth camera **translation** to the generator (the camera was fixed at x=0 and only
panned). New set `m4a_v1_counterbalanced_pilot_j2`: pos_x ±0.3 m, pos_y ±0.2 m, yaw ±4°, pitch ±3°,
height ±0.16 m (60 imgs, validation green). Two things surfaced:

**(1) The tool was regressing the WRONG lateral target.** `leak_ceiling.py` uses `pos_cam[0]` =
**camera-frame** x, which is coupled to image position by the projection identity
`u ≈ f·X_cam/Z_cam + c_x` — **no camera motion can decorrelate it**, so its ~0.94 ceiling is a
definitional identity, not a representational leak (the same trap as v0's x). The
scientifically meaningful target is **world-frame** x (`pos_world[0]`): the model must combine image
position with inferred camera pose to recover it, so the mask alone cannot when the camera varies.

**(2) Translation works on the target that can actually move.** World-frame x leak, held-out camera
pose:

| set | camera | world-x R² | cam-x R² | corr(centroid_u, world-x) |
|---|---|---:|---:|---:|
| counterbalanced pilot | pan-only ±3° | 0.915 | 0.940 | 0.960 |
| **counterbalanced j2** | **+translation ±0.3 m** | **0.817** | 0.929 | 0.915 |

A modest ±0.3 m dolly dropped the world-x leak **0.915 → 0.817**; camera-frame x stayed put (0.94 →
0.93), confirming it is un-decorrelatable. More translation would lower it further, but the
**target-placement guard limits how far it can go** — aggressive jitter (±0.6 m / ±10°) failed to
place non-overlapping in-frame target pairs. Going further needs a **wider FOV / pulled-back camera**
(more scene in frame → room for bigger camera motion), which triggers the §2.2(e) size recalibration.

**Also found & fixed while doing this:** `target_bbox_margin_px` / `target_frame_margin_px` /
`target_placement_attempts` were read from the wrong config section (`constraints` vs `condition`),
so the documented 14/6-px margins silently defaulted to **0** and attempts was stuck at 120 on every
M4a render to date. Fixed (`cf244b3`) with two regression tests; the existing pilots were rendered
with zero target margins and need re-rendering under the corrected wiring regardless.

## Decisions now on the table (advisor-level)

1. **Which lateral target is the claim about** — world-frame x (decorrelatable, meaningful; ~0.82
   and falling with translation) or camera-frame/egocentric x (projection-coupled, un-decorrelatable
   — drop it as a leak target, like v0's x). Update `leak_ceiling.py` to target world-frame x.
2. **How far to push camera motion** — accept ±0.3 m (world-x ≈ 0.82) or widen the FOV / pull the
   camera back to allow more (and recalibrate).
3. **z policy** — z ceiling ≈ 0.82–0.88 is largely monocular cues (elevation + retinal size),
   partly irreducible; accept as the baseline the model must beat, or split position vs monocular
   features in the ceiling.

---

## RETARGETED per advisor ruling 1 (2026-07-17) — world-x is the gate, cam-x is a positive control

`leak_ceiling.py` now targets **world-frame x** (`pos_world[0]`) as the lateral gate and reports
**camera-frame x** (`pos_cam[0]`) as a **projection-coupled POSITIVE CONTROL** (expected band
[0.85, 0.98]; a drop out of band = the geometry features regressed, not a decorrelation). z stays
the primary axis. Two refuted spec sentences (M4a §2.2(b), m3 §2.4(3): "camera jitter makes
camera-frame coordinates no longer image positions") corrected in place with visible retractions.

| set | camera | **cam-x (pos. control)** | **world-x gate** (heldout pose / depth) | z (heldout depth) |
|---|---|---:|---:|---:|
| v0_congruent | fixed | 0.942 ✓ | 0.94 (= cam-x: un-decorrelatable) | 0.957 |
| counterbalanced pilot | pan-only ±3° | 0.935 ✓ | 0.915 / 0.893 | 0.837 |
| **counterbalanced j2** | **+translation ±0.3 m** | 0.923 ✓ | **0.817 / 0.791** | 0.873 |

**Reading.** The positive control holds across all sets (0.92–0.94, in band) — the tool reads the
projection identity correctly, so a *drop* in world-x is a real decorrelation, not a tool artifact.
World-x: v0 0.94 (fixed camera, world-x = image position) → j2 0.82 with a ±0.3 m dolly. z is
unmoved by translation (~0.84–0.88), as expected since depth is not position-coupled (image
position fixes X/Z, not Z). **⚠ world-x's 0.82 counts as a decorrelation success ONLY if world-x
also passes raw-pixel identifiability under held-out pose** (ruling 1) — that Gate-1 check is the
next owed step; if world-x is not pixel-identifiable, it is descoped and the depth core is
unaffected. **Still pending:** the B0/B1/B2 z-baseline split (ruling 3), re-render under fixed
placement wiring, and the rejection-sampling bias check (ruling 2).

---

## World-x IDENTIFIABILITY gate (ruling 1's owed step) — DONE

`scripts/worldx_identifiability.py`, held-out camera pose (translation in the pose key). Tests the
decorrelation⊥identifiability trade-off directly: MASK-ONLY (selection baseline / identifiability
lower bound) vs MASK+POSE (oracle upper bound, true extrinsics). HEADROOM = the room where
recovering world-x *requires* pose inference (representation), not image position (selection).

| set | camera | mask-only | mask+pose (oracle) | headroom | verdict |
|---|---|---:|---:|---:|:--|
| counterbalanced pilot | pan-only ±3° | 0.915 | 0.935 | +0.020 | **DESCOPE** |
| **counterbalanced j2** | **+translation ±0.3 m** | 0.817 | 0.922 | **+0.105** | **KEEP** |

**Verdict: the ±0.3 m translation is exactly what makes world-x a viable target.** With pan only,
pose contributes ~nothing (world-x ≈ image position → no representation claim possible, descope
like camera-frame x). With translation, the selection baseline drops (0.915→0.817) while the info
ceiling barely moves (0.935→0.922), so recovering world-x now *requires* inferring camera pose —
which is representation, not selection. world-x is **identifiable AND has ~0.10 headroom → KEEP**,
as a SECONDARY target; the primary axis z is unaffected either way.

⚠ Two honest caveats: (1) MASK+POSE uses TRUE extrinsics — an upper bound; whether a model realises
that 0.10 from SCENE cues (not given the pose) is a gate-scale question a 60-image pilot can't
settle. (2) The verdict endorses ruling 2's ±0.3 m: it clears world-x's gate without the
identifiability loss that more aggressive translation risks.
