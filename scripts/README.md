# scripts/

Thin CLI entrypoints, run via `uv run scripts/<name>.py`. They parse args, load a
config from `configs/`, and call into `src/sbind/`. GPU scripts must call
`sbind.utils.gpu.claim_gpu(args.gpu, ...)` **before** importing torch.

Populated from M1 onward (render, extract, probe, ...). Empty at M0 by design.
