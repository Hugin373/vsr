"""Smoke-test contact sheet: load N items from a dataset and render them to HTML.

Usage:
    uv run --extra analysis scripts/dataset_contact_sheet.py --name cvbench --n 5
    uv run --extra analysis scripts/dataset_contact_sheet.py --all --n 5

Prints each item's QUESTION and ANSWER under its image(s). That pairing is the whole point
of the eyeball check: a silently mis-joined annotation (right image, wrong question) is the
failure mode a schema test cannot catch.

Images are embedded as base64 so the HTML is a single self-contained file.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import sys
import traceback
from pathlib import Path

from sbind.datasets import load, take
from sbind.datasets.base import decode_frames
from sbind.utils.config import load_config
from sbind.utils.io import ensure_dir
from sbind.utils.logging import get_logger

log = get_logger("sbind.contactsheet")

ALL = ["cvbench", "mindcube", "causalspatial", "depthcues", "revsi", "whatsup"]
MAX_IMAGES_PER_ITEM = 4  # multi-view / video items: show at most this many


def _thumb_b64(path_or_img, max_px: int = 320) -> str | None:
    from PIL import Image

    try:
        im = path_or_img if hasattr(path_or_img, "convert") else Image.open(path_or_img)
        im = im.convert("RGB")
        im.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:  # noqa: BLE001
        log.warning("thumbnail failed for %s: %s", path_or_img, e)
        return None


def _item_images(item):
    """Paths for image items; lazily-decoded frames for video items."""
    if item.video and item.frame_indices:
        idx = item.frame_indices[:MAX_IMAGES_PER_ITEM]
        return decode_frames(item.video, idx), [f"frame {i}" for i in idx]
    paths = item.images[:MAX_IMAGES_PER_ITEM]
    return paths, [Path(p).name for p in paths]


def render_dataset(name: str, config: dict, n: int) -> str:
    items = take(load(name, config), n)
    if not items:
        return f"<h2>{html.escape(name)}</h2><p class='err'>no items returned</p>"

    parts = [f"<h2>{html.escape(name)} <span class='n'>({len(items)} items)</span></h2>"]
    for it in items:
        imgs, labels = _item_images(it)
        cells = []
        for img, lab in zip(imgs, labels, strict=False):
            b64 = _thumb_b64(img)
            if b64:
                cells.append(
                    f"<figure><img src='data:image/jpeg;base64,{b64}'/>"
                    f"<figcaption>{html.escape(str(lab))}</figcaption></figure>"
                )
            else:
                cells.append(f"<figure class='missing'>missing: {html.escape(str(lab))}</figure>")
        opts = it.meta.get("options")
        opts_html = (
            f"<div class='opts'>options: {html.escape(', '.join(map(str, opts)))}</div>"
            if opts
            else ""
        )
        extra = f"{it.meta.get('task') or ''} {it.meta.get('answer_type') or ''}".strip()
        parts.append(
            "<div class='item'>"
            f"<div class='imgs'>{''.join(cells)}</div>"
            f"<div class='qa'>"
            f"<div class='id'>{html.escape(it.id)}"
            + (f" <span class='tag'>{html.escape(extra)}</span>" if extra else "")
            + "</div>"
            f"<div class='q'><b>Q:</b> {html.escape(str(it.question))}</div>"
            f"<div class='a'><b>A:</b> {html.escape(str(it.answer))}"
            + (
                f" <span class='at'>({html.escape(str(it.meta['answer_text']))})</span>"
                if it.meta.get("answer_text")
                else ""
            )
            + "</div>"
            f"{opts_html}"
            "</div></div>"
        )
    return "\n".join(parts)


CSS = """
body{font-family:system-ui,sans-serif;margin:24px;background:#fafafa;color:#111}
h1{font-size:20px}
h2{font-size:17px;margin-top:28px;border-bottom:2px solid #ddd;padding-bottom:4px}
.n{color:#888;font-weight:400;font-size:13px}
.item{display:flex;gap:16px;align-items:flex-start;background:#fff;border:1px solid #e2e2e2;
      border-radius:8px;padding:12px;margin:10px 0}
.imgs{display:flex;gap:8px;flex-wrap:wrap}
figure{margin:0;text-align:center} img{max-width:240px;border-radius:4px;display:block}
figcaption{font-size:10px;color:#888;margin-top:3px}
.missing{color:#b00;font-size:12px;padding:20px;border:1px dashed #b00;border-radius:4px}
.qa{flex:1;min-width:260px}
.id{font-family:ui-monospace,monospace;font-size:11px;color:#666;margin-bottom:6px}
.tag{background:#eef;border-radius:3px;padding:1px 5px;color:#446}
.q{margin:4px 0} .a{margin:4px 0;color:#063} .at{color:#888}
.opts{font-size:12px;color:#777;margin-top:4px}
.err{color:#b00}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Dataset smoke-test contact sheet.")
    ap.add_argument("--config", default="configs/datasets.yaml")
    ap.add_argument("--name")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    config = load_config(args.config)
    names = ALL if args.all else ([args.name] if args.name else [])
    if not names:
        ap.error("pass --name X or --all")

    body = []
    for name in names:
        try:
            body.append(render_dataset(name, config, args.n))
        except Exception as e:  # noqa: BLE001 - one broken adapter must not kill the sheet
            log.error("%s failed: %s", name, e)
            body.append(
                f"<h2>{html.escape(name)}</h2><pre class='err'>"
                f"{html.escape(traceback.format_exc())}</pre>"
            )

    out = Path(args.out) if args.out else Path(config["root"]) / "contact_sheets.html"
    ensure_dir(out.parent)
    out.write_text(
        f"<!doctype html><meta charset='utf-8'><title>dataset contact sheets</title>"
        f"<style>{CSS}</style><h1>External dataset contact sheets (M2 smoke test)</h1>"
        + "\n".join(body),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
