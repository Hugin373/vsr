# §5 revalidation — PRE-REGISTERED criteria block (RECONCILED)

**Canonical source:** `docs/M4A_S5_CRITERIA-reviewer.md`, ratified 2026-07-19. That file is the
**received artifact and is not edited** — it is the record of what was ratified. This file is the
operative reconciliation: canonical Check A–D content, carrying forward the C-1…C-5 numbering and
the pre-committed bound machinery.

**Reconciliation blocker: CLEARED** on this commit. The previous contents of this file were my own
draft standing in for A–D text that had not arrived; they are superseded below.

**Status: bound cells still EMPTY.** Ratification remains blocked on the 8-seed sweep. No §5 render
may run until check A's bounds are filled mechanically from the pre-committed formula.

---

## Reconciliation record — what my draft got wrong

Kept honest rather than quietly overwritten, because two of these were load-bearing.

| | my draft | canonical | verdict |
|---|---|---|---|
| **A** | natural-congruent ratio validity | Sampling semantics | ~matches; canonical adds the unclamped-subset measures, per-pairing counts, and "instrument failure, not model result" framing |
| **B** | realized-set band separation | **Category and role independence** | **wrong subject.** Symmetry and P(near\|c) live in B, not in my "construction invariants" |
| **C** | category ↔ depth coupling | **Clamp burden and support overlap** | **partly wrong.** My band-separation content belongs here |
| **D** | construction invariants | **Pixel-level ratio identifiability** | **entirely wrong.** Canonical D is a check my draft did not contain at all |
| **C-5** | provenance/determinism | engineering gates **including** all construction invariants | my C-4 content belongs here |

🔴 **Consequence I must retract in place.** Last session I wrote that "realized = placed" means the
8-seed sweep "covers more of **check D** than the scoping implies". Under my draft's D (construction
invariants) that was true. Under **canonical D — pixel-level identifiability — it is false**, and the
advisor's boundary ruling corrects exactly this. The underlying observation survives; only its
destination was wrong. See the boundary section below.

Check **C** also carries **five** binding hard failures in the canonical text, not the three quoted
in the ruling summary. All five are transcribed.

---

## 🔒 Boundary: what the assignment-level sweep can and cannot establish (ruled 2026-07-19)

**"Realized" means PLACED, not RENDERED.** Placement lives in the sampler, so the 8-seed
assignment-level sweep — with no renderer — establishes every quantity in **Checks A, B and C**,
**including placed-level `P(near|c)`**, and the construction invariants that sit in **C-5**.

**The sweep contributes NOTHING to Check D.** Check D is **exclusively pixel-level**, evaluated on
the frozen rendered pilot. A sampling correlation such as `r(realized ratio, depth_gap_bin)`
validates generator semantics and **does not satisfy Check D** under any circumstances. Metadata-level
ratio variation is not evidence of visual recoverability.

This boundary is written here, in the criteria file, as ruled — so that no future session can
recover the conflation by re-deriving it.

---

## Gate-scale render N — derived, replacing the retired "~1k" constant

The historical "~1k gate-scale pilot" figure is **RETIRED**. It predates the three-regime matched
contrast and the eligibility manifest, and it is not derivable from the criteria block. N is now
derived from the per-cell requirement.

**Given:** pre-registered minimum **25 images per (near, far) pairing cell**
(`configs/m4a_eligibility_manifest.yaml` v2), 16 eligible pairings in the matched contrast.

| arm | generated pairings | eligible | eligible fraction | derivation | **minimum N** |
|---|---:|---:|---:|---|---:|
| natural-congruent | 16 | 16 | 1.000 | 16 × 25 ÷ 1.000 | **400** |
| counterbalanced | 36 | 16 | 0.444 | 16 × 25 ÷ 0.444 | **900** |
| conflict | 36 | 16 | 0.444 | 16 × 25 ÷ 0.444 | **900** |
| | | | | **total** | **≥ 2 200** |

These land exactly on 25 per cell for **both** tiers simultaneously: at N = 900 a six-category arm
gives 900 ÷ 36 = 25 per cell for the tier-3 full-arm analysis, and 900 × 0.444 ÷ 16 = 25 per cell for
the tier-2 restricted contrast. No arm is over- or under-provisioned relative to the other.

