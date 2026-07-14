# Project Memory — Kaho's VSR Research (last updated 2026-07-15)

*Orientation file for future sessions. Read this first, then `research_proposal_spatial_binding.md` (the plan) and `VSR_niches_critical_deep_read.md` (the literature analysis). Companion: `docs/vsr_landscape_v8.pptx` — Kaho's independent 19-paper landscape analysis (2026-07-05, predating this project), folded into these docs on 2026-07-15 (stage reframing, the S1.5 occlusion stage, the "isolated structured perception hurts" finding, the five definitions / capability levels / tensions vocabulary).*

## Who / context
- Kaho: master's student (also covering undergrad research continuity), CV/VLM/spatial reasoning focus; also interested in image generation and medical AI. Has a Notion paper database and paper-analysis skills (paper-deep-dive-notion, research-reading, research-paper-summarizer).
- Compute: lab A100 cluster. Video-scale work deliberately deferred (GPU cost).
- Private goal: CVPR 2027 (abstract deadline Nov 15, 2026 — ~18 weeks from July 8). **Deliberately omitted from the advisor-facing deck**; the pptx speaks in phases, not deadlines.
- Style preferences: concise and direct; Traditional Chinese whenever Chinese is requested; enjoys mechanistic interpretability but wants papers that also "make or improve" (Type-2: diagnose → repair), not interp-only.
- Tooling: **uses `uv` for Python** — all project setup should be uv-based (pyproject.toml, uv.lock, `uv run`), not pip/conda.
- Infra: lab server via SSH; **shared machine, no scheduler** (informal GPU coordination, no Slurm); **no container runtime installed** (could be added — prefer Apptainer over Docker if needed); OK to keep everything on the server. Not familiar with rendering tools — willing to learn; keep rendering-side complexity low.

## The project (settled — hypothesis wording REVISED 2026-07-15 after external review)

- **⚠ WORDING DISCIPLINE, project-wide: "becomes unavailable or unusable" — NEVER "is lost" / "is
  destroyed."** The loss vocabulary silently collapses **five mechanistically distinct
  possibilities** the whole design exists to distinguish: metric information may be **erased**,
  **recoded nonlinearly**, **detached from the object**, **present-but-ignored** by the answering
  computation, or **corrupted at verbalization**. Canonical statement: *"VLMs exhibit a robust
  qualitative–metric spatial asymmetry, but it remains unknown where metric fidelity becomes
  inaccessible to the downstream language computation: visual encoding, multimodal projection,
  object–token binding, or readout."*
- **S1's hypothesis, split in two (do not state it as one claim):**
  - **H1 — localization (primary):** metric variables remain **recoverable** in visual
    representations but lose **object-specific accessibility** when bound into language-token
    representations.
  - **H2 — mechanistic sub-hypothesis:** the binding transformation preferentially preserves
    low-dimensional **ordinal** structure while collapsing continuous magnitude.
- **🔴 DO NOT ARGUE "rank-3, therefore incapable."** Three continuous dimensions can carry arbitrary
  precision. The coarseness evidence is Kang's **discretized (4×4-bin)** ID derivation and Cui's
  ordinal-only codes — they **support H2 without proving it**. Candidate mechanisms stay open:
  discretization, effective rank under the data distribution, SNR, ordinal-preserving many-to-one
  maps. (The old memory line asserted "destroyed … coarse rank-3 channel" as settled fact. It was
  neither.)
- Positioning: DepthCues + Ill-Posed by Design establish the endpoints; Kang 2601.12626 and
  Wang & Gao 2605.07148 constrain the middle. We localize where metric becomes inaccessible. NOT
  claiming "present but unverbalized" — Wang & Gao contradict that raw form. **⚠ And state DepthCues
  precisely: it shows depth-RELATED information is *recoverable* from encoders — NOT that "the metric
  signal exists" there.** Do not overclaim it; the image-identifiability gate is what licenses any
  "the encoder had it" claim.
- S1 design (the visible-metric stage): ordinal/ratio core (absolute secondary, prior-contaminated per ReVSI); factorial synthetic stimuli decorrelating depth × vertical position × size across **THREE regimes** (natural-congruent / **counterbalanced ← the primary claim lives here** / conflict); **five-functional-stage** probing grid (encoder → interface → early multimodal LM → object-conditioned language → answer/readout); probe-vs-verbalization with rank correlations + calibrated baseline + oracle-text; **anchor experiment (promoted to core — it IS the prompt-conditioned binding test)**; continuous metric-ID injection with dose-response + the full anti-logit-hack control battery; binding-layer LoRA vs brute-force SFT at matched data; validation via a **small, CLOSED, predeclared** external set (see dataset rules) + task-level oracle injection.
- **Models — MINIMAL PUBLISHABLE CORE, not 4–6 everywhere (revised 2026-07-15):** core = **2 architectures**, Qwen2.5-VL-7B (M-RoPE) + LLaVA-1.5-7B (classic CLIP), both already cached. One metric variable (egocentric depth), one qualitative positive control, five stages, one behavioral test, one intervention. **Expansion to 4–6 (InternVL/SigLIP, Gemma-3, Qwen2-VL) happens ONLY after the site-wise pattern stabilizes on two.** (Qwen2.5-VL-3B stays cached for S2 forward-compatibility but is **outside the core analysis matrix**; InternVL3-8B, used in M3.2, likewise.)
- Simple tasks for mechanism; complex benchmarks only as validation layer (composition-interp = future work).

## The research program — STAGES, not papers (reframed 2026-07-14; program frame added 2026-07-15)

### Program frame (adopted 2026-07-15 from the second external review)

- **Canonical program question** (replaces the old enumerating sentence): ***"How is object-specific
  spatial state represented, transferred, and causally used across multimodal model computations?"***
  — tested under four increasingly demanding information conditions: **visible / partially occluded /
  previously-visible-now-absent / hypothetical.**
- **Program hypothesis — DE-DIRECTIONALIZED.** The old "progressive loss" phrasing **prejudged the
  later stages**, which exist precisely to find out. Correct form: *"Spatial failure is not a unitary
  absence of geometry. It can arise because spatial information is weakly encoded, loses
  object-specific structure during multimodal transfer, remains represented but inaccessible to the
  relevant readout, or is not causally used. The program localizes these failure modes across
  visible, occluded, absent, and hypothetical spatial states, then tests whether interventions repair
  the responsible transition."* **S1 keeps its directional claim (H1/H2) as a STAGE hypothesis — it
  is not the program's.**
