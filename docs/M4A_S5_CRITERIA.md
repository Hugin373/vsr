# §5 revalidation — PRE-REGISTERED criteria block (RECONCILED)

**This is the single canonical §5 criteria file.** It carries the ratified Check A–D text
(reviewer-authored, 2026-07-19) reconciled with the C-1…C-5 numbering and the pre-committed bound
machinery. Where this file and any earlier draft differ, this file governs.

**Verbatim source of the ratified A–D text:** `docs/M4A_S5_CRITERIA-reviewer.md` as committed in
**`7a25800`**, since removed so that only one criteria file exists. Recover it with
`git show 7a25800:docs/M4A_S5_CRITERIA-reviewer.md`. Before removal, all 46 substantive items of
that text were mechanically checked as present here.

**Reconciliation blocker: CLEARED** on this commit. The previous contents of this file were my own
draft standing in for A–D text that had not arrived; they are superseded below.

**Status: bounds FILLED (2026-07-20, 8-seed sweep). Ratification BLOCKED on a new finding —
see below.** No §5 render may run.

> ## 🔴 BLOCKER — floor under root search (ruled 2026-07-20)
>
> Re-deriving the cue constants over natural-congruent's **own 4-set envelope** gives a worst-case
> area-congruence requirement of **1.1761**, while the pre-registered floor is **1.1707** — short by
> **0.46%**. Area congruence is a HARD validator check here.
>
> **Cause:** 1.1707 came from constants measured on the **six-category** envelope. The requirement is
> a *function of the floor* — R = R(F), falling as F rises, because a higher floor puts far objects
> deeper where perspective is less extreme. So a valid floor must satisfy **F ≥ R(F)**: a fixed-point
> condition, not a one-shot derivation.
>
> **1.2320 REJECTED.** It is the fixed point plus a margin policy inherited from the dead
> six-category envelope, and it destroys sampling semantics: r(ratio, gap) 0.73 → **0.50**,
> weakest stratum 0.64 → **0.18**, clamp 0.48 → **0.72**.
>
> **Resolution: minimal self-consistent floor via a pre-committed root search**
> (`scripts/floor_root_search.py`, committed before it ran). Grid 1.165–1.200 step 0.005,
> calibration seeds 8001–8002, r* = smallest grid point with F ≥ R(F) (tolerance one step),
> **r_op = r\* + 0.005 rounded up to 3 dp**. Interpolation predicts r* ≈ 1.175, candidate ≈ 1.181.
>
> ### Acceptance is JOINT — both, or the candidate fails
> **(a) Area validity** — r_op ≥ R(r_op), re-derived at r_op itself.
> **(b) Sampling validity** — the check A–C design-selection bounds below.
>
> Expect a genuine test: interpolation puts weakest-stratum r and the clamp rate both near their
> bounds.
>
> ### Pre-registered escape hatch — usable ONLY if the joint test fails
> Before declaring the 4-set infeasible, evaluate **extending the FAR depth-bin envelope**. Deeper
> bins place easily and raise the ratio ceiling, relaxing the squeeze *from above* rather than
> pushing the floor up into the distribution. ⚠ This is **battery-wide** (it changes the depth
> envelope for every regime) and **re-opens the z-identifiability checks**. Only if that also fails
> is the 4-set dead.

---

## 🔒 Formal seed roles (ruled 2026-07-20)

Disjoint splits, the same discipline as M5's direction protocol. **A seed used for one role may
never be reused for another** — reusing a calibration seed to set bounds would let the design be
selected and judged on the same draw.

| role | seeds | answers | may it move a threshold? |
|---|---|---|---|
| **calibration** | 8001–8008 | "which floor?" — root search and design selection | yes, that is its job |
| **bound-setting** | 9009–9016 | "how far may it drift?" — operative bounds at the ratified floor | yes |
| **frozen pilot** | config seed | accept/reject only | **never** |
| ~~development~~ | ~~9001–9008~~ | superseded; v1 evidence at floor 1.1707 | **no longer** |

⚠ **The bounds tabulated below were computed on 9001–9008 at floor 1.1707. They are
DESIGN-SELECTION EVIDENCE ONLY.** Operative bounds recompute on the fresh bound-setting seeds at
the ratified floor, from the same committed formula.

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

**BOUNDS — filled mechanically 2026-07-20** from `reports/m4a_s5_sweep_natural_congruent.json`
(8 seeds × n = 1200, sampler only). No judgement was applied after seeing the values.

| quantity | direction | 8-seed min … max | SD | CV | **BOUND** |
|---|---|---|---:|---:|---:|
| r(realized ratio, `depth_gap_bin`) | lower | 0.7282 … 0.7533 | 0.0097 | 0.013 | **≥ 0.70** |
| retained realized-ratio range | lower | 1.2524 … 1.2698 | 0.0063 | 0.005 | **≥ 1.23** |
| weakest-stratum r(ratio, gap) | lower | 0.6375 … 0.7094 | 0.0247 | 0.037 | **≥ 0.58** |
| weakest-stratum retained range | lower | 1.1660 … 1.1972 | 0.0111 | 0.009 | **≥ 1.14** |

