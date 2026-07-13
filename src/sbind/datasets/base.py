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
import re
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
    """Where dataset ``name`` lives on disk (config-driven, never hardcoded).

    Raises if it cannot be resolved. It used to fall back to
    ``os.environ.get("DATA_ROOT", "") + "/external"``, which with DATA_ROOT unset silently
    fabricated the absolute path ``/external/<name>`` — a forgotten export became a wrong path
    instead of an error, which is the bug class this project keeps paying for.
    """
    root = config.get("root") or os.environ.get("DATA_ROOT")
    if not root:
        raise ValueError(
            f"cannot resolve the data root for {name!r}: pass config['root'] or export "
            f"$DATA_ROOT. (Never fall back to a default path — a forgotten export must fail "
            f"loudly, not write to the wrong place.)"
        )
    resolved = os.path.expandvars(str(root))
    if "$" in resolved:
        raise ValueError(f"unresolved environment variable in data root: {resolved!r}")
    if not config.get("root"):
        resolved = f"{resolved}/external"
    return Path(resolved) / name


# --- What may a dataset be USED FOR? (enforced, not merely documented) -----------------
#
# `meta.synthesized_question` alone is too blunt a flag: it is true for BOTH What'sUp and
# DepthCues, but they are not the same kind of thing.
#
#   NATIVE_QA      native question AND native answer -> safe for behavioral claims.
#   NATIVE_TASK    the TASK and answer key are native (What'sUp: pick the correct caption
#                  from 4); only our prompt WORDING is synthesized. Safe for behavioral
#                  claims — it is our qualitative positive control.
#   PROBE_ONLY     NOT a question-answering benchmark at all. DepthCues ships regression /
#                  binary probe targets (image + mask pair + label) with NO task text; the
#                  "question" is entirely our invention and its "answer" is a raw label.
#
# RULE: nothing that scores a VERBALIZED answer may touch a PROBE_ONLY dataset. A model's
# "accuracy" on a question we made up is not a behavioral result about anything. Call
# assert_behavioral_safe() at the top of any eval/scoring entrypoint.
NATIVE_QA = frozenset({"cvbench", "mindcube", "causalspatial", "revsi"})
NATIVE_TASK = frozenset({"whatsup"})
PROBE_ONLY = frozenset({"depthcues"})

BEHAVIORAL_SAFE = NATIVE_QA | NATIVE_TASK


def assert_behavioral_safe(name: str) -> None:
    """Raise if ``name`` must not be used for a verbalized-answer / behavioral claim."""
    if name in PROBE_ONLY:
        raise ValueError(
            f"{name!r} is PROBE_ONLY: its questions are synthesized by us and its answers are "
            f"raw probe targets, so scoring verbalized answers on it would be meaningless. "
            f"Use it for encoder-level probing (meta.label) only. "
            f"Behavioral-safe datasets: {', '.join(sorted(BEHAVIORAL_SAFE))}."
        )


LETTERS = "ABCDEFGH"

# Options written into a question body. Several benchmarks do this, in different formats:
#   "A. Curtain B. Gray-green backrest C. TV"        (MindCube)
#   "A. Yes; B. No; C. Not Sure."                    (CausalSpatial collision)
#   "Answer by (A) Yes, (B) No or (C) Not sure."     (CausalSpatial physics/...)
# and sometimes with an instruction paragraph spliced BETWEEN two options.
#
# The space after the marker is OPTIONAL (some rows read "E.Removing the vase"). The
# ordered-run check in parse_inline_options is what guards against matching a stray "A."
# in prose — NOT a character class on the option text: a naive `[^A-H]*?` for the text
# stops dead on the "C" in "Curtain".
_OPT_MARKER = re.compile(r"(?:^|[\s;(])([A-H])[.)]\s*(?=\S)")


def parse_inline_options(question: str) -> dict[str, str]:
    """Recover {letter: text} from multiple-choice options written into the question body."""
    markers = []
    expected = 0
    for m in _OPT_MARKER.finditer(question):
        if LETTERS.index(m.group(1)) == expected:  # accept only a strict A, B, C, ... run
            markers.append(m)
            expected += 1
    if len(markers) < 2:
        return {}

    out: dict[str, str] = {}
    for i, m in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(question)
        text = question[m.end() : end]
        text = re.split(r"\bNote\s*:", text)[0]  # drop a spliced-in instruction paragraph
        text = text.strip().strip(";,.").strip()
        text = re.sub(r"\s+or$", "", text).strip()
        if text:
            out[m.group(1)] = text
    return out


def strip_option_letters(options: list[str]) -> list[str]:
    """Drop a leading "A. " / "(A) " marker from options that ship pre-lettered (ReVSI)."""
    return [re.sub(r"^\(?([A-H])[.)]\s*", "", str(o)).strip() for o in options]


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

    RAISES if any requested index is not in the clip. It used to return
    ``[out[i] for i in wanted if i in out]`` — silently handing back FEWER images than asked
    for, so a model was fed a different input than the record claimed, and the contact sheet
    captioned frame 3 as "frame 2". A short read here is a broken assumption, not a shorter list.
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
    missing = [i for i in wanted if i not in out]
    if missing:
        raise IndexError(
            f"{video_path}: requested {len(wanted)} frames but {len(missing)} do not exist "
            f"(e.g. {missing[:5]}). The clip is shorter than the annotation claims."
        )
    return [out[i] for i in wanted]


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
