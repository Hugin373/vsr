# Checkpoint briefing

Date: 2026-07-20 · describes repo state at commit `e555414`
(superseded by later commits; this file always holds the LATEST completed checkpoint)

**Question.** What is the congruence requirement R for the natural-congruent 4-set on the newly
adopted 1.95 depth envelope, derived deterministically by envelope coverage rather than random
seeds — and does the resulting floor hold up?

**Method.** Sweep the object's reachable pose envelope: discrete factors (size multiplier, lateral
side) exhaustive; continuous factors (depth, lateral magnitude, all five camera-jitter axes) at
boundaries; depth additionally gridded through the interior. 9,216 solo renders, 4 categories.
Poses filtered by the sampler's own placement guard and by role-wise depth *and* world-y
reachability. Then an independent random verification: 300 real sampler scenes (600 objects,
dedicated seeds) checked against the swept envelope.

**Results.**

| quantity | value |
|---|---:|
| deterministic R | **1.2072** (binding: near_mug / far_cube, area) |
| height requirement | 1.1145 (not binding) |
| r* | 1.2100 |
| r_op = r* + 0.005 | **1.2150** |
| random verification | **19 / 600 exceed — FAIL**, worst +2.283% |

**A bug in my own instrument, found and fixed mid-derivation.** The first version admitted any pose
whose projected *centre* was on-screen. Measured: **712/9,216 (7.7%) of those poses are rejected by
the real placement guard** — edge-clipped silhouettes with truncated area, which deflates C_a and
inflates the requirement. That version reported **R = 1.4314**. With the correct guard, R = 1.2072.

**Established.** R = 1.2072 under envelope coverage, on the corrected guard. It sits *above* the
random-seed estimates (~1.18), the direction the standing rule predicts — random maxima are biased
low.

**NOT established — the headline.** **The boundary-extremal assumption is falsified.** Corner
evaluation does not cover the reachable set at this grid resolution. The violations happen not to
touch R (all five area exceedances are on the near-role *maximum*; R uses the near-role *minimum*
and the far-role maximum, where nothing exceeded) — but that is luck, not construction. **R = 1.2072
is NOT RATIFIED.** Separately, the R(F) curve reads flat at 1.2072 across F ∈ [1.15, 1.25]; that is
an artifact of the conservative far-pose filter, so r* = 1.2100 is an upper bound on the minimal
floor, not an estimate of it.

**Open decisions.** None outstanding — the rigorous path was ratified and the ×1.02283 inflation
shortcut rejected (a margin measured on a non-load-bearing extremum is not an error bound for the
load-bearing pair).

**Weakest point.** Two instrument defects shipped in one session (centre-only filter; `--verify-random`
declared but unimplemented for a full run). Both caught, but the pattern says the instrument
deserves more suspicion than its output gets. Specifically: the *far-role* envelope is unverified,
and the far-role maximum is one of the two terms in R. Zero far-role exceedances in 600 objects is
consistent with good coverage and equally with the far range being sampled thinly by a uniform
random draw.

**Next step.** Refinement pass 1 running: depth grid 6→8, lateral 2→3 (18,432 renders, ~55 min),
verification on fresh seeds 6003–6006. Nothing else proceeds until R is ratified; textures are
decoupled and may run in a parallel session.
