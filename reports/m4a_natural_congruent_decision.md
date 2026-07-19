# Natural-congruent: congruence vs. an informative ratio target — decision table

Date: 2026-07-19 · advisor arbitration item 1 · **built before textures, per the ruled sequence**

Numbers: `reports/m4a_natural_congruent_options.json`, reproduced by
`scripts/natural_congruent_options.py` and `scripts/floor_squeeze.py`. Every row below is measured
at n = 1200, not estimated.

## The problem in one line

Area congruence over the six-category set needs a far/near depth ratio of **1.7661** worst case;
the design produces at most **1.4737**. So every image is clamped to the floor, the ratio target
becomes an independent uniform draw, and oracle R² = −0.252 follows by construction.

## Why this must be fixed rather than descoped

The control regime's ratio arm is the **all-cues-agree reference** against which the conflict
regime's fusion analysis is read. A reference arm whose target is noise cannot anchor a fusion
claim. Descoping the ratio target is therefore last-resort, not first-choice.

## Decision table

| | **A1-4cat** (default) | **A1-primitives** (fallback) | **A2** all six, per-pair floors | **B** area recalibration | **C** widen depth range | **D** descope ratio |
|---|---|---|---|---|---|---|
| **Categories / pairings** | cube, cylinder, mug, sphere — 16 | cube, cylinder, sphere — 9 | all six — 36 | all six — 36 | all six — 36 | all six — 36 |
| **Uniform floor** | 1.1707 | 1.1512 | per-pair, 1.08–1.85 | unknown until recalibrated | 1.7661 unchanged | n/a |
| **Feasible range** (accepted) | 1.171–1.458, **dyn 1.25×**, sd 0.059 | 1.151–1.475, **dyn 1.28×**, sd 0.064 | **4/36 pairings still infeasible** | not measured | needs available max ≥ ~1.85 | n/a |
| **Clamped fraction** | 0.332 | 0.261 | — | — | — | n/a |
| **r(ratio, depth_gap_bin)** | **+0.751** | **+0.786** | — | — | — | n/a |
| **Coverage** (images retained at fixed n) | 0.44 → restrict `categories`, then 1.00 | 0.25 → restrict, then 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **Category/role balance** | exact 1.000 (symmetric set) | exact 1.000 | exact | exact | exact | exact |
| **Coupling** (does pairing predict ratio) | **η² = 0 by construction** | **η² = 0 by construction** | **η² = 0.823, worst overlap 0.000** | unknown | η² = 0 | n/a |
| **Validator meaning** | area congruence stays a HARD check, and now binds on pairings that can satisfy it | same | hard check, but floor varies by shape | hard check on area; height congruence becomes the loose one | hard check, unchanged | congruence kept, ratio target withdrawn |
| **Ordinal margin (min)** | 0.534 m | 0.490 m | — | — | — | 2.630 m |
| **Depth span** | 2.09× | 2.09× | — | — | — | 3.22× |
| **Cost** | config change (category list + floor); re-derive constants over the retained envelope; re-render | same | config change only | **full recalibration** + all constants re-derived + re-render; breaks the 90 px height equalisation | camera/depth redesign + re-validate placement at scale (the bin drop was forced by placement) | none |
| **Primary-regime impact** | see below — control/conflict category-set mismatch | larger mismatch | none | changes `size_m` per category, i.e. the B2 semantic prior, in **all** regimes | none | fusion reference arm becomes invalid |

## Reading

**A2 is disqualified by the safeguard the ruling specified.** Per-pair floors across all six
categories give **η² = 0.823** — the pairing explains 82% of ratio variance — with a worst pairwise
distribution overlap of **0.000**, i.e. some pairings' ratio distributions are entirely disjoint.
That is v0's shape-predicts-ratio confound in its most severe form. It also does not even solve the
problem: 4 pairings (bottle-as-near against cube, sphere, cylinder, mug) remain infeasible because
their per-pair floor still exceeds the available maximum.

