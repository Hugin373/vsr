"""Config loading. Every experiment is one YAML in configs/ (CLAUDE.md hard rule).

- Loads YAML to a plain dict (no hidden schema magic; experiments stay greppable).
- Expands ``${VAR}`` / ``$VAR`` in string values from the environment, so configs
  reference ``${DATA_ROOT}`` / ``${HF_HOME}`` instead of hardcoding machine paths.
- Captures run metadata (config + git hash + seed) for reproducible logging.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _expand(value: Any) -> Any:
    """Recursively expand ``$VAR`` / ``${VAR}`` in all string leaves of a structure."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def load_config(path: str | os.PathLike, *, expand_env: bool = True) -> dict:
    """Load a YAML config to a dict, expanding environment variables in string values.

    Args:
        path: path to the YAML file.
        expand_env: if True (default), expand ``${VAR}`` references against os.environ.

    Raises:
        FileNotFoundError: if the file is missing.
        ValueError: if the top-level document is not a mapping.
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
    return _expand(data) if expand_env else data


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
