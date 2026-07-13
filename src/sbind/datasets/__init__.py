"""Adapters for external benchmarks (M2).

Uniform interface: ``load(name, config) -> Iterable[Item]``. Importing this package
registers every adapter. See base.py for the Item contract.
"""

from . import causalspatial, cvbench, depthcues, mindcube, revsi, whatsup  # noqa: F401
from .base import Item, available, decode_frames, load, register, take

__all__ = ["Item", "load", "available", "take", "decode_frames", "register"]
