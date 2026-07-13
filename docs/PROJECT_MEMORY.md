# Project Memory — Kaho's VSR Research (last updated 2026-07-08)

*Orientation file for future sessions. Read this first, then `research_proposal_spatial_binding.md` (the plan) and `VSR_niches_critical_deep_read.md` (the literature analysis).*

## Who / context
- Kaho: master's student (also covering undergrad research continuity), CV/VLM/spatial reasoning focus; also interested in image generation and medical AI. Has a Notion paper database and paper-analysis skills (paper-deep-dive-notion, research-reading, research-paper-summarizer).
- Compute: lab A100 cluster. Video-scale work deliberately deferred (GPU cost).
- Private goal: CVPR 2027 (abstract deadline Nov 15, 2026 — ~18 weeks from July 8). **Deliberately omitted from the advisor-facing deck**; the pptx speaks in phases, not deadlines.
- Style preferences: concise and direct; Traditional Chinese whenever Chinese is requested; enjoys mechanistic interpretability but wants papers that also "make or improve" (Type-2: diagnose → repair), not interp-only.
- Tooling: **uses `uv` for Python** — all project setup should be uv-based (pyproject.toml, uv.lock, `uv run`), not pip/conda.
- Infra: lab server via SSH; **shared machine, no scheduler** (informal GPU coordination, no Slurm); **no container runtime installed** (could be added — prefer Apptainer over Docker if needed); OK to keep everything on the server. Not familiar with rendering tools — willing to learn; keep rendering-side complexity low.

## The project (settled)
- **Core hypothesis — binding bottleneck:** metric spatial info (ordinal depth, distance ratios) survives in VLM visual tokens but is destroyed at the vision→text binding step (coarse rank-3 channel per Kang et al.); qualitative survives coarse binding, metric cannot.
- Positioning: DepthCues (encoders have cues) + Ill-Posed by Design (behavior ignores geometry) establish the endpoints; Kang 2601.12626 and Wang & Gao 2605.07148 constrain the middle. We localize where metric dies. NOT claiming "present but unverbalized" — Wang & Gao contradict that raw form.
- Paper 1 design: ordinal/ratio core (absolute secondary, prior-contaminated per ReVSI); factorial synthetic stimuli decorrelating depth × vertical position × size, congruent + conflict (cue integration: fusion vs winner-take-all); four-site probing grid (encoder → projector → LM visual tokens → bound text tokens); probe-vs-verbalization with rank correlations + calibrated baseline + oracle-text; anchor localization experiment; continuous metric-ID injection with dose-response; binding-layer LoRA vs brute-force SFT at matched data; validation via complex benchmarks decomposed by primitive (VSI-Bench, MindCube, CausalSpatial) + task-level oracle injection.
- Models: 4–6 spanning encoder design — LLaVA-1.5/1.6 (CLIP), Qwen2-VL/2.5-VL (M-RoPE), InternVL / Gemma-3 (SigLIP).
- Simple tasks for mechanism; complex benchmarks only as validation layer (composition-interp = future work).

