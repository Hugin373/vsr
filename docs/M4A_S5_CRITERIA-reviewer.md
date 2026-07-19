## Canonical §5 Acceptance Checks A–D

These checks are the ratified scientific acceptance criteria for the frozen M4a natural-congruent design. They must be reconciled against the existing C-1…C-5 draft before that draft can become canonical.

Mapping:

* C-1 → Check A: Sampling semantics
* C-2 → Check B: Category and role independence
* C-3 → Check C: Clamp burden and support overlap
* C-4 → Check D: Pixel-level ratio identifiability
* C-5 → Engineering gates: provenance, determinism, configuration coverage, and machine-checked invariants

The assignment-level sweep uses the precommitted seeds and bound formula already recorded in the repository. Thresholds must not be derived from the same frozen-pilot results that they gate.

### Check A — Sampling semantics

**Purpose:** Verify that the realized distance ratio remains governed by the intended depth-gap design, rather than being replaced by floor clamping, floor-band jitter, or another sampling artifact.

Measure, for every seed:

1. Pearson or prespecified rank correlation between realized ratio and `depth_gap_bin`.
2. Retained realized-ratio range:
   [
   \frac{\max(r_{\mathrm{realized}})}
   {\min(r_{\mathrm{realized}})}
   ]
3. The same correlation and range on the unclamped subset.
4. The weakest category-pairing stratum for each quantity.
5. Aggregate and per-pairing sample counts.

The primary lower-bound quantities are:

* correlation between realized ratio and `depth_gap_bin`;
* retained realized-ratio range;
* any separately preregistered acceptance fraction.

For quantities where higher is better, the seed-robust lower bound is computed mechanically as:

[
L_q=\min_s q_s-k,\mathrm{SD}_s(q)
]

using the precommitted seed list, precommitted (k), and outward rounding rule.

The bound must be computed only after all seeds complete. The formula, seeds, (k), spread rule, rounding rule, and weakest-stratum rule must exist in git history before the sweep results.

**Failure interpretation:** Failure means the generator does not express the intended ratio variable reliably. It is an instrument failure, not a model result.

---

### Check B — Category and role independence

**Purpose:** Ensure that category identity, category pairing, or near/far role does not provide a lookup table for realized ratio, depth, or clamp status.

The retained category support must be symmetric:

[
(a,b)\in S\Rightarrow(b,a)\in S
]

For every retained category (c), verify both at assignment level and after successful placement:

[
P(\mathrm{near}\mid c)=0.5
]

[
P(\mathrm{far}\mid c)=0.5
]

Measure, for every seed:

1. (\eta^2(\text{category pairing}\rightarrow\text{realized ratio}))
2. (\eta^2(\text{near category}\rightarrow\text{realized ratio}))
3. (\eta^2(\text{far category}\rightarrow\text{realized ratio}))
4. (\eta^2(\text{near category}\rightarrow\text{realized far depth}))
5. (\eta^2(\text{far category}\rightarrow\text{realized far depth}))
6. Category and pairing effects on clamp status.
7. Category-conditioned near/far balance before and after placement.
8. The weakest pairing and weakest near-/far-role category for every measure.

Both roles must be bounded. The currently measured mechanism is near-role dominant—most notably bottle-as-near forcing the far object deeper—but the criterion must not depend on that mechanism being remembered correctly.

For quantities where lower is better, the seed-robust upper bound is computed mechanically as:

[
U_q=\max_s q_s+k,\mathrm{SD}_s(q)
]

using the precommitted seed list, precommitted (k), spread rule, and outward rounding rule.

If the precommitted spread rule is triggered, the affected quantity is demoted to reported-only and cannot serve as a binding gate until its instability is resolved.

**Structural hard failures:**

* asymmetric retained category-pair support;
* assignment-level or placed-level category-role imbalance beyond the preregistered tolerance;
* category pairing deterministically or near-deterministically identifies the realized ratio;
* category or role deterministically identifies clamp status.

---

### Check C — Clamp burden and support overlap

