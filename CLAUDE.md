# vsr

Mechanistic study of where metric spatial information is lost in VLMs (the vision→text-token binding bottleneck). Master's thesis project.

## Before any work

1. Read `docs/IMPLEMENTATION_PLAN.md` — milestones M0–M7 with acceptance criteria. Work on exactly ONE milestone per session; STOP when its acceptance criteria pass. Never start the next milestone unprompted.
2. Read `docs/PROJECT_MEMORY.md` — research context, decisions, and hard-won lessons.
3. `docs/research_proposal_spatial_binding.md` and `docs/VSR_niches_critical_deep_read.md` hold the scientific rationale and literature analysis — read only when a task needs them (probe design, paper writing), not by default.

## Hard rules

- **uv only.** `uv sync`, `uv run`, `uv add`. Never bare `python`, never pip/conda. Dependency groups: `extract` (GPU), `analysis` (CPU), `stimuli`, `dev`.
- **Config-driven.** Every experiment is a YAML in `configs/`. No hardcoded model names, layer indices, paths, prompts, or seeds in code. Same experiment on a different model/checkpoint must be a config change only.
- **Shared GPU server, no scheduler.** Every GPU script: requires explicit `--gpu N`, sets `CUDA_VISIBLE_DEVICES` itself, aborts with a clear message if the target GPU is occupied by another user (check via nvidia-smi at startup). Never claim more than one GPU unless the config says so. Long jobs checkpoint per-batch and support `--resume`.
- **Determinism.** Everything seeded from config. Generated data must be exactly reproducible from config + seed — **and this is verified by re-running and byte-comparing, not assumed from the presence of a seed.** Known traps (all silently violated it): renderer denoising and adaptive sampling (non-deterministic thread scheduling), and timestamps embedded into output files. Annotations/labels/masks must be byte-identical; rendered pixels may differ by at most ~1 LSB on a handful of pixels (irreducible float-accumulation order in multithreaded Cycles) — state that limit, never overclaim.
- **GPU/CPU separation.** GPU code lives only in `src/sbind/extract/` and `src/sbind/interventions/`. Probing and analysis read cached features and must run on a laptop.
- **License caution.** `Raphoo/linear-mech-vlms` and `pittisl/vlm-latent-shaping` have NO license — read for understanding, NEVER copy code from them. MIT-licensed repos (What'sUp, DepthCues, CausalSpatial) may be adapted with attribution.
- **Tests.** Every module ships pytest coverage per the plan's §0: schema round-trips, geometry projection checks, pooling correctness, probe-finds-planted-signal + probe-fails-on-shuffled-labels. **Plus at least one invariant test per data-producing module** — a check that fails if the output is subtly wrong, not merely if the code throws (see "How to verify work"). A milestone is not done until its output is validated, not just produced.
- **Data lives outside git** (`$DATA_ROOT`, `$HF_HOME` — see Environment below). Code is pushed to the remote every session; the server is never the only copy.

## How to verify work (READ THIS BEFORE CLAIMING ANYTHING WORKS)

**Every single bug found in M0–M2 had the same shape: the pipeline ran green while producing wrong data.** Not one was caught by "did it run?", "did the test pass?", or "did it render 500 images?". A green check on the wrong quantity is worse than no check — it manufactures false confidence. So:

### The rule: validate the OUTPUT, never the fact that the pipeline ran.

Before saying something works, ask: *what must be true of the output if this is correct, that would be false if it were subtly broken?* Then measure that. Concretely:

1. **Check an invariant the output cannot violate if correct.** A nearer object subtends more pixels. A projected centre lands inside its own bbox. `loaded_items == source_records`. Invariants catch what smoke tests structurally cannot.
   - *(The mask pipeline silently bled into bounce-lit floor for an entire milestone. Every test passed. It was caught by asking "is a sphere as tall as it is wide?" — it was 66 px wide and 103 px tall.)*
   - ⚠ **But state the invariant in its exact form, or it becomes a false alarm.** "A sphere is exactly as tall as it is wide" holds only **on-axis**: a perspective-projected sphere is an *ellipse*, and off-axis in v0 it legitimately measures w/h ∈ [0.984, 1.037] (the exact projected ellipse predicts [0.984, 1.040]). As literally written the invariant now false-positives by up to 3.9%. The robust general form is **measured == analytic**: derive what the quantity *should* be from first principles and compare, rather than asserting a symmetry that only holds in a special case.
2. **Full scans, not samples.** Smoke-testing 5 items proves nothing about item 4,000. Count integrity, id uniqueness, and file existence must be checked over **every** item.
   - *(A 5-item smoke test missed a whole 14,862-record subset silently resolving to zero, and 2,529 unscoreable MCQs.)*
3. **NEVER silently skip.** No bare `continue` on a record that fails to parse or resolve. Count skips, log them, and **raise if a subset yields zero** — an empty result is a broken assumption, not an empty dataset.
4. **Never trust upstream metadata.** Dataset cards lie. A field documented as a "unique identifier" had 192 rows sharing one string. Verify counts and uniqueness against the actual files.
5. **Never key anything on an id you have not verified is unique.** Especially not output filenames — a colliding id silently *overwrites* data (1,541 items produced 949 images; most pointed at another question's picture).
6. **Measure the margin, not the pass/fail.** A check that passes tells you nothing about whether it will still pass under a different seed. If a property is supposed to hold *by construction*, measure how close it came to breaking.
   - *(Area-congruence reported 0 violations twice while the worst-case margin was 0.6% — it was passing by luck, not construction.)*
7. **Derive thresholds from WORST-CASE measurements, never means — for CONSTRUCTED quantities. For SAMPLED ones, use the weakest prespecified stratum + CIs.** Two clauses; applying either to the wrong class is itself a bug (refined 2026-07-15).
   - **Deterministic, constructible** (rendered geometry, cue constants, calibration thresholds): **worst case, always.** The extremes are measured *exactly*. A mean-based safety threshold was 1.096 when the true worst case was 1.158; it passed validation while guaranteeing nothing.
   - **Sampled / statistical** (probe scores, benchmark accuracies, per-category rates): **no aggregate threshold without checking the weakest PRESPECIFIED stratum**, plus condition-wise uncertainty (CIs, quantiles, failure-rate distribution). **One noisy item must not define a gate** — a literal worst-case rule on noisy data gates on the unluckiest sample, which is noise-chasing, not rigour.
8. **Verify determinism by actually re-running and byte-comparing.** Do not assume seeding is sufficient. Renderer denoising, adaptive sampling, and embedded timestamps all silently broke reproducibility while every test stayed green.
9. **Look at the artefact with your own eyes** when correctness depends on a pairing (image↔annotation, question↔answer). Render it and inspect it. Do not just confirm the file was written.
10. **Never fabricate a constant, path, URL, or ID.** Get it from the source and verify it resolves. *(Placeholder Google-Drive ids were invented once, and a plausible-looking wrong id downloaded 23,937 records of the wrong dataset.)*
11. **A NULL RESULT IS ONLY AS TRUSTWORTHY AS THE PROOF THAT YOUR INSTRUMENT CAN REGISTER A POSITIVE.** Before believing "no effect", show the measurement *moves* when it must — a positive control, an ablation, a sanity intervention. **This is the most dangerous failure mode left in this project**, because unlike an inflated positive, a null *feels* like honest science and gets written up as a finding.
    - *(M3: steering reported a clean 0.0% belief-swap for an hour. The steering was fine. The READOUT was dead: `" left"` and `" right"` share their first token under the LLaMA tokenizer, so both options scored an identical logit and every belief came out exactly 0.5/0.5 — **even under zero-ablation**. Then, once fixed, it turned out LLaVA answers `"Left"`/`"Right"` (capitalised, carrying ~all the mass) while the lowercase forms sit at p ≈ 2e-5 — so the probe was reading the far TAIL of the distribution. Two independent bugs, both silent, both producing a confident null.)*
    - The check that caught it: **zero-ablate the thing you are intervening on.** If destroying it does not move your metric, your metric is not measuring it.
12. **A shuffled-label control is NOT enough — every probe needs a DUMB-FEATURES CEILING, reported as an INCREMENTAL GAIN.** The shuffled control catches a probe fitting noise; it cannot catch a probe reading a trivially available *non-representational* feature. Decodability only counts **above** what mask geometry / shape / colour / cue values already give you.
    - **Report three numbers per cell (refined 2026-07-15), and the third is load-bearing:** (1) best dumb-feature score; (2) the probe score; (3) **`Δ_repr|dumb = score(dumb ∪ representation) − score(dumb)`**. A bare `probe − dumb` difference never establishes that the representation adds anything the dumb features didn't already carry; the incremental form does.
    - **Held-out splits must target the CLAIMED generalization** — held-out object identities, camera poses, depth *ranges*, cue combinations — **never only random image splits.** A random split over a factorial battery leaks every factor into training by construction.
    - *(Mask geometry ALONE — centroid, area, bbox — predicts lateral position at R² = 0.942 and depth at R² = 0.972 on v0. The model's activations added ~0.05. Every shuffled-label control passed.)*
    - *(Same class of bug: category was never balanced against the near/far depth role, so a **shape-only** constant strategy scored 55.1%. Passed every unit test; died only under an adversarial baseline.)*
13. **🔴 AN ARGUMENT THAT MAKES YOUR FINDING FOLLOW FROM A DEFINITION IS A BUG, NOT AN INSIGHT.** Rules 1–12 all validate an **output**. **None of them can catch a bad INFERENCE** — and this project has now shipped one.
    - *(2026-07-14: "occlusion is the third depth cue and the only **categorical** one — it carries **ZERO metric content** — **therefore**, if VLMs lean on it, their best cue *cannot* carry metric information and the qualitative-vs-metric asymmetry follows *in principle*." It stood in two docs for a day. It is **false**: T-junctions/containment/support are also ordinal cues, and occlusion boundaries + known shapes + camera geometry **do** constrain metric depth. No measurement was wrong. The *deduction* was — and it felt like insight precisely because it was **cheap**: it made the program's headline asymmetry true a priori, so no experiment could have contradicted it.)*
    - **The smell test: if the claim would survive even if every experiment came back null, it is not an empirical claim.** A result you cannot lose is a result you cannot earn.
    - **Any deduction load-bearing for a headline claim gets an adversarial domain read BEFORE it enters a doc** — the same standard as rule 12's dumb-features baseline, applied to arguments instead of probes. Prefer the weak, measurable form ("over-reliance on an ordinal cue *could* leave metric depth poorly represented") over the strong, deductive one ("therefore it *cannot*").
    - **When a claim is retracted, leave the retraction visible in the doc.** A silent deletion re-opens the door for the same elegant argument to walk back in next session.

### When the user doubts something, treat it as a signal, not a challenge.
Every time a doubt was raised ("did you download all of it?", "does it all work?", "was M0/M1 also broken?"), **measuring instead of answering from memory found real bugs.** Re-derive the answer from the data every time.

## End of every session

Update `docs/IMPLEMENTATION_PLAN.md` and `docs/PROJECT_MEMORY.md` with decisions made and state reached, then commit with a descriptive message.

## Environment (filled in at M0 — 2026-07-10, server plant-ai06)

- ⚠ **`$DATA_ROOT` and `$HF_HOME` are NOT exported in any shell profile** — a fresh shell has them unset. Export both at the start of every session (or add them to `~/.bashrc`):
  ```bash
  export DATA_ROOT=/data3/hugin/vsr HF_HOME=/data3/hugin/hf_home
  ```
  Nothing silently defaults if you forget: `load_config` and `dataset_root` both raise (they used to fabricate the absolute path `/external` instead). The test suite skips its data-dependent tests rather than erroring.
- `$DATA_ROOT`: `/data3/hugin/vsr` — data3 is a shared 20T NFS mount with ~7.8T free (62% used); ample for models + activation caches + stimuli.
- `$HF_HOME`: `/data3/hugin/hf_home` — HF model cache on the big disk, NOT on `/home` (home partition is shared NFS, only ~1.5T free at 73%; model zoo grows to ~300–500 GB across Paper 1 + Paper 2 checkpoints). Non-model caches (pip/uv) may stay in `~/.cache`.
- GPUs: **8× NVIDIA RTX A6000, 48 GB each** on plant-ai06 (the main server). First-come-first-served, no scheduler; multi-GPU allowed. Other servers have 4090/2080 but are rarely used — out of scope. **NOTE: hardware is A6000 48 GB, not A100** — the plan's prose says "A100"; compute all memory budgets against 48 GB. GPU-guard treats a device as occupied-by-another-user when `nvidia-smi` memory-used exceeds a configurable threshold (default 1024 MiB, so a small idle resident does not false-trip) or a foreign compute process is present.
- Experiment tracking: **CSV by default** (config, git-hash, seed logged to tidy local files under `$DATA_ROOT`); wandb available via config (`tracking.backend: wandb`) — wandb login already cached in `~/.netrc` (verified 2026-07-10), entity **`chaso-hosei-university`** (user `chaso`), default project `vsr`. Switch is a one-line config change; targeted for M4/M5 when the probing grid produces many runs.
- Git remote: **`origin` = `git@github.com:Hugin373/vsr.git`**, and `main` is pushed. The "server is never the only copy" hard rule is **met** (the M0/M1 docs said otherwise for a while — they were stale; verified 2026-07-14). Push every session.

## Commands

- Setup: `uv sync --extra dev --extra analysis` (add `--extra extract` on the server)
- Tests: `uv run pytest`
- Lint: `uv run ruff check src/ tests/`
