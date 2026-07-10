"""Small filesystem/JSON helpers shared across milestones.

Stdlib-only on purpose: the core package must import on a laptop with no extras.
Parquet/zarr helpers (which need the ``analysis`` extra) live with their consumers.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


def ensure_dir(path: str | os.PathLike) -> Path:
    """Create ``path`` (and parents) if absent; return it as a Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(obj: Any, path: str | os.PathLike, *, indent: int = 2) -> None:
    """Atomically write ``obj`` as JSON (write to a temp file, then rename)."""
    p = Path(path)
    ensure_dir(p.parent)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)
    os.replace(tmp, p)


def read_json(path: str | os.PathLike) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_jsonl(records: Iterable[dict], path: str | os.PathLike) -> int:
    """Atomically write an iterable of dicts as JSON Lines. Returns the row count."""
    p = Path(path)
    ensure_dir(p.parent)
    tmp = p.with_suffix(p.suffix + ".tmp")
    n = 0
    with open(tmp, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    os.replace(tmp, p)
    return n


def read_jsonl(path: str | os.PathLike) -> Iterator[dict]:
    """Lazily yield dicts from a JSON Lines file. Blank lines are skipped."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
