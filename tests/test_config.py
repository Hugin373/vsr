"""Config loader: YAML load + env-var expansion + run metadata + git provenance."""

import shutil
import subprocess

import pytest

from sbind.utils.config import git_dirty, git_hash, git_patch_sha, load_config, run_metadata


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
    assert "git_dirty" in meta


# ---------------------------------------------------------------------------
# Provenance: git_hash MUST see a dirty tree.
#
# INVARIANT (not a smoke test): the stamp must differ between a clean tree and a dirty one.
# The pre-2026-07-17 git_hash() returned a bare HEAD hash and never looked at the working
# tree, so a run from uncommitted code stamped a commit that could not have produced it.
# Real damage: the aborted m4a_v1_counterbalanced render stamped `git_hash: 725ad42` while
# the config it rendered from did not exist at that commit. These tests fail if that
# regresses — including the UNTRACKED case, which is the one that actually bit us and which
# a `git diff HEAD`-only check would miss.
# ---------------------------------------------------------------------------

_GIT = shutil.which("git")


def _run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway git repo with exactly one commit, cwd'd into."""
    if _GIT is None:
        pytest.skip("git unavailable")
    _run("git", "init", "-q", cwd=tmp_path)
    _run("git", "config", "user.email", "t@t.t", cwd=tmp_path)
    _run("git", "config", "user.name", "t", cwd=tmp_path)
    (tmp_path / "tracked.txt").write_text("v1\n")
    _run("git", "add", "tracked.txt", cwd=tmp_path)
    _run("git", "commit", "-q", "-m", "init", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_git_hash_clean_tree_has_no_dirty_suffix(repo):
    assert git_dirty() is False
    assert not git_hash().endswith("-dirty")
    assert git_patch_sha() is None
    assert run_metadata({}, seed=0)["git_dirty"] is False


def test_git_hash_flags_modified_tracked_file(repo):
    (repo / "tracked.txt").write_text("v2\n")
    assert git_dirty() is True
    assert git_hash().endswith("-dirty")
    meta = run_metadata({}, seed=0)
    assert meta["git_dirty"] is True
    assert meta["git_patch_sha"] is not None


def test_git_hash_flags_UNTRACKED_file(repo):
    """The m4a_v1_counterbalanced case: an untracked config drove a run stamped 'clean'."""
    (repo / "new_config.yaml").write_text("n_images: 420\n")
    assert git_dirty() is True, "untracked file must count as dirty — this is the real bug"
    assert git_hash().endswith("-dirty")
    assert run_metadata({}, seed=0)["git_patch_sha"] is not None


def test_clean_and_dirty_stamps_differ(repo):
    """The invariant that matters: the stamp must actually distinguish the two states."""
    clean = git_hash()
    (repo / "tracked.txt").write_text("v2\n")
    dirty = git_hash()
    assert clean != dirty


def test_patch_sha_is_stable_and_content_sensitive(repo):
    """Same dirty state -> same sha (identifiable); different delta -> different sha."""
    (repo / "tracked.txt").write_text("v2\n")
    a, b = git_patch_sha(), git_patch_sha()
    assert a == b
    (repo / "tracked.txt").write_text("v3\n")
    assert git_patch_sha() != a


def test_git_hash_outside_a_repo_is_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # tmp_path is not a git repo
    assert git_hash() == "unknown"
    assert git_dirty() is None


def test_unresolved_env_var_raises(tmp_path, monkeypatch):
    """A forgotten `export DATA_ROOT` must FAIL, not silently write to a '${DATA_ROOT}' dir.

    os.path.expandvars leaves an unknown ${VAR} as literal text, so the whole dataset would
    land in a directory named '${DATA_ROOT}' and every check would still pass.
    """
    monkeypatch.delenv("DATA_ROOT", raising=False)
    cfg = tmp_path / "c.yaml"
    cfg.write_text("paths:\n  out: ${DATA_ROOT}/stimuli\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unresolved environment variable"):
        load_config(cfg)


def test_unresolved_env_var_can_be_allowed(tmp_path, monkeypatch):
    monkeypatch.delenv("DATA_ROOT", raising=False)
    cfg = tmp_path / "c.yaml"
    cfg.write_text("paths:\n  out: ${DATA_ROOT}/stimuli\n", encoding="utf-8")
    out = load_config(cfg, strict_env=False)
    assert out["paths"]["out"] == "${DATA_ROOT}/stimuli"


def test_empty_but_set_env_var_raises(tmp_path, monkeypatch):
    """An EMPTY var is a forgotten export too — and it defeated the guard.

    `DATA_ROOT=""` made expandvars turn "${DATA_ROOT}/external" into "/external": an absolute
    path at the filesystem root, with no `${...}` left for the unresolved-check to find. The
    guard has to look at the vars the config REFERENCES, before expansion destroys the evidence.
    """
    monkeypatch.setenv("DATA_ROOT", "")
    cfg = tmp_path / "c.yaml"
    cfg.write_text("root: ${DATA_ROOT}/external\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unset or empty"):
        load_config(cfg)


def test_unbraced_env_var_is_also_checked(tmp_path, monkeypatch):
    """`$VAR` (no braces) is advertised as supported, and expandvars leaves an unknown one as
    literal text — so `root: $NOPE/external` sailed through as the path '$NOPE/external'."""
    monkeypatch.delenv("NOPE", raising=False)
    cfg = tmp_path / "c.yaml"
    cfg.write_text("root: $NOPE/external\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unset or empty"):
        load_config(cfg)
