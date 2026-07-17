# Implementation Plan — Spatial Binding Bottleneck (for AI-assisted coding)

*Written 2026-07-09; stage reframing + M4.5 added 2026-07-15. Companion docs: `research_proposal_spatial_binding.md` (science), `VSR_niches_critical_deep_read.md` (literature), `vsr_landscape_v8.pptx` (19-paper landscape analysis), `PROJECT_MEMORY.md` (context). This document is the coding spec: hand milestones to a coding agent one at a time, in order. Acceptance criteria are the definition of done — do not move on until they pass.*

**Milestones vs stages.** The milestones below (M0…M7) are the *build order*. The **science** is
organized as dependency-gated **stages** — S1 (visible metric) → S1.5 (occlusion & the amodal probe)
→ S2 (method audit) → S3 (generation) → S4 (the unseen) — described in `PROJECT_MEMORY.md`. **There
are no "Paper 1 / Paper 2 / PhD" labels any more**: publications are snapshots of whichever stages
have defensible results at a deadline. Mapping: M1–M5 build S1 · **M4.5 = S1.5** · M6 = S1's
interventions · M7 = S2.

---

## 0. Ground rules for the coding agent

- **Python via `uv` only.** One repo, one `pyproject.toml`, committed `uv.lock`. Dependency groups: `extract` (torch, transformers, accelerate, pillow), `analysis` (scikit-learn, numpy, pandas, matplotlib, seaborn), `stimuli` (bpy or pyrender + trimesh, depending on M1 outcome), `dev` (pytest, ruff).
- **Config-driven everything.** Every experiment = one YAML in `configs/`. No hardcoded model names, layer indices, paths, or prompts in code. Same experiment on six models must be a config change.
- **Shared GPU server, no scheduler.** Every GPU script: (a) requires explicit `--gpu N`, sets `CUDA_VISIBLE_DEVICES` itself; (b) checks `nvidia-smi` for the target GPU at startup and aborts with a clear message if another user's process occupies it; (c) never grabs more than one GPU unless the config says so. Long jobs checkpoint per-batch and resume via `--resume`.
- **Determinism.** Every stimulus, split, and probe run seeded from config. Generated data must be exactly reproducible from config + seed.
- **Separation of GPU and CPU work.** GPU code lives only in `extract/` (and later `interventions/`). Probing/analysis reads cached features from disk; it must run on a laptop.
- **License caution.** The Kang repo (`Raphoo/linear-mech-vlms`) and Wang & Gao repo (`pittisl/vlm-latent-shaping`) have **no LICENSE** → all-rights-reserved by default. Read them to understand methods; **do not copy code** into our repo. Reimplement. What'sUp (MIT), DepthCues (MIT), CausalSpatial (MIT) are safe to adapt with attribution.
- **Tests:** each module ships minimal pytest coverage — schema round-trips, geometry math (projection of known 3D point → expected pixel), pooling correctness against a hand-computed example, probe pipeline on synthetic random data (must find signal planted in features, must NOT find signal in shuffled labels).

## 1. Directory & environment layout (server)

```
~/vsr/                        # git checkout (origin: GitHub — server is never the only copy)
  pyproject.toml  uv.lock
  configs/            # YAML experiment configs
  src/sbind/
    stimuli/          # scene specs → rendered images + annotations (M1, M4)
    datasets/         # loaders/adapters for external benchmarks (M2)
    extract/          # model loading, hooks, pooling, caching  [GPU]
    probes/           # ridge/logistic probes + controls        [CPU]
    interventions/    # steering, metric-ID injection           [GPU, M6+]
    eval/             # verbalized-answer collection, benchmark scoring
    utils/            # gpu guard, seeding, io, logging
  scripts/            # thin CLI entrypoints (uv run scripts/...)
  tests/
data (NOT in git):
  $DATA_ROOT/stimuli/<set_name>/{images/, annotations.jsonl, config.yaml}
  $DATA_ROOT/activations/<model>/<set_name>/...   # pooled features
  $DATA_ROOT/external/{whatsup,cvbench,vsibench,revsi,mindcube,causalspatial,depthcues,coco}/
  $HF_HOME → shared disk (models ≈ 100+ GB; check df -h first)
```

Experiment tracking: wandb (or CSV + git-hash logging if the lab has no wandb). Every run logs config, git hash, seed.

## 2. Data inventory (availability verified 2026-07-08; **downloaded + measured 2026-07-14 at M2**)

All under `$DATA_ROOT/external/<name>/`. Disk is **measured on disk after extraction**, and
includes the retained source archives (so it exceeds the hub's download size — e.g. ReVSI
is a 4.9 GB zip plus its extracted videos). **Total 23 GB against 7.8 TB free — a non-issue.**
⚠ **Loading a dataset MUTATES `$DATA_ROOT`:** CV-Bench and CausalSpatial embed their images in
parquet, so the adapters extract them to disk on first load — both roughly *double* on disk
(394 M → 782 M, 2.4 G → 4.8 G). The 20 GB figure once quoted here was measured before that.

| Dataset | Status | Adapter | Items loaded | Disk | Notes |
|---|---|---|---|---|---|
| What'sUp (`amitakamath/whatsup_vlms`) | ✅ MIT, Google Drive | `whatsup` | 820 | 313 M | Controlled A (412 real photos) + B (408 CLEVR renders). 4 caption options; the **first option is always correct** upstream (verified against the relation encoded in each image filename, 718/718 — not merely trusted). ⚠ Therefore the adapter **SHUFFLES the options** (seeded) and records the true `answer_index`: served in upstream order, an A-biased model scores 100% and our qualitative positive control passes for the wrong reason. **🎁 RELATION COUNTS (verified by full scan, 2026-07-15): A = `on` 103 / `under` 103 / `left_of` 103 / `right_of` 103. B = `left_of` 102 / `right_of` 102 / `in-front_of` 102 / `behind` 102 → B holds 204 FRONT/BEHIND items = our qualitative-DEPTH control** (see §2.5(f)). ⚠ COCO/GQA-spatial subsets deferred (need COCO/GQA corpora) |
| CV-Bench (`nyu-visionx/CV-Bench`) | ✅ Apache-2.0 | `cvbench` | 2,638 (2D 1,438 · **3D 1,200**) | 782 M | 2D (Count 788/Relation 650; COCO 805 + ADE20K 633) + 3D (**Depth 600 / Distance 600** — our ordinal primitive). Images embedded in parquet; target objects drawn as red/blue boxes. ⚠ **SOURCE MIX, measured in our copy (full scan, 2026-07-15): `Omni3D_Hypersim` 400 · `Omni3D_SUNRGBD` 400 · `Omni3D_nuScenes` 400** — exactly 200 per (task × source) → **33.3% photorealistic SYNTHETIC.** Report per-source; do not call it "real-image validation" unqualified. ⚠ The third source is **nuScenes, not ARKitScenes** (that's SpatialRGPT's Omni3D slice — different dataset). ⚠ **Zero absolute-metric items**; binary → 50% chance → two-ordering protocol mandatory |
| VSI-Bench (`nyu-visionx/VSI-Bench`) | ⛔ **SKIPPED** | — | — | 0 | ReVSI ships its own videos + corrected annotations, so the raw benchmark adds 5.7 GB for nothing |
| **ReVSI** (`3dlg-hcvc/ReVSI`) | ✅ Apache-2.0 | `revsi` | 16f: 4,568 · **32f: 6,158** · 64f: 6,616 · all: 6,808 | 9.1 G | **Video.** Pre-sampled per frame budget; frames decoded **lazily** via PyAV. Numeric + MCQ answers. ⚠ The parquet's `num_frames` column is a budget **label**, not a count (it is the literal string `'all'` in `all_frame/`) — the adapter derives the real clip length from the video itself |
| MindCube (`MLL-Lab/MindCube`) | ✅ MIT | `mindcube` | 1,050 (tinybench) · 21,154 (test) · 10,000 (train) | 1.3 G | **Multi-view** (4 images/item) — the dataset that forces the list-valued `images` interface. Options inline in the question. An unknown split now **raises**. 🔴 **REMOVED from the S1/M5 validation layer (2026-07-15, item-level inspection):** every item is multi-view perspective-taking under stated camera motion; **nothing reduces to a single-image primitive**, and its own eval excludes the `translation` setting. Re-scoped to a **cross-view integration contrast (S4-adjacent)**. Adapter stays; §2.5(a)'s split rule still governs any use |
| **SpatialRGPT-Bench** (`a8cheng/SpatialRGPT-Bench`) | ⚠ **NOT YET DOWNLOADED**; license murky | — | *claimed* 1,406 (val only) | — | **ADD WITH CAVEATS** — see §2.5(g). Supplies the **absolute-metric** type CV-Bench lacks (~375 inter-object distance items), on **Omni3D sensor GT**. ⚠ **Every count is the advisor's inspection, NOT verified locally — re-verify against the files before use** (rule 4) |
| CausalSpatial (`Mwxinnn/CausalSpatial`) | ✅ MIT | `causalspatial` | 1,541 | 4.8 G | ⚠ **Two schemas**: 4 sim subsets have options inline + letter answers + a `not_sure` column; `realworld` has an explicit options list + text answers. Adapter normalises both. ⚠⚠ **Neither the upstream `id` NOR the `not_sure` column can be trusted** — see §2.5(c) |
| DepthCues (`danier97/depthcues`) | ✅ per-source terms (non-commercial research); code MIT | `depthcues` | **19,235** (test) | 6.7 G | ⚠ **NOT a VQA benchmark** — raw probe targets (image + mask pair + label). Questions are SYNTHESIZED by us; consumers use `meta.label`. ⚠ Perspective subset skipped (its hub zip is empty — images live at the original vanishing-point project) |
| Kang synthetic grid + COCO-Spatial | ⚠ code-generated, not shipped | — | — | — | M3: run their data-engine recipe; COCO downloaded separately; **no license — reimplement, don't copy** |
| SynSpat3D (Wang & Gao) | ⚠ NOT released | — | — | — | regenerate equivalent stimuli ourselves (M1 generator covers this) |
| Metric VQA (Ill-Posed by Design) | ❌ NOT released | — | — | — | do not plan around it; re-check monthly |

