# Rejected designs — kept with their evidence

A design rejected on measured evidence is worth more written down than deleted. Without the
record, the same reasonable-sounding option gets re-proposed every few sessions and re-tested from
scratch; worse, it can get adopted by someone who only sees that it is not currently in use.

Each entry states: what was proposed, why it was appealing, what killed it, and what would have to
change for it to be reconsidered.

---

## R1 — Per-pair `min_depth_ratio` floors (natural-congruent)

**Rejected 2026-07-19.** Evidence: `reports/m4a_natural_congruent_options.json`,
`reports/m4a_natural_congruent_decision.md`.

**Proposed.** Keep all six categories in the natural-congruent regime and give each (near, far)
category pairing its own `min_depth_ratio`, derived from that pairing's own worst-case area
requirement, instead of one uniform floor over a restricted category set.

**Why it was appealing.** It is the least destructive-looking option: no category is dropped, every
pairing gets exactly the floor its geometry requires and no more, and it uses the per-pair
requirements the derivation already produces. It also maximises the retained ratio range on paper,
because most pairings need far less than the worst one.

**What killed it — measured, not argued.**

| quantity | all six categories, per-pair floors | the 4-set with a uniform floor |
|---|---:|---:|
| η²(pairing → ratio) | **0.823** | **0** (by construction) |
| worst pairwise distribution overlap | **0.000** | n/a |
| median pairwise overlap | 0.455 | n/a |
| pairings still infeasible | **4 / 36** | 0 |

η² = 0.823 means the category pairing explains 82% of the variance in the depth ratio, and a worst
pairwise overlap of 0.000 means some pairings' ratio distributions are **entirely disjoint** — the
ratio identifies the pairing outright. This is precisely the confound v0 rejected per-pairing
thresholds for, in its most severe form: *"per-pairing limits would make shape predict the
depth-ratio distribution — a confound a probe could exploit"* (`docs/PROJECT_MEMORY.md`, 2026-07-10).

It also fails on its own terms: 4 pairings (bottle-as-near against cube, sphere, cylinder, mug)
have per-pair floors above the maximum ratio the design produces, so they clamp on every image
regardless.

Applying per-pair floors to the *restricted* 4-set is milder but still not free — η² = 0.042,
worst overlap 0.147 — and buys only ~0.03× of dynamic range over the uniform floor. Not worth any
coupling at all.

**What would have to change to reconsider.** A camera/depth design whose available ratio range
comfortably exceeds every pairing's requirement, so that no pairing's floor binds and the per-pair
floors are all slack. At that point they would be equivalent to a uniform floor anyway.

---

## R2 — Six-category natural-congruent with analysis-only restriction

**Rejected 2026-07-19** (binding advisor disambiguation, confirmed with numbers). Evidence:
`reports/m4a_natural_congruent_options.json` → `six_category_control`.

**Proposed.** Have natural-congruent *generate* all six categories, and restrict only the fusion
*analysis* to the four eligible ones — "subset the analysis, not the stimuli". **This was my own
recommendation on 2026-07-19 and it was wrong.** Retained visibly per AGENTS.md rule 13.

**Why it was appealing.** It keeps the control category-matched to the six-category conflict arm
for every analysis that does not need the restricted contrast, preserves bottle and chair for B2
(semantic prior) coverage, and treats the category set as a property of the contrast rather than of
the generator. That reasoning is sound — for counterbalanced and conflict, which do not clamp
(measured `clamped_fraction` 0.001 and 0.000).

**What killed it.** Natural-congruent *does* clamp, because area congruence is a hard validator
check for it. A six-category congruent set is therefore only realizable by giving each pairing its
own floor, and then:

| quantity | value |
|---|---:|
| pairings clamped on **every** image | 4 / 36 |
| always-clamped ratio band | 1.665 – 1.850 |
| all other pairings' band | 1.171 – 1.474 |
| **overlap of the two bands** | **0.000** |
| η²(pairing → realized ratio) | **0.865** |
| η²(near category → realized ratio) | 0.578 |
| η²(near category → realized far depth) | 0.330 |
| η²(far category → realized far depth) | 0.051 |

The realized set contains two disjoint ratio populations keyed to the category pairing, and
category predicts depth. That is the B15 confound rebuilt inside the reference arm — by the exact
mechanism that had just been diagnosed as the reason natural-congruent's ratio target was invalid.

**Restricting the analysis does not undo it**, which is the load-bearing point: the confound lives
in the *realized stimuli*. Every other target read over that set — ordinal depth, absolute depth,
lateral position — is still read over all six generated categories, contaminated.

⚠ **One correction to the ruling's wording, on the evidence.** The ruling described "far-role
category ↔ depth coupling". The coupling is measurably **near-role dominant**: η²(near → far depth)
= 0.330 versus η²(far → far depth) = 0.051. The mechanism is that *bottle-as-near* has the smallest
area constant (48 653 vs a cube's 151 754 as far), which forces the far object deep. A far category
is diluted because e.g. cube-as-far appears in both clamped and unclamped pairings. The conclusion
is unaffected; the attribution is corrected so the mechanism is not misremembered.

**What would have to change to reconsider.** A congruent design in which no pairing clamps — i.e.
the same condition as R1. Until then, natural-congruent generates the symmetric 4-set.
