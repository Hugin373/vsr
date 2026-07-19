# M4a blocker #9 — cue constants, floor squeeze, bin-drop consistency

Date: 2026-07-19 · derivation version `2.0.0` · derived at git `da0b83c` · source sha `957dbef540f7c3ce`

Scope: **derive the cue constants and measure the 1.85 floor.** Textures, the
freeze tag, contrastive pairs and the 1k render were deliberately not touched.

---

## 1. Schema fix — three size schemas, hard-fail, no fallback

`derive_cue_constants.py` read `factors["size_multiplier"]` unconditionally. That key exists only
on the shared-multiplier sets (v0, natural-congruent); counterbalanced and conflict record
`size_multiplier_near` / `size_multiplier_far`, so the script could not run on two of the three
regimes at all. The schema handling now lives in `src/sbind/stimuli/cue_constants.py`:

| schema | normalizer | used by |
|---|---|---|
| `shared` | `factors["size_multiplier"]` | v0, natural-congruent |
| `per_object` | `factors["size_multiplier_<role>"]` | counterbalanced, conflict, contrastive-pairs |
| `explicit` | the object's own `size_m` | reserved for per-object physical sizing |

The schema is resolved from `condition.size_schema`, else from `condition.size_condition` via an
exhaustive map **with no default** — an unrecognised `size_condition` stops the derivation. A
missing required field raises `CueConstantSchemaError`; there is no cross-schema fallback.

**Two further defects were found and fixed while doing this**, both of the project's usual
silently-wrong-output shape:

1. **Roles were assigned by `argmin` over *all* objects.** Distractors sit at world-y 2.7–4.4 m
   and can be nearer than the far target, so on the 7/40 and 12/60 images that carry one, the
   distractor was labelled "near" and both targets' constants were attributed to the wrong role.
   Distractors also carry their own multiplier (0.45–0.7× category size), unrelated to the target
   pair's, so they were being normalised by the wrong number as well. Roles now come from
   `factors["target_object_indices"]` + `factors["closer_object"]`, and distractors are excluded.
2. **`--check-floor` would have reported counterbalanced and conflict as violations.** Those
   regimes decorrelate or invert the size cue on purpose; a congruence floor is not a requirement
   there. The check is now applied only where the design claims congruence — the same distinction
   `validate_stimuli.py` already makes.

### The invariant that makes a fallback structurally impossible

Forbidding a fallback in prose is weak. Every object additionally has to satisfy

```
size_norm × size_m_by_category[category] == object.size_m
```

which breaks immediately if the wrong multiplier is divided out, whatever the reason — a shared
value on a per-object set, or the far object's multiplier read for the near object. A silently
wrong constant of this class cannot pass.

### Rule-11 verification: the tests fail against the old behaviour

`tests/test_cue_constants.py` (17 tests) was run against a shim reproducing the pre-fix logic
(unconditional shared multiplier + the tempting `factors.get("size_multiplier", …)` fallback +
`argmin` roles). **15 of 17 fail**; the 2 that pass describe behaviour that was already correct for
shared-multiplier sets. Reproduce with the plugin in the session scratchpad, or by reverting
`size_norm` / `target_roles` to the versions quoted in the test module docstring. The suppressed
error is quantified in `test_naive_shared_fallback_is_caught`: the naive fallback inflates the far
object's height constant by `far_mult / near_mult` = **1.60×** on the counterbalanced ranges, with
no exception and no downstream symptom.

---

## 2. Measurement instrument — dense ID-pass-only sweep

The rendered pilots give only ~23 samples per (category, role) cell, and a half-sample subset of
the worst cell recovered just **48%** of the measured range: the extremes had visibly not
converged, so a floor derived from them would be a lower bound wearing a worst case's clothes.

The constants depend on the flat-emission ID pass only (silhouette height + mask area) — the beauty
pass, materials, ground colour and lighting do not enter them. `scripts/measure_silhouettes.py`
renders that pass alone at **0.17 s/scene** instead of ~3 s, buying ~50× the pose coverage.

**Instrument validated (rule 11 / rule 1):** replaying the exact scenes of two rendered sets through
the measurement path reproduces the shipped annotations **exactly** — 0.000 px and 0 px max
difference on `retinal_size_px` and `mask_area_px` over 179 objects (natural-congruent 89, conflict
90). It is not an approximation of the renderer; it is the same code path with the beauty pass
removed.

⚠ These write to `$DATA_ROOT/measurements/`, not `stimuli/`. They are **measurement sets, not
stimuli**: no beauty images, no mask PNGs, no questions.

