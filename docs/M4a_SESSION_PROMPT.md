# M4a Session Prompt — Stimulus Battery v1 (gate: IMAGE-IDENTIFIABILITY)

You are implementing **milestone M4a only** of the spatial-binding project, in `~/vsr` on
plant-ai06. One milestone per session. **Do NOT start M4b (extraction), M4.5 (occlusion), or M5
(probing).** M4a needs **no VLM and no GPU** — rendering is CPU (bpy/Cycles, ~2.5 s/img); leave
the shared GPUs alone.

## 0. Read first, in this order (do not skip)

1. `AGENTS.md` — ground rules + verification rules (especially 3: no silent exemptions; 7:
   two-clause evaluation law; 11: no null without a registered positive; 12: dumb-features
   ceiling; 13: no findings-by-definition).
2. `PROJECT_MEMORY.md` — sections: **M4 design constraints**, **M3 — THE GO-GATE**, **THE
   POSITION LEAK**, **SECOND retro-audit**, **Hard-won lessons**.
3. `IMPLEMENTATION_PLAN.md` — §2.5(d), §3 (schemas), §4 M4a spec, and the M4.5 forward
   constraints.
4. `reports/m3_reproduction.md` §2.4.

## 1. Why this milestone exists (context to hold the whole session)

M3.2 proved the v0 congruent set **cannot measure models — only itself**: (i) `x` had exactly 2
values (±0.7) — a binary side label, and mask-pooling selects tokens *by* object position, so
x R² = 0.997 measured the pooling; (ii) `z` was 86% predictable from apparent size alone
(r = 0.93) — the exact monocular shortcut Wang & Gao discount; (iii) two primitives, bare plane,
**fixed camera** — with a fixed camera, camera-frame x *is* image position. Mask geometry alone
(no model) gives x R² = 0.942, z R² = 0.972.

**M4a's one-line job: make the stimuli able to disagree with the mask.** Its gate —
image-identifiability — is a property of the *stimuli* and needs no VLM, which is exactly why it
runs before M4b. M3.2's pass bar (the W&G difficulty gradient) transfers to **M4b**, not here.

## 2. Deliverables

### 2.1 Generator v1 — three regimes, from one config each

1. **natural-congruent** — all cues agree. *Controls only.*
2. **counterbalanced** — nuisance cues (elevation, retinal size) vary **independently** of true
   depth while scenes stay **physically plausible**. **The primary localization claim lives
   here** — this regime is the battery's centerpiece; give it the most design attention and the
   largest share of images.
3. **conflict** — cues actively disagree (farther object rendered lower in image, or with larger
   retinal size — physically consistent via camera/geometry, never pasted). *Cue-integration
   analyses only.*

### 2.2 The five REQUIRED decorrelations — each is a measured v0 defect, none optional

- **(a) Continuous lateral positions.** `lateral_offset` becomes a continuous range (config-set),
  so `x` is a metric coordinate, not a side label. Balanced left/right by construction.
- **(b) Camera-pose jitter (height / pitch / yaw), per image.** This kills the position leak at
  its source. ⚠ **RETRACTED 2026-07-17 (measured false for x — advisor ruling 1):** the original
  spec said *"with camera jitter, camera-frame coordinates are no longer image positions."* This is
  FALSE for lateral x: camera-frame x is coupled to image position by the projection identity
  `u ≈ f·X_cam/Z_cam + c_x`, which **no camera motion can break** (measured: cam-x 0.94→0.93 under
  strong jitter). Camera-frame x is therefore a **projection-coupled POSITIVE CONTROL** (expected
  ~0.93), never a leak target. The decorrelation lever works on **WORLD-frame x** and on **depth z**
  (z is not projection-coupled — image position fixes the X/Z ratio, not Z), and world-x is a
  SECONDARY target conditional on passing its own raw-pixel identifiability under held-out pose.
  Ranges in config; record exact K, R, t per image as before.
- **(c) `size_condition` — independent per-object physical-size jitter. LOAD-BEARING.** It is the
  only thing that breaks the size↔depth shortcut. The congruent regime keeps the pair-shared
  multiplier (that is what "congruent" means); independent jitter belongs to counterbalanced/
  conflict via the `size_condition` factor.
- **(d) Nuisance variation:** floor/background textures, 0–2 distractor objects, lighting jitter —
  enough degrees of freedom that "modest decodability" is expressible.
