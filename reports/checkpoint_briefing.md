# Checkpoint briefing

Date: 2026-07-20 · describes repo state at commit `ed0b698` (+ this commit)
This file always holds the LATEST completed checkpoint; git history holds the rest.

**Question.** Does refining the deterministic envelope grid close the verification failure, so that
R can be ratified?

**Method.** Refinement pass 1 of the envelope sweep: depth grid 6 → 8 points, lateral magnitude
levels 2 → 3, all 32 camera-jitter corners retained. 18,432 solo renders. Verification on FRESH
seeds 6003–6006 (6001–6002 were burnt on inspection), 400 real sampler scenes = 800 objects.
Exceedances are now split into load-bearing vs not, where load-bearing means the two extrema that
actually enter R = sqrt(max C_a[far] / min C_a[near]).

**Results.**

| | pass 0 (depth 6, lat 2) | pass 1 (depth 8, lat 3) |
|---|---:|---:|
| deterministic R | 1.2072 | **1.2060** |
| ΔR | — | **−0.0012 (−0.10%)** |
| binding pairing | near_mug / far_cube | near_mug / far_cube — **STABLE** |
| r* / r_op | 1.2100 / 1.2150 | 1.2100 / 1.2150 (unchanged) |
| total exceedances | 19 / 600 (3.2%) | 17 / 800 (2.1%) |
| **load-bearing exceedances** | 0 | **1 — FAIL** |

The single load-bearing violation: `sphere / near / area = 127,253.9` against an envelope minimum of
`127,319.9` — **0.052% below**. That is C_a,near^min, one of the two terms R reads.

Violations split sharply by constant: **15 of 17 are height** (worst +2.03%), only **2 are area**
(worst +0.137%).

**Established.**
- **Binding-cell stability holds** — the argmax pair did not move under refinement, satisfying that
  stopping condition.
- **R is essentially converged in magnitude**: refining two axes moved it by 0.0012.
- **Area is nearly covered; height is not.** Plausible mechanism: mask area averages over thousands
  of pixels, while mask height is a single extremal pixel measurement, so it is far spikier as a
  function of pose. Height does not drive R here (1.1102 vs area 1.2060, a 0.096 gap that a 2%
  height error cannot close), so this is a coverage defect rather than a threat to R.

**NOT established — R remains NOT RATIFIED.** The zero-exceedance requirement on the load-bearing
pair is not met: 1 violation, 0.052%. Correcting for it would move R to roughly 1.2063 — immaterial
in magnitude, but the criterion is zero, not small.

**Open decisions.** None new.

**Weakest point — two of the ruling's requirements were not implemented before I ran this pass.**
1. **ε_R was never pre-specified.** The ruling requires pre-specified ε_R convergence; I launched
   refinement without committing a value first. ΔR = 0.0012 looks convergent against any plausible
   ε_R, but choosing ε_R now, having seen ΔR, is precisely the post-hoc threshold selection the
   whole protocol exists to prevent. It must be committed before pass 2, and pass 1 should be
   treated as evidence that cannot itself certify convergence.
2. **Targeted adversarial verification is not implemented.** The ruling requires oversampling the
   far-role extremes specifically (cube-as-far, max multiplier, camera/depth boundaries, the binding
   pairing), on the explicit grounds that uniform random verification cannot certify C_a,far^max.
   This pass used uniform random only. **Zero far-role exceedances in 800 objects is therefore not
   evidence of far-role coverage** — it is the exact gap the ruling anticipated, and it happens to
   sit on the term of R I already flagged as unverified.

**Next step.** Blocked on my own process gaps, not on a decision. In order: pre-commit ε_R and the
targeted-verification spec (no compute); implement targeted far-role adversarial verification;
re-run verification on fresh seeds 6007–6010 against the pass-1 envelope (~10 min, no re-sweep
needed unless it fails); only if the load-bearing count reaches zero does R become ratifiable.
Textures remain decoupled and can proceed in parallel.
