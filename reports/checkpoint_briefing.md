# Checkpoint briefing

Date: 2026-07-21 · describes repo state at commit `0e1b721` (+ this commit)
This file always holds the LATEST completed checkpoint; git history holds the rest.

**Question.** Pass 2 under the committed rules: does R satisfy the four-part ratification
conjunction (ε_R = 0.002, binding-pair stability, zero load-bearing exceedance, targeted
adversarial pass)?

**Method.** Envelope sweep at depth grid 10 × lateral 4 (30,720 poses, 23,706 admitted by the
placement guard), run chunked at 2,000 renders per process because a long-lived Blender process
degrades superlinearly. Verification in a separate fresh process, two-part as committed:
deterministic adversarial probe of the load-bearing strata (far: cube at max multiplier; near: mug
AND sphere at min multiplier; depth on a 12-point interior grid, lateral and all 32 camera corners
at boundaries) plus fresh random on seeds 6007–6010.

**Results — R = 1.2026. RATIFICATION FAILS 3 of 4 conditions.**

| # | condition | result | |
|---|---|---|---|
| 1 | \|ΔR\| ≤ 0.002 | 1.2060 → 1.2026, **ΔR = −0.0034** | **FAIL** |
| 2 | binding pair stable | near_mug/far_cube → near_mug/far_cube | **PASS** |
| 3 | zero load-bearing exceedance | **10** (targeted 10, random 0) | **FAIL** |
| 4 | targeted adversarial pass | **126 / 3,168** exceed | **FAIL** |

R across passes: 1.2072 → 1.2060 → **1.2026**. The binding pairing has never moved.

Exceedances split by role and constant:

| | height:near | height:far | area:near | area:far |
|---|---:|---:|---:|---:|
| targeted (3,168 objs) | 100 | 16 | **10** | **0** |
| random (798 objs) | 3 | 3 | 0 | 0 |

Load-bearing violations are **all on C_a,near^min** — mug (+0.076%, +0.328%) and sphere (+0.075%).
Worst is 0.328%, which would move R to roughly 1.2046.

**Established.**
- **The targeted probe earns its place.** It found **10** load-bearing violations where uniform
  random found **0** on a comparable sample. The ruling's reasoning — that uniform random cannot
  certify these cells — is now measured, not argued.
- **C_a,far^max is clean**: zero area:far exceedances across 3,966 targeted far-role objects.
- **Binding-cell stability holds** across all three passes.
- Chunking works: 23,706 renders completed with resume, versus a 4.6-hour single process that
  produced nothing recoverable.

**NOT established — R is NOT RATIFIED.** ΔR is 1.7× the committed ε_R and is *growing* between
passes (−0.0012 then −0.0034), so refinement is not converging on this axis; the envelope is still
tightening as coverage improves. C_a,near^min is under-covered.

**Open decisions.** How to close C_a,near^min. The evidence points at the *near* role and the
*minimum* — the opposite corner from where I aimed my earlier suspicion — so refinement should be
directed there rather than uniformly.

**Weakest point.** I flagged far-role coverage as the likely gap last checkpoint. **That was wrong**:
far-role area is clean and near-role minimum is the problem. Worth noting I got there by reasoning
about which term uniform random samples thinly, rather than by measuring — the targeted probe
settled in one run what my reasoning had pointed the wrong way on. Also: 100 of 126 targeted
exceedances are height:sphere:near, which is a *pixel-extremal* artifact and reinforces the ruling's
preference for an analytic height bound over denser grids.

**Next step.** Blocked on nothing; the direction is determined by the data. Refine specifically on
the near-role minimum — finer lateral and multiplier resolution in the near depth band — and re-run
pass 3 with fresh verification seeds. ~90 min chunked. R stays unratified and nothing may consume it
meanwhile; textures remain decoupled and parallelisable.
