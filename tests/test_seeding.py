"""Seeding determinism (works with or without torch installed)."""

import random

from sbind.utils.seeding import seed_everything


def test_returns_seed():
    assert seed_everything(123) == 123


def test_same_seed_same_draws():
    seed_everything(42)
    import numpy as np

    a_py = [random.random() for _ in range(5)]
    a_np = np.random.rand(5).tolist()

    seed_everything(42)
    b_py = [random.random() for _ in range(5)]
    b_np = np.random.rand(5).tolist()

    assert a_py == b_py
    assert a_np == b_np


def test_different_seed_different_draws():
    seed_everything(0)
    import numpy as np

    a = np.random.rand(5).tolist()
    seed_everything(1)
    b = np.random.rand(5).tolist()
    assert a != b
