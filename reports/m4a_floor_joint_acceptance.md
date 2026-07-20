# Floor root search and joint acceptance — the 4-set FAILS at its own minimal floor

> ## ⛔ STATUS OF R (2026-07-20)
>
> **R = 1.2072 is the CURRENT CORRECTED-SWEEP ESTIMATE on the 1.95 envelope. Envelope verification
> FAILED (19/600). R is NOT RATIFIED and nothing may consume it.**
>
> The ×1.02283 inflation shortcut was **rejected**: that margin was measured on the near-role
> *maximum*, which R never reads. R is `sqrt(max C_a[far] / min C_a[near])` — a margin measured on
> a non-load-bearing extremum is not an error bound for the load-bearing pair.
>
> `r* = 1.2100` is an **upper-bound candidate only**. The flat R(F) curve is an artifact of the
> conservative far-pose filter, not a property of the design; floor dependence must be recovered by
> the adaptive few-floor procedure once the instrument is trusted.
>
> Atomic three-regime constant derivation stays blocked (2.55 escalation is still live, so no
> regime may derive early). **Textures are decoupled** — they touch no silhouette geometry and
> consume neither R nor the floor.

Date: 2026-07-20 · protocol committed at `f0589b9` **before** it ran · raw:
`reports/m4a_floor_root_search.json`, `reports/m4a_s5_candidate_F1.1900.json`

## 1. Root search — r\* = 1.1850, r_op = 1.1900

Grid 1.165–1.200 step 0.005, calibration seeds 8001–8002, n = 1200 each, R = worst case over seeds.

| F | R(F) | F − R(F) | self-consistent |
|---:|---:|---:|:--|
| 1.1650 | 1.1915 | −0.0265 | no |
| 1.1700 | 1.1786 | −0.0086 | no |
| 1.1750 | 1.1769 | −0.0019 | no |
| 1.1800 | 1.1828 | −0.0028 | no |
| **1.1850** | **1.1797** | **+0.0053** | **YES** |

r\* = 1.1850 → **r_op = r\* + 0.005 = 1.1900**, applied mechanically.

### ⚠ The root is not resolved beyond its own noise

R(F) is non-monotone (1.1915, 1.1786, 1.1769, 1.1828, 1.1797), and the seed-to-seed spread in R
averages **0.0043** — the same size as the grid step (0.005), the margin (0.005), and the winning
gap F − R(F) = +0.0053.

Two consequences, both to be weighed rather than waved through:

1. **The margin does not exceed the measurement noise.** `r_op = r* + 0.005` buys roughly one noise
   unit of headroom, not a safety margin. The margin was pre-committed before the noise scale of R
   was known — reasonable at the time, wrong in hindsight.
2. **R is biased DOWNWARD.** It is a worst case over a finite sample whose extremes have not
   converged (a half-sample recovers only ~75–95% of the measured range). More sampling can only
   push R **up**, so the true r\* is likely *above* 1.1850.

## 2. Joint acceptance at r_op = 1.1900 — **FAIL**

### Area validity — PASS, on 6 calibration seeds

Deliberately measured with **6** calibration seeds rather than the root search's 2: more samples can
only raise a worst-case estimate, so this makes the test **harder**, never easier.

| seed | R(1.1900) |
|---|---:|
| 8001 | 1.1771 |
| 8002 | 1.1757 |
| 8003 | 1.1702 |
| 8004 | 1.1754 |
| 8005 | 1.1777 |
| 8006 | **1.1812** ← worst |

**r_op = 1.1900 ≥ R = 1.1812 → PASS, headroom +0.0088 (+0.75%).**

#### ⚠ This also measures the downward bias directly, and it is the size of the whole margin

R(1.1900) from seeds 8001–8002 alone is **1.1771**; from all six it is **1.1812**. Four extra seeds
moved the worst case up by **+0.0041** — essentially the entire 0.005 margin.

The prediction that R is biased downward at small seed counts is therefore not a caveat, it is
measured. Two consequences:

1. **The root search itself understates r\*.** It used 2 seeds. Had it used 6, R at each grid point
   would have been ~0.004 higher, and 1.1850 would likely no longer have been self-consistent —
   r\* would have moved up a grid step or more.
2. **The +0.75% area headroom at r_op is thin and would erode with further sampling.** It is a pass,
   but not a comfortable one, and it should not be read as evidence that the current envelope has
   room.

### Sampling validity — FAIL on all six quantities

Calibration seeds 8001–8008, n = 1200, worst seed (a bound only the average clears is not a bound).

