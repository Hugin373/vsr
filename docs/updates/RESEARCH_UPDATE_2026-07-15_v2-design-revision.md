# Research Update 2026-07-15 — Stage Reframing + Occlusion Integration + Landscape Fold-In

*Produced with the advisor session after reviewing `vsr_landscape_v8.pptx` (Kaho's independent
19-paper landscape analysis, 2026-07-05, predating this project) against the live
PROJECT_MEMORY.md / IMPLEMENTATION_PLAN.md (M3-gate state). This document is a MERGE SPEC:
apply the changes below to both docs, then delete or archive this file. The landscape deck
becomes a companion document — reference it as `docs/vsr_landscape_v8.pptx`.*

---

## Change 1 — The program is STAGES, not papers/degrees (Kaho's decision, 2026-07-14)

Retire all "Paper 1 / Paper 2 / Paper 3 / PhD direction / master's thesis" labels in both docs.
The research is ONE program — **where spatial information lives, dies, and gets used** — organized
as dependency-gated stages. Publications are snapshots of whichever stages have defensible results
when a deadline passes; degree documents are bindings of completed stages. (The private CVPR 2027
target is unchanged; it just doesn't structure the science.)

| Stage | Question | Unlock gate | Current status |
|---|---|---|---|
| **S1 — Visible metric** | where metric info dies in the pipeline (binding bottleneck) | M3 GO ✅ | running (M4 = real gate) |
| **S1.5 — Occlusion & the amodal probe** | occlusion as the third (categorical) cue; is the hidden part represented and bound? | M4 passes the transferred W&G bar | new — spec below |
| **S2 — The method audit** | what do spatial fixes actually change (representation / binding / prior)? | S1 probes + baselines exist | spec'd (M7) |
| **S3 — Other readouts (generation)** | does the generation pathway read the same spatial code? | S1 finding (it tests S1's prediction) | parked |
| **S4 — The unseen** | what does the model maintain about what it cannot currently see: occluded (by things), out-of-view (by framing), future (by time); visibility graphs, spatial state, hypothetical-state probing | S1.5 amodal result (tells us whether hidden-object representation exists to study) | umbrella named; do not build |

Naming note: S4's umbrella — **"representation of the unseen"** — unifies the landscape deck's
capability levels 4–6 (visibility/permanence, dynamic state, counterfactual modeling) with the
memory/simulation ideas already in the docs. Kaho's visibility-graph idea (who-occludes-whom
edges; recurring open question in the deck) is S4's centerpiece candidate.

## Change 2 — S1.5 spec: occlusion enters the battery (new milestone **M4.5**, AFTER the M4 gate)

**Scientific motivation (add to proposal §1 as a sub-hypothesis):** occlusion is the third
classical monocular depth cue and the only *categorical* one — it carries ordinal order (A in
front of B) and ZERO metric content, whereas elevation/retinal size are graded. If VLMs lean on
occlusion as their dominant depth cue, the observed qualitative-vs-metric asymmetry follows
*in principle*: their best cue cannot carry metric information. Testable within the existing
cue-decomposition design. (This is landscape Tension T2 — geometry vs visibility-aware state —
made mechanistic.)

**Design (physically rendered, congruent-only at this stage):**
- New factor `occlusion_condition ∈ {none, partial}`: in `partial`, the nearer object partially
  overlaps the farther one, both fully physical (no compositing). Record per-object
  `occlusion_ratio` = 1 − visible_area/amodal_area.
- **Masks:** composite ID pass gives the *visible* mask (current pipeline); add a **per-object
  solo ID pass** (each object rendered alone) giving the *amodal* mask for free. Schema: per
  object add `mask_amodal`, `occlusion_ratio`, `retinal_size_px_amodal`.
- **Validation exemptions, explicit:** occluded variants are EXEMPT from the retinal/area
  congruence checks (visible height of an occluded object is not the calibrated quantity — check
  congruence on the AMODAL measurements instead). Recalibration rule (M4 note (e)) applies.

**Two questions, both cheap once M4's battery exists:**
1. **Cue-use:** at matched depth gaps, does ordinal accuracy/decodability jump when occlusion is
   present vs absent? (Behavioral + probe versions; two-ordering protocol as usual.)
2. **The amodal probe:** for a partially occluded object, are its position/depth/full extent
   decodable — at which sites — and does the occluded object still BIND (Kang's own open
   question: "do spatial IDs exist for objects behind occluders?")? Measurement detail that is
   itself a finding: pooling over the *visible* mask vs the *amodal* extent tests whether the
   representation completes the object.
- **Leak-ceiling extension:** the dumb-features baseline for occluded items must include
  *visible*-mask geometry AND `occlusion_ratio` (an amodal-decodability claim must beat a probe
  that sees the visible fragment's geometry).

**Deferred (S4, not S1.5):** occlusion cue-CONFLICT (inverted depth) — physically impossible to
render; requires O-Bench-style layered composites, which break the exact-geometry guarantee and
make ground truth cue-relative. Legitimate later; out of scope now. Also deferred: occlusion
chains (A hides B hides C), full visibility graphs.

**Verification-reads BEFORE the M4.5 design freeze** (per the standing rule):
- **Mirage Probes (arXiv 2606.13870, Jun 2026)** — "How Vision Models Fake Visual Understanding";
  probing-validity critique, directly relevant to ALL probe claims (S1 included). PRIORITY.
- arXiv 2508.04567 (masked-object linear probes, >95% — check whether "masked" ≈ our occlusion).
- arXiv 2603.28333 (MLLM-guided amodal completion) + O-Bench (occlusion benchmark; its
  inverted-depth/answer-frequency controls) + CAPTURe (amodal counting; oracle decompositions) +
  SpatialMosaic (occlusion-ratio data pipeline — engineering reference for r_obj computation).
- Search at freeze time: "amodal representation probing VLM occluded object depth" (checked
  2026-07-15: geometric probing of physically occluded objects appears OPEN; adjacent work is
  classification probes on masked objects and amodal segmentation).

## Change 3 — Folds into existing stages (from the landscape deck)

**Into S2 (method audit / M7) motivation:** the deck's cross-paper finding — **"isolated
structured perception HURTS"** (EmbodiedVSR: detector/depth/graph alone degrade; SpatiaLQA: seg
alone 67.4→50.3, depth alone →64.1; reported as 4 independent findings incl. NuScenes-SpatialQA,
ISGR) — is a behavioral mystery the audit's scaffold probing can explain mechanistically: does
isolated structured input never reach binding sites, or actively interfere? Cite these papers in
the audit's motivation; add "isolated vs integrated scaffold" as an audit condition axis
(scene-graph-alone vs depth-alone vs integrated — mirrors their behavioral contrast).

**Into S1's validation layer (M5) notes:** CausalSpatial details from the deck's read —
(a) Not-Sure-Rate analysis: NSR collapses with scale (18.77%→0.10%) while accuracy stays flat —
"larger models become decisively wrong"; use NSR as a reported metric where the abstain option
exists (the adapter already carries `meta.not_sure_letter`). (b) COW (their video-sim method)
FAILS on its own occlusion task — useful context when our oracle-injection helps/doesn't.
(c) Scale saturation (Qwen3-VL 4B/8B/30B plateau 44–46%) — a model-scale claim our per-primitive
decomposition can speak to.

**Into the proposal's framing (thesis-level, wherever the arc is described):** adopt from the
deck — (a) the **five definitions of "spatial understanding"** (behavioral / decodable / causal
use / transfer / world-modeling), with **causal use** as the program's operational definition
(this was Kaho's pre-existing commitment; the program operationalizes it); (b) the **capability
levels** (perception → relations → geometry → visibility → dynamic state → counterfactual) as the
map of which stage addresses which level (S1: 1–3; S1.5: 4-entry; S4: 4–6); (c) tensions **T1**
(representation vs interface → S2's core question), **T4** (decodability vs causal use → S1's
probe+injection pairing), **T2** (geometry vs visibility state → S1.5/S4).

**Into S3 (generation) notes:** the deck's C2 application — T2I evaluation relies on VLM judges
whose spatial verification is unproven — is independent motivation for the judge-circularity
methodology already spec'd there.

## Change 4 — Watch/reading list additions

Add to the biweekly watch + must-read lists:
- **Mirage Probes (2606.13870)** — must-read BEFORE M5 probe claims (probing validity).
- **Structural Graph Probing** (population-level neuron-correlation topology; its open question
  "would spatial IDs appear as hubs?" is adjacent to S1) — verification-read, low priority.
- O-Bench, CAPTURe, SpatialMosaic — S1.5/S4 references (above).
- The landscape deck's corpus (19 papers) merged into the literature tracking; deck archived as
  `docs/vsr_landscape_v8.pptx`.

## Change 5 — Validation-layer corrections from GROUND-TRUTH dataset inspection (2026-07-15)

*Actual rows/templates/counts were inspected (HF files, official generation & eval code,
item-level counts) — replacing paper-description assumptions. Full details in the session log;
apply these to the M5 validation-layer spec and §2.5:*

- **What'sUp — a gift we missed: subset B contains 204 front/behind items** (in-front_of/behind,
  102 each; subset A is on/under/left/right, 103 each; first-option-correct confirmed at the
  item level). → B becomes a **qualitative-DEPTH control**: categorical depth relations to
  contrast against metric depth. Caveat to record: per Kang, front/behind may be answered via the
  vertical proxy — in tabletop scenes front≈lower, so B is proxy-confounded; treat it as a
  *behavioral* control, and note the proxy story is exactly what our S1 probes can test.
- **CV-Bench 3D: FITS, three caveats.** Depth (600) is verbatim our ordinal primitive; Distance
  (600) is also ordinal (object-anchored). **Zero absolute-metric items** — never describe
  CV-Bench as metric validation. Binary choices → 50% chance, two-ordering protocol mandatory.
  ⚠ A large fraction is **Omni3D_Hypersim (photorealistic SYNTHETIC)** — audit the source-mix
  before calling it "real-image validation"; report per-source if mixed.
- **ReVSI is the validation workhorse.** Its 13 question types tag cleanly onto primitives:
  4 absolute-metric (distance m / size cm / room m²), 2 ordinal (rel-distance closest/farthest,
  4-way), 4 egocentric-qualitative (perspective-taking), 2 counting, 1 other (route). Numeric
  types scored by Mean Relative Accuracy (0.5–0.95 thresholds). ⚠ Type mix VARIES by frame
  config (16f drops room-size + route-planning) — fix the config per analysis; add
  **video/cross-frame as a nuisance covariate** (every ReVSI item adds cross-frame memory on top
  of the primitive).
- **MindCube: POOR FIT for S1's primitive decomposition — remove it from the M5 validation
  layer.** Every inspected item is multi-view perspective-taking under stated camera motion
  (rotation/among/around); nothing reduces to a single-image primitive; its own eval excludes
  the `translation` setting. Re-scope: MindCube belongs to a **cross-view integration contrast**
  (S4-adjacent), not S1 validation. (Adapter stays — nothing wasted.)
- **CausalSpatial: use the collision (n=826) and occlusion (n=189) slices only** for
  primitive-predicts-failure analyses. Compatibility (n=99, size-ratio) and realworld (n=116) are
  too small for per-category stats; physics (311) loads on physics priors, not spatial
  primitives — keep both as non-target controls. ⚠ Record their own admission that sim scenes'
  "floor strip spacing encodes depth perspective" — the depth cue is artificially legible;
  caveat any cross-dataset comparison.
- **NEW DERIVED DATASET — ReVSI-1F (decided 2026-07-15).** ReVSI is video; cross-frame demand
  varies BY CATEGORY, confounding primitive-difficulty with memory-difficulty (and LLaVA-1.5
  isn't a video model). Derivation: from `obj_visibility.json`, keep items where ALL
  `queried_object_ids` are co-visible in ≥1 frame; select the frame maximizing the minimum
  visible-pixel count across queried objects (tie-break earliest, seeded, rule in config);
  emit `revsi_1f/` with original item id + chosen `frame_idx` + per-object visibility stats +
  primitive tag. **Report per-category survival rates** (the co-visibility filter drops
  categories unevenly — that selection bias must be stated). Validate with counts + contact
  sheet. Internal instrument (Apache-2.0 permits); if ever released, ship script + index, not
  frames. Core validation layer becomes: CV-Bench Depth/Distance (ordinal) + What'sUp-B
  (qualitative-depth control) + **ReVSI-1F** (ordinal + absolute-metric, real scenes) +
  CausalSpatial collision/occlusion (consequence-level) — all single-image. Full-video ReVSI at
  2–3 budgets = labeled extension analysis only.
- **Standing rule reinforced:** a dataset enters an experiment only after item-level inspection
  (rows, templates, per-category counts, answer-format quirks) — paper descriptions and adapter
  counts are hypotheses. What'sUp-B's depth items and MindCube's poor fit were both invisible
  from descriptions.

## Change 6 — Methodological refinements from external review (2026-07-15; adopted after
independent critique — apply to proposal §1–2 and plan M4/M5/M6)

**(a) Thesis wording: "becomes unavailable or unusable," never "is lost/destroyed."** Five
mechanistically distinct possibilities the design must distinguish: erased / recoded nonlinearly /
detached from the object / present-but-ignored by the answering computation / corrupted at
verbalization. Canonical statement: *"VLMs exhibit a robust qualitative–metric spatial asymmetry,
but it remains unknown where metric fidelity becomes inaccessible to the downstream language
computation: visual encoding, multimodal projection, object–token binding, or readout."* Also:
DepthCues establishes "depth-RELATED information is recoverable from encoders," not "the metric
signal exists" — do not overclaim it. Robotics motivation stays secondary to the
representational question.

**(b) Split the hypothesis. H1 (localization, primary):** metric variables remain recoverable in
visual representations but lose *object-specific accessibility* when bound into language-token
representations. **H2 (mechanistic sub-hypothesis):** the binding transformation preferentially
preserves low-dimensional ordinal structure while collapsing continuous magnitude. Do NOT argue
"rank-3 therefore incapable" — three continuous dims can carry arbitrary precision; the coarseness
evidence is Kang's *discretized* (4×4-bin) ID derivation and Cui's ordinal-only codes, which
support H2 without proving it. Candidate mechanisms stay open: discretization, effective rank
under the data distribution, SNR, ordinal-preserving many-to-one maps.

**(c) OPERATIONAL DEFINITION OF BINDING (mandatory before M5):** *the prompt-conditioned transfer
by which object-specific visual information becomes causally available at the language-token
positions responsible for referring to and answering about that object.* Probe THREE
representation targets, not two: object-associated visual tokens; object-name text tokens; and a
JOINT visual+text token set (cross-token decoder) — a site-3→4 drop alone is vulnerable to
"different token populations, different probe conditions." **Decision rule — claim a binding
bottleneck only when ALL hold:** (1) metric recoverable from object-associated visual tokens;
(2) substantially less recoverable from that object's text tokens under matched evaluation;
(3) qualitative info DOES transfer to those same text tokens (within-model positive control);
(4) causal intervention at the transfer layers changes metric answers; (5) effects are
object-specific, not global answer bias.

**(d) Outcome matrix, formalized (replaces "every outcome is a finding"):** the design
distinguishes failure locations *provided per-site positive controls validate probe sensitivity*.
| visual sites | bound-text sites | behavior | reading |
|---|---|---|---|
| high | low | low | candidate binding bottleneck (apply decision rule (c)) |
| high | high | low | downstream access/readout failure |
| low | low | low | upstream absence OR instrument failure → identifiability check adjudicates |
| low | high | high | probe/site mismatch — investigate before interpreting |
| high | low + injection restores | — | strong causal support |
| high | low + injection fails | — | binding loss epiphenomenal or intervention inadequate |

**(e) THREE stimulus regimes, not two:** natural-congruent / **counterbalanced** (nuisance cues
vary independently, scenes stay plausible) / conflict. **The primary localization claim lives in
the counterbalanced regime** — conflict is for cue-integration analyses, congruent for controls.
Preempts the OOD attack structurally.

**(f) IMAGE-IDENTIFIABILITY GATE (new M4-pilot acceptance criterion):** exact renderer GT ≠
pixel-inferable GT. Before any "encoder failure" claim: a directly-supervised model on raw
pixels (or oracle geometric image features) must recover each target variable; spot-check human
performance on a subset. If the image doesn't contain the evidence, no site can.

**(g) Leak-ceiling refinement:** report three numbers per cell — best dumb-feature score; probe
score; and **Δ_repr|dumb = score(dumb ∪ representation) − score(dumb)** (the incremental-gain
form is the load-bearing one). Held-out splits must target the claimed generalization: held-out
object identities, camera poses, depth RANGES, cue combinations — never only random image splits.

**(h) Probe-capacity ladder:** linear (primary, comparable to prior work) → low-rank linear →
shallow MLP → controlled kernel → RSA/ranking. Where signal "disappears" between sites, the
nonlinear tier distinguishes ERASED from RECODED. Interpretation: linear-high = directly
accessible; nonlinear-only = present but recoded; neither (with validated sensitivity) =
unavailable; high-globally-but-low-object-conditionally = binding/assignment failure.

**(i) Anchor experiment PROMOTED to a core mechanistic experiment** (prompt-conditioned binding
test): same image; prompts {no reference / refer to B / ask A-relative-to-B}; compare
representation changes for A, B, unrelated objects, answer tokens. Distinguishes absolute
encoding / relational recoding / answer-only computation / binding-dependent relationalization.

**(j) Injection anti-"logit-hack" controls (M6):** layer controls (hypothesized vs early/late);
position controls (object tokens vs unrelated); content controls (correct vs sign-flipped vs
shuffled vs random-direction); dose-response; generalization to unseen values; paraphrase
transfer; free-response + ordinal ranking, not only MCQ; qualitative controls undegraded; and
**the mediation pattern: injection → downstream metric decodability rises → behavior improves.**
Injection that moves answers without moving downstream decodability is answer steering, not repair.

**(k) MINIMAL PUBLISHABLE CORE + pilot scope (replaces "4–6 models everywhere"):** the pilot
FIXES the final analysis matrix, not just the generator. Core = 2 architectures (Qwen2.5-VL-7B +
LLaVA-1.5-7B — one modern M-RoPE, one classic CLIP, both already cached), ONE metric variable
(egocentric depth), one qualitative positive control, four sites, leak-controlled linear+MLP
probes, one behavioral test, one intervention. Expansion to 4–6 models happens only after the
site-wise pattern stabilizes on two. **Pilot exit criterion:** ≥1 model shows metric decoding
above the nuisance ceiling at an upstream site (or strong evidence the premise fails) + the
identifiability gate passes + the W&G gradient emerges. **M6's intervention is CHOSEN by M5's
pattern** (upstream-low → encoder/projector intervention; visual-high/text-low → binding;
text-high/behavior-low → readout) — do not pre-commit to binding-layer injection.

## Change 7 — SpatialRGPT-Bench: ADD WITH CAVEATS (item-level inspection 2026-07-15)

`a8cheng/SpatialRGPT-Bench` (HF, ungated, 1,406 rows, val only): 657 qualitative + 749
quantitative; GT from **Omni3D real 3D cuboid annotations** (SUNRGBD-dominant, ARKitScenes,
nuScenes, KITTI, Hypersim) — sensor/synthetic GT, NOT monocular-pseudo-GT, so no shared failure
modes with evaluated models; but QA generation is templated with **no human verification pass**
(GT tier: below ReVSI's human re-annotation, above auto-pseudo-GT). Usage rules:
- Core signal = the **~375 inter-object distance items** (direct/horizontal/vertical) — absolute
  metric, the type CV-Bench lacks. There is NO ratio type and no closer-to-camera type.
- **Width/height are prior-contaminated:** blind GPT-4 (no image) scores 48–52% within ±25% —
  always report a blind-LLM baseline alongside; treat as secondary.
- Evaluate generic VLMs with **SoM-drawn marks** (their own baseline protocol), never text
  referral (breaks on same-class regions); bboxes+RLE masks ship in the JSON.
- **Replace the GPT-4 judge** with deterministic number-extraction + configurable relative-error
  thresholds; report ±10% and AbsRel alongside their lenient ±25%. Unit lottery (in/ft/cm/m) makes
  exact match meaningless.
- License murky (GitHub says Apache-2.0, HF card untagged, nuScenes/KITTI upstream
  non-commercial) — internal eval use only.
Validation layer final: CV-Bench Depth/Distance (ordinal) + What'sUp-B (qualitative-depth) +
ReVSI-1F (ordinal + absolute, human-verified GT) + **SpatialRGPT-Bench distance slice** (absolute,
sensor GT) + CausalSpatial collision/occlusion (consequence). R3D (2607.02921) added to watch.

## Change 8 — Program-level refinements from second external review (2026-07-15; apply to
proposal framing + stage specs; stage maturity labels mandatory)

**(a) Canonical program question (replaces the enumerating sentence):** *"How is object-specific
spatial state represented, transferred, and causally used across multimodal model computations?"*
— tested under four increasingly demanding information conditions: visible / partially occluded /
previously-visible-now-absent / hypothetical.

**(b) Program hypothesis DE-DIRECTIONALIZED (the old "progressive loss" phrasing prejudged
later stages):** *"Spatial failure is not a unitary absence of geometry. It can arise because
spatial information is weakly encoded, loses object-specific structure during multimodal
transfer, remains represented but inaccessible to the relevant readout, or is not causally used.
The program localizes these failure modes across visible, occluded, absent, and hypothetical
spatial states, then tests whether interventions repair the responsible transition."* S1 keeps
its directional claim (S1-H1/H2) as a stage hypothesis, not the program's.

**(c) Evidential ladder, program-wide:** representation ⊂ accessibility ⊂ causal task use.
"Spatial understanding = causal use" is qualified to **task-relevant** causal use: *the
represented variable causally contributes to the corresponding output under controlled
intervention* — failure of one answering pathway ≠ absence of understanding in every sense.

**(d) THREE-AXIS PROGRAM CUBE (adopt as the canonical organizing figure & thesis structure):**
Axis A information condition {visible / occluded / absent / hypothetical} × Axis B computational
transition {encoding / interface / binding / readout / memory / generation} × Axis C evidential
level {decodable / object-specific / accessible / causally used / repairable}. Each stage
occupies a declared region of the cube.

**(e) S1: "four sites" become FIVE FUNCTIONAL STAGES,** because architectures aren't homologous
(projector vs resampler vs interleaving; binding emergent over layers): (1) vision-encoder
representation; (2) vision→language interface output; (3) early multimodal LM representation;
(4) object-conditioned language representation; (5) answer/readout representation. Per
architecture, a table maps each functional stage to its concrete tensor. Also: dataset framing =
**one primary identification instrument** (the factorial battery) + **a small PREDECLARED
external-validation set** (qualitative control / ordinal / absolute / consequence) — the external
list is closed, not extensible.

**(f) S1.5 corrections:** (i) DROP "occlusion is the only categorical cue / zero metric content"
— false as stated (T-junctions, containment, support are also ordinal cues; occlusion boundaries
+ known shapes + camera geometry constrain metric depth). Corrected claim: *"occlusion is
primarily an ordinal visibility cue — it identifies front–behind ordering more directly than
continuous magnitude; over-reliance on it could support qualitative depth while leaving metric
depth poorly represented."* (ii) Split the amodal hypothesis: **H1.5a object persistence**
(entity-level representation survives partial visibility) / **H1.5b amodal geometry** (hidden
extent recoverable beyond visible-fragment features) / **H1.5c amodal binding** (available at
object-referential tokens). (iii) ⚠ Amodal-extent POOLING is insufficient — pooling under the
invisible mask mostly collects occluder/background tokens. Test *implicit* representation:
visible-fragment pooled / occluder-region / object-name token / joint decoder conditioned on
object identity — do not assume hidden geometry is spatially stored under the hidden mask.

**(g) S2: three-way labels become a FIVE-DIMENSIONAL MECHANISM PROFILE per method:**
(ΔR_visual: upstream representational gain; ΔR_bound: object-specific transfer gain; ΔB: readout
gain conditional on matched internal decoding; ΔP: prior reliance under blind/black/
geometry-conflict controls; ΔC: causal repair — mediation + specificity). Categories are not
mutually exclusive; report the vector. Plus a **checkpoint comparability checklist** (tokenizer,
image resolution, prompt/conversation template, preprocessing, transformers revision) before any
base-vs-finetune internal comparison. S2 stays prioritized ahead of S3 unless S1 yields a strong
readout-specific result.

**(h) S3: hypothesis SYMMETRIZED to branch-point localization:** *"if failure originates before
the shared representation, both pathways fail on the same relations; if during task-specific
binding/readout, failures dissociate after the branch point."* "Generation suffers less from
lexical binding loss" survives only as a derived corollary conditional on S1's finding. Probe
transfer must be defined at three levels: decoding transfer / subspace alignment / causal
direction transfer (strongest, hardest).

**(i) S4 becomes a RESEARCH FAMILY with three branches — only one becomes the next project,
selected by earlier results:** S4-A hidden extent & visibility graph; S4-B persistent spatial
memory (out-of-view, KV-cache); S4-C hypothetical spatial state. Reformulate the visibility
hypothesis neutrally: *"models may encode scalar visibility attributes without maintaining
relational occluder–occludee structure — we test whether pairwise structure is represented,
bound, and used"* (don't presuppose the negative). Inverted-depth composites = one conflict
regime only (compositing-artifact confound); physically rendered occlusion chains primary.

**(j) Evaluation-law refinement (the one place the review overcorrects, resolved by synthesis):**
the worst-case rule stays for **deterministic, constructible quantities** (rendered geometry,
cue constants — extremes are measured exactly; means were the proven failure). For **sampled/
statistical quantities**, use the reviewer's form: no aggregate threshold without checking the
weakest PREspecified stratum + condition-wise uncertainty (CIs, quantiles, failure-rate
distribution) — one noisy item must not define a gate unless scientifically required.

**(k) Stage maturity labels (mandatory wherever stages are described):** S1 = executable paper
plan · S1.5 = well-formed extension · S2 = strong next-paper candidate · S3 = comparative
framework needing operational definitions · S4 = long-horizon agenda (three candidate projects,
not one experiment).

## Merge instructions for the coding agent (covers Changes 1–8; doc edits ONLY, no code)

**Order of operations: read this whole file first, then edit the three docs, then archive.**

1. **PROJECT_MEMORY.md**
   - Replace the "Research arc" section with the Stage table (Change 1), adding the maturity
     labels from Change 8(k) to each stage row.
   - Add the canonical program question + de-directionalized program hypothesis (8a, 8b) and the
     evidential ladder (8c) as a short "Program frame" block above the stage table.
   - Fold Change 3 items into the relevant sections (M4 design constraints ← S1.5 schema/
     validation notes; dataset rules ← NSR metric note; audit notes ← isolated-perception-hurts).
   - Append to the must-read/watch lists: Mirage Probes 2606.13870 (PRIORITY, pre-M5),
     2508.04567, 2603.28333, O-Bench, CAPTURe, SpatialMosaic, Structural Graph Probing,
     R3D 2607.02921; note `docs/vsr_landscape_v8.pptx` as a companion document (Change 4).
   - Record the dataset ground-truth corrections + ReVSI-1F decision + SpatialRGPT-Bench
     verdict (Changes 5, 7) under the dataset-rules section.
   - Update the evaluation-law wording with the two-clause threshold rule (8j).
   - Update "Current state / next step": M4.5 exists, unlocks only on M4's transferred bar;
     stage labels replace paper labels everywhere.
2. **IMPLEMENTATION_PLAN.md**
   - Insert **M4.5** between M4 and M5 with the Change-2 spec, REVISED by Change 8(f): the
     corrected occlusion-cue claim, the H1.5a/b/c split, and the implicit-representation test
     menu replacing naive amodal-extent pooling. Acceptance: solo-ID amodal masks validated
     (amodal ⊇ visible, ratio ∈ [0,1)); occlusion renders pass exempt-adjusted validation;
     H1.5a/b/c analyses runnable from cache. Do NOT start M4.5 unprompted.
   - M4/M5: rename the four sites to the FIVE FUNCTIONAL STAGES of 8(e) and add the
     per-architecture tensor-mapping table as an M4 deliverable; restate the dataset framing as
     primary-instrument + closed predeclared external-validation set (8e); fold Change 6 items
     (three regimes with counterbalanced primary; image-identifiability gate as an M4-pilot
     acceptance criterion; Δ_repr|dumb incremental form + structured held-out splits; probe
     ladder; anchor experiment promoted; outcome table 6(d); minimal-core pilot scope + exit
     criteria 6(k)).
   - M6: add the injection control battery incl. mediation (6j); M6's design is selected by
     M5's pattern via the three-branch rule.
   - M7: rename to "S2 audit"; replace the three-way outcome labels with the five-dimensional
     mechanism profile + checkpoint comparability checklist (8g); add the isolated-vs-integrated
     scaffold axis (Change 3).
   - §2/§2.5: add ReVSI-1F derivation spec (Change 5), SpatialRGPT-Bench row + usage rules
     (Change 7); local verification TODOs: CV-Bench source-mix fractions; What'sUp-B counts.
   - §5 gotchas: Mirage Probes pre-M5 must-read; two-clause threshold rule (8j).
3. **docs/research_proposal_spatial_binding.md**
   - Replace the program framing with 8(a)+8(b)+8(c); insert the three-axis cube (8d) as the
     program map; apply the S1 hypothesis wording of Change 6(a,b) (H1/H2, "unavailable or
     unusable", DepthCues wording); add the five-condition binding decision rule (6c); replace
     the arc section with the stage table + maturity labels; update S1.5/S2/S3/S4 hypothesis
     statements per 8(f,g,h,i).
4. Do NOT renumber existing milestones M0–M7. Preserve all existing agent-authored content not
   explicitly amended here.
5. Archive this file to `docs/updates/RESEARCH_UPDATE_2026-07-15.md` when done.
6. Commit as `docs: design revision 2 — stages, occlusion (M4.5), dataset ground-truth
   corrections, external-review refinements (changes 1-8)`.
