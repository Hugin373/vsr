"""GPU guard: pure parsing + the occupied-abort decision, testable without a GPU."""

import os

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


def _no_apps():
    """No compute processes. Injected so the guard's unit tests never touch real nvidia-smi —
    otherwise a colleague's live job on the *real* GPU 1 fails this test (it did)."""
    return []


def test_claim_free_gpu_sets_env(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    idx = claim_gpu(1, _status_fn=_fake_status, _apps_fn=_no_apps)
    assert idx == 1
    import os

    assert os.environ["CUDA_VISIBLE_DEVICES"] == "1"


def test_claim_occupied_gpu_aborts(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    with pytest.raises(GpuOccupiedError) as exc:
        claim_gpu(5, _status_fn=_fake_status, _apps_fn=_no_apps)
    # abort message is actionable
    assert "occupied" in str(exc.value).lower()
    assert "42990" in str(exc.value)
    # and it must NOT have claimed the device
    import os

    assert os.environ.get("CUDA_VISIBLE_DEVICES") != "5"


def test_claim_occupied_with_override(monkeypatch):
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    idx = claim_gpu(5, allow_occupied=True, _status_fn=_fake_status, _apps_fn=_no_apps)
    assert idx == 5


def test_claim_nonexistent_gpu(monkeypatch):
    with pytest.raises(GpuError) as exc:
        claim_gpu(9, _status_fn=_fake_status, _apps_fn=_no_apps)
    assert "does not exist" in str(exc.value)


def test_gpu_status_off_host_raises(monkeypatch):
    # Simulate a laptop: nvidia-smi not on PATH.
    monkeypatch.setattr(gpu.shutil, "which", lambda _: None)
    with pytest.raises(gpu.NvidiaSmiUnavailable):
        gpu.gpu_status()


# --- the foreign-compute-process half of the guard (was declared but never called) ---------


def _apps_csv():
    # gpu_uuid,pid,used_memory,process_name
    return "GPU-aaa, 12345, 512, python\nGPU-bbb, 999, 40000, train.py\n"


def _uuid_csv():
    return "0, GPU-aaa\n1, GPU-bbb\n"


def test_parse_compute_apps_resolves_uuid_to_index():
    apps = gpu.parse_compute_apps(_apps_csv(), gpu.parse_uuid_map(_uuid_csv()))
    assert [(a.gpu_index, a.pid, a.used_mib) for a in apps] == [(0, 12345, 512), (1, 999, 40000)]


def test_parse_compute_apps_tolerates_no_process_notices():
    """A guard that crashes is a guard that gets bypassed."""
    assert gpu.parse_compute_apps("No running processes found\n", {}) == []
    assert gpu.parse_compute_apps("", {}) == []


def test_claim_gpu_aborts_on_a_foreign_process_below_the_memory_threshold(monkeypatch):
    """The bug this closes: the guard was memory-only, so a colleague's job that had not yet
    allocated 1 GiB was INVISIBLE and we would have claimed the GPU out from under them."""
    free_gpu = [gpu.GpuInfo(index=0, mem_used_mib=200, mem_total_mib=49140, util_pct=0)]
    foreign = [gpu.ComputeApp(gpu_index=0, pid=4242, used_mib=200, process_name="theirs.py")]
    # memory alone says FREE (200 MiB < 1024 threshold)
    assert not gpu.is_occupied(free_gpu[0])
    with pytest.raises(gpu.GpuOccupiedError, match="another user"):
        claim_gpu(
            0,
            _status_fn=lambda: free_gpu,
            _apps_fn=lambda: foreign,
            _uid_fn=lambda: 1000,  # us
        )


def test_claim_gpu_allows_our_own_process(monkeypatch):
    free_gpu = [gpu.GpuInfo(index=0, mem_used_mib=200, mem_total_mib=49140, util_pct=0)]
    mine = [gpu.ComputeApp(gpu_index=0, pid=4242, used_mib=200, process_name="mine.py")]
    monkeypatch.setattr(gpu, "process_owner_uid", lambda pid: 1000)
    claim_gpu(0, _status_fn=lambda: free_gpu, _apps_fn=lambda: mine, _uid_fn=lambda: 1000)
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "0"


def test_unreadable_process_owner_is_treated_as_foreign():
    """Fail safe on a shared machine."""
    apps = [gpu.ComputeApp(gpu_index=0, pid=999999, used_mib=10, process_name="?")]
    assert gpu.foreign_compute_apps(apps, 0, my_uid=1000) == apps
