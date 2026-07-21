# M4a-Solo — Stage 1 protocol (representation localization)

Ratified 2026-07-21. Status of the pair track, recorded verbatim as ruled:

> The corrected role-boundary logic reproduces the cumulative extremum exactly. No substantive
> load-bearing verification exceedance remains.

> **F = 1.225 is the frozen robust operating floor, selected within an empirically stable range
> rather than claimed as the exact mathematical minimum.**

Optimizer and global-minimum search are **formally retired**.

## The Solo question is INCREMENTAL, never raw decodability

`r(depth, image v) = −0.747` in the solo set — elevation is a strong, *real* monocular cue that is
deliberately left intact. So a raw probe score can be high while the representation contributes
nothing. **The question must never be written as "can depth be decoded from the representation?"**
It is:

> Does the model representation provide depth information **beyond observable geometric cues**?

$$\Delta_{\text{repr}\mid B} = S(B \cup H_l) - S(B)$$

Raw probe $R^2$ is reported, but it is not the claim; $\Delta R^2_l = R^2(B + H_l) - R^2(B)$ is.

## Three baseline levels, all reported

**B0 — explicit projective geometry:** centroid (u, v) · bbox width/height · mask area · apparent
size · image elevation · border distances · category · physical-size multiplier.
*Answers: how much depth do explicit geometric features already give?*

**B1 — pixel-only supervised model:** small CNN, or frozen visual backbone + linear head.
*Answers: is there depth signal in the image beyond hand-crafted geometry?*

**Model representation:** per layer, $H_l \to z$ and $B + H_l \to z$, reporting $\Delta R^2_l$.

## Readouts — mask pooling alone is not enough

Mask pooling is already known to carry geometry, so compare, at minimum: global visual-token mean ·
object-mask pooled · bbox pooled · fixed spatial strip/patch · LM-input visual tokens · projector
output.

⚠ If object-mask pooling beats global but the increment is fully explained by area/centroid, that is
**not** an object-centric depth representation. The valuable result is

$$\Delta_{\text{object readout}\mid \text{geometry}} > \Delta_{\text{global readout}\mid \text{geometry}}$$

holding under held-out camera and held-out size.

## Positive controls FIRST

Before any depth result is interpreted: category ID high · world-x readable · apparent size/area
readable · depth bin at least readable by the pixel baseline. **If category or world-x cannot be
read, the fault is extraction/pooling — not a missing depth representation.**

## Two-step pilot (n matters)

**Smoke pilot, 200–400** — renderer, annotation/mask consistency, extraction pipeline, feature
shapes, positive-control plumbing. **No scientific conclusion drawn.**

**Scientific pilot, ≥ 1,200** — the full sampler allocation, so held-out depth-bin / category /
camera-pose / physical-size / joint-nuisance splits are all constructible. A 200–400 set cannot
support layerwise probing of a 7B VLM's hidden states under held-out splits without inviting a
small-sample false positive.

## Realized-distribution independence — MEASURED, passes

Marginal independence is not sufficient; category × size interaction and the **post-placement**
distribution were checked (n = 1200, realized not assignment):

| check | η² |
|---|---:|
| category → depth | 0.0015 |
| size multiplier → depth | 0.0002 |
| **category × size → depth** | **0.0050** |

Per-category realized depth 2.95–6.65 m (means 4.76–4.86); per-size 2.95–6.65 m (means 4.79–4.82).
Heavy overlap, no partitioning — neither factor nor their interaction predicts depth.

## Standing division of labour

**Solo** = where depth-related signal is readable, whether it exceeds the geometry baseline, how it
changes across the projector, object-local vs global readout. **Localization, not final thesis
evidence.**
**Pair** = binding to the correct object, ordinal/ratio comparison, cue-conflict fusion, causal use.
**Distractor** = selector robustness under clutter; extension, not blocker.
