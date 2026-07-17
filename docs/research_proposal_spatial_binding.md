# Research Proposal — Object-Specific Spatial State in Vision-Language Models: Representation, Transfer, and Causal Use

*Kaho, July 2026 (framing revised 2026-07-15). Compute: lab cluster, 8× RTX A6000 48 GB. Companion documents: `VSR_niches_critical_deep_read.md` (critical literature analysis), `vsr_landscape_v8.pptx` (19-paper landscape), `IMPLEMENTATION_PLAN.md` (build spec), `PROJECT_MEMORY.md` (state).*

---

## 0. The Program

**Canonical question:** *How is object-specific spatial state represented, transferred, and causally used across multimodal model computations?* — tested under four increasingly demanding information conditions: **visible / partially occluded / previously-visible-now-absent / hypothetical.**

**Program hypothesis (deliberately non-directional).** *Spatial failure is not a unitary absence of geometry. It can arise because spatial information is weakly encoded, loses object-specific structure during multimodal transfer, remains represented but inaccessible to the relevant readout, or is not causally used. The program localizes these failure modes across visible, occluded, absent, and hypothetical spatial states, then tests whether interventions repair the responsible transition.* Directional claims belong to individual stages (S1 keeps its own), **not** to the program — an earlier "progressive loss" phrasing prejudged what the later stages exist to find out.

**Evidential ladder (program-wide), operationalized at DR3-r3 as five rungs:** `linearly decodable ⊂ image-grounded decodable (arbiter + nuisance baselines) ⊂ causally alterable (controlled intervention) ⊂ object-specific mediated use (specificity + mediation) ⊂ task-relevant causal use` (DR3-r5: rung 3 renamed — a generic intervention that moves answers is rung-3 evidence only with off-target controls; 'available/used' start at rung 4). The former three-term ladder compressed rungs 2–3 into "accessibility", letting probes+controls claim too much. "Spatial understanding = causal use" is qualified: *the represented variable causally contributes to the corresponding output under controlled intervention.* Failure of **one** answering pathway is not absence of understanding in every sense.

**The program cube (organizing figure; also the thesis structure).** Each stage occupies a declared region of:
- **Axis A — information condition:** visible / occluded / absent / hypothetical
- **Axis B — computational transition:** encoding / interface / binding / readout / memory / generation
- **Axis C — evidential level:** decodable / object-specific / accessible / causally used / repairable

**Stages and their maturity** (publications are snapshots of whichever stages have defensible results at a deadline; degree documents bind completed stages — the private CVPR 2027 target does not structure the science):

| Stage | Question | Unlock gate | Maturity |
|---|---|---|---|
| **S1 — Visible metric** | where metric fidelity becomes inaccessible to the language computation | M3 GO ✅ | **executable paper plan** |
| **S1.5 — Occlusion & the amodal probe** | is the hidden part represented, object-specific, and bound? | **M4b** clears its validity gate (5 conditions, DR3) | **well-formed extension** |
| **S2 — The method audit** | what do spatial "fixes" actually change? | S1's probes + baselines exist | **strong next-paper candidate** |
| **S3 — Other readouts (generation)** | does the generation pathway read the same spatial code? | an S1 finding (S3 tests it) | comparative framework — **needs operational definitions** |
| **S4 — The unseen** | what is maintained about what cannot currently be seen? | S1.5's amodal result | **long-horizon agenda** (three candidate projects, not one experiment) |

## 1. S1 — Locating Where Metric Fidelity Becomes Inaccessible

**Canonical statement of the problem:** *VLMs exhibit a robust qualitative–metric spatial asymmetry, but it remains unknown where metric fidelity becomes inaccessible to the downstream language computation: visual encoding, multimodal projection, object–token binding, or readout.*

⚠ **Wording discipline: "becomes unavailable or unusable" — never "is lost" or "is destroyed."** Five mechanistically distinct possibilities the design must distinguish, which the loss vocabulary silently collapses: metric information may be **erased**, **recoded nonlinearly**, **detached from the object**, **present-but-ignored** by the answering computation, or **corrupted at verbalization**.

- **H1 — localization (primary), split into two predictions (DR3-r3 — "accessibility" must not be
  claimed from probes alone):
  · probe-level prediction:** continuous depth remains linearly recoverable at visual sites but
  becomes **substantially less linearly recoverable** at object-word sites;
  **· causal-level prediction:** targeted intervention at those sites changes **object-specific**
  depth answers. **Only the two together license an accessibility/binding claim.**