**Purpose:** Quantify how often the floor changes a sampled ratio and ensure that clamping does not create a separate, category-identifiable ratio regime.

The primary intervention-rate measure is:

[
\mathrm{clamped_fraction}
=========================

\frac{
#{r_{\mathrm{raw}}<r_{\mathrm{floor}}}
}{N}
]

`accepted_in_floor_band_fraction` is a separate descriptive statistic:

[
\mathrm{accepted_in_floor_band_fraction}
========================================

\frac{
#{r_{\mathrm{accepted}}\in\text{floor band}}
}{N}
]

It must never be interpreted as the fraction of samples changed by the floor.

Measure, for every seed:

1. Aggregate `clamped_fraction`.
2. Per-pairing `clamped_fraction`.
3. Per-near-category `clamped_fraction`.
4. Per-far-category `clamped_fraction`.
5. Maximum stratum-level `clamped_fraction`.
6. Raw, unclamped, and realized ratio ranges.
7. Overlap between clamped and unclamped realized-ratio distributions.
8. Whether pairing, near category, or far category predicts clamp status.
9. `accepted_in_floor_band_fraction`, explicitly labelled as descriptive only.

For `clamped_fraction` and other quantities where lower is better, use the preregistered seed-robust upper-bound formula:

[
U_q=\max_s q_s+k,\mathrm{SD}_s(q)
]

**Binding hard failures:**

1. Any retained category pairing is always clamped.
2. The realized-ratio support of clamped and unclamped samples is disjoint.
3. Category identity or category pairing predicts clamp status strongly enough to make clamping a semantic lookup.
4. Clamping causes realized ratio to cease tracking the intended depth-gap design.
5. A weakest prespecified stratum violates its bound even when the aggregate passes.

Failure cannot be repaired analytically after rendering. It requires changing the generator or the retained support.

---

### Check D — Pixel-level ratio identifiability

**Purpose:** Verify that the ratio variation established by Checks A–C is recoverable from rendered pixels under held-out nuisance factors. Metadata-level variation alone is insufficient.

This check runs on the frozen rendered pilot, not on the assignment-level seed sweep.

Evaluate at least:

1. Held-out depth-gap bins.
2. Held-out object categories within the preregistered eligible support.
3. Held-out camera poses.
4. Held-out lighting families.
5. Held-out background or texture families.
6. Held-out nuisance combinations.
7. The shared four-category, three-regime matched contrast:

   * natural-congruent;
   * counterbalanced;
   * conflict.
8. The weakest prespecified category-pairing and nuisance stratum.

Report separately:

* ordinal identifiability;
* continuous ranking;
* calibrated ratio magnitude;
* an interpretable pixel or geometric-image baseline;
* a stronger directly supervised pixel model;
* confidence intervals or the preregistered resampling summary;
* sample counts for every held-out stratum.

A sampling correlation such as

[
r(\mathrm{realized\ ratio},\mathrm{depth\ gap\ bin})
]

does not satisfy Check D. It validates generator semantics, not visual recoverability.

**Failure interpretation:** If ratio is present in metadata but not statistically recoverable from pixels under the preregistered held-out conditions, the rendered instrument does not license a downstream representation claim for ratio.

---

### C-5 — Engineering gates

C-5 remains separate from scientific Checks A–D and covers:

* deterministic regeneration;
* byte-identical annotations and masks where required;
* documented pixel tolerance for beauty renders;
* clean provenance;
* source/config/input manifest hashes;
* `derivation_source_sha`;
* frozen-config manifest completeness:
  [
  \mathrm{discovered}=\mathrm{expected}
  ]
* failure when a required config is absent;
* no glob or optional-field filter that can silently exclude production configs;
* exact category-support symmetry;
* exact assignment-level balance;
* placed-level balance within the preregistered tolerance;
* correct target-only near/far role assignment;
* per-object physical-size reconstruction invariant;
* regime-aware floor validation;
* all freeze-critical fields matching the canonical frozen block.

No §5 criterion is ratified until this canonical text has been reconciled against the existing local draft.
