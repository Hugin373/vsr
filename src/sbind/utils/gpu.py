"""GPU guard for a shared, scheduler-less server.

Hard rule (CLAUDE.md): every GPU script requires an explicit ``--gpu N``, sets
``CUDA_VISIBLE_DEVICES`` itself, and aborts with a clear message if the target GPU is
occupied by another user. This module owns that logic.

Design: the ``nvidia-smi`` call is isolated in one thin function; all parsing and the
occupancy decision are pure functions, so the guard is fully unit-testable on a
GPU-less laptop (see tests/test_gpu.py) and also verifiable live against a real
occupied GPU.

Usage (in a GPU entrypoint, BEFORE importing torch / initializing CUDA)::

    from sbind.utils.gpu import claim_gpu
    claim_gpu(args.gpu, mem_threshold_mib=cfg["gpu"]["mem_threshold_mib"])
    import torch  # now sees exactly one device, indexed 0
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

# Default: a device is "occupied by someone else" if >1 GiB is resident. Small idle
# residents (driver/display buffers, ~a few hundred MiB) do not false-trip. Override
# per experiment via config (gpu.mem_threshold_mib).
DEFAULT_MEM_THRESHOLD_MIB = 1024


class GpuError(RuntimeError):
    """Base class for GPU-guard failures."""


class NvidiaSmiUnavailable(GpuError):
    """nvidia-smi is not on PATH (e.g. a laptop). Guard cannot run here."""


class GpuOccupiedError(GpuError):
    """The requested GPU is in use by another process above the memory threshold."""


@dataclass(frozen=True)
class GpuInfo:
    """One row of ``nvidia-smi --query-gpu`` output."""

    index: int
    mem_used_mib: int
    mem_total_mib: int
    util_pct: int


@dataclass(frozen=True)
class ComputeApp:
    """One row of ``nvidia-smi --query-compute-apps`` output."""

    gpu_index: int  # note: nvidia-smi reports gpu_uuid; we resolve to index upstream
    pid: int
    used_mib: int
    process_name: str


# --- pure parsing helpers (no subprocess; unit-tested directly) ---------------------


def parse_gpu_query(csv_text: str) -> list[GpuInfo]:
    """Parse ``--query-gpu=index,memory.used,memory.total,utilization.gpu`` CSV.

    Expects ``--format=csv,noheader,nounits``. Blank lines are ignored.
    """
    rows: list[GpuInfo] = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            raise ValueError(f"unexpected nvidia-smi row: {line!r}")
        idx, used, total, util = parts
        rows.append(
            GpuInfo(
                index=int(idx),
                mem_used_mib=int(used),
                mem_total_mib=int(total),
                util_pct=int(util),
            )
        )
    return rows


def is_occupied(info: GpuInfo, mem_threshold_mib: int = DEFAULT_MEM_THRESHOLD_MIB) -> bool:
    """True if the GPU's resident memory exceeds the threshold."""
    return info.mem_used_mib > mem_threshold_mib


# --- subprocess boundary ------------------------------------------------------------


def _run_nvidia_smi(query: str) -> str:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        raise NvidiaSmiUnavailable(
            "nvidia-smi not found on PATH. The GPU guard only runs on a GPU host; "
            "run extraction/intervention scripts on the server, not a laptop."
        )
    proc = subprocess.run(
        [exe, f"--query-gpu={query}", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def gpu_status() -> list[GpuInfo]:
    """Live snapshot of every visible GPU. Raises NvidiaSmiUnavailable off a GPU host."""
    return parse_gpu_query(_run_nvidia_smi("index,memory.used,memory.total,utilization.gpu"))


# --- the guard ----------------------------------------------------------------------


def claim_gpu(
    gpu_index: int,
    mem_threshold_mib: int = DEFAULT_MEM_THRESHOLD_MIB,
    allow_occupied: bool = False,
    _status_fn=gpu_status,
) -> int:
    """Reserve exactly one GPU for this process, aborting if another user holds it.

    On success sets ``CUDA_VISIBLE_DEVICES`` to ``gpu_index`` and returns it. MUST be
    called before torch initializes CUDA — afterwards the visible-device mask is fixed.

    Args:
        gpu_index: physical device index the user passed via ``--gpu``.
        mem_threshold_mib: occupancy threshold; from config (gpu.mem_threshold_mib).
        allow_occupied: escape hatch (e.g. your own earlier process). Off by default.
        _status_fn: injection point for tests; do not pass in production code.

    Raises:
        GpuError: if the index is out of range.
        GpuOccupiedError: if the GPU is occupied and allow_occupied is False.
        NvidiaSmiUnavailable: if not on a GPU host.
    """
    statuses = {g.index: g for g in _status_fn()}
    if gpu_index not in statuses:
        available = ", ".join(str(i) for i in sorted(statuses)) or "none"
        raise GpuError(
            f"GPU {gpu_index} does not exist on this host. Visible indices: {available}."
        )

    info = statuses[gpu_index]
    if is_occupied(info, mem_threshold_mib) and not allow_occupied:
        raise GpuOccupiedError(
            f"GPU {gpu_index} is occupied: {info.mem_used_mib} MiB / {info.mem_total_mib} "
            f"MiB used (threshold {mem_threshold_mib} MiB), util {info.util_pct}%. "
            f"This is a shared server — pick a free GPU or coordinate. "
            f"Pass allow_occupied=True only if this is your own process."
        )

    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_index)
    return gpu_index
