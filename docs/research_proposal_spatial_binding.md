# Research Proposal — Where Metric Spatial Information Is Lost in Vision-Language Models

*Kaho — Master's thesis proposal, July 2026. Target: CVPR 2027 (abstract deadline Nov 15, 2026; ~18 weeks). Compute: lab A100 cluster. Companion document: `VSR_niches_critical_deep_read.md` (full critical literature analysis).*

---

## 1. Core Hypothesis — the Binding Bottleneck

**Metric spatial information (ordinal depth, distance ratios) survives in VLM visual tokens but is destroyed at the vision→text binding step, because the binding channel is coarse by construction. Qualitative relations survive coarse binding; metric ones cannot.**

This composes three established results that have never been connected:

1. **Kang et al.** ([2601.12626](https://arxiv.org/abs/2601.12626), Caltech): qualitative 2D relations reach the answer by binding a *coarse, rank-3* "spatial ID" to the object's text token at middle LM layers (causal, 11 models). Their faithfulness result: qualitative failures are perceptual — the readout is faithful. They never probe metric quantities; they flag depth (conflated with image height) as open.
2. **DepthCues** ([2411.17385](https://arxiv.org/abs/2411.17385), CVPR 2025): human-like monocular depth cues are decodable from modern *vision encoders* — the signal exists on the vision side.
3. **Ill-Posed by Design** ([2606.24335](https://arxiv.org/abs/2606.24335), June 2026): behaviorally, VLM metric estimates barely use scene geometry — identity/category priors dominate; LoRA learns the task *without* learning to use geometry.

The two endpoints (signal present in encoders; geometry unused in behavior) are established. **The pipeline between them — where between encoder and answer the metric signal stops mattering — is unlocalized. That localization is this project.**

Constraint from Wang & Gao ([2605.07148](https://arxiv.org/abs/2605.07148)): raw metric decodability at LM decoder layers is low (x-coord R²<0, distance RSA≈0), while a *topological* subspace survives. The claim is therefore not "metric is present but unverbalized" — it is a **localization claim**: metric fidelity is high at the encoder, degrades at identifiable stages (projector / binding / readout), and the degradation profile causally explains behavior.

Fifth anchor — **Dual Mechanisms of Spatial Variable Binding** ([2603.22278](https://arxiv.org/abs/2603.22278), v2 Jun 2026, Cui et al. — Bau/Torralba groups): causal interchange interventions show *ordinal* ordering information is carried by content-independent representations distributed in strips across visual tokens (including background), with an LM-side backup; probe-direction amplification corrects 40–55% of failures on COCO-spatial. **Terminology note:** their "spatial variable binding" = ordering-ID binding in the LM (qualitative); our "binding" = the vision→text-token step (Kang-style). We cite them as the ordinal counterpart to our metric claim, and adopt their evaluation standards (§2.3). Still absent from their work: metric quantities, site-wise decomposition (post-projector only), text-token binding sites, probe-vs-verbalization.

**Positioning sentence:** *Kang et al. showed qualitative spatial reading is faithful; Wang & Gao showed metric position is barely represented at LM layers; DepthCues and Ill-Posed by Design establish the endpoints. We localize where metric spatial information dies across the VLM pipeline, with depth-shortcut-controlled stimuli, and causally test whether repairing that stage repairs behavior.*

## 2. Paper 1 Design (CVPR 2027)

### 2.1 Measurement taxonomy

"Metric" is decomposed by what monocular geometry permits: **ordinal** depth (well-posed, prior-free), **ratio** distance (prior-free), **absolute** metric (requires a size prior — in principle). Core claims target ordinal + ratio; absolute is a secondary, explicitly prior-framed analysis (ReVSI showed absolute-scale scores are contaminated by category priors — e.g., size "estimation" from black videos).

### 2.2 Stimuli — factorial synthetic scenes, exact geometry

Blender/AI2-THOR rendering decorrelating what nature correlates: true depth × vertical image position × retinal size, congruent and conflict conditions, two object sets (canonical-size objects vs. arbitrary primitives — their difference measures the size-prior contribution). Controls: congruent-condition baseline for OOD-weirdness; real-image validation subset (What'sUp, CV-Bench + manually verified photos). This design also runs the **cue-integration test** (weighted fusion vs. winner-take-all under conflict — psychophysics framing) that Ill-Posed by Design's real-photo edits cannot.

### 2.3 The causal chain — four measurements

1. **Four-site probing grid**: vision-encoder output → post-projector → LM visual tokens → bound object text tokens, per layer, per quantity (ordinal/ratio/absolute; depth-axis vs lateral). Trained regression probes with selectivity controls (random-label nulls; qualitative relations as within-model positive control — binding demonstrably works there per Kang). The decodability *profile across sites* is the finding: where metric fidelity drops is where it dies. **Adopted standards from Cui et al. v2:** probe both mask-pooled object tokens AND all-token/strip-level representations (their negative control shows spatial signal is distributed across background tokens — object-pooled-only probing underestimates what survives); two-ordering strict MCQ protocol for all verbalized answers; random-direction nulls for injections; fixed-α and per-example-α (Probe*) reporting.
2. **Probe-vs-verbalization comparison** with three fairness defenses: rank correlations (not raw R²), few-shot-calibrated verbalization baseline, and oracle-text condition (ground-truth coordinates as text → proves the reasoning/verbalization machinery works given resolved input).
3. **Anchor localization** (from Q-Spatial's >40-pt reference-object effect): insert a known-size object — does the internal metric representation shift (perception aid) or only the verbalized answer (decoding-strategy aid)? One manipulation, adjudicates between the two halves of the hypothesis.
4. **Causal repair**: metric extension of Kang's oracle-ID injection — inject continuous-valued metric IDs at the binding layers; measure verbalized-answer recovery. Graded steering with dose-response validation (see §4, continuous mediation).

### 2.4 Intervention block (W7–11, stretch)

Derived from whatever the causal chain shows: binding-layer LoRA with a metric auxiliary loss (extending Kang's +6% proof-of-concept), benchmarked against **brute-force spatial SFT at matched compute/data** — Ill-Posed by Design's "LoRA learns the task but not geometry" is the direct motivation. Paper stands on the causal chain alone if this underdelivers (Type-2 paper structure: diagnosis primary, repair supporting).

### 2.5 Validation layer (W12–14)

External validity on complex benchmarks, inference-only: decompose VSI-Bench / MindCube / **CausalSpatial** ([2601.13304](https://arxiv.org/abs/2601.13304)) by required primitive; test whether per-model binding-loss measurements predict per-category failure patterns; metric-oracle injection at the *task* level (does repairing the primitive repair the composition?). CausalSpatial's own failure diagnosis — CoT "drifting from visual evidence" — is the binding hypothesis at reasoning level; confirming the correlation plants the seed for the PhD arc (§5).

### 2.6 Model selection — a natural experiment

4–6 open VLMs spanning encoder design: CLIP-based (LLaVA-1.5/1.6), native-resolution M-RoPE (Qwen2-VL/2.5-VL), SigLIP-based (InternVL, Gemma-3). Systematic variation of the decodability profile with encoder design addresses the "one phenomenon or three?" question left open across Kang / Beyond Semantics / Dual Mechanisms.

### 2.7 Mandatory pre-reads before design freeze

[Attention in Space, 2603.20662](https://arxiv.org/pdf/2603.20662) (head-level routing — needed to distinguish "destroyed in transit" from "never shipped"); [Why Far Looks Up, 2605.30161](https://arxiv.org/html/2605.30161v1) (depth-vertical entanglement); full read of Ill-Posed by Design §6.6 + limitations.

## 3. Timeline (18 weeks to Nov 15)

| Weeks | Work |
|---|---|
| 1–2 | Reproduce Kang et al. pipeline ([code](https://github.com/Raphoo/linear-mech-vlms)) + Wang & Gao probe setup (load-bearing, not warm-up). Build synthetic scene generator. Mandatory pre-reads. Ethics application if human baseline wanted. |
| 3–6 | Core causal chain (§2.3) across 4–6 models in parallel. **W6: write intro + Figure 1; scope freeze** — later ideas go to `future_work.md`. |
| 7–11 | Intervention block (§2.4). Side experiment: inference-time norm rescaling (untested causal claim from Beyond Semantics). |
| 10 | **Go/no-go**: muddy core finding → retarget ICCV 2027 (~March) + CVPR workshop; do not force a weak submission. |
| 12–14 | Validation layer (§2.5), ablations, matched-stimuli controls. |
| 15–17 | Full writing pass; advisor + one external reader. |
| 18 | Buffer. |

Risk management: biweekly scoping search (papers citing 2601.12626, 2605.07148, 2606.24335, 2411.17385) — this analysis was materially revised twice in one day by newly found papers; every specific design claim gets a verification search before entering the paper.

## 4. Method-Harvest Strategy

Scientific claims first; methods extracted where the toolbox forces invention. Three anticipated gaps:

1. **Causal mediation for continuous features** — existing interchange interventions and steering are discrete (left↔right); metric quantities need graded steering with dose-response validation. Paper 1 must build this; if it generalizes (size, count, time, any continuous property), it is a standalone methods contribution (ICLR/NeurIPS) with the spatial results as demonstration.
2. **Probe transfer as a representational-sharing measure** (paper 2, below).
3. **Hypothetical-state probing** (PhD arc, below).

First versions stay minimal (linear directions, scalar doses); formalization happens in writing if data cooperates. New interp methods carry a double validation burden — method-first framing is explicitly avoided on this timeline.

## 5. Research Arc

**Paper 1 (CVPR 2027):** where metric spatial information dies in *understanding* — the binding bottleneck (§1–2).

**Paper 2 (post-deadline start) — the spatial-method mechanistic audit** *(updated 2026-07-09; supersedes the generation paper in this slot)*: how do existing spatial-enhancement methods change internal behavior? Per method, the four-site probe grid decomposes: representation improved / binding improved / answer prior installed at readout. Ties directly to ReVSI's behavioral finding that spatial fine-tunes lose gains under corrected evaluation; scaffold analysis would mechanistically explain why verbalized spatial cues barely help (the C-niche convergent fact). **Verified audit set (all public, matched bases):** 7B on Qwen2.5-VL-7B-Instruct — SpaceR (pure RL) vs ViLaSR (SFT+RL, drawing scaffold); 3B on Qwen2.5-VL-3B-Instruct — SpatialLadder (SFT→RL) vs SpaceQwen/SpaceOm (synthetic SFT) vs Spatial-MLLM (arch+SFT); plus inference-time scaffolds (scene-graph prompt, depth input, SoM — weight-free). Skip: Cambrian-S (no untouched base VLM), SVQA-R1 and SpatialVLM (no checkpoints). **Closest neighbor checked:** [2511.11440] probes only their own synthetic-SFT, LM-layers × final-question-token only, single toy task, no method comparison, no site decomposition, no scaffolds — cite and differentiate. Reuses ~90% of Paper 1 infrastructure.

**Paper 3 / PhD-start — generation:** does *generation* read the same spatial representation? Unified models (Janus-Pro = decoupled control, Emu3.5 = fully shared AR, BAGEL = hybrid/best pixels) spanning the sharing spectrum: (i) probe transfer understanding→generation activations; (ii) generation-time failure taxonomy (never planned / planned-then-drifts / planned-but-misrendered); (iii) stretch: inject understanding-derived spatial directions during generation. Evaluation circularity handled probing-first; pixel endpoint via 2AFC + disjoint detector ensembles + ~300-image human calibration. Paper 1 generates the falsifiable prediction: if the bottleneck is lexical binding, the generation pathway (image-space readout) should suffer less — or fail elsewhere.

**PhD direction:** spatial state over time and under intervention. Near-term ports that avoid the video-compute wall: multi-image guaranteed-evidence protocol (decay vs interference vs never-encoded vs readout — DISJOINT-3DQA precedent), KV-cache-as-memory probing, generation-trajectory state maintenance. Long-term: hypothetical-state probing — does the model internally represent predicted future positions before verbalizing? (CausalSpatial-level simulation; humans 84% vs GPT-5 54%.) One toolkit, one question — *where spatial information lives, dies, and gets used* — at escalating levels: layers → images → generation steps → simulated futures.

## 6. Asks (advisor meeting)

1. Confirmation of the November CVPR target and priority cluster access W3–11.
2. Model coverage sign-off (§2.6) — affects GPU allocation.
3. Whether to pursue the human baseline (~20 participants, cue-integration comparison) — ethics application must go in ~W1 if yes.
4. One external reader commitment for W15–17.

---

*Full critical analysis of 15+ papers, overlap verdicts, and superseded alternatives: see `VSR_niches_critical_deep_read.md`.*
