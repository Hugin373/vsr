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

---

# AMENDMENT 2026-07-21 — 1,200 render HALTED; camera-envelope calibration first

Smoke test (n=200, rendered) found a design problem that would change Stage-1 interpretation:

$$R^2(B0_{\text{position}}) = 0.799$$

Object image position alone explains ~80% of depth variance. Not a pipeline failure, but it makes a
layerwise probe unable to separate *"the model represents depth"* from *"the model represents the
object's vertical image position"*.

## Renamed taxonomy for SOLO (the old name was wrong)

`B0 selection` is a misnomer here — there is no multi-object selection in a solo set. It measures
projected-position / localization geometry. Solo reports:

| name | contents |
|---|---|
| **B0_position** | centroid (u, v), ground-contact point, bbox location, border distances |
| **B1_appearance** | retinal size, height/width, mask area |
| **B2_semantic** | category, physical size, size multiplier |

Keeping "selection" would permanently conflate two different problems: multi-object target
selection (a Pair concern) versus single-object position↔depth projection coupling (this one).

## TWO claims, reported separately — never merged into one verdict

**Claim A — is depth-related information linearly retained?** Does not require beating monocular
cues; the model may legitimately build depth *from* elevation and retinal size.
$$\Delta_{H\mid B0,B2} = S(B0 \cup B2 \cup H) - S(B0 \cup B2)\qquad\text{headroom } 1-0.896 = 0.104$$

**Claim B — does the representation exceed explicit monocular geometry?** Stronger.
$$\Delta_{H\mid B0,B1,B2}\qquad\text{headroom } 1-0.954 = 0.046$$

Always report **three** numbers: raw $H_l \to z$ · $\Delta_{H|B0,B2}$ · $\Delta_{H|B0,B1,B2}$.
Merging them into a single "depth representation succeeded/failed" is prohibited.

## PRE-COMMITTED acceptance targets (fixed BEFORE any candidate is rendered)

```
HARD      R²(B0_position)        ≤ 0.60
DESIRABLE R²(B0 ∪ B2)            ≤ 0.70     (leaves ≳0.30 raw headroom)
DESIRABLE R²(B0 ∪ B1 ∪ B2)       ≤ 0.90     (else Claim B is untestable)
```

B1 is *not* required to be low — it is real depth evidence. The goal is **no single cue nearly
solves depth**, not zero correlation.

## Calibration protocol — small, rendered, not analytic

The analytic proxy already proved unreliable (−0.575 → −0.705 rendered; −0.747 → −0.882), so every
candidate is judged on **rendered silhouette and ground-contact measurements**. 3–4 candidate camera
envelopes, 200–300 images each: current · wider pitch · wider height · wider pitch+height.

Per candidate measure: R²(B0_position) · R²(B1) · R²(B0∪B2) · R²(B0∪B1∪B2) · r(z, retinal) ·
r(z, image v) · placement failures · truncation · depth-range coverage · category-conditioned
balance.

⚠ **Widening range alone may not fix it.** The direct check is the overlap of
$p(v_{\text{image}} \mid z\text{ bin})$: if depth bins remain separable by image v, more jitter has
not solved the coupling and the fix is **stratified / rejection balancing over depth-bin × image-
position cells**. Calibrate first; do not build a complex sampler up front.

## Solo need NOT share the pair camera envelope

Solo is a localization diagnostic; Pair is binding/ratio/fusion. Two subsets:

- **Solo-Orthogonalized** — wider camera variation, the main layerwise depth-localization data.
- **Solo-Pair-Matched** — pair envelope, a SMALLER control subset checking whether the stage pattern
  transfers to a pair-like visual distribution.

Only the orthogonalized set needs the full n.

## What the smoke test does and does not establish

**Does:** solo pipeline works end-to-end · validator handles single-object sets · annotations match
metadata exactly · B2 does not leak (R² = −0.015) · physical size orthogonal to depth · retinal
coupling improved over v0.

**Does NOT:** that solo provides a clean depth-representation test · that position leakage is
removed · that the current design has enough headroom for a strong incremental claim.
