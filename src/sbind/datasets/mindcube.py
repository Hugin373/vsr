"""MindCube (MLL-Lab/MindCube, MIT) — multi-view spatial reasoning validation layer.

~21k questions. Each item shows ONE object from several viewpoints (front/left/back/right)
and asks a spatial question from a given viewpoint — so ``images`` genuinely holds multiple
paths (this is the dataset that forced the list-valued interface).

Options are inline in the question text ("... A. TV B. Wooden dining table ..."), and the
answer ships as a bare letter, so we parse the options out into ``meta.options`` and
resolve ``meta.answer_text``.
"""

from __future__ import annotations

from collections.abc import Iterator

from ..utils.io import read_jsonl
from ..utils.logging import get_logger
from .base import Item, dataset_root, parse_inline_options, register

log = get_logger("sbind.mindcube")

SPLITS = {
    "tinybench": "MindCube_tinybench.jsonl",
    "test": "MindCube.jsonl",
    "train": "MindCube_train.jsonl",
}


def _parse_options(question: str) -> tuple[str, list[str], dict[str, str]]:
    """Split an inline-MCQ question into (stem, options, letter->text)."""
    by_letter = parse_inline_options(question)
    if not by_letter:
        return question, [], {}
    first = question.find(" A.")
    stem = question[:first].strip() if first > 0 else question
    return stem, [by_letter[k] for k in sorted(by_letter)], by_letter


@register("mindcube")
def load_mindcube(config: dict, split: str | None = None) -> Iterator[Item]:
    """Yield MindCube items. ``split`` in {tinybench, test, train}.

    The split may be given as an argument or set in the experiment config
    (``datasets.mindcube.split``) — §2.5 requires a reported result to state it explicitly, so
    it has to be settable from a config, like ReVSI's frame budget.
    """
    root = dataset_root(config, "mindcube")
    entry = (config.get("datasets") or {}).get("mindcube", {})
    explicit = split is not None or "split" in entry
    split = split or entry.get("split") or "tinybench"

    # An UNKNOWN split must never silently degrade to the dev default: `SPLITS.get(split,
    # tinybench)` used to return tinybench's 1,050 items stamped `meta.split="val"`, so a typo
    # produced the wrong population under the right-looking label — the exact rule it was
    # supposed to enforce, inverted.
    if split not in SPLITS:
        raise KeyError(f"unknown mindcube split {split!r}. Valid: {', '.join(SPLITS)}")

    # The split is a SCIENTIFIC parameter: tinybench is 1,050 items, the full set ~21k.
    # A dev-speed default must never slip silently into a reported result.
    log.info(
        "mindcube: split=%s (%s)",
        split,
        "explicit"
        if explicit
        else "DEFAULT tinybench — set it explicitly for any reported result",
    )
    data_dir = root / "data"
    jsonl = data_dir / "raw" / SPLITS[split]
    if not jsonl.exists():
        raise FileNotFoundError(
            f"{jsonl} missing. Run: uv run --extra analysis "
            f"scripts/download_dataset.py --name mindcube"
        )

    for rec in read_jsonl(jsonl):
        images = [str(data_dir / p) for p in rec.get("images", [])]
        raw_q = rec.get("question", "")
        stem, options, by_letter = _parse_options(raw_q)
        letter = str(rec.get("gt_answer", "")).strip()
        yield Item(
            id=f"mindcube/{rec['id']}",
            images=images,
            question=raw_q,  # keep the full prompt as the model sees it
            answer=letter,
            meta={
                "dataset_name": "mindcube",
                "answer_type": "mcq",
                "options": options,
                "answer_text": by_letter.get(letter),
                "question_stem": stem,
                "category": rec.get("category"),
                "type": rec.get("type"),  # e.g. '1_frame', '4_frames'
                "meta_info": rec.get("meta_info"),
                "n_images": len(images),
                "split": split,
                "original_index": rec["id"],
            },
        )
