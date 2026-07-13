"""Config loading. Every experiment is one YAML in configs/ (CLAUDE.md hard rule).

- Loads YAML to a plain dict (no hidden schema magic; experiments stay greppable).
- Expands ``${VAR}`` / ``$VAR`` in string values from the environment, so configs
  reference ``${DATA_ROOT}`` / ``${HF_HOME}`` instead of hardcoding machine paths.
- Captures run metadata (config + git hash + seed) for reproducible logging.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

_UNRESOLVED = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}")


def _expand(value: Any) -> Any:
    """Recursively expand ``$VAR`` / ``${VAR}`` in all string leaves of a structure."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def _find_unresolved(value: Any, path: str = "") -> list[str]:
    """Collect config keys whose value still contains an unexpanded ``${VAR}``."""
    if isinstance(value, str):
        return [f"{path}: {value}"] if _UNRESOLVED.search(value) else []
    if isinstance(value, dict):
        return [x for k, v in value.items() for x in _find_unresolved(v, f"{path}.{k}".lstrip("."))]
    if isinstance(value, list):
        return [x for i, v in enumerate(value) for x in _find_unresolved(v, f"{path}[{i}]")]
    return []


def load_config(
    path: str | os.PathLike, *, expand_env: bool = True, strict_env: bool = True
) -> dict:
    """Load a YAML config to a dict, expanding environment variables in string values.

    Args:
        path: path to the YAML file.
        expand_env: if True (default), expand ``${VAR}`` references against os.environ.
        strict_env: if True (default), RAISE when a ``${VAR}`` cannot be resolved. Without
            this, ``os.path.expandvars`` leaves the text as-is and a forgotten
            ``export DATA_ROOT`` silently writes the whole dataset into a directory named
            literally ``${DATA_ROOT}`` — a failure that looks like success.

    Raises:
        FileNotFoundError: if the file is missing.
        ValueError: if the top level is not a mapping, or a ${VAR} is unresolved.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"config top level must be a mapping, got {type(data).__name__}: {p}")
    if not expand_env:
        return data

    expanded = _expand(data)
    if strict_env:
        unresolved = _find_unresolved(expanded)
        if unresolved:
            names = sorted({m.group(0) for u in unresolved for m in _UNRESOLVED.finditer(u)})
            raise ValueError(
                f"unresolved environment variable(s) in {p}: {', '.join(names)}\n"
                + "\n".join(f"  {u}" for u in unresolved)
                + "\nExport them (e.g. `export DATA_ROOT=...`) before running."
            )
    return expanded


def git_hash(short: bool = True) -> str:
    """Current git commit hash, or ``"unknown"`` if not a repo / git unavailable."""
    try:
        args = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
        out = subprocess.run(args, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_metadata(config: dict, seed: int) -> dict:
    """Assemble the reproducibility stamp attached to every run: config + git + seed."""
    return {
        "git_hash": git_hash(),
        "seed": seed,
        "config": config,
    }
