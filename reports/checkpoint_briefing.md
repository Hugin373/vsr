# Checkpoint briefing

Date: 2026-07-21 · repo state at commit `cb8df2e` (+ this commit)

**Question.** Render the 1,200-image Solo-Orthogonalized set, confirm the calibrated envelope holds
on real rendered data, and measure the baselines the Stage-1 probe will be judged against.

**Method.** 1,200 images rendered (34 min, 1.70 s/img), full validator, then B0/B1/B2 baselines with
5-fold CV ridge, fold-level SD reported, and the held-out splits the probe is specified to use. The
baseline taxonomy was validated by its own instrument checks before any fit.

## Render and baselines — as designed

**Validator: ALL CHECKS GREEN.** 1200/1200 unique depths, retinal median 88 px (61% in the 60–120
band). Taxonomy check passed: max cross-group reconstruction R² = 0.9478 (< 0.995 threshold).

| baseline | R² (5-fold) | fold SD |
|---|---:|---:|
| B0_position | **0.486** | 0.060 |
| B1_appearance | 0.483 | 0.025 |
| B2_semantic | **−0.004** | 0.002 |
| **B0 ∪ B2 — Claim A baseline** | **0.868** | 0.018 |
| B0∪B1∪B2 — Claim B baseline | 0.949 | 0.005 |

B0 = 0.486 on rendered data confirms the 300-image calibration (0.468) and passes the pre-committed
hard target (≤ 0.60). B2 is dead. **Claim A headroom = 0.132** (calibration predicted 0.156 — the
real value is slightly worse, as the rendered numbers have been every time).

## 🔴 The held-out splits as specified are UNUSABLE

| split | R² | fold SD |
|---|---:|---:|
| held-out size multiplier | 0.766 | 0.120 |
| held-out category | 0.097 | **1.213** |
| **held-out depth bin** | **−15.130** | 13.129 |

Diagnosed to **two compounding causes, both design flaws in the split rather than model failures:**

1. **Extrapolation at the extremes.** Holding out depth bin 0 or 4 removes the end of the training
   range entirely — R² = −30.4 and −33.7 — because a linear model must extrapolate beyond every
   depth it has seen.
2. **A metric artifact that hits even the interior bins.** R² within one held-out bin is computed
   against *that bin's* variance, and each bin's depth SD is only ~0.15 m against the full set's
   1.14 m. So a model predicting depth well in absolute terms still scores hugely negative:
   interior bins give −7.6, −5.0, −4.6. **Interior-only holdout does not fix this.**

Held-out category is separately unstable — 4 groups, fold SD 1.213, so the aggregate 0.097 hides
folds that are catastrophically bad.

**Established.** The stimulus set is rendered, valid, and has the intended baseline structure. The
envelope decision transfers from calibration to full rendered data.

**NOT established.** Nothing about representations. And the probe's evaluation protocol is not yet
sound — reporting Δ = S(B∪H) − S(B) where both terms are ≈ −5 to −30 would be meaningless.

**Weakest point.** I specified these splits, ran them, and only caught the problem because
fold-level SD was required alongside the aggregate. Had I reported only the mean, held-out category
at 0.097 would have read as "poor generalization" rather than "unstable measurement", and held-out
depth would have read as a finding about depth rather than an artifact of within-bin variance. The
instruction to report fold variability is what surfaced it.

**Open decision — the evaluation metric for grouped splits.** Options: (a) score held-out folds
against the FULL-set variance rather than the fold's, making R² comparable across splits;
(b) use MAE / RMSE in metres, which has no variance-normalisation problem; (c) keep grouped splits
for *ranking* (Spearman) and use random splits for magnitude; (d) hold out contiguous depth
*ranges* wider than one bin so the test set has real variance. I lean (b)+(a) reported together —
absolute error is interpretable for depth and immune to this artifact.

**Next step.** Fix the evaluation protocol before extracting any model features. That is pure
analysis, no rendering, and it must be settled first: the probe's headline number is an increment
between two scores, so a broken score makes the increment uninterpretable regardless of what the
representations contain.