Swept 1200 scenes / 2400 target objects per regime from the frozen pilot configs → **198–202
samples per (category, role) cell**, up from ~23.

---

## 3. Derived constants (six categories, worst case, per regime)

Committed as a `cue_constants` block in every M4a config, between generated sentinel comments, with
full provenance (source set, seed, render git hash, derivation version, per-cell n). Full numbers:
`reports/m4a_cue_constants/{natural_congruent,counterbalanced,conflict}.json`.

| regime | source sweep | n img / obj | per-cell n | height thr | area thr | **binding** |
|---|---|---:|---:|---:|---:|---:|
| natural-congruent | `cue_sweep_natural_congruent` | 1200 / 2400 | 198–202 | 1.0700 | 1.7661 | **1.7661** |
| counterbalanced | `cue_sweep_counterbalanced` | 1200 / 2400 | 198–202 | 1.1135 | 1.8671 | **1.8671** |
| conflict | `cue_sweep_conflict` | 1200 / 2400 | 198–201 | 1.0843 | 1.8526 | **1.8526** |

Area binds in every regime, and the binding pairing is **near=bottle / far=cube** in all three.
`contrastive_pairs` inherits the counterbalanced block, marked `inherited_note` in its provenance:
that regime is still a scaffold and has never been rendered, and its multiplier range differs
slightly ([0.75, 1.22] vs [0.75, 1.20]).

Natural-congruent height and area constants (`px·depth` and `px·depth²`, size normalised out):

| category | C_h near | C_h far | C_a near | C_a far |
|---|---|---|---|---|
| bottle | 398.7 – 408.1 | 393.5 – 412.4 | 48 653 – 52 741 | 46 995 – 50 866 |
| chair | 397.0 – 421.3 | 382.5 – 405.4 | 80 047 – 94 484 | 72 753 – 85 805 |
| cube | 391.3 – 446.3 | 367.0 – 397.5 | 140 690 – 177 093 | 126 252 – 151 754 |
| cylinder | 389.8 – 437.2 | 362.1 – 393.6 | 125 638 – 142 034 | 118 085 – 126 849 |
| mug | 396.7 – 431.2 | 378.0 – 402.3 | 121 496 – 130 053 | 117 734 – 122 923 |
| sphere | 400.0 – 408.8 | 397.2 – 417.1 | 127 792 – 133 677 | 126 730 – 131 469 |

The v0 lesson reproduces at six categories: the cube's area constant spreads **25.9%** as near and
**20.2%** as far, while a sphere's spreads 4.6% / 3.7%. Means are not usable here.

### Per-regime derivation is a FORMAL RULE; pooling is a diagnostic

**Enforced in code (2026-07-19):** `--write-config` refuses to run when more than one `--set` is
pooled, and a pooled run prints a banner saying it is never the operative bound. Pooling remains
useful for two things, and only these:

* **Stress diagnostic** — how far a regime's bound moves when foreign pose conditions are admitted.
* **Regime isolation** — *which* pairing drives that divergence, i.e. where one regime's envelope
  reaches conditions another never produces.

Measured (`reports/m4a_cue_constants/POOLED_DIAGNOSTIC.json`, pooled bound 1.8672):

| regime | own bound | inflation under pooling | worst diverging pairing | median divergence |
|---|---:|---:|---|---:|
| natural-congruent | 1.7661 | **+5.72%** | near_bottle_far_cube (+0.1011) | +0.0429 |
| counterbalanced | 1.8671 | +0.00% | near_sphere_far_sphere (+0.0161) | +0.0029 |
| conflict | 1.8526 | +0.79% | near_mug_far_mug (+0.0363) | +0.0120 |

The divergence is concentrated almost entirely in natural-congruent's bottle/cube pairing: the
shared-multiplier congruent envelope never produces the far-object sizes the per-object regimes do.
The other two regimes are close to exchangeable. `C_a` is not perfectly size-invariant — conflict
renders far objects at 1.12–1.30× physical size, and a larger object at the same depth presents a
different perspective — so pooling imports pose conditions a regime never produces.

### Residual uncertainty, stated rather than assumed away

At n≈200 per cell the extremes still have not fully converged: the worst cell's half-sample subset
recovers **74.9% / 78.8% / 87.2%** of the measured range (median across cells ~94–96%). So each
threshold remains a **lower bound** on the true worst case, and the committed floors must retain
margin rather than sit on the number. Re-derive at §5 re-render scale before the freeze tag.

---

## 4. The 1.85 floor — floor-squeeze measurement and verdict

