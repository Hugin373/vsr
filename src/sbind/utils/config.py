"""Config loading. Every experiment is one YAML in configs/ (CLAUDE.md hard rule).

- Loads YAML to a plain dict (no hidden schema magic; experiments stay greppable).
- Expands ``${VAR}`` / ``$VAR`` in string values from the environment, so configs
  reference ``${DATA_ROOT}`` / ``${HF_HOME}`` instead of hardcoding machine paths.
- Captures run metadata (config + git hash + seed) for reproducible logging.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

# BOTH forms. Matching only ${VAR} left a hole: os.path.expandvars leaves an unresolved $VAR
# as literal text, so `root: $NOPE/external` sailed through strict_env as the path "$NOPE/…".
_UNRESOLVED = re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]*")

# Which env vars a config REFERENCES — collected BEFORE expansion. Checking only the expanded
# result cannot see an empty-but-SET var: `DATA_ROOT=""` expands `${DATA_ROOT}/external` to
# "/external" with nothing left to match, i.e. a forgotten export silently became an absolute
# path at the filesystem root. That is the exact failure this module exists to prevent.
_VAR_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


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
    """Collect config keys whose value still contains an unexpanded ``$VAR`` / ``${VAR}``."""
    if isinstance(value, str):
        return [f"{path}: {value}"] if _UNRESOLVED.search(value) else []
    if isinstance(value, dict):
        return [x for k, v in value.items() for x in _find_unresolved(v, f"{path}.{k}".lstrip("."))]
    if isinstance(value, list):
        return [x for i, v in enumerate(value) for x in _find_unresolved(v, f"{path}[{i}]")]
    return []


def _find_empty_vars(value: Any, path: str = "") -> list[str]:
    """Config keys referencing an env var that is unset OR set to the empty string."""
    if isinstance(value, str):
        out = []
        for m in _VAR_REF.finditer(value):
            name = m.group(1) or m.group(2)
            if not os.environ.get(name):  # unset or empty — both are misconfiguration
                state = "empty" if name in os.environ else "unset"
                out.append(f"{path}: {value}  (${name} is {state})")
        return out
    if isinstance(value, dict):
        return [x for k, v in value.items() for x in _find_empty_vars(v, f"{path}.{k}".lstrip("."))]
    if isinstance(value, list):
        return [x for i, v in enumerate(value) for x in _find_empty_vars(v, f"{path}[{i}]")]
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

    # Check the vars the config REFERENCES, before expansion wipes the evidence.
    if strict_env:
        empty = _find_empty_vars(data)
        if empty:
            raise ValueError(
                f"unresolved environment variable(s) in {p} — unset or empty:\n"
                + "\n".join(f"  {e}" for e in empty)
                + "\nExport them (e.g. `export DATA_ROOT=...`) before running."
            )

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


def _git(*args: str) -> str | None:
    """Run a git command, returning stripped stdout, or None if not a repo / git absent."""
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_dirty() -> bool | None:
    """Does the working tree differ from HEAD? None if not a repo / git unavailable.

    ⚠ UNTRACKED FILES COUNT AS DIRTY, deliberately. This is not paranoia — it is the exact
    case that produced the bug this function exists to catch: the aborted
    ``m4a_v1_counterbalanced`` render (2026-07-16) stamped ``git_hash: 725ad42`` while the
    config it rendered from (``configs/m4a_v1_counterbalanced.yaml``) was still UNTRACKED and
    the generator uncommitted — neither existed at that commit. Checking only *tracked*
    modifications would have called that tree clean and reproduced the same false stamp.
    A false "dirty" costs nothing; a false "clean" is a provenance lie.
    """
    status = _git("status", "--porcelain")
    return None if status is None else bool(status)


def git_patch_sha(short: bool = True) -> str | None:
    """sha256 of the uncommitted delta, so two runs from the SAME dirty tree stamp alike.

    Covers tracked edits (``git diff HEAD``) AND the untracked/staged file list
    (``git status --porcelain``) — a diff alone cannot see a new untracked file's existence.
    Returns None when the tree is clean or git is unavailable. This does not make a dirty run
    reproducible; it makes it *identifiable*.
    """
    if not git_dirty():
        return None
    status = _git("status", "--porcelain") or ""
    diff = _git("diff", "HEAD") or ""
    digest = hashlib.sha256(f"{status}\n{diff}".encode()).hexdigest()
    return digest[:12] if short else digest


def git_hash(short: bool = True) -> str:
    """Current git commit, ``-dirty``-suffixed if the tree has uncommitted changes.

    Returns ``"unknown"`` if not a repo / git unavailable.

    ⚠ The suffix is load-bearing (added 2026-07-17). This returned a bare ``HEAD`` hash and
    never looked at the working tree, so the plan's §1 promise — "every run logs config, git
    hash, seed" — was silently FALSE for every run made from a dirty tree, i.e. most runs
    during active development. A stamp naming a commit that could not have produced the output
    is worse than no stamp: it manufactures provenance. Same shape as every other bug in this
    project's history — the pipeline ran green while recording wrong data.
    """
    args = ["rev-parse", "--short", "HEAD"] if short else ["rev-parse", "HEAD"]
    head = _git(*args)
    if head is None:
        return "unknown"
    return f"{head}-dirty" if git_dirty() else head


def run_metadata(config: dict, seed: int) -> dict:
    """Assemble the reproducibility stamp attached to every run: config + git + seed.

    ``git_dirty`` is recorded EXPLICITLY rather than left implicit in the hash suffix, so a
    consumer can filter on it without string-matching, and ``git_patch_sha`` identifies *which*
    dirty state. A run with ``git_dirty: true`` is NOT reproducible from (git_hash, seed) alone
    and must not be treated as such — that is precisely the claim this field exists to refute.
    """
    return {
        "git_hash": git_hash(),
        "git_dirty": git_dirty(),
        "git_patch_sha": git_patch_sha(),
        "seed": seed,
        "config": config,
    }
