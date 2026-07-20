# Seed ledger — ranges, roles, and what consumed them

Ruled 2026-07-20. **Seed roles are disjoint and a seed is never reused across roles.** Reusing a
calibration seed to set bounds lets the design be selected and judged on the same draw; reusing a
verification seed after looking at its result turns a falsification test into a fitting exercise.

**Verification seeds are single-look consumables.** Once a verification run has been inspected, its
seeds are burnt: any re-verification after a change to the instrument must use fresh ones. This is
the strictest role, because verification is the only test whose job is to fail.

| range | role | status | consumed by |
|---|---|---|---|
| 410 | frozen-pilot / reference | in use | natural-congruent config seed; reported alongside sweeps as a reference value, **excluded** from every bound |
| 411, 412, 413 | frozen-pilot | in use | counterbalanced, conflict, contrastive-pairs config seeds |
| 6001–6002 | verification | **BURNT** 2026-07-20 | deterministic-envelope random verification (300 scenes, 19/600 exceedances — result inspected) |
| 6003–6006 | verification | **BURNT** 2026-07-21 | pass-1 (refine1) random verification |
| 6007–6010 | verification | **BURNT** 2026-07-21 | pass-2/3 verification; used to find AND analyse the role-boundary bug, so disqualified from final ratification evidence |
| 6011–6014 | verification | **RESERVED** | corrected-pass final random verification (fresh) |
| 6015–6020 | verification | free | future passes |
| 7001–7002 | instrument-internal | in use | `reachable_ranges()` — measures the reachable depth/world-y envelope; not a statistical estimate, never gates anything |
| 8001–8002 | calibration | consumed | floor root search (grid 1.165–1.200) |
| 8003–8006 | calibration | consumed | area-validity leg at r_op = 1.1900 (6-seed worst case) |
| 8007–8008 | calibration | consumed | sampling-validity leg (8001–8008 as a block) |
| 8009–8016 | calibration | free | reserved for the adaptive few-floor R(F) recovery |
| 9001–9008 | ~~bound-setting~~ → development | **DEMOTED** 2026-07-19 | v1 bounds at floor 1.1707; design-selection evidence only, never operative |
| 9009–9016 | bound-setting | **UNSPENT — do not touch** | reserved for final operative bounds at the ratified floor |

## Rules

1. **Never reuse across roles.** A seed appears in exactly one row.
2. **Verification seeds burn on inspection**, not on use. If a verification run is started and its
   output is read, those seeds are spent even if the run is later discarded.
3. **Bound-setting seeds are spent once**, at the ratified floor, under the committed formula. They
   may not be used to explore, preview, or sanity-check.
4. **Update this file in the same commit** that consumes a range. A ledger reconstructed afterwards
   is not a ledger.