**The ruled default is confirmed, with one refinement: uniform floor, not per-pair.** Restricting to
a symmetric category subset and then applying a *single* floor over it gives η² = 0 by
construction — the floor no longer depends on the pairing, so there is nothing for a probe to
exploit. Per-pair floors over the same 4-category subset still leave η² = 0.042 and a worst overlap
of 0.147; there is no reason to pay that when the uniform floor costs only ~0.03× of dynamic range.

**The safeguard's fallback trigger is not met.** The ruling said: if category predicts ratio, fall
back to primitives-only. Under A1-4cat with a uniform floor, category does not predict ratio at all
(η² = 0). Primitives-only remains available and is marginally *better* on range (1.28× vs 1.25×,
clamped 0.261 vs 0.332) but costs a category — worth taking only if 4-category coverage turns out
to matter less than the extra headroom.

**Does A1-4cat actually restore the arm?** `r(ratio, depth_gap_bin)` goes from **−0.017** (current)
to **+0.751**, and retained dynamic range from 1.08× to 1.25×. For calibration, the two regimes that
*pass* the ratio gate sit at r = +0.905 and 1.38×, with R² = +0.803 (counterbalanced) and +0.420
(conflict). So A1-4cat lands between the current failure and the passing regimes. **Predicted to
pass, not proven to** — that is a §5 measurement, and it must be reported as a result, not assumed
here.

## The cross-regime consideration the table surfaces

If natural-congruent runs 4 categories while counterbalanced and conflict run 6, the control is no
longer category-matched to the arm it anchors.

> ### 🔴 RETRACTED 2026-07-19 — my recommendation here was wrong
>
> This section originally recommended **"subset the ANALYSIS, not the stimuli — keep 6 categories
> everywhere and restrict the fusion comparison to the 4 shared ones"**, on the reasoning that the
> category set is a property of the analysis contrast rather than of the generator.
>
> That reasoning holds for **counterbalanced and conflict**, which do not clamp (measured
> `clamped_fraction` 0.001 and 0.000). It **fails for natural-congruent**, which does clamp,
> because area congruence is a hard validator check there. A six-category congruent set is only
> realizable by giving each pairing its own floor, and four pairings then clamp on every image:
>
> | quantity | value |
> |---|---:|
> | always-clamped ratio band | 1.665 – 1.850 |
> | all other pairings | 1.171 – 1.474 |
> | **overlap** | **0.000** |
> | η²(pairing → realized ratio) | **0.865** |
> | η²(near category → realized far depth) | 0.330 |
>
> That is the B15 confound rebuilt inside the reference arm, by the exact mechanism just diagnosed
> as the reason the ratio target was invalid. **Restricting the analysis does not undo it** — the
> confound is in the realized stimuli, and ordinal / absolute-depth / lateral targets are still
> read over all six generated categories.
>
> Filed with full evidence in `docs/REJECTED_DESIGNS.md` → **R2**.

**Binding resolution (advisor, 2026-07-19).** Natural-congruent's **generator** is the symmetric
4-set {cube, cylinder, mug, sphere} at uniform floor 1.1707 — it does not generate six categories.
"Six categories everywhere" applies to counterbalanced and conflict. The matched-arm fusion
contrast runs on the shared four via the pre-registered eligibility manifest
(`configs/m4a_eligibility_manifest.yaml`), which also carries the per-cell n check for the
restricted contrast at gate scale.

## The symmetry principle (recorded explicitly, as ruled)

> **A pairing restriction must preserve exact per-category role balance.** Legal pairings must form
> a symmetric set: if (a, b) is generated then (b, a) must be too. This is not an aesthetic
> preference — `cat_pair` balancing is what gives each category an exact P(near | category) = 0.500
> split, and that split is what closes B2→z (identity priors predicting depth). Retaining
> (bottle, cube) without (cube, bottle) would make bottle preferentially NEAR and rebuild the
> confound the balancing exists to kill.

Enforced as machine-checked invariants rather than prose: symmetry hard-fail, and
P(near | category) = 0.5 at **both** the assignment level and the **realized** level — placement is
a selection operator, so assignment-level balance does not imply realized balance.

## What is NOT decided here

