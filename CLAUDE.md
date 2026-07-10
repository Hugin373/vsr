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
- **Determinism.** Everything seeded from config. Generated data must be exactly reproducible from config + seed.
- **GPU/CPU separation.** GPU code lives only in `src/sbind/extract/` and `src/sbind/interventions/`. Probing and analysis read cached features and must run on a laptop.
- **License caution.** `Raphoo/linear-mech-vlms` and `pittisl/vlm-latent-shaping` have NO license — read for understanding, NEVER copy code from them. MIT-licensed repos (What'sUp, DepthCues, CausalSpatial) may be adapted with attribution.
- **Tests.** Every module ships pytest coverage per the plan's §0: schema round-trips, geometry projection checks, pooling correctness, probe-finds-planted-signal + probe-fails-on-shuffled-labels.
- **Data lives outside git** (`$DATA_ROOT`, `$HF_HOME` — see Environment below). Code is pushed to the remote every session; the server is never the only copy.

## End of every session

Update `docs/IMPLEMENTATION_PLAN.md` and `docs/PROJECT_MEMORY.md` with decisions made and state reached, then commit with a descriptive message.

## Environment (filled in at M0 — 2026-07-10, server plant-ai06)

- `$DATA_ROOT`: `/data3/hugin/vsr` — data3 is a shared 20T NFS mount with ~7.8T free (62% used); ample for models + activation caches + stimuli.
- `$HF_HOME`: `/data3/hugin/hf_home` — HF model cache on the big disk, NOT on `/home` (home partition is shared NFS, only ~1.5T free at 73%; model zoo grows to ~300–500 GB across Paper 1 + Paper 2 checkpoints). Non-model caches (pip/uv) may stay in `~/.cache`.
- GPUs: **8× NVIDIA RTX A6000, 48 GB each** on plant-ai06 (the main server). First-come-first-served, no scheduler; multi-GPU allowed. Other servers have 4090/2080 but are rarely used — out of scope. **NOTE: hardware is A6000 48 GB, not A100** — the plan's prose says "A100"; compute all memory budgets against 48 GB. GPU-guard treats a device as occupied-by-another-user when `nvidia-smi` memory-used exceeds a configurable threshold (default 1024 MiB, so a small idle resident does not false-trip) or a foreign compute process is present.
- Experiment tracking: **CSV by default** (config, git-hash, seed logged to tidy local files under `$DATA_ROOT`); wandb available via config (`tracking.backend: wandb`) — user has a wandb account; entity to be filled when enabled (targeted for M4/M5 when the probing grid produces many runs).
- Git remote: **deferred** (personal research, local-only for now). ⚠ CLAUDE.md hard rule "server is never the only copy" is currently unmet — add a GitHub `origin` and push when convenient.

## Commands

- Setup: `uv sync --extra dev --extra analysis` (add `--extra extract` on the server)
- Tests: `uv run pytest`
- Lint: `uv run ruff check src/ tests/`
