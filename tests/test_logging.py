"""Tracker backend selection + CSV logger behavior."""

import csv

from sbind.utils.io import read_json
from sbind.utils.logging import (
    CsvRunLogger,
    NullRunLogger,
    make_run_logger,
)


def test_make_run_logger_defaults_to_csv(tmp_path):
    cfg = {"tracking": {"backend": "csv", "dir": str(tmp_path / "runs")}}
    logger = make_run_logger(cfg, metadata={"seed": 0, "config": cfg, "git_hash": "abc"})
    assert isinstance(logger, CsvRunLogger)


def test_make_run_logger_none_backend():
    assert isinstance(make_run_logger({"tracking": {"backend": "none"}}), NullRunLogger)


def test_unknown_backend_raises():
    import pytest

    with pytest.raises(ValueError):
        make_run_logger({"tracking": {"backend": "mlflow"}})


def test_csv_logger_writes_metrics_and_metadata(tmp_path):
    run_dir = tmp_path / "run1"
    meta = {"seed": 3, "git_hash": "deadbeef", "config": {"experiment": "t"}}
    with CsvRunLogger(run_dir, metadata=meta) as logger:
        logger.log_metrics({"spearman": 0.6, "n": 500}, step=0)
        logger.log_metrics({"spearman": 0.7, "r2": 0.4}, step=1)

    saved_meta = read_json(run_dir / "metadata.json")
    assert saved_meta == meta

    with open(run_dir / "metrics.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["step"] == "0"
    assert rows[0]["spearman"] == "0.6"
    # heterogeneous keys across steps end up as a column superset; missing -> blank
    assert rows[0]["r2"] == ""
    assert rows[1]["r2"] == "0.4"


def test_csv_logger_uses_run_name_subdir(tmp_path):
    cfg = {"tracking": {"backend": "csv", "dir": str(tmp_path), "run_name": "exp_a"}}
    logger = make_run_logger(cfg)
    logger.log_metrics({"x": 1})
    assert (tmp_path / "exp_a" / "metrics.csv").exists()


def test_csv_logger_refuses_to_clobber_a_previous_run(tmp_path):
    """Reusing a run_dir silently overwrote the previous run's metrics.csv — data loss."""
    import pytest

    CsvRunLogger(tmp_path).log_metrics({"a": 1})
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        CsvRunLogger(tmp_path)
    # explicit opt-in still works
    CsvRunLogger(tmp_path, overwrite=True).log_metrics({"a": 2})