- **Evidential ladder (program-wide):** `representation ⊂ accessibility ⊂ task-relevant causal use`.
  "Spatial understanding = causal use" is **qualified to *task-relevant* causal use**: *the
  represented variable causally contributes to the corresponding output under controlled
  intervention.* ⚠ Failure of **one** answering pathway ≠ absence of understanding in every sense —
  that overclaim is exactly what S3 exists to test.
- **THE PROGRAM CUBE — the canonical organizing figure and the thesis structure.** Every stage
  occupies a **declared region** of:
  **Axis A — information condition** {visible / occluded / absent / hypothetical} ×
  **Axis B — computational transition** {encoding / interface / binding / readout / memory / generation} ×
  **Axis C — evidential level** {decodable / object-specific / accessible / causally used / repairable}.

### The stages

**This is ONE program.** It is organized as **dependency-gated stages**, not as papers or degree
chapters. **Publications are snapshots of whichever stages have defensible results when a deadline
passes; degree documents are bindings of completed stages.** The private CVPR 2027 target is
unchanged — it simply does not structure the science. ⚠ **Do not reintroduce "Paper 1 / Paper 2 /
Paper 3 / PhD direction" labels.**

**⚠ Maturity labels are MANDATORY wherever the stages are described** — they stop a long-horizon
agenda from being read as a queued experiment.

| Stage | Question | Unlock gate | Maturity / status |
|---|---|---|---|
| **S1 — Visible metric** | where metric fidelity becomes inaccessible to the language computation | M3 GO ✅ | **executable paper plan** — running; M4 is the real gate |
| **S1.5 — Occlusion & the amodal probe** | is the hidden part represented, object-specific, and bound? | **M4b** clears the transferred W&G bar | **well-formed extension** — spec'd as milestone **M4.5** (plan §4) |
| **S2 — The method audit** | what do spatial "fixes" actually change? | S1's probes + baselines exist | **strong next-paper candidate** (M7) — stays ahead of S3 unless S1 yields a strong readout-specific result |
| **S3 — Other readouts (generation)** | does the generation pathway read the same spatial code? | an S1 finding (S3 tests it) | **comparative framework needing operational definitions** — parked |
| **S4 — The unseen** | what is maintained about what cannot currently be seen: occluded (by things), out-of-view (by framing), future (by time) | S1.5's amodal result | **long-horizon agenda — THREE candidate projects, not one experiment.** Do not build |

**Stage notes (the facts each stage was built on — keep these, they are verified):**
- **S1.5 (new 2026-07-15; the cue claim CORRECTED the same day — see below).**
  **H-occ:** occlusion is **primarily an ORDINAL VISIBILITY cue** — it identifies front–behind
  ordering more directly than continuous magnitude. **Over-reliance on it *could* support qualitative
  depth while leaving metric depth poorly represented.** That is the mechanistic form of the
  qualitative-vs-metric asymmetry, and it is testable inside the existing cue-decomposition design.
  (Landscape Tension **T2**, geometry vs visibility-aware state, made mechanistic.) Full spec:
  IMPLEMENTATION_PLAN **M4.5**.
  - 🔴 **RETRACTED, do not restate (it was in these docs for one day):** *"occlusion is the only
    **categorical** cue, carrying **zero metric content**, therefore their best cue **cannot** carry
    metric information."* **False as stated.** T-junctions, containment and support are **also**
    ordinal cues (so it is not the only one), and occlusion boundaries combined with known shapes and
    camera geometry **do** constrain metric depth (so "zero metric content" is wrong). The seductive
    part was the *deduction* — it made the program's central asymmetry look like it followed from a
    definition. It doesn't; it has to be measured. **Weaken to "primarily ordinal / over-reliance
    could…" and keep it a hypothesis.**
  - **The amodal question splits into THREE — do not conflate them:** **H1.5a object persistence**
    (an entity-level representation survives partial visibility) / **H1.5b amodal geometry** (hidden
    extent recoverable *beyond* visible-fragment features) / **H1.5c amodal binding** (available at
    object-referential tokens).
- **S2 — the spatial-method mechanistic audit (Kaho's idea).** How do existing spatial-enhancement
  methods (data-SFT, RL-tuned, inference-time scaffolds like scene-graph / depth-input / SoM) change
  internal behavior?
  - **⚠ The three-way label (representation / binding / prior) is REPLACED by a FIVE-DIMENSIONAL
    MECHANISM PROFILE — a vector per method, not a category** (the categories are **not mutually
    exclusive**, and forcing a method into one was going to manufacture false clarity):
    **ΔR_visual** (upstream representational gain) · **ΔR_bound** (object-specific transfer gain) ·
    **ΔB** (readout gain *conditional on matched internal decoding*) · **ΔP** (prior reliance, under
    blind / black-image / geometry-conflict controls) · **ΔC** (causal repair: mediation +
    specificity). **Report the vector.**
  - **⚠ CHECKPOINT COMPARABILITY CHECKLIST — run before ANY base-vs-finetune internal comparison:**
    tokenizer · image resolution · prompt/conversation template · preprocessing · transformers
    revision. A mismatch on any one of these produces a "mechanistic difference" that is a pure
    artifact — and this audit's entire signal is a *difference between checkpoints*.
  Ties to ReVSI's behavioral debunking (fine-tunes lose gains
  under corrected eval); scaffold analysis would mechanistically explain the C-niche convergent fact
  (verbalized cues barely help). Reuses ~90% of S1's infra. **Verified 2026-07-09:** 2511.11440
  deep-read — LM-layers × final-question-token probes on their own synthetic-SFT only, single toy
  task; comparative audit / site decomposition / scaffolds all NOT covered → the idea is open; cite
  and differentiate. Checkpoint audit set confirmed public with matched bases: SpaceR + ViLaSR (both
  on Qwen2.5-VL-7B-Instruct); SpatialLadder + SpaceQwen/SpaceOm + Spatial-MLLM (all on
  Qwen2.5-VL-3B-Instruct); VLM-3R vs LLaVA-Video-7B-Qwen2 optional second-architecture case. Skip
  Cambrian-S (no untouched base), SVQA-R1/SpatialVLM (no checkpoints).
  - **🔑 The behavioral mystery S2 exists to explain (from the landscape deck, added 2026-07-15):
    ISOLATED STRUCTURED PERCEPTION *HURTS*.** Four independent papers report it — EmbodiedVSR
    (detector / depth / graph alone each *degrade* performance), SpatiaLQA (segmentation alone
    67.4 → **50.3**; depth alone → **64.1**), NuScenes-SpatialQA, ISGR. Giving a VLM a *correct*
    structured spatial input makes it *worse*. That is a purely behavioral fact with no mechanism
    attached, and the audit's scaffold probing is exactly the instrument that can settle it: **does
    isolated structured input never reach the binding sites, or does it actively interfere there?**
    → cite these four in the audit's motivation, and carry **"isolated vs integrated scaffold"** as
    an audit condition axis (scene-graph-alone vs depth-alone vs integrated), mirroring their
    behavioral contrast.
