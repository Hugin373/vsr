"""Uniform interface for external benchmarks (IMPLEMENTATION_PLAN M2).

    load(name, config) -> Iterable[Item]

Every adapter yields the same ``Item``, whatever the source format. Notes on the shape:

- ``images`` is ALWAYS a list of paths, length 1 for single-image datasets. Half of these
  benchmarks are not single-image (ReVSI is video, MindCube is multi-view), so a singular
  ``image`` field could not express them; one uniform list beats two interfaces.
- ``id`` is stable and carries its origin (``"<dataset>/<original index or key>"``), so an
  eval result can always be joined back to the source item.
- ``meta`` carries everything source-specific: ``dataset_name``, ``answer_type``
  (mcq|numeric|open), ``options`` for MCQ, plus any per-dataset fields.
- Video items carry ``video`` (path) and ``frame_indices``; frames are decoded LAZILY via
  ``decode_frames`` — nothing is materialised to disk at load time.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..utils.io import ensure_dir

# name -> loader function
_REGISTRY: dict[str, Callable[..., Iterable[Item]]] = {}


@dataclass
class Item:
    """One benchmark question. The uniform currency of every adapter."""

    id: str  # stable, origin-carrying: "<dataset>/<index-or-key>"
    images: list[str]  # ALWAYS a list; length 1 for single-image datasets
    question: str
    answer: str
    meta: dict[str, Any] = field(default_factory=dict)
    video: str | None = None  # set for video datasets; frames decoded lazily
    frame_indices: list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Item:
        return cls(
            id=d["id"],
            images=list(d["images"]),
            question=d["question"],
            answer=d["answer"],
            meta=d.get("meta", {}),
            video=d.get("video"),
            frame_indices=d.get("frame_indices"),
        )

    @property
    def dataset_name(self) -> str:
        return self.meta.get("dataset_name", self.id.split("/")[0])


def register(name: str):
    """Decorator: register an adapter under ``name``."""

    def _wrap(fn):
        _REGISTRY[name] = fn
        return fn

    return _wrap


def available() -> list[str]:
    return sorted(_REGISTRY)


def load(name: str, config: dict | None = None, **kwargs) -> Iterable[Item]:
    """Load a registered dataset by name. ``config`` is the parsed configs/datasets.yaml."""
    if name not in _REGISTRY:
        raise KeyError(f"unknown dataset {name!r}. Available: {', '.join(available())}")
    return _REGISTRY[name](config or {}, **kwargs)


def dataset_root(config: dict, name: str) -> Path:
    """Where dataset ``name`` lives on disk (config-driven, never hardcoded)."""
    root = config.get("root") or os.environ.get("DATA_ROOT", "") + "/external"
    return Path(os.path.expandvars(str(root))) / name


def materialize_image(data: bytes, path: str | os.PathLike) -> str:
    """Write embedded image bytes to ``path`` once; return the path.

    Several benchmarks (CV-Bench, CausalSpatial) embed images inside parquet rather than
    shipping files. Extracting them on first access keeps ``Item.images`` a uniform list
    of paths for every dataset, instead of paths for some and PIL objects for others.
    """
    p = Path(path)
    if not p.exists():
        ensure_dir(p.parent)
        tmp = p.with_suffix(p.suffix + ".tmp")
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, p)
    return str(p)


def decode_frames(video_path: str | os.PathLike, indices: Iterable[int]) -> list:
    """Lazily decode the given frame indices from a video. Returns a list of PIL Images.

    PyAV rather than decord (decord has no maintained wheels for our Python/numpy pin).
    """
    import av
    from PIL import Image

    wanted = sorted(set(int(i) for i in indices))
    if not wanted:
        return []
    out: dict[int, Image.Image] = {}
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        for i, frame in enumerate(container.decode(stream)):
            if i in out:
                continue
            if i in wanted:
                out[i] = frame.to_image()
            if len(out) == len(wanted):
                break
    return [out[i] for i in wanted if i in out]


def take(iterable: Iterable[Item], n: int) -> list[Item]:
    """First n items (adapters stream, so never materialise a whole benchmark)."""
    result: list[Item] = []
    it: Iterator[Item] = iter(iterable)
    for _ in range(n):
        try:
            result.append(next(it))
        except StopIteration:
            break
    return result
