# Implementation Plan — Spatial Binding Bottleneck (for AI-assisted coding)

*Written 2026-07-09. Companion docs: `research_proposal_spatial_binding.md` (science), `VSR_niches_critical_deep_read.md` (literature), `PROJECT_MEMORY.md` (context). This document is the coding spec: hand milestones to a coding agent one at a time, in order. Acceptance criteria are the definition of done — do not move on until they pass.*

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
is a 4.9 GB zip plus its extracted videos). **Total 20 GB against 7.8 TB free — a non-issue.**

| Dataset | Status | Adapter | Items loaded | Disk | Notes |
|---|---|---|---|---|---|
| What'sUp (`amitakamath/whatsup_vlms`) | ✅ MIT, Google Drive | `whatsup` | 820 | 312 M | Controlled A (412 real photos) + B (408 CLEVR renders). 4 caption options; **first option is always correct** (upstream convention). ⚠ COCO/GQA-spatial subsets deferred to M3 (need COCO/GQA corpora) |
| CV-Bench (`nyu-visionx/CV-Bench`) | ✅ Apache-2.0 | `cvbench` | 2,638 | 394 M | 2D (Count/Relation) + 3D (**Depth/Distance** — our primitive). Images embedded in parquet; target objects drawn as red/blue boxes |
| VSI-Bench (`nyu-visionx/VSI-Bench`) | ⛔ **SKIPPED** | — | — | 0 | ReVSI ships its own videos + corrected annotations, so the raw benchmark adds 5.7 GB for nothing |
| **ReVSI** (`3dlg-hcvc/ReVSI`) | ✅ Apache-2.0 | `revsi` | 6,158 | 9.1 G | **Video.** Pre-sampled per frame budget (16/32/64/all); frames decoded **lazily** via PyAV. Numeric + MCQ answers |
| MindCube (`MLL-Lab/MindCube`) | ✅ MIT | `mindcube` | 1,050 (tinybench) | 1.3 G | **Multi-view** (4 images/item) — the dataset that forces the list-valued `images` interface. Options inline in the question |
| CausalSpatial (`Mwxinnn/CausalSpatial`) | ✅ MIT | `causalspatial` | 1,541 | 2.4 G | ⚠ **Two schemas**: 4 sim subsets have options inline + letter answers + a `not_sure` abstain option; `realworld` has an explicit options list + text answers. Adapter normalises both |
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

## 3. Core data schemas (freeze these in M0)

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

**Pooled activation cache (per model × stimulus set):** one `.npz`/safetensors per layer-site or a single zarr store; TWO variants per site — (a) mask-pooled per-object `[n_images, n_objects, hidden_dim]`, (b) all-token/strip-level pooled `[n_images, n_strips, hidden_dim]` (spatial signal is distributed across background tokens — Cui et al. v2; object-pooled-only caching would silently bias M5 toward "metric absent"). Sites: {`enc_out`, `proj_out`, `lm_vis_L{k}`, `lm_txt_L{k}`} (strip variant applies to visual-token sites). Plus `meta.parquet` (image id, object id, all geometry targets, factors). fp16. Target: ≤ 1 MB/image/model total.

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

### M3 — Reproductions (load-bearing gate)
1. **Kang reproduction (reimplemented):** mirror-swap activation patching + spatial-ID derivation + steering on LLaVA-1.5-7B and Qwen2.5-VL-7B, using their data-engine recipe (tile two objects on grid; COCO-Spatial from downloaded COCO). Pass bar: steering belief-swap ≫ noise control, direction of all key effects matches paper (~64% vs ~30%; exact numbers within a few points).
2. **Wang & Gao pattern reproduction:** mask-pooled object tokens on our M1 stimuli, ridge probes for x/z/pairwise distance + color/shape. Pass bar: pattern match — semantics ≫ metric; x ≈ chance; z modest.
**Accept:** a short internal report (numbers table vs paper) committed to `reports/`. **If either fails after honest effort, STOP and rethink framing before Phase 2 — this is the project's go-gate.**

