# Arbitration of the third external review (2026-07-16, on the lab deck read as a scientific argument)

*Verdict legend: **ADOPT** (fully accepted, changes docs and/or deck) · **ADOPT±** (accepted with a
nuance the review missed) · **CLARIFY** (the design already does this; the deck misstated it).
Reviewer-loop precedent: this is the pass that previously caught the occlusion deduction and the
"progressive loss" phrasing.*

## Meta-finding (ours, not the reviewer's)
The deck re-introduced overclaims that the project docs had already retracted or stated more
carefully ("kills", "dies", DepthCues precision, W&G "raw form"). **Third documented instance of
compression-from-memory re-creating retracted claims.** Consequence: the deck now copies its claim
sentences from PITCH.md/proposal verbatim, like every other artifact.

## Central problem — variable inconsistency (ordinal vs continuous) — **CLARIFY + ADOPT the two-level frame**
The design was already the reviewer's "two-level project": probes REGRESS continuous quantities
(z, Δz, ratio — M3.2 probed continuous z), while the behavioral primitive of the minimal core is
ordinal (where models can produce answers at all). But the docs/deck used "ordinal depth" and
"continuous metric depth" interchangeably in claim-level sentences — a real, fixable
inconsistency. **Fix (Design Revision 3.1): the two-level structure is now explicit everywhere —
"CONTINUOUS depth (z; Δz/ratio secondary) as the probe target; ORDINAL ordering as the behavioral
anchor; qualitative as positive control."** Claim sentences must name both levels.

## 1. Deccan-vs-Anchored "published disagreement" — **ADOPT±**
Adopted: they studied different variables (categorical occlusion vs continuous slant), different
methods (patching vs probing), different endpoints; strictly compatible; "adjudicate the
disagreement" invites the killer rebuttal. **New canonical framing: "their results motivate
competing localization hypotheses for different forms of spatial information; we test which
pattern — projector-, binding-, or readout-bottleneck — holds for controlled continuous depth."**
Nuance kept: the *interpretations* the two papers put on their own results do point at opposite
ends of the LM, which is legitimate motivation — attributed as interpretation, never as
established contradiction. The pre-registered site-2-vs-site-4 primary contrast is unchanged.

## 2. "Dies at the projector" (Deccan) — **ADOPT**
Violates our own wording rule. Also: their recovery snapping back to 1.0 at LM L0 itself shows
the information is not absent downstream. Canonical: **"a sharp causal-recovery discontinuity
around the merger/projector boundary, for categorical occlusion under their patching protocol."**

## 3. "Dies at the readout" (Anchored) — **ADOPT**
The LM interior is unmeasured (their own declared future work). Canonical: **"decodable at
LM-input, not faithfully expressed in the answer; the failure location inside the LM is
unresolved."** Their interface interpretation is attributed, not asserted.

## 4. Monocular taxonomy too categorical — **ADOPT**
"Ratio is prior-free/recoverable" holds only under assumptions (calibration, support plane).
Canonical: **"ordinal is often constrained by monocular evidence; ratio requires geometric
assumptions; absolute additionally requires a scale prior — our battery supplies these conditions
by construction, and the identifiability gate verifies rather than assumes them."** (Ordinal
ambiguity inside the battery is already excluded by the `unambiguous_ordinal` constraint.)

## 5. Cues ≠ shortcuts by definition — **ADOPT** (construct improvement)
Monocular depth perception IS cue use. The distinction is **cue-responsive prediction
(single-cue reliance that fails under decorrelation) vs cue-integrated, object-specific depth
that generalizes when cue correlations change.** This is what the conflict regime's
fusion-vs-winner-take-all analysis operationalizes; the deck's "answers depth without depth"
assumed the conclusion. Wording adopted project-wide.

## 6. DepthCues overweighted — **ADOPT** (deck regression; docs already had the precise form)
Canonical: "makes complete cue blindness unlikely; does not establish integrated or metric depth,
nor anything past the encoder." DepthLM: fine-tuning can CREATE/reorganize a representation —
constrains "absent" claims only weakly.

## 7. "Linear probe ⇒ explicitly, accessibly encoded" — **ADOPT**
Deck contradicted its own ladder. Canonical: "linearly recoverable under the probe's sampling and
controls" — accessibility claims need the arbiter + more.

