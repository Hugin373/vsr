# M4a Stimulus Battery Pilot Report

Date: 2026-07-16

Status: pilot implementation and result analysis started; M4a is not complete. The three-regime pilot renders, validates, and produces oracle-feature analyses, but the full M4a gate still needs full-scale image-identifiability, true contrastive matched pairs, determinism byte-compare on the M4a outputs, and a human spot-check/contact sheet.

## What Was Implemented

- Added M4a regimes: `natural_congruent`, `counterbalanced`, `conflict`, plus a scaffold config for `contrastive_pairs`.
- Added continuous lateral sampling, camera height/pitch/yaw jitter, lighting/ground variation, optional distractors, and target-placement guards.
- Added canonical procedural stand-ins for `chair`, `mug`, and `bottle` alongside cube/sphere/cylinder. These are not imported CC0 assets yet, so they are acceptable for the pilot but not the final asset claim.
- Added solo-object ID passes and amodal mask annotations: `mask_amodal`, `bbox_px_amodal`, `retinal_size_px_amodal`, `mask_area_px_amodal`, and `occlusion_ratio`.
- Added simple question records to stimulus annotations.
- Added `scripts/m4a_analyze_stimuli.py` for oracle geometric-image feature checks under held-out object/camera/depth/cue splits.
- Updated validation so target occlusion is a hard failure, while distractor occlusion is reported but allowed.

## Size Calibration

Calibrated at target apparent height 90 px, reference depth 4.4948 m, final spread 0.0 px:

| category | size_m |
|---|---:|
| cube | 0.6660 |
| sphere | 0.8090 |
| cylinder | 0.6660 |
| chair | 0.7353 |
| mug | 0.9913 |
| bottle | 0.8378 |

Recorded in `configs/m4a_v1_size_calibration.yaml` and copied into the M4a configs. Strict target placement margins are now explicit in the YAML configs rather than hidden as code defaults.

## Rendered Pilot Sets

| regime | config | images | target objects | all objects | distractors |
|---|---|---:|---:|---:|---|
| natural-congruent | `configs/m4a_v1_natural_congruent_pilot.yaml` | 40 | 80 | 87 | 33 images with 0, 7 with 1 |
| counterbalanced | `configs/m4a_v1_counterbalanced_pilot.yaml` | 60 | 120 | 132 | 48 images with 0, 12 with 1 |
| conflict | `configs/m4a_v1_conflict_pilot.yaml` | 40 | 80 | 87 | 33 images with 0, 7 with 1 |

## Output Validation

All three pilot sets pass `scripts/validate_stimuli.py` with zero hard violations.

| regime | worst near/far height | worst near/far area | min depth ratio | min bbox-bottom gap | note |
|---|---:|---:|---:|---:|---|
| natural-congruent | 1.8361 | 1.3092 | 1.8542 | 69 px | natural size cues agree |
| counterbalanced | 0.7766 | 0.3909 | 1.0801 | 13 px | size cues intentionally decorrelated; 1 occluded distractor reported |
| conflict | 0.7188 | 0.2474 | 1.0848 | 7 px | size cue intentionally conflicts |

Amodal checks are green across all objects: no missing/empty amodal masks, no amodal bbox/height/area mismatch, visible masks are subsets of amodal masks, and target `occlusion_ratio` is zero.

## Oracle Image-Feature Analysis

The analysis uses oracle geometric image features, not VLM activations. This answers whether the rendered image contains enough signal for a simple supervised readout. Thresholds were `acc >= 0.70` and `R2 >= 0.20`.

| regime | ordinal depth acc, held-out depth gap | ratio depth R2, held-out depth gap | lateral x R2, held-out camera pose | z depth R2, held-out object identity | interpretation |
|---|---:|---:|---:|---:|---|
| natural-congruent | 1.000 PASS | -0.252 FAIL | 0.840 PASS | 0.695 PASS | control only; ratio range is narrow and shortcut-heavy |
| counterbalanced | 0.967 PASS | 0.803 PASS | 0.948 PASS | 0.518 PASS | primary pilot regime clears target-variable gates |
| conflict | 1.000 PASS | 0.420 PASS | 0.958 PASS | 0.299 PASS | usable for cue-integration, weaker z/object split |

Key correlations with depth:

| regime | depth-retinal r | depth-size r |
|---|---:|---:|
| natural-congruent | -0.929 | -0.076 |
| counterbalanced | -0.807 | 0.033 |
| conflict | -0.591 | 0.444 |

The counterbalanced pilot reduces physical-size/depth correlation to near zero but apparent size remains correlated with depth, as expected for monocular images where retinal size is a real cue. The full M4a image-identifiability gate should report these dumb-feature ceilings explicitly rather than treating them as failures.

## Retired Artifacts (2026-07-17) — recorded, not silently dropped

