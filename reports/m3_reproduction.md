# M3 — Reproductions (the project's go-gate)

*Run 2026-07-14. Both source repos have **NO LICENSE**; they were read for understanding and
**reimplemented from the papers**, never copied (CLAUDE.md hard rule).*

**Verdict at a glance**

| Milestone | Bar | Result |
|---|---|---|
| **M3.1 — Kang et al.** (2601.12626) | steering ≫ norm-matched noise; effect *directions* match; magnitudes within a few points | **PASS on the mechanism, FAIL on the absolute magnitude.** Every qualitative claim reproduces, several more cleanly than in the paper. The absolute belief-swap rate does not. |
| **M3.2 — Wang & Gao** (2605.07148) | pattern match: semantics ≫ metric; x ≈ chance; z modest | **FAIL — and the cause is OUR STIMULI, not the method or the models.** |

**The one-sentence read:** the *mechanistic* reproduction (M3.1) succeeds and the project's
core premise survives; the *stimulus* reproduction (M3.2) fails because the v0 congruent set
cannot express the phenomenon — which is a finding about our generator, and it must be fixed
in M4 before any Phase-2 metric-probing claim is made.

Per the milestone rule ("if either fails after honest effort, STOP and rethink framing"), no
parameter was tuned to make M3.2 pass. §3 says exactly what is wrong and what M4 must change.

## 🚦 GATE DECISION: **GO** (advisor review, 2026-07-14)

Phase 2 proceeds. The reasoning:

- **M3.1 is sufficient.** The binding-bottleneck design depends on the mechanism *existing and
  being steerable*, not on a 64% swap rate. Patching profile, rank-3 structure, and selective
  steering against a dead noise floor all reproduce. The magnitude gap is a property of our
  stimuli's difficulty, not of the mechanism (and §1.4 shows the certainty story is refuted —
  the gap is honestly *unexplained*, and does not need to be resolved to proceed).
- **M3.2's failure is not re-run on v0.** The diagnosis is complete and v0 cannot support the
  measurement by construction. Re-running it would be theatre.
- **Instead, M3.2's pass bar TRANSFERS to M4 as an acceptance criterion:** *"the Wang & Gao
  pattern emerges — semantics ≫ metric, with a difficulty gradient present."* If the
  decorrelated M4 battery still yields R² ≈ 0.99 everywhere **after the leak controls of §2.4**,
  the stimuli are still broken. **When the gradient appears, the instrument is finally
  measuring the models rather than itself.** That is the real gate on Phase 2, and it now sits
  in M4 where it belongs.

---

## 1. M3.1 — Kang et al., reimplemented

### 1.1 Setup

- **Models:** LLaVA-1.5-7B (`llava-hf/llava-1.5-7b-hf`, 32 layers), Qwen2.5-VL-7B
  (`Qwen/Qwen2.5-VL-7B-Instruct`, 28 layers).