- **H2 — mechanistic sub-hypothesis, SPLIT at DR3-r4 (the 'or' let two different outcomes both
  count as confirmation):
  · H2a (representational):** ordinal information remains linearly recoverable at object-word
  sites while continuous magnitude declines there;
  **· H2b (causal):** continuous-magnitude interventions show weaker object-specific behavioral
  mediation than ordinal interventions.
  Each is tested by its own instrument; whether a decline reflects compression, recoding,
  detachment, or non-use is what the probe-capacity ladder and interventions determine.
- **H-occ — sub-hypothesis (S1.5, tested in the same battery):** occlusion is **primarily an ordinal visibility cue** — it identifies front–behind ordering more directly than continuous magnitude. **Over-reliance on it could support qualitative depth while leaving metric depth poorly represented.** *(Do not claim occlusion is "the only categorical cue" or carries "zero metric content" — false as stated: T-junctions, containment and support are also ordinal cues, and occlusion boundaries combined with known shapes and camera geometry do constrain metric depth.)*

⚠ **Do NOT argue "rank-3, therefore incapable."** Three continuous dimensions can carry arbitrary precision. The coarseness evidence is Kang's **discretized** (4×4-bin) ID derivation and Cui's ordinal-only codes; these **support H2 without proving it**. Candidate mechanisms stay open: discretization, effective rank under the data distribution, SNR, ordinal-preserving many-to-one maps.

This composes three established results that have never been connected:

