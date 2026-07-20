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

---

# AMENDMENT 2026-07-21 — cumulative ledger supersedes per-pass R

## The correction

Per-pass R **discards evidence**. The sequence 1.2072 → 1.2060 → 1.2026 read like convergence from
above; it is an artifact of **non-nested grids**. Pass 2 sampled depth × lateral at 10 × 4 where
pass 0 sampled 6 × 2, so each pass re-rolls the extrema from its own sample and is free to miss a
pose an earlier pass hit. A falling per-pass R is **forgetting, not convergence**.

Over the union of all admitted evaluated poses the extrema can only widen, so **cumulative R is
monotone non-decreasing** — a lower bound on the true worst case that improves with evidence.

**ε_R applies to the CUMULATIVE sequence, never to per-pass values.**

## Ratification, restated

Convergence requires **all three**:
1. cumulative R stationary within ε_R = 0.002;
2. fresh targeted verification finds **nothing new**;
3. binding pair stable.

Zero-exceedance stands. **No tolerance creep** — "at least ~1.2046" style wording is withdrawn; the
correct statement is **"at least the cumulative-union value"**.

## Every evaluation deposits into the ledger

Grid sweeps, random verification, targeted adversarial probes and optimizer calls all accumulate
into one extrema set. **Verification violations are DATA, not merely failures**: each is a
guard-admitted, measured pose, and its value belongs in the extrema set with provenance. Recording
only "10 failures" discards the measurements that prove the envelope too narrow — and in fact the
current binding minimum comes from two of them.

## Pre-committed stopping safeguard

If the next pass **either** moves cumulative R by more than ε_R **or** produces violations in new
interior regions, then regular grids are **abandoned** for **constrained adaptive minimization of
C_a,near over the guard-defined reachable set**. Optimizer evaluations feed the same ledger.

Rationale: grids are a bet that extrema sit near sampled points. Two refinements that keep moving
the cumulative bound falsify that bet, and buying resolution uniformly is then the wrong lever.

## Height — analytic track

Start with **SPHERE**: its silhouette is an exact projected ellipse with a closed form, and it
accounts for 100 of 126 targeted exceedances. Height does **not** enter R (1.1193 against area's
1.2026) but it **blocks the full-instrument claim and the conflict regime's constants**, so it must
close before the atomic three-regime derivation.

---

# AMENDMENT 2026-07-21b — pass-3 rules, triggers, and the post-ratification queue

## Pass 3 is the LAST grid attempt

Per-role depth grids (the near band gridded over its own range, not the union), all other axes held
exhaustive, everything deposited into the cumulative ledger, criterion **cumulative ΔR ≤ 0.002**,
fresh role-specific verification. All five optimizer triggers live.

## Pre-committed interpretation of residual violations

| where the violating pose sits | reading | remedy |
|---|---|---|
| camera **CORNER**, between depth points | resolution deficit | safeguard per existing rules |
| camera **INTERIOR** value | **corner-extremality assumption FALSIFIED** | **immediate optimizer trigger, regardless of depth resolution** |

The second is not a matter of degree. If an extremum sits at an interior camera value, no amount of
depth refinement reaches it, because the sweep only ever evaluates camera corners. The random
verification path draws real sampler cameras (interior almost surely) and is therefore the leg most
able to expose this.

## Ledger monotonicity is a hard-fail invariant

`ΔR_cum < 0` beyond float tolerance is **ledger corruption, never a result** — the cumulative R is a
max over a growing union and can only rise. Tested (`test_I6`, with `test_I6b` as the positive
control that a narrowed ledger is detectable).

## B16 — coverage diagnostics must compare against the domain they claim to cover

A coverage diagnostic compared against the grid that *generated* its own samples measures nothing.
Shipped instance: the violation-clustering diagnostic reported "distance to nearest grid point =
0.0000" for all ten load-bearing violations, having compared them against the targeted probe's own
grid rather than the sweep grid whose coverage was in question. Against the sweep grid the same
violations sit 0.19–0.39 of a spacing away — the entire finding. Tested (`test_I7`).

## ⚠ POST-RATIFICATION QUEUE — ratifying R settles AREA VALIDITY ONLY

Ratifying R does **not** ratify the floor. The **JOINT acceptance** must re-run at the ratified
value:

1. Compute `r_op ≈ R + margin` on the **1.95 envelope**.
2. Re-run the **A–C sampling checks** at that `r_op`.
3. **The existing sampling numbers do not transfer** — they were measured at floor **1.19**
   (r = 0.845, weakest stratum 0.792, clamped 0.395). At an `r_op` near 1.21+ they will be worse,
   and by how much is unmeasured.
4. Only if BOTH legs pass is the floor ratified.
5. Then: fresh-seed operative bounds on 9009–9016, atomic three-regime constants derivation,
   determinism byte-compare, freeze tag, §5 one-shot.

Listing this now so that a ratified R is not mistaken for a finished floor.
