# Project Memory — Kaho's VSR Research (last updated 2026-07-17, fifth session — advisor rulings)

*Orientation file for future sessions. Read this first, then `research_proposal_spatial_binding.md` (the plan) and `VSR_niches_critical_deep_read.md` (the literature analysis). Companion: `docs/vsr_landscape_v8.pptx` — Kaho's independent 19-paper landscape analysis (2026-07-05, predating this project), folded into these docs on 2026-07-15 (stage reframing, the S1.5 occlusion stage, the "isolated structured perception hurts" finding, the five definitions / capability levels / tensions vocabulary).*

## 📌 2026-07-16 (second session) — docs migrated into the claude.ai Project

- **These four docs now live in the claude.ai Project "Visual Spatial Reasoning"** (under `claude/`):
  `PROJECT_MEMORY.md` (this file — the canonical state), `research_proposal_spatial_binding.md`,
  `VSR_niches_critical_deep_read.md`, `IMPLEMENTATION_PLAN.md`. **Future sessions: read the project
  copies first and write updates back there** — uploaded/attached copies in a chat are snapshots.
  The repo (`~/vsr` on plant-ai06, pushed to GitHub) keeps its own `docs/` copies; when they
  diverge, the most recent dated entry wins and the other copy gets synced.
- **Deck inventory (decks live in the repo, not in the project — text extracted and verified this
  session):**
  - `vsr_program_scope.pptx` (16 slides) — **the canonical program-scope deck** (Design Revision 2
    frame: program hypothesis, evidential ladder, cube, per-stage hypotheses, gates, evaluation
    law). Consistent with these docs.
  - `yans_professor_en.pptx` (9 slides; JA twin `yans_professor_ja.pptx`) — advisor deck for the
    YANS request: 5-stage framing, Kang-reproduction + position-leak progress, YANS logistics
    (poster Aug 16–18 Sendai, **register by Fri Jul 24**, co-author consent), JA abstract (~390
    chars). States the working target: **preliminary decodability curves by mid-August.**
  - `vsr_landscape_v8.pptx` (58 slides) — the 19-paper landscape; already folded in.
  - ⚠ **`research_proposal_detailed.pptx` (34 slides) is STALE — pre-Design-Revision-2. Do not
    copy from it.** It still contains the retracted framing: "metric information **is destroyed /
    dies** at binding" (banned wording), the **four-site** grid (now five functional stages),
    "every outcome is a paper", **Paper 1/2/3 + PhD labels** (banned — stages, not papers), the
    old CVPR-only calendar, and 4–6 models everywhere (now 2-model minimal core). It predates the
    07-15/07-16 revisions. Keep only as history; `docs/PITCH.md` + `vsr_program_scope.pptx` are
    what any new abstract/deck copies from.
- **🔁 RENAME (2026-07-16): the repo's `CLAUDE.md` is renamed `AGENTS.md`.** Every "CLAUDE.md
  rule N" reference throughout these docs now means **AGENTS.md rule N** — the rules themselves
  are unchanged; historical mentions below are not rewritten. ⚠ Practical caveat: Claude Code
  auto-loads a file named `CLAUDE.md`; depending on version it may not auto-load `AGENTS.md` —
  if the coding agent stops following the ground rules, add a one-line `CLAUDE.md` that says
  "Read AGENTS.md" (or a symlink) rather than assuming the rules were absorbed.
- **No science changed this session** — state below (WACV R2 Aug 28 primary, YANS Aug 16–18,
  M4a next, M4 = the real gate) is current. Program-scope deck confirms: M0–M3 done in six days;
  **now = M4 pilot** (~1k images, 2 models, 1 metric variable, three regimes; preregistered exit
  criteria = identifiability gate + W&G gradient above the leak ceiling).
- **Still open (unchanged):** YANS registration (closes Jul 24 — this week); the one-page
  問題・新規性・実験設定 statement for the professor; biweekly citation watch + monthly topic sweep
  not yet set up as a scheduled task; human-baseline/ethics decision.

## 📌 2026-07-17 (fourth session) — DR3 MERGED into the repo docs. M4a still IN PROGRESS.

**What happened:** DR3 (six review rounds) had been authored in a parallel session against the
pre-pilot docs and staged in `docs/update/`. Merged it into `docs/` as a **3-way merge**
(base = git `725ad42`, ours = `6c93848` the M4a pilot, theirs = `docs/update/`), so nothing was
hand-copied. **5 conflict regions, all resolved and verified.**

- **🔴 THE MERGE HAZARD, avoided:** `docs/update/` branched from `725ad42` — the commit BEFORE the
  M4a pilot (`6c93848`). Applied wholesale it would have **silently reverted the M4a pilot record**
  (header back to "second session", the pilot session block deleted, the plan's M4a status block
  deleted, NEXT reset to "M4a — do not start unprompted") while 140 rendered+validated images, a
  report and 134 green tests sat on disk. **Kept ours** for the header + pilot record, **took DR3**
  for all new content. *(The parallel session flagged the risk itself: "AMENDED WHILE M4a RUNS —
  sync to the repo copy!")* **Lesson: a doc update authored off-HEAD is a revert wearing an
  update's clothes — 3-way merge it, never copy it.**
- **🔴 DR3 BANNED WORDING IT DID NOT SWEEP — including in a doc it never opened.** DR3 retired
  "dies" / "adjudicates-the-disagreement" / pre-result "first", then left **five live instances** in
  sections it did not rewrite: PROJECT_MEMORY's "ADJUDICATION FRAMING … **We adjudicate**" +
  "***first*** leak-controlled PROBE trace"; the plan's M5-#2 "This **adjudicates** a now-published
  disagreement"; and — **the one that proves the point** — `VSR_niches_critical_deep_read.md`, which
  **was not in `docs/update/` at all** (DR3 shipped 4 docs + 2 new; the niches doc was never in
  scope), still carrying "We adjudicate", "*first* leak-controlled probe trace … across the **full
  chain**", and "framing upgraded from gap to **adjudication**". All **superseded in place with
  visible retraction banners** (rule 13: a silent deletion lets the elegant argument walk back in).
  ***Generalises — a ban is not self-enforcing, and a revision's SCOPE is not the corpus's scope:
  grep every doc for every banned form the same session the ban lands.*** The banned framing had
  survived in a doc whose own §Revision section is where the competitor analysis lives.
- **Verdict on the standing question — "was it safe to merge while M4a runs?" → YES, and NO restart.**
  DR3 changed the **GATE (evaluation)**, never the **stimulus spec**: the five M3.2 decorrelations,
  the solo-ID amodal pass, the validator, the calibration are all untouched. **No rendered pixel and
  no generator line is invalidated.** The pilot was always going to be superseded by the gate-scale
  render, so there was no sunk render to restart. **The timing was lucky** — DR3 landed *before* the
  expensive render, not after.
- **⚠ BUT M4a's SCOPE GREW, and two gaps are MEASURED (not inferred) — see plan M4a status items 6–8:**
  - **Nuisance factors vary but are DISCARDED.** `sampler.py:240–252` samples `ground_color` and
    `sun_energy`/`sun_direction_jitter` per image and never persists them into `factors` → the
    held-out-lighting / held-out-background splits DR3 now requires are **not constructible from the
    existing annotations**, even though the factor varies. Same class as `strip_pool()`-exists-but-
    never-cached.
  - **🔴 TEXTURES DO NOT EXIST** anywhere in `src/sbind/stimuli/` or the M4a configs (ground = flat
    colour). **This is a PRE-EXISTING violation of the plan's own item (d)** — `reports/m4a_battery.md`
    never flagged it. DR3 merely made it load-bearing. Also absent: lighting FAMILIES, renderer-seed
    variation (`cycles_seed: 411` fixed), render/AA variation (`samples: 96` fixed).
  - **New M4a deliverable:** the pre-registered NUMERIC bounds for M4b's leak criterion — **M4b may
    not start without them** (relative collapse is insufficient: 0.94→0.40 is still a leak).
  - Pilot NUMBERS are now measured against a superseded gate — not wrong, no longer *sufficient*.
    The load-bearing signal survives: counterbalanced drove physical-size↔depth to **r = 0.033**.
- **⚠ STALE DATA — DELETED 2026-07-17, and it exposed a PROVENANCE BUG that outlives it.**
  `$DATA_ROOT/stimuli/m4a_v1_counterbalanced/` held **60 images under the FULL-battery name**, its
  own config declaring `n_images: 420` (aborted run). Deleted, with `reports/m4a_smoke_analysis.json`
  (which analysed it). Three reasons, in ascending order of importance:
  1. **`--resume` would have silently mixed it in.** `render_stimuli.py --resume` skips ids whose
     annotation exists → a later 420 run inherits 60 images from a *different generator*, all green.
  2. **It was unreproducible**, so nothing recoverable was lost: stamp said `git_hash: 725ad42`, but
     `configs/m4a_v1_counterbalanced.yaml` **did not exist at that commit** (added in `6c93848`).
  3. **🔴 THAT MISMATCH IS THE REAL FINDING: `utils/config.git_hash()` NEVER LOOKED AT THE WORKING
     TREE.** It returned a bare `HEAD`, so the plan's §1 promise — *"every run logs config, git hash,
     seed"* — was **silently FALSE for every run from a dirty tree**, i.e. most runs during active
     development. A stamp naming a commit that could not have produced the output is worse than no
     stamp: **it manufactures provenance.** Same shape as every bug in this project's history — the
     pipeline ran green while recording wrong data. **Fixed:** `git_hash()` suffixes `-dirty`;
     `run_metadata` records `git_dirty` + `git_patch_sha` (sha of the uncommitted delta, so a dirty
     run is at least *identifiable*). **Untracked files count as dirty** — the case above was driven
     by an *untracked* config, which a `git diff HEAD`-only check would have called clean. Six tests,
     **verified to FAIL against the old implementation** (rule 11: prove the instrument registers a
     positive). This was load-bearing for **M4a blocker 3 (determinism byte-compare)**, where
     provenance IS the deliverable, and for every M5 probe run after it.
- **Docs added:** `docs/PITCH.md` (canonical short pitch — referenced as canonical since 07-16 but
  **never actually in the repo** until now) and `docs/REVIEW_RESPONSE_2026-07-16_1.md` (the DR3
  arbitration). DR3's memory cited the latter as `REVIEW_RESPONSE_2026-07-16.md` — **a path that did
  not resolve** (rule 10); fixed to the real filename.
- **Checked, no action:** PITCH.md is already CLEAN of the new bans — DR3's own warning that
  "'adjudicating' and 'first' phrasing likely present" is **stale**; its only "first" is the temporal
  "we first need to establish". Nothing blocks the Jul 24 YANS registration on wording grounds.
- **🔁 SECOND UPDATE BATCH, same day (`docs/updates/`, plural — the first was `docs/update/`):
  DR3-r7 execution annex A1–A11 ADOPTED; four REVERTS rejected. THE HAZARD REPEATED.**
  - **Taken:** the **M5/M6 EXECUTION ANNEX (DR3-r7)** — 86 lines, plan §M5: identification protocols,
    not framing (the framing stays frozen). A1 leak decomposition · A2 cross-stage equivalence ·
    A3 alternative-route battery (**new outcome-matrix row: DISTRIBUTED BINDING**) · A4 common
    latent-noise for H2a · A5 Gate-1 scope · A6 oracle-text scope · A7 anchor-experiment controls ·
    **A8 mediation needs an INDEPENDENT decoder** (an intervention-defining probe may never grade its
    own intervention — h′=h+αw raises w·h′ ALGEBRAICALLY) · A9 quantitative preregistration for H1 ·
    A10 external validity split behavioral/mechanistic · A11 capacity ladder is CORE (recoding vs
    bottleneck). Plus the M4a prompt's **THIRD AMENDMENT** (Gate 1 = *statistical recoverability under
    this training distribution*; + renderer-family/resolution+AA/photometric holdouts, cue-ablation
    renders, an interpretable pixel baseline beside the CNN, human pairwise ranking).
  - **🔴 Rejected — the batch's PLAN branched from the OLD pre-merge `docs/update/` copy, not HEAD**
    (arithmetic: 759 + 87 ≈ 846 = their line count), so adopting it wholesale would have (1) deleted
    the M4a status block **again**, (2) reverted the M4b header to the retired W&G bar, (3) restored
    **"This adjudicates a now-published disagreement"** — wording **DR3 itself banned** — and (4)
    un-fixed the M5 numbering. Their PROJECT_MEMORY was byte-identical to ours, which is what made the
    plan's off-HEAD provenance visible. **Only the annex was lifted; all four reverts rejected.**
  - **🔑 THE PATTERN, now twice in one day, and the irony is the lesson:** the very batch that ADDS a
    new ban (A1) simultaneously re-introduced wording an EARLIER ban had already retired — because it
    was authored against a stale base. **A ban travels with a document, not with the project.**
    **STANDING PRACTICE (adopt): every incoming doc drop is (a) diffed against HEAD before adoption,
    (b) checked for the authored-off-HEAD signature — does it contain the newest committed session
    entry? — and (c) merged by taking NEW CONTENT ONLY, never by copying the file over.**
  - **A1's new ban applied corpus-wide:** *"the selection IS the answer"* → **"selection and stimulus
    geometry already contain most of the answer"** (PROJECT_MEMORY + proposal, retractions visible).
    Our R² = 0.942 proves **stimulus confounding** and invalidates raw scores; it does **not** isolate
    the **selection mechanism** from **positional representation**. The strong form needs A1's
    isolation battery (random-i.i.d.-token control · position-only synthetic tokens · fixed-mask/
    different-depth pairs · content-location permutation · pooling ± positional components). Leak
    stays a **CANDIDATE** contribution. ⚠ **A1's fixed-mask/different-depth control IS the contrastive
    pairs — already M4a blocker 1**, so that blocker now carries M5 weight too.
- **🔧 PREVIOUS-MILESTONE REPAIR (2026-07-17, before resuming M4a work): the discussion updates
  had INVALIDATED CLAIMS IN CLOSED MILESTONES. Fixed M3 (wording) and M2 (taxonomy).**
  - **M3 — DR3-r2 #10 violated in three artifacts.** *"The mirror-swap patching profile reproduces
    **EXACTLY**"* → **"exact" is banned without a PREREGISTERED SIMILARITY METRIC**, and we have
    none: we matched a qualitative stage/layer pattern by eye. Now *"key qualitative signatures
    reproduce"*. And *"above-chance influence **matches or beats theirs**"* → **banned: cross-study
    effect comparisons are DESCRIPTIVE ONLY** (noise construction, doses, selection and baseline
    beliefs all differ; the figures are not commensurable). Fixed in PROJECT_MEMORY, plan, and
    `reports/m3_reproduction.md`; retractions left visible.
    - **🔑 THE SHARPEST INSTANCE YET OF "A BAN IS NOT SELF-ENFORCING": THIS FILE STATED THE BAN AT
      LINE ~228 (DR3 addendum r2) AND VIOLATED IT AT ~808 AND ~818 — in the same document, on the
      same day.** Writing a rule into a doc does not apply it to the doc.
  - **✅ RESOLVED 2026-07-18 against the paper (2601.12626v1 HTML full text) — it was the more
    serious error.** Kang's paper reports a NAMED statistic, "above-chance influence" = **+43.6%**
    (its §3 text AND Fig 2 caption: *"Spatial IDs have 43.6% above-chance influence on average"*).
    **43.6 ≠ 64.4 − 29.5 = 34.9** — it is a CROSS-MODEL AVERAGE, not the naive median-minus-noise
    subtraction our report performed. **The ledger was right; our report CONSTRUCTED 34.9 and
    labeled it "the paper's own summary statistic."** 34.9 is deleted as a Kang attribution
    everywhere; our +31.3 / +43.3 stay as OUR descriptive figures. Fixed in the report (table +
    resolved retraction block), plan, and this file. ⚠ Final owed check: eyeball the actual Fig 2
    caption in the PDF — the resolution rests on the ledger's full-text read + a web-fetch of the
    HTML (two agreeing secondary reads), not the rendered figure. DR3-r2
    #10 makes it non-load-bearing for the CLAIM; it is still load-bearing for the REPORT.
  - **M2 — 🔴 "physics" IS THE PAPER'S *TRAJECTORY* CATEGORY (verified from the items, 2026-07-17).**
    CausalSpatial's paper taxonomy is **Collision / Occlusion / Compatibility / TRAJECTORY**;
    `physics` and `realworld` are **repo folder names appearing nowhere in the paper**. Every
    `physics` item is trajectory prediction (*"based on the soccer ball's trajectory, will it go
    into the goal?"*). Our docs had written it off as *"loads on physics priors → non-target
    control"* — **a scientific judgment made against a directory name**, and it is **S4-C
    (hypothetical spatial state)** material instead. Re-scoped; arXiv **2601.13304** added (never in
    our docs); adapter docstring now warns that `SUBSETS` are folder names, not categories.
    **⚠ Third time this dataset's surface has misled us** (after the "unique" `id` and the
    `not_sure` lie). §2.5(c): a FIELD is a hypothesis. §2.5(e): a DATASET is. **Now: a DIRECTORY
    LISTING IS NOT A TAXONOMY.**
  - **Method note — how these were found:** by auditing the M4a brief's §5 Definition of Done and
    the ban list **against the artifacts**, not against the reports' own summaries. `m4a_battery.md`
    listed 5 blockers because it enumerated *what the session did*; the brief requires **three more**
    nobody had listed (below). **A report's own blocker list is a hypothesis too.**