- **Data engine:** 640 two-object scenes tiled on a **4×4 grid** (m=4, the paper's value),
  672², one binary forced-choice question per scene
  (*"Is the {A} to the left or right of the {B}? Answer with one word."*).
- **Spatial IDs:** `ID_L(i,j) = mean_o [ φ_L(o at (i,j)) − mean_cells φ_L(o) ]`, read at the
  object's **word token**, mean-centred **per object** — arithmetic, not a trained probe.
- **Steering:** `x_L[q] ← x_L[q] + α·‖x_L[q]‖·d/‖d‖` with `d = ID_L(i,j) − ID_L(m−1−i, j)`
  (the left↔right mirror), **α = 5** (the paper's grid-searched value).
- **Control:** a **norm-matched random direction**. This is the whole ballgame — a large-norm
  perturbation in *any* direction disturbs a belief, so an uncontrolled swap rate proves nothing.

**Deviation from the paper, stated plainly:** Kang tile **Objaverse renders**; we do not have
Objaverse, so we tile **COCO instance-mask cutouts** (40 categories, clean cutouts on a white
canvas). Object appearance is not the mechanism under test — the spatial ID is precisely what
*survives* mean-centring across objects — but it is a deviation and may contribute to §1.4.

**The invariant this dataset must satisfy, and does:** object identity must be decorrelated
from grid position, or mean-centring per object does not isolate a position code and the whole
derivation is circular. Enforced by construction — every object is placed in every cell exactly
twice — and checked: **total-variation from uniform = 0.000 exactly**; 0 same-column and 0
same-row pairs (so every gold answer is defined); answer key 52.0% left.

### 1.2 Results vs the paper

| | **Paper** | **LLaVA-1.5-7B** | **Qwen2.5-VL-7B** |
|---|---|---|---|
| task accuracy before intervention | — | 95.3% | 98.0% |
| **steering @ α=5**, best middle-third layer | **64.4%** | 19.3% (L12) | 31.3% (L14) |
| **norm-matched noise control** | **29.5%** | **0.7%** | **0.0%** |
| above-chance influence (Kang: NAMED stat, cross-model avg; ours: steer − noise, descriptive) | **+43.6 pts** ⚠ | +18.7 pts | **+31.3 pts** |
| peak over the α sweep | — | 31.3% (α=40) | **43.3% (α=10)** |
| peak (ours only; NOT comparable to Kang, DR3-r2 #10) | — | +30.0 pts | **+43.3 pts** |
| rank-3 R² (low-rank position code) | **≥ 0.85** | **0.87** | **0.84** |

⚠ **Column-definition mismatch, stated so the table is not misread (DR3-r2 #10):** Kang's
"above-chance influence" (+43.6%) is a NAMED statistic averaged across their tested models (§3 +
Fig 2 caption); it is **not** 64.4 − 29.5 = 34.9. Our +31.3 / +43.3 are a within-set steer − noise
difference on ONE model. The columns are **descriptive, side by side, not commensurable** — do not
subtract or rank across them.

### 1.3 The mirror-swap patching profile — the paper's central localization claim

Normalised belief shift when the mirrored image's activations are patched into the original
(0 = no effect, 1 = fully adopts the mirrored belief):

**LLaVA-1.5-7B**

| layer | 0 | 4 | 8 | 10 | **12** | **14** | 16 | 20 | 24 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|
| image patches | 1.00 | 1.00 | 0.98 | 0.98 | 0.21 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 |
| **object-word tokens** | −0.00 | −0.00 | 0.01 | 0.01 | **0.31** | **0.34** | 0.00 | 0.00 | 0.00 | 0.00 |
| text tokens | −0.00 | 0.00 | 0.01 | 0.01 | 0.74 | 0.98 | 1.00 | 1.00 | 1.00 | 1.00 |

**Qwen2.5-VL-7B**

| layer | 0 | 4 | 8 | 12 | **14** | **16** | 18 | 20 | 24 | 26 |
|---|---|---|---|---|---|---|---|---|---|---|
| image patches | 1.00 | 1.00 | 1.00 | 1.00 | 0.91 | 0.12 | 0.06 | 0.00 | 0.00 | 0.00 |
| **object-word tokens** | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 | **0.12** | 0.06 | 0.00 | 0.00 | 0.00 |
| text tokens | 0.00 | 0.00 | 0.00 | 0.00 | 0.08 | 0.88 | 0.95 | 1.00 | 1.00 | 1.00 |

This is **exactly the paper's profile — image patches early, object-word tokens in the middle,
text late** — reproduced independently on both models. It is the single most important
qualitative claim in Kang et al., and it comes out crisply.

### 1.4 The steering dose-response (diagnostic, not a fix)

At the paper's α=5 our swap rate is well below theirs, so we measured the one free parameter
across its range. **The headline number above stays fixed at α=5.** This curve exists to
distinguish "the mechanism is absent" from "the scale constant differs".

| α | LLaVA (L12) ID / noise | Qwen (L14) ID / noise |
|---|---|---|
| 1 | 4.7% / 0.7% | 10.0% / 0.0% |
| 2 | 7.3% / 0.0% | 23.3% / 0.0% |
| **5 (paper)** | **19.3% / 0.7%** | **31.3% / 0.0%** |
| 10 | 28.7% / 1.3% | **43.3% / 0.0%** |
| 20 | 30.0% / 1.3% | 42.7% / 0.0% |
| 40 | 31.3% / 1.3% | 34.0% / 0.0% |

Monotone, saturating, and **the noise control never moves at any dose** (0–1.3%). This is a
textbook dose-response for a real, graded causal mechanism.

### 1.5 PASS / FAIL per criterion

| Criterion | Verdict | Evidence |
|---|---|---|
| Steering belief-swap **far above** the norm-matched noise control | ✅ **PASS** | 31.3% vs **0.0%** (Qwen, α=5); 19.3% vs 0.7% (LLaVA). The *selectivity* is far cleaner than the paper's 64.4 vs 29.5 (a 2.2× ratio); ours is effectively unbounded. |
| All key effect **directions** match | ✅ **PASS** | patching profile (image→object-word→text) reproduces on both models; steering is monotone in α; noise is flat. |
| Spatial IDs are a **low-rank** position code | ✅ **PASS** | rank-3 R² = 0.87 / 0.84 vs the paper's ≥0.85. |
| Binding localised to **middle layers** | ✅ **PASS** | Qwen's steering peak is L14 of 28 — dead centre; object-word patching peaks at L14/L16. |
| Magnitudes **within a few points** (~64% vs ~30%) | ❌ **FAIL** | absolute swap is 19–31% at α=5, not ~64%; and our noise floor is 0–1%, not ~30%. |

**How to read the magnitude failure honestly.** Both halves of the paper's headline pair are
off, *in the same direction*: our models flip less under the spatial-ID direction **and** far
less under noise. Ours is **+31.3 pts** for Qwen at the paper's own α, and **+43.3 pts** at the
dose-response peak. Kang report ≈64.5% median vs 29.5% noise.

> 🔴 **CORRECTED 2026-07-17 (DR3-r2 #10). The retraction stays visible.**
> This concluded: *"the causal effect size **matches or exceeds the paper's**."* **Retired.**
> **Cross-study effect comparisons are DESCRIPTIVE ONLY** — noise construction, dose schedules,
> example selection and baseline belief distributions all differ between the two setups, so the
> two above-chance figures are **not commensurable** and neither is "bigger". Report both; claim
> superiority of neither.
> 🔴 **RESOLVED 2026-07-18 against the paper (arXiv 2601.12626v1 HTML full text) — and it was the
> more serious error.** This report derived Kang's above-chance as 64.4 − 29.5 = **+34.9 pts** and
> called it *"the paper's own summary statistic, the above-chance influence."* **It is not.** The
> paper reports a NAMED statistic — "above-chance influence" — equal to **+43.6%** (its own §3 text
> AND its Figure 2 caption: *"Spatial IDs have 43.6% above-chance influence on average"*), and
> **43.6 ≠ 64.4 − 29.5**: it is an AVERAGE ACROSS the tested models, not the naive median-minus-noise
> for the headline pair. So this report **constructed a statistic (a single subtraction), got 34.9,
> and attributed it to the authors** — precisely rule 4's worse branch. The ledger was correct.
> **34.9 pts is deleted as an attribution to Kang throughout** (it was never their number). Our own
> +31.3 / +43.3 remain OUR descriptive figures. ⚠ Note the now-doubly-retracted claim
> *"+43.3 matches or exceeds theirs"* was also **numerically** false against the real figure
> (43.3 < 43.6) — but the primary reason it is retired is DR3-r2 #10: the two are **not
> commensurable** (different noise construction, doses, selection, baselines), so report both and
> claim superiority of neither. **Final check owed before any write-up: eyeball the actual Fig 2
> caption in the PDF — this resolution rests on the ledger's full-text read plus a web-fetch of the
> HTML, two secondary reads that agree, not on the rendered figure itself.**

#### The obvious explanation is WRONG — we measured it (Qwen, L14, α=5, n=150)

The tempting story is "our models are more certain (95–98% accurate), so a random nudge never
flips a confident belief." **That story does not survive contact with the data:**

| baseline confidence | n | flip under spatial-ID | flip under **noise** |
|---|---|---|---|
| 0.50–0.70 | 4 | 0.0% | **0.0%** |
| 0.70–0.90 | 7 | 42.9% | **0.0%** |
| 0.90–0.99 | 23 | 30.4% | **0.0%** |
| 0.99–1.00 | 116 | 31.9% | **0.0%** |
| **all** | **150** | **31.3%** | **0.0%** |

Noise flips **nothing in any confidence bin** — including 0/23 at 0.90–0.99 and 0/7 at
0.70–0.90 — and the spatial-ID flip rate is **uncorrelated with confidence** (r = +0.03), i.e.
steering works just as well on uncertain beliefs as on certain ones. So "confident models
resist noise" is **unsupported as a within-set mechanism**, and we do not claim it.

What *is* defensible is narrower: **our task produces almost no uncertain beliefs at all**
(mean confidence 0.973; only 11 of 150 items below 0.9). A noise control can only flip a belief
that is near the decision boundary, and our stimuli barely produce any. Kang's 29.5% noise
floor implies a set with many near-chance items; ours has essentially none. That is a statement
about **stimulus difficulty**, not about model certainty — and it is not something we can test
properly on a set this easy.

**Bottom line: the noise-floor discrepancy remains UNEXPLAINED.** It does not threaten the
mechanism (spatial-ID steering beats noise by 31 points regardless of confidence), but we
should not dress it up. **We tuned nothing to close the magnitude gap**, and we do not claim
the magnitudes reproduce. What reproduces is the mechanism, its localization, its low-rank
structure, and its causal selectivity.

---

## 2. M3.2 — Wang & Gao pattern reproduction on our v0 stimuli

### 2.1 Setup

Mask-pooled object tokens at every second LM decoder layer of **Qwen2.5-VL-7B** and
**InternVL3-8B** (their exact two models), on our M1 v0 congruent set (500 images, 1000
objects). Ridge probes for **x** (lateral) and **z** (depth); logistic probes for **shape** and
**colour** as the semantic controls. 5 seeds × 5 folds, scaler fit on train only, and **every
probe reports its shuffled-label control**.

The mask→visual-token mapping was validated before any probing: `rows × cols` must equal the
image tokens in the sequence, **and** the mask's token centroid must land on the object's bbox
centre (a transposed grid has the right token *count*). Verified — LLaVA 24×24, Qwen 18×18,
InternVL 16×16; worst centroid error **0.019** grid units over all 500 images.

### 2.2 Results vs the paper

| | **Paper (Wang & Gao)** | **Qwen2.5-VL-7B (ours)** | **InternVL3-8B (ours)** |
|---|---|---|---|
| **x** (lateral) R² | **−0.09** (≈ chance) | **+0.997** | **+0.999** |
| **z** (depth) R² | **+0.28** (modest) | **+0.990** | **+0.996** |
| shape | R² = 1.00 | acc = 1.000 | acc = 1.000 |
| colour | — | acc = 1.000 | acc = 1.000 |
| shuffled-label controls | — | x/z R² ≤ −0.01, shape 0.33, colour 0.25 | same — all exactly at chance ✓ |

Flat across **every** layer probed, on **both** models: x R² ∈ [0.997, 0.999], z R² ∈ [0.984,
0.996]. Their *exact two models*, and neither shows any trace of the dissociation.

### 2.3 Verdict: ❌ **FAIL** — and the cause is diagnosed

The pass bar is *semantics ≫ metric; x ≈ chance; z modest*. We get **everything ≈ perfect**:
there is no dissociation because **there is no difficulty gradient in our stimuli at all**.

The probes are not broken (their shuffled controls sit exactly at chance, and the pooling
registration is verified). **The stimulus set is.** Two concrete, measured defects:

1. **`x` is not a metric coordinate in v0 — it is a binary side label.** Measured: `x` takes
   **exactly 2 unique values, −0.7 and +0.7** (500 objects each). The sampler places the near
   object at ±`lateral_offset` and the far one at ∓ it. So "decoding x" is "deciding which half
   of the image the object is in" — and mask-pooling *selects its tokens by the object's image
   position*, so the answer is in **which tokens were pooled**, before the model does anything.
   R² = 0.997 measures the pooling, not the representation. **The comparison to their x = −0.09
   is meaningless**: their x varies continuously.

2. **`z` is over-determined by construction.** Depth is **86% predictable from apparent size
   alone** (r = 0.93 between `depth_m` and `size_m / retinal_size_px`), and the *congruent*
   condition is *defined* by every depth cue agreeing — retinal size, elevation, and occlusion
   all point the same way, by design. This is precisely the **monocular-depth shortcut** Wang &
   Gao flag and discount when they see z R² = +0.28. Our congruent set maximises that shortcut
   rather than controlling it.

**This is a real and useful negative result**, not a bug to be papered over: it says the v0
congruent set **cannot serve as the substrate for the metric-probing science**, and it says so
*before* Phase 2 was built on top of it — which is exactly what the go-gate is for.

### 2.4 🔴 The position leak is a THREAT TO THE CORE EXPERIMENT, not a probe caveat

**Mask-pooling from position-indexed visual tokens leaks position by construction.** The pooled
vector averages the tokens *at the object's image location*, and those tokens carry positional
information. The selection **is** the answer.

**Quantified — the leak ceiling on v0** (`scripts/leak_ceiling.py`). Dumb features only: mask
centroid (u,v), mask area, bbox w/h, retinal height, elevation. **No activations. No model.**

| target | mask **geometry alone** | mask-pooled **activations** | what the model adds |
|---|---|---|---|
| **x** (lateral) | **R² = 0.942** | 0.997 | **+0.055** |
| **z** (depth) | **R² = 0.972** | 0.990 | **+0.018** |
| **shape** | **acc = 0.992** | 1.000 | **+0.008** |
| colour | acc = 0.233 (**chance**) | 1.000 | +0.767 |

| the damning slices | |
|---|---|
| x from the mask centroid *u* **alone — one number** | **R² = 0.943** |
| z from (elevation *v*, retinal height) alone | **R² = 0.915** |

*(Ridge/logistic, 5 seeds × 5 folds; shuffled controls at −0.005 / −0.003 / 0.339 / 0.253.)*

**Read the colour row first — it validates the ceiling.** A mask carries no colour information,
and the ceiling duly returns **chance** for colour (0.233 vs a 0.253 shuffled control). The
method is not simply fitting everything. Which makes the other three rows damning:

- **Essentially the entire "metric decodability" on v0 is obtainable without the model.** A
  single number — where the mask's centroid sits — gets x to **0.943**.
- **Even the SEMANTIC control is leaked.** Shape is **99.2%** decodable from mask geometry alone
  (silhouettes differ), so the "semantics ≫ metric" reference we were leaning on is itself
  mostly readable off the mask. On v0, the activations add +0.008 to shape and +0.055 to x —
  i.e. *the model contributes almost nothing to any of it.*

**Why this is bigger than M3.2.** Mask-pooled *visual*-token probes inherit this leak;
*bound-text-token* probes do not (they are not selected by image position). So the four-site
grid's central contrast — **visual sites high, text sites low** — **could be manufactured by
the measurement itself.** That is a direct threat to distinguishing Prediction 1 (metric
survives in visual tokens, dies at binding) from Prediction 2 (metric was never there). This
is the single most important thing M3 produced.

**Three controls are therefore mandatory for Phase 2, not one:**

1. **Leak-ceiling baseline (the "dumb-features" ceiling).** Every decodability claim at every
   site must **exceed** a probe trained on mask geometry alone (centroid, area, bbox, retinal
   size, elevation) — plus shape/colour/cue values. Decodability below the dumb ceiling is not
   "in the representation"; it is in the mask.
2. **Fixed-grid strip probes are PROMOTED to the primary leak-free estimator.** Strips at fixed
   image locations are not selected by the object's position, so decoding object depth from
   them cannot leak via selection. We adopted the Cui et al. strip variant as an
   *underestimation guard*; it is now the load-bearing measurement.
   ⚠ **Correction to an earlier draft of this report: the strip variant is NOT yet cached.**
   `extract/pooling.py` implements `strip_pool()`, but M3.2's extraction saved mask-pooled
   features only. M4's cache must produce both.
3. **Camera-pose jitter at the source.** This also explains the Wang & Gao discrepancy cleanly:
   their scenes have varying camera paths, so camera-frame coordinates are *not* image
   positions. Our camera is fixed, which makes x **identical** to image position — hence
   R² = 0.997 measuring the pooling. Jittering camera height/pitch/yaw decorrelates image
   position from 3D coordinates and shrinks the leak where it is created, rather than
   correcting for it after the fact.

Wang & Gao's cross-scene residualization of the semantic subspace remains a fourth, orthogonal
control.

---

## 3. What M4 must change (the actionable output of this gate)

The stimulus generator needs three fixes before any metric-decodability claim:

1. **Make `x` continuous.** `lateral_offset` is a single constant (0.7). Objects must be
   sampled across a continuous lateral range, or `x` is a side label and not a metric quantity.
2. **Break the size↔depth shortcut.** In the congruent set both objects share ONE size
   multiplier, so apparent size ∝ 1/depth and depth is readable off apparent size. This is
   what M4's `size_condition` (independent per-object physical size jitter) exists to do —
   it is now demonstrably **load-bearing, not optional**.
3. **Add nuisance variation** (camera pose jitter, backgrounds, distractors). A scene with two
   primitives on a bare plane has too few degrees of freedom for "modest decodability" to even
   be possible.

And one analysis fix: **report the position-leak control** (regress out pooled-token grid
coordinates) alongside every mask-pooled probe.

---

## 4. Reproducibility

- Configs: `configs/m3_kang.yaml`, `configs/m3_wanggao.yaml` (seed 0).
- Entrypoints: `scripts/kang_repro.py`, `scripts/kang_dose_response.py`,
  `scripts/wanggao_repro.py`. GPU etiquette per CLAUDE.md (explicit `--gpu`, guard first).
- Artefacts under `$DATA_ROOT/m3_kang/` and `$DATA_ROOT/m3_wanggao/`: spatial IDs, steering,
  patching, rank sweeps, dose-response, pooled features, per-layer probe results.
- 131 tests pass, including: the decorrelation check **fails** on a set where identity predicts
  position; a transposed/flipped token grid is caught; probes find planted signal and **do not**
  find shuffled signal; and the fast dual-ridge / kernel-feature solvers are asserted equal to
  sklearn's on the original features (they were adopted for speed, and a speedup that changes
  the answer is a bug).

### Bugs found in our own M3 code by writing the invariants first
All silent; each would have produced a confident, wrong number.
- The scene generator tied each object to a subset of cells (TV = 0.45) → the spatial-ID
  derivation would have been circular.
- Pairing dropped its unpairable tail, non-uniformly across objects → balance re-broken (TV = 0.030).
- ~1/4 of scenes put both objects in the **same column**, where "left or right" has no ground
  truth — and the code confidently labelled them "right" (key skewed to 253/640).
- The belief readout scored `" left"`/`" right"`, whose first token is the **same whitespace
  token** under the LLaMA tokenizer → both options got an identical logit and every belief was
  exactly 0.5/0.5, *even under zero-ablation*. Once fixed, LLaVA turned out to answer
  **"Left"/"Right"** (capitalised, ~all the mass) while the lowercase forms sit at p ≈ 2e-5 —
  so the readout was measuring the far tail of the distribution. Now marginalised over surface
  forms, with disjointness asserted.