| quantity | dir | bound | worst seed | |
|---|---|---:|---:|:--|
| A.r_ratio_gap | lower | 0.700 | **0.6509** | FAIL |
| A.retained_range | lower | 1.230 | **1.2172** | FAIL |
| A.weakest_stratum_r_gap | lower | 0.580 | **0.4391** | FAIL |
| A.weakest_stratum_range | lower | 1.140 | **1.1340** | FAIL |
| C.clamped_fraction_drawn_floor | upper | 0.550 | **0.5850** | FAIL |
| C.max_stratum_clamped_fraction | upper | 0.690 | **0.7600** | FAIL |

Not marginal: weakest-stratum r comes in at 0.44 against a 0.58 bound, and the clamp rate overshoots
in both aggregate and worst stratum. **JOINT VERDICT: FAIL.** Area validity passes (thinly); sampling validity fails on every quantity.
Acceptance requires both, so the candidate is rejected.

This is the genuine test it was expected to be. The floor that area congruence demands and the floor
that sampling semantics tolerate do not overlap on the current depth envelope.

## 3. Escape hatch — extending the FAR depth-bin envelope WORKS

Triggered per the pre-registration, which permits it only on joint failure. Extending `depth_gaps`
adds deeper far bins, raising the ratio **ceiling** so the floor squeezes less from below.

| variant | available ratio | ceiling | placement failures / 2400 |
|---|---|---:|---:|
| current `[0.45 … 1.35]` | 1.045 – 1.464 | 1.464 | 1 |
| extended `[… 1.95]` | 1.045 – 1.665 | 1.665 | **0** |
| extended `[… 2.55]` | 1.057 – 1.844 | 1.844 | **0** |

Sampling validity at floor 1.1900 under the extended envelopes:

| quantity | bound | `… 1.95` | `… 2.55` |
|---|---:|---:|---:|
| A.r_ratio_gap | ≥ 0.700 | **0.8452** ✅ | **0.9048** ✅ |
| A.retained_range | ≥ 1.230 | **1.3649** ✅ | **1.5114** ✅ |
| A.weakest_stratum_r_gap | ≥ 0.580 | **0.7918** ✅ | **0.8773** ✅ |
| A.weakest_stratum_range | ≥ 1.140 | **1.2576** ✅ | **1.3838** ✅ |
| C.clamped_fraction_drawn_floor | ≤ 0.550 | **0.3950** ✅ | **0.2927** ✅ |
| C.max_stratum_clamped_fraction | ≤ 0.690 | **0.5200** ✅ | **0.4000** ✅ |
| | | **PASS** | **PASS** |

**Bonus, and not a small one: the placement background rate goes to zero.** The separate §5 blocker
in `reports/m4a_placement_background_rate.md` — a ~34% chance the frozen render crashes partway — is
also resolved by this change. Deeper far bins place easily, exactly as the ruling anticipated.

## 4. What is NOT established

- **The extended envelope has not been root-searched.** These numbers use floor 1.1900, which was
  rooted on the *current* envelope. Extending the gaps changes the depth distribution and therefore
  R(F); the root search must be re-run there before any floor is ratified.
- **The change is battery-wide.** `depth_gaps` is shared design surface; counterbalanced and conflict
  must move with it or the three arms are no longer depth-matched, which breaks the matched
  three-regime contrast.
- **It re-opens z-identifiability.** Far depth extends from ~6.2 m to ~7.4 m at `… 2.55`. That
  changes the depth range every z result is measured over, so the leak-ceiling and B0/B1/B2
  decomposition need re-checking. This is the cost the ruling flagged, and it is real.
- **`… 1.95` versus `… 2.55` is not decided here.** Both pass. `2.55` has more headroom on every
  quantity; `1.95` is the smaller perturbation to the battery and to z-identifiability. Choosing
  between them is a design decision, and the minimal-perturbation argument deserves weight given
  what re-opening z costs.

## 5. Recommended sequence, if the hatch is taken

1. Choose the gap extension (`… 1.95` favoured on minimal-perturbation grounds).
2. Re-run the root search **on the extended envelope** to get its own r\*, r_op.
3. Re-run joint acceptance there — both legs, on calibration seeds.
4. Propagate `depth_gaps` battery-wide; re-derive constants for all three regimes over their new
   envelopes.
5. Re-check z-identifiability (leak ceiling, B0/B1/B2) on the new depth range.
6. Only then: bound-setting sweep on 9009–9016, and the frozen render.