- **🔬 M4a BLOCKER #10 DONE — the v1 LEAK CEILING is measured (structured splits). Result: the
  decorrelation is INSUFFICIENT as configured → §2.7 says do NOT launch the 1k render yet.**
  Report: `reports/leak_ceiling_v1.md`; JSON: `reports/leak_ceiling_v1/`.
  - **Tooling:** `leak_ceiling.py` did RANDOM KFold only, which §2.7 forbids ("never only random
    splits"). Extended it (and `probes/ridge.py` — added a `groups=` GroupKFold path, since M5 needs
    structured splits too) to hold out whole object identities / depth ranges / camera poses. New
    invariant test: a group-confounded signal recovered on a random split MUST collapse under a
    held-out-group split (`test_grouped_split_kills_a_group_confounded_leak`).
  - **z_depth (PRIMARY), structured ceiling, counterbalanced:** held-out depth-range **0.837**
    (v0 was 0.957) — a real but PARTIAL improvement; headroom opened (v0's ~0.99 left none), but the
    residual ~0.84 comes from **elevation + retinal size, which are LEGITIMATE monocular depth cues a
    plausible scene cannot remove** — a **strong interpretable monocular baseline** (B1, PRESERVED under ruling 3), NOT a baseline the model must beat,
    not a bug. ⚠ v0's held-out-OBJECT z was 0.375 only because it was removing the category↔depth
    confound; counterbalanced fixed that confound, so its held-out-object z is 0.875 (geometry leaks
    depth robustly across objects). Compare sets on held-out-DEPTH-range, the clean shared axis.
  - **x_lateral (the POSITION LEAK): did NOT improve** (≈0.94 → ≈0.94 structured). ⚠ **World-frame x
    is also 0.915** (held-out camera pose) — so it is NOT a camera-frame-target artifact; the camera
    jitter genuinely fails to decorrelate image position from lateral world position. **Hypothesis to
    TEST (rule 13), not asserted: jitter too weak** (yaw ±3°, pitch ±2.5°, height ±0.12 m). Fix is a
    generator parameter (widen ranges / add camera lateral translation), then re-measure — cheap.
  - **THE CALL (advisor-level, NOT decided by me):** before the 1k render — (1) strengthen camera
    jitter and re-run the ceiling (target: x structured < 0.9); (2) decide the z policy: accept ~0.84
    as the strong interpretable monocular baseline (B1, preserved) OR split the ceiling into position/selection features
    (fixable) vs monocular-cue features (inherent) so Δ_repr|dumb does not conflate them; (3) proceed
    only if headroom is defensible. **The blocker did its job: caught insufficient decorrelation
    BEFORE the expensive render — which is exactly why the leak ceiling runs first.**
- **🔧 STRENGTHENING EXPERIMENT (2026-07-18, "strengthen" instruction) — translation WORKS on the
  meaningful target; and it uncovered a placement-config bug + a wrong-target bug in the leak tool.**
  Report addendum: `reports/leak_ceiling_v1.md`. Set: `m4a_v1_counterbalanced_pilot_j2`.
  - **Added camera TRANSLATION** to `_jitter_camera` (`pos_x_m`/`pos_y_m`; camera was fixed at x=0,
    pan-only). Result: **world-frame x leak 0.915 → 0.817** with just ±0.3 m lateral dolly (held-out
    camera pose). It works.
  - **🔴 THE LEAK TOOL WAS REGRESSING THE WRONG LATERAL TARGET.** `leak_ceiling.py` used `pos_cam[0]`
    = **camera-frame** x, which is coupled to image position by the projection identity
    `u ≈ f·X_cam/Z_cam + c_x` — **NO camera motion can decorrelate it** (0.94 → 0.93 under strong
    jitter). Its ~0.94 "leak" is a definitional identity, not a representational leak — the SAME trap
    as v0's x. The meaningful target is **world-frame x** (`pos_world[0]`): the model must fuse image
    position with inferred camera pose to recover it. **⚠ TODO: point `leak_ceiling.py`'s x target at
    pos_world[0], not pos_cam[0]** (deferred — it is an M5 leak-methodology choice: which lateral
    quantity is the claim about).
  - **🔴 PLACEMENT CONFIG WAS DEAD (bug, `cf244b3`).** `target_bbox_margin_px` (14) /
    `target_frame_margin_px` (6) / `target_placement_attempts` were read from `constraints` but every
    config puts them under `condition` → margins silently **0**, attempts stuck at 120, on EVERY M4a
    render to date. The "explicit margins" PROJECT_MEMORY bragged about never took effect. Fixed
    (read from condition, constraints fallback) + 2 regression tests. **⚠ Existing pilots were
    rendered with ZERO target margins → they need re-rendering under the corrected wiring regardless
    of jitter.** Another "config that looked set but wasn't" — the recurring failure class.
  - **PLACEMENT vs DECORRELATION TENSION (a real design finding):** aggressive camera jitter
    (±0.6 m/±10°) can't place non-overlapping in-frame target pairs — keeping both targets cleanly
    in-frame IS a position constraint that fights decorrelation. Going past ±0.3 m needs a WIDER FOV /
    pulled-back camera (→ §2.2(e) recalibration).
  - **z is unchanged** by camera motion (~0.82–0.88) — it is monocular cues (elevation + retinal
    size), a strong interpretable monocular baseline (B1). Camera translation targets the lateral leak, not the depth one.
  - **DECISIONS ON THE TABLE (advisor-level, NOT decided):** (1) world-frame vs camera-frame lateral
    target; (2) how far to push camera motion (±0.3 m now, or wider FOV + recalibrate); (3) z policy
    (accept ~0.85 monocular baseline, or split position vs monocular features in the ceiling).
- **⚠ M4a BLOCKER LIST IS 11, NOT 8 — three found 2026-07-17 by auditing §5 Definition of Done:**
  - **9. Worst-case cue constants were NEVER re-derived.** v0 carried its derivation *in config*
    (`required_ratio_by_pairing`, worst case `near_cylinder_far_cube: 1.158`, +2% → `min_depth_ratio:
    1.18`). M4a's floors — **1.85** (natural-congruent) and **1.05** (counterbalanced/conflict) — are
    **bare numbers with no derivation**, no `cue_constants` block in any M4a config, and **no measured
    fill factors for chair/mug/bottle**. §2.2(e) requires re-deriving from worst case;
    `calibrate_sizes.py` was re-run, `derive_cue_constants.py` was not. Violates §6 ("no number
    without provenance") and evaluation-law clause 1. **Hypothesis to MEASURE (not argue, rule 13):
    the arbitrary 1.85 floor may be CAUSING natural-congruent's ratio-gate failure** (R² = −0.252) by
    squeezing the ratio range — the report writes that off as *"narrow and shortcut-heavy"*, i.e. as
    inherent, when it may be an artifact of an underived constant.
  - **10. The v1 LEAK CEILING was never run** (§2.7 + §5). `scripts/leak_ceiling.py` exists; no v1
    report; `m4a_battery.md` never mentions it. **This is M4a's most important measurement** — the
    direct v0→v1 answer to M3.2's position leak (did camera jitter collapse mask-geometry
    decodability from x R² = 0.942?). It runs on the EXISTING 140-image pilot, on CPU, in minutes,
    and it is a **go/no-go on the generator design**: if mask geometry still predicts depth near
    ceiling in counterbalanced, the decorrelation failed and textures / contrastive pairs / a
    1,020-image render are all premature. **Run it FIRST.**
  - **11. The decorrelation matrix** (§5: pairwise correlations among depth, elevation, retinal size,
    physical size, image position — *"by measurement not assertion"*) is not in the report; only two
    `r` values are.
  - ✅ **Checked and CORRECT — do not "fix":** the per-regime floors are *designed*, not sloppy —
    natural-congruent uses **1.85**, only counterbalanced/conflict use 1.05 — and
    `validate_stimuli.py:236-244` is **regime-aware**, exempting counterbalanced/conflict from
    size-congruence with a documented reason (rule 3 done right, not a silent skip). The open issue
    is the floors' **provenance**, not their regime logic.
- **📎 Decks + ledger now IN THE REPO** (`docs/CITATION_LEDGER.md`, `lab_presentation_part{A,B}.pptx`):
  the ledger is **verified against arXiv full texts** and closes the one-page's last gap — a
  **verified** concrete failure example now exists without new experiments. Strongest lead:
  **Ill-Posed 2606.24335** — a **text-only LLM that never sees the image beats every open VLM** on the
  tape-measured in-the-wild split, and apparent-size manipulation expected to move answers **2.33×**
  moves them **1.00× (median, all 12 models)** — paired with **our own** 95.3% / 98.0% qualitative
  left/right (`reports/m3_reproduction.md`). ⚠ Nuance the one-page must not muddle: Ill-Posed finds
  models **insensitive to apparent size** and driven by **identity priors** (8/12; largest −20.3 pp) —
  the *benchmark* carries the cue confound; the *model's* strategy is priors. Both true, not the same.
  ⚠ **Ledger correction NOT yet propagated:** CausalSpatial = **arXiv 2601.13304** (never in our docs)
  and its real taxonomy is **Collision / Occlusion / Compatibility / TRAJECTORY** — **"physics" and
  "realworld" are REPO FOLDER NAMES, not paper categories**. But plan §2.5(f) + this file's validation
  layer specify the closed set using those folder names, including the judgment *"physics (311) loads
  on physics priors → non-target control"* — a scientific call made against a folder name, and the
  **third** time this dataset's surface has misled us (after the `id` and `not_sure` lies). Fix before
  M5; it does not touch M4a.
- **Unchanged and still open:** YANS registration **closes Fri Jul 24** (7 days); the one-page
  問題・新規性・実験設定 statement; lit-watch scheduled task; human-baseline/ethics.

### 🔴 DESIGN REVISION 3 (2026-07-16, second session) — third external review, arbitrated
Full arbitration: `docs/REVIEW_RESPONSE_2026-07-16_1.md` (read it before writing any
claim-level sentence). The review read the lab deck as a scientific argument; most points hit
PROJECT framing, not just slides. **What changed (do not revert):**
1. **Two-level variable structure, now explicit everywhere:** CONTINUOUS depth (z; Δz/ratio
   secondary) = the PROBE target · ORDINAL ordering = the BEHAVIORAL anchor · qualitative =
   positive control. The old wording alternated "continuous metric depth" / "ordinal depth" in
   claim sentences — internally contradictory; fixed. Claim sentences must name both levels.
2. **"Adjudicate the published disagreement" is RETIRED as the claim.** Deccan (2605.20448) and
   Anchored (2606.06714) studied different variables/methods and are strictly compatible; their
   *interpretations* point at opposite ends of the LM (kept as attributed motivation). Canonical:
   *"competing localization hypotheses for different forms of spatial information; we test which
   pattern — projector-, binding-, or readout-bottleneck — holds for controlled continuous
   depth."* Pre-registered site-2-vs-4 contrast unchanged.
3. **M4b's gate reformulated as VALIDITY-ONLY** (the old "W&G pattern must emerge / semantics ≫
   metric" put a substantive hypothesis inside a validity gate): positive controls decode ·
   nulls at chance · leak ceiling COLLAPSES vs v0 · held-out-factor generalization · dynamic
   range. An unexpected metric ceiling triggers the mandatory diagnostic checklist — and if all
   validity checks pass, high metric decodability is a FINDING, not a gate failure. W&G gradient
   = benchmark comparison, not go/no-go.
4. **Position-leak = CANDIDATE contribution** until the 6-condition promotion checklist passes
   (see arbitration §18; condition 6 — prior work doesn't control an equivalent feature — already
   verified for W&G). "Non-representational features" → "external/trivial-feature baseline".
5. **Construct fix: cues are not shortcuts by definition.** Cue-responsive (single-cue reliance
   failing under decorrelation) vs cue-integrated (generalizes when correlations change) — the
   conflict regime's fusion analysis operationalizes exactly this.
6. **Scoped readings enforced:** Kang faithfulness (tested models/tasks only) · W&G null
   (protocol-relative — "challenges the naive form", never "kills") · Ill-Posed LoRA (tested
   setups) · monocular taxonomy conditional (ratio needs assumptions; gate verifies, not assumes)
   · oracle-text narrows-not-localizes · the M5 curve "distinguishes the three candidate patterns
   for controlled depth in the tested architectures" (no universal adjudication) · ablation nulls
   ≠ absence (redundancy; Cui's LM backup is the live example) · patching = "causally capable
   under this intervention".
7. **New wording bans:** dies/killed (information) · adjudicates-the-disagreement · "first…"
   pre-result (safe form: *"a stage-wise, trivial-feature-controlled protocol for tracing
   object-specific depth (continuous probe targets, ordinal behavioral anchor) from visual
   encoding through language-token representations"*) · unqualified cue-shortcut ·
   "explicitly/accessibly encoded" from a linear probe · "only rendering can decorrelate".
8. **Meta-lesson (third instance): compression re-introduces retracted overclaims.** The deck
   restated things the docs had already fixed. Every claim-level sentence in ANY artifact copies
   from PITCH.md/proposal — now including decks built by AI sessions.
⚠ PITCH.md and the YANS abstract must be re-checked against bans (2) and (7) — "adjudicating"
and "first" phrasing likely present. Flag for Kaho before Jul 24 registration.

### DR3 addendum — review round 2 (2026-07-16, same reviewer): framing ACCEPTED, 30 residuals adopted
Verdict received: *"the central argument is now defensible."* All residual items adopted; the
methodological ones (not just slide wording) are now in the docs:
- **Gate 1 hardened** (plan + M4a prompt, AMENDED WHILE M4a RUNS — sync to the repo copy!):
  supervised pixel baseline must generalize across held-out NUISANCE factors, never only random
  splits; per-LEVEL gates (ordinal / continuous ranking / calibrated magnitude); human check
  licenses ordinal only. M4a must also deliver the pre-registered NUMERIC bounds for M4b's leak
  acceptance (relative "collapse vs v0" is insufficient — 0.94→0.40 would still be a leak).
- **M5 additions 7–10 (plan):** text-side trivial baselines mandatory (token identity/position,
  mention order, template role, option order — text probes have their own leak classes; never
  imply visual=contaminated/text=clean) · stage profile reported under MATCHED evaluation
  (matched-capacity readouts, nested CV, per-cell CIs, stage-specific dumb baselines; report
  dumb-only/rep-only/combined/Δ with permutation null — Δ alone is not decodability) ·
  two-ordering operationalized as ORDER-ROBUST ACCURACY (correct under both orders, adjusted
  chance, per-order + order-effect CI) · cross-study effect comparisons DESCRIPTIVE only (our
  +43.3 vs Kang's above-chance influence [⚠ RECORDED HERE AS +34.9; CORRECTED 2026-07-18 to the
  paper's actual +43.6 — 34.9 was our own mis-derived subtraction, never Kang's number] not
  comparable — noise construction/doses/selection differ; patching profile = "qualitative
  pattern reproduced", never "exact").
- **"Metric ID" name RESERVED** until the construction is defined (probe direction / regression
  vector / matched-condition difference / low-rank subspace / interchange — different causal
  interpretations). Interim term: "graded intervention along a validated depth-related direction
  or subspace" (proposal §2.3(4), plan M6).
- **H2 rewritten** ("collapsing" presupposed a mechanism): ordinal remains recoverable at
  object-word sites while continuous magnitude becomes substantially less recoverable or less
  causally available — compression/recoding/detachment/non-use decided by the ladder +
  interventions.
- **Binding rule conditions 4–5 operationalized** (proposal): wrong-object intervention control,
  prompt-conditioning check, name-reference redirection — influence-at-a-layer ≠ binding.
- **Slide-level bans enforced in decks** (round-2 sweep): representation ≠ decodability (A6) ·
  first-answer-token autoregression correction (A7) · functional-abstraction caveat on the
  skeleton (A4) · ordinal/metric question split (A10) · "cannot measure it" → behavioral
  contrast · "falls exactly along the ladder" → broadly consistent · MindEdit = hard spatial
  reasoning, not clean metric-only evidence · compass wording → error-distribution observation ·
  cue note fixed (A19) · "only rendering" removed from Part A · "accuracy lies" → limits of
  accuracy · black-video → "much of the score available without visual evidence (linguistic/
  category/benchmark priors)" · "synthetic ⇒ priors can't help" FIXED (our own war stories
  disprove it) · "semantics: perfect" → protocol-scoped shape accuracy · "topology survives" →
  "relative-neighborhood structure remains detectable under their analysis" · endpoint synthesis
  → relationship-unmeasured wording · "nobody has traced" → "the studies reviewed here do not
  provide…" · glossary prior-free error fixed.

### DR3 addendum — review round 3 (2026-07-16): "conceptually ready"; residual wording + 4 doc refinements
Round-3 verdict: no remaining flaw at the severity of the original two; ~40 wording items fixed in
both decks (headline-vs-body compression was the pattern). **Doc-level refinements (operative):**
1. **Evidential ladder → FIVE rungs (proposal §0):** linearly decodable ⊂ image-grounded decodable
   (arbiter+ceilings) ⊂ causally available (intervention) ⊂ naturally used (specificity+mediation)
   ⊂ task-relevant causal use. "Accessible" was compressing rungs 2–3 and claiming too much from
   probes+controls.
2. **H1 split into probe-level vs causal-level predictions (proposal §1):** less-linearly-
   recoverable-at-object-word-sites is the probe prediction; accessibility/binding is licensed
   only by probe + intervention together.
3. **Binding rule conditions 1–2 hardened (proposal §2.3):** condition 1 requires beating
   selection- AND annotation-derived baselines with matched token-count/region-shape controls;
   condition 2's "matched evaluation" is now defined (matched capacity, equalized samples,
   comparable pooling, text-side nuisance baselines, CIs). Condition 3 rephrased: "validated
   Kang-style positive control" — Kang LOCALIZED influence to object-word sites and INTERPRETS it
   as binding; we do not inherit the interpretation as fact.
4. **Terminology:** "leak" reserved for the SELECTION mechanism; text-side controls are "nuisance
   baselines". Claim wording: "selection-leak-controlled (with nuisance baselines)" — never bare
   "leak-controlled" (cannot guarantee all leakage). "Kang's mechanism reproduced" → "key
   qualitative signatures partially reproduced; absolute effect did not". "Kills the leak" →
   "disrupts; residual verified against the preregistered bound". Scoop-risk phrasing: "adjacent
   or overlapping territory".
Also enforced in decks: ordinal ≠ near-floor (variable under familiar cue correlations; continuous
is the consistently weak level) · A45's "signal in, signal not used out" → unresolved-contrast
wording (the two observations are unlinked) · snap-back = patching-restorability, not
natural-encoding · "no existing study" → "the studies reviewed here" · ablation-heads,
LoRA-topology, Cui-underestimation all scoped to their setups.

### DR3 addendum — review round 4 (2026-07-16): "very close to content-ready"; 33 residuals adopted
Final wording pass on both decks (compression-overclaim pattern again) + three doc refinements:
1. **H2 SPLIT into H2a (representational) / H2b (causal)** — proposal §1. The 'less recoverable OR
   less causally available' phrasing let two different outcomes both confirm H2.
2. **Binding condition 5 operationalized as REFERENCE REDIRECTION** (rename/re-reference redirects
   the effect; non-target intervention doesn't reproduce it; effect follows the referred object,
   not token position). **Condition 2's matched evaluation extended** (equal probe class +
   regularization, nested CV, comparable pooling dimensionality, lexical-identity controls, CI on
   the cross-stage difference itself).
3. **Statistical criteria named precisely:** "nulls at chance" → label-permutation scores follow
   the preregistered null distribution + nuisance baselines below the acceptance bound (shuffled
   R² can be negative; chance is not one number). Δ reported with dumb-only / rep-only / combined
   + permutation CI, matched regularization — never Δ alone. "Dumb-features CEILING" → prefer
   "nuisance baseline + incremental-value analysis" (it is not a true upper bound).
Deck-side (highlights): A37 note comparison removed (descriptive only) · Act-4 title "one public
disagreement" → "two competing localization hypotheses" · B3 "cannot fool us" → "failure modes
explicitly tested" · anchor experiment = transfer test (binding only via the full rule) · "repair,
not steering" → "testing repair vs generic steering" · M3.2 W&G numbers = REFERENCE PATTERN (not
'reproduction target' — stimuli/extraction differ) · "in-distribution" steering qualifier now
carries operational checks (norm/distribution checks + unrelated-behavior preservation) · Kang
4×4 coarseness attributed to their SUPERVISION/EVALUATION, not the internal channel · six-item
leak-promotion checklist enumerated on-slide. Reviewer's close: content ready for a technically
informed lab audience after these.

