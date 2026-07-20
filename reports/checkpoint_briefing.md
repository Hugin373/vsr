# Checkpoint briefing

Date: 2026-07-21 · repo state at commit `296727d` (+ this commit)
Covers TWO checkpoints — the previous one was not relayed, so its live content is folded in here.

**Question.** (a) Does the cumulative extrema ledger change the operative R? (b) Where do the ten
load-bearing violations cluster, and does that choose a refinement axis or trip the safeguard?

**Method.** (a) Folded every admitted evaluated pose from all three grid sweeps plus every
verification exceedance into one extrema set; extrema of a union are the min/max of per-source
extrema, so per-pass summaries suffice for sweeps whose per-pose records were not kept.
(b) Re-ran the targeted adversarial probe (3,168 poses) with full coordinate capture on every
exceedance, then measured each violation's distance to the actual pass-2 sweep grid.

---

## (a) Cumulative ledger — R RISES to 1.2092

| | R | binding pairing |
|---|---:|---|
| pass 0 (grid 6×2) | 1.2072 | near_mug/far_cube |
| pass 1 (grid 8×3) | 1.2060 | near_mug/far_cube |
| pass 2 (grid 10×4) | 1.2026 | near_mug/far_cube |
| **cumulative union** | **1.2092** | near_mug/far_cube |

The correction is confirmed: the falling per-pass sequence was **forgetting, not convergence**. The
three grids (6×2, 8×3, 10×4) barely overlap, so each pass re-rolled the extrema.

**Treating violations as data changed the answer, not just the bookkeeping.** The binding minima for
both relevant cells now come from targeted-verification exceedances rather than from any grid:

| cell | cumulative min | source |
|---|---:|---|
| `area_mug_near` | 119,714.2 | pass-2 targeted verification |
| `area_sphere_near` | 127,114.3 | pass-2 targeted verification |

R = 1.2092 is a **lower bound** that can only rise. The "at least ~1.2046" wording is withdrawn.

## (b) Violation clustering — one axis, unambiguously

All ten load-bearing violations (every one on C_a,near^min):

| | value |
|---|---|
| multiplier | **0.92 in 10/10** — the minimum |
| camera pitch | **+3.0° in 10/10** — the maximum |
| depth | **4.611, 4.797, 4.983** — the top of the near band (max 4.983) |
| lateral | spread across ±0.85 and ±0.30 — both extremes |
| category | sphere 8, mug 2 |
| distance to sweep grid | **0.086–0.171 m = 0.19–0.39 of the 0.443 m spacing** |

**The mechanism is structural, and it is my design error.** The sweep grids the **union** depth
range (2.939–6.927 m) with 10 points, but the **near role only spans 2.939–4.983 m**. So only **5 of
10** grid points land in the near band, giving 0.443 m resolution over a 2.044 m span — while the
far band gets the other half. Every violation sits **between** those coarse points, at the deep end
of the near band, at the minimum multiplier and maximum pitch.

Multiplier and camera corners are *not* the gap: the sweep enumerates all three multipliers and all
32 camera corners exhaustively. The gap is **near-band depth resolution**.

**Established.** Cumulative R = 1.2092. The refinement axis is determined by data, not by my guess:
grid each role's **own** depth range rather than the union. Violations are systematic (one region,
one axis), not scattered.

**NOT established.** R remains **unratified**; nothing downstream may consume it. Whether fixing the
near-band resolution closes C_a,near^min or merely moves the bound again is exactly what pass 3
tests.

**Safeguard status: NOT tripped.** The pre-committed trigger is "violations appear in **new interior
regions**". These are confined to one contiguous region, explained by a known resolution deficit —
so a directed grid remains justified. If pass 3 still moves cumulative R by more than ε_R, the
trigger fires and we switch to constrained adaptive minimization of C_a,near.

**Weakest point.** Two self-inflicted measurement errors this checkpoint. First, I chose
**non-nested grids**, which is what made the per-pass R non-monotone and the "convergence" reading
possible; nesting each grid as a superset of the last would have made monotonicity automatic.
Second, my violation-clustering diagnostic initially reported "distance to nearest grid point =
0.0000 for all 10", which was **self-referential** — it compared against the targeted probe's own
12-point grid instead of the sweep's. Corrected, the same violations sit 0.19–0.39 of a grid spacing
away, which is the entire finding. Both errors share a shape: a measurement compared against itself
rather than against the thing it was meant to test.

Also: 100 of 126 total exceedances are `height:sphere:near` — pixel-extremal noise, reinforcing the
sphere-first analytic-height track.

**Next step.** Pass 3, directed: grid each role's own depth range (near band at ~0.10 m resolution
instead of 0.443 m), keeping multipliers and camera corners exhaustive, chunked and resumable,
depositing into the ledger. Then fresh targeted verification. ~90 min. Nothing else proceeds; R
stays unratified; textures remain decoupled and parallelisable.
