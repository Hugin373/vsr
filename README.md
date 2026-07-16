# vsr — spatial binding bottleneck

Mechanistic study of where metric spatial information becomes unavailable or unusable in VLMs (the
vision-to-text-token binding bottleneck). Master's thesis project.

See `AGENTS.md` for the hard rules and environment, and `docs/IMPLEMENTATION_PLAN.md`
for milestones M0–M7.

## Setup

`uv` only — never bare `python`/pip/conda.

```bash
# analysis / laptop (CPU probing, plotting)
uv sync --extra dev --extra analysis

# server (adds GPU extraction stack)
uv sync --extra dev --extra analysis --extra extract
```

## Commands

```bash
uv run pytest                 # tests
uv run ruff check src/ tests/ # lint
```

## Layout

```
src/sbind/
  stimuli/       scene specs -> images + annotations   (M1, M4)
  datasets/      external benchmark adapters           (M2)
  extract/       model loading, hooks, pooling  [GPU]  (M4)
  probes/        ridge/logistic probes + controls [CPU](M5)
  interventions/ steering, metric-ID injection  [GPU]  (M6)
  eval/          verbalized answers, benchmark scoring
  utils/         gpu guard, seeding, config, io, logging
  schemas.py     frozen §3 data schemas
configs/         YAML experiment configs
scripts/         thin CLI entrypoints (uv run scripts/...)
tests/
```

Data lives outside git under `$DATA_ROOT` / `$HF_HOME` (see `AGENTS.md` → Environment).