- **(e) Recalibrate.** Every new degree of freedom (pose freedom, per-object size jitter, new
  objects) **invalidates the M1 calibration and the 1.18 depth-ratio floor**. Re-run
  `scripts/calibrate_sizes.py` and re-derive all cue constants and thresholds from **WORST-CASE**
  measured extremes (`scripts/derive_cue_constants.py`) — never means (evaluation law, clause 1;
  the 1.096-vs-1.158 failure is the precedent).

### 2.3 Object sets and questions

- Two object sets: existing primitives (cube/sphere/cylinder) + a few **canonical-size CC0
  models** (chair, mug, bottle). Their difference later measures the size-prior contribution.
  Canonical objects go through the same empirical retinal calibration as primitives.
- Question templates per taxonomy level (qualitative / ordinal / ratio / absolute), **balanced
  answer keys**, recorded in annotations. Remember the 55.1% lesson: **balance every factor
  against the ROLE it could predict** (category/colour drawn as ordered (near, far) pairs and
  balanced), not just its own marginal.

### 2.4 Contrastive matched pairs — rendered ON PURPOSE (a battery deliverable, not analysis)

The contrastive-pair estimator (M5's third leak-immune probe) needs stimulus pairs **matched on
projected mask geometry but differing in true depth**. Post-hoc matching within a tolerance is
insufficient — the residual is exactly what a probe would exploit. Build a dedicated
`contrastive_pairs` config: for each pair, co-vary object size, placement, and camera so the
rendered mask geometry (centroid, height, area) matches **by construction**; validate the match
pixelwise on the rendered masks and record the achieved tolerance as a margin. A few hundred
pairs is enough for the pilot.

### 2.5 Solo-object ID pass (M4.5's prerequisite — cheap now, expensive to retrofit)

While the generator is open, render **each object alone** in a solo ID pass → **amodal mask** per
object. Schema additions per object: `mask_amodal`, `occlusion_ratio`
(= 1 − visible_area/amodal_area; must be ~0 everywhere in M4a since there is no occlusion
condition — assert it), `retinal_size_px_amodal`. **Do NOT add an occlusion condition** — that is
M4.5, locked behind M4b's gate. ID-pass discipline (the bounce bug is not to be relearned):
ground = black emission, all lights 0, `max_bounces = 0`, 'Raw' view transform.

### 2.6 Validation & determinism

- `scripts/validate_stimuli.py` must **open every artifact and recompute from pixels** (bbox,
  height, area, mask invariants: `mask_amodal ⊇ mask_visible`, sphere as tall as wide, projection
  vs K[R|t] < 2 px), id-uniqueness, content-duplication, frame clipping — **reporting margins,
  not pass/fail**. Any exemption is explicit, counted, and logged — never a bare `continue`.
- The `unambiguous_ordinal` centre-vs-surface constraint **becomes load-bearing** once per-object
  size varies independently — keep it ON and verify it actually fires (count how often it binds).
- `fixed_retinal_size` is defined on mask **HEIGHT** (pose-stable), or fix pose explicitly and
  only then use area — never silently mix (cube mask area varies ±11% with pose/depth).
- **Determinism re-verified by byte-compare** (hard rule): denoise OFF, adaptive sampling OFF,
  metadata stamping OFF; annotations/masks byte-identical; the known ~1-px-in-5.2M Cycles float
  residual on beauty images is acceptable and documented — **hash annotations, not pixels**.
- Everything seeded and exactly regenerable from config + seed. New/changed modules ship pytest
  coverage; suite stays green (skip, not fail) without `$DATA_ROOT`.

### 2.7 Leak-ceiling measurement on the new battery

Run `scripts/leak_ceiling.py` on the rendered pilot: dumb features = {mask geometry: centroid,
area, bbox, retinal size, elevation} ∪ {shape, colour} ∪ {cue values}, per target (x, z, ordinal,
ratio; depth vs lateral axis), on **structured held-out splits** (held-out object identities,
camera poses, depth ranges, cue combinations — never only random image splits). Report the v0 →
v1 change: camera jitter should lower the SELECTION (B0) decodability of lateral position.
⚠ **SUCCESS CRITERION REWORDED (ruling 3, 2026-07-17): NOT "all mask prediction collapses".** The
dumb baseline splits into **B0 selection · B1 monocular cues · B2 semantic priors**; the target is to
**control B0 (selection) and B2 (priors) while PRESERVING verifiable monocular evidence B1** — a
plausible image cannot remove elevation/apparent-size, and a genuine depth representation may BE
their integration. So a high B1→z is EXPECTED and fine; what must come down is B0 (fixed by camera
motion — the world-x story) and B2 (the identity-prior confound). The primary M5 gate is
`Δ_R|B0,B2`, never Δ over all cues. Tool: `scripts/baseline_decomposition.py`.

## 3. 🚦 THE GATE — image-identifiability (must pass before M4b starts)

**Exact renderer GT ≠ pixel-inferable GT.** For **each target variable** (ordinal depth, ratio,
absolute depth, lateral position — per axis) and **each regime**: a **directly-supervised model
on raw pixels** (small CNN or regression on oracle geometric image features — your choice,
justify it) must recover the variable **from the image**, **evaluated on held-out NUISANCE
factors (object identities, poses, textures, camera configurations, cue combinations) — never
only random splits** (AMENDED at DR3-r2: a pixel model that passes only random splits may be
passing through the very cues the battery controls). **Gate per LEVEL, separately: ordinal
identifiability · continuous ranking · calibrated magnitude/ratio.** The **human spot-check**
(contact sheet: can a person tell which object is closer?) licenses the ORDINAL level only —
continuous/ratio levels are gated by the supervised baseline's held-out generalization.
**Additionally deliver: the pre-registered NUMERIC acceptance bounds for M4b's leak criterion**
(trivial-feature score ceiling with CI; Δ_repr|dumb permutation-null threshold) — M4b may not
start without them.
**THIRD AMENDMENT (DR3-r7):** the gate's supervised model establishes *statistical
recoverability from pixels under this training distribution* — state it that narrowly. Add:
renderer-family / resolution+anti-aliasing / photometric-postprocessing holdouts where feasible;
cue-ablation renders; a simple INTERPRETABLE pixel baseline reported next to the CNN; human
pairwise ranking (ordinal license only). Continuous-magnitude identifiability claims are
distribution-relative, never absolute. If the image does not contain the evidence, no VLM site can — and
any later "low everywhere" probing profile would be an instrument failure wearing a finding's
clothes. **A target that fails the gate is fixed or descoped before M4b — the WACV minimal core
needs ordinal depth; protect that target first.** This gate is a per-target checklist with
margins, not one aggregate number (evaluation law, clause 2: check the weakest prespecified
stratum).

## 4. Scale

Pilot first: ~**1k images** (counterbalanced-weighted) + the contrastive pairs, enough to run the
gate, the leak ceiling, and the human spot-check. The full 5–10k render happens only after the
config freezes (it is cheap once frozen — do not burn hours rendering a config that fails its own
gate). Both scales from the same configs, differing only in N and seed.

## 5. Definition of done (all of it)

- [ ] Three regimes render end-to-end, each from one config; configs committed.
- [ ] Five decorrelations implemented and demonstrated (show the decorrelation matrix: pairwise
      correlations among depth, elevation, retinal size, physical size, image position — near
      zero in counterbalanced, by measurement not assertion).
- [ ] Recalibrated worst-case cue constants + thresholds committed to config.
- [ ] Contrastive pairs rendered, pixelwise match validated, tolerance margins reported.
- [ ] Solo-ID amodal masks validated (`⊇` full scan; `occlusion_ratio ≈ 0` asserted).
- [ ] Validation suite green **with margins reported**; determinism byte-compare passed.
- [ ] Leak ceiling on v1 reported (v0 comparison table).
- [ ] **Image-identifiability gate: per-target, per-regime results + human spot-check —
      explicit PASS/FAIL/DESCOPE table.**
- [ ] `reports/m4a_battery.md` written (numbers, margins, gate table, decisions).
- [ ] `PROJECT_MEMORY.md` + `IMPLEMENTATION_PLAN.md` updated with every decision made; committed
      and pushed (server is never the only copy).

## 6. Standing discipline (verbatim rules that apply here)

- Worst case for constructed quantities; weakest-prespecified-stratum for sampled ones.
- No silent exemption, no green check without a margin, no number without provenance
  (config + seed + git hash).
- An upstream field is a hypothesis — verify against the artifact (applies to CC0 model
  dimensions too: measure the rendered size, don't trust the asset metadata).
- If you find yourself arguing a target "must" be identifiable from geometry, render it and
  measure it instead (rule 13).
- Wording discipline in everything you write: metric information "becomes unavailable or
  unusable" — never "is lost/destroyed".