- **S3 — generation.** Understanding↔generation gap in unified models: Janus-Pro (decoupled control),
  Emu3.5 (shared AR), BAGEL (hybrid). Parked (it is a *test of S1's prediction*, so it cannot run
  before S1 has one).
  - **⚠ Hypothesis SYMMETRIZED to branch-point localization (2026-07-15).** The old "generation
    suffers less from lexical binding loss" **prejudged the answer**. Correct form: *"If failure
    originates BEFORE the shared representation, both pathways fail on the same relations; if it
    originates DURING task-specific binding/readout, failures DISSOCIATE after the branch point."*
    The "generation suffers less" line survives only as a **derived corollary, conditional on S1's
    finding.**
  - **Probe transfer needs a three-level definition** (it was hand-waved as one thing): **decoding
    transfer** / **subspace alignment** / **causal direction transfer** (strongest, hardest).
  - The deck's application **C2** — T2I evaluation leans on VLM judges whose spatial verification is
    itself unproven — is **independent motivation** for the judge-circularity methodology spec'd here.
- **S4 — the unseen. A RESEARCH FAMILY of THREE BRANCHES — exactly ONE becomes the next project,
  selected by earlier results.** (Labeling it one experiment was the error; it is an agenda.)
  - **S4-A — hidden extent & the visibility graph.** ⚠ **State it NEUTRALLY — do not presuppose the
    negative:** *"models may encode scalar visibility attributes without maintaining relational
    occluder–occludee structure — we test whether pairwise structure is represented, bound, and
    used."* **Physically rendered occlusion CHAINS are primary**; inverted-depth composites are **one
    conflict regime only** (compositing-artifact confound; they break the exact-geometry guarantee).
  - **S4-B — persistent spatial memory:** out-of-view objects; multi-image guaranteed-evidence
    protocol (decay vs interference vs never-encoded vs readout — DISJOINT-3DQA precedent);
    KV-cache-as-memory probing. Video deferred (GPU cost).
  - **S4-C — hypothetical spatial state:** does the model internally represent predicted future
    positions before verbalizing? (CausalSpatial-level simulation; humans 84% vs GPT-5 54%.)
  - The umbrella **"representation of the unseen"** spans the deck's capability levels 4–6
    (visibility/permanence → dynamic state → counterfactual). It unlocks on S1.5's amodal result: if
    the hidden part of an object is not represented at all, there is nothing for a visibility graph
    to be made of.
- **Method harvest** (byproduct, not a goal): continuous causal mediation, probe-transfer measure,
  hypothetical-state probing.

### Framing adopted from the landscape deck (2026-07-15) — use this vocabulary in the proposal
- **Five definitions of "spatial understanding"**: behavioral / decodable / **causal use** /
  transfer / world-modeling. **Causal use is this program's operational definition** — the
  pre-existing commitment; the stages *operationalize* it (a probe that reads a quantity the model
  never uses is not understanding).
- **Capability levels**: perception → relations → geometry → visibility → dynamic state →
  counterfactual. This is the map of which stage addresses which level: **S1 = 1–3; S1.5 = the
  entry to 4; S4 = 4–6.**
- **Tensions**: **T1** representation vs interface → S2's core question. **T4** decodability vs
  causal use → S1's probe+injection pairing. **T2** geometry vs visibility-aware state → S1.5/S4.