### DR3 addendum — review round 5 (2026-07-16): REVISION LOOP CLOSED
Reviewer: "substantively credible … final research-design hardening … after these, stop revising
the conceptual framing and move to implementation." All 24 items applied. The three that changed
the DESIGN (docs, not slides):
1. **Intervention-site selection PREREGISTERED** (proposal §2.5, plan M5-#13): primary = the
   stage-2 vs stage-4 contrast; probe-indicated sites are exploratory + confirmed on held-out
   data — the old "intervene where the probes indict" rule risked pick-the-largest-drop
   circularity. **Depth-direction construction / validation / causal evaluation on three disjoint
   splits.**
2. **Ordinal-vs-continuous comparisons DIFFICULTY-MATCHED** (plan M5-#11): matched-bin
   discretization, ordinal-from-continuous-labels, equalized capacity + samples, calibrated noise
   ceilings, rank/information metrics — otherwise H2a measures an easier target, not selective
   preservation. **H1/H2a/H2b relabeled as one location claim + two selectivity claims layered on
   it** (H2a extends H1, not independent).
3. **TWO positive-control classes per stage** (plan M5-#12): semantic AND
   continuous-geometric-by-construction/injection — a shape control cannot license a
   continuous-depth null. Binding **condition 4 now contains mediation** (held-out, depth-specific
   intervention must move the internal depth readout AND the object-specific answer).
Also: **ladder rung 3 renamed "causally ALTERABLE"** (available/used start at rung 4; generic
answer-moving interventions are rung-3 only with off-target controls) · Gate 1 held-out factors
extended to renderer seeds / lighting families / backgrounds / render settings (cross-renderer
ideal) · order-robust-accuracy null via permutation/paired-response model, not naive 25% ·
"dumb-features CEILING" retired as a headline (nuisance baselines + incremental-value analysis;
"leak ceiling" only as the defined selection-mechanism maximum) · "full chain" → "five
prespecified functional stages" · "immune" → "escapes this specific leak" · Kang steering repro
stated as "positive direction-vs-noise contrast". **Wording-review protocol going forward: the
conceptual framing is FROZEN; future reviews target stimuli, statistical plan, extraction code,
and results.**

### DR3 addendum — review round 6 (2026-07-16): VERDICT "READY". Conceptual deck FROZEN.
Reviewer: "This version is ready … The argument itself is no longer the weak point. The next
scientific risk is experimental execution." Three final clarifications applied:
1. **Continuous positive controls made NON-CIRCULAR** (plan M5-#12): injected implementation
   control (independent activation dimension; validates pipeline) + independently established
   natural geometric control — neither constructed from the probe being validated.
2. **H2a difficulty-matching operationalized on-slide** (B7): matched targets from the same depth
   labels/scenes, equalized capacity/samples/nuisance controls, ceiling-normalized evaluation.
3. **Binding condition 1 upgraded** (proposal + appendix slide): "significant incremental
   recoverability beyond prespecified selection/nuisance features under matched nested
   evaluation" — the "above the leak ceiling" shorthand and the glossary's Δ-only criterion are
   retired.
(+ A48: "less recoverable — and whether/where causally unavailable — is unmeasured".)
**STANDING RULE: the conceptual framing and both decks are FROZEN. Six review rounds complete.**
Remaining review surface (the reviewer's own list): site-tensor mapping, scene-family leakage in
splits, the continuous-control construction, ordinal/continuous matching, independent direction
learning/evaluation, and POWER for the preregistered stage contrast. These live in M4a/M4b/M5
execution — deck edits only follow DATA now (M4a renders into B-5, pilot curves into Act 7).

### Pre-M4a threat sweep (2026-07-16, second session) — CLEAR, M4a may start
Anchor citers + topic sweep re-run before starting M4a. **No new threat found; no design change
forced.** Details:
- **Kang 2601.12626 is now an ICLR 2026 poster** (openreview + iclr.cc confirm). Visibility ↑ →
  citer velocity will rise; cite the ICLR version in the paper. Every-day-is-load-bearing stands.
- **Citer sets, verified via Semantic Scholar:** Kang = the known set (2607.03358, 2606.31257,
  2605.30161, 2605.20784, 2605.12586, 2605.07148, 2603.22278) **plus 2603.08096 TrianguLang**
  (pose-free language-based 3D localization — pure engineering, no internal probing → LOW; it was
  not explicitly enumerated in the earlier "8 unique" note, so recorded here). W&G citers = only
  2606.31257 (known). Cui citers = only 2604.13321 (known). **Anchored 2606.06714 = 0 citers,
  Deccan 2605.20448 = 0 citers (v1 only), Ill-Posed = 0 citers.** No follow-up preprints from
  either scoop-risk group surfaced.
- **Topic-sweep triage (all LOW / cite-optional, none competing):** 2605.15876 "Unlocking Dense
  Metric Depth Estimation in VLMs" (fine-tuning existence proof — cite alongside DepthLM; not a
  localization study); 2606.30344 early-cue-precision / controlled cue-manipulation (classifiers,
  stimulus-philosophy sibling); 2603.18373 "To See or To Please" (visual-necessity diagnostics —
  adjacent to the 2606.31257 arbiter, optional cite); 2601.22150 illusions perceive-vs-recall
  (behavioral cousin of blank controls); 2602.00462 LatentLens (semantic token interpretability,
  NO spatial/metric — nugget: token interpretability drops ~30% on a spatial task, convergent
  motivation); 2605.05668 "Lost in Attention" (A2-family); 2603.29676 PID decomposition (ICLR
  2026; process-level, no geometry). Amodal-probing gap (S1.5) still appears open.
- **Metric VQA (Ill-Posed) still unreleased; SynSpat3D still unreleased.**
- ⚠ Caveats: arXiv abs-page fetches for W&G and Anchored were flaky → **new-version check for
  2605.07148 and 2606.06714 inconclusive — re-verify manually**; Semantic Scholar lags very
  recent uploads, so the ~2-week newest window is only covered by the topic sweep, not the
  citation graph.

### M4a pilot implementation + result analysis (2026-07-16, third session) — PILOT GREEN, M4a NOT DONE
Implemented the first M4a battery pilot and wrote `reports/m4a_battery.md`. Final rendered pilots under
`$DATA_ROOT/stimuli/`: natural-congruent 40 images / 87 objects, counterbalanced 60 / 132, conflict 40 /
87. `scripts/validate_stimuli.py` is green on all three with output-level checks: opened every image and
mask, verified visible and amodal masks, target non-occlusion, bbox/area/height consistency, uniqueness,
answer balance, semantic-prior CI, and worst-case margins. One counterbalanced distractor has nonzero
occlusion; validator now reports distractor occlusion as informational while keeping target occlusion a
hard failure.

Measured calibration for the expanded category set, target apparent height 90 px at reference depth
4.4948 m: cube 0.6660, sphere 0.8090, cylinder 0.6660, chair 0.7353, mug 0.9913, bottle 0.8378. Strict
target-placement margins are explicit in the M4a YAMLs (`target_bbox_margin_px: 14`,
`target_frame_margin_px: 6`) rather than hidden as sampler defaults.

Oracle geometric-image analysis: counterbalanced clears the target-variable gates (ordinal held-out depth
gap acc 0.967; ratio held-out depth-gap R² 0.803; lateral-x held-out camera-pose R² 0.948; z held-out
object-identity R² 0.518). Conflict also clears the pilot gates but has weaker z/object generalization
(R² 0.299), appropriate for cue-integration rather than the primary claim. Natural-congruent is a control:
ordinal/x/z are recoverable, but ratio generalization fails (held-out depth-gap R² -0.252).

Remaining M4a blockers before acceptance: true contrastive matched pairs are only scaffolded; pilot is 140
images total, not the gate-scale/full battery; M4a determinism has not been byte-compared; no human
spot-check/contact sheet yet; chair/mug/bottle are procedural stand-ins, not imported CC0 assets. Full
code verification after these edits: `uv run ruff check src/ tests/ scripts/` green and `uv run pytest` =
134 passed / 52 warnings. **Do not start M4b yet.**

## 🔴 2026-07-16 — TARGET CHANGE + FULL LITERATURE SWEEP (read this first)

### Venue & calendar (professor meeting 2026-07-16)
- **Primary target: WACV 2027 Round 2 — deadline Aug 28, 2026** (R1 closed Jun 26). The WACV
  paper = the MINIMAL CORE only (2 models, ordinal depth, five-stage curve, leak methodology,
  reproduction). **CVPR Nov 15 = fallback/extension** with the full battery. Professor approved
  the ambition; YANS consent obtained.
- **YANS 2026 poster: Aug 16–18, Sendai** (registration closes Jul 24, may close early — register
  this week). Poster = S1 plan + Kang reproduction + position leak + pilot curves if ready.
  Sequencing gift: YANS feedback lands 10 days before the WACV deadline.
- **Professor feedback:** problem & novelty did not land in the first presentation — deliverable
  pending: a one-page 問題・新規性・実験設定 statement (lead with ONE concrete failure example,
  novelty as a delta-sentence with names, setting as one concrete table).
- **`docs/PITCH.md` is now the canonical short pitch** (JA abstract + reviewed EN pitch + nine
  framing rules). Every abstract/deck/verbal explanation COPIES from it — compression from memory
  re-introduces retracted overclaims (happened twice). Advisor decks: `yans_professor_{ja,en}.pptx`.

### Full anchor citation sweep + TOPIC sweep (all five anchors; 2026-07-16)
- **🔴🔴 2605.20448 "Do VLMs Understand 3D Scenes or Just Catalogue Objects?" (May 19, Deccan AI)
  — found ONLY by topic sweep (cites none of our anchors).** 17-site activation-patching trace
  (ViT blocks → merger/projector → LM L0–27; **Qwen3-VL-8B-Thinking**; categorical occlusion counterfactuals):
  spatial recovery **collapses at the merger/projector**. Directly contradicts H1 AND Anchored.
- **🔴 2606.06714 "Anchored, Not Graded" — closest probe-based neighbor.** Traces continuous
  SLANT across encoder→projector→**LM-INPUT visual tokens** (factorial synthetic; 4 VLMs):
  geometry decodable at LM-input (R² **0.696–0.88** — ⚠ low end is 0.696, not 0.70, ledger L61) while verbal output anchors; blames the
  "representation-to-output interface"; LM-internal tracing = their DECLARED future work.
- 🔴 **SUPERSEDED BY DESIGN REVISION 3 (2026-07-16) — the retraction stays visible on purpose.**
  This section originally read: *"ADJUDICATION FRAMING (upgrade from 'gap'): two published traces
  now DISAGREE about where spatial fidelity **dies** … **We adjudicate.**"* and claimed
  *"**first** leak-controlled PROBE trace … across the FULL functional chain."* **All three forms
  are now BANNED** (dies · adjudicates-the-disagreement · pre-result "first"). The two traces are
  **strictly compatible** — different variables, methods, models and endpoints; only their
  *interpretations* point at opposite ends of the LM. See the DR3 block at the top of this file.
- **⇒ CANONICAL FRAMING (DR3):** the two studies motivate **competing localization hypotheses for
  different forms of spatial information**; we test **which pattern — projector-, binding-, or
  readout-bottleneck — holds for controlled continuous depth.** Neither paper uses a controlled
  continuous metric variable through the full chain, selection-leak-controlled probes, or
  object-word binding sites. M5 pre-registers the site-2(projector) vs site-4(binding) contrast as
  a PRIMARY analysis (unchanged).
- **⇒ CLAIM (1), PRE-RESULT WORDING (DR3; the two-level variable is part of the claim):** *a
  stage-wise, trivial-feature-controlled protocol for tracing object-specific depth information —
  **continuous depth (z; Δz/ratio secondary) as the probe target, ordinal ordering as the
  behavioral anchor** — from visual encoding through language-token representations including
  object-word binding sites.* A scoped "first" may return at write-up, after results + a fresh
  sweep, each qualifier re-verified.
- **Kang-citer batch (user's sweep + our completion; citer set now COMPLETE at 8 unique):**
  - 2607.03358 "Pathways of Visual Information Flow" (Copenhagen): direct vs text-mediated
    routing, categorical, LM-internal only; claims untouched. ⚠ WARNINGS: (i) routing FLIPS
    synthetic↔natural → M5 needs a natural-image probe sanity check or explicit caveat;
    (ii) fallback rerouting → frame injection in usage/necessity/sufficiency vocabulary;
    (iii) prompt format flips pathways → prompt format is a controlled+reported config var.
    Adopt: restoration score, both-correct pair filtering.
  - 2606.31257 "Decodable Is Not Grounded" (UNSW/NUS): decodability ≠ grounding; probe+steer can
    amplify blind priors. **MANDATORY M5 ADOPTION: the vision-ablation ARBITER** — rerun probes +
    behavior with gray-BLANK and MISMATCHED-real images at every stage. ⚠ NARRATIVE BOUNDARY:
    they show near-field metric-ish depth is GROUNDED-correct while egocentric front/back is
    sign-inverted — our claim is "where metric precision degrades/detaches", NEVER "depth unused".
  - 2605.12586 SpatialBabel (Unity): behavioral; code-vs-QA dissociation (r=0.12) = citable
    behavioral motivation for present-but-not-readout-accessible.
- **Other sweep verdicts:** O3-D 2607.01503 (cue-controlled behavioral depth benchmark, models ≤
  chance — stimulus-philosophy sibling, cite); 2604.13321 (orientations decodable at encoder,
  "present but diffuse, downstream unknown" — convergent motivation); 2606.01914 Spatial Lexical
  Bias (mechanistic pipeline for relation-WORD bias — methodological sibling, cite); 2605.20784
  (WATCH, low). False positives verified NOT citing Kang: Ill-Posed, DepthVLM, ViewDiag, Spatial
  Blindspot. Ill-Posed has zero citers; Metric VQA still unreleased.
- **Named scoop risks:** Anchored's group (declared LM-internal follow-up) and Deccan AI
  (declared multi-model follow-up). Every day to Aug 28 is load-bearing.
- **PROTOCOL UPGRADE:** monthly **TOPIC sweeps** (subject-based, anchor-independent) join the
  biweekly citation watch — the nearest competitor (20448) was invisible to citation graphs for
  two months. Also check anchors for NEW VERSIONS (the Cui v1→v2 lesson).

### W&G addendum (appendices F–I.4 read VERBATIM + code inspected, 2026-07-16)
- Position-leak provenance now VERIFIED COMPLETE: selection/position leak neither mentioned nor
  controlled anywhere in 2605.07148 (their only shortcut control = size features, no (u,v));
  limitations section is scope-only. Leak claim is ours; present it as completing their confound
  taxonomy (they: cue shortcut + semantic residualization; us: selection).
- **Paper–code discrepancy:** their Dirichlet shaping loss actually pools at object-NAME text
  tokens (self-described "heuristic"), NOT mask-pooled visual tokens as their §4 claims →
  (a) methods sections are hypotheses too — verify against code; (b) their +6–7pp from a
  text-token-site intervention is weak adjacent support for the binding-site hypothesis.
- Their I.1 explicitly cedes absolute metric distance as uninvestigated — quotable positioning.
- Mirage Probes 2606.13870 deep-read: TITLE COLLISION ONLY (probes FOR mirage behavior; semantic
  VQA; no selection leakage). Adopt contrastive-pair estimator lineage; cite Hewitt & Liang 2019 +
  Belinkov 2022 alongside our leak claim (they omit H&L; we must not).

## Who / context
- Kaho: master's student (also covering undergrad research continuity), CV/VLM/spatial reasoning focus; also interested in image generation and medical AI. Has a Notion paper database and paper-analysis skills (paper-deep-dive-notion, research-reading, research-paper-summarizer).
- Compute: lab A100 cluster. Video-scale work deliberately deferred (GPU cost).
- Private goal: CVPR 2027 (abstract deadline Nov 15, 2026 — ~18 weeks from July 8). **Deliberately omitted from the advisor-facing deck**; the pptx speaks in phases, not deadlines.
- Style preferences: concise and direct; Traditional Chinese whenever Chinese is requested; enjoys mechanistic interpretability but wants papers that also "make or improve" (Type-2: diagnose → repair), not interp-only.
- Tooling: **uses `uv` for Python** — all project setup should be uv-based (pyproject.toml, uv.lock, `uv run`), not pip/conda.
- Infra: lab server via SSH; **shared machine, no scheduler** (informal GPU coordination, no Slurm); **no container runtime installed** (could be added — prefer Apptainer over Docker if needed); OK to keep everything on the server. Not familiar with rendering tools — willing to learn; keep rendering-side complexity low.

## The project (settled — hypothesis wording REVISED 2026-07-15 after external review)

- **⚠ WORDING DISCIPLINE, project-wide: "becomes unavailable or unusable" — NEVER "is lost" / "is
  destroyed."** The loss vocabulary silently collapses **five mechanistically distinct
  possibilities** the whole design exists to distinguish: metric information may be **erased**,
  **recoded nonlinearly**, **detached from the object**, **present-but-ignored** by the answering
  computation, or **corrupted at verbalization**. Canonical statement: *"VLMs exhibit a robust
  qualitative–metric spatial asymmetry, but it remains unknown where metric fidelity becomes
  inaccessible to the downstream language computation: visual encoding, multimodal projection,
  object–token binding, or readout."*
- **S1's hypothesis, split in two (do not state it as one claim):**
  - **H1 — localization (primary):** metric variables remain **recoverable** in visual
    representations but lose **object-specific accessibility** when bound into language-token
    representations.
  - **H2 — mechanistic sub-hypothesis:** the binding transformation preferentially preserves
    low-dimensional **ordinal** structure while collapsing continuous magnitude.
- **🔴 DO NOT ARGUE "rank-3, therefore incapable."** Three continuous dimensions can carry arbitrary
  precision. The coarseness evidence is Kang's **discretized (4×4-bin)** ID derivation and Cui's
  ordinal-only codes — they **support H2 without proving it**. Candidate mechanisms stay open:
  discretization, effective rank under the data distribution, SNR, ordinal-preserving many-to-one
  maps. (The old memory line asserted "destroyed … coarse rank-3 channel" as settled fact. It was
  neither.)
- Positioning: DepthCues + Ill-Posed by Design establish the endpoints; Kang 2601.12626 and
  Wang & Gao 2605.07148 constrain the middle. We localize where metric becomes inaccessible. NOT
  claiming "present but unverbalized" — Wang & Gao contradict that raw form. **⚠ And state DepthCues
  precisely: it shows depth-RELATED information is *recoverable* from encoders — NOT that "the metric
  signal exists" there.** Do not overclaim it; the image-identifiability gate is what licenses any
  "the encoder had it" claim.
- S1 design (the visible-metric stage): ordinal/ratio core (absolute secondary, prior-contaminated per ReVSI); factorial synthetic stimuli decorrelating depth × vertical position × size across **THREE regimes** (natural-congruent / **counterbalanced ← the primary claim lives here** / conflict); **five-functional-stage** probing grid (encoder → interface → early multimodal LM → object-conditioned language → answer/readout); probe-vs-verbalization with rank correlations + calibrated baseline + oracle-text; **anchor experiment (promoted to core — it IS the prompt-conditioned binding test)**; continuous metric-ID injection with dose-response + the full anti-logit-hack control battery; binding-layer LoRA vs brute-force SFT at matched data; validation via a **small, CLOSED, predeclared** external set (see dataset rules) + task-level oracle injection.
- **Models — MINIMAL PUBLISHABLE CORE, not 4–6 everywhere (revised 2026-07-15):** core = **2 architectures**, Qwen2.5-VL-7B (M-RoPE) + LLaVA-1.5-7B (classic CLIP), both already cached. One metric variable (egocentric depth), one qualitative positive control, five stages, one behavioral test, one intervention. **Expansion to 4–6 (InternVL/SigLIP, Gemma-3, Qwen2-VL) happens ONLY after the site-wise pattern stabilizes on two.** (Qwen2.5-VL-3B stays cached for S2 forward-compatibility but is **outside the core analysis matrix**; InternVL3-8B, used in M3.2, likewise.)
- Simple tasks for mechanism; complex benchmarks only as validation layer (composition-interp = future work).

## The research program — STAGES, not papers (reframed 2026-07-14; program frame added 2026-07-15)

### Program frame (adopted 2026-07-15 from the second external review)

- **Canonical program question** (replaces the old enumerating sentence): ***"How is object-specific
  spatial state represented, transferred, and causally used across multimodal model computations?"***
  — tested under four increasingly demanding information conditions: **visible / partially occluded /
  previously-visible-now-absent / hypothetical.**
- **Program hypothesis — DE-DIRECTIONALIZED.** The old "progressive loss" phrasing **prejudged the
  later stages**, which exist precisely to find out. Correct form: *"Spatial failure is not a unitary
  absence of geometry. It can arise because spatial information is weakly encoded, loses
  object-specific structure during multimodal transfer, remains represented but inaccessible to the
  relevant readout, or is not causally used. The program localizes these failure modes across
  visible, occluded, absent, and hypothetical spatial states, then tests whether interventions repair
  the responsible transition."* **S1 keeps its directional claim (H1/H2) as a STAGE hypothesis — it
  is not the program's.**
- **Evidential ladder (program-wide):** `representation ⊂ accessibility ⊂ task-relevant causal use`.
  "Spatial understanding = causal use" is **qualified to *task-relevant* causal use**: *the
  represented variable causally contributes to the corresponding output under controlled
  intervention.* ⚠ Failure of **one** answering pathway ≠ absence of understanding in every sense —
  that overclaim is exactly what S3 exists to test.
- **THE PROGRAM CUBE — the canonical organizing figure and the thesis structure.** Every stage
  occupies a **declared region** of:
  **Axis A — information condition** {visible / occluded / absent / hypothetical} ×
  **Axis B — computational transition** {encoding / interface / binding / readout / memory / generation} ×
  **Axis C — evidential level** {decodable / object-specific / accessible / causally used / repairable}.

### The stages

**This is ONE program.** It is organized as **dependency-gated stages**, not as papers or degree
chapters. **Publications are snapshots of whichever stages have defensible results when a deadline
passes; degree documents are bindings of completed stages.** The private CVPR 2027 target is
unchanged — it simply does not structure the science. ⚠ **Do not reintroduce "Paper 1 / Paper 2 /
Paper 3 / PhD direction" labels.**

**⚠ Maturity labels are MANDATORY wherever the stages are described** — they stop a long-horizon
agenda from being read as a queued experiment.

| Stage | Question | Unlock gate | Maturity / status |
|---|---|---|---|
| **S1 — Visible metric** | where metric fidelity becomes inaccessible to the language computation | M3 GO ✅ | **executable paper plan** — running; M4 is the real gate |
| **S1.5 — Occlusion & the amodal probe** | is the hidden part represented, object-specific, and bound? | **M4b** clears its validity gate (DR3) | **well-formed extension** — spec'd as milestone **M4.5** (plan §4) |
| **S2 — The method audit** | what do spatial "fixes" actually change? | S1's probes + baselines exist | **strong next-paper candidate** (M7) — stays ahead of S3 unless S1 yields a strong readout-specific result |
| **S3 — Other readouts (generation)** | does the generation pathway read the same spatial code? | an S1 finding (S3 tests it) | **comparative framework needing operational definitions** — parked |
| **S4 — The unseen** | what is maintained about what cannot currently be seen: occluded (by things), out-of-view (by framing), future (by time) | S1.5's amodal result | **long-horizon agenda — THREE candidate projects, not one experiment.** Do not build |

**Stage notes (the facts each stage was built on — keep these, they are verified):**
- **S1.5 (new 2026-07-15; the cue claim CORRECTED the same day — see below).**
  **H-occ:** occlusion is **primarily an ORDINAL VISIBILITY cue** — it identifies front–behind
  ordering more directly than continuous magnitude. **Over-reliance on it *could* support qualitative
  depth while leaving metric depth poorly represented.** That is the mechanistic form of the
  qualitative-vs-metric asymmetry, and it is testable inside the existing cue-decomposition design.
  (Landscape Tension **T2**, geometry vs visibility-aware state, made mechanistic.) Full spec:
  IMPLEMENTATION_PLAN **M4.5**.
  - 🔴 **RETRACTED, do not restate (it was in these docs for one day):** *"occlusion is the only
    **categorical** cue, carrying **zero metric content**, therefore their best cue **cannot** carry
    metric information."* **False as stated.** T-junctions, containment and support are **also**
    ordinal cues (so it is not the only one), and occlusion boundaries combined with known shapes and
    camera geometry **do** constrain metric depth (so "zero metric content" is wrong). The seductive
    part was the *deduction* — it made the program's central asymmetry look like it followed from a
    definition. It doesn't; it has to be measured. **Weaken to "primarily ordinal / over-reliance
    could…" and keep it a hypothesis.**
  - **The amodal question splits into THREE — do not conflate them:** **H1.5a object persistence**
    (an entity-level representation survives partial visibility) / **H1.5b amodal geometry** (hidden
    extent recoverable *beyond* visible-fragment features) / **H1.5c amodal binding** (available at
    object-referential tokens).
- **S2 — the spatial-method mechanistic audit (Kaho's idea).** How do existing spatial-enhancement
  methods (data-SFT, RL-tuned, inference-time scaffolds like scene-graph / depth-input / SoM) change
  internal behavior?
  - **⚠ The three-way label (representation / binding / prior) is REPLACED by a FIVE-DIMENSIONAL
    MECHANISM PROFILE — a vector per method, not a category** (the categories are **not mutually
    exclusive**, and forcing a method into one was going to manufacture false clarity):
    **ΔR_visual** (upstream representational gain) · **ΔR_bound** (object-specific transfer gain) ·
    **ΔB** (readout gain *conditional on matched internal decoding*) · **ΔP** (prior reliance, under
    blind / black-image / geometry-conflict controls) · **ΔC** (causal repair: mediation +
    specificity). **Report the vector.**
  - **⚠ CHECKPOINT COMPARABILITY CHECKLIST — run before ANY base-vs-finetune internal comparison:**
    tokenizer · image resolution · prompt/conversation template · preprocessing · transformers
    revision. A mismatch on any one of these produces a "mechanistic difference" that is a pure
    artifact — and this audit's entire signal is a *difference between checkpoints*.
  Ties to ReVSI's behavioral debunking (fine-tunes lose gains
  under corrected eval); scaffold analysis would mechanistically explain the C-niche convergent fact
  (verbalized cues barely help). Reuses ~90% of S1's infra. **Verified 2026-07-09:** 2511.11440
  deep-read — LM-layers × final-question-token probes on their own synthetic-SFT only, single toy
  task; comparative audit / site decomposition / scaffolds all NOT covered → the idea is open; cite
  and differentiate. Checkpoint audit set confirmed public with matched bases: SpaceR + ViLaSR (both
  on Qwen2.5-VL-7B-Instruct); SpatialLadder + SpaceQwen/SpaceOm + Spatial-MLLM (all on
  Qwen2.5-VL-3B-Instruct); VLM-3R vs LLaVA-Video-7B-Qwen2 optional second-architecture case. Skip
  Cambrian-S (no untouched base), SVQA-R1/SpatialVLM (no checkpoints).
  - **🔑 The behavioral mystery S2 exists to explain (from the landscape deck, added 2026-07-15):
    ISOLATED STRUCTURED PERCEPTION *HURTS*.** Four independent papers report it — EmbodiedVSR
    (detector / depth / graph alone each *degrade* performance), SpatiaLQA (segmentation alone
    67.4 → **50.3**; depth alone → **64.1**), NuScenes-SpatialQA, ISGR. Giving a VLM a *correct*
    structured spatial input makes it *worse*. That is a purely behavioral fact with no mechanism
    attached, and the audit's scaffold probing is exactly the instrument that can settle it: **does
    isolated structured input never reach the binding sites, or does it actively interfere there?**
    → cite these four in the audit's motivation, and carry **"isolated vs integrated scaffold"** as
    an audit condition axis (scene-graph-alone vs depth-alone vs integrated), mirroring their
    behavioral contrast.
- **S3 — generation.** Understanding↔generation gap in unified models: Janus-Pro (decoupled control),
  Emu3.5 (shared AR), BAGEL (hybrid). Parked (it is a *test of S1's prediction*, so it cannot run
  before S1 has one).
  - **⚠ Hypothesis SYMMETRIZED to branch-point localization (2026-07-15).** The old "generation
    suffers less from lexical binding loss" **prejudged the answer**. Correct form: *"If failure
    originates BEFORE the shared representation, both pathways fail on the same relations; if it
    originates DURING task-specific binding/readout, failures DISSOCIATE after the branch point."*
    The "generation suffers less" line survives only as a **derived corollary, conditional on S1's
    finding.**
  - **Probe transfer needs a three-level definition** (it was hand-waved as one thing): **decoding
    transfer** / **subspace alignment** / **causal direction transfer** (strongest, hardest).
  - The deck's application **C2** — T2I evaluation leans on VLM judges whose spatial verification is
    itself unproven — is **independent motivation** for the judge-circularity methodology spec'd here.
- **S4 — the unseen. A RESEARCH FAMILY of THREE BRANCHES — exactly ONE becomes the next project,
  selected by earlier results.** (Labeling it one experiment was the error; it is an agenda.)
  - **S4-A — hidden extent & the visibility graph.** ⚠ **State it NEUTRALLY — do not presuppose the
    negative:** *"models may encode scalar visibility attributes without maintaining relational
    occluder–occludee structure — we test whether pairwise structure is represented, bound, and
    used."* **Physically rendered occlusion CHAINS are primary**; inverted-depth composites are **one
    conflict regime only** (compositing-artifact confound; they break the exact-geometry guarantee).
  - **S4-B — persistent spatial memory:** out-of-view objects; multi-image guaranteed-evidence
    protocol (decay vs interference vs never-encoded vs readout — DISJOINT-3DQA precedent);
    KV-cache-as-memory probing. Video deferred (GPU cost).
  - **S4-C — hypothetical spatial state:** does the model internally represent predicted future
    positions before verbalizing? (CausalSpatial-level simulation; humans 84% vs GPT-5 54%.)
  - The umbrella **"representation of the unseen"** spans the deck's capability levels 4–6
    (visibility/permanence → dynamic state → counterfactual). It unlocks on S1.5's amodal result: if
    the hidden part of an object is not represented at all, there is nothing for a visibility graph
    to be made of.
- **Method harvest** (byproduct, not a goal): continuous causal mediation, probe-transfer measure,
  hypothetical-state probing.

### Framing adopted from the landscape deck (2026-07-15) — use this vocabulary in the proposal
- **Five definitions of "spatial understanding"**: behavioral / decodable / **causal use** /
  transfer / world-modeling. **Causal use is this program's operational definition** — the
  pre-existing commitment; the stages *operationalize* it (a probe that reads a quantity the model
  never uses is not understanding).
- **Capability levels**: perception → relations → geometry → visibility → dynamic state →
  counterfactual. This is the map of which stage addresses which level: **S1 = 1–3; S1.5 = the
  entry to 4; S4 = 4–6.**
- **Tensions**: **T1** representation vs interface → S2's core question. **T4** decodability vs
  causal use → S1's probe+injection pairing. **T2** geometry vs visibility-aware state → S1.5/S4.

## Dataset usage rules (set at M2 — SCIENTIFIC constraints, enforced in code; see plan §2.5)
- **Split/frame-budget is an experiment parameter, never a loader default.** MindCube defaults to `tinybench` (1,050 vs the full ~21k) and ReVSI to the **32-frame** budget — dev-speed conveniences only. Any *reported* result must set them explicitly in the experiment config. Both adapters now log the value (flagging when it's a default) and record it per item (`meta.split`, `meta.frame_budget`). **ReVSI's entire thesis is that conclusions change with the frame budget — the paper should report 2–3 budgets (16/32/64), not one.** A single-budget result is provisional.
- **DepthCues is PROBE-ONLY: it must never appear in a behavioral claim.** No task text exists in it; its "questions" are OURS and its "answers" are raw regression/binary labels. Scoring a model's verbalized accuracy on a question we invented measures nothing. `datasets/base.py` classifies every dataset (`NATIVE_QA` / `NATIVE_TASK` / `PROBE_ONLY`) and `assert_behavioral_safe()` raises on PROBE_ONLY — **call it at the top of every eval/scoring entrypoint (M5, M7).**
- **Important distinction the `meta.synthesized_question` flag is too blunt to make: What'sUp IS behavioral-safe.** Its *task* and answer key are native (choose the correct caption of four); only our prompt *wording* is synthesized — it is the qualitative positive control. DepthCues has no native task at all. Conflating the two would either wrongly bar What'sUp or wrongly admit DepthCues.
### 🔬 GROUND-TRUTH DATASET INSPECTION (2026-07-15) — the validation layer, corrected

**Standing rule, reinforced: a dataset enters an experiment only after ITEM-LEVEL inspection** (rows,
templates, per-category counts, answer-format quirks). **Paper descriptions AND our own adapter counts
are hypotheses.** Proof that this is not paranoia: What'sUp-B's 204 depth items and MindCube's total
unsuitability were **both invisible** from the dataset descriptions we had been working from.

- **🎁 What'sUp subset B contains 204 FRONT/BEHIND items — a qualitative-DEPTH control we already
  owned and never noticed.** *(Verified locally by full scan, 2026-07-15: subset B = 408 items,
  `left_of` 102 / `right_of` 102 / `in-front_of` **102** / `behind` **102**. Subset A = 412 items,
  `on` / `under` / `left_of` / `right_of`, **103 each**.)* B gives **categorical depth relations to
  contrast against metric depth**. ⚠ **Caveat to carry:** per Kang, front/behind may be answered via
  the **vertical proxy** (in tabletop scenes, front ≈ lower) — so B is proxy-confounded. Treat it as
  a **behavioral** control. *And note the proxy story is exactly what our S1 probes can test* — the
  confound is an experiment.
- **CV-Bench 3D: FITS, with three caveats.** Depth (600) is verbatim our ordinal primitive; Distance
  (600) is also ordinal (object-anchored). **ZERO absolute-metric items — never describe CV-Bench as
  metric validation.** Binary choices → 50% chance → **two-ordering protocol mandatory**.
  ⚠ **Source mix, measured in OUR copy (full scan, 2026-07-15):** `Omni3D_Hypersim` **400** /
  `Omni3D_SUNRGBD` **400** / `Omni3D_nuScenes` **400**, i.e. exactly 200 per (task × source) —
  **33.3% photorealistic SYNTHETIC** (Hypersim), 66.7% real-sensor. So: **report per-source, and do
  not call CV-Bench "real-image validation" without qualification.** (2D is COCO 805 / ADE20K 633.)
  ⚠ **The third source is nuScenes, NOT ARKitScenes** — ARKitScenes appears in *SpatialRGPT-Bench's*
  Omni3D slice, a different dataset. Do not conflate them.
- **ReVSI is the validation workhorse.** Its 13 question types tag cleanly onto primitives: 4
  absolute-metric (distance m / size cm / room m²), 2 ordinal (rel-distance closest/farthest, 4-way),
  4 egocentric-qualitative (perspective-taking), 2 counting, 1 other (route). Numeric types scored by
  **Mean Relative Accuracy** (0.5–0.95 thresholds). ⚠ **Type mix VARIES by frame config** (16f drops
  room-size + route-planning) — fix the config per analysis. ⚠ Add **video/cross-frame as a nuisance
  covariate**: every ReVSI item stacks cross-frame memory *on top of* the primitive.
- **🔴 MindCube: POOR FIT — REMOVED from the S1/M5 validation layer.** Every inspected item is
  multi-view perspective-taking under stated camera motion (rotation / among / around); **nothing
  reduces to a single-image primitive**, and its own eval excludes the `translation` setting.
  Re-scoped to a **cross-view integration contrast (S4-adjacent)**. **The adapter stays — nothing is
  wasted, and §2.5(a)'s split-is-a-parameter rule remains in force for any future MindCube use.**
- **CausalSpatial (arXiv **2601.13304** — ID added 2026-07-17; it was never in our docs): use the
  collision (n=826) and occlusion (n=189) slices ONLY** for primitive-predicts-failure analyses.
  Compatibility (n=99, size-ratio) and realworld (n=116) are too small for per-category stats.
  > 🔴 **CORRECTED 2026-07-17 — "physics" IS THE PAPER'S *TRAJECTORY* CATEGORY. Retraction visible.**
  > This read: *"physics (311) loads on **physics priors**, not spatial primitives — keep as a
  > **non-target control**."* **That judgment was made against a DIRECTORY NAME.** The ledger records
  > the paper's taxonomy as **Collision / Occlusion / Compatibility / TRAJECTORY**; `physics` and
  > `realworld` are **repo folder names that do not appear in the paper**. Verified by reading the
  > items (not inferred from the mapping): *"Based on the soccer ball's **trajectory** shown in the
  > image, will the ball go into the goal?"*, *"If the billiard ball moves in the direction of the
  > red arrow, will any ball go into the pocket and score?"* — **predicted future position from a
  > current spatial configuration.** That is **S4-C (hypothetical spatial state)** territory — the
  > very thing S4-C names CausalSpatial-level simulation for — **not** a prior-loaded throwaway.
  > **Consequence:** it stays OUT of the S1 consequence-level row (S1 is visible-metric), but it is
  > **re-scoped from "non-target control" to an S4-C candidate instrument**. ⚠ **THIRD TIME this
  > dataset's surface has misled us** — after the "unique" `id` (192 rows shared one string) and the
  > `not_sure` column (constant 'C', gold on 11 rows). §2.5(c) said *an upstream FIELD is a
  > hypothesis*; §2.5(e) generalized it to *datasets*. **This generalizes it again: a DIRECTORY
  > LISTING is not a taxonomy.** ⚠ Record their own admission: **sim scenes' "floor strip
  spacing encodes depth perspective"** — the depth cue is *artificially legible*, so caveat any
  cross-dataset comparison.
- **🆕 NEW DERIVED DATASET — ReVSI-1F (decided 2026-07-15).** ReVSI is video, and **cross-frame demand
  varies BY CATEGORY** — which confounds primitive-difficulty with memory-difficulty (and LLaVA-1.5
  is not a video model at all). Derivation: from `obj_visibility.json` *(verified present in our copy
  at `external/revsi/metadata/obj_visibility.json`)*, keep items where **all** `queried_object_ids`
  are co-visible in ≥1 frame; select the frame maximizing the **minimum** visible-pixel count across
  queried objects (tie-break earliest; seeded; rule in config). Emit `revsi_1f/` with original item
  id + chosen `frame_idx` + per-object visibility stats + primitive tag. ⚠ **Report per-category
  SURVIVAL RATES — the co-visibility filter drops categories unevenly, and that selection bias must
  be stated, not buried.** Validate with counts + contact sheet. Internal instrument (Apache-2.0
  permits); if ever released, ship **the script + index, not frames**.
- **✅ VALIDATION LAYER, FINAL (all single-image):** CV-Bench Depth/Distance (ordinal) + **What'sUp-B**
  (qualitative-depth control) + **ReVSI-1F** (ordinal + absolute, human-verified GT) +
  **SpatialRGPT-Bench distance slice** (absolute, sensor GT) + CausalSpatial collision/occlusion
  (consequence-level). **The list is CLOSED and predeclared** — not extensible mid-project. Full-video
  ReVSI at 2–3 budgets = a **labeled extension analysis**, not the core.
- **SpatialRGPT-Bench — ADD, WITH CAVEATS** (`a8cheng/SpatialRGPT-Bench`, HF, ungated, val only).
  ⚠ **NOT YET DOWNLOADED — every count below is from the advisor's item-level inspection and must be
  re-verified locally against the actual files before use** (rule 4: an upstream field is a
  hypothesis; this dataset has already burned us once in spirit — see CausalSpatial). Claimed: 1,406
  rows = 657 qualitative + 749 quantitative; GT from **Omni3D real 3D cuboid annotations**
  (SUNRGBD-dominant, ARKitScenes, nuScenes, KITTI, Hypersim) — **sensor/synthetic GT, not
  monocular-pseudo-GT**, so it shares no failure modes with the models we evaluate. But QA generation
  is **templated with no human-verification pass** → GT tier: *below* ReVSI's human re-annotation,
  *above* auto-pseudo-GT.
  - **Core signal = the ~375 inter-object DISTANCE items** (direct/horizontal/vertical) — absolute
    metric, **the type CV-Bench entirely lacks**. There is **no ratio type** and **no
    closer-to-camera type**.
  - ⚠ **Width/height items are PRIOR-CONTAMINATED:** blind GPT-4 (no image) scores **48–52% within
    ±25%**. Always report a **blind-LLM baseline** alongside; treat as secondary.
  - Evaluate generic VLMs with **SoM-drawn marks** (their own baseline protocol), **never text
    referral** (it breaks on same-class regions); bboxes + RLE masks ship in the JSON.
  - **Replace their GPT-4 judge** with deterministic number-extraction + configurable relative-error
    thresholds; report **±10% and AbsRel** alongside their lenient ±25%. The unit lottery
    (in/ft/cm/m) makes exact match meaningless.
  - ⚠ **License murky** (GitHub says Apache-2.0, HF card untagged, nuScenes/KITTI upstream
    non-commercial) → **internal eval use only**.

- **REPORT THE NOT-SURE RATE wherever an abstain option exists (added 2026-07-15, from the landscape deck's CausalSpatial read).** CausalSpatial's own scaling analysis finds **NSR collapses with model scale (18.77% → 0.10%) while accuracy stays flat** — i.e. *larger models become decisively wrong*, not more right. Accuracy alone hides that entirely. The adapter already carries `meta.not_sure_letter` (derived from the option TEXT, since the upstream column is a lie — see the second retro-audit), so NSR is free to compute: **report it as a metric alongside accuracy in the M5 validation layer.** Two further details from the same read, worth holding: **COW (their video-sim method) FAILS on its own occlusion task** — useful context for when our oracle-injection helps or doesn't; and **scale saturation** (Qwen3-VL 4B/8B/30B plateau at **43.5–45.8%** — 44.76/43.53/45.80; ⚠ corrected 2026-07-18 from "44–46", ledger L81) — a model-scale claim our per-primitive decomposition can actually speak to.

## M4 design constraints (inherited from M1 — read before building the conflict conditions)
- **⚠ `fixed_retinal_size` condition must NOT define "retinal size" as mask AREA.** A cube's mask area varies **±11% with pose/depth** (a nearer cube shows more of its faces; measured cube-as-far ∈ [139863, 171495] vs cube-as-near ∈ [148480, 182933] for `area×depth²`). So "equal retinal area" is not well-defined without also fixing pose. Two acceptable routes: **(a) define retinal size as mask HEIGHT** (`retinal_size_px`, which the M1 calibration equalises across shapes to `height×depth` ≈ 407 — pose-stable), or **(b) control pose explicitly (fixed yaw per object)** and only then use area. Do not silently mix the two.
- The `size_condition` factor owns **independent per-object size jitter**; the congruent condition deliberately gives both objects of a pair ONE shared multiplier (independent jitter is precisely how you invert the retinal cue on purpose).
- `cue_constants` in `configs/stimuli_v0_congruent.yaml` records the measured fill factors, `height×depth`, `area×depth²` (split by near/far role) and per-pairing required depth ratios — the numbers a conflict design needs to invert a cue by a *known* amount.
- Anything M4 adds (new primitive, new pose freedom, per-object size jitter) **invalidates the M1 calibration and the 1.158 area threshold** — recalibrate (`scripts/calibrate_sizes.py`) and re-derive the thresholds from worst-case constants.

### Forward constraints from S1.5 / M4.5 (added 2026-07-15) — M4 should not paint itself into a corner
M4.5 (occlusion) runs only AFTER **M4b** passes its VALIDITY gate (5 conditions, DR3 — the old
"transferred W&G bar" is retired as a go/no-go), but two of its needs are cheap
to accommodate now and expensive to retrofit:
- **The amodal mask is nearly free — take it.** The composite ID pass gives the *visible* mask
  (current pipeline); rendering each object **alone** in a solo ID pass gives the **amodal** mask
  for the cost of one extra tiny render per object. Schema additions M4.5 needs per object:
  `mask_amodal`, `occlusion_ratio` (= 1 − visible_area / amodal_area), `retinal_size_px_amodal`.
- **⚠ The congruence validators will FALSE-ALARM on occluded objects unless exempted.** The
  *visible* height/area of an occluded object is **not the calibrated quantity** — check retinal and
  area congruence on the **AMODAL** measurements instead. Write the exemption into
  `scripts/validate_stimuli.py` explicitly (as a recorded exemption, never a silent skip — CLAUDE.md
  rule 3), and note that adding the occlusion factor triggers the recalibration rule (M4 note (e))
  like any other new degree of freedom.
- **The leak ceiling extends too:** for occluded items the dumb-features baseline must include the
  **visible**-mask geometry AND `occlusion_ratio`. An amodal-decodability claim (H1.5b) has to beat a
  probe that only ever sees the visible fragment's geometry — otherwise "the model completes the
  object" is just "the fragment's shape told us".
- **🔴 BUT: do NOT plan on amodal-extent POOLING as the test (corrected 2026-07-15).** The first
  version of this note called "pool over the visible mask vs the amodal extent" a measurement detail
  that *is itself a finding*. It isn't — **pooling under the invisible mask mostly collects OCCLUDER
  and BACKGROUND tokens**, so a null there measures the occluder, not the object. **Do not assume
  hidden geometry is spatially stored under the hidden mask.** Test *implicit* representation instead:
  **visible-fragment pooled / occluder-region / object-name token / joint decoder conditioned on
  object identity.** Amodal-extent pooling survives only as a *labeled naive baseline*.

## 🚦 M3 — THE GO-GATE (2026-07-14). Full report: `reports/m3_reproduction.md`

### ✅ GATE DECISION: **GO** (advisor review, 2026-07-14). Phase 2 proceeds.
- **M3.1 is sufficient.** The binding-bottleneck design needs the mechanism to *exist and be
  steerable*, not a 64% swap rate. Log it and build.
- **Do NOT re-run Wang & Gao on v0.** The diagnosis is complete; v0 cannot support the
  measurement by construction. Re-running it would be theatre.
- **M3.2's pass bar TRANSFERS to M4 as an acceptance criterion:** *"the W&G pattern emerges —
  semantics ≫ metric, difficulty gradient present, measured ABOVE the leak ceiling."* If the
  decorrelated M4 battery still gives R² ≈ 0.99 everywhere after the leak controls, the stimuli
  are still broken and **M5 does not start**. When the gradient appears, the instrument is
  finally measuring models instead of itself. **M4 is now the real gate on Phase 2.**

**M3.1 (Kang) = PASS on the mechanism. M3.2 (Wang & Gao) = FAIL, and the cause is OUR STIMULI.**
Nothing was tuned to make either pass.

### M3.1 — the project's core premise SURVIVES
Reimplemented from the paper (their repo has no license). 640 two-object 4×4-grid scenes, COCO
cutouts (deviation: they used Objaverse), on LLaVA-1.5-7B + Qwen2.5-VL-7B.
- **The mirror-swap patching profile's KEY QUALITATIVE SIGNATURES reproduce on both models: image
  patches early → object-word tokens middle → text late.** This is Kang's central localization
  claim and the stage/layer pattern comes out crisply (LLaVA object-word peaks at 0.31–0.34 on
  L12–14; Qwen at L16). ⚠ **Wording corrected 2026-07-17 (DR3-r2 #10): this said "reproduces
  EXACTLY".** "Exact" is banned without a **preregistered similarity metric**, and we have none —
  we matched a *qualitative* stage/layer pattern by eye, not a quantified profile distance.
- **rank-3 R² = 0.87 (LLaVA) / 0.84 (Qwen)** vs the paper's ≥0.85. Spatial IDs really are a
  low-rank position code.
- **Steering is dramatically selective: 31.3% belief-swap vs 0.0% norm-matched noise** (Qwen, at
  the paper's α=5); dose-response is monotone and saturating (10→23→31→43% as α goes 1→10) while
  **noise never moves at any dose**.
- **What does NOT reproduce: the absolute swap rate** (19–31%, not their ≈64.5% median). Our noise
  floor is ~0%, not their 29.5%. **Report both; claim superiority of neither** — ours: +31.3 pts at
  α=5, +43.3 pts at peak; theirs: ≈64.5% vs 29.5% noise.
  > 🔴 **CORRECTED 2026-07-17 (DR3-r2 #10) — retraction visible.** This said the above-chance
  > influence **"matches or beats theirs"**. **Banned: cross-study effect comparisons are
  > DESCRIPTIVE ONLY** — noise construction, doses, selection and baseline belief distributions all
  > differ, so the two numbers are not commensurable and neither is "bigger". ⚠ **And the ban was
  > ALREADY RECORDED IN THIS FILE (see the DR3 addendum r2 above) while these lines still violated
  > it** — a ban is not self-enforcing.
  > ✅ **RESOLVED 2026-07-18 against the paper.** Kang's "above-chance influence" is a NAMED
  > statistic = **+43.6%** (§3 + Fig 2 caption), a CROSS-MODEL AVERAGE — **not** 64.4 − 29.5 = 34.9.
  > The ledger was right; this report constructed 34.9 by subtraction and mislabeled it "the paper's
  > own summary statistic" (rule 4's worse branch). Kang's number is +43.6; ours (+31.3 / +43.3) are
  > descriptive and NOT commensurable with it (DR3-r2 #10). Owed: PDF Fig-2-caption eyeball.
  **⚠ The obvious explanation is WRONG and we measured it.** "Our models are more certain, so
  noise can't flip them" does NOT survive: noise flips **0.0% in EVERY confidence bin** (0/23 at
  conf 0.90–0.99; 0/7 at 0.70–0.90), and spatial-ID flip rate is **uncorrelated with confidence**
  (r = +0.03). What *is* defensible: **our task produces almost no uncertain beliefs at all**
  (mean conf 0.973; only 11/150 below 0.9), and a noise control can only flip a belief near the
  boundary. That is a statement about **stimulus difficulty**, not model certainty. **The
  noise-floor gap remains UNEXPLAINED** — it does not threaten the mechanism, and we do not dress
  it up. Report the mechanism; do not claim the magnitudes.

### 🔴 M3.2 — THE FINDING THAT MATTERS: v0 CANNOT CARRY THE METRIC SCIENCE
Mask-pooled object tokens at LM layers of Qwen2.5-VL-7B + InternVL3-8B (their exact models) on our
v0 congruent set → **x R² = 0.997, z R² = 0.990 at EVERY layer**, shape/colour = 1.000, all
shuffled controls exactly at chance. Wang & Gao get **x = −0.09, z = +0.28**. We do not reproduce
"semantics ≫ metric" because **there is no difficulty gradient in our stimuli at all.**
**The probes are fine (controls at chance; token registration verified to 0.019 grid units). The
stimuli are the problem:**
1. **`x` has exactly 2 unique values (±0.7)** — it is a binary SIDE label, not a metric coordinate.
   And mask-pooling picks its tokens BY the object's image position, so "decode x" is answered by
   *which tokens were pooled*. R²=0.997 measures the pooling, not the model.
2. **`z` is 86% predictable from apparent size alone** (r=0.93 for `size_m/retinal_px` vs depth) —
   because "congruent" *means* every depth cue agrees. This is the exact monocular-depth shortcut
   Wang & Gao flag and discount.
3. Two primitives on a bare plane, fixed camera: too few degrees of freedom for "modest
   decodability" to even be expressible.
**→ M4 MUST: make `lateral_offset` continuous; treat `size_condition` (independent per-object size
jitter) as LOAD-BEARING (it is what breaks the size↔depth shortcut); add camera/background/
distractor variation.** See IMPLEMENTATION_PLAN §2.5(d).

### 🔴 THE POSITION LEAK — a THREAT TO THE CORE EXPERIMENT, not a probe caveat
**Mask-pooling from position-indexed visual tokens LEAKS POSITION BY CONSTRUCTION** — the pooled
vector averages tokens *at the object's image location*. **Selection and stimulus geometry already
contain most of the answer.**
> 🔴 **WORDING CORRECTED 2026-07-17 (DR3-r7 / annex A1) — the retraction stays visible.** This read
> **"The selection IS the answer."** That overstates what we measured. A1 decomposes the claim into
> THREE sources: (1) **stimulus confounding** (depth ↔ size/height/position in v0); (2) **positional
> representation** (activations genuinely encode 2D token location); (3) **selection-induced
> leakage** (the pooling operator itself creates the signal). **Our mask-geometry R² = 0.942 proves
> (1) and invalidates raw scores — it does NOT isolate (3).** Only after checklist item 4's
> isolation battery (random-i.i.d.-token control · position-only synthetic tokens · fixed-mask /
> different-depth matched pairs · content-location permutation · pooling ± positional components)
> may the stronger form be used. Until then the leak is a **CANDIDATE contribution** (DR3 §18).

**Measured leak ceiling on v0 (dumb features, NO activations, no model at all):**
| target | mask **geometry alone** | mask-pooled activations | model adds |
|---|---|---|---|
| x (lateral) | **R² = 0.942** | 0.997 | +0.055 |
| x from the mask centroid *u* **alone** (one number) | **R² = 0.943** | — | — |
| z (depth) | **R² = 0.972** | 0.990 | +0.018 |

**Why this is bigger than M3.2.** Mask-pooled *visual*-token probes inherit the leak;
*bound-text-token* probes do not (they are not selected by image position). So the probing grid's
central contrast — **visual stages high, text stages low** — **could be manufactured by the
measurement itself.** That directly threatens telling **Prediction 1** (metric survives in visual
tokens, becomes inaccessible at binding) from **Prediction 2** (metric was never there). **This is the single most
important thing M3 produced.**

**THREE controls are mandatory for Phase 2, not one:**
1. **Dumb-features leak ceiling** — every claim at every site must EXCEED a probe on mask geometry
   (+ shape/colour/cue values). Below the ceiling it is in the mask, not the representation.
2. **Fixed-grid STRIP probes are PROMOTED to the primary leak-free estimator** — strips are not
   selected by object position, so they cannot leak via selection. (We adopted Cui et al.'s strip
   variant as an "underestimation guard"; it is now load-bearing.) ⚠ **`strip_pool()` exists in
   `extract/pooling.py` but M3.2 cached mask-pooled features ONLY — M4's cache must produce both.**
3. **Camera-pose jitter at the SOURCE** — and this explains the W&G discrepancy cleanly: their
   scenes vary camera path, so camera-frame coords are not image positions. Our fixed camera makes
   x **identical** to image position (hence R²=0.997 measuring the pooling). Jitter kills the leak
   where it is created rather than correcting after the fact.
(+ Wang & Gao's cross-scene residualization of the semantic subspace, as an orthogonal fourth.)

### 🔑 STANDING METHODOLOGY: every probe ships a DUMB-FEATURES BASELINE (adopted 2026-07-14)
A shuffled-label control catches a probe fitting *noise*; it cannot catch a probe reading a
trivially available **non-representational** feature. Two findings this session passed every
shuffled-label control: the **55.1% shape-only** depth-role imbalance, and the **R²=0.942 mask-
geometry** leak. Same failure class — *a confound that survives every unit test and dies only
under an adversarial baseline*. So: for every (model, site, layer, target), also fit on
`{mask geometry} ∪ {shape, colour} ∪ {cue values}` and report **Δ = probe − dumb ceiling**.
Decodability only counts above the ceiling. Now in CLAUDE.md as verification rule 12.

### Bugs in OUR OWN M3 code, all caught by writing the invariant BEFORE trusting the number
- Scene generator systematically tied each object to a cell subset (TV=0.45) → the spatial-ID
  derivation would have been **circular**. Then the pairing dropped its unpairable tail
  non-uniformly → balance re-broken (TV=0.030). Now every object is in every cell exactly twice,
  TV = 0.000.
- **~1/4 of scenes put both objects in the SAME COLUMN**, where "left or right" has no ground truth
  — and the code confidently labelled them "right" (answer key skewed 253/640).
- **The belief readout was measuring nothing.** `" left"`/`" right"` share their FIRST TOKEN (the
  LLaMA whitespace token 29871), so both options got an identical logit and every belief came out
  exactly 0.5/0.5 — *even under zero-ablation*. Once fixed, LLaVA turned out to answer
  **"Left"/"Right"** (capitalised, ~all the mass) while lowercase sits at p≈2e-5: the readout was
  reading the far TAIL of the distribution. Now marginalised over surface forms, disjointness
  asserted. **Lesson: verify that an intervention MOVES the quantity you are measuring before you
  trust a null result** — a 0% steering effect looked like a real negative for an hour.

## SECOND retro-audit — all of M0/M1/M2 (2026-07-14, at the M3 gate). Full report: `reports/m0_m2_audit.md`

**Verdict: the DATA is clean; the CODE and the DOCS were not.** Every count, id, media file and
answer key in M1/M2 survives a full scan (all six adapters load exactly their source counts,
0 dropped, 0 duplicate ids, 0 missing files, 0 unscoreable MCQs; M1's geometry re-derives to
**0.0 error** over 1000 objects using an independently re-implemented camera; determinism
re-verified by byte-compare, and the documented residual claim is honest). But **six real code
bugs survived M2's closure, two of them producing wrong data**, and five documented constants
were false. All silent. All fixed this session, each with an invariant test.

- **CausalSpatial's `not_sure` column is a LIE** (HIGH): constant `'C'` for all 189 occlusion
  rows, but 54 of those have four *semantic* options and no abstain — and **on 11, C is the GOLD
  answer**. A scorer honouring the adapter's own contract would have discarded the correct
  answer. → now derived from the option TEXT. *Second* upstream field in this one dataset to be
  false (after the "unique" id). Hence the new plan §2.5(c): **an upstream field is a hypothesis.**
- **MindCube silently fell back to tinybench** (HIGH): `load(split="val")` returned 1,050
  tinybench items **stamped `meta.split="val"`** — the wrong population under the right label,
  inverting the very §2.5 rule the previous commit claimed to enforce. → unknown split raises;
  split is now settable from config (it wasn't, unlike ReVSI's budget).
- **ReVSI `frame_budget='all'` was dead** (`int('all')`): the parquet's `num_frames` is a budget
  LABEL, not a count. → clip length is now derived from the video. All four budgets load
  (16: 4,568 · 32: 6,158 · 64: 6,616 · all: 6,808).
- **`decode_frames` silently returned fewer frames than requested** → now raises.
- **What'sUp's gold answer is at position A in 100% of items** (the upstream convention is real —
  verified from the filename-encoded relation, 718/718). Served in that order, an A-biased model
  scores 100% and **the qualitative positive control passes for the wrong reason.** → options are
  now shuffled (seeded) with the true `answer_index` recorded.
- **The M0 config guard added by the FIRST retro-audit still had two holes**: `DATA_ROOT=""`
  (empty but set) resolved to the absolute path `/external`, and an unbraced `$VAR` stayed
  literal. The exact bug it was written to prevent, twice over. → checks the vars a config
  *references*, before expansion destroys the evidence.
- **The GPU guard's "foreign compute process" half was never implemented** — `ComputeApp` was
  declared with zero call sites, so the guard was memory-threshold-only and a colleague's job
  that hadn't yet allocated 1 GiB was invisible. → implemented; it immediately caught a real
  foreign process on GPU 1 during testing. **Load-bearing: M3 is the first GPU milestone.**
- **`seed_everything` set `PYTHONHASHSEED` after interpreter start** — a no-op. It looked seeded
  and wasn't. → removed, with `torch.use_deterministic_algorithms` added for M4.
- **`scripts/validate_stimuli.py` never opened a single mask or image** — it validated the JSON
  against itself, and its geometry check called the same function that *generated* the
  annotations. It would have reported ALL GREEN under a missing or overwritten PNG. → now opens
  every artefact, recomputes bbox/height/area from the pixels, checks id-uniqueness, image
  content-duplication, frame-clipping, occlusion, and **reports margins, not just pass/fail**.
- **Docs recorded `depthcues = 4,373`** — which is precisely the *pre-fix, broken* count
  (19,235 − 14,862, the occlusion subset that silently vanished). The code and tests already had
  19,235. **The docs preserved the bug.** Also: disk is 23 GB not 20 GB (loading CV-Bench and
  CausalSpatial *materialises* their parquet images, roughly doubling both), and the git remote
  is **not** deferred — `origin` exists and `main` is pushed.

### 🔑 THE STIMULUS CONFOUND (the finding that actually threatened the science)
**Category was never balanced against the near/far depth role.** v0 came out sphere-near 148 /
far 182, cube-near 168 / far 147, so the best **shape-only constant strategy scored 55.1%** on
the 345 mixed-category pairs ("the cube is closer" won 59.6% of cube-vs-sphere pairs). In the
very set built to *decorrelate semantics from geometry*: a language-only model gets 55% free on
"which is closer?", and **a depth probe can read depth off object IDENTITY** — which is exactly
the confound Wang & Gao residualize out, and M3.2's expected result ("semantics ≫ metric, z
modest") is precisely the number it would inflate.
→ **Fixed by construction:** category and colour are now drawn as *ordered* `(near, far)` pairs
and **balanced**, so "X nearer than Y" and "Y nearer than X" are equally frequent for every
{X,Y}. Re-rendered. Shape-only strategy: **55.1% → 50.2%** (χ² p=0.997). `balanced_on` was only
covering `closer_object` and `near_depth_bin`; the lesson generalises — **balance every factor
against the ROLE it could predict, not just its own marginal.**

## Retro-audit of M0/M1 (done 2026-07-14, after M2's bugs raised the question "was the earlier work also silently broken?") — YES, IT WAS
- **Answer: four more bugs, all silent.** This is why CLAUDE.md now carries a "How to verify work" section. Every bug across M0–M2 had the same shape: **the pipeline ran green while producing wrong data**.
- **M1 — the DETERMINISM hard rule was being violated the whole time.** Re-rendering from an identical (config, seed) produced *different images every run*. Three causes: (a) Blender embeds `Date`/`RenderTime` into PNG `tEXt` chunks; (b) **OIDN denoising is non-deterministic** (thread scheduling perturbs ~0.01% of pixels by 1 LSB); (c) **Cycles adaptive sampling is non-deterministic** (per-pixel stopping depends on thread timing). All three now default OFF (`denoise: false`, `adaptive_sampling: false`, metadata stamping disabled); `samples` raised to 128 to compensate for losing the denoiser. Render cost 1.2 → 2.5 s/img (500 imgs ≈ 22 min).
- **The determinism guarantee, stated precisely (do not overclaim):** annotations and masks are **byte-identical** across runs; images are byte-identical for ~19/20, with an irreducible residual of **~1 pixel in 5.2 M differing by 1/255** — float-accumulation order in multithreaded Cycles. Single-threaded rendering would remove it but costs 50 s/img (≈7 h for 500 images; untenable for M4's 5–10k). Scientifically nil (far below any model's preprocessing noise), but it means content-hash provenance on images is unreliable — hash the annotations, not the pixels.
- **M0 — config loader silently swallowed a missing env var.** `os.path.expandvars` leaves an unknown `${DATA_ROOT}` as literal text, so a forgotten `export` would have written the entire dataset into a directory named `${DATA_ROOT}` while every check still passed. `load_config` now raises on unresolved vars (`strict_env=True`).
- **M0 — CSV logger silently destroyed previous runs.** Reusing a run dir overwrote `metrics.csv` with no append and no warning; with M5's probing grid writing dozens of runs, a repeated `run_name` would have quietly eaten results. Now raises unless `tracking.overwrite: true`.
- Nothing else in M0/M1 was found broken: GPU guard, seeding, schema round-trips, geometry projection (<2 px), mask/annotation integrity all re-verified.

## Hard-won lessons (do not relearn)
- **🔴 A NULL IS ONLY AS TRUSTWORTHY AS THE PROOF THAT YOUR INSTRUMENT CAN REGISTER A POSITIVE.**
  **This is the most dangerous failure mode left in this project.** Unlike an inflated positive, a
  null *feels* like honest science — it looks like rigour, it gets written up as a finding, and
  nobody interrogates it. Phase 2 is *made of* nulls ("metric is not decodable at site X", "steering
  does not transfer", "the fine-tune did not improve binding"). Every one of them must be
  accompanied by a demonstration that the measurement MOVES when it must.
  - *(M3: steering reported a clean 0.0% belief-swap for an hour, with a plausible story attached.
    The steering was fine — the READOUT was dead. `" left"` and `" right"` share their first token
    under the LLaMA tokenizer, so both options scored an identical logit and every belief came out
    exactly 0.5/0.5 — **even under zero-ablation**. Fixing that revealed a SECOND bug: LLaVA answers
    "Left"/"Right" (capitalised, carrying ~all the mass) while the lowercase forms sit at p≈2e-5, so
    the readout was reading the far TAIL of the distribution. Two independent silent bugs, both
    producing a confident, publishable-looking null.)*
  - **The check that caught it: zero-ablate the thing you are intervening on.** If destroying it
    does not move your metric, your metric is not measuring it. Now CLAUDE.md rule 11.
- **🔴 AN ARGUMENT THAT MAKES YOUR FINDING FOLLOW FROM A DEFINITION IS A BUG, NOT AN INSIGHT**
  (CLAUDE.md **rule 13**, added 2026-07-15). Every other verification rule in this project validates
  an **output**. **None of them can catch a bad INFERENCE** — and on 2026-07-14 we shipped one into
  two docs and a commit.
  - *The claim:* "occlusion is the only **categorical** depth cue, it carries **ZERO metric
    content**, **therefore** if VLMs lean on it their best cue *cannot* carry metric information — so
    the qualitative-vs-metric asymmetry follows **in principle**." Nothing was mis-measured. The
    **deduction** was wrong (T-junctions/containment/support are also ordinal; occlusion boundaries +
    known shapes + camera geometry *do* constrain metric depth) — and, worse, it was **shaped to make
    the program's headline result true a priori.**
  - **Why it got through:** it felt like insight *because it was cheap*. An argument that derives your
    central finding from a definition is the most seductive object in a research project, and it is
    exactly the one nobody stress-tests, because agreeing with it feels like understanding.
  - **The smell test: if the claim would survive even if every experiment came back null, it is not an
    empirical claim.** A result you cannot lose is a result you cannot earn.
  - **The controls:** any deduction load-bearing for a headline claim gets an **adversarial domain
    read before it enters a doc** (this one died in a single external review pass). Prefer the weak
    measurable form ("over-reliance on an ordinal cue *could* leave metric depth poorly represented")
    over the strong deductive one ("therefore it *cannot*"). And **when a claim is retracted, leave
    the retraction visible** — a silent deletion lets the same elegant argument walk back in next
    session.
- **A shuffled-label control is NOT enough — every probe needs a DUMB-FEATURES CEILING** (CLAUDE.md
  rule 12). The shuffled control catches a probe fitting *noise*; it cannot catch a probe reading a
  trivially available **non-representational** feature. Both of this session's worst findings passed
  every shuffled-label control and died only under an adversarial baseline: the **55.1% shape-only**
  depth-role imbalance, and the **R²=0.942 mask-geometry** position leak (a *single* number — the
  mask centroid — gives x R²=0.943; even SHAPE is 99.2% readable from geometry). Run
  `scripts/leak_ceiling.py` on any new stimulus set; decodability counts only *above* the ceiling.
  Sanity property of the method: it correctly returns **chance for colour**, which a mask genuinely
  cannot encode.
- **⚖ THE EVALUATION LAW, IN TWO CLAUSES (refined 2026-07-15 — the one place external review
  overcorrected, resolved by synthesis; CLAUDE.md rule 7 updated to match).** The worst-case rule was
  learned from a real failure and is **not** being softened where it was earned — but it was being
  applied to a second class of quantity where it is wrong.
  - **(1) DETERMINISTIC, CONSTRUCTIBLE quantities** (rendered geometry, cue constants, calibration
    thresholds): **WORST CASE, always. Never means.** The extremes are *measured exactly*, and means
    were the *proven* failure — the area-congruence threshold from mean constants was 1.096 when the
    true worst case (splitting the constant by near/far role, since perspective differs) was
    **1.158**; the mean-based floor (1.12) passed validation while holding by a 0.6% margin, i.e. by
    luck. Any "safe threshold" for a rendered quantity comes from the extremes of its measured
    distribution.
  - **(2) SAMPLED / STATISTICAL quantities** (probe scores, benchmark accuracies, per-category rates):
    **no aggregate threshold without checking the weakest PRESPECIFIED stratum**, plus condition-wise
    uncertainty (CIs, quantiles, failure-rate distribution). ⚠ **One noisy item must NOT define a
    gate** unless that is scientifically required — a literal worst-case rule on noisy data gates on
    the unluckiest sample, which is not rigour, it is noise-chasing.
  - **The distinction is the whole point: worst-case is about a quantity you CONSTRUCTED and can
    bound; strata-plus-CIs is about a quantity you SAMPLED and can only estimate.** Do not apply
    either rule to the other class.
- **Verify a guarantee empirically AFTER applying it — passing ≠ guaranteed.** Both the 1.074 (no floor) and 1.12 (mean-based floor) sets reported `area_congruence 0/500`. The check passed both times; the *margin* (worst-case near/far area ratio) was 1.006 both times, which is what revealed the floor had done nothing. Always measure the margin, not just the pass/fail count — a green check on a contingent property tells you nothing about whether it will stay green under a different seed.
- **Never trust a rendered metric without an invariant check.** The colour-keyed mask silently bled into bounce-lit floor for the entire first version of the generator (see the ID-pass bug above); it was caught only by asking "is a sphere as tall as it is wide?" Validate the metric itself, not just that the pipeline ran.
- **Field velocity is extreme**: the literature analysis was materially revised twice in one day by newly-found papers (Kang et al., then Wang & Gao / Ill-Posed by Design — the latter two found only after Kaho pushed to search newer work). **Rule: every specific design claim gets a verification search before being asserted or written.** Biweekly citation watch on 2601.12626, 2605.07148, 2606.24335, 2411.17385 (offered as scheduled task; not yet set up).
- Superseded ideas (don't re-propose): qualitative-direction steering, ordering-probe amplification (Kang/Dual Mechanisms territory); behavioral-only cue decomposition for size (Ill-Posed); new static benchmarks; "present but unverbalized" as stated.
- Must-reads before design freeze: Attention in Space (2603.20662), Why Far Looks Up (2605.30161), full Ill-Posed §6.6 + limitations; Echo-Memory (2606.09803) before any memory work.
- **🔴 MUST-READ BEFORE ANY M5 PROBE CLAIM — "Mirage Probes" (arXiv 2606.13870, Jun 2026), "How Vision Models Fake Visual Understanding".** A probing-*validity* critique: it bears on **every probe claim this program makes**, S1 included, not just the occlusion work. Read it *before* the M5 numbers exist, not after a reviewer cites it at us. **PRIORITY.**
- **Verification-reads before the M4.5 (S1.5 / occlusion) design freeze** — per the standing rule that every specific design claim gets a search before it is asserted:
  - **Mirage Probes (2606.13870)** — as above; the amodal probe is a probe claim like any other.
  - **arXiv 2508.04567** — masked-object linear probes (>95%). Check whether their "masked" ≈ our occlusion; if it is, our amodal claim needs to differentiate hard.
  - **arXiv 2603.28333** (MLLM-guided amodal completion), **O-Bench** (occlusion benchmark — steal its inverted-depth and answer-frequency controls), **CAPTURe** (amodal counting; oracle decompositions), **SpatialMosaic** (occlusion-ratio data pipeline — engineering reference for computing `occlusion_ratio`).
  - **Search to re-run at freeze time:** "amodal representation probing VLM occluded object depth". Checked 2026-07-15: **geometric probing of physically occluded objects appears OPEN** — the adjacent work is classification probes on masked objects, and amodal *segmentation*. Re-verify; do not assert the gap from this note alone.
- **Watch list additions (2026-07-15):** **Structural Graph Probing** (population-level neuron-correlation topology; its open question *"would spatial IDs appear as hubs?"* is adjacent to S1) — verification-read, low priority. **R3D (2607.02921)** — added to watch alongside the SpatialRGPT-Bench decision. Plus O-Bench / CAPTURe / SpatialMosaic as S1.5–S4 references, and the landscape deck's 19-paper corpus merged into literature tracking.
- Kang reproduction is load-bearing (code: github.com/Raphoo/linear-mech-vlms).
- **Dual Mechanisms v2 (2603.22278v2, Jun 2026, deep-read 2026-07-09):** retitled to "spatial VARIABLE BINDING" — terminology collision risk; define our claim explicitly as the *vision→text-token binding step* (Kang-style), cite them as the ordinal counterpart. Our territory intact (no metric, no site decomposition, no text-token sites, no probe-vs-verbalization in v2). Adopted their standards into IMPLEMENTATION_PLAN M5: strip-level + object-pooled probing (their negative control shows background tokens carry signal), two-ordering MCQ protocol, random-direction nulls, Probe* reporting. Their code/data: spatial.baulab.info.

## Deliverables in outputs folder
- `lab_presentation_partA.pptx` (55 slides) + `lab_presentation_partB.pptx` (35 slides) +
  `CITATION_LEDGER.md` (built 2026-07-16): rookie-oriented lab seminar deck, English, 90+ min.
  Every number verified against paper full texts (ledger caught: W&G shape=1.00 is ACCURACY not
  R²; Kang steering 64.4/64.6 inconsistency; Cui null 9.6–13.1; CausalSpatial = arXiv 2601.13304,
  taxonomy Collision/Occlusion/Compatibility/Trajectory). Paper figures redrawn (sandbox can't
  fetch arXiv images) — original-figure URLs in slide citations/notes for manual paste-in.
  Part B slide B-5 regime sketches: swap for real M4a renders when available.
  **Revised at Design Revision 3 (same day):** all claim-level sentences re-scoped per the third
  external review (two-level variable, competing-hypotheses framing, no "dies/kills/adjudicates/
  first", validity-only Gate 2, candidate leak contribution). Decks now match the framing docs.
- `research_proposal_spatial_binding.md` — full proposal (advisor asks: plan endorsement + cluster access, model sign-off, human-baseline/ethics decision, external reader).
- `VSR_niches_critical_deep_read.md` — 15+ paper critical analysis with revision banners per niche.
- `research_proposal_spatial_binding.pptx` — 11-slide advisor deck (phase-framed, no conference dates).
- `docs/vsr_landscape_v8.pptx` — **companion document** (in-repo since 2026-07-15): Kaho's independent 19-paper landscape analysis, 2026-07-05, produced *before* this project's docs existed. Its contribution is folded in above; its 19-paper corpus joins the literature tracking. Keep it as the source for the five-definitions / capability-levels / tensions vocabulary.

## Current state / next step

- **🧭 PROGRAM REFRAMED (2026-07-14/15): stages, not papers — then DESIGN REVISION 2 (2026-07-15).**
  See "The research program" above. The work is S1 → S1.5 → S2 → S3 → S4, dependency-gated; papers and
  degree documents are *bindings* of whatever is defensible at a deadline. **M4.5 (= stage S1.5) now
  exists as a milestone** in IMPLEMENTATION_PLAN §4, between M4 and M5, **LOCKED until M4b passes
  its VALIDITY gate (reformulated at Design Revision 3 — 5 conditions; the old 'W&G pattern must
  emerge' bar is retired as a go/no-go)**. A validity failure blocks **both M4.5 and M5.** Do not start M4.5 unprompted.
- **⚠ WHAT DESIGN REVISION 2 CHANGED THAT YOU MUST NOT REVERT** (two external reviews + a
  ground-truth dataset inspection, all 2026-07-15). Each of these *overwrote something these docs
  asserted a day earlier* — if you find the old form somewhere, it is stale, not a second opinion:
  1. **"destroyed / lost" → "becomes unavailable or unusable"**, and the hypothesis splits into
     **H1** (localization) + **H2** (ordinal-preserved / magnitude-collapsed). **"Rank-3 therefore
     incapable" is banned.**
  2. **Occlusion is NOT "the only categorical cue with zero metric content"** — it is *primarily an
     ordinal visibility cue*. The deduction that made the program's asymmetry follow from a
     definition was **wrong**, and it was in these docs for a day.
  3. **Four probing sites → FIVE functional stages**, and the M0 §3 schema freeze is **superseded**:
     M4 must add the **answer/readout** hook + a per-architecture tensor-mapping table.
  4. **Three stimulus regimes**, and **the primary localization claim lives in the COUNTERBALANCED
     one** (plausible scenes, independent nuisance cues) — not in conflict, which is for
     cue-integration only. This is what preempts the OOD attack structurally.
  5. **The IMAGE-IDENTIFIABILITY GATE** is now an M4-pilot acceptance criterion: *exact renderer GT ≠
     pixel-inferable GT.* **If the image doesn't contain the evidence, no site can** — and "low
     everywhere" would be an instrument failure wearing a finding's clothes.
  6. **MindCube is OUT of the validation layer** (multi-view perspective-taking; no single-image
     primitive). **What'sUp-B is IN** — 204 front/behind items we already owned. **SpatialRGPT-Bench's
     distance slice is IN** (absolute metric, sensor GT — the type CV-Bench lacks). **ReVSI-1F** is a
     new derived single-frame instrument. The external list is now **CLOSED**.
  7. **Models: a 2-architecture minimal core** (Qwen2.5-VL-7B + LLaVA-1.5-7B), expanding to 4–6 only
     after the site-wise pattern stabilizes.
  8. **The leak ceiling's load-bearing number is the INCREMENTAL form**
     `Δ_repr|dumb = score(dumb ∪ repr) − score(dumb)`, and held-out splits must target the **claimed
     generalization** (object identities, camera poses, depth ranges, cue combinations) — **never only
     random image splits.**
- **As of 2026-07-14: M2 COMPLETE** (external dataset adapters), **re-audited and fixed at the M3 gate** (see the second retro-audit above). Six adapters under `src/sbind/datasets/` behind one interface `load(name, config) -> Iterable[Item]`; `scripts/{download_dataset,dataset_contact_sheet}.py`; `configs/datasets.yaml`. **23 GB** on disk under `$DATA_ROOT/external/` (7.8 TB free — non-issue; note CV-Bench and CausalSpatial *grow on first load*, since their images are extracted from parquet). **111 tests pass**; without `$DATA_ROOT` exported they SKIP rather than error (they used to error — the "green on a laptop" claim was false).
  **Item counts, verified by full scan against the source files:** cvbench 2,638 · revsi 6,158 (32-frame; 4,568/6,616/6,808 at 16/64/all) · **depthcues 19,235 (test)** · causalspatial 1,541 · mindcube 1,050 (tinybench; 21,154 test, 10,000 train) · whatsup 820.
  ⚠ **The old docs said `depthcues 4373` — that was the PRE-FIX broken count** (19,235 − 14,862, the occlusion subset that had silently vanished). The code and tests always had 19,235; only the docs preserved the bug. *Lesson: when you fix a bug, fix the number the docs recorded too — a stale doc re-introduces a corrected bug into the next session's assumptions.*
- **Interface decision (M2): `images` is a LIST, not a singular `image`.** ReVSI is video and MindCube is multi-view (4 images/item), so the plan's singular `image` field could not express half the benchmarks. Items also carry a stable origin-carrying `id` (`<dataset>/<original index>`) so eval results always join back to source items, and video items carry `video` + `frame_indices` with **lazy** PyAV decode (nothing materialised to disk).
- **Raw VSI-Bench skipped:** ReVSI ships its OWN `video.zip` + corrected annotations, so the raw benchmark would add 5.7 GB for nothing. (This was the open question at M2 planning; resolved by inspecting the hub file list.)
- **⚠ Per-dataset gotchas that cost time — do not relearn:**
  - **What'sUp is not on HF** (Google Drive). Its upstream loader file ALSO contains gdown ids for VG_Relation / VG_Attribution — **those are inherited ARO datasets, not What'sUp**. I initially grabbed those and downloaded 23,937 Visual Genome records instead of the 412 controlled photos. The correct ids are in the `Controlled_Images` class: subset **A = real photos**, subset **B = CLEVR renders**, each with its own json + tarball. Upstream convention (confirmed in their README): **the first caption option is always the correct one.**
  - **CausalSpatial has TWO schemas.** The four simulation subsets (collision/physics/compatibility/occlusion) have NO `options` column — the choices are inline in the question text ("A. Yes; B. No; C. Not Sure.") and `answer` is a LETTER, with a `not_sure` column naming an **abstain** option (a scorer must not count it as a wrong answer). `realworld` instead has an explicit `options` list and a TEXT answer. The adapter normalises both to `meta.{options,answer_letter,answer_text}`.
  - **DepthCues is NOT a VQA benchmark.** It ships raw probe targets (image + red/green mask pair + label), designed for linear probes on encoder features. There is no question text: ours are **synthesized** (`meta.synthesized_question`) and `answer` is just the label stringified — **consumers must use `meta.label`**. Each of the five subsets has a different schema and image directory. Its **Perspective** subset is annotations-only (the hub zip is literally empty); images live at the original vanishing-point project. Data terms: per-source, non-commercial research use (an `HLW_LICENSE.txt` ships with it); the CODE is MIT.
  - **CV-Bench's 3D `Depth` task is our primitive** ("which object is closer, the one in the red box or the blue box?") and the boxes are **drawn into the image**, so the annotation↔image join is visually verifiable — which is exactly what the contact-sheet eyeball check confirmed.
- **✅ M3 COMPLETE (2026-07-14) — GATE DECISION: GO.** See the M3 section at the top of this file.
  M3.1 PASS on the mechanism; M3.2 FAIL because v0 cannot measure models, only itself. **M3.2's bar
  transfers to M4.**
- **➡ NEXT: continue M4a to the actual acceptance gate — M4a pilot is implemented/analyzed, but M4a is
  NOT DONE. M4 IS THE REAL GATE ON PHASE 2. ⚠ M4 IS SPLIT INTO M4a + M4b; they are TWO SESSIONS,
  not one.** Do not start M4b unprompted. Before continuing, read
  IMPLEMENTATION_PLAN §2.5(d), the M4a/M4b specs, and `reports/m3_reproduction.md` §2.4.
  - **M4a = the stimulus battery.** Gate: **image-identifiability** — *do our images actually contain
    the evidence?* Needs **no VLM at all**, which is exactly why it runs first.
  - **M4b = the extraction pipeline.** Gate: **validity, 5 conditions (DR3)** — *does our instrument
    measure models, or itself?* (W&G gradient = benchmark comparison, not go/no-go.)
  - **Why split:** M4 had two deliverables and two gates, and run as one milestone **a failure at
    either gate could not be attributed** — "metric is not decodable" would be indistinguishable from
    "the images never contained it" *and* from "the extraction is mis-mapping tokens". With M4a
    cleared first, a failure at M4b is unambiguous.
  - The one-line version: **make the stimuli able to disagree with the mask, or Phase 2 measures the
    instrument.** **M4b** gates two downstream milestones: M5 (probing) *and* M4.5 (occlusion / S1.5).
  - ⚠ Read the "Forward constraints from S1.5 / M4.5" note above — **the solo-ID amodal pass belongs
    to M4a**, while the generator is open. It is nearly free now and expensive to retrofit.
- **Infrastructure now in place for M4/M5** (built at M3, designed to be extended not thrown away):
  `extract/vlm.py` (generic HF-VLM wrapper; locates decoder layers; one forward captures AND
  intervenes), `extract/pooling.py` (mask→token mapping per family, validated by centroid
  registration; `strip_pool()` present but **not yet cached** — M4 must), `probes/ridge.py` (probes
  with shuffled-label controls + exact fast dual/kernel solvers), `interventions/spatial_id.py`,
  `scripts/leak_ceiling.py`.
- **M3 prerequisites (done):** all six M2 bugs fixed + the stimulus confound removed and the set re-rendered; **COCO downloaded in full** (train2017 19.3 G + val2017 + annotations — the full set was chosen so Kang's spatial-ID auxiliary-loss result stays reproducible later); **four models cached** (`llava-hf/llava-1.5-7b-hf`, `Qwen/Qwen2.5-VL-7B-Instruct`, `OpenGVLab/InternVL3-8B-hf`, `OpenGVLab/InternVL3-8B` — 59 GB in `$HF_HOME`). ⚠ **Use the `-hf` InternVL conversion**: the original ships custom remote code that `AutoModelForImageTextToText` refuses.
  - **M3.1 = Kang reproduction** (LLaVA-1.5-7B + Qwen2.5-VL-7B). Targets from the paper: steering belief-swap **64.4–64.6% vs 29.5%** norm-matched noise; spatial IDs ≈ **rank-3** transform of the encoder's positional basis (R² ≥ 0.85); mirror-swap patching profile = image patches early, object-word tokens middle, text late.
  - **M3.2 = Wang & Gao pattern reproduction** on our v0 stimuli, on **Qwen2.5-VL-7B + InternVL3-8B** (their exact two models). Their numbers: x R² = **−0.09**, z R² = **+0.28**, pairwise-distance RSA ρ ≈ **0.01**, shape R² = **1.00**. Pass bar is *pattern* match: semantics ≫ metric; x ≈ chance; z modest.
  - COCO also unblocks What'sUp's deferred COCO/GQA-spatial subsets (TODO still open in the adapter).
  - ⚠ M3 front-loads a minimal `extract/` (HF-VLM wrapper + named hook sites + mask-pooling), which is formally M4's deliverable — build it to be EXTENDED by M4, not thrown away.

- **As of 2026-07-10: M1 COMPLETE** (rendering spike + minimal scene generator). **RENDERER DECISION = bpy (Blender 5.0 Python module), rendered headless with Cycles on CPU.** Rationale: `uv add bpy` pulled a 357 MB prebuilt wheel (`bpy==5.0.1`) — no compile, no system Blender, no Apptainer; imports + renders headless with no display; ~1.3 s/img CPU @512² so stimulus generation never touches the shared GPUs (Cycles OPTIX/CUDA also detect all 8 A6000s if ever needed). Apptainer/pyrender fallbacks NOT needed. Built `src/sbind/stimuli/{geometry,scene_spec,sampler,render_bpy}.py`, `scripts/{render_stimuli,contact_sheet}.py`, `configs/stimuli_v0_congruent.yaml`; rendered 500-image congruent-only set + contact-sheet PDF. 44 tests pass (28 M0 + 16 M1), incl. render-consistency: rendered mask centroids match K[R|t] projection <2 px.
- **numpy pinned <2.0 project-wide (M1 decision):** bpy requires numpy<2; verified torch 2.13 + the analysis stack all run fine under numpy 1.26.4 (scipy floor is exactly 1.26.4; torch↔numpy ABI interop + CUDA confirmed). So ALL extras (stimuli/analysis/extract) coexist in ONE env — the plan's anticipated "isolate stimuli env" is NOT needed. If a future dep hard-requires numpy≥2, revisit via uv conflicting-extras.
- **bpy 5.0 API notes (hard-won, don't relearn):** pixel filter moved to `scene.cycles.filter_width` + `scene.cycles.pixel_filter_type` (NOT `render.filter_width`); `read_factory_settings(use_empty=True)` yields `scene.world is None` (create a world before setting the sky); view transforms include 'Standard'/'Raw' (used 'Standard' for beauty, 'Raw' + 1-sample + near-zero BOX filter for the flat-emission ID pass so per-object masks are crisp & colour-management-immune). `World/Material.use_nodes` deprecation-warns (removal in Blender 6.0) — harmless now, revisit if we bump bpy.
- **v0 generator params (revised 2026-07-10 after review):** camera pulled in to (0,−2.5,1.4) and objects enlarged via the per-category calibration below → **retinal median 98 px** (p10 71, p90 147; 74% in the 60–120 band), up from ~30 px. Depth is now **continuous** (`depth_jitter: ±0.15` on both the near-bin centre and the gap, floored by `min_gap: 0.3`) → 500/500 unique depths, so ratio/absolute regression targets no longer collapse onto 5 discrete values. Sampler enforces **no identical pairs** (never same category AND colour) → 0/500, so "which object is closer?" is always answerable. Depth ratio far/near spans 1.08–1.58 (median 1.28).
- **🐛 ID-PASS BOUNCE BUG (found & fixed 2026-07-10 — the important lesson):** per-object masks come from a flat-emission ID render, but the ground kept its *diffuse* material and the sun stayed on, so an emissive red object **bounced red light onto the floor beneath it**; that lit floor fell inside the ID colour-match tolerance and the mask **bled downward**, silently inflating every `bbox_px` bottom and `retinal_size_px`. Caught only by a size-sweep sanity check: a sphere rendered 66 px WIDE but 103 px TALL — impossible. Fix: in the ID pass the ground also becomes **black emission**, all **lights are set to 0**, and **`max_bounces = 0`**. After the fix a sphere renders exactly as tall as it is wide and height is exactly linear in `size_m` (matches `f·size/depth` to ±1 px). **Lesson: never trust a colour-keyed mask without an invariant check — validate the metric itself (a sphere is as tall as it is wide), not just that the pipeline ran.** Any pre-fix retinal/bbox numbers in this doc's history are inflated and were superseded.
- **🔑 PRINCIPLE — "congruent means congruent BY CONSTRUCTION, for every measured cue" (decided 2026-07-10):** a congruent stimulus set must not rely on the seed's luck for any cue it records. Applied to the apparent-size cues: **you cannot equalise height and area simultaneously across shapes** (silhouettes fill their bboxes differently — cube 0.939, cylinder 0.908, sphere 0.784 — so equalising one leaves the other shape-dependent). We calibrate on HEIGHT (the quantity `retinal_size_px` records) and then make AREA structural via a **uniform minimum far/near depth ratio: `min_depth_ratio: 1.18`**. Both height- and area-congruence are now **hard validation checks** (any violation = construction bug).
- **⚠ METHOD LESSON — derive safety thresholds from WORST-CASE constants, never means.** First attempt set `min_depth_ratio: 1.12` from a *mean*-based area threshold of 1.096. It was wrong: a cube's area constant varies **±11% with pose/depth** (a nearer cube shows more of its faces), which the mean hides. Splitting the area constant by NEAR/FAR role gives the true requirement — **near=cylinder/far=cube needs 1.158**, near=sphere/far=cube 1.153 — so 1.12 left a 0.6% worst-case margin and area-congruence was *still* holding only by luck. Corrected to **1.18** (1.158 + ~2% headroom). Generalise: any "safe threshold" for a rendered quantity must be computed from the extremes of its measured distribution, not its mean.
- **Why a UNIFORM ratio floor, not per-pairing thresholds:** per-pairing limits would be less restrictive (near=cube/far=sphere needs no constraint at all, 0.947) but would make **shape predict the depth-ratio distribution** — a confound a probe could exploit. A uniform floor keeps depth ratio independent of the shape pairing, at the cost of some small-ratio (hard ordinal) cases.
- **Cue constants (measured, in `configs/stimuli_v0_congruent.yaml` → `cue_constants`) — reuse for M4 conflict designs**, which must invert a cue on purpose by a known amount: fill factors {cube .939, cyl .908, sphere .784}; `height×depth` {cube 409.3, cyl 410.3, sphere 405.3} (equalised → height congruence structural); `area×depth²` split by role, e.g. cube-as-far ∈ [139863, 171495] vs sphere-as-near ∈ [128932, 135860] (NOT equalised → needs the ratio floor); per-pairing required ratios recorded in the config.
- **Retinal-size calibration (2026-07-10):** a cube/cylinder subtend ~1.27× a sphere's pixel-height at equal `size_m` (silhouette reaches the diagonal, not the diameter), which let a FAR cube out-measure a NEAR sphere and invert the size cue. `scripts/calibrate_sizes.py` now measures each primitive's rendered mask height empirically (the *same* metric `retinal_size_px` records — not a closed form) and solves per-category `size_m` for a target pixel-height, iterating to convergence → **all three shapes render 90.0 px at the reference depth (spread 0.00 px)**. Calibrated sizes live in `configs/size_calibration.yaml` (cube 0.666, sphere 0.809, cylinder 0.666 m). **Consequence to remember: physical size is now a deterministic function of shape** — a probe could in principle read `size_m` off the category. The shared per-image `size_multipliers` factor adds physical-size variance to partially decorrelate this; revisit if an absolute-size probe looks suspiciously easy.
- **Centre vs surface depth (2026-07-10):** `depth_m` is the object CENTRE depth (the probes' regression target); `nearest_surface_m` = centre depth − half-extent along the viewing axis (what the bbox bottom and a human viewer actually track) — verbalized QA uses it. `pair_relations` carries both `ordinal_depth` (centre) and `ordinal_depth_surface` (surface). The sampler's `unambiguous_ordinal` constraint forces the two to agree by requiring the centre gap to exceed |h_near − h_far| + 0.15 m. **Measured: the two orderings disagree on 0/500 even with the constraint OFF** — with a pair-shared size multiplier, `|h_near − h_far|` only reflects *shape* (≤~0.05 m) while the min centre gap is 0.34 m. The constraint is a guard that currently binds on 0 images; it becomes load-bearing as soon as per-object size varies independently (M4's `size_condition`).
- **Congruent condition = pair-shared size multiplier.** Both objects of a pair scale by ONE `size_multiplier`; independent per-object size jitter would let physical size invert the retinal cue, which is precisely the M4 conflict manipulation — so it belongs to the `size_condition` factor, not to a congruent set. Noted in the generator config.
- **v0 acceptance state (2026-07-10, after the calibration + bounce fix): ALL CHECKS GREEN** via `scripts/validate_stimuli.py` — geometry 0/1000, corrected bbox-bottom rule 0/500, **retinal congruence 0/500 violations (100%)**, centre/surface ordinal agreement 0/500 disagreements, ratio 0/500, identical pairs 0/500, pair-shared size multiplier 0/500, masks 0/1000, surface sanity 0/1000. Answer key balanced 250/250 on BOTH centre and surface ordinals. Retinal median 98 px; depth ratio 1.07–1.61; 500/500 unique depths. (Historical note: an earlier "430/500 retinal congruence" figure was measured under the ID-pass bounce bug and is void.)
- **Geometry conventions frozen:** stored (K,R,t) are OpenCV-style (camera looks +Z, +X right, +Y down, pixel origin top-left); `depth_m` = CV-frame z; Blender camera built from the same look-at so projection matches render. `elevation_px` = v-pixel of the projected object centre; `retinal_size_px` = mask pixel-height; masks via flat-colour ID pass (≤6 objects palette).
- **As of 2026-07-10: M0 COMPLETE** (repo skeleton + infra utilities). On server plant-ai06. `uv run pytest` → 28 passed; `uv sync --extra analysis` and `--extra extract` both work; torch 2.13.0+cu130 sees all 8 GPUs; GPU guard verified live (aborts on really-occupied GPU 5 @43 GB, claims free GPU 6 + sets CUDA_VISIBLE_DEVICES). Built: `pyproject.toml` (extras extract/analysis/stimuli/dev), `src/sbind/{stimuli,datasets,extract,probes,interventions,eval,utils}` + `schemas.py`, utils (`gpu` guard, `seeding`, `config` loader w/ ${VAR} expansion, `io` jsonl, `logging` CSV/wandb tracker), §3 schema dataclasses w/ round-trip tests, `configs/example.yaml`. uv.lock committed.
- **Environment interviewed & frozen (see CLAUDE.md):** `$DATA_ROOT=/data3/hugin/vsr` (data3 = 7.8 T free), `$HF_HOME=/data3/hugin/hf_home` (kept off the 1.5 T-free shared /home). Tracking = CSV default, wandb via config — login cached & verified 2026-07-10, entity `chaso-hosei-university` (user `chaso`), now wired into configs/example.yaml + CLAUDE.md; flip to wandb at M4/M5. Git remote still deferred (local-only) — CLAUDE.md "server is never the only copy" rule remains UNMET; add origin when convenient.
- **⚠ HARDWARE CORRECTION:** the plan's prose says "A100", but plant-ai06 is **8× RTX A6000, 48 GB each** (first-come, no scheduler, multi-GPU OK). Compute all memory budgets against 48 GB, not 80. Other servers (4090/2080) out of scope.
- **Decisions made in M0:** flash-attn deferred but pre-wired via `[tool.uv] no-build-isolation-package` (models run on eager/sdpa; don't add until a checkpoint benefits). Stimuli extra holds only renderer-agnostic deps (trimesh/pillow/imageio) — bpy-vs-pyrender still decided at M1.1. Schemas are stdlib dataclasses (no pydantic dep in core) so the package imports on a bare laptop. requires-python `>=3.11,<3.13` (3.11 floor for bpy).
- Next: **M2 — external dataset adapters** (What'sUp/CV-Bench/ReVSI/MindCube/CausalSpatial/DepthCues; skip Kang/SynSpat3D/MetricVQA). **Do not start unprompted.**
- Dataset availability verified 2026-07-08: What'sUp/CV-Bench/VSI-Bench/ReVSI/MindCube/CausalSpatial/DepthCues all released & ungated. Kang data is script-generated (repo has NO license — reimplement, never copy; same for pittisl/vlm-latent-shaping). SynSpat3D dataset NOT released. **Metric VQA (Ill-Posed) NOT released despite abstract claim** — recheck monthly.
- Open decisions: ~~bpy vs Apptainer vs pyrender~~ RESOLVED (bpy, M1.1); ~~wandb vs CSV~~ RESOLVED (CSV default, wandb wired, M0); human baseline yes/no (ethics timing) still open; biweekly lit-watch scheduled task not yet created.

## 📌 2026-07-18 (sixth session) — M4a FREEZE finalization (§2 corrections + §3 decision gate)

Executing the "FREEZE the generator, then REVALIDATE" finalization prompt. Done so far:
- **§2 doc corrections (visible retractions), committed:** three-estimators "must agree" → need not
  agree in MAGNITUDE (contrastive-pair conditions away part of B1; agreement = qualitative story);
  "irreducible" applied to B1 → "strong interpretable monocular baseline" (PRESERVED, not beaten)
  corpus-wide; ruling-3d verbatim into PITCH + plan; 07-18→07-17 JST dates. (§2a already done.)
- **§3 DECISION GATE — B2→z RESOLVED as CLEAN (no sampler fix needed).** Measured the category↔role
  balance directly from `factorial_assignments` (instant): **exactly 0.500 per category at n=4000**
  (0.05 residual at n=60 = incomplete factorial); factor-level B2→depth R² ~0 at n=60 and n=800. The
  rendered pilot 0.26 was a **small-sample held-out-pose CV artifact**, NOT a design confound — the
  ordered-(near,far)-pair balancing (`balanced_on=cat_pair`) is correct. Guard test added
  (`test_category_role_balanced_at_scale`). ⚠ re-confirm the *rendered* B2→z at gate scale.
- **🔴 NEW FREEZE PREREQUISITE found by the §3 dry-run: PLACEMENT FAILS AT SCALE.** The j2 config
  (±0.3 m translation) can't place ~1 in ~110 factor combinations within 500 attempts (crashed at
  image 110/10k) → the 1k render would crash on ~9 images. Must fix in §4 before the render (raise
  attempts vs loosen the binding constraint — measure which). Added `raise_on_placement_failure=False`
  to `build_scene_specs` for audits (rendering keeps the raise default).
- **§4 freeze PROGRESS:** ✅ **placement-at-scale FIXED** — the ±0.3 m translation made near_depth_bin=0
  (0.2 m) un-placeable (~0.5% of combos), and MORE ATTEMPTS NEVER HELPED (500 vs 2000 identical); it is
  a framing limit. Dropped the closest bin → `near_depth_bins: [0.65, 1.1, 1.55, 2.0]` in all three
  frozen pilot configs; 100% placement at n=1200 verified; config-guard test added. Added
  `build_scene_specs(placement_failures=...)` audit hook. ✅ **factor persistence (§4.2)** —
  ground_color/sun_energy/sun_direction now written into `factors` (were sampled and discarded → DR3
  held-out-lighting/background splits are now constructible); regression test added.
  **STILL OWED in §4:** derive_cue_constants for 6 cats (⚠ script reads shared `size_multiplier`; the
  counterbalanced/conflict sets use `size_multiplier_near/far` — needs a schema update) + measure the
  1.85 floor's ratio-squeeze · nuisance TEXTURE families (do not exist — real work) + lighting/renderer-
  seed families · determinism byte-compare · TAG the freeze. **§5 revalidation** (~100–200 imgs, re-render
  frozen configs + all four audits + decorrelation matrix + validate + contact sheet). NOT started:
  contrastive pairs, 1k render.
  ⚠ **The existing pilot renders are now STALE** (old bins, no appearance factors) → §5 re-renders anyway.

### 📋 ADVISOR ADDENDUM (2026-07-18, session close) — BINDING for the next session, execute in this order

1. **`derive_cue_constants` SCHEMA.** Must support all three size schemas: **shared multiplier**
   (`size_multiplier`, v0/natural-congruent) · **per-object near/far multipliers**
   (`size_multiplier_near` / `_far`, counterbalanced + conflict) · **explicit per-object physical
   size**. **HARD-FAIL on missing fields — NO fallback to a shared value** (a silent fallback would
   divide the wrong multiplier out and corrupt the constant, which is the exact class of bug this
   project keeps catching). Ship a regression test per schema.
2. **FLOOR-SQUEEZE measurement** (the 1.85 natural-congruent floor vs its ratio-gate failure):
   report **available-vs-accepted ratio range, STRATIFIED by (near-category, far-category)
   pairing** — per pairing give the **minimum required ratio**, the **configured floor**, the
   **acceptance fraction**, **quantiles**, and the **retained worst-case dynamic range**.
3. **BIN-DROP CONSISTENCY SWEEP.** `near_depth_bins: [0.65, 1.10, 1.55, 2.00]` **everywhere**
   (all M4a configs, pilot AND full — currently only the three frozen pilots carry it). Re-check
   **ordinal margins, class balance, demonstrated dynamic range**. ⚠ **Per DR3 #14 the gate is
   VALIDITY-ONLY: "easier" is a REPORTED PROPERTY, never a failure.** Do not treat a rise in
   decodability from the bin drop as a gate failure.
4. **TEXTURES LATER** — scoped to **minimal procedural nuisance families**, **balanced and
   persisted** as factors (same treatment as ground_color/sun_energy). Not a full asset pipeline.
5. **FREEZE TAG DEAD LAST** — after every generative change lands and revalidation passes.
6. **§5 RUNS ONCE**, against **acceptance criteria + M4b numeric bounds written in advance as ONE
   PRE-REGISTERED BLOCK** (write the block, then run; no post-hoc threshold selection).
7. **B2→z is CLOSED at the ASSIGNMENT level.** ⚠ Note explicitly: **100% placement at n=1200 is
   what closes the REJECTION channel** — because assignments become realizations only if they place,
   a 100% placement rate means the balanced assignment IS the rendered distribution (no rejection
   re-weighting). The **rejection-bias audit remains the routine confirmation**, not the primary
   evidence.

## 📌 2026-07-17 (fifth session, advisor chat) — RULINGS on the three leak-ceiling decisions; project docs synced

The strengthening experiment (camera translation; see the leak-ceiling entry above and
`reports/leak_ceiling_v1.md`) left three advisor-level calls open. Ruled this session in the
advisor chat (Kaho present; delegated the calls to the standing recommendations). **These are
decisions, not suggestions — sync this entry back into the repo copy next code session, then act
on it.**

1. **Lateral target → WORLD-FRAME x (`pos_world[0]`).** Retarget `leak_ceiling.py`'s lateral
   target. Camera-frame x is coupled to image position by the projection identity
   `u ≈ f·X_cam/Z_cam + c_x`; no camera motion can decorrelate it, so as a leak target it is
   unfalsifiable — the same trap as v0's x. Keep cam-x as a reference ROW labeled "definitional
   identity (projection-coupled)", never as a leak target and never as a claim target. Camera-frame
   z REMAINS the primary depth variable — z is not projection-coupled the way x is (image position
   fixes X/Z, not Z), which is exactly why translation moved world-x and left z alone.
2. **Camera motion → ACCEPT ±0.3 m for now.** Freeze the j2 jitter config (pos_x ±0.3 m,
   pos_y ±0.2 m, yaw ±4°, pitch ±3°, height ±0.16 m) and re-render the pilots under the corrected
   placement wiring (mandatory regardless — `cf244b3`). Rationale: Aug 28 is the binding
   constraint; world-x ≈ 0.82 and falling, plus the two leak-immune estimators (strip probes,
   contrastive pairs) and Δ_repr|dumb, is defensible headroom. Wider FOV / pulled-back camera is
   DEFERRED, not rejected: revisit only if M4b's headroom proves insufficient — and if taken, it
   rides along with the §2.2(e) recalibration that blocker #9 owes anyway (derive_cue_constants
   was never re-run), so its marginal cost is lower than it looks. Record the placement-vs-
   decorrelation tension as a design finding in `m4a_battery.md`.
3. **z policy → SPLIT the ceiling.** Decompose the dumb-feature set into (a) position/selection
   features (centroid u/v, bbox position) and (b) monocular-cue features (elevation, retinal
   height/size, area) and report BOTH group ceilings per cell alongside the combined number.
   (b)'s ~0.85 is a strong interpretable monocular baseline [⚠ this initial ruling said
   "irreducible … the model must beat" — SUPERSEDED by the amendment below: B1 is PRESERVED, gate is
   Δ_R|B0,B2]; (a) is
   the fixable selection leak. This is the A1 leak-decomposition direction and keeps Δ_repr|dumb
   from conflating fixable with inherent. Headline wording per DR3-r4: "nuisance baseline +
   incremental-value analysis", not "ceiling".

- **Sequencing implied by the rulings:** retarget the tool (1) → re-render pilots at frozen j2
  jitter + fixed placement wiring (2) → re-run the split ceiling (3) → if world-x structured
  ceiling and the split-z position group land with defensible headroom, proceed toward the 1k
  render and the remaining blockers (contrastive pairs, textures/nuisance persistence, numeric
  M4b bounds, decorrelation matrix, cue-constant derivation).
- **Project docs synced this session (repo → claude.ai Project):** PROJECT_MEMORY (with this
  entry), IMPLEMENTATION_PLAN, PITCH, research proposal, M4a_SESSION_PROMPT, REVIEW_RESPONSE.
  Repo copies are current EXCEPT for this entry — sync it back.
- ⚠ **Date nit, flagged not fixed:** the strengthening entry and `reports/leak_ceiling_v1.md`
  are dated 2026-07-18; the work happened 2026-07-17 (JST). Left as-is in the repo record;
  correct opportunistically next code session so "most recent dated entry wins" stays reliable.

### 🔁 AMENDED same session — second-opinion arbitration refines rulings 1 & 3, extends 2 (ADOPTED)

A second advisor-level review of the strengthening results was arbitrated in the chat session.
**These amendments SUPERSEDE the rulings above where they differ.** Key upgrades:

1. **Camera-frame x → PROJECTION-COUPLED POSITIVE CONTROL (not a passive reference row).** Its
   EXPECTED result is HIGH R² (register the expected range, ~0.93 on current sets, so a feature
   regression is catchable): it verifies the dumb features capture image-plane location and that
   the tool reads a known-recoverable geometric quantity (rule-11 shape: a registered positive).
   Never call it a leak; a high nuisance score on a projection-defined target is the correct
   geometric relationship, not leakage.
   **World-frame x = SECONDARY scientific target, CONDITIONAL on passing its own Gate-1 raw-pixel
   identifiability under held-out camera pose.** Rationale — decorrelation and identifiability
   pull in OPPOSITE directions: the VLM never sees extrinsics, so world-x is recoverable only via
   scene cues about camera pose; the same translation that lowers the mask baseline can remove the
   evidence a pixel model (or human) needs. A low nuisance baseline on an unidentifiable target is
   a Gate-1 failure wearing a decorrelation success's clothes. If world-x fails its gate →
   descope; the depth core is unaffected. The leak tool reports both; **the gate reads world-x
   only. Primary scientific axis remains egocentric depth z.**
   **⚠ SPEC CORRECTION OWED (visible, not quiet):** M4a prompt §2.2(b) and m3_reproduction §2.4(3)
   say camera jitter makes "camera-frame coordinates no longer image positions" — now MEASURED
   FALSE for x (0.94→0.93 under strong jitter; the projection identity survives any camera
   motion). Correct both with a retraction note.
2. **±0.3 m confirmed; post-re-render battery extended with a REJECTION-SAMPLING BIAS CHECK.**
   The placement guard is itself a selection operator: under stronger jitter it accepts only
   special pose × object-position combinations and can quietly re-introduce the correlation the
   jitter removed. Measure it: log proposed vs accepted samples, compare the joint distributions.
   Full post-re-render battery: acceptance rate · world-x structured baseline · world-x pixel
   identifiability · depth identifiability · full decorrelation matrix · rejection-induced
   pose↔position correlation. FOV/pull-back ablation ONLY if (baseline still high ∧ pixel-model
   headroom exists ∧ world-x still matters to the core paper) — the paper is depth localization,
   not world-coordinate reconstruction.
3. **z baseline → THREE layers, not two: B0 selection (centroid, bbox location, token indices /
   region shape / count) · B1 monocular cues (retinal size, elevation, perspective values) · B2
   semantic priors (category, shape, colour, canonical size, template role); B3 = B0∪B1∪B2
   combined, DESCRIPTIVE only.** Report S(B0), S(B1), S(B2), S(R), S(Bi∪R) and the Δ variants.
   **PREREGISTERED PRIMARY CRITERION: Δ_R|B0,B2** (selection + priors controlled; legitimate
   visual evidence not treated as a competitor). Rationale: by data-processing, a genuine depth
   representation may BE the integration of retinal size + elevation — requiring Δ over the
   all-cues baseline demands information the image does not contain. Δ_R|B0,B1,B2 is reported
   descriptively, never as the sole gate (preregistering ONE primary Δ now is what prevents a
   forking-paths objection later). The combined ~0.85 is the descriptive cue ceiling — never
   called "leak".
4. **M4a success criterion, reworded:** not "all mask-based prediction collapses" but
   "selection- and prior-derived prediction is controlled, while verifiable monocular evidence is
   preserved so depth remains image-identifiable." Measurement semantics: *mask-derived features
   predicting a target highly → first determine whether it follows from (a) target-definition
   geometry [cam-x], (b) legitimate monocular evidence [z's B1], (c) stimulus confounding, or
   (d) selection-induced leakage — only (c) and (d) threaten the representation claim.*
5. **Scope notes kept from the arbitration:** none of this softens the v0 indictment (activations
   added +0.02–0.06 over the dumb baseline; that conclusion survives every reframing — the
   taxonomy changes what the ceiling MEANS, not what v0 showed). The primary claim is the
   stage-2-vs-stage-4 CONTRAST under the SAME baseline battery at both sites, so the taxonomy
   mainly protects the absolute premise, not the contrast. Existing pilot numbers = audit history,
   not gate evidence (re-render owed regardless via `cf244b3`).


### ✅ EXECUTION (2026-07-17, code session) — ruling 1 DONE (tool retarget + positive control + spec retractions)
- `leak_ceiling.py` retargeted: lateral gate = **world-frame x** (`pos_world[0]`); camera-frame x is
  now a **registered positive control** (`CAM_X_EXPECTED = (0.85, 0.98)`), reported and range-checked,
  never a leak/claim target. z stays primary. JSON gains a `positive_control` block.
- **Confirmed across sets** (positive control in band everywhere → tool validated, so a world-x drop
  is real): cam-x v0 0.942 / pilot 0.935 / j2 0.923. **world-x gate (held-out pose):** v0 0.94
  (fixed camera = un-decorrelatable) → pilot 0.915 → **j2 0.817** with ±0.3 m translation. z unmoved
  (~0.84–0.88), as predicted (depth not position-coupled). Report: `reports/leak_ceiling_v1.md`.
- **Refuted spec sentences retracted in place** (visible): M4a prompt §2.2(b) and
  `reports/m3_reproduction.md` §2.4(3) — "camera jitter makes camera-frame coordinates no longer
  image positions" is FALSE for x (cam-x 0.94→0.93 under strong jitter; projection identity survives).
- **✅ world-x IDENTIFIABILITY GATE DONE** (`scripts/worldx_identifiability.py`, held-out pose):
  measures MASK-ONLY (selection baseline) vs MASK+POSE (oracle upper bound); HEADROOM = pose
  contribution = the room where world-x needs pose inference (representation), not image position.
  **Verdict: pan-only pilot → DESCOPE (headroom +0.02, world-x ≈ image position); j2 +translation
  ±0.3 m → KEEP (identifiable 0.92, headroom +0.105).** So the ±0.3 m translation is precisely what
  converts world-x from a selection-determined quantity into a viable SECONDARY target — an
  empirical endorsement of ruling 2's ±0.3 m and ruling 1's keep-world-x-conditional logic. z
  unaffected (primary). ⚠ MASK+POSE uses true extrinsics (upper bound); realising it from scene cues
  is a gate-scale question. **cam-x stays the projection-coupled positive control (~0.93, in band).**
- **✅ RE-RENDER UNDER FIXED WIRING DONE (2026-07-18) — and the margin bug WAS consequential.**
  Isolated it: current code + seed, `target_bbox_margin_px` 14 vs 0 → **366 geometry mismatches**
  over 60 images (the 14 px margin feeds the target-OVERLAP check, so it rejects pairs packed tighter
  than 14 px). So the pre-fix pilots (`725ad42`, margins silently 0) were genuinely corrupted — their
  measurements are audit history. **j2 (counterbalanced primary) was rendered post-fix → its numbers
  stand.** Re-rendered conflict + natural-congruent with the frozen j2 jitter (ruling 2) + fixed
  margins; **both validate GREEN**, and **natural-congruent kept congruence under translation** (worst
  retinal 1.89 / area 1.38 — the 1.85 floor absorbs the camera motion) → **no §2.2(e) recalibration
  triggered.** cam-x positive control in band on all three regimes; world-x ~0.82, z ~0.78–0.89
  consistent. Old pan-only pilots superseded; `_j2` now redundant with the canonical counterbalanced.
  ⚠ **Latent reproducibility caveat found:** `_uniform_range` consumes an RNG draw even for a
  zero-width range, so adding zero-defaulted `pos_x_m`/`pos_y_m` shifts the whole random stream — old
  renders are not byte-reproducible by new code (determinism still holds WITHIN a code version). Left
  as-is (fixing reshuffles measured j2).
- **✅ REJECTION-SAMPLING BIAS AUDIT DONE (ruling 2, 2026-07-18).** `scripts/rejection_bias.py`
  (new `proposal_log` hook on `build_scene_specs` — logs every accepted+rejected placement, no
  render, no RNG change). Estimand = pose↔position correlation in the ACCEPTED (rendered) set; band
  = 2/√n. **Primary regime (j2, n=60, acceptance 0.31 = the MOST rejection pressure): CLEAN** — worst
  accepted |r|=0.126 << band 0.258, and the guard actually REDUCED correlation (proposed yaw×near-x
  −0.53 → accepted −0.11). So the guard is NOT re-introducing what the translation removed. conflict
  + natural-congruent (n=40) each show ONE borderline `camera_x_delta × far_x` ≈ 0.32 (~band 0.316),
  **present in the independent draws too → NOT guard-introduced → small-sample noise** (~1 false
  positive/regime expected across 18 tests). **Re-audit at gate scale** (500 imgs → band ~0.09;
  cheap, no render). Report: `reports/leak_ceiling_v1.md`.
- **✅ B0/B1/B2 BASELINE DECOMPOSITION DONE (ruling 3, 2026-07-18).** `scripts/baseline_decomposition.py`
  splits the dumb baseline into **B0 selection** (centroid u/v) · **B1 monocular** (area, bbox, retinal
  size, elevation) · **B2 semantic** (category/colour/size_m). **Preregistered M5 primary gate =
  Δ_R|B0,B2** (control selection + priors, PRESERVE B1 — a depth representation may BE monocular
  integration, so the model must NOT be required to beat B1); Δ over all cues is descriptive only.
  Wired into plan §M5 (three-numbers-per-cell) + M4a success criterion reworded ("control B0+B2,
  preserve B1", not "collapse everything"). **Battery reading (held-out camera pose):** z B1-dominated
  (0.79–0.88), B0 moderate (0.56–0.58); world-x B0-dominated (0.81–0.82), B1≈chance — empirically
  confirms *why* camera motion moves world-x and not z. ⚠ **REAL FINDING: B2→z = 0.26 (counterbalanced)
  / 0.45 (conflict) / −0.01 (natural-congruent)** — identity priors predict depth in the decorrelated
  regimes (conflict partly by design via size_condition; counterbalanced = residual coupling the gate
  controls but **MUST re-check at gate scale** — the 55.1% shape-only lesson). Watch item, not a blocker.
- **STILL OWED from the rulings:** ~~world-x raw-pixel identifiability gate~~ ✅ (KEEP ±0.3 m); ~~re-render under fixed wiring~~ ✅ (green); ~~rejection-sampling bias~~ ✅ (primary CLEAN); ~~B0/B1/B2 split~~ ✅ (Δ_R|B0,B2 preregistered). **ALL FOUR ADVISOR RULINGS EXECUTED.** Remaining M4a: descope world-x
  if it fails) · re-render pilots under fixed placement wiring `cf244b3` (ruling 2) · rejection-
  sampling bias check (ruling 2) · B0/B1/B2 z-baseline split + preregister Δ_R|B0,B2 (ruling 3) ·
  decorrelation matrix (#11) · `derive_cue_constants` (#9).


## 📌 2026-07-19 (seventh session) — M4a blocker #9 CLOSED: cue constants, floor squeeze, bin sweep

Executed advisor addendum items 1–3 only. Textures (#4), freeze tag (#5), §5 (#6), contrastive
pairs and the 1k render deliberately untouched. Full report: `reports/m4a_cue_constants.md`.

- **✅ SCHEMA FIX (addendum #1).** Size-schema handling moved into `src/sbind/stimuli/cue_constants.py`:
  **shared** (`size_multiplier`) · **per_object** (`size_multiplier_near/_far`) · **explicit**
  (object's own `size_m`). Resolved from `condition.size_schema`, else `condition.size_condition`
  via an exhaustive map **with NO default**. Missing field → `CueConstantSchemaError`. No fallback.
  - **The real safeguard is an invariant, not a prohibition:** every object must satisfy
    `size_norm × size_m_by_category[cat] == object.size_m`. That identity breaks the instant the
    wrong multiplier is divided out, so a silent cross-schema fallback is structurally impossible
    rather than merely forbidden.
  - **Rule-11 verified:** 15 of 17 tests in `tests/test_cue_constants.py` FAIL against a shim
    reproducing the old behaviour (the 2 that pass describe behaviour already correct for shared
    sets). The suppressed error is quantified: the naive fallback inflates a far object's height
    constant by **1.60×** with no exception.
  - **🐛 TWO MORE BUGS FOUND IN THE SAME CODE.** (a) Roles were assigned by `argmin` over ALL
    objects — distractors (world-y 2.7–4.4 m, own multiplier 0.45–0.7×) can be nearer than the far
    target, so on every image carrying one, roles were mislabelled and a distractor's silhouette was
    normalised by the target pair's multiplier. Roles now come from `target_object_indices` +
    `closer_object`, distractors excluded. (b) `--check-floor` would have flagged counterbalanced
    and conflict as violations; congruence is only a requirement where the design claims it.

- **✅ NEW INSTRUMENT: `scripts/measure_silhouettes.py`** — ID-pass-only sweep, **0.17 s/scene** vs
  ~3 s for a full render, because the constants depend on the flat-emission pass alone. **Validated
  exactly** against two rendered sets (0.000 px / 0 px max diff on 179 objects) — it is the same
  code path with the beauty pass removed, not an approximation. Writes to
  `$DATA_ROOT/measurements/`, never `stimuli/`.
  - **Why it was needed:** the pilots gave ~23 samples per (category, role) cell and a half-sample
    subset of the worst cell recovered only **48%** of the measured range. A worst case from
    unconverged extremes is a lower bound wearing a worst case's clothes. Swept 1200 scenes/regime
    → **198–202 per cell**.

- **✅ CONSTANTS COMMITTED (addendum #1).** `cue_constants` block in all 8 M4a configs, between
  generated sentinel comments (TEXT surgery, not a YAML round-trip — `safe_dump` would have deleted
  every hand-written freeze comment in the pilot configs). Provenance: source set, seed, render git
  hash, derivation version `2.0.0`, per-cell n. Binding worst-case ratio **1.7661 / 1.8671 / 1.8526**
  (natural-congruent / counterbalanced / conflict); **area binds in all three, always at
  near=bottle/far=cube**. Cube area constant spreads 25.9% as near vs a sphere's 4.6% — the v0
  means-are-unsafe lesson reproduces at six categories.
  - **DERIVE PER REGIME, NOT POOLED.** Pooling all three inflates natural-congruent's requirement to
    1.8640 (**+5.5%**): `C_a` is not perfectly size-invariant, so conflict's 1.12–1.30× far objects
    import pose conditions that regime never produces.
  - ⚠ **Extremes still not fully converged at n≈200** (worst cell's half-sample recovers 74.9%).
    Each threshold is a LOWER BOUND; keep margin and re-derive at §5 scale before the freeze tag.

- **🔴 ✅ FLOOR SQUEEZE (addendum #2) — VERDICT: the natural-congruent ratio failure IS an artifact,
  but NOT of the number 1.85.** Measured with `scripts/floor_squeeze.py` (same seed, real floor vs a
  non-binding 1.000001 that still consumes the jitter draw), n=1200, stratified by pairing:
  - Natural-congruent available ratio **1.046–1.474**; floor **1.85** — above the ENTIRE range.
    Acceptance fraction **0.000**; floor-determined fraction **1.000**. The accepted depth ratio is
    `1.85 × (1 + U(0, 0.08))` and nothing else.
  - **`r(ratio, depth_gap_bin)`: +0.906 without the floor → −0.017 with it.** The two regimes that
    PASS the gate are untouched (+0.905 → +0.905, floor 1.05, acceptance 1.000). So the ratio is
    statistically independent of every depth factor by construction, and **R² = −0.252 is exactly
    what regressing on independent noise under a held-out split produces.**
  - **1.85 is nevertheless justified:** derived requirement 1.7661, cleared by **+4.75%**, all 36
    pairings clear, and `validate_stimuli.py` enforces area congruence as a HARD check for this
    regime. The incompatibility is structural: **the minimum floor any congruent six-category design
    can use (1.766) already exceeds the maximum ratio the design produces (1.474).** Height
    calibration leaves area shape-dependent — a height-calibrated bottle's silhouette area is ~3×
    smaller than a cube's, and `sqrt(151754/48653) = 1.766`.
  - **DECISION OWED (not taken this session, belongs with the §5 re-render):** calibrate the
    congruent regime on AREA instead of height · per-pairing floors (v0's shape-predicts-ratio
    confound objection still stands) · restrict natural-congruent to an area-compatible category
    subset · widen the depth range (interacts with the placement limit that forced the bin drop).
    Meanwhile natural-congruent stays a CONTROL — but the reason is corrected: its ratio target is
    not "narrow and shortcut-heavy", it is **not a scene property at all**.

- **✅ BIN-DROP SWEEP (addendum #3) — five configs were stale AND the guard was scoped out.**
  `natural_congruent`, `counterbalanced`, `conflict`, `contrastive_pairs`, `counterbalanced_pilot`
  still carried the dropped 0.2 m bin, the pre-freeze pan-only jitter (no `pos_x_m`/`pos_y_m`) and
  `target_placement_attempts: 120`. All synced to the frozen generator block.
  - ⚠ **`test_frozen_m4a_configs_place_at_scale` passed the whole time** because it globbed only
    `*_pilot*` AND skipped configs without `pos_x_m` — the two filters between them excluded exactly
    the five configs that were wrong. **A guard whose scope excludes the un-migrated cases certifies
    nothing.** Widened to all M4a configs + new `test_all_m4a_configs_share_the_frozen_generator_block`;
    both verified to FAIL against the pre-fix configs.
  - **Dynamic range (validity-only per DR3 #14, "easier" is REPORTED not failed):** depth span
    2.44×→2.11× (counterbalanced) and 3.80×→3.22× (natural-congruent); ratio sd 0.100→0.089.
    Bought: placement failures 5–6/1200 → **0**, near_depth_bin balance 0.975–0.992 → **1.000**.
    Ordinal margin strictly positive everywhere (min 0.242 m conflict / 2.630 m natural-congruent,
    0 non-positive over 1200 each).
  - ⚠ **Could not reproduce the "max ratio ~3.1×, was ~10×" figure** from the session prompt.
    Measured max far/near ratio 1.474 available / 1.998 accepted; depth dynamic range 2.08–3.22×.
    The nearest 3.1 is conflict's shape+multiplier apparent-size requirement (3.0876). Flagged, not
    repeated.

- **STILL OWED in §4:** nuisance TEXTURE families (#4) + lighting/renderer-seed families ·
  determinism byte-compare · TAG the freeze (#5, dead last). **§5 revalidation** (#6, runs ONCE
  against a pre-registered block). NOT started: contrastive pairs, 1k render. New: the
  natural-congruent congruence-vs-ratio design decision, and re-deriving the constants at §5 scale.

### 📋 ADVISOR ARBITRATION (2026-07-19, same session) — 6 items, ALL EXECUTED

Adopted with one supersession of the advisor's earlier descope lean. Reports:
`reports/m4a_natural_congruent_decision.md`, `reports/m4a_cue_constants.md`.

1. **✅ NATURAL-CONGRUENT RULING: RESTRICTED CATEGORY PAIRINGS is the default** (per-pair derived
   requirements, hard area congruence KEPT). Rationale: the control regime's ratio arm is the
   **all-cues-agree reference for the conflict regime's fusion analysis** and must stay valid — a
   reference arm whose target is noise cannot anchor a fusion claim. **The earlier descope lean is
   SUPERSEDED**; full descope of the ratio target is last-resort only. Decision table built with
   numbers (n=1200 each), BEFORE textures, per the sequence:
   - **Largest symmetric feasible subset = {cube, cylinder, mug, sphere}**, uniform floor 1.1707 →
     retained ratio 1.171–1.458 (**1.25×** vs 1.08× now), clamped fraction 0.332, and
     **`r(ratio, depth_gap_bin)` restored −0.017 → +0.751**.
   - 🔴 **THE SAFEGUARD FIRED.** Per-pair floors over all six categories give
     **η²(pairing→ratio) = 0.823** with worst pairwise distribution overlap **0.000** (some pairings'
     ratio distributions entirely disjoint) — v0's shape-predicts-ratio confound at full strength.
     It also fails to solve the problem: 4 pairings (bottle-as-near) stay infeasible. **REFINEMENT
     to the ruling: restricted set + UNIFORM floor (η² = 0 by construction), not per-pair floors.**
   - **Primitives-only fallback NOT triggered** — category does not predict ratio under the default.
     It stays available and measures marginally better (1.28×, clamped 0.261) at the cost of a
     category.
   - ⚠ **Retained sets must be SYMMETRIC (C×C).** `cat_pair` balancing is what gives each category
     an exact 0.500 near/far split, and that split is what closes B2→z. An asymmetric retention
     would make bottle preferentially NEAR and reintroduce the confound the balancing exists to kill.
   - ⚠ **CROSS-REGIME ISSUE SURFACED BY THE TABLE:** a 4-category control is no longer
     category-matched to the 6-category conflict arm it anchors. **Recommendation: subset the
     ANALYSIS, not the stimuli** — keep 6 categories everywhere and restrict the fusion comparison
     to the 4 shared ones. Category set is a property of the analysis contrast, not the generator.
   - **Predicted to pass the ratio gate, NOT proven to** (passing regimes sit at r = +0.905 / 1.38×,
     R² = +0.803 / +0.420). A §5 measurement to be reported, not assumed.

2. **✅ POOLED = DIAGNOSTIC, per-regime = FORMAL RULE — ENFORCED IN CODE.** `--write-config` now
   refuses when >1 `--set` is pooled; a pooled run prints a never-the-operative-bound banner and
   emits a **regime-isolation** diagnostic. Measured (pooled bound 1.8672): natural-congruent own
   1.7661 → **+5.72%** (worst pairing near_bottle_far_cube, +0.1011); counterbalanced **+0.00%**;
   conflict **+0.79%**. The divergence is concentrated almost entirely in the congruent regime's
   bottle/cube pairing — the shared-multiplier envelope never produces the far-object sizes the
   per-object regimes do. The other two are close to exchangeable.

3. **✅ MANIFEST-BASED FROZEN-CONFIG GUARD** replaces the widened glob. `M4A_CONFIG_MANIFEST` lists
   the 8 stimulus configs explicitly; `test_m4a_config_manifest_matches_disk` asserts
   **discovered == expected BEFORE any field is compared**, then `test_frozen_generator_block_per_config`
   checks bins · jitter · **translation (called out separately)** · attempts, parametrised per config.
   **Why the widened glob was still not enough:** a glob only answers "is everything I found
   consistent?", which stays vacuously true if a config is DELETED or RENAMED — coverage silently
   drops to nothing and the suite stays green. Verified: manifest test FAILS when a config is
   removed from disk; both field tests FAIL against the pre-fix configs.

4. **✅ PROVENANCE AUDIT — all committed constants DO derive from post-role-fix runs.** Could not be
   settled from the recorded provenance: `derived_at_git_hash` said `ac36cd3-dirty` for every run and
   **`-dirty` erases exactly the distinction being asked about**; the three sweeps carry three
   different `git_patch_sha` because the tree changed between them. Settled by reproduction instead:
   - **640 of 3600 swept scenes carry a distractor**, so the role fix genuinely bites.
   - **Measurement reproduces BYTE-IDENTICALLY at HEAD** (natural-congruent sweep re-run at
     `da0b83c`, clean tree, md5 `0f4a68f4…` matches).
   - **Derivation reproduces BYTE-IDENTICALLY at HEAD** for all 7 per-regime configs.
   - **Nothing needed re-running.** Hardened so it is answerable without reproduction next time:
     every block now records **`derivation_source_sha`** (content hash of `cue_constants.py` +
     `derive_cue_constants.py`), which stays meaningful for runs from a working tree — most runs.

5. **✅ RETIRED-NUMBER PROVENANCE CORRECTED.** The "~3.1× / ~10×" figures were **advisor
   bin-endpoint arithmetic**: `2.0/0.65 = 3.0769` and `2.0/0.20 = 10.0` — ratios of the near
   object's **world-y offsets**, not depth ratios and not dynamic ranges (the camera sits at
   y = −2.5, so those offsets map to depths of ~2.95–4.95 m). Measured equivalents: depth dynamic
   range 3.80×→3.22× (natural-congruent), 2.44×→2.11× (counterbalanced); max far/near ratio
   1.538→1.474.
   🔴 **LABELING HAZARD, recorded deliberately:** `2.0/0.65 = 3.0769` sits **0.35%** from conflict's
   shape-plus-multiplier apparent-size requirement **3.0876** — two unrelated quantities in
   different units that both round to "~3.1". Last session flagged the near-collision as "the
   nearest 3.1 in this session's numbers", which is precisely the coincidence that would let a
   bin-endpoint number be re-attributed to an apparent-size derivation later. **Neither number may
   be quoted as "~3.1" without its unit and derivation.**

6. **✅ SEQUENCE RECORDED (binding):** decision table ✅ → **implement the chosen natural-congruent
   fix (freeze work)** → textures → determinism byte-compare → freeze tag → **§5 one-shot** against a
   pre-registered block. NEXT SESSION starts at "implement the chosen fix", which also requires
   re-deriving the constants over whichever envelope is selected.

### ⚖️ BINDING DISAMBIGUATION (2026-07-19) — natural-congruent GENERATES the 4-set; my "subset the analysis" recommendation RETRACTED

Advisor adopted the review (items 1–8 + acceptance checks A–D) with one binding disambiguation.
⚠ **The review's items 1–8 and checks A–D are NOT in the repo record** — they were not supplied in
text, so `docs/M4A_S5_CRITERIA.md` cannot be reconciled against them yet and says so explicitly.
**Supply them before the §5 block is ratified.**

- **🔴 RETRACTION (rule 13, left visible).** I recommended "subset the ANALYSIS, not the stimuli —
  keep 6 categories everywhere and restrict the fusion comparison to the 4 shared ones". **That was
  WRONG for natural-congruent.** It holds for counterbalanced/conflict, which do not clamp (measured
  clamped_fraction 0.001 / 0.000). Natural-congruent DOES clamp, because area congruence is a hard
  validator check there.
- **MEASURED CONFIRMATION of the ruling** (`reports/m4a_natural_congruent_options.json` →
  `six_category_control`): a six-category congruent set is realizable only by per-pairing floors,
  and then 4/36 pairings clamp on EVERY image →
  **always-clamped band 1.665–1.850 vs the rest 1.171–1.474, OVERLAP 0.000**;
  **η²(pairing → realized ratio) = 0.865**. The ratio reveals the pairing deterministically and
  category predicts depth — **the B15 confound rebuilt inside the reference arm, by the very
  mechanism just diagnosed**. Restricting the ANALYSIS does not undo it: the confound is in the
  REALIZED stimuli, and ordinal / absolute-depth / lateral targets are still read over all six.
- ⚠ **ONE CORRECTION TO THE RULING'S WORDING, on evidence.** It said "far-role category↔depth
  coupling". Measured, the coupling is **NEAR-role dominant**: η²(near → realized far depth) =
  **0.330** vs η²(far → far depth) = **0.051** (and η²(near → ratio) 0.578 vs far 0.079). Mechanism:
  bottle-as-NEAR has the smallest area constant (48,653 vs cube-as-far 151,754), forcing the far
  object deep; a far category is diluted because e.g. cube-as-far appears in both clamped and
  unclamped pairings. Conclusion unaffected; attribution corrected so the mechanism is not
  misremembered. §5 criteria bound BOTH roles rather than only the named one.
- **ADOPTED SETTLEMENT:** natural-congruent GENERATOR = symmetric **{cube, cylinder, mug, sphere}**
  at uniform floor **1.1707**. "Six categories everywhere" applies to counterbalanced/conflict.
  Matched-arm fusion contrast reads the shared four via a pre-registered eligibility manifest.
  Constants: natural-congruent re-derived over the 4-set envelope; counterbalanced/conflict over the
  full six.
- **✅ SYMMETRY PRINCIPLE recorded explicitly:** a pairing restriction must preserve exact
  per-category role balance — legal pairings form a symmetric set, because `cat_pair` balancing is
  what gives P(near|category) = 0.500 and that split is what closes B2→z.
- **✅ EXCLUSION TABLE published** as Appendix A of `reports/m4a_natural_congruent_decision.md`.
  Key reading: **a category is excluded for what it forces as NEAR, not as FAR** (bottle needs
  1.7661 as near, only 1.0579 as far). 5 categories is technically feasible but useless (floor
  1.4423 vs available max 1.4737 → **1.022× retained range**); 4 is the first usable point (1.259×);
  3 buys only 0.056× more at the cost of a category.
- **✅ ELIGIBILITY MANIFEST written BEFORE §5:** `configs/m4a_eligibility_manifest.yaml` — generated
  sets, analysis eligibility, and a **per-cell n check** (≥25 per pairing cell → conflict arm needs
  n ≥ 900, since it loses 55.6% of images to eligibility).
- **✅ REJECTED-DESIGN RECORD created:** `docs/REJECTED_DESIGNS.md` — R1 per-pair floors (η² 0.823,
  worst overlap 0.000, 4/36 still infeasible) and R2 six-category-with-analysis-restriction, each
  with the evidence that killed it and what would have to change to reconsider.
- **✅ METRIC RENAMED:** `clamped_fraction` is PRIMARY; `floor_determined_fraction` →
  `accepted_in_floor_band_fraction`, DESCRIPTIVE ONLY. The rename immediately earned itself: the
  conflict regime reads clamped **0.000** but accepted-in-band **0.058**, so the old name implied
  5.8% of images were floor-determined when zero were moved.
- **✅ PROVENANCE WORDING CORRECTED + STAMPS EXTENDED.** The claim is **"reproducible under corrected
  HEAD"**, never "historical runs proven corrected" — no stamp taken at the time can support the
  stronger claim. Now recorded as a `provenance_claim` field, plus `render_git_patch_sha` and
  `measurement_only`.
  - 🔑 **META-LESSON (second hardening of the SAME subsystem).** The 2026-07-17 fix added `-dirty`
    because `git_hash()` recorded a commit that could not have produced the output. Right, and
    insufficient: **`-dirty` flags impurity but destroys RESOLUTION** — it makes every dirty run of a
    commit indistinguishable, which is exactly the question asked two days later. **A stamp must
    answer the questions that will later be asked of it, not merely record that a hazard existed.**
    A flag that collapses distinctions forecloses the audit it appears to enable.
- **✅ §5 CRITERIA BLOCK DRAFTED** (`docs/M4A_S5_CRITERIA.md`, NOT ratified): eligibility + per-cell
  n · natural-congruent ratio-validity bounds proposed from measurement with margins
  (r ≥ +0.60, clamped ≤ 0.45, dyn ≥ 1.18×; weakest-stratum clamp burden ≤ 0.60) · realized-set band
  separation · category↔depth coupling · the four hard-fail invariants.
  ⚠ **Owed before ratification:** C-1's margins are off a SINGLE seed. Rule 7 clause 2 makes these
  sampled quantities → re-measure at ≥8 seeds and set each bound below the observed minimum, BEFORE
  the render.

**NEXT SESSION:** implement the 4-set fix + the machine-checked invariants (symmetry hard-fail;
P(near|c)=0.5 at assignment AND realized level), re-derive constants over the new envelopes
(natural-congruent 4-set @ 1.1707; counterbalanced/conflict full six), then textures.

### ✅ RULINGS FINAL (2026-07-19, session accepted) — design frozen as an IDENTIFICATION NECESSITY

All rulings final. Session accepted; the in-place retraction and R2 filing endorsed.

1. **Six-category natural-congruent stimuli are FORMALLY DEAD BY MEASUREMENT** — 4/36 pairings
   always-clamped, disjoint support 1.665–1.850 vs 1.171–1.474, η² = 0.865. **Final design, framed
   as an identification necessity rather than a preference:** natural-congruent generator =
   symmetric **{cube, cylinder, mug, sphere}** @ uniform floor **1.1707**; counterbalanced/conflict
   stay six-category. There is no version of the congruent regime that generates six categories and
   remains identifiable.
2. **THREE ANALYSIS TIERS** (manifest v2, `configs/m4a_eligibility_manifest.yaml`):
   **tier 1 control-specific** (4 cats, natural-congruent alone) · **tier 2 matched contrast**
   (shared 4, ⚠ **THREE regimes** — natural-congruent + counterbalanced + conflict, not two as I
   first wrote it) · **tier 3 full-arm** (6 cats, counterbalanced + conflict only; natural-congruent
   is absent by construction). Every analysis must declare its tier. Per-cell n ≥ 25 → n ≥ 400
   congruent arm, **n ≥ 900 each six-category arm** (they lose 55.6% of images to eligibility).
3. **NEAR-role correction ACCEPTED as the advisor's own error.** η²(near → far depth) 0.330 vs
   far 0.051; bottle-as-near's area constant is the mechanism. §5 bounds BOTH roles as implemented —
   bounding only the originally-named role would have left the actual mechanism ungated.
4. **§5 CHECK MAPPING RULED:** C-1→**A** (ratio validity) · C-2→**B** (band separation) · C-3→**C**
   (category↔depth/clamp coupling) · C-4→**D** (construction invariants) · C-5 = engineering gates.
   **Check C carries three BINDING HARD-FAILS:** any always-clamped pairing · disjoint
   clamped/unclamped support · category predicts clamp.
   - 🔴 **STILL NOT RECEIVED: the reviewer's A–D SPEC TEXT.** Said to be "pasted with this message"
     twice now; no spec text has arrived either time. The mapping and C's hard-fails are held (they
     are stated in the ruling itself), but A–D's CONTENTS in `docs/M4A_S5_CRITERIA.md` are MINE, not
     the reviewer's. **Reconciliation is a ratification blocker.** Where they differ, the reviewer's
     spec governs.
5. **🔒 THRESHOLD-SETTING PROTOCOL (binding, now recorded as a project rule):**
   **NEVER derive a threshold from the same results it gates.** Single-seed bounds rejected under
   rule 7 clause 2 — correctly; they are sampled quantities.
   - **Instrument: an ASSIGNMENT-LEVEL sweep, no rendering.** All gated quantities are **pre-pixel**
     (fixed once placement runs, and placement is in the sampler). ⚠ Note this includes the
     **realized** level: "realized" = PLACED, not rendered, so realized-level role balance is also
     measurable without the renderer.
   - **Pre-specified and COMMITTED BEFORE the sweep runs** (git history is the ordering proof):
     `SEEDS = [9001..9008]` (none reused elsewhere; config seed 410 reported as a reference but
     EXCLUDED from the bound, being the seed the design was developed against);
     **k = 2.0**; `bound = min − k·SD` (lower-bounded) / `max + k·SD` (upper-bounded), rounded
     outward to 2 dp; weakest-stratum clause applies the formula to the worst pairing per seed.
   - **Pre-committed spread rule:** any quantity whose seed-to-seed SD exceeds 25% of its mean is
     declared too unstable to gate and demoted to reported-only — recorded before the render. This
     blocks the opposite failure: a noisy quantity given a tight bound and failing for reasons
     unrelated to the design.
   - Sequence: state k ✅ (committed here) → run sweep → write pre-registration → **only then**
     render the frozen pilot.

**NEXT SESSION SCOPE (ruled):** implement the 4-set generator + machine-checked invariants
(symmetry hard-fail; P(near|c)=0.5 at assignment AND realized levels; eligibility manifest) + the
8-seed sweep + re-derive operative constants over the new envelopes (natural-congruent 4-set @
1.1707; counterbalanced/conflict full six). **Textures follow.**

### ✅ §5 CRITERIA RECONCILED (2026-07-19) — canonical A–D received; my draft's mapping was WRONG

Canonical text arrived as `docs/M4A_S5_CRITERIA-reviewer.md`, reconciled into
`docs/M4A_S5_CRITERIA.md` keeping the C-1…C-5 numbering and the pre-committed bound machinery.
**Reconciliation blocker CLEARED.**

⚠ **ONE criteria file only** (2026-07-19). `M4A_S5_CRITERIA-reviewer.md` was **removed** after
reconciliation so no second, divergable copy exists — `docs/M4A_S5_CRITERIA.md` is canonical and
governs. The verbatim ratified A–D text remains recoverable at
`git show 7a25800:docs/M4A_S5_CRITERIA-reviewer.md`. Before removal, **all 46 substantive items of
the canonical text were mechanically checked as present** in the surviving file (two initial
mismatches were line-wrapping artifacts, confirmed on whitespace-normalised re-check).

- 🔴 **MY DRAFT'S A–D CONTENTS WERE SUBSTANTIALLY WRONG — recorded, not quietly overwritten:**

  | | my draft | canonical | verdict |
  |---|---|---|---|
  | A | natural-congruent ratio validity | **Sampling semantics** | ~matches; canonical adds unclamped-subset measures, per-pairing counts, "instrument failure not model result" |
  | B | realized-set band separation | **Category and role independence** | **wrong subject** — symmetry + P(near\|c) live in B |
  | C | category↔depth coupling | **Clamp burden and support overlap** | partly wrong — my band-separation content belongs here |
  | D | construction invariants | **Pixel-level ratio identifiability** | **entirely wrong** — a check my draft did not contain at all |
  | C-5 | provenance/determinism | engineering gates **including all construction invariants** | my C-4 content belongs here |

  This is why guessing at a spec's contents and labelling it with the spec's letters is dangerous:
  the labels were right, the contents were mine, and D in particular was a whole missing check.
- 🔴 **RETRACTION (in place, rule 13):** I wrote last session that "realized = placed" means the
  8-seed sweep "covers more of **check D** than the scoping implies". TRUE under my draft's D
  (construction invariants); **FALSE under canonical D (pixel-level identifiability)**. The
  observation survives, its destination was wrong.
- **✅ BOUNDARY WRITTEN INTO THE CRITERIA FILE (ruling 1):** "realized = PLACED, not RENDERED". The
  assignment-level sweep establishes **Checks A, B, C** (including **placed-level P(near|c)**) and
  the C-5 construction invariants, with no renderer. It contributes **NOTHING to Check D**, which is
  **exclusively pixel-level on the frozen pilot**. `r(realized ratio, depth_gap_bin)` **does not
  satisfy Check D under any circumstances** — it validates generator semantics, not visual
  recoverability.
- **✅ CHECK C HAS FIVE BINDING HARD FAILURES, not the three in the ruling summary.** Adds:
  (4) clamping causes realized ratio to cease tracking the intended depth-gap design; (5) a weakest
  pre-specified stratum violates its bound even when the aggregate passes. All five transcribed.
- **✅ GATE-SCALE N DERIVED; "~1k" RETIRED (ruling 2).** From the pre-registered ≥25 images per
  pairing cell and 16 eligible pairings: natural-congruent **≥400** (eligible fraction 1.000),
  counterbalanced **≥900** and conflict **≥900** (eligible fraction 16/36 = 0.444) → **≥2 200
  total**. Neat property: at N=900 a six-category arm gives exactly 25/cell for BOTH the tier-3
  full-arm (900/36) and the tier-2 restricted contrast (900×0.444/16) — no arm is over- or
  under-provisioned. ⚠ **2 200 is a FLOOR:** Check D requires per-stratum counts for held-out
  lighting and texture families, which **do not exist yet**; N must be re-derived against the
  weakest held-out stratum once they do, and will only go up.
- **Bound cells remain EMPTY** (ruling 3). Single-seed numbers stay as labelled reference only.

**NEXT SESSION (unchanged, now unblocked):** 4-set generator + machine-checked invariants + the
8-seed sweep (bounds filled mechanically from the pre-committed formula) + constants re-derived over
the new envelopes. Textures follow.

## 📌 2026-07-20 (eighth session) — 4-set generator + invariants + 8-seed sweep; a NEW BLOCKER found

Scoped work executed. **Textures NOT started** (they follow, per the standing sequence).

- **✅ 4-SET GENERATOR IMPLEMENTED.** natural-congruent now generates `{cube, cylinder, mug, sphere}`
  at floor 1.1707; `size_m_by_category` trimmed to exactly those four (a leftover entry for a
  dropped category is dead config that looks set). n_images set from the DERIVED gate scale:
  natural-congruent 400, counterbalanced 900, conflict 900 (was 180/420/180 — stale, predating the
  criteria block).
- **✅ MACHINE-CHECKED INVARIANTS** (`tests/test_eligibility_invariants.py`, 15 tests):
  `sampler.assert_symmetric_pairings` hard-fails on an asymmetric support and is called inside
  `build_scene_specs` · placed-level P(near|c) = 0.5 ± 0.02 · manifest↔config agreement (categories,
  size map, floor) · natural-congruent-is-not-six · clamp-audit correctness. Manifest invariant
  statuses flipped `owed` → `IMPLEMENTED`.
- **✅ CLAMP AUDIT HOOK** — `build_scene_specs(ratio_log=...)` records per placed image the pre-floor
  ratio, the drawn floor and whether the floor moved it. **Necessary because check C's
  `clamped_fraction = #{r_raw < r_floor}/N` cannot be recovered after the fact**, and re-running with
  a non-binding floor changes placement rather than giving a paired comparison. Records only — no RNG
  draw, verified not to perturb output.
- **✅ 8-SEED SWEEP RUN** (`scripts/s5_assignment_sweep.py`, seeds 9001–9008, n=1200, sampler only).
  Bounds computed mechanically from the pre-committed formula.
  - **Check A (floor 1.1707):** r(ratio,gap) 0.728–0.753 → **bound ≥ 0.70**; retained range
    1.252–1.270 → **≥ 1.23**; weakest-stratum r 0.638–0.709 → **≥ 0.58**. Reference seed 410 inside
    the envelope (not anomalous).
  - **Check C:** clamped 0.484–0.524 → **≤ 0.55**; max stratum 0.587–0.640 → **≤ 0.69**. **All five
    binding hard failures PASS**: 0/16 always-clamped, clamped/unclamped support overlap 0.338,
    category does not predict clamp (η² ≤ 0.021), ratio still tracks the gap.
  - **Placed-level P(near|c) = 0.5000 EXACTLY on every seed, all four categories** — placement
    introduces no role bias whatsoever.
- 🔴 **`clamped_fraction` CORRECTED: ~0.50, not 0.332.** The 0.332 was a DIFFERENT ESTIMAND —
  `floor_squeeze.py` compared the **base** floor 1.1707 against ratios from a **separate**
  non-binding-floor run. Canonical check C uses the **per-image drawn (jittered)** floor
  [1.1707, 1.2642], mean 1.2181, paired within one run. Measured both ways on identical data:
  **0.4842 canonical vs 0.3283 base-floor proxy**; the 0.156 gap is fully accounted for by the
  jitter. Corrected in the criteria file.
- ⚠ **THE SPREAD RULE IS DEFECTIVE FOR NEAR-ZERO QUANTITIES — applied anyway, not amended.** All
  seven check-B quantities were DEMOTED to reported-only: they are bounded near zero by intent
  (η² ≈ 0.01–0.02 against a 0.10 bound), so a trivial absolute spread of 0.005 yields CV > 0.25. The
  reductio: placed-level role imbalance is **exactly 0.0000 on all 8 seeds** — the best attainable
  value — and CV = ∞ demotes it. **Not amended, deliberately**: rewriting a pre-committed rule after
  seeing its output is the forking path the protocol exists to prevent. **Proposed for ratification:**
  exempt a quantity when its 8-seed maximum is already far inside its bound absolutely
  (e.g. `max_s q_s < 0.25 × bound`). Until then check B is reported-only and its structural hard
  failures remain the operative gate.
- 🔴🔴 **NEW BLOCKER — THE PRE-REGISTERED FLOOR 1.1707 DOES NOT CLEAR ITS OWN RE-DERIVED
  REQUIREMENT.** Re-deriving over natural-congruent's **own 4-set envelope** gives **1.1761**; the
  floor is short by **0.46%**, and area congruence is a HARD validator check for this regime.
  - **Cause:** 1.1707 came from constants measured on the **six-category** envelope, which this
    regime no longer generates. **The constants depend on the floor** (via the realized depth
    distribution), so a floor derived at one floor is not self-consistent at another — a fixed-point
    problem that was not visible until the generator actually changed.
  - **Fixed point measured:** at floor **1.2320** the requirement re-measures to **1.1601**,
    headroom **+6.20%**. Converges DOWNWARD — a higher floor puts far objects deeper, where
    perspective is less extreme and area constants less variable.
  - **Cost, 8 seeds, 1.1707 → 1.2320:** r(ratio,gap) 0.73–0.75 → **0.47–0.53**; weakest-stratum r
    0.64–0.71 → **0.18–0.41**; clamped 0.48–0.52 → **0.69–0.72**; retained range 1.25 → 1.19.
  - **NOT APPLIED.** Changing a pre-registered value is a ratification decision. Configs still carry
    1.1707; the violation is recorded as a **`strict=True` xfail** which FAILS the moment the floor
    is raised, forcing the marker's removal instead of leaving a stale exemption.
  - **The filled bounds are PROVISIONAL** — computed at 1.1707. If 1.2320 is ratified the sweep
    re-runs and bounds recompute from the same formula.

**OWED / NEXT:** ratify the floor (and with it, re-run the sweep + re-fill bounds) · ratify or reject
the spread-rule amendment · then textures → determinism → freeze tag → §5 one-shot.

### ⚖️ 2026-07-20 — three rulings adopted; §5 protocol v2 PRE-COMMITTED before execution

Executed as **two commits by design**: `f0589b9` pre-commits the protocol with nothing run, then a
second commit carries the results. Git history is the ordering proof that r* was not chosen after
seeing which value looked good.

1. **FLOOR: 1.2320 REJECTED; minimal self-consistent floor via pre-committed root search.**
   Rejection reason recorded: 1.2320 is the fixed point *plus a margin policy inherited from the
   now-dead six-category envelope*, and it demonstrably destroys sampling semantics
   (r 0.73→0.50, weakest stratum 0.64→**0.18**, clamp 0.48→0.72).
   - **Pre-committed** (`scripts/floor_root_search.py`): calibration seeds 8001–8002, n=1200 each,
     **worst case over seeds** (constructed quantity, rule 7 clause 1) · grid 1.165–1.200 step
     0.005 · r* = smallest grid point with **F ≥ R(F)**, tolerance one step ·
     **r_op = r\* + 0.005, rounded UP to 3 dp**. Interpolation predicts r* ≈ 1.175 → candidate ≈1.181.
   - **Why a root search at all:** the requirement is a FUNCTION of the floor, R = R(F), falling as
     F rises (a higher floor puts far objects deeper, where perspective is less extreme). Validity
     is the fixed-point condition F ≥ R(F), never a one-shot derivation.
   - **ACCEPTANCE IS JOINT:** (a) area validity F ≥ R(F) re-derived at r_op itself AND (b) sampling
     validity against the check A–C design-selection bounds. Expected to be a genuine test —
     interpolation puts weakest-stratum r and clamp both near their bounds.
   - **PRE-REGISTERED ESCAPE HATCH, usable only on joint failure:** evaluate extending the **FAR
     depth-bin envelope** (deeper bins place easily; raises the ratio ceiling, relaxing the squeeze
     *from above* instead of pushing the floor up into the distribution) before declaring the 4-set
     infeasible. ⚠ Battery-wide, and it **re-opens the z-identifiability checks**. Only if that also
     fails is the 4-set dead.
2. **CLAMP ESTIMAND FIXED AND RENAMED AT BOTH SITES** so the names carry the meaning:
   **`clamped_fraction_drawn_floor`** (per-image DRAWN jittered floor, ≈0.484) is the **gating**
   quantity; **`below_base_floor_fraction`** (≈0.328) is a **diagnostic** and **must never again be
   called "clamped"**. Headroom vs the ≤0.55 bound is only ~0.07 → **re-verify at the new floor**.
3. **NEAR-ZERO SPREAD EXEMPTION RATIFIED AS AMENDED (protocol v2.0):** the CV spread rule is
   inapplicable when **max_s q_s ≤ 0.25 × criterion bound**, restricted to **natural-zero,
   lower-is-better** quantities (η², imbalances, clamp-predictability) — **never** correlations or
   retained range, which are far from zero so relative spread is meaningful there. Each quantity
   carries an explicit `natural_zero` flag and its criterion bound so the exemption cannot silently
   widen. **Ratified on FRESH seeds 9009–9016**: a rule amended in response to a result may not be
   validated on that same result.

- **🔒 SEED ROLES ARE NOW FORMAL AND DISJOINT** (same discipline as M5's direction protocol).
  **calibration 8001–8008** (which floor? — selects) · **bound-setting 9009–9016** (how far may it
  drift? — sets operative bounds) · **frozen pilot = config seed** (accept/reject ONLY, never moves
  a threshold). **9001–9008 demoted to DEVELOPMENT EVIDENCE**; the bounds they produced at floor
  1.1707 are **design-selection evidence only**, and operative bounds recompute at the ratified
  floor from the committed formula. A seed used for one role may never be reused for another —
  otherwise the design is selected and judged on the same draw.

### 🔴 2026-07-20 (execution) — ROOT SEARCH DONE, JOINT ACCEPTANCE **FAILS**, escape hatch WORKS

Protocol committed at `f0589b9` before it ran; results in `reports/m4a_floor_joint_acceptance.md`
and `reports/m4a_placement_background_rate.md`.

- **ROOT SEARCH: r\* = 1.1850 → r_op = 1.1900** (grid 1.165–1.200 step 0.005, calibration seeds
  8001–8002, R = worst case over seeds). Applied mechanically.
  - ⚠ **The root is NOT resolved beyond its own noise.** R(F) is non-monotone (1.1915, 1.1786,
    1.1769, 1.1828, 1.1797) and the seed-to-seed spread in R averages **0.0043** — the same size as
    the grid step (0.005), the margin (0.005) AND the winning gap F − R(F) = +0.0053. **The margin
    was pre-committed before the noise scale of R was known and does not exceed it.** Also, R is a
    worst case over unconverged extremes, so it is biased DOWNWARD: more sampling can only push it
    up, and the true r\* is likely ABOVE 1.1850.
- 🔴 **JOINT ACCEPTANCE AT 1.1900: FAIL — all six sampling quantities, not marginally.**
  r 0.6509 (bound 0.700) · retained range 1.2172 (1.230) · **weakest-stratum r 0.4391 (0.580)** ·
  weakest range 1.1340 (1.140) · clamped 0.5850 (0.550) · max stratum 0.7600 (0.690). Acceptance
  requires BOTH legs, so this fails regardless of the area leg. **The floor area congruence demands
  and the floor sampling semantics tolerate do not overlap on the current depth envelope.**
- ✅ **ESCAPE HATCH EVALUATED (triggered legitimately, only on joint failure) — IT WORKS.**
  Extending `depth_gaps` raises the ratio CEILING so the floor squeezes less from below:
  ceiling 1.464 → **1.665** (`…1.95`) → **1.844** (`…2.55`). At floor 1.1900 **all six sampling
  quantities PASS with margin** under both extensions (`…1.95`: r 0.845, weakest 0.792, clamped
  0.395; `…2.55`: r 0.905, weakest 0.877, clamped 0.293).
  - 🎁 **It also fixes the separate placement blocker**: failures 1/2400 → **0/2400**. Deeper far
    bins place easily, exactly as the ruling anticipated.
- ⚠ **NOT ESTABLISHED:** the extended envelope has **not been root-searched** (these numbers use a
  floor rooted on the OLD envelope) · the change is **battery-wide** (`depth_gaps` must move for
  counterbalanced/conflict too or the arms stop being depth-matched) · it **re-opens
  z-identifiability** (far depth ~6.2 → ~7.4 m at `…2.55`; leak ceiling and B0/B1/B2 need
  re-checking) · **`…1.95` vs `…2.55` is NOT decided** — both pass; 2.55 has more headroom, 1.95 is
  the smaller perturbation, and minimal perturbation deserves weight given what re-opening z costs.

### 🐛 SEPARATE §5 BLOCKER FOUND: placement failures are a floor-independent background rate

`reports/m4a_placement_background_rate.md`. Surfaced when the root search CRASHED on an un-placeable
image.

- **My first amendment (protocol v1.1) was WRONG, and measuring it is what showed so.** I made any
  placement failure mark a grid point INFEASIBLE, reasoning it could only push r\* upward. The
  *argument* was fine; the **premise** was false. The feasibility map came out NON-MONOTONE (1.165
  fail, 1.170 ok, 1.175 fail, 1.180 ok, 1.185 fail) — not how a property of F behaves.
- **Measured rate, 6 seeds × 1200 per floor: FLAT at ~0.02% across the whole range INCLUDING the old
  six-category floor 1.85** (where placement should be easiest). Pooled **8/43 200 = 0.019%**.
  Gating on a 1-in-2400 event would have made r\* depend on a coin-flip — with this map r\* would
  have come out 1.180 instead of 1.175 purely because seed 8001 lost a die roll. **Superseded by
  v1.2**; both amendments kept visible in the script, since a silent deletion invites the same
  reasoning back.
- 🔴 **The real defect:** the gate-scale render uses `raise_on_placement_failure=True` (correctly —
  an un-placeable image breaks the factor balance). At 0.019%/image: P(≥1 failure) ≈ **7.3%** at
  N=400, **15.7%** at N=900 each, **~34% across the 2 200-image battery**. A one-in-three chance the
  ONE-SHOT §5 render dies partway, presenting as a mysterious late crash rather than a diagnosis.
- **More attempts does NOT fix it** (500 → 2 failures, 2000 → 1, 8000 → 1): specific factor
  combinations are structurally un-placeable, the same lesson as the dropped 0.2 m bin.
- **Resolved for free by the escape hatch** (0/2400), which is a substantive argument for taking it.
- Added `measure_silhouettes.py --allow-placement-failures`, **calibration-only** and explicitly
  documented as never valid for a stimulus render.

**DECISIONS OWED:** take the escape hatch? (`…1.95` vs `…2.55`) · if so, re-root on the extended
envelope, propagate battery-wide, re-derive all constants, re-check z-identifiability · whether the
margin formula needs revising now that R's noise scale is known (0.0043 vs a 0.005 margin).
