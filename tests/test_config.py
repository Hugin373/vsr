"""Config loader: YAML load + env-var expansion + run metadata."""

import pytest

from sbind.utils.config import load_config, run_metadata


def test_load_and_expand_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_ROOT", "/data3/hugin/vsr")
    monkeypatch.setenv("HF_HOME", "/data3/hugin/hf_home")
    cfg_path = tmp_path / "exp.yaml"
    cfg_path.write_text(
        "experiment: t\n"
        "seed: 7\n"
        "paths:\n"
        "  activations: ${DATA_ROOT}/activations\n"
        "  hf: ${HF_HOME}\n"
        "  nested:\n"
        "    - ${DATA_ROOT}/a\n"
        "    - literal\n",
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg["seed"] == 7
    assert cfg["paths"]["activations"] == "/data3/hugin/vsr/activations"
    assert cfg["paths"]["hf"] == "/data3/hugin/hf_home"
    assert cfg["paths"]["nested"] == ["/data3/hugin/vsr/a", "literal"]


def test_expand_env_can_be_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_ROOT", "/x")
    cfg_path = tmp_path / "exp.yaml"
    cfg_path.write_text("p: ${DATA_ROOT}/a\n", encoding="utf-8")
    cfg = load_config(cfg_path, expand_env=False)
    assert cfg["p"] == "${DATA_ROOT}/a"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")


def test_non_mapping_top_level_raises(tmp_path):
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(cfg_path)


def test_example_config_loads(monkeypatch):
    # The shipped configs/example.yaml must load and expand cleanly.
    monkeypatch.setenv("DATA_ROOT", "/data3/hugin/vsr")
    monkeypatch.setenv("HF_HOME", "/data3/hugin/hf_home")
    cfg = load_config("configs/example.yaml")
    assert cfg["tracking"]["backend"] == "csv"
    assert cfg["paths"]["activations"] == "/data3/hugin/vsr/activations"
    assert cfg["gpu"]["mem_threshold_mib"] == 1024


def test_run_metadata_shape():
    meta = run_metadata({"experiment": "t"}, seed=3)
    assert meta["seed"] == 3
    assert meta["config"] == {"experiment": "t"}
    assert "git_hash" in meta