## Dataset usage rules (set at M2 — SCIENTIFIC constraints, enforced in code; see plan §2.5)
- **Split/frame-budget is an experiment parameter, never a loader default.** MindCube defaults to `tinybench` (1,050 vs the full ~21k) and ReVSI to the **32-frame** budget — dev-speed conveniences only. Any *reported* result must set them explicitly in the experiment config. Both adapters now log the value (flagging when it's a default) and record it per item (`meta.split`, `meta.frame_budget`). **ReVSI's entire thesis is that conclusions change with the frame budget — the paper should report 2–3 budgets (16/32/64), not one.** A single-budget result is provisional.
- **DepthCues is PROBE-ONLY: it must never appear in a behavioral claim.** No task text exists in it; its "questions" are OURS and its "answers" are raw regression/binary labels. Scoring a model's verbalized accuracy on a question we invented measures nothing. `datasets/base.py` classifies every dataset (`NATIVE_QA` / `NATIVE_TASK` / `PROBE_ONLY`) and `assert_behavioral_safe()` raises on PROBE_ONLY — **call it at the top of every eval/scoring entrypoint (M5, M7).**
- **Important distinction the `meta.synthesized_question` flag is too blunt to make: What'sUp IS behavioral-safe.** Its *task* and answer key are native (choose the correct caption of four); only our prompt *wording* is synthesized — it is the qualitative positive control. DepthCues has no native task at all. Conflating the two would either wrongly bar What'sUp or wrongly admit DepthCues.
### 🔬 GROUND-TRUTH DATASET INSPECTION (2026-07-15) — the validation layer, corrected

**Standing rule, reinforced: a dataset enters an experiment only after ITEM-LEVEL inspection** (rows,
templates, per-category counts, answer-format quirks). **Paper descriptions AND our own adapter counts
are hypotheses.** Proof that this is not paranoia: What'sUp-B's 204 depth items and MindCube's total
unsuitability were **both invisible** from the dataset descriptions we had been working from.

- **🎁 What'sUp subset B contains 204 FRONT/BEHIND items — a qualitative-DEPTH control we already
  owned and never noticed.** *(Verified locally by full scan, 2026-07-15: subset B = 408 items,
  `left_of` 102 / `right_of` 102 / `in-front_of` **102** / `behind` **102**. Subset A = 412 items,
  `on` / `under` / `left_of` / `right_of`, **103 each**.)* B gives **categorical depth relations to
  contrast against metric depth**. ⚠ **Caveat to carry:** per Kang, front/behind may be answered via
  the **vertical proxy** (in tabletop scenes, front ≈ lower) — so B is proxy-confounded. Treat it as
  a **behavioral** control. *And note the proxy story is exactly what our S1 probes can test* — the
  confound is an experiment.
- **CV-Bench 3D: FITS, with three caveats.** Depth (600) is verbatim our ordinal primitive; Distance
  (600) is also ordinal (object-anchored). **ZERO absolute-metric items — never describe CV-Bench as
  metric validation.** Binary choices → 50% chance → **two-ordering protocol mandatory**.
  ⚠ **Source mix, measured in OUR copy (full scan, 2026-07-15):** `Omni3D_Hypersim` **400** /
  `Omni3D_SUNRGBD` **400** / `Omni3D_nuScenes` **400**, i.e. exactly 200 per (task × source) —
  **33.3% photorealistic SYNTHETIC** (Hypersim), 66.7% real-sensor. So: **report per-source, and do
  not call CV-Bench "real-image validation" without qualification.** (2D is COCO 805 / ADE20K 633.)
  ⚠ **The third source is nuScenes, NOT ARKitScenes** — ARKitScenes appears in *SpatialRGPT-Bench's*
  Omni3D slice, a different dataset. Do not conflate them.
- **ReVSI is the validation workhorse.** Its 13 question types tag cleanly onto primitives: 4
  absolute-metric (distance m / size cm / room m²), 2 ordinal (rel-distance closest/farthest, 4-way),
  4 egocentric-qualitative (perspective-taking), 2 counting, 1 other (route). Numeric types scored by
  **Mean Relative Accuracy** (0.5–0.95 thresholds). ⚠ **Type mix VARIES by frame config** (16f drops
  room-size + route-planning) — fix the config per analysis. ⚠ Add **video/cross-frame as a nuisance
  covariate**: every ReVSI item stacks cross-frame memory *on top of* the primitive.
- **🔴 MindCube: POOR FIT — REMOVED from the S1/M5 validation layer.** Every inspected item is
  multi-view perspective-taking under stated camera motion (rotation / among / around); **nothing
  reduces to a single-image primitive**, and its own eval excludes the `translation` setting.
  Re-scoped to a **cross-view integration contrast (S4-adjacent)**. **The adapter stays — nothing is
  wasted, and §2.5(a)'s split-is-a-parameter rule remains in force for any future MindCube use.**
- **CausalSpatial: use the collision (n=826) and occlusion (n=189) slices ONLY** for
  primitive-predicts-failure analyses. Compatibility (n=99, size-ratio) and realworld (n=116) are too
  small for per-category stats; physics (311) loads on **physics priors**, not spatial primitives —
  keep both as **non-target controls**. ⚠ Record their own admission: **sim scenes' "floor strip
  spacing encodes depth perspective"** — the depth cue is *artificially legible*, so caveat any
  cross-dataset comparison.
- **🆕 NEW DERIVED DATASET — ReVSI-1F (decided 2026-07-15).** ReVSI is video, and **cross-frame demand
  varies BY CATEGORY** — which confounds primitive-difficulty with memory-difficulty (and LLaVA-1.5
  is not a video model at all). Derivation: from `obj_visibility.json` *(verified present in our copy
  at `external/revsi/metadata/obj_visibility.json`)*, keep items where **all** `queried_object_ids`
  are co-visible in ≥1 frame; select the frame maximizing the **minimum** visible-pixel count across
  queried objects (tie-break earliest; seeded; rule in config). Emit `revsi_1f/` with original item
  id + chosen `frame_idx` + per-object visibility stats + primitive tag. ⚠ **Report per-category
  SURVIVAL RATES — the co-visibility filter drops categories unevenly, and that selection bias must
  be stated, not buried.** Validate with counts + contact sheet. Internal instrument (Apache-2.0
  permits); if ever released, ship **the script + index, not frames**.
- **✅ VALIDATION LAYER, FINAL (all single-image):** CV-Bench Depth/Distance (ordinal) + **What'sUp-B**
  (qualitative-depth control) + **ReVSI-1F** (ordinal + absolute, human-verified GT) +
  **SpatialRGPT-Bench distance slice** (absolute, sensor GT) + CausalSpatial collision/occlusion
  (consequence-level). **The list is CLOSED and predeclared** — not extensible mid-project. Full-video
  ReVSI at 2–3 budgets = a **labeled extension analysis**, not the core.
- **SpatialRGPT-Bench — ADD, WITH CAVEATS** (`a8cheng/SpatialRGPT-Bench`, HF, ungated, val only).
  ⚠ **NOT YET DOWNLOADED — every count below is from the advisor's item-level inspection and must be
  re-verified locally against the actual files before use** (rule 4: an upstream field is a
  hypothesis; this dataset has already burned us once in spirit — see CausalSpatial). Claimed: 1,406
  rows = 657 qualitative + 749 quantitative; GT from **Omni3D real 3D cuboid annotations**
  (SUNRGBD-dominant, ARKitScenes, nuScenes, KITTI, Hypersim) — **sensor/synthetic GT, not
  monocular-pseudo-GT**, so it shares no failure modes with the models we evaluate. But QA generation
  is **templated with no human-verification pass** → GT tier: *below* ReVSI's human re-annotation,
  *above* auto-pseudo-GT.
  - **Core signal = the ~375 inter-object DISTANCE items** (direct/horizontal/vertical) — absolute
    metric, **the type CV-Bench entirely lacks**. There is **no ratio type** and **no
    closer-to-camera type**.
  - ⚠ **Width/height items are PRIOR-CONTAMINATED:** blind GPT-4 (no image) scores **48–52% within
    ±25%**. Always report a **blind-LLM baseline** alongside; treat as secondary.
  - Evaluate generic VLMs with **SoM-drawn marks** (their own baseline protocol), **never text
    referral** (it breaks on same-class regions); bboxes + RLE masks ship in the JSON.
  - **Replace their GPT-4 judge** with deterministic number-extraction + configurable relative-error
    thresholds; report **±10% and AbsRel** alongside their lenient ±25%. The unit lottery
    (in/ft/cm/m) makes exact match meaningless.
  - ⚠ **License murky** (GitHub says Apache-2.0, HF card untagged, nuScenes/KITTI upstream
    non-commercial) → **internal eval use only**.

- **REPORT THE NOT-SURE RATE wherever an abstain option exists (added 2026-07-15, from the landscape deck's CausalSpatial read).** CausalSpatial's own scaling analysis finds **NSR collapses with model scale (18.77% → 0.10%) while accuracy stays flat** — i.e. *larger models become decisively wrong*, not more right. Accuracy alone hides that entirely. The adapter already carries `meta.not_sure_letter` (derived from the option TEXT, since the upstream column is a lie — see the second retro-audit), so NSR is free to compute: **report it as a metric alongside accuracy in the M5 validation layer.** Two further details from the same read, worth holding: **COW (their video-sim method) FAILS on its own occlusion task** — useful context for when our oracle-injection helps or doesn't; and **scale saturation** (Qwen3-VL 4B/8B/30B plateau at 44–46%) — a model-scale claim our per-primitive decomposition can actually speak to.

## M4 design constraints (inherited from M1 — read before building the conflict conditions)
- **⚠ `fixed_retinal_size` condition must NOT define "retinal size" as mask AREA.** A cube's mask area varies **±11% with pose/depth** (a nearer cube shows more of its faces; measured cube-as-far ∈ [139863, 171495] vs cube-as-near ∈ [148480, 182933] for `area×depth²`). So "equal retinal area" is not well-defined without also fixing pose. Two acceptable routes: **(a) define retinal size as mask HEIGHT** (`retinal_size_px`, which the M1 calibration equalises across shapes to `height×depth` ≈ 407 — pose-stable), or **(b) control pose explicitly (fixed yaw per object)** and only then use area. Do not silently mix the two.
- The `size_condition` factor owns **independent per-object size jitter**; the congruent condition deliberately gives both objects of a pair ONE shared multiplier (independent jitter is precisely how you invert the retinal cue on purpose).
- `cue_constants` in `configs/stimuli_v0_congruent.yaml` records the measured fill factors, `height×depth`, `area×depth²` (split by near/far role) and per-pairing required depth ratios — the numbers a conflict design needs to invert a cue by a *known* amount.
- Anything M4 adds (new primitive, new pose freedom, per-object size jitter) **invalidates the M1 calibration and the 1.158 area threshold** — recalibrate (`scripts/calibrate_sizes.py`) and re-derive the thresholds from worst-case constants.

### Forward constraints from S1.5 / M4.5 (added 2026-07-15) — M4 should not paint itself into a corner
M4.5 (occlusion) runs only AFTER **M4b** passes the transferred W&G bar, but two of its needs are cheap
to accommodate now and expensive to retrofit:
- **The amodal mask is nearly free — take it.** The composite ID pass gives the *visible* mask
  (current pipeline); rendering each object **alone** in a solo ID pass gives the **amodal** mask
  for the cost of one extra tiny render per object. Schema additions M4.5 needs per object:
  `mask_amodal`, `occlusion_ratio` (= 1 − visible_area / amodal_area), `retinal_size_px_amodal`.
- **⚠ The congruence validators will FALSE-ALARM on occluded objects unless exempted.** The
  *visible* height/area of an occluded object is **not the calibrated quantity** — check retinal and
  area congruence on the **AMODAL** measurements instead. Write the exemption into
  `scripts/validate_stimuli.py` explicitly (as a recorded exemption, never a silent skip — CLAUDE.md
  rule 3), and note that adding the occlusion factor triggers the recalibration rule (M4 note (e))
  like any other new degree of freedom.
- **The leak ceiling extends too:** for occluded items the dumb-features baseline must include the
  **visible**-mask geometry AND `occlusion_ratio`. An amodal-decodability claim (H1.5b) has to beat a
  probe that only ever sees the visible fragment's geometry — otherwise "the model completes the
  object" is just "the fragment's shape told us".
- **🔴 BUT: do NOT plan on amodal-extent POOLING as the test (corrected 2026-07-15).** The first
  version of this note called "pool over the visible mask vs the amodal extent" a measurement detail
  that *is itself a finding*. It isn't — **pooling under the invisible mask mostly collects OCCLUDER
  and BACKGROUND tokens**, so a null there measures the occluder, not the object. **Do not assume
  hidden geometry is spatially stored under the hidden mask.** Test *implicit* representation instead:
  **visible-fragment pooled / occluder-region / object-name token / joint decoder conditioned on
  object identity.** Amodal-extent pooling survives only as a *labeled naive baseline*.

## 🚦 M3 — THE GO-GATE (2026-07-14). Full report: `reports/m3_reproduction.md`

### ✅ GATE DECISION: **GO** (advisor review, 2026-07-14). Phase 2 proceeds.
- **M3.1 is sufficient.** The binding-bottleneck design needs the mechanism to *exist and be
  steerable*, not a 64% swap rate. Log it and build.
- **Do NOT re-run Wang & Gao on v0.** The diagnosis is complete; v0 cannot support the
  measurement by construction. Re-running it would be theatre.
- **M3.2's pass bar TRANSFERS to M4 as an acceptance criterion:** *"the W&G pattern emerges —
  semantics ≫ metric, difficulty gradient present, measured ABOVE the leak ceiling."* If the
  decorrelated M4 battery still gives R² ≈ 0.99 everywhere after the leak controls, the stimuli
  are still broken and **M5 does not start**. When the gradient appears, the instrument is
  finally measuring models instead of itself. **M4 is now the real gate on Phase 2.**

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
  matches or beats theirs (+31.3 pts at α=5, **+43.3 pts** at peak, vs their +34.9).
  **⚠ The obvious explanation is WRONG and we measured it.** "Our models are more certain, so
  noise can't flip them" does NOT survive: noise flips **0.0% in EVERY confidence bin** (0/23 at
  conf 0.90–0.99; 0/7 at 0.70–0.90), and spatial-ID flip rate is **uncorrelated with confidence**
  (r = +0.03). What *is* defensible: **our task produces almost no uncertain beliefs at all**
  (mean conf 0.973; only 11/150 below 0.9), and a noise control can only flip a belief near the
  boundary. That is a statement about **stimulus difficulty**, not model certainty. **The
  noise-floor gap remains UNEXPLAINED** — it does not threaten the mechanism, and we do not dress
  it up. Report the mechanism; do not claim the magnitudes.

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

### 🔴 THE POSITION LEAK — a THREAT TO THE CORE EXPERIMENT, not a probe caveat
**Mask-pooling from position-indexed visual tokens LEAKS POSITION BY CONSTRUCTION** — the pooled
vector averages tokens *at the object's image location*. **The selection IS the answer.**

**Measured leak ceiling on v0 (dumb features, NO activations, no model at all):**
| target | mask **geometry alone** | mask-pooled activations | model adds |
|---|---|---|---|
| x (lateral) | **R² = 0.942** | 0.997 | +0.055 |
| x from the mask centroid *u* **alone** (one number) | **R² = 0.943** | — | — |
| z (depth) | **R² = 0.972** | 0.990 | +0.018 |

**Why this is bigger than M3.2.** Mask-pooled *visual*-token probes inherit the leak;
*bound-text-token* probes do not (they are not selected by image position). So the probing grid's
central contrast — **visual stages high, text stages low** — **could be manufactured by the
measurement itself.** That directly threatens telling **Prediction 1** (metric survives in visual
tokens, becomes inaccessible at binding) from **Prediction 2** (metric was never there). **This is the single most
important thing M3 produced.**

**THREE controls are mandatory for Phase 2, not one:**
1. **Dumb-features leak ceiling** — every claim at every site must EXCEED a probe on mask geometry
   (+ shape/colour/cue values). Below the ceiling it is in the mask, not the representation.
2. **Fixed-grid STRIP probes are PROMOTED to the primary leak-free estimator** — strips are not
   selected by object position, so they cannot leak via selection. (We adopted Cui et al.'s strip
   variant as an "underestimation guard"; it is now load-bearing.) ⚠ **`strip_pool()` exists in
   `extract/pooling.py` but M3.2 cached mask-pooled features ONLY — M4's cache must produce both.**
3. **Camera-pose jitter at the SOURCE** — and this explains the W&G discrepancy cleanly: their
   scenes vary camera path, so camera-frame coords are not image positions. Our fixed camera makes
   x **identical** to image position (hence R²=0.997 measuring the pooling). Jitter kills the leak
   where it is created rather than correcting after the fact.
(+ Wang & Gao's cross-scene residualization of the semantic subspace, as an orthogonal fourth.)

### 🔑 STANDING METHODOLOGY: every probe ships a DUMB-FEATURES BASELINE (adopted 2026-07-14)
A shuffled-label control catches a probe fitting *noise*; it cannot catch a probe reading a
trivially available **non-representational** feature. Two findings this session passed every
shuffled-label control: the **55.1% shape-only** depth-role imbalance, and the **R²=0.942 mask-
geometry** leak. Same failure class — *a confound that survives every unit test and dies only
under an adversarial baseline*. So: for every (model, site, layer, target), also fit on
`{mask geometry} ∪ {shape, colour} ∪ {cue values}` and report **Δ = probe − dumb ceiling**.
Decodability only counts above the ceiling. Now in CLAUDE.md as verification rule 12.

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
- **🔴 A NULL IS ONLY AS TRUSTWORTHY AS THE PROOF THAT YOUR INSTRUMENT CAN REGISTER A POSITIVE.**
  **This is the most dangerous failure mode left in this project.** Unlike an inflated positive, a
  null *feels* like honest science — it looks like rigour, it gets written up as a finding, and
  nobody interrogates it. Phase 2 is *made of* nulls ("metric is not decodable at site X", "steering
  does not transfer", "the fine-tune did not improve binding"). Every one of them must be
  accompanied by a demonstration that the measurement MOVES when it must.
  - *(M3: steering reported a clean 0.0% belief-swap for an hour, with a plausible story attached.
    The steering was fine — the READOUT was dead. `" left"` and `" right"` share their first token
    under the LLaMA tokenizer, so both options scored an identical logit and every belief came out
    exactly 0.5/0.5 — **even under zero-ablation**. Fixing that revealed a SECOND bug: LLaVA answers
    "Left"/"Right" (capitalised, carrying ~all the mass) while the lowercase forms sit at p≈2e-5, so
    the readout was reading the far TAIL of the distribution. Two independent silent bugs, both
    producing a confident, publishable-looking null.)*
  - **The check that caught it: zero-ablate the thing you are intervening on.** If destroying it
    does not move your metric, your metric is not measuring it. Now CLAUDE.md rule 11.
- **🔴 AN ARGUMENT THAT MAKES YOUR FINDING FOLLOW FROM A DEFINITION IS A BUG, NOT AN INSIGHT**
  (CLAUDE.md **rule 13**, added 2026-07-15). Every other verification rule in this project validates
  an **output**. **None of them can catch a bad INFERENCE** — and on 2026-07-14 we shipped one into
  two docs and a commit.
  - *The claim:* "occlusion is the only **categorical** depth cue, it carries **ZERO metric
    content**, **therefore** if VLMs lean on it their best cue *cannot* carry metric information — so
    the qualitative-vs-metric asymmetry follows **in principle**." Nothing was mis-measured. The
    **deduction** was wrong (T-junctions/containment/support are also ordinal; occlusion boundaries +
    known shapes + camera geometry *do* constrain metric depth) — and, worse, it was **shaped to make
    the program's headline result true a priori.**
  - **Why it got through:** it felt like insight *because it was cheap*. An argument that derives your
    central finding from a definition is the most seductive object in a research project, and it is
    exactly the one nobody stress-tests, because agreeing with it feels like understanding.
  - **The smell test: if the claim would survive even if every experiment came back null, it is not an
    empirical claim.** A result you cannot lose is a result you cannot earn.
  - **The controls:** any deduction load-bearing for a headline claim gets an **adversarial domain
    read before it enters a doc** (this one died in a single external review pass). Prefer the weak
    measurable form ("over-reliance on an ordinal cue *could* leave metric depth poorly represented")
    over the strong deductive one ("therefore it *cannot*"). And **when a claim is retracted, leave
    the retraction visible** — a silent deletion lets the same elegant argument walk back in next
    session.
- **A shuffled-label control is NOT enough — every probe needs a DUMB-FEATURES CEILING** (CLAUDE.md
  rule 12). The shuffled control catches a probe fitting *noise*; it cannot catch a probe reading a
  trivially available **non-representational** feature. Both of this session's worst findings passed
  every shuffled-label control and died only under an adversarial baseline: the **55.1% shape-only**
  depth-role imbalance, and the **R²=0.942 mask-geometry** position leak (a *single* number — the
  mask centroid — gives x R²=0.943; even SHAPE is 99.2% readable from geometry). Run
  `scripts/leak_ceiling.py` on any new stimulus set; decodability counts only *above* the ceiling.
  Sanity property of the method: it correctly returns **chance for colour**, which a mask genuinely
  cannot encode.
- **⚖ THE EVALUATION LAW, IN TWO CLAUSES (refined 2026-07-15 — the one place external review
  overcorrected, resolved by synthesis; CLAUDE.md rule 7 updated to match).** The worst-case rule was
  learned from a real failure and is **not** being softened where it was earned — but it was being
  applied to a second class of quantity where it is wrong.
  - **(1) DETERMINISTIC, CONSTRUCTIBLE quantities** (rendered geometry, cue constants, calibration
    thresholds): **WORST CASE, always. Never means.** The extremes are *measured exactly*, and means
    were the *proven* failure — the area-congruence threshold from mean constants was 1.096 when the
    true worst case (splitting the constant by near/far role, since perspective differs) was
    **1.158**; the mean-based floor (1.12) passed validation while holding by a 0.6% margin, i.e. by
    luck. Any "safe threshold" for a rendered quantity comes from the extremes of its measured
    distribution.
  - **(2) SAMPLED / STATISTICAL quantities** (probe scores, benchmark accuracies, per-category rates):
    **no aggregate threshold without checking the weakest PRESPECIFIED stratum**, plus condition-wise
    uncertainty (CIs, quantiles, failure-rate distribution). ⚠ **One noisy item must NOT define a
    gate** unless that is scientifically required — a literal worst-case rule on noisy data gates on
    the unluckiest sample, which is not rigour, it is noise-chasing.
  - **The distinction is the whole point: worst-case is about a quantity you CONSTRUCTED and can
    bound; strata-plus-CIs is about a quantity you SAMPLED and can only estimate.** Do not apply
    either rule to the other class.
- **Verify a guarantee empirically AFTER applying it — passing ≠ guaranteed.** Both the 1.074 (no floor) and 1.12 (mean-based floor) sets reported `area_congruence 0/500`. The check passed both times; the *margin* (worst-case near/far area ratio) was 1.006 both times, which is what revealed the floor had done nothing. Always measure the margin, not just the pass/fail count — a green check on a contingent property tells you nothing about whether it will stay green under a different seed.
- **Never trust a rendered metric without an invariant check.** The colour-keyed mask silently bled into bounce-lit floor for the entire first version of the generator (see the ID-pass bug above); it was caught only by asking "is a sphere as tall as it is wide?" Validate the metric itself, not just that the pipeline ran.
- **Field velocity is extreme**: the literature analysis was materially revised twice in one day by newly-found papers (Kang et al., then Wang & Gao / Ill-Posed by Design — the latter two found only after Kaho pushed to search newer work). **Rule: every specific design claim gets a verification search before being asserted or written.** Biweekly citation watch on 2601.12626, 2605.07148, 2606.24335, 2411.17385 (offered as scheduled task; not yet set up).
- Superseded ideas (don't re-propose): qualitative-direction steering, ordering-probe amplification (Kang/Dual Mechanisms territory); behavioral-only cue decomposition for size (Ill-Posed); new static benchmarks; "present but unverbalized" as stated.
- Must-reads before design freeze: Attention in Space (2603.20662), Why Far Looks Up (2605.30161), full Ill-Posed §6.6 + limitations; Echo-Memory (2606.09803) before any memory work.
- **🔴 MUST-READ BEFORE ANY M5 PROBE CLAIM — "Mirage Probes" (arXiv 2606.13870, Jun 2026), "How Vision Models Fake Visual Understanding".** A probing-*validity* critique: it bears on **every probe claim this program makes**, S1 included, not just the occlusion work. Read it *before* the M5 numbers exist, not after a reviewer cites it at us. **PRIORITY.**
- **Verification-reads before the M4.5 (S1.5 / occlusion) design freeze** — per the standing rule that every specific design claim gets a search before it is asserted:
  - **Mirage Probes (2606.13870)** — as above; the amodal probe is a probe claim like any other.
  - **arXiv 2508.04567** — masked-object linear probes (>95%). Check whether their "masked" ≈ our occlusion; if it is, our amodal claim needs to differentiate hard.
  - **arXiv 2603.28333** (MLLM-guided amodal completion), **O-Bench** (occlusion benchmark — steal its inverted-depth and answer-frequency controls), **CAPTURe** (amodal counting; oracle decompositions), **SpatialMosaic** (occlusion-ratio data pipeline — engineering reference for computing `occlusion_ratio`).
  - **Search to re-run at freeze time:** "amodal representation probing VLM occluded object depth". Checked 2026-07-15: **geometric probing of physically occluded objects appears OPEN** — the adjacent work is classification probes on masked objects, and amodal *segmentation*. Re-verify; do not assert the gap from this note alone.
- **Watch list additions (2026-07-15):** **Structural Graph Probing** (population-level neuron-correlation topology; its open question *"would spatial IDs appear as hubs?"* is adjacent to S1) — verification-read, low priority. **R3D (2607.02921)** — added to watch alongside the SpatialRGPT-Bench decision. Plus O-Bench / CAPTURe / SpatialMosaic as S1.5–S4 references, and the landscape deck's 19-paper corpus merged into literature tracking.
- Kang reproduction is load-bearing (code: github.com/Raphoo/linear-mech-vlms).
- **Dual Mechanisms v2 (2603.22278v2, Jun 2026, deep-read 2026-07-09):** retitled to "spatial VARIABLE BINDING" — terminology collision risk; define our claim explicitly as the *vision→text-token binding step* (Kang-style), cite them as the ordinal counterpart. Our territory intact (no metric, no site decomposition, no text-token sites, no probe-vs-verbalization in v2). Adopted their standards into IMPLEMENTATION_PLAN M5: strip-level + object-pooled probing (their negative control shows background tokens carry signal), two-ordering MCQ protocol, random-direction nulls, Probe* reporting. Their code/data: spatial.baulab.info.

## Deliverables in outputs folder
- `research_proposal_spatial_binding.md` — full proposal (advisor asks: plan endorsement + cluster access, model sign-off, human-baseline/ethics decision, external reader).
- `VSR_niches_critical_deep_read.md` — 15+ paper critical analysis with revision banners per niche.
- `research_proposal_spatial_binding.pptx` — 11-slide advisor deck (phase-framed, no conference dates).
- `docs/vsr_landscape_v8.pptx` — **companion document** (in-repo since 2026-07-15): Kaho's independent 19-paper landscape analysis, 2026-07-05, produced *before* this project's docs existed. Its contribution is folded in above; its 19-paper corpus joins the literature tracking. Keep it as the source for the five-definitions / capability-levels / tensions vocabulary.

## Current state / next step

- **🧭 PROGRAM REFRAMED (2026-07-14/15): stages, not papers — then DESIGN REVISION 2 (2026-07-15).**
  See "The research program" above. The work is S1 → S1.5 → S2 → S3 → S4, dependency-gated; papers and
  degree documents are *bindings* of whatever is defensible at a deadline. **M4.5 (= stage S1.5) now
  exists as a milestone** in IMPLEMENTATION_PLAN §4, between M4 and M5, **LOCKED until M4b passes the
  transferred Wang & Gao bar** — the same gate that guards M5. If M4's battery still gives R² ≈ 0.99
  everywhere after the leak controls, **neither M4.5 nor M5 starts.** Do not start M4.5 unprompted.
- **⚠ WHAT DESIGN REVISION 2 CHANGED THAT YOU MUST NOT REVERT** (two external reviews + a
  ground-truth dataset inspection, all 2026-07-15). Each of these *overwrote something these docs
  asserted a day earlier* — if you find the old form somewhere, it is stale, not a second opinion:
  1. **"destroyed / lost" → "becomes unavailable or unusable"**, and the hypothesis splits into
     **H1** (localization) + **H2** (ordinal-preserved / magnitude-collapsed). **"Rank-3 therefore
     incapable" is banned.**
  2. **Occlusion is NOT "the only categorical cue with zero metric content"** — it is *primarily an
     ordinal visibility cue*. The deduction that made the program's asymmetry follow from a
     definition was **wrong**, and it was in these docs for a day.
  3. **Four probing sites → FIVE functional stages**, and the M0 §3 schema freeze is **superseded**:
     M4 must add the **answer/readout** hook + a per-architecture tensor-mapping table.
  4. **Three stimulus regimes**, and **the primary localization claim lives in the COUNTERBALANCED
     one** (plausible scenes, independent nuisance cues) — not in conflict, which is for
     cue-integration only. This is what preempts the OOD attack structurally.
  5. **The IMAGE-IDENTIFIABILITY GATE** is now an M4-pilot acceptance criterion: *exact renderer GT ≠
     pixel-inferable GT.* **If the image doesn't contain the evidence, no site can** — and "low
     everywhere" would be an instrument failure wearing a finding's clothes.
  6. **MindCube is OUT of the validation layer** (multi-view perspective-taking; no single-image
     primitive). **What'sUp-B is IN** — 204 front/behind items we already owned. **SpatialRGPT-Bench's
     distance slice is IN** (absolute metric, sensor GT — the type CV-Bench lacks). **ReVSI-1F** is a
     new derived single-frame instrument. The external list is now **CLOSED**.
  7. **Models: a 2-architecture minimal core** (Qwen2.5-VL-7B + LLaVA-1.5-7B), expanding to 4–6 only
     after the site-wise pattern stabilizes.
  8. **The leak ceiling's load-bearing number is the INCREMENTAL form**
     `Δ_repr|dumb = score(dumb ∪ repr) − score(dumb)`, and held-out splits must target the **claimed
     generalization** (object identities, camera poses, depth ranges, cue combinations) — **never only
     random image splits.**
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
- **✅ M3 COMPLETE (2026-07-14) — GATE DECISION: GO.** See the M3 section at the top of this file.
  M3.1 PASS on the mechanism; M3.2 FAIL because v0 cannot measure models, only itself. **M3.2's bar
  transfers to M4.**
- **➡ NEXT: M4a — and M4 IS THE REAL GATE ON PHASE 2. ⚠ M4 IS NOW SPLIT INTO M4a + M4b (2026-07-15);
  they are TWO SESSIONS, not one.** Do not start unprompted. Before touching it, read
  IMPLEMENTATION_PLAN §2.5(d), the M4a/M4b specs, and `reports/m3_reproduction.md` §2.4.
  - **M4a = the stimulus battery.** Gate: **image-identifiability** — *do our images actually contain
    the evidence?* Needs **no VLM at all**, which is exactly why it runs first.
  - **M4b = the extraction pipeline.** Gate: **the transferred W&G bar** — *does our instrument
    measure models, or itself?*
  - **Why split:** M4 had two deliverables and two gates, and run as one milestone **a failure at
    either gate could not be attributed** — "metric is not decodable" would be indistinguishable from
    "the images never contained it" *and* from "the extraction is mis-mapping tokens". With M4a
    cleared first, a failure at M4b is unambiguous.
  - The one-line version: **make the stimuli able to disagree with the mask, or Phase 2 measures the
    instrument.** **M4b** gates two downstream milestones: M5 (probing) *and* M4.5 (occlusion / S1.5).
  - ⚠ Read the "Forward constraints from S1.5 / M4.5" note above — **the solo-ID amodal pass belongs
    to M4a**, while the generator is open. It is nearly free now and expensive to retrofit.
- **Infrastructure now in place for M4/M5** (built at M3, designed to be extended not thrown away):
  `extract/vlm.py` (generic HF-VLM wrapper; locates decoder layers; one forward captures AND
  intervenes), `extract/pooling.py` (mask→token mapping per family, validated by centroid
  registration; `strip_pool()` present but **not yet cached** — M4 must), `probes/ridge.py` (probes
  with shuffled-label controls + exact fast dual/kernel solvers), `interventions/spatial_id.py`,
  `scripts/leak_ceiling.py`.
- **M3 prerequisites (done):** all six M2 bugs fixed + the stimulus confound removed and the set re-rendered; **COCO downloaded in full** (train2017 19.3 G + val2017 + annotations — the full set was chosen so Kang's spatial-ID auxiliary-loss result stays reproducible later); **four models cached** (`llava-hf/llava-1.5-7b-hf`, `Qwen/Qwen2.5-VL-7B-Instruct`, `OpenGVLab/InternVL3-8B-hf`, `OpenGVLab/InternVL3-8B` — 59 GB in `$HF_HOME`). ⚠ **Use the `-hf` InternVL conversion**: the original ships custom remote code that `AutoModelForImageTextToText` refuses.
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