⚠ **2 200 is a FLOOR, not the final N.** Check D additionally requires reported sample counts for
every held-out stratum — depth-gap bins, categories, camera poses, **lighting families**, **background
/ texture families**, and nuisance combinations. The texture and lighting families **do not exist
yet**. Once they are defined, N must be re-derived against the weakest held-out stratum, and it will
only go up. Any margin above 2 200 is a separate decision to be taken then, not now.

---

## 🔒 Threshold-setting protocol (carried forward, unchanged)

> **Never derive a threshold from the same results it gates.**

Committed to git **before** the sweep runs; git history is the ordering proof.

```
SEEDS = [9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008]   # none reused elsewhere
k     = 2.0

lower-bounded quantity:   L_q = min_s(q_s) − k · SD_s(q),  rounded DOWN to 2 dp
upper-bounded quantity:   U_q = max_s(q_s) + k · SD_s(q),  rounded UP   to 2 dp
```

- The config's own seed (410) is reported as a ninth **reference** value and **excluded** from the
  bound, being the seed the design was developed against.
- **Bounds are computed only after all seeds complete** (canonical Check A requirement).
- **Weakest-stratum clause:** for per-pairing quantities the formula is applied to the weakest
  stratum in each seed, not to the pooled value.
- **Spread rule:** any quantity whose seed-to-seed SD exceeds 25% of its mean is **demoted to
  reported-only** and cannot serve as a binding gate until its instability is resolved. Demotions are
  recorded here before the render.

---

## Check A (C-1) — Sampling semantics

**Purpose:** verify the realized distance ratio remains governed by the intended depth-gap design,
rather than being replaced by floor clamping, floor-band jitter, or another sampling artifact.

**Measure, for every seed:**

1. Pearson (or pre-specified rank) correlation between realized ratio and `depth_gap_bin`.
2. Retained realized-ratio range, `max(r_realized) / min(r_realized)`.
3. The same correlation and range **on the unclamped subset**.
4. The weakest category-pairing stratum for each quantity.
5. Aggregate and per-pairing sample counts.

**Primary lower-bound quantities:** correlation with `depth_gap_bin`; retained realized-ratio range;
any separately pre-registered acceptance fraction.

| quantity | direction | single-seed REFERENCE (n = 1200, seed 410) | bound |
|---|---|---:|---|
| r(realized ratio, `depth_gap_bin`) | lower | +0.751 | *pending sweep* |
| retained realized-ratio range | lower | 1.25× | *pending sweep* |
| `clamped_fraction` (gated under C) | upper | 0.332 | *pending sweep* |
| weakest-stratum variants of the above | — | not yet measured per-cell | *pending sweep* |

⚠ The reference column is **not** a bound. Bounds proposed from a single seed were rejected under
AGENTS.md rule 7 clause 2, correctly.

**Failure interpretation:** the generator does not express the intended ratio variable reliably.
**This is an instrument failure, not a model result.**

## Check B (C-2) — Category and role independence

**Purpose:** ensure category identity, category pairing, or near/far role does not provide a lookup
table for realized ratio, depth, or clamp status.

**Structural requirements:**

- Retained support symmetric: (a, b) ∈ S ⟹ (b, a) ∈ S.
- For every retained category c, at **assignment level and after successful placement**:
  P(near | c) = 0.5 and P(far | c) = 0.5.

**Measure, for every seed:** η²(pairing → realized ratio) · η²(near category → realized ratio) ·
η²(far category → realized ratio) · η²(near category → realized far depth) · η²(far category →
realized far depth) · category and pairing effects on clamp status · category-conditioned near/far
balance **before and after placement** · the weakest pairing and weakest near-/far-role category for
every measure.

**Both roles are bounded.** The measured mechanism is near-role dominant — bottle-as-near forcing the
far object deeper — but *the criterion must not depend on that mechanism being remembered correctly.*

**Structural hard failures:** asymmetric retained support · assignment- or placed-level category-role
imbalance beyond tolerance · pairing deterministically or near-deterministically identifies realized
ratio · category or role deterministically identifies clamp status.

