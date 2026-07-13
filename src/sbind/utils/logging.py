"""Console logging + a config-driven experiment tracker (CSV default, wandb optional).

Every run logs its config, git hash, and seed (IMPLEMENTATION_PLAN §1). The tracker
backend is chosen by config (``tracking.backend``), so switching CSV<->wandb is a
one-line config change with no code edits. wandb is imported lazily, so a CSV-only run
never needs it installed.

Config shape::

    tracking:
      backend: csv            # csv | wandb | none
      dir: ${DATA_ROOT}/runs  # csv backend: where run folders are written
      project: vsr            # wandb backend
      entity: null            # wandb backend (fill in when enabling wandb)
      run_name: null          # optional label for either backend
"""

from __future__ import annotations

import csv
import logging as _logging
from pathlib import Path
from typing import Any

from .io import ensure_dir, write_json

_CONSOLE_CONFIGURED = False


def get_logger(name: str = "sbind", level: int = _logging.INFO) -> _logging.Logger:
    """Return a console logger with a one-time-configured stream handler."""
    global _CONSOLE_CONFIGURED
    if not _CONSOLE_CONFIGURED:
        handler = _logging.StreamHandler()
        handler.setFormatter(
            _logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S")
        )
        root = _logging.getLogger("sbind")
        root.addHandler(handler)
        root.setLevel(level)
        root.propagate = False
        _CONSOLE_CONFIGURED = True
    return _logging.getLogger(name)


class RunLogger:
    """Abstract experiment tracker. Use ``make_run_logger(config, metadata)``."""

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        raise NotImplementedError

    def finish(self) -> None:
        pass

    def __enter__(self) -> RunLogger:
        return self

    def __exit__(self, *exc: object) -> None:
        self.finish()


class NullRunLogger(RunLogger):
    """No-op backend (``tracking.backend: none``)."""

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        pass


class CsvRunLogger(RunLogger):
    """CSV backend: metrics.csv + a metadata.json stamp under a per-run folder.

    The CSV grows a superset of columns across calls; missing fields are left blank so
    heterogeneous metric dicts across steps stay in one tidy file.
    """

    def __init__(
        self, run_dir: str | Path, metadata: dict | None = None, overwrite: bool = False
    ):
        self.run_dir = ensure_dir(run_dir)
        self.csv_path = Path(self.run_dir) / "metrics.csv"
        # Refuse to clobber a previous run's results. Reusing a run_dir used to overwrite
        # metrics.csv silently — with the M5 probing grid writing many runs, a repeated
        # run_name would have destroyed earlier results with no warning at all.
        if self.csv_path.exists() and not overwrite:
            raise FileExistsError(
                f"{self.csv_path} already exists — refusing to overwrite a previous run. "
                f"Use a distinct tracking.run_name, or set tracking.overwrite: true."
            )
        self._fieldnames: list[str] = []
        self._rows: list[dict[str, Any]] = []
        if metadata is not None:
            write_json(metadata, Path(self.run_dir) / "metadata.json")

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        row = {"step": step, **metrics}
        for key in row:
            if key not in self._fieldnames:
                self._fieldnames.append(key)
        self._rows.append(row)
        self._flush()

    def _flush(self) -> None:
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames)
            writer.writeheader()
            writer.writerows(self._rows)


class WandbRunLogger(RunLogger):
    """wandb backend. Imported lazily so CSV-only environments need no wandb install."""

    def __init__(self, config: dict, metadata: dict | None = None):
        try:
            import wandb
        except ImportError as e:  # pragma: no cover - exercised only when wandb selected
            raise RuntimeError(
                "tracking.backend is 'wandb' but wandb is not installed. "
                "Install the 'analysis' extra or set tracking.backend: csv."
            ) from e
        tracking = config.get("tracking", {})
        self._wandb = wandb
        self._run = wandb.init(
            project=tracking.get("project", "vsr"),
            entity=tracking.get("entity"),
            name=tracking.get("run_name"),
            config=(metadata or {}).get("config", config),
        )

    def log_metrics(self, metrics: dict[str, Any], step: int | None = None) -> None:
        self._wandb.log(metrics, step=step)

    def finish(self) -> None:
        self._run.finish()


def make_run_logger(config: dict, metadata: dict | None = None) -> RunLogger:
    """Construct the tracker named by ``config['tracking']['backend']`` (default csv)."""
    tracking = config.get("tracking", {})
    backend = tracking.get("backend", "csv")
    if backend == "none":
        return NullRunLogger()
    if backend == "csv":
        run_dir = tracking.get("dir", "runs")
        name = tracking.get("run_name")
        if name:
            run_dir = str(Path(run_dir) / name)
        return CsvRunLogger(
            run_dir, metadata=metadata, overwrite=bool(tracking.get("overwrite", False))
        )
    if backend == "wandb":
        return WandbRunLogger(config, metadata=metadata)
    raise ValueError(f"unknown tracking.backend: {backend!r} (expected csv|wandb|none)")