## 2.5 Dataset usage rules (set at M2 — these are SCIENTIFIC constraints, not loader details)

**(a) Split / frame-budget is an experiment parameter, never a loader default.**
The adapters default to MindCube `tinybench` (1,050 items, vs the full ~21k) and ReVSI's
**32-frame** budget purely for development speed. Which split/budget a *reported result* uses
is a scientific choice and **must be stated explicitly in the experiment config** — a dev
default must never be inherited into a paper number by accident. Both adapters now LOG the
value at load (flagging when it is a default) and record it on every item
(`meta.split`, `meta.frame_budget`), so any result is traceable to it.
- **TODO (M5 validation layer):** ReVSI's whole point is that *conclusions change with the
  frame budget* — the paper should report **2–3 budgets (e.g. 16 / 32 / 64)**, not one. Treat
  a single-budget result as provisional.

**(b) DepthCues is PROBE-ONLY and must never appear in a behavioral claim.**
It ships raw probe targets (image + red/green mask pair + label) with **no task text**: its
"questions" are synthesized by us and its "answers" are regression/binary labels. A model's
"accuracy" on a question we invented is not a behavioral result about anything. Anything that
scores a **verbalized** answer must use only datasets with a native task.
- Enforced in code, not just documented: `datasets/base.py` classifies every dataset as
  `NATIVE_QA` / `NATIVE_TASK` / `PROBE_ONLY`, and `assert_behavioral_safe(name)` raises on
  PROBE_ONLY. **Call it at the top of every eval/scoring entrypoint (M5, M7).**
- Note the distinction `meta.synthesized_question` alone is too blunt to make: **What'sUp is
  behavioral-safe** — its *task* and answer key are native (pick the correct caption of four);
  only our prompt *wording* is synthesized. DepthCues has no native task at all.

**(c) An upstream field is a HYPOTHESIS, not a fact — verify it against the artefact.**
Added at M3's retro-audit, after the *second* upstream field in the same dataset turned out to
be a lie. Both were silent, and both would have corrupted a reported number:
- CausalSpatial's `id` is documented as a "unique sample identifier"; **192 physics rows share
  one string**. Keying the extracted images on it overwrote most of them (1,541 items → 949
  files). Now keyed on `(subset, shard, row index)`.
- CausalSpatial's `not_sure` column names the abstain option; it is the **constant `'C'` for all
  189 occlusion rows**, but 54 of those rows have four *semantic* options and no abstain at all
  — **and on 11 of them, C is the gold answer.** A scorer honouring the column would have
  discarded the correct answer as a non-answer. `meta.not_sure_letter` is now derived by
  checking the option TEXT; the raw claim survives as `meta.not_sure_upstream`.
- Similarly: ReVSI's `num_frames` is a budget label, not a count; What'sUp's "first option is
  correct" convention is TRUE but was verified from the filename-encoded relation rather than
  taken on faith (and, being true, forces an option shuffle — see the table).
**Rule: before keying, counting, or scoring on any upstream field, verify it against the data.
A cross-check is nearly always available for free** (option text vs the abstain letter; clip
length vs the declared frame count; filename vs the answer key).

**(d) ⚠⚠ THE v0 CONGRUENT SET CANNOT CARRY A METRIC-DECODABILITY CLAIM (found at M3.2, 2026-07-14).**
Probing mask-pooled object tokens on `stimuli/v0_congruent` gives **x R² = 0.997 and z R² = 0.990
at EVERY LM layer** of Qwen2.5-VL-7B and InternVL3-8B (shape and colour = 1.000; all
shuffled-label controls exactly at chance). Wang & Gao report **x = −0.09, z = +0.28**. We do not
get "semantics ≫ metric" because **we get no difficulty gradient at all**. The probes are fine —
the stimuli are not. Three measured defects, each of which M4 MUST fix:

1. **`x` is not a metric coordinate — it is a binary side label.** It takes **exactly 2 values
   (±0.7)**: the sampler puts the near object at ±`lateral_offset` and the far one at ∓ it. And
   mask-pooling *selects its tokens by the object's image position*, so "decode x" is answered by
   **which tokens were pooled**, before the model contributes anything. → **`lateral_offset` must
   become a continuous range.**
2. **`z` is over-determined.** Depth is **86% predictable from apparent size alone**
   (r = 0.93 between `depth_m` and `size_m / retinal_size_px`), because a congruent set is
   *defined* by every depth cue agreeing. This is exactly the monocular-depth shortcut Wang & Gao
   flag and discount. → **M4's `size_condition` (independent per-object size jitter) is
   LOAD-BEARING, not optional** — it is the thing that breaks the size↔depth shortcut.
3. **Too few degrees of freedom.** Two primitives on a bare plane, fixed camera. "Modest
   decodability" is not even expressible. → **add camera-pose jitter, backgrounds, distractors.**