1. **Kang et al.** ([2601.12626](https://arxiv.org/abs/2601.12626), Caltech): qualitative 2D relations reach the answer by binding a *coarse, rank-3* "spatial ID" to the object's text token at middle LM layers (causal, 11 models). Their faithfulness result: qualitative failures are perceptual — the readout is faithful. They never probe metric quantities; they flag depth (conflated with image height) as open.
2. **DepthCues** ([2411.17385](https://arxiv.org/abs/2411.17385), CVPR 2025): human-like monocular depth cues are decodable from modern *vision encoders*. ⚠ **Stated precisely: this establishes that depth-RELATED information is *recoverable* from encoders — NOT that "the metric signal exists" there.** Do not overclaim it; the identifiability gate (§2.4) is what licenses any "the encoder had it" claim.
3. **Ill-Posed by Design** ([2606.24335](https://arxiv.org/abs/2606.24335), June 2026): behaviorally, VLM metric estimates barely use scene geometry — identity/category priors dominate; LoRA learns the task *without* learning to use geometry.

The two endpoints (signal present in encoders; geometry unused in behavior) are established. **The pipeline between them — where between encoder and answer the metric signal stops mattering — is unlocalized. That localization is this project.**

Constraint from Wang & Gao ([2605.07148](https://arxiv.org/abs/2605.07148)): raw metric decodability at LM decoder layers is low (x-coord R²<0, distance RSA≈0), while a *topological* subspace survives. The claim is therefore not "metric is present but unverbalized" — it is a **localization claim**: metric fidelity is high at the encoder, degrades at identifiable stages (projector / binding / readout), and the degradation profile causally explains behavior.

Fifth anchor — **Dual Mechanisms of Spatial Variable Binding** ([2603.22278](https://arxiv.org/abs/2603.22278), v2 Jun 2026, Cui et al. — Bau/Torralba groups): causal interchange interventions show *ordinal* ordering information is carried by content-independent representations distributed in strips across visual tokens (including background), with an LM-side backup; probe-direction amplification corrects 40–55% of failures on COCO-spatial. **Terminology note:** their "spatial variable binding" = ordering-ID binding in the LM (qualitative); our "binding" = the vision→text-token step (Kang-style). We cite them as the ordinal counterpart to our metric claim, and adopt their evaluation standards (§2.3). Still absent from their work: metric quantities, site-wise decomposition (post-projector only), text-token binding sites, probe-vs-verbalization.

**Positioning sentence:** *Kang et al. showed qualitative spatial reading is faithful; Wang & Gao showed metric position is barely recoverable at LM layers; DepthCues and Ill-Posed by Design establish the endpoints. We localize where metric spatial information becomes inaccessible to the language computation, with depth-shortcut-controlled stimuli, and causally test whether repairing that transition repairs behavior.*

The representational question is primary; **robotics/embodied motivation stays explicitly secondary.**

**Positioning update 2 (2026-07-16, revised at Design Revision 3 — supersedes the earlier
"adjudication" framing).** Two very recent stage-localization studies motivate **competing
localization hypotheses for different forms of spatial information**: **2605.20448** (activation
patching, ViT→merger→LM, *categorical occlusion*) reports a sharp causal-recovery discontinuity
around the merger/projector boundary; **Anchored, Not Graded (2606.06714)** (probes, factorial
*continuous slant*, encoder→LM-input only) finds geometry decodable at LM-input while verbal
output anchors, and interprets this as a representation-to-output failure — with the LM interior
explicitly unmeasured (their declared future work). ⚠ These results are **strictly compatible**
(different variables, methods, models, endpoints); only their *interpretations* point at
opposite ends of the LM. Do NOT frame this as a published contradiction we "adjudicate" — frame
it as **a variable-specific localization question no existing study can answer:** *does
controlled continuous depth follow a projector-, binding-, or readout-bottleneck pattern?*
Neither paper uses a controlled continuous metric variable through the full chain,
leak-controlled probes, or object-word binding sites.
**Claim, pre-result wording (Design Revision 3; the two-level variable structure is part of the
claim):** *we develop a stage-wise, trivial-feature-controlled protocol for tracing
object-specific depth information — **continuous depth (z; Δz/ratio secondary) as the probe
target, ordinal ordering as the behavioral anchor** — from visual encoding through
language-token representations including object-word binding sites, testing which localization
pattern holds (pre-registered site-2 vs site-4 primary contrast).* A scoped "first" claim may be
added at write-up only after results and a fresh sweep. Supporting neighbors, cited: 2606.31257
(decodability ≠ grounding; we adopt its vision-ablation arbiter), 2607.03358 (direct vs
text-mediated routing; synthetic↔natural flip caveat), SpatialBabel 2605.12586 and O3-D
2607.01503 (behavioral dissociations motivating internal analysis).

## 2. S1 Design

### 2.1 Measurement taxonomy

"Metric" is decomposed by what monocular geometry permits, **stated conditionally (Design
Revision 3)**: **ordinal** depth is often constrained by monocular evidence; **ratio** distance
is recoverable only under geometric assumptions (calibration, support plane, known camera);
**absolute** metric additionally requires a scale prior. Our battery *supplies* these conditions
by construction (exact calibration, known geometry), and the image-identifiability gate
**verifies rather than assumes** per-level recoverability. Core claims target ordinal + ratio;
absolute is a secondary, explicitly prior-framed analysis (ReVSI showed absolute-scale scores are
contaminated by category priors — e.g., size "estimation" from black videos). **Two-level
variable structure (claim-level): continuous depth (z; Δz/ratio secondary) is the PROBE target;
ordinal ordering is the BEHAVIORAL anchor; qualitative is the positive control. Never write
"ordinal depth" and "continuous metric depth" interchangeably in a claim sentence.**

### 2.2 Stimuli — THREE regimes, not two

Blender rendering with exact geometry, decorrelating what nature correlates (true depth × vertical image position × retinal size):

1. **natural-congruent** — all cues agree. *Controls only.*
2. **counterbalanced** — nuisance cues vary **independently** while scenes stay **plausible**. **⚠ THE PRIMARY LOCALIZATION CLAIM LIVES HERE.** This is what structurally preempts the OOD attack: the claim does not rest on physically bizarre images.
3. **conflict** — cues actively disagree. *For cue-integration analyses only* (weighted fusion vs winner-take-all — the psychophysics framing Ill-Posed by Design's real-photo edits cannot run).

Two object sets (canonical-size objects vs arbitrary primitives — their difference measures the size-prior contribution). Occlusion (`none` / `partial`, physically rendered) enters as a factor at S1.5.

### 2.3 The causal chain

**OPERATIONAL DEFINITION OF BINDING (mandatory, fixed before any probing):** *the prompt-conditioned transfer by which object-specific visual information becomes causally available at the language-token positions responsible for referring to and answering about that object.*

1. **Probing grid over FIVE functional stages** (architectures are not homologous — projector vs resampler vs interleaving; binding is emergent over layers — so the sites are defined **functionally** and mapped per architecture to concrete tensors): **(1)** vision-encoder representation → **(2)** vision→language interface output → **(3)** early multimodal LM representation → **(4)** object-conditioned language representation → **(5)** answer/readout representation. Per layer, per quantity (ordinal/ratio/absolute; depth vs lateral axis).
   **Probe THREE representation targets, not two:** object-associated **visual** tokens; object-name **text** tokens; and a **JOINT visual+text token set** (cross-token decoder). A bare site-3→4 drop is vulnerable to "different token populations, different probe conditions" — the joint decoder is what closes that hole.
   **Adopted standards (Cui et al. v2):** probe mask-pooled object tokens AND all-token/strip-level representations (spatial signal is distributed across background tokens; object-pooled-only probing underestimates what survives); two-ordering strict MCQ protocol; random-direction nulls; fixed-α and per-example-α (Probe*) reporting.

   **DECISION RULE — claim a binding bottleneck only when ALL FIVE hold:**
   1. metric information has **significant incremental recoverability** from object-associated
      **visual** representations, beyond prespecified selection- and annotation-derived nuisance
      features, **under matched nested evaluation** (dumb-only / representation-only / combined /
      Δ with permutation CI; matched token-count and region-shape controls — DR3-r3/r6: the token
      *selection* itself can encode location, and Δ alone is not the criterion);
   2. it is **substantially less** recoverable from that object's **text** tokens *under matched
      evaluation* — **defined as: equal probe class and regularization (nested CV), matched probe capacity,
      equalized sample counts, comparable pooling dimensionality, stage-specific nuisance
      baselines (text side: token identity/position, mention order, template role;
      lexical-identity controls), and a CI on the cross-stage DIFFERENCE itself** (DR3-r3: visual and text tokens are non-equivalent populations;
      an unmatched comparison can manufacture the visual-high/text-low contrast as a readout
      mismatch);
   3. **qualitative** information **does** transfer to those same text tokens (within-model positive control);
   4. a **held-out, depth-specific intervention** at the candidate transfer layer changes **the
      relevant internal depth readout AND the corresponding object-specific answer** (DR3-r5:
      mediation moves INSIDE the decision rule — a generic vector that changes answers globally
      does not satisfy this condition);
   5. effects are **object-specific**, operationalized by **reference redirection** (DR3-r4):
      renaming or re-referencing the object redirects the effect; intervening on the non-target
      object does not reproduce it; adding a distractor does not absorb it; the effect follows
      the **referred object**, not a fixed token position or answer option.

   **Operationalization of 4–5 (DR3-r2 — influence-at-a-layer ≠ binding):** a BINDING reading
   additionally requires that the intervention affects the CORRECT object's text token
   (wrong-object intervention does not produce the same change), that the transfer is
   prompt-conditioned, and that renaming/re-referencing the object REDIRECTS the effect —
   object swaps, distractor controls, and name-reference manipulations are the concrete tests.

   **Outcome matrix** (replaces the vacuous "every outcome is a finding" — and it holds *only if* per-site positive controls validate probe sensitivity):

   | visual sites | bound-text sites | behavior | reading |
   |---|---|---|---|
   | high | low | low | candidate binding bottleneck → apply the five-condition decision rule |
   | high | high | low | downstream access / readout failure |
   | low | low | low | upstream absence **OR** instrument failure → the identifiability gate adjudicates |
   | low | high | high | probe/site mismatch — investigate before interpreting |
   | high | low + injection **restores** | — | strong causal support |
   | high | low + injection **fails** | — | binding loss epiphenomenal, or intervention inadequate |

   **Probe-capacity ladder** — linear (primary, comparable to prior work) → low-rank linear → shallow MLP → controlled kernel → RSA/ranking. Where signal "disappears" between stages, the nonlinear tier is what distinguishes **ERASED** from **RECODED**. Interpretation: linear-high = directly accessible; nonlinear-only = present but recoded; neither (with validated sensitivity) = unavailable; high-globally-but-low-object-conditionally = **binding/assignment failure**.

   **Leak ceiling — report THREE numbers per cell:** best dumb-feature score; probe score; and **Δ_repr|dumb = score(dumb ∪ representation) − score(dumb)**. ⚠ **The incremental-gain form is the load-bearing one** (mask geometry alone already gives x R² = 0.942 on our v0 set). Held-out splits must target the **claimed generalization** — held-out object identities, camera poses, depth **ranges**, cue combinations — **never only random image splits.**

   **Three estimators, not one — and they must agree.** (a) mask-pooled (leaky; reported for comparison); (b) fixed-grid **strip** probes (leak-free — not selected by object position); (c) the **contrastive-pair estimator** — pairs **matched on mask geometry, differing in true depth**, decoding depth from the *difference* of their activations. Where the ceiling *subtracts* the leak, (c) makes it **inexpressible by construction**: identical mask geometry ⇒ no function of mask geometry can separate the pair ⇒ the dumb-features probe is at chance **by design**. ⚠ Its matched pairs must be **rendered on purpose** (a stimulus-battery deliverable) — post-hoc matching within a tolerance leaves exactly the residual the probe would exploit.

   **Prior art, cited explicitly:** the dumb-features ceiling is a **descendant of control tasks** (Hewitt & Liang 2019; Belinkov 2022), and the contrastive-pair estimator descends from **Why Far Looks Up's minimal contrastive pairs** — neither is a new invention. **Our contribution is narrower and more defensible: the SELECTION leak** — *the pooled vector is chosen BY the object's image position, so the selection IS the answer* — together with the incremental-gain form of the ceiling and the application of matched pairs to that leak.

   **Positioning of the leak result — additive, not corrective.** Wang & Gao's confound taxonomy controls the **cue shortcut** (apparent size) and **semantic residualization**; **we complete it with SELECTION.** *(Verified 2026-07-16 by reading their appendices F–I.4 verbatim and inspecting their code read-only: the selection leak is neither mentioned nor controlled; their only shortcut control is size-based, with no `(u,v)` features anywhere.)* ⚠ **Why Far Looks Up's text-delta probe is IMMUNE to the leak** (visual components cancel in the delta) — do not list them as leak-affected.
2. **Probe-vs-verbalization comparison** with three fairness defenses: rank correlations (not raw R²), few-shot-calibrated verbalization baseline, and oracle-text condition (ground-truth coordinates as text → proves the reasoning/verbalization machinery works given resolved input).
3. **Anchor experiment — PROMOTED to a core mechanistic experiment** (it is the prompt-conditioned *binding* test, not a side manipulation). Same image; prompts {no reference / refer to B / ask A-relative-to-B}; compare representation changes for **A, B, unrelated objects, and answer tokens**. This is what distinguishes absolute encoding / relational recoding / answer-only computation / binding-dependent relationalization.
4. **Causal repair**: a **graded intervention along a validated depth-related direction or subspace** (DR3-r2: 'metric ID' is reserved until the construction is formally defined — candidate constructions: probe direction, regression-derived depth vector, matched-condition activation difference, low-rank depth subspace, interchange between depth-matched scenes; these have DIFFERENT causal interpretations and the choice must be stated). Measure verbalized-answer recovery with dose-response (see §4).

### 2.4 The image-identifiability gate (must pass before any "encoder failure" claim)

**Exact renderer ground truth ≠ pixel-inferable ground truth.** Before concluding that *any* site fails to carry a variable, show the **image contains the evidence**: a directly-supervised model on raw pixels (or oracle geometric image features) must recover each target variable, plus a human spot-check on a subset. **If the image doesn't contain it, no site can** — and a "low everywhere" result would be an instrument failure masquerading as a finding.

### 2.5 Intervention block — and its anti-"logit-hack" controls

**Site selection, DR3-r5 (the old 'chosen by the probing pattern' rule risked circular analysis —
inspect all stages, pick the largest drop, intervene there, declare confirmation):** the
**PRIMARY intervention site is PREREGISTERED** (the stage-2 vs stage-4 contrast, matching the
probing primary). Probe-indicated sites beyond it are **EXPLORATORY** and must be **confirmed on
held-out data** (new scenes/splits untouched by site selection). The probing pattern still
*informs* the exploratory branch: upstream-low → encoder/projector; visual-high/text-low →
binding; text-high/behavior-low → readout. **Direction validation is split-independent:** the
depth direction/subspace is constructed on training data, validated on a separate split, and
causally evaluated on untouched test scenes.

**Control battery (all of it, or the result is answer steering):** layer controls (hypothesized vs early/late); position controls (object tokens vs unrelated); content controls (correct vs sign-flipped vs shuffled vs random-direction); dose-response; generalization to unseen values; paraphrase transfer; free-response **and** ordinal ranking, not only MCQ; qualitative controls undegraded. **And the mediation pattern: injection → downstream metric decodability rises → behavior improves.** ⚠ **Injection that moves answers *without* moving downstream decodability is answer steering, not repair.**

### 2.6 Validation layer — a small, CLOSED, predeclared external set

The factorial battery is the **one primary identification instrument**. External data serves **validation only**, from a **closed predeclared list** (it is not extensible mid-project — that is what keeps it from becoming a fishing expedition). All single-image:

| Role | Instrument | Verified basis |
|---|---|---|
| qualitative-depth control | **What'sUp subset B** — 204 front/behind items (`in-front_of` 102, `behind` 102; verified by full scan) | ⚠ proxy-confounded: per Kang, front/behind may be answered via the vertical proxy (in tabletop scenes front≈lower). Treat as **behavioral** control — and note the proxy story is exactly what our S1 probes can test. |
| ordinal | **CV-Bench Depth (600) + Distance (600)** | Verbatim our ordinal primitive; object-anchored. **Zero absolute-metric items — never describe CV-Bench as metric validation.** Binary → 50% chance → two-ordering protocol mandatory. Source mix measured in our copy: Hypersim 400 / SUNRGBD 400 / nuScenes 400 → **33.3% photorealistic synthetic**; report per-source. |
| ordinal + absolute, human-verified GT | **ReVSI-1F** (derived, single-frame — see plan §2.5) | 13 question types tag cleanly onto primitives; numeric types scored by Mean Relative Accuracy. |
| absolute, sensor GT | **SpatialRGPT-Bench distance slice** (~375 inter-object distance items) | The absolute-metric type CV-Bench lacks. ⚠ width/height items are prior-contaminated (blind GPT-4 scores 48–52% within ±25%) — secondary, always with a blind-LLM baseline. |
| consequence-level | **CausalSpatial collision (826) + occlusion (189)** | Does primitive-level binding loss *predict* downstream failure? ⚠ their own admission: sim scenes' floor-strip spacing encodes depth perspective — the cue is artificially legible. |

**MindCube is NOT in the validation layer** (removed 2026-07-15 after item-level inspection): every item is multi-view perspective-taking under stated camera motion; nothing reduces to a single-image primitive. It is re-scoped to a **cross-view integration contrast (S4-adjacent)**. Full-video ReVSI at 2–3 frame budgets is a **labeled extension analysis**, not the core.

### 2.7 Model selection — a MINIMAL PUBLISHABLE CORE, then expansion

**Core = 2 architectures**, not 4–6: **Qwen2.5-VL-7B** (modern, M-RoPE) + **LLaVA-1.5-7B** (classic CLIP) — both already cached. One metric variable (**egocentric depth**), one qualitative positive control, five functional stages, leak-controlled linear+MLP probes, one behavioral test, one intervention. **Expansion to 4–6 models (InternVL/SigLIP, Gemma-3, Qwen2-VL) happens only after the site-wise pattern stabilizes on two** — the "one phenomenon or three?" question is worth answering, but not before there is a phenomenon.

**Pilot exit criterion (the pilot fixes the final analysis matrix, not just the generator):** ≥1 model shows metric decoding **above the nuisance ceiling** at an upstream site (or strong evidence the premise fails) **AND** the identifiability gate passes **AND** the Wang & Gao difficulty gradient emerges.

### 2.8 Mandatory pre-reads before design freeze

**✅ [Mirage Probes, 2606.13870](https://arxiv.org/abs/2606.13870) — READ 2026-07-16; CLEARED.** *"How Vision Models Fake Visual Understanding"* was flagged as the top threat to every probe claim here. It is a **title collision only**: it probes *"mirage behavior"* (answering **without the image**) on **semantic VQA** — no spatial targets, no selection leakage, no contradiction with our controls. **The position-leak result and the incremental-gain ceiling remain open contributions.** Adopted from it: the **contrastive-pair estimator** (§2.3). ⚠ **Cite [Hewitt & Liang 2019](https://arxiv.org/abs/1909.03368) (control tasks) and [Belinkov 2022](https://arxiv.org/abs/2102.12452) (probing survey) whenever the leak or the ceiling is presented — Mirage Probes omits Hewitt & Liang, and we must not**: our ceiling descends from control tasks, and saying so is what makes the *selection*-leak claim legible as the real novelty.

**✅ The pre-design-freeze must-read list is CLOSED (2026-07-16).** Both remaining papers were deep-read; neither blocks the build, both change the writing:
- **[Why Far Looks Up, 2605.30161](https://arxiv.org/html/2605.30161v1) — read.** The phenomenon is **vertical–distance entanglement (VD-EI), and it is AXIS-SPECIFIC: the horizontal axis is clean.** Use their term and state the axis-specificity — the loose "depth–vertical entanglement" phrasing this proposal used before is wrong. ⚠ **Their text-delta probe is IMMUNE to our position leak** (the visual components cancel in the delta) — **never list them among leak-affected work.** Adopted: **minimal contrastive pairs** (cited as prior art for our contrastive-pair estimator, §2.3), the **consistent/counter split**, and **vertical/depth-decoupled corridor stimuli**. They leave open — and we take — **metric regression** (they classify), **site-wise decomposition**, and **camera variation**.
- **[Attention in Space, 2603.20662](https://arxiv.org/pdf/2603.20662) — read. It is head-OUTPUT probing, not routing** — so **the "never shipped" vs "destroyed in transit" fork remains ours to resolve** (it is the ambiguous row of the outcome matrix, §2.3). Adopted as known: spatial heads are **sparse (<1%)**, **ablating them collapses performance**, and **generic ITI-style steering yields only ~1–2pp** — which makes it the **foil** our metric-ID injection must beat. ⚠ Their labels are LLM-generated and their eval is circular: **verify any number against the PDF before quoting it.**
- Remaining reads are **stage-gated** (2508.04567 → S1.5; Echo-Memory 2606.09803 → S4-B) or **writing-time** (Hewitt & Liang 2019; Belinkov 2022), plus a re-read of Ill-Posed by Design §6.6 + limitations.

## 3. Timeline

**⚠ Superseded 2026-07-16 — venue pivot (professor-approved): primary target = WACV 2027 R2
(deadline Aug 28) with the MINIMAL CORE (2 models, ordinal depth, five-stage curve, leak
methodology, reproduction); YANS poster Aug 16–18 (feedback lands 10 days before the deadline);
CVPR Nov 15 = fallback/extension with the full battery.** The table below describes the original
full-battery CVPR path and now applies to the fallback branch.


| Weeks | Work |
|---|---|
| 1–2 | Reproduce Kang et al. pipeline ([code](https://github.com/Raphoo/linear-mech-vlms)) + Wang & Gao probe setup (load-bearing, not warm-up). Build synthetic scene generator. Mandatory pre-reads (**Mirage Probes first**). Ethics application if human baseline wanted. |
| 3–6 | Core causal chain (§2.3) on the **2-model core** (§2.7) — *not* 4–6. **The identifiability gate (§2.4) passes before any site claim.** **W6: write intro + Figure 1; scope freeze** — later ideas go to `future_work.md`. |
| 7–11 | Intervention block (§2.5), with the full anti-logit-hack control battery. Side experiment: inference-time norm rescaling (untested causal claim from Beyond Semantics). |
| 10 | **Go/no-go**: muddy core finding → retarget ICCV 2027 (~March) + CVPR workshop; do not force a weak submission. Expansion beyond the 2-model core happens here, and only if the site-wise pattern has stabilized. |
| 12–14 | Validation layer (§2.6 — the closed predeclared set), ablations, matched-stimuli controls. |
| 15–17 | Full writing pass; advisor + one external reader. |
| 18 | Buffer. |

Risk management: biweekly scoping search (papers citing 2601.12626, 2605.07148, 2606.24335, 2411.17385) — this analysis was materially revised twice in one day by newly found papers; every specific design claim gets a verification search before entering the paper.

## 4. Method-Harvest Strategy

Scientific claims first; methods extracted where the toolbox forces invention. Three anticipated gaps:

1. **Causal mediation for continuous features** — existing interchange interventions and steering are discrete (left↔right); metric quantities need graded steering with dose-response validation. **S1 must build this**; if it generalizes (size, count, time, any continuous property), it is a standalone methods contribution (ICLR/NeurIPS) with the spatial results as demonstration.
2. **Probe transfer as a representational-sharing measure** (S3 — and it needs the three-level definition: decoding transfer / subspace alignment / causal direction transfer).
3. **Hypothetical-state probing** (S4-C).

First versions stay minimal (linear directions, scalar doses); formalization happens in writing if data cooperates. New interp methods carry a double validation burden — method-first framing is explicitly avoided on this timeline.

## 5. The Stages

*One program — see §0 for the canonical question, the cube, and the maturity labels. Stages are dependency-gated; they are **not** papers, and they are not degree chapters.*

**S1 — Visible metric** *(executable paper plan)*: §1–2 above.

**S1.5 — Occlusion & the amodal probe** *(well-formed extension; unlocks on M4b's gate)*. Hypothesis **H-occ** as stated in §1 (ordinal-visibility cue, **not** "the only categorical cue"). The amodal question splits into three, and they must not be conflated:
- **H1.5a — object persistence:** an entity-level representation survives partial visibility.
- **H1.5b — amodal geometry:** the **hidden extent** is recoverable *beyond* what visible-fragment features already give.
- **H1.5c — amodal binding:** that information is available **at object-referential tokens**.

⚠ **Amodal-extent *pooling* is insufficient as a test** — pooling under the invisible mask mostly collects **occluder and background** tokens. Do not assume hidden geometry is spatially stored under the hidden mask. Test *implicit* representation instead: visible-fragment pooled / occluder-region / object-name token / joint decoder conditioned on object identity. **The dumb-features ceiling for H1.5b must include the visible fragment's geometry AND `occlusion_ratio`** — otherwise "the model completes the object" is indistinguishable from "the fragment's shape gave it away."

**S2 — The method audit** *(strong next-paper candidate; stays prioritized ahead of S3 unless S1 yields a strong readout-specific result)*. How do existing spatial-enhancement methods change internal behavior? **Report a FIVE-DIMENSIONAL MECHANISM PROFILE per method — a vector, not a label** (the categories are not mutually exclusive):
- **ΔR_visual** — upstream representational gain
- **ΔR_bound** — object-specific transfer gain
- **ΔB** — readout gain *conditional on matched internal decoding*
- **ΔP** — prior reliance, under blind / black-image / geometry-conflict controls
- **ΔC** — causal repair: mediation + specificity

**Motivating mystery — "isolated structured perception HURTS":** four independent papers report that handing a VLM *correct* structured spatial input makes it **worse** (EmbodiedVSR: detector/depth/graph alone each degrade; SpatiaLQA: segmentation alone **67.4 → 50.3**, depth alone → **64.1**; NuScenes-SpatialQA; ISGR). Scaffold probing can settle it: **does isolated structured input never reach the binding sites, or actively interfere there?** → carry **isolated vs integrated scaffold** as an audit condition axis.

⚠ **Checkpoint comparability checklist — mandatory before ANY base-vs-finetune internal comparison:** tokenizer, image resolution, prompt/conversation template, preprocessing, transformers revision. A mismatch on any of these produces a "mechanistic difference" that is an artifact.

**Verified audit set (all public, matched bases):** 7B on Qwen2.5-VL-7B-Instruct — SpaceR (pure RL) vs ViLaSR (SFT+RL, drawing scaffold); 3B on Qwen2.5-VL-3B-Instruct — SpatialLadder (SFT→RL) vs SpaceQwen/SpaceOm (synthetic SFT) vs Spatial-MLLM (arch+SFT); plus weight-free inference-time scaffolds (scene-graph prompt, depth input, SoM). Skip: Cambrian-S (no untouched base), SVQA-R1 / SpatialVLM (no checkpoints). **Closest neighbor checked:** [2511.11440] probes only its own synthetic-SFT, LM-layers × final-question-token only, single toy task — no method comparison, no site decomposition, no scaffolds → cite and differentiate. Reuses ~90% of S1's infrastructure.

**S3 — Other readouts (generation)** *(comparative framework; needs operational definitions before it is a project)*. **Hypothesis SYMMETRIZED to branch-point localization** — the old "generation suffers less" phrasing prejudged the answer: *"If failure originates **before** the shared representation, both pathways fail on the same relations; if it originates **during task-specific binding/readout**, failures **dissociate** after the branch point."* "Generation suffers less from lexical binding loss" survives only as a **derived corollary, conditional on S1's finding**. Probe transfer must be defined at three levels: **decoding transfer / subspace alignment / causal direction transfer** (strongest, hardest). Unified models spanning the sharing spectrum: Janus-Pro (decoupled control), Emu3.5 (shared AR), BAGEL (hybrid). Independent motivation from the landscape deck's application **C2**: T2I evaluation leans on VLM judges whose spatial verification is itself unproven — which is the judge-circularity problem this stage must solve anyway (probing-first; pixel endpoint via 2AFC + disjoint detector ensembles + human calibration).

**S4 — The unseen** *(long-horizon agenda — a RESEARCH FAMILY of three branches; **exactly one** becomes the next project, selected by earlier results)*:
- **S4-A — hidden extent & the visibility graph.** ⚠ State the hypothesis **neutrally**, do not presuppose the negative: *"models may encode scalar visibility attributes without maintaining relational occluder–occludee structure — we test whether pairwise structure is represented, bound, and used."* Physically rendered occlusion **chains** are primary; inverted-depth composites are **one conflict regime only** (they carry a compositing-artifact confound and break the exact-geometry guarantee).
- **S4-B — persistent spatial memory:** out-of-view objects, KV-cache-as-memory probing, multi-image guaranteed-evidence protocol (decay vs interference vs never-encoded vs readout — DISJOINT-3DQA precedent).
- **S4-C — hypothetical spatial state:** does the model internally represent predicted future positions before verbalizing? (CausalSpatial-level simulation; humans 84% vs GPT-5 54%.)

The umbrella — **"representation of the unseen"** — spans capability levels 4–6 (visibility/permanence → dynamic state → counterfactual). It unlocks on S1.5's amodal result: if the hidden part of an object is not represented at all, there is nothing for a visibility graph to be made of.

## 6. Asks (advisor meeting)

1. ~~November CVPR target~~ → **WACV R2 (Aug 28) + YANS approved 2026-07-16**; priority cluster access through August is the standing ask.
2. Model coverage sign-off (§2.7 — the 2-model minimal core, with expansion gated on pattern stability) — affects GPU allocation.
3. Whether to pursue the human baseline (~20 participants, cue-integration comparison) — ethics application must go in ~W1 if yes.
4. One external reader commitment for W15–17.

---

*Full critical analysis of 15+ papers, overlap verdicts, and superseded alternatives: see `VSR_niches_critical_deep_read.md`.*
