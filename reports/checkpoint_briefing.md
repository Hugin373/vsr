# Checkpoint briefing

Date: 2026-07-21 · describes repo state at commit `d1f894f` (+ this commit)
This file always holds the LATEST completed checkpoint; git history holds the rest.

**Question.** Run pass 2 of the deterministic envelope refinement under the committed ratification
protocol (ε_R = 0.002, four-way conjunction, targeted adversarial strata) and determine whether R
can be ratified.

**Method.** Protocol pre-committed to git BEFORE any pass-2 compute. Targeted two-part verification
implemented per the committed strata. Pass 2 launched at depth grid 8→10, lateral 3→4 = 30,720
solo renders, plus deterministic adversarial cells and fresh random seeds 6007–6010.

**Result: PASS 2 DID NOT COMPLETE. There is no pass-2 number.**

The job died at **14,718 / 30,720 renders (47.9%)** after ~5 hours. No traceback: Python's buffered
output was lost when the process was killed, which is also why no partial JSON was written.

The cause is not a code defect — it is throughput collapse on the shared machine:

| | renders | sustained rate |
|---|---:|---:|
| pass 0 | 6,406 | ~0.16 s/render |
| pass 1 | 14,018 | ~0.16 s/render |
| **pass 2 (died)** | 14,718 of 30,720 | **~1.2 s/render** |

Server state at diagnosis: **123 users, load average 7.87**. Memory was never a constraint (979 GB
free). At the degraded rate the full pass-2 grid costs **~10 hours**, not the ~100 minutes I
estimated from the historical rate.

**Established.**
- The ratification protocol is committed and unrun — ε_R = 0.002, the four-way conjunction, and the
  targeted strata all exist in git before any pass-2 result.
- Targeted adversarial verification is implemented, with outputs split by role and constant through
  a single code path shared with the random verification. The total-exceedance aggregate is gone.
- Cost model corrected: this instrument's runtime is **not** stable on a contended shared server,
  and every prior time estimate I gave assumed the uncontended rate.

**NOT established.** Everything pass 2 was meant to decide. **R is unchanged at 1.2060 from pass 1,
which remains development evidence and cannot certify its own convergence.** None of the four
ratification conditions has been evaluated under the committed rules. **R is NOT RATIFIED.**

**Open decisions.**
1. **Re-run pass 2 as-is (~10 h at current contention), or change the instrument first?** The
   ruling already prefers replacing pixel-extremal height with an analytic/semi-analytic bound.
   The throughput collapse argues for extending that idea to the whole sweep: project the mesh and
   rasterise the silhouette directly instead of ray-tracing an ID pass. That removes Blender from
   the inner loop entirely — plausibly ~100× faster, making exhaustive grids cheap and the
   contention problem irrelevant. It requires validating the rasteriser against the renderer to the
   same standard the ID-pass instrument already met (0.000 px / 0 px on 179 objects).
2. Whether to accept a coarser pass-2 grid as an interim, which would weaken the ΔR evidence.

**Weakest point.** I estimated pass 2 at ~100 minutes from a rate measured when the machine was
idle, on a server the project documentation explicitly describes as shared and unscheduled. That is
a planning error I should not repeat: long runs need either a measured current rate or a
checkpoint/resume path. This job had neither, so five hours of compute produced nothing recoverable
— the renders were done but the results existed only in a lost buffer.

**Next step.** Recommend deciding (1) before spending more compute, since a re-run at current
contention costs ~10 h and would still leave the same instrument. If the analytic rasteriser is
approved I would build and validate it first (~2 h, no long-running job), then re-run pass 2 cheaply
and exhaustively. Textures remain decoupled and unblocked.
