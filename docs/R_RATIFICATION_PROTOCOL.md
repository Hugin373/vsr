# R ratification protocol — COMMITTED BEFORE PASS 2 RUNS

Ruled 2026-07-20. This file exists in git before any pass-2 compute; that ordering is the proof
that ε_R and the strata were not chosen after seeing results.

## ε_R and the ratification conjunction

```
ε_R = 0.002          # half the floor operating step (0.005)
```

R is ratified only when **ALL FOUR** hold. This is a conjunction, not a scorecard — three out of
four is a failure.

1. **|ΔR| ≤ 0.002** between consecutive refinement passes.
2. **Binding pair stable** — the argmax pairing does not move between passes. If it moves, coverage
   was insufficient *regardless of* ΔR: a small ΔR with a migrating argmax means the sweep is
   sampling different cells, not converging on one.
3. **Zero exceedance on BOTH load-bearing extrema** (C_a,near^min and C_a,far^max) under
   independent verification. Zero, not small.
4. **Targeted adversarial verification passes** (strata below).

**Pass 1 is DEVELOPMENT EVIDENCE and cannot certify its own convergence** — it ran before ε_R was
committed. **Pass 2 under these rules is mandatory regardless of the 6007–6010 outcome**: a
verification pass on the pass-1 envelope does not substitute for a refinement pass judged by
committed criteria.

## Targeted adversarial verification — committed strata

Uniform random verification **cannot certify C_a,far^max**: the far-role extremes occupy a small
corner of the reachable set, so a uniform draw hits them rarely and zero exceedances there is
consistent with never having probed them. The targeted pass oversamples exactly those cells.

**Far-role strata (probing C_a,far^max):**
- category **cube** (the current argmax far cell)
- **maximum** size multiplier
- depth, lateral and camera-jitter axes at their **boundaries**
- the binding cell specifically (near_mug / far_cube)

**Near-role strata (probing C_a,near^min):**
- categories **mug AND sphere** — mug is the current argmax; sphere produced the pass-1
  load-bearing violation, so both are probed rather than only the incumbent
- **minimum** size multiplier
- depth and lateral at their **endpoints**

**Two-part, both required:**
- **(a) deterministic adversarial cells** — enumerate the strata above directly;
- **(b) fresh random** on seeds **6007–6010**, single-look consumables.

## Output rule

Results are reported **split by role and by constant**. A total-exceedance aggregate is never
again an acceptable summary: pass 0 reported 19/600 with "0 load-bearing", and pass 1 reported
17/800 with "1 load-bearing" — the aggregate moved in the reassuring direction while the number
that matters moved in the failing one.

## Height coverage — required before the atomic derivation, not before R

Height does **not** inflate R (1.1102 against area's 1.2060; the 0.096 gap is not closable by the
observed ~2% height error). But **"not binding for R" ≠ "not binding for the battery"**: the
conflict regime's apparent-size requirements consume height envelopes (the B13 lineage), so height
coverage must be **closed before the atomic three-regime constants derivation**.

Preferred route, to be tried before buying coverage with denser grids: replace the **pixel-extremal**
height measurement with an **analytic/semi-analytic silhouette-height bound** derived from projected
mesh geometry, which is already validated. Rendered mask height is an integer extremal pixel and is
therefore spiky in pose — the reason it is 15 of 17 violations while area is 2 of 17. An analytic
bound plus a quantisation allowance is exact where a grid is merely dense.
