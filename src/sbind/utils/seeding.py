"""Determinism helpers. Everything in this project seeds from config (CLAUDE.md).

torch is imported lazily and guarded so this module works on a GPU-less analysis
machine where torch is not installed (the ``extract`` extra is server-only).
"""

from __future__ import annotations

import os
import random


def seed_everything(seed: int, deterministic_torch: bool = True) -> int:
    """Seed Python, NumPy, and (if available) torch CPU+CUDA RNGs. Returns the seed.

    Args:
        seed: the integer seed (from config; never hardcoded in experiment code).
        deterministic_torch: also request deterministic cuDNN kernels. Slightly slower
            but required for exactly-reproducible extraction.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
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

    return seed