## Research arc (updated 2026-07-09)
- **Paper 2 — leading candidate (Kaho's idea): the spatial-method mechanistic audit.** How do existing spatial-enhancement methods (data-SFT, RL-tuned, inference-time scaffolds like scene-graph/depth-input/SoM) change internal behavior? Four-site probe decomposition per method: representation improved / binding improved / prior installed at readout. Ties to ReVSI's behavioral debunking (fine-tunes lose gains under corrected eval); scaffold analysis would mechanistically explain the C-niche convergent fact (verbalized cues barely help). Reuses ~90% of Paper 1 infra. **Verified 2026-07-09:** 2511.11440 deep-read — LM-layers × final-question-token probes on their own synthetic-SFT only, single toy task; comparative audit / site decomposition / scaffolds all NOT covered → idea is open, cite and differentiate. Checkpoint audit set confirmed public with matched bases: SpaceR + ViLaSR (both on Qwen2.5-VL-7B-Instruct); SpatialLadder + SpaceQwen/SpaceOm + Spatial-MLLM (all on Qwen2.5-VL-3B-Instruct); VLM-3R vs LLaVA-Video-7B-Qwen2 optional second arch case. Skip Cambrian-S (no untouched base), SVQA-R1/SpatialVLM (no checkpoints).
- **Paper 3 / PhD-start — generation:** understanding↔generation gap in unified models — probe transfer across pathways; Janus-Pro (decoupled control), Emu3.5 (shared AR), BAGEL (hybrid). Demoted from Paper 2 on 2026-07-09 (higher risk, slower; more fundamental — keep for PhD arc).
- **PhD direction:** spatial state over time/simulation — multi-image guaranteed-evidence memory protocol, KV-cache probing, hypothetical-state probing (CausalSpatial-level). Video deferred.
- **Method harvest** (byproduct, not goal): continuous causal mediation, probe-transfer measure, hypothetical-state probing.

## Dataset usage rules (set at M2 — SCIENTIFIC constraints, enforced in code; see plan §2.5)
- **Split/frame-budget is an experiment parameter, never a loader default.** MindCube defaults to `tinybench` (1,050 vs the full ~21k) and ReVSI to the **32-frame** budget — dev-speed conveniences only. Any *reported* result must set them explicitly in the experiment config. Both adapters now log the value (flagging when it's a default) and record it per item (`meta.split`, `meta.frame_budget`). **ReVSI's entire thesis is that conclusions change with the frame budget — the paper should report 2–3 budgets (16/32/64), not one.** A single-budget result is provisional.
- **DepthCues is PROBE-ONLY: it must never appear in a behavioral claim.** No task text exists in it; its "questions" are OURS and its "answers" are raw regression/binary labels. Scoring a model's verbalized accuracy on a question we invented measures nothing. `datasets/base.py` classifies every dataset (`NATIVE_QA` / `NATIVE_TASK` / `PROBE_ONLY`) and `assert_behavioral_safe()` raises on PROBE_ONLY — **call it at the top of every eval/scoring entrypoint (M5, M7).**
- **Important distinction the `meta.synthesized_question` flag is too blunt to make: What'sUp IS behavioral-safe.** Its *task* and answer key are native (choose the correct caption of four); only our prompt *wording* is synthesized — it is the qualitative positive control. DepthCues has no native task at all. Conflating the two would either wrongly bar What'sUp or wrongly admit DepthCues.

## M4 design constraints (inherited from M1 — read before building the conflict conditions)
- **⚠ `fixed_retinal_size` condition must NOT define "retinal size" as mask AREA.** A cube's mask area varies **±11% with pose/depth** (a nearer cube shows more of its faces; measured cube-as-far ∈ [139863, 171495] vs cube-as-near ∈ [148480, 182933] for `area×depth²`). So "equal retinal area" is not well-defined without also fixing pose. Two acceptable routes: **(a) define retinal size as mask HEIGHT** (`retinal_size_px`, which the M1 calibration equalises across shapes to `height×depth` ≈ 407 — pose-stable), or **(b) control pose explicitly (fixed yaw per object)** and only then use area. Do not silently mix the two.
- The `size_condition` factor owns **independent per-object size jitter**; the congruent condition deliberately gives both objects of a pair ONE shared multiplier (independent jitter is precisely how you invert the retinal cue on purpose).
- `cue_constants` in `configs/stimuli_v0_congruent.yaml` records the measured fill factors, `height×depth`, `area×depth²` (split by near/far role) and per-pairing required depth ratios — the numbers a conflict design needs to invert a cue by a *known* amount.
- Anything M4 adds (new primitive, new pose freedom, per-object size jitter) **invalidates the M1 calibration and the 1.158 area threshold** — recalibrate (`scripts/calibrate_sizes.py`) and re-derive the thresholds from worst-case constants.

## 🚦 M3 — THE GO-GATE (2026-07-14). Full report: `reports/m3_reproduction.md`

**M3.1 (Kang) = PASS on the mechanism. M3.2 (Wang & Gao) = FAIL, and the cause is OUR STIMULI.**
Nothing was tuned to make either pass.

### M3.1 — the project's core premise SURVIVES
Reimplemented from the paper (their repo has no license). 640 two-object 4×4-grid scenes, COCO
cutouts (deviation: they used Objaverse), on LLaVA-1.5-7B + Qwen2.5-VL-7B.
- **The mirror-swap patching profile reproduces EXACTLY on both models: image patches early →
  object-word tokens middle → text late.** This is Kang's central localization claim and it comes
  out crisply (LLaVA object-word peaks at 0.31–0.34 on L12–14; Qwen at L16).
- **rank-3 R² = 0.87 (LLaVA) / 0.84 (Qwen)** vs the paper's ≥0.85. Spatial IDs really are a
  low-rank position code.
- **Steering is dramatically selective: 31.3% belief-swap vs 0.0% norm-matched noise** (Qwen, at
  the paper's α=5); dose-response is monotone and saturating (10→23→31→43% as α goes 1→10) while
  **noise never moves at any dose**.
- **What does NOT reproduce: the absolute swap rate** (19–31%, not their 64.4%). But our noise
  floor is ~0%, not their 29.5% — so the paper's own summary statistic, **above-chance influence**,
  matches or beats theirs (+31.3 pts at α=5, **+43.3 pts** at peak, vs their +34.9). Our models are
  simply far more certain here (95–98% task accuracy, mean confidence 0.89), so a random nudge
  essentially never flips a belief. Report the mechanism; do not claim the magnitudes.

### 🔴 M3.2 — THE FINDING THAT MATTERS: v0 CANNOT CARRY THE METRIC SCIENCE
Mask-pooled object tokens at LM layers of Qwen2.5-VL-7B + InternVL3-8B (their exact models) on our
v0 congruent set → **x R² = 0.997, z R² = 0.990 at EVERY layer**, shape/colour = 1.000, all
shuffled controls exactly at chance. Wang & Gao get **x = −0.09, z = +0.28**. We do not reproduce
"semantics ≫ metric" because **there is no difficulty gradient in our stimuli at all.**
**The probes are fine (controls at chance; token registration verified to 0.019 grid units). The
stimuli are the problem:**
1. **`x` has exactly 2 unique values (±0.7)** — it is a binary SIDE label, not a metric coordinate.
   And mask-pooling picks its tokens BY the object's image position, so "decode x" is answered by
   *which tokens were pooled*. R²=0.997 measures the pooling, not the model.
2. **`z` is 86% predictable from apparent size alone** (r=0.93 for `size_m/retinal_px` vs depth) —
   because "congruent" *means* every depth cue agrees. This is the exact monocular-depth shortcut
   Wang & Gao flag and discount.
3. Two primitives on a bare plane, fixed camera: too few degrees of freedom for "modest
   decodability" to even be expressible.
**→ M4 MUST: make `lateral_offset` continuous; treat `size_condition` (independent per-object size
jitter) as LOAD-BEARING (it is what breaks the size↔depth shortcut); add camera/background/
distractor variation.** See IMPLEMENTATION_PLAN §2.5(d).

### ⚠ METHOD CONSTRAINT that outlives the stimulus fix
**Mask-pooling from position-indexed visual tokens LEAKS POSITION BY CONSTRUCTION** — the pooled
vector averages tokens *at the object's image location*, and those tokens carry positional
information. A high x/z R² is therefore NOT by itself evidence of a metric representation. Every
Phase-2 mask-pooled probe needs a **position-leak control** (regress out the pooled tokens' grid
coordinates), plus the strip/all-token variant (already cached) and Wang & Gao's cross-scene
residualization.

### Bugs in OUR OWN M3 code, all caught by writing the invariant BEFORE trusting the number
- Scene generator systematically tied each object to a cell subset (TV=0.45) → the spatial-ID
  derivation would have been **circular**. Then the pairing dropped its unpairable tail
  non-uniformly → balance re-broken (TV=0.030). Now every object is in every cell exactly twice,
  TV = 0.000.
- **~1/4 of scenes put both objects in the SAME COLUMN**, where "left or right" has no ground truth
  — and the code confidently labelled them "right" (answer key skewed 253/640).
- **The belief readout was measuring nothing.** `" left"`/`" right"` share their FIRST TOKEN (the
  LLaMA whitespace token 29871), so both options got an identical logit and every belief came out
  exactly 0.5/0.5 — *even under zero-ablation*. Once fixed, LLaVA turned out to answer
  **"Left"/"Right"** (capitalised, ~all the mass) while lowercase sits at p≈2e-5: the readout was
  reading the far TAIL of the distribution. Now marginalised over surface forms, disjointness
  asserted. **Lesson: verify that an intervention MOVES the quantity you are measuring before you
  trust a null result** — a 0% steering effect looked like a real negative for an hour.

## SECOND retro-audit — all of M0/M1/M2 (2026-07-14, at the M3 gate). Full report: `reports/m0_m2_audit.md`

**Verdict: the DATA is clean; the CODE and the DOCS were not.** Every count, id, media file and
answer key in M1/M2 survives a full scan (all six adapters load exactly their source counts,
0 dropped, 0 duplicate ids, 0 missing files, 0 unscoreable MCQs; M1's geometry re-derives to
**0.0 error** over 1000 objects using an independently re-implemented camera; determinism
re-verified by byte-compare, and the documented residual claim is honest). But **six real code
bugs survived M2's closure, two of them producing wrong data**, and five documented constants
were false. All silent. All fixed this session, each with an invariant test.

- **CausalSpatial's `not_sure` column is a LIE** (HIGH): constant `'C'` for all 189 occlusion
  rows, but 54 of those have four *semantic* options and no abstain — and **on 11, C is the GOLD
  answer**. A scorer honouring the adapter's own contract would have discarded the correct
  answer. → now derived from the option TEXT. *Second* upstream field in this one dataset to be
  false (after the "unique" id). Hence the new plan §2.5(c): **an upstream field is a hypothesis.**
- **MindCube silently fell back to tinybench** (HIGH): `load(split="val")` returned 1,050
  tinybench items **stamped `meta.split="val"`** — the wrong population under the right label,
  inverting the very §2.5 rule the previous commit claimed to enforce. → unknown split raises;
  split is now settable from config (it wasn't, unlike ReVSI's budget).
- **ReVSI `frame_budget='all'` was dead** (`int('all')`): the parquet's `num_frames` is a budget
  LABEL, not a count. → clip length is now derived from the video. All four budgets load
  (16: 4,568 · 32: 6,158 · 64: 6,616 · all: 6,808).
- **`decode_frames` silently returned fewer frames than requested** → now raises.
- **What'sUp's gold answer is at position A in 100% of items** (the upstream convention is real —
  verified from the filename-encoded relation, 718/718). Served in that order, an A-biased model
  scores 100% and **the qualitative positive control passes for the wrong reason.** → options are
  now shuffled (seeded) with the true `answer_index` recorded.
- **The M0 config guard added by the FIRST retro-audit still had two holes**: `DATA_ROOT=""`
  (empty but set) resolved to the absolute path `/external`, and an unbraced `$VAR` stayed
  literal. The exact bug it was written to prevent, twice over. → checks the vars a config
  *references*, before expansion destroys the evidence.
- **The GPU guard's "foreign compute process" half was never implemented** — `ComputeApp` was
  declared with zero call sites, so the guard was memory-threshold-only and a colleague's job
  that hadn't yet allocated 1 GiB was invisible. → implemented; it immediately caught a real
  foreign process on GPU 1 during testing. **Load-bearing: M3 is the first GPU milestone.**
- **`seed_everything` set `PYTHONHASHSEED` after interpreter start** — a no-op. It looked seeded
  and wasn't. → removed, with `torch.use_deterministic_algorithms` added for M4.
- **`scripts/validate_stimuli.py` never opened a single mask or image** — it validated the JSON
  against itself, and its geometry check called the same function that *generated* the
  annotations. It would have reported ALL GREEN under a missing or overwritten PNG. → now opens
  every artefact, recomputes bbox/height/area from the pixels, checks id-uniqueness, image
  content-duplication, frame-clipping, occlusion, and **reports margins, not just pass/fail**.
- **Docs recorded `depthcues = 4,373`** — which is precisely the *pre-fix, broken* count
  (19,235 − 14,862, the occlusion subset that silently vanished). The code and tests already had
  19,235. **The docs preserved the bug.** Also: disk is 23 GB not 20 GB (loading CV-Bench and
  CausalSpatial *materialises* their parquet images, roughly doubling both), and the git remote
  is **not** deferred — `origin` exists and `main` is pushed.

### 🔑 THE STIMULUS CONFOUND (the finding that actually threatened the science)
**Category was never balanced against the near/far depth role.** v0 came out sphere-near 148 /
far 182, cube-near 168 / far 147, so the best **shape-only constant strategy scored 55.1%** on
the 345 mixed-category pairs ("the cube is closer" won 59.6% of cube-vs-sphere pairs). In the
very set built to *decorrelate semantics from geometry*: a language-only model gets 55% free on
"which is closer?", and **a depth probe can read depth off object IDENTITY** — which is exactly
the confound Wang & Gao residualize out, and M3.2's expected result ("semantics ≫ metric, z
modest") is precisely the number it would inflate.
→ **Fixed by construction:** category and colour are now drawn as *ordered* `(near, far)` pairs
and **balanced**, so "X nearer than Y" and "Y nearer than X" are equally frequent for every
{X,Y}. Re-rendered. Shape-only strategy: **55.1% → 50.2%** (χ² p=0.997). `balanced_on` was only
covering `closer_object` and `near_depth_bin`; the lesson generalises — **balance every factor
against the ROLE it could predict, not just its own marginal.**

## Retro-audit of M0/M1 (done 2026-07-14, after M2's bugs raised the question "was the earlier work also silently broken?") — YES, IT WAS
- **Answer: four more bugs, all silent.** This is why CLAUDE.md now carries a "How to verify work" section. Every bug across M0–M2 had the same shape: **the pipeline ran green while producing wrong data**.
- **M1 — the DETERMINISM hard rule was being violated the whole time.** Re-rendering from an identical (config, seed) produced *different images every run*. Three causes: (a) Blender embeds `Date`/`RenderTime` into PNG `tEXt` chunks; (b) **OIDN denoising is non-deterministic** (thread scheduling perturbs ~0.01% of pixels by 1 LSB); (c) **Cycles adaptive sampling is non-deterministic** (per-pixel stopping depends on thread timing). All three now default OFF (`denoise: false`, `adaptive_sampling: false`, metadata stamping disabled); `samples` raised to 128 to compensate for losing the denoiser. Render cost 1.2 → 2.5 s/img (500 imgs ≈ 22 min).
- **The determinism guarantee, stated precisely (do not overclaim):** annotations and masks are **byte-identical** across runs; images are byte-identical for ~19/20, with an irreducible residual of **~1 pixel in 5.2 M differing by 1/255** — float-accumulation order in multithreaded Cycles. Single-threaded rendering would remove it but costs 50 s/img (≈7 h for 500 images; untenable for M4's 5–10k). Scientifically nil (far below any model's preprocessing noise), but it means content-hash provenance on images is unreliable — hash the annotations, not the pixels.
- **M0 — config loader silently swallowed a missing env var.** `os.path.expandvars` leaves an unknown `${DATA_ROOT}` as literal text, so a forgotten `export` would have written the entire dataset into a directory named `${DATA_ROOT}` while every check still passed. `load_config` now raises on unresolved vars (`strict_env=True`).
- **M0 — CSV logger silently destroyed previous runs.** Reusing a run dir overwrote `metrics.csv` with no append and no warning; with M5's probing grid writing dozens of runs, a repeated `run_name` would have quietly eaten results. Now raises unless `tracking.overwrite: true`.
- Nothing else in M0/M1 was found broken: GPU guard, seeding, schema round-trips, geometry projection (<2 px), mask/annotation integrity all re-verified.

## Hard-won lessons (do not relearn)
- **Derive safety thresholds from WORST-CASE constants, never from means.** The area-congruence threshold computed from mean constants was 1.096; the true worst case (splitting the constant by near/far role, since perspective differs) was **1.158**. The mean-based floor (1.12) passed validation while leaving a 0.6% margin — i.e. it was still holding by luck. Any "safe threshold" for a rendered quantity must come from the extremes of its measured distribution.
- **Verify a guarantee empirically AFTER applying it — passing ≠ guaranteed.** Both the 1.074 (no floor) and 1.12 (mean-based floor) sets reported `area_congruence 0/500`. The check passed both times; the *margin* (worst-case near/far area ratio) was 1.006 both times, which is what revealed the floor had done nothing. Always measure the margin, not just the pass/fail count — a green check on a contingent property tells you nothing about whether it will stay green under a different seed.
- **Never trust a rendered metric without an invariant check.** The colour-keyed mask silently bled into bounce-lit floor for the entire first version of the generator (see the ID-pass bug above); it was caught only by asking "is a sphere as tall as it is wide?" Validate the metric itself, not just that the pipeline ran.
- **Field velocity is extreme**: the literature analysis was materially revised twice in one day by newly-found papers (Kang et al., then Wang & Gao / Ill-Posed by Design — the latter two found only after Kaho pushed to search newer work). **Rule: every specific design claim gets a verification search before being asserted or written.** Biweekly citation watch on 2601.12626, 2605.07148, 2606.24335, 2411.17385 (offered as scheduled task; not yet set up).
- Superseded ideas (don't re-propose): qualitative-direction steering, ordering-probe amplification (Kang/Dual Mechanisms territory); behavioral-only cue decomposition for size (Ill-Posed); new static benchmarks; "present but unverbalized" as stated.
- Must-reads before design freeze: Attention in Space (2603.20662), Why Far Looks Up (2605.30161), full Ill-Posed §6.6 + limitations; Echo-Memory (2606.09803) before any memory work.
- Kang reproduction is load-bearing (code: github.com/Raphoo/linear-mech-vlms).
- **Dual Mechanisms v2 (2603.22278v2, Jun 2026, deep-read 2026-07-09):** retitled to "spatial VARIABLE BINDING" — terminology collision risk; define our claim explicitly as the *vision→text-token binding step* (Kang-style), cite them as the ordinal counterpart. Our territory intact (no metric, no site decomposition, no text-token sites, no probe-vs-verbalization in v2). Adopted their standards into IMPLEMENTATION_PLAN M5: strip-level + object-pooled probing (their negative control shows background tokens carry signal), two-ordering MCQ protocol, random-direction nulls, Probe* reporting. Their code/data: spatial.baulab.info.

## Deliverables in outputs folder
- `research_proposal_spatial_binding.md` — full proposal (advisor asks: plan endorsement + cluster access, model sign-off, human-baseline/ethics decision, external reader).
- `VSR_niches_critical_deep_read.md` — 15+ paper critical analysis with revision banners per niche.
- `research_proposal_spatial_binding.pptx` — 11-slide advisor deck (phase-framed, no conference dates).

## Current state / next step
- **As of 2026-07-14: M2 COMPLETE** (external dataset adapters), **re-audited and fixed at the M3 gate** (see the second retro-audit above). Six adapters under `src/sbind/datasets/` behind one interface `load(name, config) -> Iterable[Item]`; `scripts/{download_dataset,dataset_contact_sheet}.py`; `configs/datasets.yaml`. **23 GB** on disk under `$DATA_ROOT/external/` (7.8 TB free — non-issue; note CV-Bench and CausalSpatial *grow on first load*, since their images are extracted from parquet). **111 tests pass**; without `$DATA_ROOT` exported they SKIP rather than error (they used to error — the "green on a laptop" claim was false).
  **Item counts, verified by full scan against the source files:** cvbench 2,638 · revsi 6,158 (32-frame; 4,568/6,616/6,808 at 16/64/all) · **depthcues 19,235 (test)** · causalspatial 1,541 · mindcube 1,050 (tinybench; 21,154 test, 10,000 train) · whatsup 820.
  ⚠ **The old docs said `depthcues 4373` — that was the PRE-FIX broken count** (19,235 − 14,862, the occlusion subset that had silently vanished). The code and tests always had 19,235; only the docs preserved the bug. *Lesson: when you fix a bug, fix the number the docs recorded too — a stale doc re-introduces a corrected bug into the next session's assumptions.*
- **Interface decision (M2): `images` is a LIST, not a singular `image`.** ReVSI is video and MindCube is multi-view (4 images/item), so the plan's singular `image` field could not express half the benchmarks. Items also carry a stable origin-carrying `id` (`<dataset>/<original index>`) so eval results always join back to source items, and video items carry `video` + `frame_indices` with **lazy** PyAV decode (nothing materialised to disk).
- **Raw VSI-Bench skipped:** ReVSI ships its OWN `video.zip` + corrected annotations, so the raw benchmark would add 5.7 GB for nothing. (This was the open question at M2 planning; resolved by inspecting the hub file list.)
- **⚠ Per-dataset gotchas that cost time — do not relearn:**
  - **What'sUp is not on HF** (Google Drive). Its upstream loader file ALSO contains gdown ids for VG_Relation / VG_Attribution — **those are inherited ARO datasets, not What'sUp**. I initially grabbed those and downloaded 23,937 Visual Genome records instead of the 412 controlled photos. The correct ids are in the `Controlled_Images` class: subset **A = real photos**, subset **B = CLEVR renders**, each with its own json + tarball. Upstream convention (confirmed in their README): **the first caption option is always the correct one.**
  - **CausalSpatial has TWO schemas.** The four simulation subsets (collision/physics/compatibility/occlusion) have NO `options` column — the choices are inline in the question text ("A. Yes; B. No; C. Not Sure.") and `answer` is a LETTER, with a `not_sure` column naming an **abstain** option (a scorer must not count it as a wrong answer). `realworld` instead has an explicit `options` list and a TEXT answer. The adapter normalises both to `meta.{options,answer_letter,answer_text}`.
  - **DepthCues is NOT a VQA benchmark.** It ships raw probe targets (image + red/green mask pair + label), designed for linear probes on encoder features. There is no question text: ours are **synthesized** (`meta.synthesized_question`) and `answer` is just the label stringified — **consumers must use `meta.label`**. Each of the five subsets has a different schema and image directory. Its **Perspective** subset is annotations-only (the hub zip is literally empty); images live at the original vanishing-point project. Data terms: per-source, non-commercial research use (an `HLW_LICENSE.txt` ships with it); the CODE is MIT.
  - **CV-Bench's 3D `Depth` task is our primitive** ("which object is closer, the one in the red box or the blue box?") and the boxes are **drawn into the image**, so the annotation↔image join is visually verifiable — which is exactly what the contact-sheet eyeball check confirmed.
- **M3 IN PROGRESS (started 2026-07-14).** Prerequisites done this session: all six M2 bugs fixed + the stimulus confound removed and the set re-rendered; **COCO downloaded in full** (train2017 19.3 G + val2017 + annotations — the full set was chosen so Kang's spatial-ID auxiliary-loss result stays reproducible later); **three models cached** (`llava-hf/llava-1.5-7b-hf`, `Qwen/Qwen2.5-VL-7B-Instruct`, `OpenGVLab/InternVL3-8B` — 44 GB in `$HF_HOME`).
  - **M3.1 = Kang reproduction** (LLaVA-1.5-7B + Qwen2.5-VL-7B). Targets from the paper: steering belief-swap **64.4–64.6% vs 29.5%** norm-matched noise; spatial IDs ≈ **rank-3** transform of the encoder's positional basis (R² ≥ 0.85); mirror-swap patching profile = image patches early, object-word tokens middle, text late.
  - **M3.2 = Wang & Gao pattern reproduction** on our v0 stimuli, on **Qwen2.5-VL-7B + InternVL3-8B** (their exact two models). Their numbers: x R² = **−0.09**, z R² = **+0.28**, pairwise-distance RSA ρ ≈ **0.01**, shape R² = **1.00**. Pass bar is *pattern* match: semantics ≫ metric; x ≈ chance; z modest.
  - COCO also unblocks What'sUp's deferred COCO/GQA-spatial subsets (TODO still open in the adapter).
  - ⚠ M3 front-loads a minimal `extract/` (HF-VLM wrapper + named hook sites + mask-pooling), which is formally M4's deliverable — build it to be EXTENDED by M4, not thrown away.

- **As of 2026-07-10: M1 COMPLETE** (rendering spike + minimal scene generator). **RENDERER DECISION = bpy (Blender 5.0 Python module), rendered headless with Cycles on CPU.** Rationale: `uv add bpy` pulled a 357 MB prebuilt wheel (`bpy==5.0.1`) — no compile, no system Blender, no Apptainer; imports + renders headless with no display; ~1.3 s/img CPU @512² so stimulus generation never touches the shared GPUs (Cycles OPTIX/CUDA also detect all 8 A6000s if ever needed). Apptainer/pyrender fallbacks NOT needed. Built `src/sbind/stimuli/{geometry,scene_spec,sampler,render_bpy}.py`, `scripts/{render_stimuli,contact_sheet}.py`, `configs/stimuli_v0_congruent.yaml`; rendered 500-image congruent-only set + contact-sheet PDF. 44 tests pass (28 M0 + 16 M1), incl. render-consistency: rendered mask centroids match K[R|t] projection <2 px.
- **numpy pinned <2.0 project-wide (M1 decision):** bpy requires numpy<2; verified torch 2.13 + the analysis stack all run fine under numpy 1.26.4 (scipy floor is exactly 1.26.4; torch↔numpy ABI interop + CUDA confirmed). So ALL extras (stimuli/analysis/extract) coexist in ONE env — the plan's anticipated "isolate stimuli env" is NOT needed. If a future dep hard-requires numpy≥2, revisit via uv conflicting-extras.
- **bpy 5.0 API notes (hard-won, don't relearn):** pixel filter moved to `scene.cycles.filter_width` + `scene.cycles.pixel_filter_type` (NOT `render.filter_width`); `read_factory_settings(use_empty=True)` yields `scene.world is None` (create a world before setting the sky); view transforms include 'Standard'/'Raw' (used 'Standard' for beauty, 'Raw' + 1-sample + near-zero BOX filter for the flat-emission ID pass so per-object masks are crisp & colour-management-immune). `World/Material.use_nodes` deprecation-warns (removal in Blender 6.0) — harmless now, revisit if we bump bpy.
- **v0 generator params (revised 2026-07-10 after review):** camera pulled in to (0,−2.5,1.4) and objects enlarged via the per-category calibration below → **retinal median 98 px** (p10 71, p90 147; 74% in the 60–120 band), up from ~30 px. Depth is now **continuous** (`depth_jitter: ±0.15` on both the near-bin centre and the gap, floored by `min_gap: 0.3`) → 500/500 unique depths, so ratio/absolute regression targets no longer collapse onto 5 discrete values. Sampler enforces **no identical pairs** (never same category AND colour) → 0/500, so "which object is closer?" is always answerable. Depth ratio far/near spans 1.08–1.58 (median 1.28).
- **🐛 ID-PASS BOUNCE BUG (found & fixed 2026-07-10 — the important lesson):** per-object masks come from a flat-emission ID render, but the ground kept its *diffuse* material and the sun stayed on, so an emissive red object **bounced red light onto the floor beneath it**; that lit floor fell inside the ID colour-match tolerance and the mask **bled downward**, silently inflating every `bbox_px` bottom and `retinal_size_px`. Caught only by a size-sweep sanity check: a sphere rendered 66 px WIDE but 103 px TALL — impossible. Fix: in the ID pass the ground also becomes **black emission**, all **lights are set to 0**, and **`max_bounces = 0`**. After the fix a sphere renders exactly as tall as it is wide and height is exactly linear in `size_m` (matches `f·size/depth` to ±1 px). **Lesson: never trust a colour-keyed mask without an invariant check — validate the metric itself (a sphere is as tall as it is wide), not just that the pipeline ran.** Any pre-fix retinal/bbox numbers in this doc's history are inflated and were superseded.
- **🔑 PRINCIPLE — "congruent means congruent BY CONSTRUCTION, for every measured cue" (decided 2026-07-10):** a congruent stimulus set must not rely on the seed's luck for any cue it records. Applied to the apparent-size cues: **you cannot equalise height and area simultaneously across shapes** (silhouettes fill their bboxes differently — cube 0.939, cylinder 0.908, sphere 0.784 — so equalising one leaves the other shape-dependent). We calibrate on HEIGHT (the quantity `retinal_size_px` records) and then make AREA structural via a **uniform minimum far/near depth ratio: `min_depth_ratio: 1.18`**. Both height- and area-congruence are now **hard validation checks** (any violation = construction bug).
- **⚠ METHOD LESSON — derive safety thresholds from WORST-CASE constants, never means.** First attempt set `min_depth_ratio: 1.12` from a *mean*-based area threshold of 1.096. It was wrong: a cube's area constant varies **±11% with pose/depth** (a nearer cube shows more of its faces), which the mean hides. Splitting the area constant by NEAR/FAR role gives the true requirement — **near=cylinder/far=cube needs 1.158**, near=sphere/far=cube 1.153 — so 1.12 left a 0.6% worst-case margin and area-congruence was *still* holding only by luck. Corrected to **1.18** (1.158 + ~2% headroom). Generalise: any "safe threshold" for a rendered quantity must be computed from the extremes of its measured distribution, not its mean.
- **Why a UNIFORM ratio floor, not per-pairing thresholds:** per-pairing limits would be less restrictive (near=cube/far=sphere needs no constraint at all, 0.947) but would make **shape predict the depth-ratio distribution** — a confound a probe could exploit. A uniform floor keeps depth ratio independent of the shape pairing, at the cost of some small-ratio (hard ordinal) cases.
- **Cue constants (measured, in `configs/stimuli_v0_congruent.yaml` → `cue_constants`) — reuse for M4 conflict designs**, which must invert a cue on purpose by a known amount: fill factors {cube .939, cyl .908, sphere .784}; `height×depth` {cube 409.3, cyl 410.3, sphere 405.3} (equalised → height congruence structural); `area×depth²` split by role, e.g. cube-as-far ∈ [139863, 171495] vs sphere-as-near ∈ [128932, 135860] (NOT equalised → needs the ratio floor); per-pairing required ratios recorded in the config.
- **Retinal-size calibration (2026-07-10):** a cube/cylinder subtend ~1.27× a sphere's pixel-height at equal `size_m` (silhouette reaches the diagonal, not the diameter), which let a FAR cube out-measure a NEAR sphere and invert the size cue. `scripts/calibrate_sizes.py` now measures each primitive's rendered mask height empirically (the *same* metric `retinal_size_px` records — not a closed form) and solves per-category `size_m` for a target pixel-height, iterating to convergence → **all three shapes render 90.0 px at the reference depth (spread 0.00 px)**. Calibrated sizes live in `configs/size_calibration.yaml` (cube 0.666, sphere 0.809, cylinder 0.666 m). **Consequence to remember: physical size is now a deterministic function of shape** — a probe could in principle read `size_m` off the category. The shared per-image `size_multipliers` factor adds physical-size variance to partially decorrelate this; revisit if an absolute-size probe looks suspiciously easy.
- **Centre vs surface depth (2026-07-10):** `depth_m` is the object CENTRE depth (the probes' regression target); `nearest_surface_m` = centre depth − half-extent along the viewing axis (what the bbox bottom and a human viewer actually track) — verbalized QA uses it. `pair_relations` carries both `ordinal_depth` (centre) and `ordinal_depth_surface` (surface). The sampler's `unambiguous_ordinal` constraint forces the two to agree by requiring the centre gap to exceed |h_near − h_far| + 0.15 m. **Measured: the two orderings disagree on 0/500 even with the constraint OFF** — with a pair-shared size multiplier, `|h_near − h_far|` only reflects *shape* (≤~0.05 m) while the min centre gap is 0.34 m. The constraint is a guard that currently binds on 0 images; it becomes load-bearing as soon as per-object size varies independently (M4's `size_condition`).
- **Congruent condition = pair-shared size multiplier.** Both objects of a pair scale by ONE `size_multiplier`; independent per-object size jitter would let physical size invert the retinal cue, which is precisely the M4 conflict manipulation — so it belongs to the `size_condition` factor, not to a congruent set. Noted in the generator config.
- **v0 acceptance state (2026-07-10, after the calibration + bounce fix): ALL CHECKS GREEN** via `scripts/validate_stimuli.py` — geometry 0/1000, corrected bbox-bottom rule 0/500, **retinal congruence 0/500 violations (100%)**, centre/surface ordinal agreement 0/500 disagreements, ratio 0/500, identical pairs 0/500, pair-shared size multiplier 0/500, masks 0/1000, surface sanity 0/1000. Answer key balanced 250/250 on BOTH centre and surface ordinals. Retinal median 98 px; depth ratio 1.07–1.61; 500/500 unique depths. (Historical note: an earlier "430/500 retinal congruence" figure was measured under the ID-pass bounce bug and is void.)
- **Geometry conventions frozen:** stored (K,R,t) are OpenCV-style (camera looks +Z, +X right, +Y down, pixel origin top-left); `depth_m` = CV-frame z; Blender camera built from the same look-at so projection matches render. `elevation_px` = v-pixel of the projected object centre; `retinal_size_px` = mask pixel-height; masks via flat-colour ID pass (≤6 objects palette).
- **As of 2026-07-10: M0 COMPLETE** (repo skeleton + infra utilities). On server plant-ai06. `uv run pytest` → 28 passed; `uv sync --extra analysis` and `--extra extract` both work; torch 2.13.0+cu130 sees all 8 GPUs; GPU guard verified live (aborts on really-occupied GPU 5 @43 GB, claims free GPU 6 + sets CUDA_VISIBLE_DEVICES). Built: `pyproject.toml` (extras extract/analysis/stimuli/dev), `src/sbind/{stimuli,datasets,extract,probes,interventions,eval,utils}` + `schemas.py`, utils (`gpu` guard, `seeding`, `config` loader w/ ${VAR} expansion, `io` jsonl, `logging` CSV/wandb tracker), §3 schema dataclasses w/ round-trip tests, `configs/example.yaml`. uv.lock committed.
- **Environment interviewed & frozen (see CLAUDE.md):** `$DATA_ROOT=/data3/hugin/vsr` (data3 = 7.8 T free), `$HF_HOME=/data3/hugin/hf_home` (kept off the 1.5 T-free shared /home). Tracking = CSV default, wandb via config — login cached & verified 2026-07-10, entity `chaso-hosei-university` (user `chaso`), now wired into configs/example.yaml + CLAUDE.md; flip to wandb at M4/M5. Git remote still deferred (local-only) — CLAUDE.md "server is never the only copy" rule remains UNMET; add origin when convenient.
- **⚠ HARDWARE CORRECTION:** the plan's prose says "A100", but plant-ai06 is **8× RTX A6000, 48 GB each** (first-come, no scheduler, multi-GPU OK). Compute all memory budgets against 48 GB, not 80. Other servers (4090/2080) out of scope.
- **Decisions made in M0:** flash-attn deferred but pre-wired via `[tool.uv] no-build-isolation-package` (models run on eager/sdpa; don't add until a checkpoint benefits). Stimuli extra holds only renderer-agnostic deps (trimesh/pillow/imageio) — bpy-vs-pyrender still decided at M1.1. Schemas are stdlib dataclasses (no pydantic dep in core) so the package imports on a bare laptop. requires-python `>=3.11,<3.13` (3.11 floor for bpy).
- Next: **M2 — external dataset adapters** (What'sUp/CV-Bench/ReVSI/MindCube/CausalSpatial/DepthCues; skip Kang/SynSpat3D/MetricVQA). **Do not start unprompted.**
- Dataset availability verified 2026-07-08: What'sUp/CV-Bench/VSI-Bench/ReVSI/MindCube/CausalSpatial/DepthCues all released & ungated. Kang data is script-generated (repo has NO license — reimplement, never copy; same for pittisl/vlm-latent-shaping). SynSpat3D dataset NOT released. **Metric VQA (Ill-Posed) NOT released despite abstract claim** — recheck monthly.
- Open decisions: ~~bpy vs Apptainer vs pyrender~~ RESOLVED (bpy, M1.1); ~~wandb vs CSV~~ RESOLVED (CSV default, wandb wired, M0); human baseline yes/no (ethics timing) still open; biweekly lit-watch scheduled task not yet created.