### M4 — Full stimulus battery + extraction pipeline
1. Generator v1: conflict conditions (fixed-retinal-size, elevation-conflict), canonical-object set (import a few CC0 models: chair, mug, bottle) alongside primitives, question templates per taxonomy level (qualitative / ordinal / ratio / absolute) with balanced answer keys. Scale: ~5–10k images per config decision.
2. `extract/`: generic HF-VLM wrapper (LLaVA-1.5/1.6, Qwen2-VL, Qwen2.5-VL-7B, **Qwen2.5-VL-3B**, InternVL, Gemma-3) with named hook sites {enc_out, proj_out, lm_vis_L*, lm_txt_L*}; mask-pooling (coverage-weighted, per Wang & Gao's method — reimplemented) and object-word token extraction (needs tokenizer-aware span finding); writes §3 caches; per-batch checkpointing + `--resume`.
   **Paper-2 forward-compatibility:** include both Qwen2.5-VL-7B and -3B Instruct in the model list — they are the shared bases of the planned method-audit checkpoints (Paper 2: SpaceR + ViLaSR on 7B; SpatialLadder + SpaceQwen/SpaceOm + Spatial-MLLM on 3B), so every Paper-1 measurement on them doubles as the audit baseline. The wrapper must accept arbitrary HF checkpoint paths of the same architecture (base vs fine-tune swap = config change only).
**Accept:** full battery cached for 2 models overnight on one A100; cache size within budget; pooling unit tests green; resume-after-kill verified.

### M5 — Probing & the core result (Phase-2 science)
Probe runner: for every (model, site, layer, target, axis) → ridge/logistic with 5 seeds × 5 splits, shuffled-label control, selectivity contrast (qualitative vs metric), rank-correlation metrics; verbalized-answer collection on identical stimuli (+ few-shot calibrated variant + oracle-text condition); anchor experiment (scenes ± known-size reference object).
**Dataset usage rules (§2.5) apply here:** call `assert_behavioral_safe(name)` in the
verbalized-answer collector (DepthCues is PROBE-ONLY — probe `meta.label` only, never score
its synthesized questions); and state the MindCube split + ReVSI frame budget **explicitly**
in the experiment config, reporting ReVSI at **2–3 budgets** since its conclusions change with
the budget.
**Adopted standards (from Dual Mechanisms v2, 2603.22278v2):** (a) probe BOTH mask-pooled object tokens AND all-visual-token / strip-level representations — their central negative control shows spatial signal is distributed across background tokens, so object-pooled-only probing underestimates what survives (M4's cache must store an all-token pooled variant per layer too); (b) two-ordering strict protocol for all verbalized MCQ answers (ask both option orders, correct only if both pass); (c) random-direction nulls for any steering/injection; (d) report fixed-α and per-example-α (Probe*) intervention variants. Outputs: tidy parquet (§3) + the Figure-1 plotting script (decodability profile across sites/layers vs verbalized accuracy).
**Accept:** full grid runs from cached features on CPU in hours; every plotted number traceable to config+seed; positive control (qualitative) shows the Kang-consistent profile.

### M6 — Interventions (Phase-3, spec later)
Placeholder: continuous metric-ID injection (graded steering, dose-response curves), binding-layer LoRA + metric auxiliary loss vs matched-budget SFT. **Do not design in detail until M5 results exist — the evidence chooses the intervention.**

### M7 — Paper 2 audit (post-deadline; keep in mind, don't build yet)
Comparative mechanistic audit of spatial-enhancement methods: run the M5 probing grid unchanged on public fine-tuned checkpoints vs their bases (7B: SpaceR, ViLaSR vs Qwen2.5-VL-7B-Instruct; 3B: SpatialLadder, SpaceQwen/SpaceOm, Spatial-MLLM vs Qwen2.5-VL-3B-Instruct) + inference-time scaffolds (scene-graph prompt, depth-map input, Set-of-Marks — implemented as prompt/input transforms in `eval/`). Per method, decompose: representation / binding / prior. Design constraint on earlier milestones: nothing in `extract/` or `probes/` may assume the checkpoint is a base model.

## 5. Known gotchas
- `bpy` wheels are Python-version-pinned (3.11); set `requires-python` accordingly, or isolate stimuli env from extract env (uv workspaces handle this).
- flash-attn under uv needs `no-build-isolation-package`; test in M0, not when a model demands it.
- Qwen2-VL M-RoPE and InternVL tiling mean "visual token ↔ image location" mapping differs per model — the mask-pooling module must own this mapping per model family, with a test per family (render a probe dot, check the pooled token responds).
- Gemma-3 / InternVL may need recent transformers; pin per-model versions in config if conflicts arise.
- LibreOffice-style "works on my machine": run everything through `uv run` — never a bare `python`.
- Monthly re-check: Metric VQA release; SynSpat3D dataset appearance; new papers citing the four anchors (biweekly).

## 6. Suggested vibe-coding session order
M0 → M1.1 (spike, decides renderer) → M1.2–1.3 → M2 (parallelizable, boring) → M3.1 → M3.2 (gate) → M4 → M5. One milestone per session; start each session by pasting this doc + `PROJECT_MEMORY.md`; end each by updating both with decisions made.