- **DELETED `$DATA_ROOT/stimuli/m4a_v1_counterbalanced/`** — 60 images carrying the FULL-battery
  name while its own `config.yaml` / `run_metadata.json` declared `n_images: 420` (aborted run).
  It was **unreproducible**: the stamp said `git_hash: 725ad42`, but
  `configs/m4a_v1_counterbalanced.yaml` did not exist at that commit (added in `6c93848`) — the
  tree was dirty and that generator state was never committed. Deleting lost nothing recoverable.
  The active hazard was `render_stimuli.py --resume`, which **skips ids whose annotation already
  exists**: a later 420-image run with `--resume` would have rendered 360 and silently inherited
  60 stale images from a different generator, with every validator green.
- **DELETED `reports/m4a_smoke_analysis.json`** — it analysed exactly that set, so it was an
  analysis of a 60-image fragment of a 420-image config produced by uncommitted code. Superseded
  by `m4a_counterbalanced_pilot_analysis.json` (the proper `_pilot` set). Git retains the history.
- **FIXED the cause, not just the symptom:** `utils/config.git_hash()` recorded a bare `HEAD` and
  **never inspected the working tree**, so the plan's §1 promise ("every run logs config, git
  hash, seed") was silently false for every run from a dirty tree. It now suffixes `-dirty`, and
  `run_metadata` records `git_dirty` + `git_patch_sha`. **Untracked files count as dirty** — the
  case above was driven by an untracked config, which a `git diff HEAD`-only check would miss.
  Six tests, verified to FAIL against the old implementation.

## Remaining M4a Blockers

- True contrastive matched pairs are not implemented yet; only the config scaffold exists.
- The pilot is 140 images total, not the planned ~1k gate-scale pilot or 5-10k final battery.
- Determinism has not yet been re-verified by byte-comparing M4a annotations/masks and measuring pixel tolerance on rerendered images.
- No human spot-check/contact sheet has been generated for the M4a pilot.
- The canonical new object classes are procedural stand-ins, not imported CC0 assets.
- Natural-congruent ratio recovery fails under held-out depth-gap/object-pair/cue splits; keep it as a control, not the localization claim regime.
  - ⚠ **REASON CORRECTED 2026-07-19** (`reports/m4a_cue_constants.md` §4, measured). The line above
    once read that the ratio range there is "narrow and shortcut-heavy". Measured: the 1.85 floor sits
    ABOVE the entire ratio range the design produces (available 1.046–1.474), so acceptance fraction is
    **0.000** and **100%** of images are clamped into the floor band. The accepted depth ratio is
    `1.85 × (1 + U(0, 0.08))` — an independent uniform draw. `r(ratio, depth_gap_bin)` collapses
    **+0.906 → −0.017**, while the two passing regimes keep +0.905 → +0.905. A negative R² is the
    expected signature of regressing on independent noise, so **R² = −0.252 is a design artifact, not a
    property of depth**. It is NOT a mis-set constant: the derived worst-case congruence requirement is
    1.7661 and 1.85 clears it by +4.75%, but 1.7661 already exceeds the maximum available ratio 1.474 —
    area congruence and an informative ratio target are incompatible for this six-category set as
    currently (height-)calibrated. Design options recorded, none chosen.

## Cue Constants (2026-07-19, blocker #9 — CLOSED)

Six-category worst-case `cue_constants` are committed to every M4a config with full provenance,
derived per regime from 1200-scene dense silhouette sweeps (198–202 samples per category×role cell,
up from ~23 in the pilots). Binding requirement 1.7661 / 1.8671 / 1.8526 for
natural-congruent / counterbalanced / conflict; area binds in all three, at near=bottle/far=cube.
Schema now supports shared · per-object · explicit sizing with hard-fail and no fallback. Full
report: `reports/m4a_cue_constants.md`.

## Verification Commands

- `uv run --extra stimuli scripts/render_stimuli.py --config configs/m4a_v1_natural_congruent_pilot.yaml`
- `uv run --extra stimuli scripts/render_stimuli.py --config configs/m4a_v1_counterbalanced_pilot.yaml`
- `uv run --extra stimuli scripts/render_stimuli.py --config configs/m4a_v1_conflict_pilot.yaml`
- `uv run --extra stimuli scripts/validate_stimuli.py --set /data3/hugin/vsr/stimuli/m4a_v1_natural_congruent_pilot`
- `uv run --extra stimuli scripts/validate_stimuli.py --set /data3/hugin/vsr/stimuli/m4a_v1_counterbalanced_pilot`
- `uv run --extra stimuli scripts/validate_stimuli.py --set /data3/hugin/vsr/stimuli/m4a_v1_conflict_pilot`
- `uv run --extra analysis scripts/m4a_analyze_stimuli.py --set ... --out ...`
- `uv run ruff check src/ tests/ scripts/`
- `uv run pytest tests/test_sampler.py tests/test_render_consistency.py tests/test_schemas.py tests/test_geometry.py`
