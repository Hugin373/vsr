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

## Merge instructions for the coding agent

1. **PROJECT_MEMORY.md:** replace the "Research arc" section with the Stage table (Change 1);
   append Change 2's S1.5 summary + verification-reads to the must-read list; fold Change 3's
   items into the relevant sections (M4 design constraints ← S1.5 schema/validation notes;
   dataset rules ← NSR metric note); update "Current state / next step" to mention M4.5 exists
   and unlocks only after M4's transferred bar.
2. **IMPLEMENTATION_PLAN.md:** insert **M4.5** between M4 and M5 with the spec in Change 2
   (design, schema additions, validation exemptions, two questions, leak-ceiling extension,
   acceptance criteria: solo-ID amodal masks validated — amodal mask ⊇ visible mask, ratio in
   [0,1); occlusion condition renders + passes exempt-adjusted validation; the two probe/behavior
   analyses runnable from cache). Rename M7's framing from "Paper 2" to "S2 audit"; add the
   isolated-vs-integrated scaffold axis. Add Mirage Probes to §5 gotchas as a pre-M5 must-read.
3. Do NOT renumber existing milestones. Do NOT start M4.5 unprompted — it unlocks on M4's gate.
4. Commit as `docs: stage reframing + occlusion stage (S1.5/M4.5) + landscape fold-in`.
