"""Determinism helpers. Everything in this project seeds from config (CLAUDE.md).

torch is imported lazily and guarded so this module works on a GPU-less analysis
machine where torch is not installed (the ``extract`` extra is server-only).
"""

from __future__ import annotations

import os
import random


def seed_everything(seed: int, deterministic_torch: bool = True) -> int:
    """Seed Python, NumPy, and (if available) torch CPU+CUDA RNGs. Returns the seed.

    ⚠ This does NOT set PYTHONHASHSEED. Assigning it here would be theatre: CPython reads it
    once, at interpreter start-up, so setting it from inside a running process has no effect
    whatsoever on string-hash randomisation — the old code did exactly that and looked seeded
    while not being. Nothing in this project may depend on `hash()` / set-iteration order; seed
    a `random.Random(...)` explicitly instead (see the What'sUp option shuffle). If a launcher
    ever truly needs it, it must be exported in the ENVIRONMENT before `python` starts.

    Args:
        seed: the integer seed (from config; never hardcoded in experiment code).
        deterministic_torch: also request deterministic kernels. Slightly slower but required
            for exactly-reproducible extraction (M4).
    """
    random.seed(seed)

    import numpy as np

    np.random.seed(seed)

    try:
        import torch
    except ImportError:
        return seed

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic_torch:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        # cudnn.deterministic alone does NOT make CUDA matmul/scatter kernels deterministic.
        # Without this, M4's extraction can vary run-to-run while appearing fully seeded —
        # and this project has already been bitten once by assuming a seed was sufficient.
        # warn_only: a few ops have no deterministic kernel; warn rather than hard-fail.
        torch.use_deterministic_algorithms(True, warn_only=True)
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")  # required by cuBLAS

    return seed
