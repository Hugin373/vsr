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
longer category-matched to the arm it anchors. Two ways out, and this is a real choice, not a
detail:

1. **Subset the ANALYSIS, not the stimuli** — keep 6 categories in conflict/counterbalanced and
   restrict the *fusion comparison* to the 4 shared ones. Costs nothing in stimuli, keeps bottle and
   chair available for every analysis that does not need the congruent reference.
2. **Restrict all regimes to the 4 categories** — perfectly matched, but drops bottle and chair from
   the whole battery, reducing the category diversity that B2 (semantic priors) is measured over.

Recommendation: **(1)**. The category set is a property of the analysis contrast, not of the
generator, and B2 coverage is worth keeping.

## What is NOT decided here

The choice itself. This table is the numbers the ruling asked to be confirmed against; per the
sequence, implementing the chosen fix is freeze work that comes next, and the constants must be
re-derived over whichever envelope is chosen before anything is rendered at scale.