Reference seed 410 (excluded from the bounds): r = 0.7515, range = 1.246 — inside the 8-seed
envelope, so the design seed was not anomalous.

🔴 **CORRECTION to a number previously recorded here.** This table used to carry
`clamped_fraction = 0.332` as its single-seed reference. **That was the wrong estimand.** Canonical
Check C defines `clamped_fraction = #{r_raw < r_floor} / N`, where `r_floor` is the **per-image
drawn floor**, which is jittered over [1.1707, 1.2642] (mean 1.2181). The 0.332 came from
`floor_squeeze.py`, which compared the **base** floor 1.1707 against a ratio distribution taken from
a **separate** non-binding-floor run — a different denominator and an unpaired comparison. Measured
both ways on the same data: canonical **0.4842** vs base-floor proxy **0.3283**, a gap of 0.156
fully accounted for by the jitter. The canonical value is ~**0.50**, not 0.33.

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

### 8-seed result — every Check B quantity was DEMOTED by the pre-committed spread rule

| quantity | 8-seed min … max | SD | CV | status |
|---|---|---:|---:|---|
| η²(pairing → ratio) | 0.0112 … 0.0255 | 0.0050 | 0.255 | demoted |
| η²(near cat → ratio) | 0.0005 … 0.0122 | 0.0045 | 0.649 | demoted |
| η²(far cat → ratio) | 0.0014 … 0.0122 | 0.0035 | 0.506 | demoted |
| η²(near cat → far depth) | 0.0004 … 0.0062 | 0.0020 | 0.606 | demoted |
| η²(far cat → far depth) | 0.0008 … 0.0030 | 0.0008 | 0.448 | demoted |
| η²(pairing → clamp) | 0.0082 … 0.0211 | 0.0046 | 0.294 | demoted |
| max abs role imbalance | 0.0000 … 0.0000 | 0.0000 | **inf** | demoted |

Applied mechanically, as the protocol requires. **Reported honestly: this leaves Check B with no
gated quantity at all, which is a defect in the pre-committed rule, not a property of the design.**

The rule tests *relative* spread (CV = SD / mean). Every Check B quantity is bounded **near zero by
intent** — η² ≈ 0.01–0.02 against a bound of 0.10 — so a trivial absolute spread of 0.005 produces a
large CV. The reductio is the last row: placed-level role imbalance is **exactly 0.0000 on all eight
seeds**, the best result the quantity can have, and CV = ∞ demotes it.

### ✅ AMENDMENT RATIFIED 2026-07-20 — near-zero exemption (protocol v2.0)

> The spread rule **does not apply** when `max_s q_s ≤ 0.25 × criterion bound`.
>
> **Scope, deliberately narrow:** natural-zero, *lower-is-better* quantities only — η², imbalances,
> clamp-predictability. It **never** applies to correlations or retained range, which are
> lower-bounded and far from zero, so relative spread is meaningful there and instability is real.

Implemented in `scripts/s5_assignment_sweep.py` (`NEAR_ZERO_EXEMPTION`), with each quantity
carrying an explicit `natural_zero` flag and its criterion bound, so the exemption cannot silently
widen to a quantity it was not ratified for.

⚠ **Ratified on FRESH seeds 9009–9016.** The v1 results tabulated above (9001–9008) are development
evidence and do not carry over: a rule amended in response to a result may not then be validated on
that same result.

**Structural results, 8 seeds:** support symmetric ✓ · placed-level P(near|c) = 0.5000 exactly for
all four categories on every seed ✓ · no pairing near-deterministically identifies ratio
(max η² = 0.0255) ✓ · no category or role identifies clamp status (max η² = 0.0211) ✓.

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

### 8-seed result

| quantity | 8-seed min … max | SD | CV | **BOUND** |
|---|---|---:|---:|---:|
| `clamped_fraction` | 0.4842 … 0.5242 | 0.0114 | 0.023 | **≤ 0.55** |
| max stratum `clamped_fraction` | 0.5867 … 0.6400 | 0.0213 | 0.034 | **≤ 0.69** |

**All five binding hard failures: PASS on every seed.** No always-clamped pairing (0/16) ·
clamped/unclamped realized-ratio support overlaps at 0.338, far above the 0.05 separation threshold ·
category does not predict clamp (η² ≤ 0.0211) · realized ratio still tracks the depth-gap design
(r = 0.73–0.75) · no weakest stratum violates its bound while the aggregate passes.

⚠ **Clamp burden is ~0.50, higher than the 0.33 previously recorded** — see the correction under
Check A. Half of all images have their far object moved by the floor. The arm still works
(r = 0.73–0.75, retained range 1.25×), but this is the honest figure and it is the one the bound is
set on.

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