## Check C (C-3) — Clamp burden and support overlap

**Purpose:** quantify how often the floor changes a sampled ratio, and ensure clamping does not create
a separate, category-identifiable ratio regime.

```
clamped_fraction                 = #{ r_raw < r_floor } / N          ← PRIMARY intervention rate
accepted_in_floor_band_fraction  = #{ r_accepted ∈ floor band } / N   ← DESCRIPTIVE ONLY
```

`accepted_in_floor_band_fraction` **must never be interpreted as the fraction of samples changed by
the floor.** (Measured illustration of why: the conflict regime reads clamped 0.000 against
accepted-in-band 0.058.)

**Measure, for every seed:** aggregate `clamped_fraction` · per-pairing · per-near-category ·
per-far-category · maximum stratum-level `clamped_fraction` · raw, unclamped and realized ratio
ranges · overlap between clamped and unclamped realized-ratio distributions · whether pairing, near
category or far category predicts clamp status · `accepted_in_floor_band_fraction`, labelled
descriptive only.

**BINDING HARD FAILURES — all five:**

1. Any retained category pairing is **always clamped**.
2. The realized-ratio support of clamped and unclamped samples is **disjoint**.
3. Category identity or pairing **predicts clamp status** strongly enough to make clamping a semantic
   lookup.
4. Clamping causes realized ratio to **cease tracking the intended depth-gap design**.
5. A **weakest pre-specified stratum violates its bound even when the aggregate passes**.

**Failure cannot be repaired analytically after rendering.** It requires changing the generator or the
retained support.

## Check D (C-4) — Pixel-level ratio identifiability

**Purpose:** verify that the ratio variation established by Checks A–C is **recoverable from rendered
pixels** under held-out nuisance factors. Metadata-level variation alone is insufficient.

**Runs on the frozen rendered pilot, NOT on the assignment-level seed sweep.**

**Evaluate at least:** held-out depth-gap bins · held-out object categories within the pre-registered
eligible support · held-out camera poses · held-out lighting families · held-out background/texture
families · held-out nuisance combinations · the shared four-category **three-regime matched contrast**
(natural-congruent, counterbalanced, conflict) · the weakest pre-specified category-pairing and
nuisance stratum.

**Report separately:** ordinal identifiability · continuous ranking · calibrated ratio magnitude · an
interpretable pixel or geometric-image baseline · a stronger directly-supervised pixel model ·
confidence intervals or the pre-registered resampling summary · sample counts for every held-out
stratum.

> A sampling correlation such as `r(realized ratio, depth_gap_bin)` **does not satisfy Check D.** It
> validates generator semantics, not visual recoverability.

**Failure interpretation:** if ratio is present in metadata but not statistically recoverable from
pixels under the pre-registered held-out conditions, **the rendered instrument does not license a
downstream representation claim for ratio.**

## C-5 — Engineering gates

Separate from scientific Checks A–D.

**Reproducibility:** deterministic regeneration · byte-identical annotations and masks where required
· documented pixel tolerance for beauty renders.

**Provenance:** clean provenance · source/config/input manifest hashes · `derivation_source_sha`.

**Configuration coverage:** frozen-config manifest completeness (`discovered == expected`) · failure
when a required config is absent · **no glob or optional-field filter that can silently exclude
production configs**.

**Machine-checked invariants:** exact category-support symmetry · exact assignment-level balance ·
placed-level balance within tolerance · correct **target-only** near/far role assignment · per-object
physical-size reconstruction invariant · regime-aware floor validation · all freeze-critical fields
matching the canonical frozen block.

---

## Ratification checklist

- [x] Receive the reviewer's A–D spec text and reconcile — **done, blocker cleared**.
- [x] Write the assignment-sweep / pixel-level boundary into this file.
- [x] Derive gate-scale N from per-cell requirements; retire the "~1k" constant.
- [ ] Run the 8-seed assignment-level sweep under the protocol above.
- [ ] Fill Check A's bounds mechanically; record any quantity demoted by the spread rule.
- [ ] Re-derive N once lighting/texture families exist (Check D held-out strata).
- [ ] Advisor ratifies the block as written.
- [ ] Only then: render the frozen pilot.
