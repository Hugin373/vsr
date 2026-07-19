# §5 revalidation — PRE-REGISTERED criteria block

**Status: DRAFT. Not ratified. No §5 render may run against it yet.** §5 runs ONCE, against
criteria written in advance as one block. Nothing here may be adjusted after seeing §5 output.

Check labels follow the reviewer's canonical scheme (mapping ruled 2026-07-19):

| this doc | canonical | subject |
|---|---|---|
| C-1 | **A** | natural-congruent ratio validity |
| C-2 | **B** | realized-set band separation |
| C-3 | **C** | category ↔ depth / clamp coupling |
| C-4 | **D** | construction invariants |
| C-5 | *engineering gates* | provenance · determinism · invariant plumbing |

> ## ⚠ OPEN GAP — the A–D spec text has still not reached me
>
> The adopting message says the reviewer's A–D specs were "pasted with this message". **No spec
> text arrived** — not in that message and not in the previous one. What I hold is the *mapping*
> above and check **C**'s three binding hard-fails, both of which are stated in the ruling itself
> and are transcribed below verbatim in substance.
>
> So: the labels A–D here are correctly *mapped*, but their contents are **mine**, not the
> reviewer's. Where my content and the reviewer's spec differ, the reviewer's governs.
> **Reconciliation is a ratification blocker.** Paste the A–D text and this file gets checked
> against it line by line.

---

## Scope

The §5 revalidation render of natural-congruent (4-set), counterbalanced and conflict. Every bound
is checked by a script and every result reported, pass or fail.

## Pre-registered eligibility

`configs/m4a_eligibility_manifest.yaml` v2, ratified 2026-07-19, before any §5 render. Three
analysis tiers: control-specific (4) · matched three-regime contrast (shared 4) · full-arm (6,
counterbalanced + conflict only). Per-cell n ≥ 25 per pairing cell, implying n ≥ 400 for the
congruent arm and n ≥ 900 for each six-category arm.

---

## 🔒 Threshold-setting protocol (ruled 2026-07-19, binding)

> **Never derive a threshold from the same results it gates.** A bound fitted to the data it judges
> is not a gate; it is a description wearing a gate's clothes.

Consequently every numeric bound in check **A** is set by the procedure below, which **runs and is
committed before the §5 render**, on data that §5 does not reuse.

**Instrument.** An **assignment-level sweep** — `build_scene_specs` only, no rendering. Every
quantity A gates (`r(ratio, depth_gap_bin)`, `clamped_fraction`, retained dynamic range, per-pairing
clamp burden) is **pre-pixel**: it is fixed once placement has run, and placement lives in the
sampler. *Note this includes the **realized** level: "realized" means placed, not rendered, so
realized-level role balance is also measurable here. Only pixel-derived quantities need the
renderer, and none of A's do.*

**Pre-specified seeds** — fixed here so they cannot be chosen after seeing spread:

```
SEEDS = [9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008]     # 8 seeds, none reused elsewhere
```

The config's own seed (410) is reported alongside as a ninth reference value but is **excluded**
from the bound computation, since it is the seed the design was developed against.

**Margin formula — k stated before running, as required:**

```
k = 2.0

lower-bounded quantity:   bound = min(over SEEDS)  −  k · SD(over SEEDS),  rounded DOWN to 2 dp
upper-bounded quantity:   bound = max(over SEEDS)  +  k · SD(over SEEDS),  rounded UP   to 2 dp
```

