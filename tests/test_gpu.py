"""GPU guard: pure parsing + the occupied-abort decision, testable without a GPU."""

import pytest

from sbind.utils import gpu
from sbind.utils.gpu import (
    GpuError,
    GpuInfo,
    GpuOccupiedError,
    claim_gpu,
    is_occupied,
    parse_gpu_query,
)

# A realistic nvidia-smi CSV (mirrors plant-ai06: 8x A6000 48GB, GPUs 5 & 7 busy).
SAMPLE = """
0, 486, 49140, 0
1, 4, 49140, 0
5, 42990, 49140, 0
7, 17288, 49140, 0
"""


def test_parse_gpu_query():
    rows = parse_gpu_query(SAMPLE)
    assert [r.index for r in rows] == [0, 1, 5, 7]
    assert rows[2] == GpuInfo(index=5, mem_used_mib=42990, mem_total_mib=49140, util_pct=0)


def test_parse_rejects_malformed():
    with pytest.raises(ValueError):
        parse_gpu_query("0, 486, 49140\n")  # only 3 fields


def test_is_occupied_threshold():
    free = GpuInfo(index=1, mem_used_mib=4, mem_total_mib=49140, util_pct=0)
    small_resident = GpuInfo(index=0, mem_used_mib=486, mem_total_mib=49140, util_pct=0)
    busy = GpuInfo(index=5, mem_used_mib=42990, mem_total_mib=49140, util_pct=0)
    assert not is_occupied(free)
    assert not is_occupied(small_resident)  # 486 MiB < 1024 default -> not occupied
    assert is_occupied(busy)
    # threshold is configurable: a strict 100 MiB threshold flags the idle resident
    assert is_occupied(small_resident, mem_threshold_mib=100)


def _fake_status():
    return parse_gpu_query(SAMPLE)


def test_claim_free_gpu_sets_env(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    idx = claim_gpu(1, _status_fn=_fake_status)
    assert idx == 1
    import os

    assert os.environ["CUDA_VISIBLE_DEVICES"] == "1"


def test_claim_occupied_gpu_aborts(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    with pytest.raises(GpuOccupiedError) as exc:
        claim_gpu(5, _status_fn=_fake_status)
    # abort message is actionable
    assert "occupied" in str(exc.value).lower()
    assert "42990" in str(exc.value)
    # and it must NOT have claimed the device
    import os

    assert os.environ.get("CUDA_VISIBLE_DEVICES") != "5"


def test_claim_occupied_with_override(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    idx = claim_gpu(5, allow_occupied=True, _status_fn=_fake_status)
    assert idx == 5


def test_claim_nonexistent_gpu(monkeypatch):
    with pytest.raises(GpuError) as exc:
        claim_gpu(9, _status_fn=_fake_status)
    assert "does not exist" in str(exc.value)


def test_gpu_status_off_host_raises(monkeypatch):
    # Simulate a laptop: nvidia-smi not on PATH.
    monkeypatch.setattr(gpu.shutil, "which", lambda _: None)
    with pytest.raises(gpu.NvidiaSmiUnavailable):
        gpu.gpu_status()
