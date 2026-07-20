# Checkpoint briefing

Date: 2026-07-21 · repo state at commit `45815c5` (+ this commit)

**Question.** Pass 3 (the last grid attempt): does per-role depth resolution close C_a,near^min and
converge cumulative R within ε_R?

**Method.** Per-role depth grids — near band 21 points (0.102 m spacing, was 0.443) over its own
range, far band 12 points; camera corners and multipliers held exhaustive; lateral reduced 4→2
(justified: all prior violations sat at lateral boundaries, none interior). 50,688 renders, chunked
and resumable, deposited into the cumulative ledger. Fresh role-specific verification: targeted
adversarial (3,168) + random on seeds 6007–6010 (798). Every pose's camera classified corner vs
interior.

**Results — NOT converged. The safeguard TRIPS.**

| ratification condition | result | |
|---|---|---|
| cumulative \|ΔR\| ≤ 0.002 | 1.2092 → **1.2167**, ΔR = **+0.0075** | **FAIL** |
| fresh targeted verification finds nothing new | **8** load-bearing violations | **FAIL** |
| binding pair stable | near_mug/far_cube unchanged | PASS |
| ledger monotone (hard invariant) | R rose, as it must | OK |

Cumulative R: 1.2092 → **1.2167**. Per-pass R for contrast: 1.2072 / 1.2060 / 1.2026 / 1.2167 —
still non-monotone per-pass, still monotone cumulative, exactly as the ledger predicts.

Residual load-bearing violations, all on C_a,near^min:

| | value |
|---|---|
| count | 8 targeted, 0 random |
| category | **sphere, all 8** (mug now covered) |
| camera | **all 8 at CORNERS** — 0 at interior |
| worst excess | +0.098% (sphere, 127,114.3 vs envelope 127,239.3) |

**Established.**
- **Grids are not closing this.** A 0.102 m near grid still missed the extremum, and it improved the
  near-band coverage (mug is now clean; violations dropped 10→8, all sphere). But R *rose* rather
  than settled, and the lowest value (127,114.3) was found by a **verification pose, not any grid** —
  the same value in pass 2 and pass 3, so it is reproducible geometry the grid keeps stepping over.
- **The corner-extremality path did NOT fire**: all residual violations are at camera corners, so
  the boundary assumption on camera axes holds. The gap is depth/pose geometry, not a mis-modelled
  camera axis.
- The four ruled invariants are in and green (ledger monotonicity + positive control, B16
  self-comparison, corner/interior classification).

**NOT established — R is NOT RATIFIED, cumulative R ≥ 1.2167 and still rising.** Pass 3 was the last
grid attempt and it did not converge.

**Safeguard verdict: TRIPPED** (via the ΔR > ε_R trigger; the corner-interior trigger did not fire,
but only one is needed). Per the pre-committed rule, grids are now abandoned for **constrained
adaptive minimization of C_a,near over the guard-defined reachable set**, feeding the same ledger.

**Weakest point.** One violation sits at depth **4.983 m — which IS a near-grid endpoint**, not
between points. A pure resolution-deficit story predicts violations only *between* grid points, so a
violation *on* a grid point means the miss is not solely depth resolution: the extremum is
off-grid in some other continuous axis the sweep samples coarsely (world-y, or the lateral I just
reduced), or the sweep and verification differ subtly at that pose. Either way it is more evidence
that a grid is the wrong instrument — which is where the safeguard sends us — but I have not
isolated *which* axis, and the optimizer should be told to vary all of them, not assume depth.

**Next step — the optimizer is a NEW load-bearing instrument, so I am holding for design
confirmation rather than launching, the same discipline the root search got (pre-committed before
running).** Proposed: minimize C_a,near(pose) over the guard-defined reachable set — pose = (depth,
lateral, multiplier, 5 camera axes) for sphere and mug — via multi-start SLSQP/differential
evolution with the guard as a constraint, every evaluation deposited into the ledger, converged when
the minimum is stable within an area tolerance that maps to ε_R on R. I want to pre-commit that
protocol (starts, seeds from the verification role, convergence tolerance, restart count) in one
commit before it runs. Textures remain decoupled and parallelisable meanwhile.
