"""MindCube (MLL-Lab/MindCube, MIT) — multi-view spatial reasoning validation layer.

~21k questions. Each item shows ONE object from several viewpoints (front/left/back/right)
and asks a spatial question from a given viewpoint — so ``images`` genuinely holds multiple
paths (this is the dataset that forced the list-valued interface).

Options are inline in the question text ("... A. TV B. Wooden dining table ..."), and the
answer ships as a bare letter, so we parse the options out into ``meta.options`` and
resolve ``meta.answer_text``.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from ..utils.io import read_jsonl
from .base import Item, dataset_root, register

# " A. foo B. bar C. baz D. qux" -> [(letter, text), ...]
_OPT_RE = re.compile(r"(?:^|\s)([A-H])\.\s*([^A-H]*?)(?=\s+[A-H]\.\s|\s*$)")

SPLITS = {
    "tinybench": "MindCube_tinybench.jsonl",
    "test": "MindCube.jsonl",
    "train": "MindCube_train.jsonl",
}


def _parse_options(question: str) -> tuple[str, list[str], dict[str, str]]:
    """Split an inline-MCQ question into (stem, options, letter->text)."""
    matches = list(_OPT_RE.finditer(question))
    if not matches:
        return question, [], {}
    stem = question[: matches[0].start()].strip()
    by_letter = {m.group(1): m.group(2).strip() for m in matches}
    return stem, [by_letter[k] for k in sorted(by_letter)], by_letter


@register("mindcube")
def load_mindcube(config: dict, split: str = "tinybench") -> Iterator[Item]:
    """Yield MindCube items. ``split`` in {tinybench, test, train}."""
    root = dataset_root(config, "mindcube")
    data_dir = root / "data"
    jsonl = data_dir / "raw" / SPLITS.get(split, SPLITS["tinybench"])
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