Rationale for k = 2.0: the minimum over 8 seeds is already an extreme-order statistic, so k is
absorbing residual seed-to-seed variation beyond the observed extreme rather than standing in for a
confidence interval. Two SDs past the observed extreme is deliberately generous — a §5 failure
should mean the design changed, not that a seed was unlucky (AGENTS.md rule 7 clause 2: "one noisy
item must not define a gate").

**Weakest-stratum clause.** For per-pairing quantities the formula is applied to the **weakest
stratum** (the worst pairing) in each seed, not to the pooled value — so the bound is set on the
worst cell's seed-to-seed behaviour.

**Pre-committed spread rule.** If any quantity's seed-to-seed SD exceeds 25% of its mean, the
quantity is declared **too unstable to gate**, is demoted to *reported-only*, and that demotion is
recorded here before the render. This prevents the alternative failure mode — a noisy quantity
being given a tight bound and then failing for reasons unrelated to the design.

---

## Check A — natural-congruent ratio validity

The arm the 4-set fix exists to restore. Quantities gated:

| quantity | direction | single-seed reference (n = 1200, seed 410) | bound |
|---|---|---:|---|
| `r(ratio, depth_gap_bin)` | lower | +0.751 | *pending 8-seed sweep* |
| `clamped_fraction` | upper | 0.332 | *pending* |
| retained ratio dynamic range | lower | 1.25× | *pending* |
| per-pairing clamp burden, weakest stratum | upper | not yet measured per-cell | *pending* |

⚠ **The single-seed column is a REFERENCE, not a bound.** Bounds proposed from it were **rejected**
2026-07-19 under rule 7 clause 2, correctly: they are sampled quantities and a single draw cannot
set a gate. The cells above stay empty until the sweep runs under the protocol.

## Check B — realized-set band separation

For every regime, over the realized set:

| quantity | bound |
|---|---|
| overlap between any two pairings' ratio distributions | ≥ 0.05 (no disjoint bands) |
| η²(pairing → realized ratio) | ≤ 0.10 |

Reference contrast: the rejected six-category congruent arm measures overlap **0.000**, η² **0.865**
(`docs/REJECTED_DESIGNS.md` R2). The adopted design has η² = 0 by construction, so B should be
slack — which is exactly why it is worth checking.

## Check C — category ↔ depth and clamp coupling

**Three HARD-FAILS, binding (ruled 2026-07-19). Any one of them fails §5 outright:**

1. **Any always-clamped pairing.** A pairing whose floor exceeds the available maximum, so every one
   of its images is moved by the floor.
2. **Disjoint clamped/unclamped support.** The clamped and unclamped image populations must not
   occupy separable ratio bands.
3. **Category predicts clamp.** Category (either role) must not be predictive of whether an image
   was clamped.

Continuous bounds alongside the hard-fails:

| quantity | bound |
|---|---|
| η²(near category → realized far depth) | ≤ 0.05 |
| η²(far category → realized far depth) | ≤ 0.05 |
| P(near \| category), realized | 0.500 ± 0.02, every category |

⚠ **Both roles are bounded, deliberately.** The earlier ruling said *far*-role coupling; measurement
showed the mechanism is **near**-role dominant (η² 0.330 vs 0.051, driven by bottle-as-near's area
constant). The advisor has accepted that correction as their own error. Bounding only the named role
would have left the actual mechanism ungated.

## Check D — construction invariants

Machine-checked, hard-fail:

- **Symmetry** — every generated pairing set satisfies (a, b) legal ⟺ (b, a) legal.
- **Role balance, assignment level** — P(near | category) = 0.5 exactly at n ≥ 2000.
- **Role balance, realized level** — P(near | category) = 0.5 ± 0.02 over placed images.
  Placement is a selection operator; assignment-level balance does not imply it.
- **Eligibility manifest precedes the render** — `ratified_utc` earlier than the render stamp.
- **Frozen generator block** — manifest-based config guard passes.

## C-5 — Engineering gates

Provenance (`provenance_claim`, `derivation_source_sha`, `render_git_patch_sha`) · determinism
byte-compare · validation suite green with margins reported not pass/fail · cue constants derived
per regime over the correct envelope (natural-congruent over the **4-set at 1.1707**;
counterbalanced/conflict over the full six) · rejection bias re-audited at gate scale (band ~0.09) ·
B2→z re-confirmed on the rendered set.

---

## Ratification checklist

- [ ] **Receive the reviewer's A–D spec text** and reconcile this file against it (blocker).
- [ ] Run the 8-seed assignment-level sweep under the protocol above.
- [ ] Fill check A's bounds from the formula; record any quantity demoted by the spread rule.
- [ ] Confirm per-cell n at the chosen gate scale.
- [ ] Advisor ratifies the block as written.
- [ ] Only then: render the frozen pilot.
