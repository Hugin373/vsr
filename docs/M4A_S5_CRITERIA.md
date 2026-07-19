# §5 revalidation — PRE-REGISTERED criteria block

**Status: DRAFT, not yet ratified.** §5 runs ONCE, against criteria written in advance as one
block. Nothing here may be adjusted after seeing §5 output; adjusting a bound post-hoc converts the
one-shot design into a forking path and forfeits its value.

> ## ⚠ COVERAGE GAP — must be closed before ratification
>
> The 2026-07-19 advisor message adopts **"items 1–8 + acceptance checks A–D"**. That review is not
> in my working context, so **I cannot reproduce checks A–D by number**, and this file does not
> claim to. What follows is (a) the checks the adopting message names explicitly, and (b) bounds
> proposed from measurement, as instructed. **Paste the review's items 1–8 and checks A–D and this
> block gets reconciled against them before ratification.** Until then, treat any A/B/C/D labels
> below as my placeholders, not as the review's.
>
> One check *is* pinned by the adopting message: it states the six-category natural-congruent arm
> **"fail[s] check B on the full arm"**, so check B concerns realized-set confounding
> (band separation / category→depth coupling). That is reflected in C-2 and C-3 below.

---

## Scope

Applies to the §5 revalidation render of the three frozen regimes plus the natural-congruent 4-set
fix. Every bound is checked by a script, not by eye, and every result is reported whether it passes
or fails.

## Pre-registered eligibility

Fixed in `configs/m4a_eligibility_manifest.yaml` (ratified 2026-07-19, before any §5 render):

- **Generated sets** — natural-congruent {cube, cylinder, mug, sphere}; counterbalanced and
  conflict all six.
- **Matched-arm fusion contrast** — read over the shared four, both arms.
- **Per-cell n** — ≥ 25 images per (near, far) pairing cell in the restricted contrast, implying
  n ≥ 900 for the conflict arm (it loses 55.6% of images to eligibility). Failing this is reported
  as underpowered, never quietly read anyway.

---

## C-1 — Natural-congruent ratio validity

The arm this whole fix exists to restore. Bounds proposed from the 4-set candidate measured at
n = 1200 (`r = +0.751`, `clamped_fraction = 0.332`, retained dynamic range 1.25×), with margin.

| quantity | measured (candidate) | proposed bound | margin |
|---|---:|---|---|
| `r(ratio, depth_gap_bin)` | +0.751 | **≥ +0.60** | −0.15 absolute |
| `clamped_fraction` | 0.332 | **≤ 0.45** | +0.12 absolute |
| retained ratio dynamic range | 1.25× | **≥ 1.18×** | −0.07× |

⚠ **These are single-seed measurements.** Per AGENTS.md rule 7 clause 2 they are sampled
quantities, so the margins above are provisional until the seed-to-seed spread is measured; the
bound should sit below the weakest of several seeds, not below one. **Owed before ratification:**
run the candidate at ≥ 8 seeds and set each bound below the observed minimum. If the spread proves
wide, the bounds loosen — that is a pre-registration decision, not a post-hoc one, and it must
happen before the render.

**Weakest-stratum clause.** The bounds above are on the pooled arm. Additionally, per-pairing
**clamp burden** is reported for all 16 cells, and the **weakest stratum** (highest
`clamped_fraction`) must satisfy `clamped_fraction ≤ 0.60`. A pooled number can look healthy while
one pairing is fully clamped.

## C-2 — Realized-set band separation (the check the six-category arm fails)

For every regime, over the **realized** set:

| quantity | bound |
|---|---|
| overlap between any two pairings' ratio distributions | **≥ 0.05** (no disjoint bands) |
| η²(pairing → realized ratio) | **≤ 0.10** |

The rejected six-category natural-congruent arm measures overlap **0.000** and η² **0.865**
(`docs/REJECTED_DESIGNS.md` R2). The adopted 4-set with a uniform floor has η² = 0 by construction,
so this check should be slack — which is the point of checking it.

## C-3 — Category ↔ depth coupling in the realized set

| quantity | bound |
|---|---|
| η²(near category → realized far depth) | **≤ 0.05** |
| η²(far category → realized far depth) | **≤ 0.05** |
| P(near \| category), realized | **0.500 ± 0.02**, every category |

Measured on the rejected arm for contrast: η²(near → far depth) = 0.330. ⚠ Note the ruling's
wording said *far*-role coupling; measurement shows the mechanism is **near**-role dominant
(0.330 vs 0.051), so both roles are bounded here rather than only the one named.

## C-4 — Invariants that must hold by construction

Machine-checked, hard-fail:

- **Symmetry** — every generated pairing set satisfies (a, b) legal ⟺ (b, a) legal.
- **Role balance, assignment level** — P(near | category) = 0.5 exactly at n ≥ 2000.
- **Role balance, realized level** — P(near | category) = 0.5 ± 0.02 over placed-and-rendered
  images. Placement is a selection operator; assignment-level balance does not imply it.
- **Eligibility manifest precedes the render** — `ratified_utc` earlier than the render stamp.
- **Frozen generator block** — manifest-based config guard passes.

## C-5 — Carried over from the existing gate

Unchanged, restated so the block is self-contained: determinism byte-compare; validation suite green
with margins reported not pass/fail; cue constants derived per regime over the correct envelope
(natural-congruent over the 4-set at 1.1707; counterbalanced/conflict over the full six); rejection
bias re-audited at gate scale (band ~0.09); B2→z re-confirmed on the *rendered* set.

---

## Ratification checklist

- [ ] Reconcile against the review's items 1–8 and checks A–D (blocked on those being supplied).
- [ ] Replace C-1's single-seed margins with ≥ 8-seed weakest-observation bounds.
- [ ] Confirm per-cell n at the chosen gate scale.
- [ ] Advisor ratifies the block as written.
- [ ] Only then: render.