## 8. "Patching = the model uses it" — **ADOPT**
Canonical: "causally capable of mediating the behavioral difference under this intervention."
Natural-use requires specificity + mediation (already in the M6 battery). Pedagogical contrast
survives in speaker notes with the caveat attached.

## 9. Ablation null ≠ absence — **ADOPT**
Redundancy is not hypothetical: Cui's LM backup mechanism is a live example in our own anchor
set. The zero-ablation rule is about **metric responsiveness** (instrument), never component
absence — the deck conflated the two.

## 10. Kang faithfulness scope — **ADOPT**
"For the tested models, stimuli and relations, wrong answers were already reflected in wrong
internal IDs — arguing against a purely final-verbalization explanation." Not a universal law.

## 11. "W&G kills hypothesis 2" — **ADOPT**
A probe null is protocol-relative (our own leak work is the proof that instrument caveats cut
both ways). Canonical: "challenges the naive form under their pooling, sites, targets and
protocol." The proposal's "raw form contradicted" stays, correctly scoped.

## 12. "Training does not install geometry" — **ADOPT**
Scoped: "in the tested LoRA setups, gains came without increased sensitivity to the manipulated
geometric evidence — consistent with sharpened priors."

## 13. "Only rendering decorrelates" — **ADOPT**
False exclusivity. Canonical: "rendering enforces exact factorial control and exact GT at a scale
natural data rarely provides."

## 14. Gate 2 bakes in the conclusion — **ADOPT± (design change, IMPLEMENTATION_PLAN edited)**
Adopted: "metric must be hard" as a GO criterion would reject a genuine strong-metric world —
a substantive hypothesis was living inside a validity gate. **M4b's gate is reformulated as
validity-only:** positive controls decode · label/feature nulls at chance · leak ceiling
COLLAPSES vs v0 · generalization across held-out objects/poses/depth-ranges · demonstrated
dynamic range. Nuance kept (the diagnostic teeth): an unexpected ceiling result triggers a
**mandatory diagnostic checklist** (leak ceiling per cell, contrastive pairs, held-out-factor
splits) before interpretation — but if all validity checks pass, high metric decodability is a
FINDING, not a gate failure. W&G's gradient is demoted to a benchmark comparison.

## 15. Oracle-text ≠ full upstream isolation — **ADOPT**
"Narrows — but does not uniquely localize — the failure to extraction, cross-modal transfer, or
accessibility; text coordinates may also recruit a different strategy."

## 16. "Whatever curve appears, it adjudicates" — **ADOPT**
"The curve distinguishes the three candidate patterns for controlled depth in the tested
architectures." Generality claims wait for the expansion models.

## 17. "First" claims exposed — **ADOPT for all pre-result artifacts**
Pre-result canonical: **"a stage-wise, trivial-feature-controlled protocol for tracing
object-specific depth information (continuous probe targets, ordinal behavioral anchor) from
visual encoding through language-token representations."** A scoped "first" may return at
write-up, only after results + a fresh sweep, with each qualifier re-verified.

## 18. Leak contribution premature — **ADOPT: "candidate" + a 6-condition promotion checklist**
(1) baseline predicts targets under the original study's split; (2) survives held-out-object/
position splits; (3) incremental Δ_repr|dumb small; (4) selection mechanism formally isolated;
(5) impact on published conclusions assessed (not just our v0); (6) prior work verified not to
control an equivalent positional feature — **(6) is already done for W&G** (appendices + code,
verbatim, 2026-07-16); (1)–(5) await battery v1. Also adopted: mask geometry is an
**external/trivial-feature baseline**, not "non-representational" — the mask represents location;
the point is the signal's provenance (selection/annotation, not learned activation content).

## New wording bans (join the standing list)
"dies / killed / destroyed (for information)" · "adjudicates the disagreement" · "first …"
(pre-result) · "cues are shortcuts" (unqualified) · "the model uses it" (from patching alone) ·
"component wasn't carrying it" (from an ablation null) · "explicitly/accessibly encoded" (from a
linear probe alone) · "only rendering can decorrelate".