**And a methodological constraint that outlives the stimulus fix: mask-pooling from
position-indexed visual tokens LEAKS POSITION BY CONSTRUCTION.** The pooled vector averages the
tokens *at the object's image location*, and those tokens carry positional information — so a
high x/z R² is not by itself evidence of a metric representation. **Every Phase-2 mask-pooled
probe must report a position-leak control** (regress out the pooled tokens' grid coordinates),
alongside the strip/all-token variant (already cached) and Wang & Gao's cross-scene
residualization of the semantic subspace.

**(e) A DATASET ENTERS AN EXPERIMENT ONLY AFTER ITEM-LEVEL INSPECTION** (added 2026-07-15).
Rows, templates, per-category counts, answer-format quirks — inspected against the actual files.
**Paper descriptions AND our own adapter counts are hypotheses.** This is (c) generalized from
*fields* to *datasets*, and it paid immediately: **What'sUp-B's 204 depth items** (a control we
already owned) and **MindCube's total unsuitability** were *both invisible* from the descriptions we
had been designing against.

**(f) THE VALIDATION LAYER IS A CLOSED, PREDECLARED SET (fixed 2026-07-15).**
The factorial battery is the **one primary identification instrument**; external data is **validation
only**. The list below is **closed — not extensible mid-project**, which is what stops it becoming a
fishing expedition. All single-image:

| Role | Instrument | Basis / caveat |
|---|---|---|
| qualitative-depth control | **What'sUp subset B** — 204 front/behind (verified: `in-front_of` 102, `behind` 102) | ⚠ **proxy-confounded**: per Kang, front/behind may be answered by the **vertical proxy** (tabletop front ≈ lower). **Behavioral** control only — *and the proxy story is itself an S1 probe experiment* |
| ordinal | **CV-Bench Depth (600) + Distance (600)** | 33.3% synthetic (Hypersim); report per-source. Zero absolute items. Two-ordering mandatory |
| ordinal + absolute, human-verified GT | **ReVSI-1F** (derived — spec below) | the workhorse |
| absolute, sensor GT | **SpatialRGPT-Bench distance slice** (~375 items) | the absolute type CV-Bench lacks — see (g) |
| consequence-level | **CausalSpatial collision (826) + occlusion (189)** ONLY | compatibility (99) + realworld (116) too small for per-category stats; physics (311) loads on **physics priors** → both are **non-target controls**. ⚠ Their own admission: sim **floor-strip spacing encodes depth perspective** — the cue is artificially legible; caveat cross-dataset comparisons |

**MindCube is NOT in it** (see §2 table). **Full-video ReVSI at 2–3 frame budgets is a *labeled
extension analysis*, not the core.**

**ReVSI question-type map** (13 types → primitives): 4 absolute-metric (distance m / size cm / room
m²), 2 ordinal (rel-distance closest/farthest, 4-way), 4 egocentric-qualitative (perspective-taking),
2 counting, 1 other (route). Numeric types scored by **Mean Relative Accuracy** (0.5–0.95 thresholds).
⚠ **The type mix VARIES by frame config** (16f drops room-size + route-planning) — fix the config per
analysis. ⚠ Every ReVSI item stacks **cross-frame memory on top of** the primitive → carry
**video/cross-frame as a nuisance covariate.**

**🆕 ReVSI-1F — derived single-frame instrument (decided 2026-07-15; code deliverable, NOT built yet).**
*Why:* ReVSI is video, and **cross-frame demand varies BY CATEGORY**, confounding primitive-difficulty
with memory-difficulty — and LLaVA-1.5 is not a video model at all.
*Derivation* (source file **verified present**: `$DATA_ROOT/external/revsi/metadata/obj_visibility.json`):
1. keep items where **all** `queried_object_ids` are co-visible in **≥1 frame**;
2. select the frame maximizing the **minimum** visible-pixel count across queried objects
   (tie-break: earliest frame; seeded; **the rule lives in config**);
3. emit `revsi_1f/` = original item id + chosen `frame_idx` + per-object visibility stats + primitive tag.
*Acceptance:* counts + contact sheet, **and ⚠ per-category SURVIVAL RATES reported** — the
co-visibility filter **drops categories unevenly**, and that selection bias must be stated, not buried.
Internal instrument (Apache-2.0 permits); if ever released, ship **the script + index, never frames**.

**(g) SpatialRGPT-Bench usage rules (added 2026-07-15).** ⚠ **Not yet downloaded — re-verify every
count locally before use.** GT is **Omni3D real 3D cuboid annotations** (SUNRGBD-dominant,
ARKitScenes, nuScenes, KITTI, Hypersim) — **sensor/synthetic, not monocular-pseudo-GT**, so no shared
failure modes with the models we evaluate; but QA generation is **templated with no human-verification
pass** (GT tier: below ReVSI's human re-annotation, above auto-pseudo-GT).
- **Core signal = the ~375 inter-object DISTANCE items** (direct/horizontal/vertical). **No ratio
  type; no closer-to-camera type.**
- ⚠ **Width/height items are PRIOR-CONTAMINATED** — blind GPT-4 (no image) scores **48–52% within
  ±25%**. **Always report a blind-LLM baseline alongside**; treat as secondary.
- Evaluate generic VLMs with **SoM-drawn marks** (their own baseline protocol), **never text
  referral** (breaks on same-class regions). bboxes + RLE masks ship in the JSON.
- **Replace their GPT-4 judge** with deterministic number-extraction + configurable relative-error
  thresholds; report **±10% and AbsRel** alongside their lenient ±25%. The unit lottery (in/ft/cm/m)
  makes exact match meaningless.
- ⚠ **License murky** (GitHub Apache-2.0, HF card untagged, nuScenes/KITTI upstream non-commercial) →
  **internal eval use only.**

## 3. Core data schemas
*(⚠ **The M0 "freeze" is SUPERSEDED as of 2026-07-15** — the site list below grew from four to five.
Frozen meant "don't churn it casually", not "never correct it when the science says it's wrong".)*

**Stimulus annotation (`annotations.jsonl`, one line per image):**
```json
{"id": "set3_00142", "image": "images/set3_00142.png",
 "camera": {"K": [[fx,0,cx],[0,fy,cy],[0,0,1]], "R": [...], "t": [...], "height_m": 1.5},
 "objects": [{"name": "red_cube", "category": "cube", "size_m": 0.3,
              "pos_world": [x,y,z], "pos_cam": [x,y,z], "depth_m": 2.1,
              "bbox_px": [x0,y0,x1,y1], "mask": "masks/set3_00142_obj0.png",
              "retinal_size_px": 88.2, "elevation_px": 312.0}],
 "factors": {"depth_bin": 3, "elevation_condition": "conflict", "size_condition": "fixed_retinal"},
 "pair_relations": {"(0,1)": {"ordinal_depth": "0_closer", "dist_ratio": 1.83, "dist_m": 1.2}}}
```

**⚠ THE FOUR SITES BECOME FIVE FUNCTIONAL STAGES (revised 2026-07-15).**
Architectures are **not homologous** — projector vs resampler vs interleaving, and binding is
*emergent over layers*, not a place. So sites are defined **functionally**, and each is **mapped per
architecture to a concrete tensor**:

| # | Functional stage | Concrete tensor today | Status |
|---|---|---|---|
| 1 | vision-encoder representation | `enc_out` | exists |
| 2 | vision→language **interface** output | `proj_out` | exists |
| 3 | **early multimodal LM** representation | `lm_vis_L{k}` | exists |
| 4 | **object-conditioned language** representation | `lm_txt_L{k}` | exists |
| 5 | **answer / readout** representation | `lm_ans_L{k}` | 🔴 **M4 MUST ADD — no hook exists** |

**M4 deliverable: the per-architecture tensor-mapping table** (LLaVA-1.5 / Qwen2.5-VL / InternVL3),
written into config, not code. A functional stage that maps to *different* tensors across
architectures is exactly what makes the cross-model comparison meaningful — and silently mapping it
to the *wrong* tensor is how the comparison becomes noise.

**Pooled activation cache (per model × stimulus set):** one `.npz`/safetensors per layer-site or a single zarr store; TWO variants per site — (a) mask-pooled per-object `[n_images, n_objects, hidden_dim]`, (b) all-token/strip-level pooled `[n_images, n_strips, hidden_dim]` (spatial signal is distributed across background tokens — Cui et al. v2; object-pooled-only caching would silently bias M5 toward "metric absent"). Plus `meta.parquet` (image id, object id, all geometry targets, factors). fp16. Target: ≤ 1 MB/image/model total.
**Three probe TARGETS per stage, not two** (6c): object-associated **visual** tokens · object-name
**text** tokens · a **JOINT visual+text** token set (cross-token decoder). A bare stage-3→4 drop is
vulnerable to *"different token populations, different probe conditions"* — the joint decoder is what
closes that hole, so the cache must support it.

**Probe result record:** `{model, site, layer, target (ordinal|ratio|absolute|qualitative|x|z), axis (depth|lateral), stimulus_set, seed, split, metric (spearman|R2|acc), value, n, control_value (shuffled-label)}` → one tidy parquet for all of Phase-2 plotting.

## 4. Milestones

### M0 — Repo skeleton + infra utilities (no science) — ✅ DONE 2026-07-10
Scaffold everything in §1: pyproject with groups, module stubs, config loader, seeding util, GPU-guard util (`utils/gpu.py`: `claim_gpu(n)` — nvidia-smi check + CUDA_VISIBLE_DEVICES + clear abort), wandb/CSV logger, schema dataclasses for §3 with (de)serialization + round-trip tests.
**Accept:** `uv run pytest` green on a GPU-less machine; `uv sync --extra analysis` works locally, `--extra extract` works on server; GPU guard verified against an occupied GPU.
**Status:** all criteria met. 28 tests pass; guard tests are GPU-independent (injected nvidia-smi + monkeypatched off-host path) so they're green on a GPU-less machine, and the guard was ALSO verified live on plant-ai06 (aborts on occupied GPU 5, claims free GPU 6). Env values filled into CLAUDE.md. **NB hardware is A6000 48 GB, not A100** (see PROJECT_MEMORY) — budget the M4 "overnight on one A100" line against 48 GB.

### M1 — Rendering spike + minimal scene generator — ✅ DONE 2026-07-10
**Renderer decision (M1.1): bpy (Blender 5.0 Python module), Cycles on CPU.** `uv add bpy` installed a 357 MB prebuilt wheel with no compile/Apptainer; imports + renders headless; ~1.3 s/img CPU @512² (Apptainer/pyrender not needed). Generator (M1.2–1.3) built: `stimuli/{geometry,scene_spec,sampler,render_bpy}.py`, `scripts/{render_stimuli,contact_sheet}.py`, `configs/stimuli_v0_congruent.yaml`. 44 tests pass incl. render-consistency <2 px. See PROJECT_MEMORY for the numpy<2 unification decision and bpy 5.0 API notes.
1. **Spike (½ day):** on the server, `uv add bpy` in a scratch project; render one cube headless. If bpy wheel fails → try Apptainer install; if blocked → pyrender fallback. Record decision in `PROJECT_MEMORY.md`.
2. Generator v0: scene spec (YAML) → N images: ground plane, 2–3 primitives (cube/sphere/cylinder, solid colors), parameterized object positions, camera at parameterized height/pitch; exports §3 annotations incl. per-object masks and exact geometry. Verify projection math: rendered pixel position of object center must match `K[R|t]` projection within 2 px (test).
3. Factorial sampler: given factor grid (depth × elevation-condition × size-condition × object-set) + seed → balanced stimulus set. v0 target: 500 images, congruent conditions only.
**Accept:** 500-image set renders end-to-end from one config; annotations pass geometry tests; a contact-sheet script produces a visual sanity PDF.

### M2 — External dataset adapters — ✅ DONE 2026-07-14
Download + adapter per dataset in §2 (skip Kang/SynSpat3D/MetricVQA). Uniform interface: `load(name) -> iterable[{image, question, answer, meta}]`. Include ReVSI's corrected annotations as the VSI variant. Store under `$DATA_ROOT/external/`.
**Accept:** one smoke test per dataset loads 5 items and displays them; disk usage documented.
**Status:** all criteria met. Six adapters (`src/sbind/datasets/`), `scripts/{download_dataset,dataset_contact_sheet}.py`, `configs/datasets.yaml`. 16 dataset tests pass (skip cleanly when data is absent, so the suite stays green on a laptop); HTML contact sheets with question+answer under each image, eyeballed. 20 GB on disk, inventory above.
**Interface note:** the spec's singular `image` became **`images: list[str]`** — ReVSI is video and MindCube is multi-view, so a singular field could not express half the benchmarks. Items also carry a stable origin-carrying `id` (`<dataset>/<index>`) so eval results join back to source, and video items carry `video` + `frame_indices` with **lazy** frame decode (nothing materialised).

### M3 — Reproductions (load-bearing gate) — ⚠ DONE 2026-07-14: **M3.1 PASS (mechanism), M3.2 FAIL (our stimuli)**
1. **Kang reproduction (reimplemented):** mirror-swap activation patching + spatial-ID derivation + steering on LLaVA-1.5-7B and Qwen2.5-VL-7B, using their data-engine recipe (tile two objects on grid; COCO-Spatial from downloaded COCO). Pass bar: steering belief-swap ≫ noise control, direction of all key effects matches paper (~64% vs ~30%; exact numbers within a few points).
2. **Wang & Gao pattern reproduction:** mask-pooled object tokens on our M1 stimuli, ridge probes for x/z/pairwise distance + color/shape. Pass bar: pattern match — semantics ≫ metric; x ≈ chance; z modest.
**Accept:** a short internal report (numbers table vs paper) committed to `reports/`. **If either fails after honest effort, STOP and rethink framing before Phase 2 — this is the project's go-gate.**

**RESULT — full report: `reports/m3_reproduction.md`.**
- **M3.1 = PASS on the mechanism, FAIL on the absolute magnitude.** The mirror-swap patching
  profile reproduces *exactly* on both models (**image patches early → object-word tokens middle
  → text late**), rank-3 R² = **0.87 / 0.84** vs their ≥0.85, and steering along the spatial-ID
  mirror direction is dramatically selective: **31.3% vs 0.0% norm-matched noise** (Qwen, at the
  paper's α=5). What does NOT reproduce is the absolute swap rate (19–31%, not ~64%) — but our
  noise floor is also ~0%, not their ~30%, so the paper's own summary statistic, the
  **above-chance influence**, matches or exceeds theirs (+31.3 pts at α=5, **+43.3 pts** at the
  dose-response peak, vs their +34.9). Our models are simply far more certain on this task
  (95–98% accuracy), so a random nudge never flips a belief. **Nothing was tuned to close the gap.**
- **M3.2 = FAIL, and the cause is OUR STIMULI, not the method.** See §2.5(d) below — this is the
  most consequential thing M3 produced.

**⚠ M3.2's failure is the go-gate's real output. Read §2.5(d) before touching M4.**

### M4 — Full stimulus battery + extraction pipeline — **SPLIT INTO M4a + M4b (2026-07-15)**
**⚠ M4 IS THE REAL GATE ON PHASE 2.** M3.2's pass bar transferred here (advisor decision,
2026-07-14). Read §2.5(d) and `reports/m3_reproduction.md` §2.4 first — v0 could not measure models,
only itself.

**🔀 WHY THE SPLIT (decided 2026-07-15).** M4 had accumulated two independent deliverables (a
generator and an extraction pipeline) **and two independent gates** — the image-identifiability gate
and the M4b validity gate (formerly 'the transferred Wang & Gao bar' — reformulated at Design Revision 3). Run as one milestone, **a failure at either gate leaves you
unable to say which half was wrong**: "metric is not decodable" would be indistinguishable from "the
images never contained it" *and* from "the extraction is mis-mapping tokens". They are now separate
milestones with **separate gates**, in dependency order. *(This is a sub-split like M1.1/M1.2 and
M3.1/M3.2 — **M0–M7 are NOT renumbered**; M4.5 still follows M4b.)*

| | Deliverable | Its gate | The question that gate answers |
|---|---|---|---|
| **M4a** | stimulus battery v1 (generator) | **image-identifiability** | *Do our images actually contain the evidence?* |
| **M4b** | extraction pipeline + cache | **validity gate (5 conditions)** | *Does our instrument measure models, or itself?* |

**M4a's gate is a property of the STIMULI and needs no VLM at all** — which is exactly why it must
pass first. Do not build M4b against a battery that has not cleared it.

**⚠ M4 IS A PILOT THAT FIXES THE FINAL ANALYSIS MATRIX — not just a generator run.** Scope it to the
**minimal publishable core** (6k): **2 architectures** (Qwen2.5-VL-7B + LLaVA-1.5-7B — both cached),
**one metric variable** (egocentric depth), one qualitative positive control, five functional stages,
leak-controlled linear+MLP probes, one behavioral test, one intervention. **Expansion to 4–6 models
happens only after the site-wise pattern stabilizes on two.** (Qwen2.5-VL-3B stays cached for S2
forward-compat but is outside the core matrix.)

---

#### M4a — Stimulus battery v1 (generator). Gate: IMAGE-IDENTIFIABILITY

**THREE STIMULUS REGIMES, not two (6e):**
1. **natural-congruent** — all cues agree. *Controls only.*
2. **counterbalanced** — nuisance cues vary **independently**, scenes stay **PLAUSIBLE**.
   **🚩 THE PRIMARY LOCALIZATION CLAIM LIVES HERE.** This is what preempts the OOD attack
   *structurally* rather than by argument: the headline claim never rests on physically bizarre images.
3. **conflict** — cues actively disagree. *Cue-integration analyses only* (fusion vs winner-take-all).

1. **Generator v1 — the five REQUIRED decorrelations.** Conflict conditions
   (fixed-retinal-size, elevation-conflict), canonical-object set (import a few CC0 models:
   chair, mug, bottle) alongside primitives, question templates per taxonomy level (qualitative
   / ordinal / ratio / absolute) with balanced answer keys. Scale: ~5–10k images per config
   decision. **On top of that, and non-negotiable — each one is a MEASURED defect of v0:**
   - **(a) Continuous lateral positions.** v0's `lateral_offset` is a single constant (0.7), so
     `x` took **exactly 2 values** and was a binary SIDE label, not a metric coordinate.
   - **(b) Camera-pose jitter (height / pitch / yaw).** With a fixed camera, camera-frame `x`
     **is** image position — which is why x R² = 0.997 was measuring the mask-pooling, not the
     model. Jitter decorrelates image position from 3D coordinates and **kills the position leak
     at its source**. It also explains the Wang & Gao discrepancy: their scenes vary camera path.
   - **(c) `size_condition` is LOAD-BEARING, not an optional factor.** Independent per-object
     physical-size jitter is the ONLY thing that breaks the size↔depth shortcut. In v0 both
     objects share one multiplier, so apparent size ∝ 1/depth and **depth is 86% predictable
     from apparent size alone** (r = 0.93).
   - **(d) Nuisance variation:** textures, distractor objects, lighting jitter. Two primitives on
     a bare plane have too few degrees of freedom for "modest decodability" to be *expressible*.
   - **(e) Recalibrate.** Any new primitive, pose freedom, or per-object size jitter invalidates
     the M1 calibration and the 1.18 depth-ratio floor — re-derive from WORST CASE
     (`scripts/derive_cue_constants.py`).
2. ⚠ **While the generator is open, add the SOLO-OBJECT ID PASS** (M4.5's prerequisite). It is nearly
   free now — one extra tiny render per object — and expensive to retrofit once 5–10k images are
   rendered. M4.5 does not *run* until M4b's gate passes; its cheap prerequisite belongs **here**.

**Accept — M4a:**
- The battery renders end-to-end from one config across all three regimes; **determinism re-verified
  by byte-compare** (hard rule); validation suite green **with margins reported, not pass/fail**;
  recalibrated cue constants derived from **worst case** (evaluation law, clause 1 — these are
  constructed quantities).
- **🚦 M4a's GATE — THE IMAGE-IDENTIFIABILITY GATE (6f; hardened at DR3-r2). Exact renderer GT ≠
  pixel-inferable GT.** A **directly-supervised model on raw pixels** (or oracle geometric image
  features) must recover each target variable **from the image** — **evaluated on held-out
  nuisance factors (object identities, poses, textures, camera configurations, cue combinations — plus renderer
  seeds, lighting families, backgrounds, and render/anti-aliasing settings; cross-renderer
  validation is the ideal), never only random splits**: otherwise the supervised baseline can pass
  through the very cues and artifacts the battery is meant to control.
  **Per-LEVEL gates, separately: ordinal identifiability · continuous ranking · calibrated
  magnitude/ratio.** The human spot-check licenses ORDINAL identifiability only (humans do not
  produce calibrated metric values) — continuous/ratio levels are gated by the supervised
  baseline's held-out generalization.
  **If the image does not contain the evidence, no site can** — and a "low everywhere" probing
  profile would then be an **instrument failure wearing a finding's clothes** (CLAUDE.md rule 11).
  **This gate needs no VLM, and it is why M4a runs first:** clearing it is what makes a later null at
  *any* site interpretable at all.
- **Do not start M4b against a battery that has not cleared this gate.**

- **Status 2026-07-16 (M4a pilot implementation + result analysis): IN PROGRESS, not accepted yet.**
  Implemented the three-regime pilot generator, continuous lateral sampling, camera/lighting jitter,
  optional distractors, procedural chair/mug/bottle stand-ins, target-placement guards, and the
  solo-object ID/amodal mask pass. Rendered and validated final pilots: natural-congruent 40 images,
  counterbalanced 60, conflict 40. All three pass the output validator with margins reported; full
  test suite: `134 passed`. Oracle geometric-image analysis clears the target-variable gates for the
  counterbalanced and conflict pilots, while natural-congruent remains a control and fails ratio
  generalization under held-out splits. Report: `reports/m4a_battery.md`.
  ⚠ **The pilot NUMBERS were measured against the PRE-DR3 gate** (flat `acc >= 0.70` / `R2 >= 0.20`,
  no per-level split, nuisance factors not held out). They are not wrong; they are **no longer
  SUFFICIENT** to clear the hardened Gate 1. The load-bearing pilot signal survives: counterbalanced
  drove physical-size↔depth to **r = 0.033**, breaking the shortcut M3.2 died on.

  **Remaining before M4a accept — ORIGINAL five:**
  1. true contrastive matched pairs (only a config scaffold exists);
  2. gate-scale pilot / full battery (140 rendered; configs declare 1,020 = 180+420+180+240);
  3. M4a determinism byte-compare (hard rule, never yet run on M4a outputs);
  4. human spot-check / contact sheet (⚠ DR3: licenses the ORDINAL level ONLY);
  5. procedural chair/mug/bottle → imported CC0 assets, if the final claim needs canonical objects.

  **Added by DR3's hardened Gate 1 (2026-07-16; measured against the battery 2026-07-17):**
  6. **Persist the nuisance factors that ALREADY vary but are DISCARDED.** `sampler.py` samples
     `ground_color` (4 values) and `sun_energy` (3.0–5.5) + `sun_direction_jitter` per image, passes
     them to the renderer, and **never writes them into the annotation's `factors`** — so no
     held-out-lighting / held-out-background split is constructible even though the factor varies.
     Cheap, pure gain. *(Same class as `strip_pool()` existing but never cached.)*
  7. **Add the factor axes that DO NOT EXIST.** ⚠ **TEXTURES ARE ABSENT ENTIRELY** — grep of
     `src/sbind/stimuli/` + the M4a configs returns nothing for texture/checker/HDRI; ground is flat
     colour. **This is a PRE-EXISTING gap against the plan's own item (d)** ("nuisance variation:
     textures, distractors, lighting jitter"), not something DR3 created — DR3 only made it
     load-bearing by naming textures in the held-out list. Also absent: **lighting FAMILIES**
     (one sun + continuous jitter is one family), **renderer-seed variation** (`cycles_seed: 411`
     fixed battery-wide), **render/AA-setting variation** (`samples: 96` fixed).
  8. **Per-LEVEL gates + PRE-REGISTERED NUMERIC BOUNDS.** Gate separately: ordinal identifiability ·
     continuous ranking · calibrated magnitude/ratio. And deliver the numeric bounds M4b's leak
     criterion needs (trivial-feature ceiling with CI; Δ_repr|dumb permutation-null threshold) —
     **relative "collapse vs v0" is insufficient (0.94→0.40 is still a leak), and M4b MAY NOT START
     without them.**
  `scripts/m4a_analyze_stimuli.py` currently implements held-out object identity / camera pose /
  depth range / object pair / depth gap / cue combo — i.e. the ORIGINAL list only.
  **Sequencing (nothing needs re-rendering for DR3):** DR3 changed the GATE, not the stimulus spec —
  no rendered pixel and no generator line is invalidated, and the pilot was always going to be
  superseded by the gate-scale render. Do 6+7 (generator + annotation), THEN render at gate scale,
  THEN analyze under 8. **M4b remains locked.**

  ⚠ **STALE DATA ON DISK (found 2026-07-17):** `$DATA_ROOT/stimuli/m4a_v1_counterbalanced/` carries
  the FULL-battery name but holds only **60 images**, while its own `config.yaml` /
  `run_metadata.json` declare `n_images: 420` (aborted run at git `725ad42`). Delete or rename before
  it is mistaken for the battery — an analysis pointed at it would silently get 14% of the intended
  set with every name and config asserting otherwise (rule 5).

---

#### M4b — Extraction pipeline + cache. Gate: THE VALIDITY GATE (5 conditions, DR3)

1. `extract/`: generic HF-VLM wrapper (LLaVA-1.5/1.6, Qwen2-VL, Qwen2.5-VL-7B, **Qwen2.5-VL-3B**, InternVL, Gemma-3) over the **five functional stages** of §3 — including the **new `lm_ans_L{k}` readout hook, which does not exist yet**; mask-pooling (coverage-weighted, per Wang & Gao's method — reimplemented) and object-word token extraction (tokenizer-aware span finding); writes §3 caches; per-batch checkpointing + `--resume`.
   **S2 forward-compatibility:** include both Qwen2.5-VL-7B and -3B Instruct in the model list — they are the shared bases of the method-audit checkpoints (S2/M7: SpaceR + ViLaSR on 7B; SpatialLadder + SpaceQwen/SpaceOm + Spatial-MLLM on 3B), so every S1 measurement on them doubles as the audit baseline. The wrapper must accept arbitrary HF checkpoint paths of the same architecture (base vs fine-tune swap = config change only).
   **⚠ The cache MUST contain the strip/all-token variant, not only the mask-pooled one.**
   `extract/pooling.py` has `strip_pool()`, but M3.2 cached mask-pooled features only. Fixed-grid
   strips are not selected by object position, so they are the **primary leak-free estimator** —
   promoted from "underestimation guard" to load-bearing.
2. **The per-architecture tensor-mapping table** (§3) — which concrete tensor realises each of the
   five functional stages, per architecture — **in config, not code.**

**Accept — M4b:**
- Full battery cached for the **2-model core** overnight on one A6000 (48 GB); cache size within
  budget; pooling unit tests green; resume-after-kill verified.
- The **tensor-mapping table** exists in config and the **`lm_ans_L{k}` readout hook** is implemented
  and cached.
- **The three leak controls of `reports/m3_reproduction.md` §2.4 implemented and reported**:
  dumb-features leak ceiling, fixed-grid strip probes, camera-pose jitter — the ceiling in the
  **incremental form Δ_repr|dumb** (6g), never as a bare difference of two scores.
- **🚦 M4b's GATE — VALIDITY-ONLY (reformulated at Design Revision 3, 2026-07-16; the old
  "W&G pattern must emerge" bar put a SUBSTANTIVE HYPOTHESIS inside a validity gate — if metric
  were genuinely strong on the fixed battery, the old bar would have rejected the experiment for
  failing to reproduce the expected weakness).** The gate now requires ALL of:
  1. **positive controls decode** (per-stage probe sensitivity demonstrated);
  2. **label and feature nulls at chance** (shuffled labels; dumb-features probe at its expected
     floor on decorrelated targets);
  3. **the leak ceiling COLLAPSES vs v0 — with a PRE-REGISTERED ABSOLUTE acceptance rule, not
     only a relative one** (DR3-r2: 0.94→0.40 would still be an unacceptable leak). Before M4b
     probing starts, the M4a report must fix numeric bounds: trivial-feature score below a
     prespecified ceiling (with CI), incremental gain Δ_repr|dumb materially above a permutation
     null, and held-out-factor splits where the nuisance baseline FAILS while the target remains
     identifiable;
  4. **generalization across held-out objects / camera poses / depth ranges** (not only random
     splits);
  5. **demonstrated dynamic range** (the protocol can distinguish representations it should
     distinguish).
  **⚠ If metric decodability is STILL near ceiling after 1–5 pass:** run the mandatory diagnostic
  checklist (per-cell leak ceilings, contrastive-pair estimator, held-out-factor splits, token
  registration re-verification). If everything passes, **high metric decodability is a FINDING —
  strong metric representation — not a gate failure**; Phase 2 proceeds with the finding
  inverted. The **W&G gradient (semantics ≫ metric, x≈chance, z modest) is a BENCHMARK
  COMPARISON to report, not a go/no-go criterion.** ⚠ Because M4a's gate has already passed, a
  *validity* failure here is unambiguous — extraction or leak controls, NOT the images. That
  disambiguation is the point of the split.
- **Pilot exit criterion (fixes the final analysis matrix):** M4a's identifiability gate passed
  **AND** M4b's five validity conditions hold **AND** the leak-ceiling collapse is demonstrated.
  (The old "W&G gradient emerged" clause is retired with the gate reformulation.)

### M4.5 — Occlusion & the amodal probe (= stage **S1.5**) — 🔒 LOCKED until **M4b's** gate passes
*(Its cheap prerequisite — the solo-object ID pass — belongs to **M4a**, while the generator is open.)*
**Do not start this unprompted.** M4.5 unlocks *only* when M4b clears its VALIDITY gate (5
conditions, Design Revision 3 — positive controls, nulls, leak-ceiling collapse, held-out
generalization, dynamic range). If the instrument fails validity, **an occlusion result would be
just as meaningless as a metric one** — fix the instrument first. Milestones are **not renumbered**: M4.5 sits
between M4 and M5 and is independent of M5 (both are gated on M4; either may run first).

**Why occlusion, scientifically — H-occ.** Occlusion is **primarily an ORDINAL VISIBILITY cue**: it
identifies front–behind ordering more directly than continuous magnitude. **Over-reliance on it
*could* support qualitative depth while leaving metric depth poorly represented** — which is the
mechanistic form of this program's central asymmetry, testable inside the cue-decomposition design M4
already builds. (Landscape Tension **T2** — geometry vs visibility-aware state — made mechanistic.)

> 🔴 **RETRACTED — do not restate (it stood in these docs for one day, 2026-07-14→15):**
> *"occlusion is the only **categorical** cue, carries **ZERO metric content**, therefore their best
> cue **cannot** carry metric information."* **False as stated.** T-junctions, containment and support
> are **also** ordinal cues (not "the only"), and occlusion boundaries + known shapes + camera geometry
> **do** constrain metric depth (not "zero metric content"). The dangerous part was the **deduction** —
> it made the program's headline asymmetry appear to follow from a *definition*. It does not. It has to
> be **measured**. Keep H-occ a hypothesis, stated in the weak form above.

**The amodal question splits into THREE — H1.5a/b/c. Do not conflate them:**
- **H1.5a — object persistence:** an entity-level representation survives partial visibility.
- **H1.5b — amodal geometry:** the **hidden extent** is recoverable *beyond* what visible-fragment
  features already give.
- **H1.5c — amodal binding:** that information is available **at object-referential tokens**.

**1. Design — physically rendered, congruent-only at this stage.**
- New factor **`occlusion_condition ∈ {none, partial}`**. In `partial`, the nearer object partially
  overlaps the farther one — **both fully physical, no compositing** (this preserves the
  exact-geometry guarantee that makes our ground truth trustworthy).
- Record per object **`occlusion_ratio` = 1 − visible_area / amodal_area**.

**2. Schema additions (per object).** `mask_amodal`, `occlusion_ratio`, `retinal_size_px_amodal`.
- **The amodal mask is nearly free.** The composite ID pass already yields the *visible* mask;
  rendering **each object alone** in a solo ID pass yields the **amodal** mask directly. (Same ID-pass
  discipline as M1: black-emission ground, lights at 0, `max_bounces = 0` — the bounce bug is *not*
  to be relearned.)

**3. Validation exemptions — state them, never let them fire silently.**
- Occluded variants are **EXEMPT from the retinal/area congruence checks**: the *visible* height of
  an occluded object is **not the calibrated quantity**. Check congruence on the **AMODAL**
  measurements instead. Encode this as an explicit, *counted and logged* exemption in
  `scripts/validate_stimuli.py` — a bare `continue` here is exactly the CLAUDE.md rule-3 failure.
- The occlusion factor is a new degree of freedom → **the M4 note (e) recalibration rule applies.**
- **Invariant to assert (not a smoke test):** `mask_amodal ⊇ mask_visible` pixelwise for every
  object, and `occlusion_ratio ∈ [0, 1)` for every object — with `> 0` for every object flagged
  occluded and `== 0` for every object in the `none` condition. Report **margins**, not pass/fail.

**4. The two questions (both cheap once M4's battery and cache exist).**
- **(a) Cue-use.** At **matched depth gaps**, does ordinal accuracy / decodability *jump* when
  occlusion is present vs absent? Behavioral **and** probe versions; two-ordering MCQ protocol as
  usual. This is the direct test of "occlusion is their dominant depth cue".
- **(b) The amodal probe — H1.5a/b/c.** For a partially occluded object, is its **position / depth /
  full extent** decodable, **at which functional stage**, and does the occluded object still **BIND**?
  (Kang's own open question: *do spatial IDs exist for objects behind occluders?*)

  > 🔴 **CORRECTED 2026-07-15 — amodal-extent POOLING is NOT the test.** The first draft of this
  > milestone called *"pool over the visible mask vs over the amodal extent"* a measurement detail
  > that **is itself a finding**. It is not: **pooling under the *invisible* mask mostly collects
  > OCCLUDER and BACKGROUND tokens**, so a null there measures the occluder, not the object. **Do not
  > assume hidden geometry is spatially stored under the hidden mask** — that assumption smuggles in
  > a strong (and unlikely) claim about *where* a representation lives.

  **Test IMPLICIT representation — the menu, all four:** (i) **visible-fragment** pooled; (ii)
  **occluder-region** tokens; (iii) the **object-name text token**; (iv) a **joint decoder conditioned
  on object identity**. Amodal-extent pooling survives only as a **labeled naive baseline**, never as
  the primary estimator.

**5. Leak-ceiling extension (mandatory — CLAUDE.md rule 12).** For occluded items the dumb-features
baseline must include the **visible**-mask geometry **AND `occlusion_ratio`**. An amodal-decodability
claim must beat a probe that only ever sees the *visible fragment's* geometry — otherwise "the model
completes the hidden part" is indistinguishable from "the visible fragment's shape gave it away".

**6. Explicitly DEFERRED to S4 — do not build:**
- **Occlusion cue-CONFLICT (inverted depth).** Physically impossible to render; it needs O-Bench-style
  layered composites, which **break the exact-geometry guarantee** and make ground truth
  cue-relative. Legitimate later; out of scope now.
- **Occlusion chains** (A hides B hides C) and **full visibility graphs** (who-occludes-whom edges) —
  S4's centerpiece candidate, gated on this milestone's amodal result.

**Verification-reads BEFORE the M4.5 design freeze** (standing rule: every specific design claim gets
a search before it is asserted):
- **🔴 Mirage Probes (arXiv 2606.13870, Jun 2026), "How Vision Models Fake Visual Understanding"** —
  a probing-*validity* critique. Bears on **every probe claim in this program, S1 included.** PRIORITY.
- **arXiv 2508.04567** — masked-object linear probes (>95%). Check whether their "masked" ≈ our occlusion.
- **arXiv 2603.28333** (MLLM-guided amodal completion); **O-Bench** (occlusion benchmark — adopt its
  inverted-depth / answer-frequency controls); **CAPTURe** (amodal counting; oracle decompositions);
  **SpatialMosaic** (occlusion-ratio data pipeline — engineering reference for computing `occlusion_ratio`).
- **Re-run at freeze time:** search *"amodal representation probing VLM occluded object depth"*.
  Checked 2026-07-15: geometric probing of *physically occluded* objects appears **OPEN** (adjacent
  work is classification probes on masked objects, and amodal *segmentation*). **Re-verify — do not
  assert the gap from this note.**

**Accept (ALL of these):**
- **Solo-ID amodal masks validated:** `mask_amodal ⊇ mask_visible` for every object (full scan, not a
  sample), `occlusion_ratio ∈ [0, 1)` for every object, correct by condition, margins reported.
- The `occlusion_condition` renders end-to-end from one config and **passes the exempt-adjusted
  validation suite** (congruence checked on amodal measurements; exemptions counted and logged;
  determinism re-verified by byte-compare, per the hard rule).
- **The H1.5a / H1.5b / H1.5c analyses each run from the cache on CPU**, reported **separately** (they
  are three claims, not one), each **against the extended leak ceiling** (visible-mask geometry +
  `occlusion_ratio`, in the incremental **Δ_repr|dumb** form), with shuffled-label controls.
- A positive control exists for the amodal claim: **show the measurement MOVES when it must**
  (CLAUDE.md rule 11 — a null here would be the most seductive kind of wrong result this project can
  produce). Zero-ablate the tokens you are pooling; if the metric does not move, the metric is dead.

### M5 — Probing & the core result (Phase-2 science)

**🔑 STANDING METHODOLOGY (adopted 2026-07-14): EVERY probe experiment ships with a
DUMB-FEATURES BASELINE. Decodability only counts ABOVE the dumb ceiling.**
The shuffled-label control is necessary but *not sufficient*: it catches a probe fitting noise,
but it cannot catch a probe reading a **trivially available non-representational feature**. Two
findings this session, both of which passed every shuffled-label control:
- the v0 category↔depth-role imbalance (a **shape-only** constant strategy scored **55.1%**);
- the mask-pooling position leak (mask **geometry alone** gives x R² = **0.942**, z R² = 0.972 —
  the model adds ~0.05).
Both are the same failure: **a confound that survives every unit test and dies only under an
adversarial baseline.** So the ceiling is standing policy, not a one-off control. For each
(model, stage, layer, target), also fit the probe on:
`{mask geometry: centroid, area, bbox, retinal size, elevation} ∪ {shape, colour} ∪ {cue values}`.

**⚠ REPORT THREE NUMBERS PER CELL (refined 2026-07-15) — and the third is the load-bearing one:**
1. best **dumb-feature** score;
2. the **probe** score;
3. **Δ_repr|dumb = score(dumb ∪ representation) − score(dumb)** — the **incremental gain** of the
   representation *over and above* the dumb features. A bare `probe − dumb` difference does not
   establish that the representation adds anything the dumb features didn't already have; the
   incremental form does.

**⚠ HELD-OUT SPLITS MUST TARGET THE CLAIMED GENERALIZATION — never only random image splits.**
Held-out **object identities**, **camera poses**, **depth RANGES**, **cue combinations**. A random
split over a factorial battery leaks every factor into training by construction.

**OPERATIONAL DEFINITION OF BINDING (fix this BEFORE probing — it is not a wording preference):**
*the prompt-conditioned transfer by which object-specific visual information becomes causally
available at the language-token positions responsible for referring to and answering about that
object.*

**🚦 DECISION RULE — claim a binding bottleneck only when ALL FIVE hold:**
1. metric is **recoverable** from object-associated **visual** tokens;
2. it is **substantially less** recoverable from that object's **text** tokens, *under matched
   evaluation*;
3. **qualitative** information **DOES** transfer to those same text tokens (within-model positive
   control — binding demonstrably works there, per Kang);
4. **causal intervention** at the transfer layers **changes metric answers**;
5. effects are **object-specific**, not a global answer bias.

**OUTCOME MATRIX** (replaces "every outcome is a finding", which was unfalsifiable). ⚠ **It is only
readable if per-stage positive controls have validated probe sensitivity first:**

| visual stages | bound-text stages | behavior | reading |
|---|---|---|---|
| high | low | low | candidate binding bottleneck → **apply the five-condition rule above** |
| high | high | low | downstream **access / readout** failure |
| low | low | low | upstream absence **OR instrument failure** → the **identifiability gate** (M4) adjudicates |
| low | high | high | **probe/site mismatch** — investigate before interpreting anything |
| high | low + injection **restores** | — | **strong causal support** |
| high | low + injection **fails** | — | binding loss **epiphenomenal**, or the intervention is inadequate |

**PROBE-CAPACITY LADDER** — linear (primary, comparable to prior work) → low-rank linear → shallow
MLP → controlled kernel → RSA/ranking. **Where signal "disappears" between stages, the nonlinear tier
is what distinguishes ERASED from RECODED** — and that distinction is half the thesis. Interpretation:
linear-high = directly accessible · nonlinear-only = **present but recoded** · neither (*with
validated sensitivity*) = unavailable · high-globally-but-low-object-conditionally = **binding /
assignment failure**.

Probe runner: for every (model, **functional stage**, layer, target, axis) → the capacity ladder with 5 seeds × 5 splits, shuffled-label control, **dumb-features ceiling (above)**, selectivity contrast (qualitative vs metric), rank-correlation metrics; probing **three representation targets** (visual tokens / object-name text tokens / joint cross-token decoder); verbalized-answer collection on identical stimuli (+ few-shot calibrated variant + oracle-text condition).

**ANCHOR EXPERIMENT — PROMOTED to a core mechanistic experiment** (it *is* the prompt-conditioned
binding test, not a side manipulation): same image; prompts {no reference / refer to B / ask
A-relative-to-B}; compare representation changes for **A, B, unrelated objects, and answer tokens**.
Distinguishes absolute encoding / relational recoding / answer-only computation /
binding-dependent relationalization.

**⚠ THE POSITION LEAK THREATENS M5'S CENTRAL CONTRAST.** Mask-pooled *visual*-token probes are
selected by the object's image position and therefore leak it; *bound-text-token* probes are not.
So "visual sites high, text sites low" — the very shape that separates **Prediction 1** (metric
survives in visual tokens, dies at binding) from **Prediction 2** (metric was never there) —
**could be manufactured by the measurement itself.** Mandatory: report the fixed-grid **strip**
(leak-free) estimator as primary, the mask-pooled one alongside, and both against the dumb
ceiling. See `reports/m3_reproduction.md` §2.4.
**Dataset usage rules (§2.5) apply here:** call `assert_behavioral_safe(name)` in the
verbalized-answer collector (DepthCues is PROBE-ONLY — probe `meta.label` only, never score
its synthesized questions). **The validation layer is the CLOSED predeclared set of §2.5(f)** —
CV-Bench Depth/Distance + What'sUp-B + ReVSI-1F + SpatialRGPT-Bench distance slice + CausalSpatial
collision/occlusion. **MindCube is OUT** (no single-image primitive). ReVSI's frame budget must be
stated **explicitly** in the config; full-video ReVSI at 2–3 budgets is a **labeled extension
analysis**, not the core. **Report the NOT-SURE RATE** wherever an abstain option exists
(`meta.not_sure_letter`) — CausalSpatial's own scaling result is that NSR collapses 18.77% → 0.10%
while accuracy stays flat, i.e. *larger models become decisively wrong*, which accuracy alone hides.
**Adopted standards (from Dual Mechanisms v2, 2603.22278v2):** (a) probe BOTH mask-pooled object tokens AND all-visual-token / strip-level representations — their central negative control shows spatial signal is distributed across background tokens, so object-pooled-only probing underestimates what survives (M4's cache must store an all-token pooled variant per layer too); (b) two-ordering strict protocol for all verbalized MCQ answers (ask both option orders, correct only if both pass); (c) random-direction nulls for any steering/injection; (d) report fixed-α and per-example-α (Probe*) intervention variants. Outputs: tidy parquet (§3) + the Figure-1 plotting script (decodability profile across sites/layers vs verbalized accuracy).
**Accept:** full grid runs from cached features on CPU in hours; every plotted number traceable to config+seed; positive control (qualitative) shows the Kang-consistent profile.

#### ⚠ M5 ADDITIONS (2026-07-16 — from the full literature sweep; all MANDATORY unless marked)

1. **Vision-ablation ARBITER at every stage (mandatory; from 2606.31257):** rerun probes AND
   behavioral readouts with (a) gray-blank images and (b) mismatched-real images. Report
   real-vs-ablated per site. Decodability that survives blanking is prior, not grounding.
2. **Pre-registered PRIMARY contrast: site 2 (projector output) vs site 4 (object-word tokens).**
   This tests which of three competing localization patterns holds for controlled continuous
   depth: 2605.20448 (patching: a sharp causal-recovery discontinuity around the merger/projector,
   for categorical occlusion) vs Anchored 2606.06714 (probes: decodable at LM-input, slant) vs our
   H1 (binding). ⚠ **The two are strictly compatible — do NOT frame this as adjudicating a
   published contradiction (DR3 ban);** their *interpretations* are the motivation. Name the
   comparison in the analysis plan; power the design for it.
3. **Natural-image sanity check (from 2607.03358):** routing flips synthetic↔natural — run a
   reduced probe pass on a real-image subset (CV-Bench sensor slices) or carry an explicit
   scope caveat in every claim.
4. **Prompt format = controlled, reported config variable** (it alone flips pathways; 2607.03358).
5. **Contrastive-pair estimator** (third leak-immune probe; lineage: Why Far Looks Up minimal
   pairs, Mirage Probes contrastive probing): stimulus pairs matched on mask geometry, differing
   in true depth (camera jitter makes these constructible).
6. **Intervention vocabulary:** frame injection/patching results as usage / necessity /
   sufficiency (2607.03358), with the mediation chain as the sufficiency-with-specificity test.
   Adopt their normalized restoration score + both-clean-correct pair filtering.
7. **(DR3-r2) TEXT-SIDE trivial baselines are mandatory, mirroring the visual-side dumb ceiling:**
   token identity, token position, object mention order, prompt-template role, option order —
   plus text-only / blank-image hidden-state controls. Text-token probes escape the SELECTION
   leak but have their own leak classes; the visual-vs-text contrast must never imply
   "contaminated vs clean".
8. **(DR3-r2) The stage-wise profile is reported UNDER MATCHED EVALUATION, never as one raw
   curve:** matched-capacity readouts (or capacity controls), equalized sample counts, nested CV
   for probe hyperparameters, per-cell CIs, and the incremental score over STAGE-SPECIFIC dumb
   baselines. Report per cell: dumb-only, representation-only, combined, and Δ with a permutation
   distribution — Δ alone is not the definition of decodability (suppression, capacity, and
   ceiling effects can distort it).
9. **(DR3-r2) Two-ordering protocol, operational definition:** primary metric =
   **order-robust accuracy** (correct under BOTH orderings; chance level adjusts accordingly),
   reported alongside per-order accuracies and an order-effect confidence interval. "Both orders
   must pass" without this definition changes the estimand silently.
10. **(DR3-r2) Cross-study effect comparisons are DESCRIPTIVE only:** our above-noise steering
   contrast and Kang's are not directly comparable (noise construction, doses, selection, and
   baseline belief distributions differ) — report both, claim superiority of neither. The
   patching-profile reproduction is stated as "qualitative stage/layer pattern reproduced;
   absolute effect size did not" — never "exact" without a preregistered similarity metric.
11. **(DR3-r5) Ordinal-vs-continuous comparisons must be DIFFICULTY-MATCHED — else H2a measures
   an easier classification target, not selective preservation:** discretize continuous depth
   into matched-bin classification; predict ordinal relations FROM the same continuous labels;
   equalize probe capacity and sample sizes; report calibrated noise ceilings per target class;
   prefer rank/information-theoretic metrics for the cross-target comparison.
12. **(DR3-r5/r6) THREE per-stage positive controls, and the continuous ones must be
   NON-CIRCULAR:** (a) semantic (shape/colour); (b) an **injected implementation control** — a
   known scalar written into an independent activation dimension/synthetic channel, verifying
   that extraction + probing recover it (validates the pipeline, NOT natural detection); (c) an
   **independently established natural geometric control** — a representation/site where
   continuous image geometry is expected recoverable on independent grounds. **Neither (b) nor
   (c) may be constructed from the probe being validated** — injecting along a probe-derived
   direction and decoding it with the same probe is near-guaranteed and validates nothing about
   natural geometry. A shape control alone cannot license a continuous-depth null.
13. **(DR3-r5) Intervention-site preregistration:** primary = the stage-2 vs stage-4 contrast;
   probe-indicated sites are exploratory, confirmed on held-out data. Depth-direction
   construction / validation / causal evaluation use three disjoint splits.

### M6 — Interventions (Phase-3, spec later)
Graded intervention along a **validated depth-related direction or subspace** (DR3-r2: the
construction — probe direction / regression vector / matched-condition difference / low-rank
subspace / depth-matched interchange — must be formally defined and stated; they carry different
causal interpretations. Reserve the name "metric ID" until then). Dose-response curves;
binding-layer LoRA + metric auxiliary loss vs matched-budget SFT. **Do not design in detail until M5 results exist — the evidence
chooses the intervention.**

**⚠ M6's intervention is SELECTED BY M5's PATTERN — do not pre-commit to binding-layer injection**
(the plan's own bias, named): upstream-low → **encoder/projector** intervention · visual-high /
text-low → **binding** · text-high / behavior-low → **readout**.

**🔴 ANTI-"LOGIT-HACK" CONTROL BATTERY — all of it, or the result is answer steering, not repair:**
- **layer** controls (hypothesized layers vs early/late);
- **position** controls (object tokens vs unrelated tokens);
- **content** controls (correct vs **sign-flipped** vs shuffled vs random-direction);
- **dose-response**; generalization to **unseen values**; **paraphrase transfer**;
- **free-response AND ordinal ranking**, not only MCQ;
- **qualitative controls undegraded** (the intervention must not simply break the model);
- **and THE MEDIATION PATTERN — the load-bearing one: injection → downstream metric decodability
  RISES → behavior improves.**
  ⚠ **An injection that moves ANSWERS without moving downstream DECODABILITY is answer steering, not
  repair.** That distinction is the whole difference between "we repaired the representation" and "we
  found a direction that pushes the logits", and only the mediation chain can tell them apart.

### M7 — The method audit (= stage **S2**; keep in mind, don't build yet)
Comparative mechanistic audit of spatial-enhancement methods: run the M5 probing grid unchanged on public fine-tuned checkpoints vs their bases (7B: SpaceR, ViLaSR vs Qwen2.5-VL-7B-Instruct; 3B: SpatialLadder, SpaceQwen/SpaceOm, Spatial-MLLM vs Qwen2.5-VL-3B-Instruct) + inference-time scaffolds (scene-graph prompt, depth-map input, Set-of-Marks — implemented as prompt/input transforms in `eval/`). Design constraint on earlier milestones: nothing in `extract/` or `probes/` may assume the checkpoint is a base model.

**⚠ THE THREE-WAY LABEL IS REPLACED BY A FIVE-DIMENSIONAL MECHANISM PROFILE (2026-07-15).** "Representation improved / binding improved / prior installed" forced each method into **one** box; the categories are **not mutually exclusive**, and the forcing would have manufactured false clarity. **Report the VECTOR:**
- **ΔR_visual** — upstream representational gain
- **ΔR_bound** — object-specific transfer gain
- **ΔB** — readout gain, *conditional on matched internal decoding*
- **ΔP** — prior reliance, under blind / black-image / geometry-conflict controls
- **ΔC** — causal repair: mediation + specificity

**🔴 CHECKPOINT COMPARABILITY CHECKLIST — run BEFORE any base-vs-finetune internal comparison:**
**tokenizer · image resolution · prompt/conversation template · preprocessing · transformers revision.**
This audit's entire signal *is* a difference between checkpoints, so a mismatch on any one of these
produces a "mechanistic difference" that is a pure artifact. Check first, compare second.

**🔑 The behavioral mystery this audit exists to explain (added 2026-07-15, from the landscape deck):
ISOLATED STRUCTURED PERCEPTION *HURTS*.** Four independent papers report it — EmbodiedVSR (detector /
depth / graph alone each *degrade*), SpatiaLQA (segmentation alone **67.4 → 50.3**; depth alone
→ **64.1**), NuScenes-SpatialQA, ISGR. Handing a VLM a *correct* structured spatial input makes it
*worse*, and nobody has a mechanism for it. Scaffold probing is the instrument that can settle it:
**does isolated structured input never reach the binding sites, or does it actively interfere there?**
- Cite all four in the audit's motivation.
- **Add "isolated vs integrated scaffold" as an audit condition axis**: scene-graph-alone vs
  depth-alone vs **integrated** — mirroring their behavioral contrast, so our mechanistic
  decomposition lands on the exact comparison their behavioral result is about.

## 5. Known gotchas
- **Calendar (2026-07-16): WACV 2027 R2 deadline Aug 28 = primary target (minimal core); YANS
  poster Aug 16–18; CVPR Nov 15 fallback.** M4a starts immediately; no slack for late start.
- **Sweep protocol: biweekly citation watch + monthly TOPIC sweep + anchor new-version checks.**
  Watch additions: 2605.20448 (Deccan, follow-up declared), 2606.06714 Anchored (follow-up
  declared), 2606.01914, 2605.20784, 2602.07025, 2603.18353.

- **🔴 READ "Mirage Probes" (arXiv 2606.13870, Jun 2026) BEFORE making any M5 probe claim.** *"How
  Vision Models Fake Visual Understanding"* — a probing-**validity** critique that bears on every
  probe number this project will report (M5's core result, M4.5's amodal probe, M7's audit). This is
  a **pre-M5 must-read**, not a citation to add at write-up: if it identifies a way probes can look
  informative while measuring nothing, we want that in the design, not in a reviewer's response.
  Precedent from M3 (the dead `" left"/" right"` readout) says a probe can be confidently wrong and
  entirely green.
- **⚖ THE EVALUATION LAW HAS TWO CLAUSES — applying either to the wrong class of quantity is a bug**
  (refined 2026-07-15; CLAUDE.md rule 7 updated to match):
  - **DETERMINISTIC, CONSTRUCTIBLE quantities** (rendered geometry, cue constants, calibration
    thresholds): **WORST CASE. Never means.** The extremes are measured *exactly*, and means were the
    *proven* failure here (1.096 mean-derived vs 1.158 true worst case).
  - **SAMPLED / STATISTICAL quantities** (probe scores, benchmark accuracies, per-category rates):
    **no aggregate threshold without checking the weakest PRESPECIFIED stratum**, plus condition-wise
    uncertainty (CIs, quantiles, failure-rate distribution). **One noisy item must not define a gate.**
    A literal worst-case rule on noisy data gates on the unluckiest sample — that is noise-chasing,
    not rigour.
- `bpy` wheels are Python-version-pinned (3.11); set `requires-python` accordingly, or isolate stimuli env from extract env (uv workspaces handle this).
- flash-attn under uv needs `no-build-isolation-package`; test in M0, not when a model demands it.
- Qwen2-VL M-RoPE and InternVL tiling mean "visual token ↔ image location" mapping differs per model — the mask-pooling module must own this mapping per model family, with a test per family (render a probe dot, check the pooled token responds).
- Gemma-3 / InternVL may need recent transformers; pin per-model versions in config if conflicts arise.
- LibreOffice-style "works on my machine": run everything through `uv run` — never a bare `python`.
- Monthly re-check: Metric VQA release; SynSpat3D dataset appearance; new papers citing the four anchors (biweekly).

## 6. Suggested vibe-coding session order
M0 → M1.1 (spike, decides renderer) → M1.2–1.3 → M2 (parallelizable, boring) → M3.1 → M3.2 (gate) →
**M4a (gate: image-identifiability)** → **M4b (gate: validity, 5 conditions)** → then M4.5 and M5,
in either order — **both are gated on M4b and neither is gated on the other.** M4.5 (occlusion /
S1.5) is the cheaper of the two, and its solo-ID prerequisite should already be in **M4a's**
generator. **One milestone per session** — and M4a/M4b are two sessions, not one: that is the point
of the split. Start each session by pasting this doc + `PROJECT_MEMORY.md`; end each by updating both
with decisions made.