Method: sample each config twice from the same seed, once with the real floor and once with a floor
that cannot bind (1.000001, retaining the jitter draw so the RNG stream is identical). n = 1200 per
regime. Full stratified tables: `reports/m4a_floor_squeeze/*.txt` and `*.json`.

| regime | floor | available ratio | accepted ratio | acceptance frac | floor-determined frac | r(ratio, depth_gap_bin) available → accepted | oracle ratio R² |
|---|---:|---|---|---:|---:|---|---:|
| natural-congruent | 1.85 | 1.046–1.474 | 1.850–1.998 | **0.000** | **1.000** | **+0.906 → −0.017** | −0.252 FAIL |
| counterbalanced | 1.05 | 1.055–1.471 | 1.066–1.471 | 1.000 | 0.058 | +0.905 → +0.905 | +0.803 PASS |
| conflict | 1.05 | 1.047–1.447 | 1.055–1.447 | 0.999 | 0.064 | +0.909 → +0.909 | +0.420 PASS |

### Verdict: the natural-congruent ratio-gate failure IS a design artifact — but not of the number 1.85

**The floor sits above the entire ratio range the design produces.** Natural-congruent's available
far/near depth ratio spans 1.046–1.474; the floor is 1.85. Acceptance fraction is **0.000** — not
"most images", *every* image has its far object pushed back until the ratio lands in the floor band
[1.850, 1.998]. The accepted depth ratio is therefore `1.85 × (1 + U(0, 0.08))` and nothing else: an
independent uniform draw.

The correlation collapse is the mechanism, measured: `r(ratio, depth_gap_bin)` goes from **+0.906**
without the floor to **−0.017** with it, and `r(ratio, near_depth_bin)` from −0.322 to −0.013. In
the two regimes that pass the gate, the same correlations are untouched (+0.905 → +0.905). So in
natural-congruent the depth ratio is statistically independent of every depth factor by
construction. Regressing on a target that is independent noise, under a held-out depth-gap split,
generalises worse than predicting the mean — which is exactly what a **negative** R² of −0.252 is.
Retained dynamic range collapses to 1.07–1.08× per pairing, against 1.29–1.32× in the other regimes.

**But the number 1.85 is not the culprit, and lowering it does not fix this.** The derivation in §3
gives a worst-case congruence requirement of **1.7661** for this regime, and 1.85 clears it with
**+4.75%** headroom — a defensible margin, and the per-pairing table shows every one of the 36
pairings cleared. `validate_stimuli.py` enforces area congruence as a hard check for
`natural_congruent`, so the requirement is real, not optional. The problem is structural:

> **the minimum floor any congruent six-category design can use (1.766) already exceeds the maximum
> ratio the design produces (1.474).**

There is no value of `min_depth_ratio` that both satisfies area congruence and leaves the depth
ratio informative in this camera/depth geometry. Area congruence and an informative ratio target
are incompatible for this category set as currently calibrated.

The driver is the calibration: sizes were solved to equalise retinal **height**, which leaves area
shape-dependent. A height-calibrated bottle's silhouette area is ~3× smaller than a cube's
(`sqrt(151754 / 48653) = 1.766`), and near=bottle / far=cube is the binding pairing in all three
regimes.

### Resolution direction (advisor ruling, confirmed with numbers 2026-07-19)

**RESTRICTED CATEGORY PAIRINGS is the default**, keeping hard area congruence — because the control
regime's ratio arm is the all-cues-agree reference for the conflict regime's fusion analysis and has
to stay valid. Full decision table: **`reports/m4a_natural_congruent_decision.md`**. Headline:

- Largest symmetric feasible subset is **{cube, cylinder, mug, sphere}** with a **uniform** floor of
  1.1707 → retained ratio 1.171–1.458 (**1.25×**, vs 1.08× now), clamped fraction 0.332, and
  `r(ratio, depth_gap_bin)` restored from **−0.017 to +0.751**.
- The safeguard the ruling specified **fired and disqualified per-pair floors over all six
  categories**: η²(pairing → ratio) = **0.823**, worst pairwise distribution overlap **0.000**. That
  is v0's shape-predicts-ratio confound at full strength, and it does not even solve the problem
  (4 pairings remain infeasible). A *uniform* floor over a restricted set has η² = 0 by construction.
- The fallback to primitives-only is therefore **not triggered** — category does not predict ratio
  under the default. Primitives-only stays available and measures marginally better on range
  (1.28×, clamped 0.261) at the cost of a category.
