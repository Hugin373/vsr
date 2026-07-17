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
