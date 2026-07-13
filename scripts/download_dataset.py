"""Download an external benchmark into $DATA_ROOT/external/<name>/. Idempotent.

Usage:
    uv run --extra analysis scripts/download_dataset.py --name cvbench
    uv run --extra analysis scripts/download_dataset.py --all
    uv run --extra analysis scripts/download_dataset.py --name revsi --du   # report size only

HF repos are pulled with snapshot_download straight into $DATA_ROOT/external (NOT the
opaque ~/.cache HF dir — data belongs on the big disk, per CLAUDE.md). Re-running skips
files already present. Zips listed in the config are extracted once.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from sbind.utils.config import load_config
from sbind.utils.io import ensure_dir
from sbind.utils.logging import get_logger

log = get_logger("sbind.download")

# cheap/certain first, so a failure surfaces late rather than blocking the easy ones
DEFAULT_ORDER = ["cvbench", "mindcube", "causalspatial", "depthcues", "revsi", "whatsup"]


def du(path: Path) -> str:
    if not path.exists():
        return "0"
    out = subprocess.run(["du", "-sh", str(path)], capture_output=True, text=True)
    return out.stdout.split()[0] if out.stdout else "?"


def _unzip(archives: list[str], dest: Path) -> None:
    """Extract .zip and .tar.gz archives once (marker file makes it idempotent)."""
    for z in archives:
        zp = dest / z
        if not zp.exists():
            log.warning("archive not found (skipping): %s", zp)
            continue
        marker = dest / f".unzipped_{Path(z).name}"
        if marker.exists():
            log.info("already extracted: %s", z)
            continue
        log.info("extracting %s ...", z)
        if z.endswith((".tar.gz", ".tgz")):
            with tarfile.open(zp, "r:gz") as tf:
                tf.extractall(dest)
        else:
            with zipfile.ZipFile(zp) as zf:
                zf.extractall(dest)
        marker.touch()


def download_hf(repo: str, dest: Path, zips: list[str] | None) -> None:
    from huggingface_hub import snapshot_download

    ensure_dir(dest)
    log.info("snapshot_download %s -> %s", repo, dest)
    snapshot_download(repo_id=repo, repo_type="dataset", local_dir=str(dest))
    if zips:
        _unzip(zips, dest)


def download_whatsup(cfg: dict, dest: Path) -> None:
    """What'sUp is on Google Drive (MIT), not HF. Both Controlled subsets share one image zip."""
    import gdown

    ensure_dir(dest)
    for filename, file_id in (cfg.get("gdrive") or {}).items():
        target = dest / filename
        if target.exists() and target.stat().st_size > 0:
            log.info("already have %s", filename)
            continue
        log.info("gdown %s -> %s", file_id, target)
        try:
            gdown.download(id=file_id, output=str(target), quiet=True)
        except Exception as e:  # noqa: BLE001 - report and continue; adapter will surface it
            log.error("gdown failed for %s: %s", filename, e)
    _unzip(cfg.get("unzip") or [], dest)


def main() -> int:
    ap = argparse.ArgumentParser(description="Download an external benchmark.")
    ap.add_argument("--config", default="configs/datasets.yaml")
    ap.add_argument("--name", help="dataset name (see configs/datasets.yaml)")
    ap.add_argument("--all", action="store_true", help="download all, in the default order")
    ap.add_argument("--du", action="store_true", help="only report disk usage")
    args = ap.parse_args()

    config = load_config(args.config)
    root = Path(config["root"])
    entries = config["datasets"]

    names = DEFAULT_ORDER if args.all else ([args.name] if args.name else [])
    if not names:
        ap.error("pass --name X or --all")

    if args.du:
        for n in names:
            p = root / n
            print(f"  {n:16s} {du(p):>8s}  {p}")
        print(f"  {'TOTAL':16s} {du(root):>8s}")
        return 0

    for name in names:
        if name not in entries:
            log.error("unknown dataset: %s", name)
            continue
        cfg = entries[name]
        dest = root / name
        log.info("=== %s ===", name)
        if name == "whatsup":
            download_whatsup(cfg, dest)
        else:
            download_hf(cfg["hf_repo"], dest, cfg.get("unzip"))
        log.info("%s ready: %s on disk", name, du(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
