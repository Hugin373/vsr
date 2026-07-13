"""CausalSpatial (Mwxinnn/CausalSpatial, MIT) — simulation-level validation layer.

Five subsets with TWO different schemas, which the adapter normalises:

  collision / physics / compatibility / occlusion
      no ``options`` column; the choices are inline in the question text
      ("... A. Yes; B. No; C. Not Sure.") and ``answer`` is a LETTER. A ``not_sure``
      column names the abstain letter.
  realworld
      an explicit ``options`` list and ``answer`` holding the option TEXT.

Both end up with ``meta.options`` (a list), ``meta.answer_letter`` and ``meta.answer_text``
populated, so a downstream scorer never has to know which subset it came from.
``meta.not_sure_letter`` marks the abstain option where one exists — a scorer should treat
it as a non-answer, not as a wrong answer.

⚠ THE UPSTREAM `id` IS NOT UNIQUE. The card calls it a "Unique sample identifier", but the
`collision` subset holds 826 samples = TWO question types over the SAME 413 scenes ("will
the car collide?" and "which object should be removed to prevent it?"), and BOTH reuse the
same id string (`Collision_Level_1_3` appears twice, with different questions and different
answers, in different shard groups). We therefore key Item.id by (subset, source file, id)
so it stays unique and joins back to the exact source row; the upstream id is preserved in
``meta.original_index`` and the file in ``meta.source_file``.

Images are embedded as parquet bytes; they are extracted to <root>/images/ on first access.
Because the id is not unique, the extracted image is keyed by the source file too — the two
question types share a scene image but must not overwrite each other's file.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from .base import Item, dataset_root, materialize_image, register

SUBSETS = ("collision", "physics", "compatibility", "occlusion", "realworld")
_LETTERS = "ABCDEFGH"

# " A. Yes; B. No; C. Not Sure." -> [(letter, text), ...]
_INLINE_OPT_RE = re.compile(r"(?:^|[\s;])([A-H])\.\s*([^;.]+)")


def _parse_inline_options(question: str) -> dict[str, str]:
    """Recover {letter: text} from choices written into the question body."""
    tail = question[-200:]  # options sit at the end; avoid matching prose earlier on
    return {m.group(1): m.group(2).strip() for m in _INLINE_OPT_RE.finditer(tail)}


def _normalise(row: dict) -> tuple[list[str], str | None, str | None]:
    """Return (options, answer_letter, answer_text) for either schema."""
    raw_answer = str(row.get("answer") or "").strip()
    explicit = list(row.get("options") or [])

    if explicit:  # realworld: answer is the option TEXT
        letter = (
            _LETTERS[explicit.index(raw_answer)]
            if raw_answer in explicit and explicit.index(raw_answer) < len(_LETTERS)
            else None
        )
        return explicit, letter, raw_answer

    # sim subsets: options inline in the question, answer is a LETTER
    by_letter = _parse_inline_options(str(row.get("question") or ""))
    options = [by_letter[k] for k in sorted(by_letter)]
    return options, (raw_answer or None), by_letter.get(raw_answer)


@register("causalspatial")
def load_causalspatial(config: dict, subsets: list[str] | None = None) -> Iterator[Item]:
    """Yield CausalSpatial items across ``subsets`` (default: all five)."""
    import pyarrow.parquet as pq

    root = dataset_root(config, "causalspatial")
    img_dir = root / "images"
    wanted = subsets or list(SUBSETS)

    for subset in wanted:
        sub_dir = root / subset
        if not sub_dir.exists():
            raise FileNotFoundError(
                f"{sub_dir} missing. Run: uv run --extra analysis "
                f"scripts/download_dataset.py --name causalspatial"
            )
        for pfile in sorted(sub_dir.glob("*.parquet")):
            shard = pfile.stem  # disambiguates the reused upstream ids (see module docstring)
            pf = pq.ParquetFile(pfile)
            for batch in pf.iter_batches(batch_size=32):
                for row in batch.to_pylist():
                    rid = row["id"]
                    options, letter, text = _normalise(row)
                    img_path = materialize_image(
                        row["image"]["bytes"], img_dir / subset / shard / f"{rid}.png"
                    )
                    yield Item(
                        id=f"causalspatial/{subset}/{shard}/{rid}",
                        images=[img_path],
                        question=row["question"],
                        answer=str(row.get("answer")),
                        meta={
                            "dataset_name": "causalspatial",
                            "answer_type": "mcq",
                            "options": options,
                            "answer_letter": letter,
                            "answer_text": text,
                            # abstain option — a scorer must not count it as a wrong answer
                            "not_sure_letter": row.get("not_sure"),
                            "task": row.get("type") or subset,
                            "subset": subset,
                            "source_file": pfile.name,
                            "original_index": rid,  # NOT unique upstream — see docstring
                        },
                    )