- Sets must be **symmetric** (C × C): the `cat_pair` balancing is what gives each category an exact
  0.500 near/far split, and that split is what closes B2→z. An asymmetric retention would make
  bottle preferentially near and reintroduce the confound the balancing exists to kill.

Predicted to pass the ratio gate, **not proven to** — the passing regimes sit at r = +0.905 / 1.38×
with R² = +0.803 and +0.420, so A1-4cat lands between the current failure and them. That is a §5
measurement to be reported, not assumed.

Whichever is taken: **natural-congruent stays a control, not the localisation-claim regime**, which
is where the battery report already put it. What changes is the reason — the ratio target there is
not "narrow and shortcut-heavy", it is not a scene property at all.

---

## 5. Bin-drop consistency sweep and dynamic-range assessment

### Consistency: five configs were stale, and the guard that should have caught it was scoped out

`near_depth_bins: [0.65, 1.10, 1.55, 2.00]` was applied only to the three frozen pilot configs.
`m4a_v1_natural_congruent.yaml`, `m4a_v1_counterbalanced.yaml`, `m4a_v1_conflict.yaml`,
`m4a_v1_contrastive_pairs.yaml` and `m4a_v1_counterbalanced_pilot.yaml` still carried the dropped
0.2 m bin — and also the pre-freeze pan-only camera jitter (no `pos_x_m` / `pos_y_m`) and
`target_placement_attempts: 120`. All five are now synced to the frozen generator block.

The existing guard `test_frozen_m4a_configs_place_at_scale` passed throughout, because it globbed
only `*_pilot*` configs **and** skipped any config without `pos_x_m` — the two filters between them
excluded exactly the five configs that were wrong.

**Now MANIFEST-based (advisor arbitration item 3), not a widened glob.** `M4A_CONFIG_MANIFEST` lists
the eight stimulus configs explicitly, and `test_m4a_config_manifest_matches_disk` asserts
`discovered == expected` **before** any field is compared. A glob only answers "is everything I found
consistent?", which stays vacuously true when a config is deleted or renamed — coverage silently
drops to nothing and the suite stays green. `test_frozen_generator_block_per_config` is then
parametrised per config over bins, camera jitter, **translation** (called out separately as the
load-bearing addition) and the placement budget. Verified: both fail against the pre-fix configs,
and the manifest test fails when a config is removed from disk.

### Dynamic range: reported as a property, per DR3 #14 — not a failure

| quantity | pre-drop (5 bins) | post-drop (4 bins) |
|---|---|---|
| counterbalanced depth span | 2.57–6.25 m (2.44×) | 2.95–6.23 m (2.11×) |
| counterbalanced ratio range | 1.058–1.538 (sd 0.100) | 1.055–1.471 (sd 0.089) |
| natural-congruent depth span | 2.55–9.68 m (3.80×) | 2.98–9.61 m (3.22×) |
| placement failures / 1200 | 5–6 | **0** |
| near_depth_bin balance (min/max) | 0.975–0.992 | **1.000** |

The bin drop costs ~13% of the depth dynamic range and ~11% of the ratio target's spread, and buys
100% placement (which is what closes the B2→z rejection channel) and exact factor balance. Validity
holds in every regime: ordinal margin is strictly positive everywhere (minimum 0.242 m in conflict,
0.258 m counterbalanced, 2.630 m natural-congruent — 0 non-positive over 1200 each), the near/far
class balance is exact, and the continuous targets still span 2.1–3.2× in depth. Several targets
became easier; per DR3 #14 that is reported, not engineered away.

### ⚠ Retired numbers: the "~3.1×, was ~10×" figures — provenance corrected

**Resolved 2026-07-19 (advisor).** The figures were **bin-endpoint arithmetic**: the ratio of the
outermost `near_depth_bins` entries, `2.0 / 0.65 = 3.0769` post-drop and `2.0 / 0.20 = 10.0`
pre-drop. They are ratios of the near object's **world-y offsets**, not depth ratios and not
dynamic ranges — the camera sits at y = −2.5, so those offsets map to actual depths of ~2.95–4.95 m,
a 1.68× span, and no quantity in the battery ever takes the value 10.

The measured quantities they were mistaken for:

| quantity | pre-drop | post-drop |
|---|---|---|
| depth dynamic range (natural-congruent) | 3.80× | 3.22× |
| depth dynamic range (counterbalanced) | 2.44× | 2.11× |
| max far/near depth ratio | 1.538 | 1.474 available / 1.998 accepted |

