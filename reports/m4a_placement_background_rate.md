# Placement failures are a floor-independent background rate — and a §5 blocker

Date: 2026-07-20 · found while executing the floor root search · **separate from the floor decision**

## How it surfaced

The root search crashed: `could not place non-overlapping target pair after 500 attempts for
rootsearch_F1.1650_s8002_00412`. The obvious reading was that a lower floor makes placement harder —
the far object sits closer to the near one, so their projected boxes overlap more and the guard
rejects. That reading is **wrong**, and measuring it is what showed so.

## Measurement 1 — the feasibility map is non-monotone

Placement failures over 2 seeds × 1200 images per floor:

| F | failures | | F | failures |
|---|---|---|---|---|
| 1.1650 | 2 | | 1.1800 | 0 |
| 1.1700 | 0 | | 1.1850 | 1 |
| 1.1750 | 1 | | 1.1900 | 0 |

Fail, pass, fail, pass, fail — that is not how a property of `F` behaves.

## Measurement 2 — the rate is flat across the whole range

6 calibration seeds × 1200 images per floor:

| floor | failures / 7200 | rate |
|---|---:|---:|
| 1.1650 | 2 | 0.028% |
| 1.1750 | 2 | 0.028% |
| 1.1850 | 1 | 0.014% |
| 1.1950 | 0 | 0.000% |
| 1.2320 | 1 | 0.014% |
| **1.8500** | **2** | **0.028%** |

Flat, **including at the old six-category floor of 1.85** where the far object is pushed far away and
placement should be easiest. Pooled: **8 / 43 200 = 0.019%**. This is a background rate independent
of the floor.

## Consequence 1 — placement must NOT gate the floor choice

My first amendment (protocol v1.1) made any placement failure mark a grid point infeasible. The
argument was that it could only push r\* upward, so it could not bias the result favourably. That
argument was fine; the **premise was wrong**. Gating on a 1-in-2400 event makes r\* depend on a
placement coin-flip rather than on the design — with this map, r\* would have come out 1.180 instead
of 1.175 purely because seed 8001 happened to lose a die roll at 1.175.

Superseded by v1.2: calibration runs tolerate a skipped image (`--allow-placement-failures`,
calibration-only) and record the counts. Both amendments are kept visible in the script, because the
first one was wrong and a silent deletion invites the same reasoning back.

## Consequence 2 — a real §5 blocker, separate from the floor

The gate-scale render runs with `raise_on_placement_failure=True`, correctly: an un-placeable image
there breaks the factor balance. At a 0.019% per-image rate:

| arm | N | P(at least one failure) |
|---|---:|---:|
| natural-congruent | 400 | ~7.3% |
| counterbalanced | 900 | ~15.7% |
| conflict | 900 | ~15.7% |
| **whole battery** | **2 200** | **~34%** |

**A one-in-three chance that the frozen §5 render dies partway through.** And it would present as a
mysterious late-run crash, not as a diagnosis — §5 runs once, so this is worth fixing beforehand.

## More attempts does not fix it

| `target_placement_attempts` | failures / 3600 |
|---|---:|
| 500 | 2 |
| 2 000 | 1 |
| 8 000 | 1 |

The same lesson as the dropped 0.2 m depth bin: specific factor combinations are **structurally**
un-placeable, not unlucky. Raising the attempt budget buys almost nothing and costs sampling time.

## Options — recorded, not chosen

1. **Loosen `lateral_range`** so the two targets have more room to separate. Cheapest, but it widens
   the lateral distribution and therefore touches the world-x decorrelation story.
2. **Per-image fallback**: on exhaustion, relax the *non-binding* margin (bbox margin) rather than
   giving up, and record which images used it. Keeps the factor balance; adds a documented
   inhomogeneity.
3. **Accept and skip**, with `raise_on_placement_failure=False` at render time plus a hard cap on the
   skip rate and a rebalancing check. Simplest, but it makes the realized factor balance approximate,
   which is exactly what §5 check B and the B2→z closure depend on being exact.
4. **Identify and exclude the structurally un-placeable combinations** from the factorial, the way the
   0.2 m bin was dropped. Most in keeping with what the project already did — but it needs the failing
   combinations characterised first, and it shrinks the design.

Option 4 is the closest precedent; option 3 is the one to be most careful about, since exact
placed-level role balance is currently a measured strength (P(near|c) = 0.5000 on every seed) and
skipping erodes precisely that.