The choice itself. This table is the numbers the ruling asked to be confirmed against; per the
sequence, implementing the chosen fix is freeze work that comes next, and the constants must be
re-derived over whichever envelope is chosen before anything is rendered at scale.
## Appendix A — the exclusion table

### A.1 Why each category is or is not retained

`C_a` = area constant (`mask_area_px × depth²`, size normalised out), from the natural-congruent dense sweep (n ≈ 200 per cell).

| category | C_a as near (min) | C_a as far (max) | worst req **as near** | worst req **as far** | retained |
|---|---:|---:|---:|---:|:--:|
| bottle | 48,653 | 50,866 | 1.7661 | 1.0579 | ❌ |
| chair | 80,047 | 85,805 | 1.3769 | 1.3280 | ❌ |
| cube | 140,690 | 151,754 | 1.0659 | 1.7661 | ✅ |
| cylinder | 125,638 | 126,849 | 1.0990 | 1.6147 | ✅ |
| mug | 121,496 | 122,923 | 1.1176 | 1.5895 | ✅ |
| sphere | 127,792 | 131,469 | 1.0897 | 1.6438 | ✅ |

The asymmetry is the whole story: **a category is excluded for what it forces when it is NEAR**, not when it is far. A bottle's silhouette area is ~3× smaller than a cube's at the height-calibrated size, so a near bottle against a far cube needs a depth ratio of 1.7661 — above the design's maximum of 1.4737. As the FAR object a bottle needs only 1.0579 and is entirely unproblematic.

### A.2 What each successive exclusion buys

Greedy removal, always dropping the category whose removal most reduces the worst-case requirement. Floor = worst requirement × 1.0475 (the +4.75% margin the 1.85 floor carries). Feasible means floor < available max 1.4737.

| categories retained | worst req | uniform floor | feasible | retained ratio range |
|---|---:|---:|:--:|---:|
| 6: bottle, chair, cube, cylinder, mug, sphere | 1.7661 | 1.8500 | ❌ | 1.000× |
| 5: chair, cube, cylinder, mug, sphere | 1.3769 | 1.4423 | ✅ | 1.022× |
| 4: cube, cylinder, mug, sphere ← **adopted** | 1.1176 | 1.1707 | ✅ | 1.259× |
| 3: cylinder, mug, sphere | 1.0700 | 1.1208 | ✅ | 1.315× |

Five categories is technically feasible but useless: a floor of 1.4423 against an available maximum of 1.4737 leaves a **1.022× retained range** — a target with essentially no spread, i.e. the same failure as today in milder form. Four categories is the first genuinely usable point, and three buys only a further 0.056× at the cost of another category.

### A.3 Excluded pairings

All 20 pairings involving bottle or chair are excluded from the natural-congruent **generator**. Note that most of them are individually harmless — e.g. `near_cube_far_bottle` requires only 1.0538. They are excluded because the retained set must be **symmetric** (§ symmetry principle): admitting `near_cube_far_bottle` without `near_bottle_far_cube` would make bottle preferentially FAR and break the exact 0.500 role balance that closes B2→z.

| excluded pairing | required ratio | individually feasible? |
|---|---:|:--:|
| bottle → cube | 1.7661 | **no** |
| bottle → sphere | 1.6438 | **no** |
| bottle → cylinder | 1.6147 | **no** |
| bottle → mug | 1.5895 | **no** |
| chair → cube | 1.3769 | yes |
| bottle → chair | 1.3280 | yes |
| chair → sphere | 1.2816 | yes |
| chair → cylinder | 1.2588 | yes |
| chair → mug | 1.2392 | yes |
| cylinder → bottle | 1.0579 | yes |
| cube → bottle | 1.0538 | yes |
| cylinder → chair | 1.0401 | yes |
| mug → bottle | 1.0394 | yes |
| chair → bottle | 1.0386 | yes |
| cube → chair | 1.0361 | yes |
| chair → chair | 1.0353 | yes |
| bottle → bottle | 1.0344 | yes |
| sphere → bottle | 1.0309 | yes |
| mug → chair | 1.0219 | yes |
| sphere → chair | 1.0136 | yes |
