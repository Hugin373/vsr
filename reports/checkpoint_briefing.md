# Checkpoint briefing

Date: 2026-07-21 · repo state at commit `404e146` (+ this commit)

**Question.** Item (1) of the optimizer ruling: two-path forensic reproduction of the depth-4.983
endpoint violation — do the sweep and verification paths measure it identically (→ off-grid-axis,
proceed) or divergently (→ B16, halt and fix)?

**Method.** Extracted the exact violating pose (sphere, depth 4.982996791, lateral −0.85,
multiplier 0.92, camera corner height +0.16 / pos_x −0.3 / pos_y −0.2 / pitch +3 / yaw −4). Rendered
its C_a through both code paths and compared. Then traced why the sweep's recorded near-min
(127,239) differed from the value verification found (127,114).

**Results — the gate HALTED on a real bug, not the branch the ruling anticipated.**

| | value |
|---|---|
| C_a via sweep path | 127,114.26 |
| C_a via verification path | 127,114.25 |
| Δ | **0.01 px** (pure 2e-7 depth rounding) |
| mask area, both paths | **4,333 px — identical** |

The measurement paths **agree exactly**. So it is not a C_a divergence. But the sweep still dropped
this pose from the near set, and the cause is a **role-assignment rounding bug**:

- the depth grid rounds endpoints to 6 dp: `4.982996791 → 4.982997`;
- `roles_ok` then checks that rounded value against the **unrounded** near-range max `4.982996791`;
- `4.982997 > 4.982996791` → near excluded → the pose is filed under **far only**;
- so the pose carrying the binding **C_a,near^min (127,114)** never entered the near minimum.

The sweep measured the true minimum correctly and then bucketed it wrong — every pass, at the near
endpoint, which is exactly where the minimum lives.

**Established.**
- **The bug is fixed and the fix is confirmed by re-measurement.** With a `ROLE_BOUNDARY_TOL = 1e-5`
  the corrected sweep finds `sphere_near min = 127,114.26` **itself**, on a coarse 3-point near
  grid — the value that previously only verification could see.
- This **explains the entire "grids keep missing it" narrative**: no grid resolution ever helped
  because the deepest-near pose was being excluded by rounding regardless of spacing. Only
  verification (role fixed a priori) ever saw it.
- Forensic reproduction retained as `scripts/forensic_pose_reproduction.py`; regression test `I9`
  encodes the exact rounding failure.

**NOT established — and this is the decision it raises.** The pass-3 safeguard tripped on
**bug-corrupted sweep data**: the sweep near-min was 127,239 when the truth was 127,114. The
cumulative R = 1.2167 is still correct (verification supplied the value, the ledger holds it), but
the conclusion "grids are exhausted, go to the optimizer" was drawn from a sweep that couldn't see
its own minimum. Whether a **corrected** grid pass now converges within ε_R — capturing the
deep-near region in the sweep rather than only in verification — is unmeasured.

**Weakest point.** My off-grid-axis hypothesis from last checkpoint was **wrong** (I guessed
world-y or lateral). The real cause was a boundary rounding bug in code I wrote. The forensic gate
the reviewer mandated is what caught it — I would otherwise have built the optimizer on top of a
role definition that excludes the region the optimizer was meant to search, and it would have
minimized over a set that structurally cannot contain the true minimum. That is the exact
"optimizer would inherit it" failure the gate exists to prevent, and it landed.

**Open decision — genuinely the advisor's, because it reopens a ratified ruling.** The ruling made
pass 3 the last grid attempt and sent us to the optimizer. But that ruling rested on buggy data.
Two paths:
1. **Re-run one corrected grid pass** (pass-3 resolution, fixed role logic; ~2 h chunked). If cumulative
   ΔR ≤ ε_R and verification is clean, R is ratifiable and the optimizer is not needed. Cheaper, and
   it tests the bug-vs-fundamental question directly.
2. **Proceed to the optimizer** as ruled, now on corrected role logic. Safe regardless, but may build
   a heavy instrument the fix made unnecessary.

I lean (1): the "grids can't reach it" evidence was an artifact, so the premise for the optimizer is
now in doubt, and one clean pass settles it for less than the optimizer costs. But overriding a
ratified "last grid attempt" is the advisor's call, not mine.

**Next step.** Hold for that decision. Nothing consumes R meanwhile (still ≥ 1.2167, unratified).
Textures remain decoupled and parallelisable.
