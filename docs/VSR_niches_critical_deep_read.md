# Visual Spatial Reasoning — Critical Deep-Read of Four Candidate Niches

*Prepared July 2026, **revised after adding two critical papers (see §Revision at the end): Kang et al. 2601.12626 and Wang & Gao 2605.07148.** The Overall Recommendation has been rewritten accordingly — the original A/D RQs as first phrased are partly pre-empted. Each niche: critical reading of key papers (full-text), cross-paper synthesis, and falsifiable research questions (RQs) sized for a solo researcher (open-weight 7–8B VLMs, inference-time interventions, probing, synthetic data).*

---

## Niche A — Mechanistic Failure Analysis → Targeted Fixes

> **⚠ Revision status (July 2026):** substantially affected by [Kang et al. 2601.12626](https://arxiv.org/abs/2601.12626) and [Wang & Gao 2605.07148](https://arxiv.org/abs/2605.07148) — see §Revision. A-RQ1 survives as a side experiment; **A-RQ2 and A-RQ3 are superseded** (qualitative-direction steering and ordering-probe amplification are now covered territory). Additional radar: [Attention in Space, 2603.20662](https://arxiv.org/pdf/2603.20662) likely closes A2's "which heads" gap; [Why Far Looks Up, 2605.30161](https://arxiv.org/html/2605.30161v1) (May 2026) probes relation directions and finds horizontal relations form stable opposing directions while **vertical and depth relations are entangled** — read both before committing to any attention- or direction-level claim.
>
> **Second update (July 2026):** two papers *strengthen* A's binding-bottleneck setup by establishing its two endpoints externally. [DepthCues](https://arxiv.org/abs/2411.17385) (CVPR 2025): six human monocular depth cues are decodable from modern *vision encoders* (20 models) — the signal exists on the vision side. [Ill-Posed by Design, 2606.24335](https://arxiv.org/abs/2606.24335) (June 2026): behaviorally, VLM metric estimates barely use scene geometry — identity/category priors dominate — and **LoRA learns the task without learning to use geometry** (directly motivates the targeted-fix vs brute-force-SFT comparison in the intervention block). Neither analyzes the VLM pipeline internally: the encoder→binding→verbalization localization remains ours, now with both endpoints citable rather than needing to be established from scratch.

### A1. Beyond Semantics ([arXiv:2503.17349](https://arxiv.org/abs/2503.17349))

**Hypothesis.** VSR is limited because vision embeddings have norms 1–3 orders of magnitude larger than text embeddings, forcing the LM to downscale vision attention; since RoPE's positional sensitivity is proportional to attention weight, spatial signal is suppressed — the LM treats vision tokens as a semantic bag-of-tokens. *Unstated assumption:* spatial information should flow through the LLM's 1D positional index over vision tokens — a strong assumption, since 1D raster order is a lossy proxy for 2D layout.

**Contribution.** The permutation test (shuffling vision tokens costs only 0.2–2.74% on VQAv2/POPE/GQA/CV-Bench) and compression test (576→1 token costs ≤8.5%) are informative negative results; the norm-imbalance measurement plus the RoPE-derivative argument is a plausible mechanism sketch.

**Evidence quality.** The permutation/compression tests are causal input interventions but confound model invariance with benchmark insensitivity. The norm-suppression claim itself is **correlational plus theory** — the derivation ignores that RMSNorm at every layer input should largely equalize magnitudes after layer 0. **Key missing experiment:** an inference-time causal test (rescale vision-embedding norms in a frozen LLaVA-1.5, measure spatial accuracy). Both proposed "interventions" require full two-stage retraining, so gains could come from generic training benefits; the +Normalize-only variant even hurts Shape_rel (−1.6).

**Limitations beyond the authors' list.** Single model (LLaVA-1.5-7B/CLIP); headline gains (+8.17) on a self-built benchmark; no per-example error analysis; attention-entropy analysis interpreted flexibly in both directions.

### A2. Why Is Spatial Reasoning Hard for VLMs? ([arXiv:2503.01773](https://arxiv.org/abs/2503.01773), ICML 2025)

**Hypothesis.** VSR is limited because answer-token attention to image tokens is (a) insufficient in quantity (~10.7% of attention on ~89% of tokens) and, more importantly, (b) geometrically misallocated: attention follows linguistic familiarity priors rather than actual object locations. *Unstated:* generation confidence is a reliable proxy for prior familiarity, licensing the confidence-gated intervention.

**Contribution.** Layer-wise "see (early) vs process (middle)" decomposition; attention–bounding-box alignment predicts correctness (AUROC 0.948 at layer 17 on Controlled_A); the negative control that uniformly *adding* attention to image tokens does not help — location, not quantity, matters.

**Evidence quality.** The attention–correctness link is correlational, but the intervention (ScalingVis/AdaptVis: multiply last-token attention logits toward image tokens by α, sharpen if confidence > β) is causal. Gains are bimodal: up to +50 points on synthetic Controlled_A (from a degenerate baseline) vs. only +0.6 to +7.3 on real COCO/VG. **Missing:** head-level causal patching to identify which heads carry the relation; a test disentangling the familiarity story from a plain calibration effect (α, β tuned per subset on a 20% split — part of the gain may be distribution-specific overfitting). The smoothing-helps-synthetic / sharpening-helps-real pattern is explained post hoc.

**Limitations beyond authors' list.** Mostly LLaVA family (Qwen2-VL shows smaller gains, appendix-only); real subsets have severe left/right label imbalance; YOLO-based region annotation injects errors; confidence thresholding may not transfer across calibration regimes.

**Intervention.** Training-free; ≤+7.3 on real images; 1.02–1.64× inference cost.

### A3. Dual Mechanisms of Spatial Reasoning ([arXiv:2603.22278](https://arxiv.org/abs/2603.22278))

**Hypothesis.** VSR is carried by content-independent *ordering* representations with two sources: a **primary** signal computed by the vision encoder and distributed globally across visual tokens (strip-like patterns extending into background regions), and a **secondary** backup formed in middle LM layers; amplifying the vision-derived signal improves performance. *Unstated:* mechanisms of *success* in strong models explain *failures* in general.

**Contribution.** Methodologically the strongest of the three: interchange interventions with counterfactual pairs localize a clean stage structure (Qwen2-VL: layers 20–22 transfer ordinal identity, 23–27 attribute value); strip-patching flips predictions while object-token-only patching does not — a causal demonstration that spatial code is distributed, contradicting single-token binding accounts; ablating vision-derived ordering isolates the LM backup mechanism (layers 13–17).

**Evidence quality.** Almost everything load-bearing is causal — rare. But: both models are near ceiling (0.89–1.00), so this is a mechanism-of-success study wearing failure-analysis clothes; only 50 counterfactual pairs per setting; three collinear objects only. Red flag: a random-direction baseline corrects 8.8–15.8% of failures — if noise fixes errors, decision boundaries are brittle and the ordering-amplification effect (32.4–50.7% corrected) needs a stronger null. **Missing:** run the probes on genuinely failing models/examples to show degraded ordering signal *predicts* failure.

**Intervention.** Training-free but not label-free (supervised probes need bounding boxes); +5% absolute on What'sUp.

**v2 update (Jun 2026, deep-read 2026-07-09).** Retitled "The Dual Mechanisms of Spatial **Variable Binding** in VLMs" — substantive revision, core claims unchanged. New: COCO-spatial benchmark (2,687 natural images) as main correction testbed; Qwen2-VL-2B added (genuine failure regime — v1's near-ceiling criticism partially addressed behaviorally, still not mechanistically); strict two-ordering protocol (25% chance); up to +22pp correction (40–55% of failures vs 10–13% random null); Probe vs Probe* (fixed vs per-example α); realistic-background control. **Still absent:** metric quantities, text-token binding sites, Kang engagement beyond citation, site-wise decomposition (post-projector only), probe-vs-verbalization. **Terminology alert:** they now own "spatial variable binding" = ordering-ID/LM-style binding — our claim must be explicitly defined as the *vision→text-token binding step* (Kang-style) to avoid collision; cite them as the ordinal/qualitative counterpart. **Adopt their standards:** two-ordering protocol, random-direction nulls, Probe* reporting, and the key warning that spatial signal is distributed in strips across background tokens — probing object-pooled tokens only underestimates what survives.

### A. Synthesis

All three locate the bottleneck at the vision-embedding→LM interface and agree the visual spatial signal *exists* but is under-used. A unifying reading: a weak effective spatial channel (A1's suppressed signal / A3's under-weighted ordering directions) leaves attention to default to linguistic priors (A2). **Conflict:** A1 pushes the LLM-side RoPE channel; A3 shows LM-side ordering is only a backup with the vision encoder dominant — and A3's models (M-RoPE Qwen2-VL, Gemma-3) have far stronger encoder-side position handling than LLaVA's CLIP, so the three "mechanisms" may be model-generation-dependent rather than one phenomenon.

**Diagnosed but not cheaply fixed:** norm imbalance (only fixed via retraining); familiarity-dependent attention priors (needs per-distribution tuning); distributed ordering code in failure regimes (validated only near ceiling).

**RQs.**

1. **Norm suppression, causal test.** Does rescaling vision-embedding norms to the text range at inference — no retraining — improve spatial accuracy in frozen LLaVA-1.5-7B? *Sweep a scalar norm multiplier, evaluate on 2DS/What'sUp/CV-Bench2D; a null result demotes norm suppression from inference bottleneck to training-dynamics artifact.*
2. **Mechanism unification.** Are AdaptVis's attention-scaling gains mediated by A3's ordering directions? *On Qwen2-VL-7B/What'sUp, measure probe-direction logit changes under attention scaling; test whether the two interventions correct overlapping vs disjoint error sets.*
3. **Failure prediction.** Does degraded strip-like ordering signal predict per-example spatial failures in a weak model? *Train ordering probes on LLaVA-1.5 vision embeddings, correlate probe margin with correctness, then amplify probe directions against a matched random-direction null.*

---

## Niche B — The Understanding↔Generation Spatial Gap

> **✓ Revision status (July 2026):** re-scoped against the newest literature — **still open**. [GapEval](https://arxiv.org/pdf/2602.02140) (9 UMMs, bidirectional, no spatial category), [UniSandbox](https://arxiv.org/pdf/2511.20561), [2601.21406](https://arxiv.org/abs/2601.21406), [UniPath 2605.11400](https://arxiv.org/pdf/2605.11400), [LatentUMM 2605.17766](https://arxiv.org/pdf/2605.17766) all study the general understanding↔generation relationship; none aligns spatial-relation taxonomies across both directions in the same model. B-RQ1–3 stand as written.

### B1. SpatialReward ([arXiv:2603.22228](https://arxiv.org/abs/2603.22228))

**Hypothesis.** Spatial generation is limited because *the reward signal is spatially blind*, not because the generator lacks capacity. *Unstated corollary:* base diffusion models already contain latent spatial competence that Flow-GRPO can elicit — a strong, untested assumption about what RL can vs. cannot inject.

**Contribution.** Primarily engineering: fine-tuned Qwen2.5-VL-7B prompt decomposer + expert detectors (GroundingDINO/YOLO-World, Orient-Anything, DepthAnything, PaddleOCR) + CoT VLM judge as a verifiable reward, plus SpatRelBench (~2k entries). The scientific kernel — grounded VLM judging beats ungrounded — is plausible but the paper does not isolate which component carries the gain.

**Evidence quality / circularity.** SpatRelBench is scored by the *same* detector stack used inside the reward, so training reward and evaluation metric share failure modes — classic Goodhart risk: RL will optimize into detector blind spots and the benchmark will certify the artifact. Headline jumps (GenEval Position 0.28→0.98) should read as metric saturation suspicion, not spatial competence. Mitigation: general metrics don't degrade. **Missing:** evaluation on an independent spatial benchmark not built from their detectors; detector-error analysis; out-of-detector-vocabulary prompts.

**Limitations beyond authors' list.** Reward only as open-world as GroundingDINO (deformable/amorphous relations unverifiable); RL prompts and benchmark prompts both GPT-4o-generated with unquantified distribution overlap; no transfer test to unseen relation compositions.

### B2. SpatialGenEval / "Everything in Its Place" ([arXiv:2601.20354](https://arxiv.org/abs/2601.20354))

**Hypothesis.** Spatial generation is limited because existing benchmarks use short, information-sparse prompts, so higher-order failures (occlusion, comparison, causality) go unmeasured; plus a data-centric claim (spatially dense training data is scarce). *Unstated but visible in their own analysis:* text-encoder strength is the "key determinant" — quietly relocating the bottleneck from the image decoder to language-side comprehension.

**Contribution.** Benchmark engineering with good hygiene: 1,230 information-dense prompts, 10 MCQs each across a 4-domain hierarchy; no-answer-leakage checks, refusal option, 5-round self-consistency, dual judges, human-alignment study. Finding: across 23 models, spatial *reasoning* (comparison ~26–32%, occlusion ~27–34% vs 20% random) is a universal bottleneck while foundation/attribute scores exceed 70%; unified models are more parameter-efficient — hinting understanding helps generation.

**Evidence quality / circularity.** Better managed but real: the VLM judge is weakest at exactly the spatial questions that drive the headline claim — their own Table 5 shows human alignment drops to 72–78% on the Spatial Reasoning subdomain. Part of the "reasoning deficit" may be *judge* deficit. SpatialT2I SFT images are generated by the evaluated model family and rewritten by Gemini — risks prompt-image co-adaptation; +4–6% gains are modest against judge noise.

**Limitations beyond authors' list.** MCQ judging can't detect partially correct layouts; 77-token CLIP truncation confounds "long prompt" difficulty for CLIP-based models; suspiciously high causality/motion scores (72–84%) suggest memorized action templates, undercutting the hierarchy framing.

### B. Synthesis — is the gap open?

**Partially studied, spatially unstudied.** The general understanding↔generation gap in unified models is an active thread — [GapEval](https://arxiv.org/abs/2602.02140) (no spatial category), [UniSandbox](https://arxiv.org/abs/2511.20561) (CoT bridges reasoning-generation gaps on synthetic tasks), [arXiv:2601.21406](https://arxiv.org/abs/2601.21406) (generating depth/segmentation improves spatial understanding). But **no paper aligns a spatial-understanding taxonomy with a spatial-generation taxonomy on the same relations in the same models.** SpatialGenEval never probes its unified models (Janus-Pro, Bagel, Show-o) on the mirrored VQA task. The question — do VLMs and T2I models fail on the same spatial relations, and is failure correlated within a single unified model? — appears genuinely open.

**RQs.**

1. **Mirrored failure profile.** Within a single open unified model (Janus-Pro-7B, Bagel-7B, Show-o), is per-relation spatial accuracy in understanding (VQA on real images) correlated with generation (same relation, mirrored prompt)? *Build ~500 bidirectional items from SpatialGenEval's subdomains, score generation with a detector ensemble disjoint from any judge VLM, report per-subdomain Spearman correlations.*
2. **Judge-circularity audit.** How much of the reported "spatial reasoning bottleneck" in T2I benchmarks is VLM-judge error rather than generator error? *Human re-scoring of ~300 reasoning-subdomain images; decompose disagreement into (generator wrong / judge wrong / both). Cheap, directly stress-tests both papers above.*
3. **Understanding-side intervention, generation-side readout.** Does improving a unified model's spatial *understanding* alone (LoRA-SFT on spatial VQA, zero image-generation data) transfer to spatial *generation*? *Freeze the generation head, measure pre/post per-relation deltas with detector-based scoring. Positive transfer falsifies "decoders are the bottleneck"; null falsifies "understanding informs generation" for space.*

---

## Niche C — State Memory in Dynamic/Egocentric Scenes

> **⚠ Revision status (July 2026):** partially affected by newer work. External/self-maintained memory scaffolds are now crowded: [VLM², 2511.20644](https://arxiv.org/abs/2511.20644) (dual working/episodic memory), S-Agent (scene+agent memory, June 2026), [EventVLA, 2606.20092](https://arxiv.org/html/2606.20092v2) — **C-RQ3's novelty is eroding**. [Echo-Memory, 2606.09803](https://arxiv.org/pdf/2606.09803) is a *controlled study of memory* in action world models — check whether its design already deconfounds sampling from interference before running C-RQ2. C-RQ1 (probing out-of-view object positions in frozen VLM states) appears still open but verify against Echo-Memory first.

### C1. LMM-Track4D ([arXiv:2605.19390](https://arxiv.org/abs/2605.19390))

**Hypothesis.** 4D reasoning is limited because video is encoded as framewise tokens with no dedicated mechanism for identity/motion continuity across turns — so an explicit state token (TRK), ray-time geometry encoding, and a trajectory decoder should fix it. *Unstated:* that supervised trajectory regression on 526 clips measures reasoning at all.

**Contribution.** Engineering plus a micro-benchmark (526 samples from surveillance/driving data — *not* egocentric). The headline table is nearly vacuous: every baseline scores "–" on geometric metrics because only the proposed model emits parseable trajectories — a format-compliance result, not a reasoning result.

**Evidence quality.** One experiment genuinely isolates memory: no-history / self-history / gold-history (66.0 → 71.7 → 73.6 late-turn Traj-Acc), cleanly attributing residual error to imperfect cross-turn state propagation. But "w/o TRK → no stable output" conflates memory with interface (the decoder consumes the TRK slot). Perception is partly oracled (ground-truth camera intrinsics/extrinsics). Missing: corrupted-history controls, horizons >4 steps, any transfer test. Train and eval come from the same 526 samples.

**Limitations beyond authors' list.** Three fixed venues, near-zero scene diversity; "long-horizon" = dialogue turns, never crossed with clip length (memory confounded with context length). Red flags: unresolved "Appendix ??" references; dense self-citation cluster of the authors' own 2026 preprints. Reproducibility questionable.

### C2. DISJOINT-3DQA ([arXiv:2505.24257](https://arxiv.org/abs/2505.24257))

**Hypothesis.** Egocentric VSR is limited *not by reasoning over 3D geometry but by constructing/maintaining a metric 3D representation from 2D observations across disjoint frames*. The non-co-visibility constraint is a real manipulation; the oracle ladder is the test: sparse cues (textual trajectory, BEV) give +2–4%, oracle 3D coordinates give +18–20% (GPT-4o 65.6→83.2).

**Contribution.** Best hypothesis-driven design of the three: benchmark (5,399 QA, 1,668 synthetic scenes) plus a diagnostic finding. BEV failure analysis (24% hallucinated geometry, 15% ego↔BEV misalignment, 17% cue ignored) adds mechanistic texture.

**Evidence quality.** The oracle isolates reasoning-given-geometry from geometry-construction but does **not** isolate memory from perception — a model may fail because it never estimated the position from a single view (monocular metric-depth failure), not because it forgot. Missing controls: (i) a co-visible control set with matched questions — the disjointness cost is never directly measured; (ii) an intermediate oracle of per-frame camera-frame coordinates, separating per-frame perception from cross-frame integration. The temporal-gap decline (60%→30%) confounds memory with distance, intervening-frame count, and context length.

**Limitations beyond authors' list.** Purely synthetic, purely *static* scenes — "state memory" is only positional persistence, never state *change*; Set-of-Marks prompting partially oracles referential grounding too.

### C3. UCS-Bench / DirectMe ([arXiv:2606.15200](https://arxiv.org/abs/2606.15200))

**Hypothesis.** Continual spatial reasoning fails because MLLM memory stores no *viewpoint-conditioned spatial state* (where things are relative to the user's real-time pose). *Unstated commitment:* the fix should be an external symbolic-metric scaffold (DepthAnything3 pose/depth + GroundingDINO + SAM2 → pose-anchored scene graph) rather than a learned internal capability.

**Contribution.** The benchmark is the real contribution: 8.1K manually annotated streaming QA over 170h, with **repeated queries at different timestamps** — a genuinely novel probe of state *updating*. Best empirical nuggets: object-trajectory > ego-trajectory across all models (ego-motion is the systematic weakness); GPT-5 category 58.8% vs quantity 33.5% (recognition ≫ cumulative-state updating); and an honest root-cause analysis — tracking 40% + ego-pose 23% of their own pipeline's failures, i.e. **their fix's bottleneck is perception, not memory**.

**Evidence quality.** The question–evidence-interval degradation curve is the key memory evidence, but badly confounded with **frame sampling**: baselines get 50–64 uniform frames over ~20–40-min videos, so evidence 30s before the query is frequently never in the input — "visual memory amnesia" may be "evidence never sampled." Worse, DirectMe processes 1 fps in the background (~60× more frames than baselines), confounding scaffold quality with observation bandwidth. The Desc-vs-Graph ablation (44.5 vs 50.2) is the paper's best control and does support "structured pose-anchored state > verbalized captions."

**Limitations beyond authors' list.** 35% of QA from EgoLife (one shared house); repeated-question priors survive debiasing; pose drift over 40-min outdoor streams never reported.

### C. Synthesis

All three reject "language reasoning" as the failure locus but localize differently: C2 says **representation construction** (2D→metric-3D lift), C3 says **state maintenance under ego-motion** yet its own root-cause pushes the bottleneck back into **perception**, C1 says **cross-turn propagation**. Compatible as a pipeline (perceive → lift → maintain → propagate), but no paper tests two stages against each other, and *none* deconfounds memory decay from context-window sampling.

**Convergent, unexplained fact:** sparse/verbalized spatial cues barely help (+0.5–4%) while fully resolved metric state helps massively (+6.5–20%). VLMs can *consume* resolved coordinates but cannot *integrate* partial geometric cues. Measured three ways; mechanistically explained by nobody.

**RQs.**

1. **Probing.** Do frozen VLM hidden states linearly encode the allocentric position of an out-of-view object, and does decodability decay with intervening frames when the evidence frame is guaranteed in context? *Linear probes on ProcTHOR/Habitat walkthroughs with known coordinates, varying intervening-frame count at fixed context length — dissociates encoding failure from readout failure.*
2. **Sampling vs interference.** Is temporal-gap degradation caused by evidence frames missing from input or by representational interference? *Re-run DISJOINT-3DQA-style QA with the evidence frame always included and token count matched, manipulating only intervening content; residual degradation falsifies the sampling explanation.*
3. **Self-maintained state scaffold.** How much of C2's 20-point oracle gap can a model recover by emitting and updating its *own* structured ego-anchored state (JSON: object → bearing/distance) per frame chunk, with no external geometry pipeline? *Compare no-state vs self-state vs oracle; audit whether errors are state-write or state-read — directly localizing the failure stage the three papers dispute.*

---

## Niche D — Metric vs Qualitative Asymmetry

> **⚠ Revision status (July 2026):** the asymmetry is no longer "explained nowhere". [Wang & Gao 2605.07148](https://arxiv.org/abs/2605.07148) report the x-vs-z decodability asymmetry (as a confound aside) and argue metric weakness is *representational*; [Why Far Looks Up, 2605.30161](https://arxiv.org/html/2605.30161v1) finds depth relations entangled with vertical ones in representation space (perspective-driven cues) — converging with Kang et al.'s depth-height conflation. **D-RQ1 as phrased is superseded** (probe-vs-verbalization for metric quantities must now be framed around the metric-vs-topological dissociation, §Revision); **D-RQ2 (anchor causality) and D-RQ3 (depth label-noise control) survive** and D-RQ3 gains importance as the depth-shortcut-controlled design.
>
> **Second update (July 2026):** behavioral cue-decomposition for metric estimation is now **partially claimed**. [Ill-Posed by Design, 2606.24335](https://arxiv.org/abs/2606.24335) (June 2026) decomposes six evidence channels for metric *object-size* estimation via image-level counterfactuals on real photos: identity/category priors dominate, apparent size is used direction-inconsistently, scene geometry is largely unused; their §6.6 concludes VLM centimeter estimates are "category-level priors with selective visual modulation" (converging with ReVSI). [DepthCues, 2411.17385](https://arxiv.org/abs/2411.17385) (CVPR 2025) covers cue-level probing at the *encoder* level. **What survives of D:** (i) pairwise metric *distance* and depth-axis ordering — different geometry from size (ordinal depth is well-posed monocularly; size is ill-posed by construction) and undecomposed; (ii) the **integration test** — conflict conditions distinguishing weighted cue-fusion from winner-take-all, impossible with their real-photo edits, requires factorial synthetic geometry; (iii) the **ordinal/ratio/absolute taxonomy** with matched-pair measurement; (iv) **anchor localization** (does a reference object shift the internal representation or only the decoding strategy). Both papers become motivation citations for the mechanistic bridge rather than competitors. *Their §6.6 and Limitations were only skimmed — full read required before finalizing the proposal.*

### D1. MindEdit-Bench ([arXiv:2607.00491](https://arxiv.org/abs/2607.00491))

**Hypothesis.** VSR evaluation is limited because existing benchmarks are *observational* — never testing consequences of hypothetically moving/rotating an object. *Unstated:* VLM spatial competence is anisotropic — the 8-direction × 5-distance answer grid presumes failures decompose along interpretable axes, itself a substantive representational claim.

**Contribution.** Feed-forward 3D scene-graph pipeline from three smartphone photos of 120 private scenes (contamination control); first object-level counterfactual editing benchmark; diagnostic answer design. Key finding for this niche: pure-depth answers hit **7.4%** vs **18.0%** pure-lateral (−10.6 pp), replicating at other levels; errors cluster in adjacent 45° bins (1.7× random) not 180° reversals (0.6×) — models hold a coarse compass-region sense but lose the depth coordinate.

**Evidence quality: descriptive, not causal.** The 2D-pretraining explanation is a plausibility argument, not a test — no probing, no depth-cue manipulation. Confound: depth-bin ground truth derives from monocular DepthAnything3, whose geometric noise is plausibly *larger along the depth axis* — some of the 7.4% could be label noise. Depth-vs-lateral is compared between answer *subsets*, not controlled paired stimuli.

**Limitations beyond authors' list.** L4/L5 confound counterfactual *simulation* failure with baseline metric *perception* failure (no no-edit control task); the distance-bin dimension is never analyzed separately; three annotators is thin; Gemini both builds the pipeline vocabulary and tops the leaderboard.

### D2. ReVSI ([arXiv:2604.24300](https://arxiv.org/abs/2604.24300))

**Hypothesis.** VSR evaluation is limited because QA pairs are not guaranteed answerable and correct under the model's actual inputs (annotation drift; observability mismatch at 16–64-frame budgets). *Unstated:* much reported metric progress is *prior exploitation, not measurement* — VSI-Bench counting is 62% solvable by always answering "2".

**Contribution.** Full re-annotation of 381 scenes / 5,365 objects; frame-budgeted GT; and the standout device — **dummy-video controls** (remove all frames containing the queried object, or use black frames). Findings: fine-tuned "spatial" models lose most claimed gains and hallucinate catastrophically (Spatial-MLLM: 0–0.2% on dummy videos); InternVL3.5 scores 48–50 MRA on object size from *fully black videos* — metric "size estimation" answered entirely from category priors. Scaling spatial SFT data 135k→820k yields ~3%.

**Evidence quality.** The dummy-video design is a genuine intervention decoupling visual evidence from priors — strong causal hygiene *for the evaluation-validity claim*. For *why* metric is worse, still descriptive. Valuable caution: relative error is roughly constant across GT distance; apparent "long-range weakness" can be metric-design artifact.

**Limitations beyond authors' list.** Author-only re-annotation, no inter-annotator agreement; inherits VSI-Bench's taxonomy — no matched-pair qualitative-vs-metric design (same object pair, "which is closer?" vs "how far apart?"); indoor-scan domain only; contamination hypothesized but not tested.

### D3. Context from the wider literature

[Q-Spatial Bench](https://arxiv.org/abs/2409.09788): prompting the model to reason via a *reference object* lifts Gemini 1.5 Pro distance estimation by >40 points with no fine-tuning — strong evidence a large chunk of the metric deficit is a *strategy/decoding* problem (missing scale anchor), not missing perceptual signal. [GEODE](https://arxiv.org/abs/2511.11239): frames a "dual bottleneck" (2D-only features + discrete tokenizers structurally unable to emit precise continuous values); regression head recovers metric performance. [SD-VLM](https://arxiv.org/html/2509.17664v1) + [Spatial Blindspot](https://arxiv.org/abs/2601.09954): even depth-supervised SOTA leaves quantitative (~33%) far below qualitative (~65%).

### D. Synthesis

**The asymmetry is documented everywhere, explained nowhere.** MindEdit-Bench localizes it geometrically but stops at a pretraining conjecture; ReVSI shows metric scores are contaminated by category priors — the field may not even have a clean *measurement* of the asymmetry yet; the fix-it papers assume competing causal stories (tokenizer can't regress vs encoder lacks 3D signal vs missing scale anchor) and each "works" — the community is treating an unresolved scientific question as an engineering menu. Clearest positive clue: Q-Spatial's reference-object effect suggests metric information is *latently present but not spontaneously verbalized* — favoring a decoder/strategy bottleneck — yet nobody has tested this with probes on matched stimuli.

**RQs.**

1. **Probe vs verbalization gap.** Does a linear probe on frozen VLM visual tokens predict inter-object metric distance better than the same model's verbalized answers on identical images? *~500 synthetic Blender/AI2-THOR scenes with exact geometry; compare probe R² vs verbalized R², separately for depth-axis and lateral pairs.*
2. **Anchor causality.** Is the metric deficit causally reduced by inserting a known-scale reference object, holding all other geometry fixed? *Matched scene pairs with/without a canonical-size anchor; large paired gain ⇒ scale-calibration bottleneck, not depth perception.*
3. **Depth-axis label-noise control.** Does the depth-axis weakness survive when ground truth comes from perfect synthetic geometry rather than monocular-depth pipelines? *Replicate the direction-bin analysis with exact coordinates and balanced difficulty; test whether the −10.6 pp gap persists, shrinks, or grows.*

---

## Revision (July 2026) — Two Papers That Change the Picture

### R1. Linear Mechanisms for Spatiotemporal Reasoning ([arXiv:2601.12626](https://arxiv.org/abs/2601.12626), Kang, Chen, Gkioxari, Perona — Caltech, Jan 2026)

**What it establishes.** Across **11 VLMs** (LLaVA-1.5/1.6, LLaMA-3.2V, Qwen2/2.5-VL, Gemma, InternVL, ≤14B), qualitative 2D spatial relations are carried by **"spatial IDs"**: coarse discrete position-bin vectors (4×4 grid, mean-centered activation differences — arithmetic, not trained probes) **linearly bound to object-word *text* tokens** at a narrow band of middle "modality-binding" LM layers. Spatial IDs are approximately a **rank-3 linear transform of the vision encoder's positional-encoding basis** (R²≥0.85). Causal evidence is strong: norm-scaled direction steering flips binary spatial beliefs at a median 64.4–64.6% vs 29.5% norm-matched noise, with orthogonality controls; mirror-swap patching localizes the pipeline (image patches early, object-word tokens middle, text late). Diagnostic pipeline (ID deviation → masking sensitivity → oracle injection) localizes failures per model: LLaVA fails at the vision encoder, LLaMA at cross-modal integration. Spatial-ID auxiliary loss as a training signal: +6% on COCO-Spatial (Qwen2-2B, proof-of-concept). Analogous temporal IDs in video VLMs (shallower).

**What it kills.** (a) Steering qualitative 2D spatial directions is now *covered* — A2/A3-style interventions on left/right–above/below are no longer contributions. (b) Its §4.2 faithfulness result — wrong verbal answers strongly co-occur with wrong internal IDs — means **for qualitative relations, the readout is faithful and the bottleneck is perception/binding, not verbalization**. The naive "present but unverbalized" hypothesis is pre-refuted in the qualitative regime.

**What it leaves open (explicitly).** Nothing metric: no continuous distance, no metric depth, no trained probes, no 3D. Most tantalizing loose end: LLaVA's "front/behind" beliefs collapse onto "above/below" (depth conflated with image height) — whether metric depth is *latently present* is never tested and flagged as open.

### R2. Latent Representation of 3D Scene Topology ([arXiv:2605.07148](https://arxiv.org/abs/2605.07148), Wang & Gao — Pitt, May 2026)

**What it establishes.** On synthetic exact-geometry scenes (SynSpat3D, 1,000 scenes), mask-pooled object tokens probed at LM decoder layers of Qwen2.5-VL-7B and InternVL3-8B show **raw metric decodability is weak**: x-coordinate R²=−0.09 (worse than mean predictor), z-coordinate R²=+0.28 (discounted by the authors as a monocular-depth shortcut confound), pairwise 3D-distance RSA ρ≈0.01 — while semantics are near-perfect (shape R²=1.00). Only after cross-scene residualization (projecting out the identity/semantic subspace) does a **topological** subspace emerge at middle layers (Dirichlet-energy ratio vs permutation null). "Shaping": a Dirichlet-energy LoRA regularizer at spatial-aware layers (500 steps) transfers zero-shot to VSI-Bench (+6.3) and MindCube (+7.0), beating Kang-style 2D regularization. Steering along the probe axis shifts the *probe readout* (90% sign-correct) — **never demonstrated on the verbalized answer**.

**What it kills.** (a) "Metric spatial information is strongly linearly decodable but merely unverbalized" is *contradicted* by their data — raw metric decodability is low; they argue the metric weakness is representational, not decode-only. (b) Layer-wise probing on synthetic geometry + probe-axis steering + a shaping intervention with theory: the general recipe is taken.

**What it leaves open.** (a) They recover *topology* (rank-order neighborhood structure), never faithful **metric** distance or absolute depth post-residualization — the metric-vs-topological dissociation is unmeasured. (b) The depth-shortcut confound is flagged and dropped. (c) Probing is LM-decoder-only — the **encoder → projector → LM locus** of where metric signal is created/lost is untouched. (d) Steering-to-verbalization is their own admitted gap. Only 2 models.

**Also on the radar:** [Attention in Space](https://arxiv.org/pdf/2603.20662) (head-level functional roles for spatial reasoning — likely closes A2's "which heads" gap; read before committing to any attention-level claim). [DepthLM](https://github.com/facebookresearch/DepthLM_Official) (ICLR 2026 oral: metric depth *is* extractable from VLMs with a fine-tuned prompt/head — an existence proof that constrains "depth is absent" claims). [SpatialForge](https://arxiv.org/pdf/2605.11462), [SpatialAct](https://arxiv.org/pdf/2605.31148) (adjacent, June 2026).

---

## Overall Recommendation (revised July 2026)

The original framing — "spatial information is present in VLM representations but not used at inference" — must be retired as stated. The two revision papers bracket it: Kang et al. show the *qualitative* readout is faithful (failures are perceptual); Wang & Gao show raw *metric* decodability is low (failures are representational). What neither closes, and what the evidence now points to as the sharpest 18-week wedge:

1. **Metric-vs-topological dissociation.** Wang & Gao recover topology but never test metric fidelity post-residualization. A clean "topology-present, metric-absent (or metric-present-at-encoder, lost-at-projector)" result refines both papers and is a genuinely new finding. DepthLM's existence proof (metric depth extractable after fine-tuning) makes "where is it lost at inference?" well-posed rather than speculative.
2. **Depth-shortcut-controlled design.** Both revision papers flag depth confounds and stop (Kang: depth-height conflation, LLaVA-only; Wang & Gao: z-shortcut, discounted). Synthetic scenes that *dissociate true metric depth from monocular appearance cues* — fixed appearance, varied geometry, contradictory cues — would determine whether decodable "depth" is geometry or shortcut. Most defensible single contribution; pure rendering + probing; fits the compute budget trivially.
3. **Steering-to-verbalization + three-stage locus.** Wang & Gao steer only the probe readout; Kang steers only qualitative directions. Showing whether metric probe-axis steering flips the *verbalized* answer, and localizing metric signal across encoder → projector → LM (untouched by both), are cheap, causal, and clearly differentiated.

**Positioning sentence:** *Kang et al. showed qualitative spatial reading is faithful; Wang & Gao showed metric position is barely represented — but neither measured metric fidelity where it matters. We dissociate metric from topological spatial knowledge across the VLM pipeline, with depth-shortcut-controlled stimuli, and causally test whether recovered metric signal reaches the verbalized answer.*

Niche B (understanding↔generation) remains genuinely unclaimed and is unaffected by the revision — it stays the best second paper. Niche C is unaffected but still the highest-overhead option. The original A-RQ1 (norm rescaling) survives as a minor side experiment; A-RQ2/A-RQ3 and D-RQ1 as originally phrased should be considered superseded by the three angles above.

**Reproduction targets for W1–2:** Kang et al.'s pipeline ([code](https://github.com/Raphoo/linear-mech-vlms)) and Wang & Gao's probe setup — both must be reproduced before building on them.

*Caveats: agents read full texts where available; SpatialReward's §5.3–5.4, Wang & Gao's formal appendices (F–H, I.1), and some C-paper appendices were truncated in fetched HTML; Ill-Posed by Design (2606.24335) was read at section level only. Verify quoted numbers against the PDFs before citing. Field velocity is high — this document was materially revised twice in one day by newly-found papers. Re-run a scoping search (papers citing 2601.12626, 2605.07148, 2606.24335, and 2411.17385) every 2 weeks until submission, and verify every specific design claim with a search before it enters the proposal.*


---

## Addendum — full literature sweep, 2026-07-16 (all five anchors + topic sweep)

**Method:** complete citer enumeration for every anchor (Semantic Scholar API + web verification
of actual reference lists) PLUS an anchor-independent topic sweep of May–July 2026 arXiv — the
latter found the most important paper, which cites none of our anchors.

| Paper | What it is | Verdict vs our claims |
|---|---|---|
| **2605.20448** Do VLMs Understand 3D Scenes or Just Catalogue Objects? (Deccan AI, May 19) | 17-site activation-patching trace (ViT→merger→LM L0–27), categorical occlusion | 🔴🔴 closest competitor; reports a sharp causal-recovery discontinuity around the merger/projector, **for categorical occlusion under their patching protocol**; motivates a competing localization hypothesis. ⚠ **DR3: strictly COMPATIBLE with Anchored — not a contradiction we "adjudicate"** (different variables/methods/endpoints). No controlled continuous metric var / selection-leak-controlled probes / binding sites. |
| **2606.06714** Anchored, Not Graded | probe trace of continuous SLANT, encoder→projector→LM-input, factorial synthetic | 🔴 publishes our front half; decodable at LM-input, output anchors; LM-internal = declared future work |
| 2607.03358 Pathways of Visual Information Flow (Copenhagen) | direct vs text-mediated routing, patching, categorical | claims untouched; adopt restoration score; warnings: synthetic↔natural routing flip, prompt-format sensitivity |
| 2606.31257 Decodable Is Not Grounded (UNSW/NUS) | vision-ablation arbiter; decodability ≠ grounding | claims survive; ADOPT arbiter (blank + mismatched reruns) as mandatory M5 control; boundary: near-field depth is grounded-correct — never claim "depth unused" |
| 2605.12586 SpatialBabel (Unity) | behavioral; code-emission vs QA dissociation (r=0.12) | LOW; citable behavioral motivation |
| 2607.01503 O3-D | cue-controlled behavioral depth benchmark (models ≤ chance) | stimulus-philosophy sibling; cite |
| 2604.13321 Why MLLMs Struggle w/ Orientations | encoder-only probing of continuous orientation | "present but diffuse, downstream unknown" — convergent motivation |
| 2606.01914 Spatial Lexical Bias (Kyoto/NII) | mechanistic pipeline for relation-WORD bias | methodological sibling; cite; WATCH |

**Consequences:** (1) claim wording — 🔴 **SUPERSEDED BY DR3 (2026-07-16); retraction left visible.**
This read *"**first** leak-controlled probe trace of a controlled continuous metric depth variable
across the **full chain** incl. object-word binding sites"*. Pre-result **"first" is BANNED**, as is
"full chain" (→ "five prespecified functional stages"). **Current form:** *a stage-wise,
trivial-feature-controlled protocol for tracing object-specific depth information — continuous depth
(z; Δz/ratio secondary) as the probe target, ordinal ordering as the behavioral anchor — from visual
encoding through language-token representations including object-word binding sites.*
(2) framing — 🔴 **SUPERSEDED BY DR3.** This read *"upgraded from gap to **adjudication** of the
published projector-vs-post-projector disagreement"*. **"Adjudicates the disagreement" is BANNED:**
2605.20448 and 2606.06714 are **strictly compatible** (different variables, methods, models,
endpoints) — only their *interpretations* point at opposite ends of the LM. **Current form:** the two
motivate **competing localization hypotheses for different forms of spatial information**; we test
which pattern — projector-, binding-, or readout-bottleneck — holds for controlled continuous depth
(site-2 vs site-4 pre-registered primary, unchanged); (3) two named scoop risks with declared
follow-ups (Anchored's group, Deccan AI) → WACV R2 Aug 28 target; (4) protocol: monthly topic
sweeps added — citation graphs missed the nearest competitor for two months.
