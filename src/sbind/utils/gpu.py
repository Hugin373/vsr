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

    gpu_index: int  # nvidia-smi reports gpu_uuid; resolved to an index by parse_compute_apps
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


def parse_uuid_map(csv_text: str) -> dict[str, int]:
    """Parse ``--query-gpu=index,uuid`` CSV into {uuid: index}."""
    out: dict[str, int] = {}
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        idx, uuid = (p.strip() for p in line.split(",", 1))
        out[uuid] = int(idx)
    return out


def parse_compute_apps(csv_text: str, uuid_to_index: dict[str, int]) -> list[ComputeApp]:
    """Parse ``--query-compute-apps=gpu_uuid,pid,used_memory,process_name`` CSV.

    nvidia-smi prints "[N/A]" (not a number) when it cannot read a field, and prints a
    no-processes notice on some driver versions — both are skipped rather than crashing the
    guard, since a guard that dies is a guard that gets bypassed.
    """
    rows: list[ComputeApp] = []
    for line in csv_text.strip().splitlines():
        line = line.strip()
        if not line or "not supported" in line.lower() or "no running" in line.lower():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        uuid, pid, used, name = parts[0], parts[1], parts[2], ",".join(parts[3:])
        if not pid.isdigit() or uuid not in uuid_to_index:
            continue
        rows.append(
            ComputeApp(
                gpu_index=uuid_to_index[uuid],
                pid=int(pid),
                used_mib=int(used) if used.isdigit() else 0,
                process_name=name,
            )
        )
    return rows


def process_owner_uid(pid: int) -> int | None:
    """UID owning ``pid``, or None if the process is gone / unreadable."""
    try:
        return os.stat(f"/proc/{pid}").st_uid
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None


def foreign_compute_apps(apps: list[ComputeApp], gpu_index: int, my_uid: int) -> list[ComputeApp]:
    """Compute processes on ``gpu_index`` that belong to ANOTHER user.

    This is the half of the guard CLAUDE.md promises ("...or a foreign compute process is
    present") that was declared and never called: the guard was memory-threshold-only, so a
    freshly-started job that had not yet allocated 1 GiB was invisible and we would have
    happily claimed a GPU out from under a colleague.

    A process whose owner cannot be determined is treated as foreign — fail safe on a shared
    machine.
    """
    out = []
    for a in apps:
        if a.gpu_index != gpu_index:
            continue
        uid = process_owner_uid(a.pid)
        if uid != my_uid:  # includes uid is None (unreadable -> assume someone else's)
            out.append(a)
    return out


def is_occupied(info: GpuInfo, mem_threshold_mib: int = DEFAULT_MEM_THRESHOLD_MIB) -> bool:
    """True if the GPU's resident memory exceeds the threshold."""
    return info.mem_used_mib > mem_threshold_mib


# --- subprocess boundary ------------------------------------------------------------


def _nvidia_smi(*args: str) -> str:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        raise NvidiaSmiUnavailable(
            "nvidia-smi not found on PATH. The GPU guard only runs on a GPU host; "
            "run extraction/intervention scripts on the server, not a laptop."
        )
    proc = subprocess.run(
        [exe, *args, "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def gpu_status() -> list[GpuInfo]:
    """Live snapshot of every visible GPU. Raises NvidiaSmiUnavailable off a GPU host."""
    query = "--query-gpu=index,memory.used,memory.total,utilization.gpu"
    return parse_gpu_query(_nvidia_smi(query))


def compute_apps() -> list[ComputeApp]:
    """Live snapshot of every compute process across all GPUs."""
    uuid_map = parse_uuid_map(_nvidia_smi("--query-gpu=index,uuid"))
    return parse_compute_apps(
        _nvidia_smi("--query-compute-apps=gpu_uuid,pid,used_memory,process_name"), uuid_map
    )


# --- the guard ----------------------------------------------------------------------


def claim_gpu(
    gpu_index: int,
    mem_threshold_mib: int = DEFAULT_MEM_THRESHOLD_MIB,
    allow_occupied: bool = False,
    _status_fn=gpu_status,
    _apps_fn=compute_apps,
    _uid_fn=os.getuid,
) -> int:
    """Reserve exactly one GPU for this process, aborting if another user holds it.

    Two independent occupancy tests, per CLAUDE.md — memory above the threshold, **or a
    foreign compute process present**. The second one existed only as a dataclass until the
    M3 audit: the guard was memory-only, so a colleague's job that had not yet allocated
    1 GiB was invisible to it.

    On success sets ``CUDA_VISIBLE_DEVICES`` to ``gpu_index`` and returns it. MUST be
    called before torch initializes CUDA — afterwards the visible-device mask is fixed.

    Args:
        gpu_index: physical device index the user passed via ``--gpu``.
        mem_threshold_mib: occupancy threshold; from config (gpu.mem_threshold_mib).
        allow_occupied: escape hatch (e.g. your own earlier process). Off by default.
        _status_fn, _apps_fn, _uid_fn: injection points for tests; not for production code.

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

    # Second test: someone else's compute process on this device, at ANY memory footprint.
    if not allow_occupied:
        foreign = foreign_compute_apps(_apps_fn(), gpu_index, _uid_fn())
        if foreign:
            detail = "; ".join(
                f"pid {a.pid} ({a.process_name}, {a.used_mib} MiB)" for a in foreign[:4]
            )
            raise GpuOccupiedError(
                f"GPU {gpu_index} has {len(foreign)} compute process(es) belonging to another "
                f"user: {detail}. This is a shared server — pick a free GPU or coordinate. "
                f"(Memory used is only {info.mem_used_mib} MiB, below the "
                f"{mem_threshold_mib} MiB threshold, so the memory check alone would have "
                f"missed this.)"
            )

    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_index)
    return gpu_index