🔴 **Labeling hazard, recorded deliberately.** `2.0 / 0.65 = 3.0769` sits **0.35%** away from the
conflict regime's shape-plus-multiplier apparent-size requirement, **3.0876** — two unrelated
quantities, in different units, that round to the same "~3.1". Last session this near-collision was
noted as "the nearest 3.1 in this session's numbers", which is exactly the coincidence that would
let a bin-endpoint number be re-attributed to an apparent-size derivation by a later reader. Neither
number should ever be quoted as "~3.1" without its unit and derivation.

---

## 6. Reproduce

```bash
export DATA_ROOT=/data3/hugin/vsr HF_HOME=/data3/hugin/hf_home

# instrument validation (must be exact)
uv run --extra stimuli scripts/measure_silhouettes.py \
    --validate-against $DATA_ROOT/stimuli/m4a_v1_natural_congruent_pilot

# dense sweeps (~3.5 min each)
uv run --extra stimuli scripts/measure_silhouettes.py \
    --config configs/m4a_v1_natural_congruent_pilot.yaml --n 1200 \
    --out $DATA_ROOT/measurements/cue_sweep_natural_congruent

# constants + config write-back
uv run --extra analysis scripts/derive_cue_constants.py \
    --set $DATA_ROOT/measurements/cue_sweep_natural_congruent --check-floor 1.85 \
    --json reports/m4a_cue_constants/natural_congruent.json \
    --write-config configs/m4a_v1_natural_congruent.yaml \
    --write-config configs/m4a_v1_natural_congruent_pilot.yaml

# floor squeeze
uv run --extra analysis scripts/floor_squeeze.py \
    --config configs/m4a_v1_natural_congruent_pilot.yaml --n 1200 \
    --constants reports/m4a_cue_constants/natural_congruent.json \
    --json reports/m4a_floor_squeeze/natural_congruent.json

uv run pytest -q && uv run ruff check src/ tests/ scripts/
```

## 7. Provenance audit — do the committed constants derive from post-role-fix code?

Asked because `derived_at_git_hash` recorded `ac36cd3-dirty` for every run: the `-dirty` suffix
erases exactly the distinction being asked about, and the three measurement sweeps carry three
different `git_patch_sha` values because the tree changed between them. Archaeology could not settle
it, so it was settled by reproduction instead.

- **640 of 3600 swept scenes carry a distractor**, so the role fix genuinely bites — a pre-fix
  derivation would have been corrupted, not merely differently-formatted.
- **Measurement reproduces byte-identically at HEAD.** Re-running the natural-congruent sweep at
  `da0b83c` with a clean tree gives an `annotations.jsonl` with md5 `0f4a68f4…`, identical to the
  stored one.
- **Derivation reproduces byte-identically at HEAD.** Re-deriving all seven per-regime configs
  reproduces every committed `cue_constants` value exactly (only the timestamp and git hash differ).

**Verdict: the committed constants are REPRODUCIBLE UNDER THE CORRECTED HEAD.** Nothing needed
re-running.

⚠ **Wording is load-bearing (advisor, 2026-07-19).** This is *not* the claim that "historical runs
are proven corrected" — no stamp recorded at the time can support that, because `-dirty` erased the
distinction. What is established is that re-running the current code over the same inputs yields
the committed values byte-for-byte. The report now records this as a
`provenance_claim` field rather than leaving the reader to infer the stronger claim.

**Provenance hardened so this is answerable without reproduction next time.** Every block now
records `derivation_source_sha` (content hash of `cue_constants.py` + `derive_cue_constants.py`),
`render_git_patch_sha`, `measurement_only`, and an explicit `provenance_claim` string.

**Meta-lesson, recorded because this is the SECOND hardening of the same subsystem.** The first
(2026-07-17) added `-dirty` after `git_hash()` was found to record a commit that could not have
produced the output. That fix was right and insufficient: **`-dirty` flags impurity but destroys
resolution.** It says "something was uncommitted" and thereby makes every dirty run
indistinguishable from every other dirty run of the same commit — which is exactly the question
that got asked two days later. The general rule: **a stamp must answer the questions that will
later be asked of it, not merely record that a hazard existed.** A flag that collapses distinctions
is not neutral; it forecloses the audit it appears to enable.

## 8. Still owed

Per the ruled sequence: **decision table** (done — `reports/m4a_natural_congruent_decision.md`) →
implement the chosen natural-congruent fix (freeze work) → textures → determinism byte-compare →
freeze tag → §5 one-shot. Plus re-deriving these constants over whichever envelope the
natural-congruent decision selects.
