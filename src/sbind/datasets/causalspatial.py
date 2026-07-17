"""CausalSpatial (Mwxinnn/CausalSpatial, MIT; arXiv 2601.13304) — simulation-level validation layer.

⚠ THE SUBSET NAMES BELOW ARE THE REPO'S FOLDER NAMES, **NOT THE PAPER'S TAXONOMY.**
The paper's categories are **Collision / Occlusion / Compatibility / TRAJECTORY**; ``physics`` and
``realworld`` appear nowhere in it. Verified 2026-07-17 by reading the items, not by inferring the
mapping: every ``physics`` question is trajectory prediction ("based on the soccer ball's
trajectory, will it go into the goal?"; "if the billiard ball moves along the red arrow, will any
ball score?"). So **``physics`` == the paper's Trajectory category.** This matters beyond naming:
our docs had written ``physics`` off as "loads on physics priors, not spatial primitives → a
non-target control" — a scientific judgment made against a *directory name*. Trajectory is
predicted future position from a current spatial configuration (stage S4-C territory).
``SUBSETS`` keeps the folder names because they are what is on disk; consumers must not read them
as the paper's categories.

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

⚠⚠ THE UPSTREAM `not_sure` COLUMN ALSO LIES — never pass it through. It is the constant 'C'
for all 189 occlusion rows, but occlusion mixes two question shapes: 135 genuine
"Yes / No / Not Sure" rows (3 options) and **54 rows whose four options are all semantic and
contain no abstain at all** ("C. initially not occluded, then occluded, then revealed").
**On 11 of those, C is the GOLD answer** — so a scorer obeying the column would have thrown
away the correct answer as a non-answer. ``meta.not_sure_letter`` is therefore derived by
checking the option TEXT (``_abstain_letter``); the raw claim is kept as
``meta.not_sure_upstream``. Same lesson as the id: an upstream field is a hypothesis.

⚠⚠ THE UPSTREAM `id` IS BADLY BROKEN — DO NOT KEY ANYTHING ON IT. The card calls it a
"Unique sample identifier". Measured reality:

    subset          rows   unique upstream ids
    collision        826   413   (two question types reuse one id namespace)
    physics          311     2   ('Physics_Level_1_' is repeated 192x)
    compatibility     99     2
    occlusion        189     2
    realworld        116   116   (the only sane one)

So we key Item.id on (subset, source file, ROW INDEX) — always unique, and it addresses the
exact source row. The upstream string is kept as ``meta.original_id`` (non-unique, for
reference only); ``meta.row_index`` and ``meta.source_file`` complete the provenance.

This matters beyond ids: the parquet-embedded images are extracted to <root>/images/, and
keying those filenames on the upstream id silently OVERWROTE them — 1541 items produced only
949 image files, so most physics/compatibility/occlusion items pointed at an image belonging
to a different question. Extraction is now keyed by row index too.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from ..utils.logging import get_logger
from .base import Item, dataset_root, materialize_image, parse_inline_options, register

log = get_logger("sbind.causalspatial")

SUBSETS = ("collision", "physics", "compatibility", "occlusion", "realworld")
_LETTERS = "ABCDEFGH"

# What an abstain option actually reads like. Needed because the upstream `not_sure` column is
# a CLAIM about which letter abstains, and the claim is false for 54 rows — see _abstain_letter.
_ABSTAIN_RE = re.compile(r"\bnot\s*sure\b|\bunsure\b|\bcannot\s+(?:be\s+)?determined?\b", re.I)


def _abstain_letter(options: list[str], upstream: object) -> str | None:
    """Which option (if any) is the abstain — verified against the option TEXT, not trusted.

    ⚠ The upstream ``not_sure`` column is the constant ``'C'`` for ALL 189 occlusion rows, but
    occlusion holds two question shapes: 135 genuine "Yes / No / Not Sure" rows, and 54 rows
    whose FOUR options are all semantic with no abstain at all ("C. initially not occluded,
    then occluded, then revealed"). For 11 of those, C is the GOLD answer — so honouring the
    column blindly told a scorer to discard the correct answer as a non-answer.

    So the column is a hypothesis: accept it only when the option it names really reads like
    an abstain.
    """
    letter = str(upstream or "").strip() or None
    if letter is None or letter not in _LETTERS:
        return None
    idx = _LETTERS.index(letter)
    if 0 <= idx < len(options) and _ABSTAIN_RE.search(options[idx]):
        return letter
    return None


def _normalise(row: dict) -> tuple[list[str], str | None, str | None, bool]:
    """Return (options, answer_letter, answer_text, options_parse_ok) for either schema."""
    raw_answer = str(row.get("answer") or "").strip()
    explicit = list(row.get("options") or [])

    if explicit:  # realworld: answer is the option TEXT
        letter = (
            _LETTERS[explicit.index(raw_answer)]
            if raw_answer in explicit and explicit.index(raw_answer) < len(_LETTERS)
            else None
        )
        return explicit, letter, raw_answer, True

    # sim subsets: options inline in the question, answer is a LETTER
    by_letter = parse_inline_options(str(row.get("question") or ""))
    options = [by_letter[k] for k in sorted(by_letter)]

    # Integrity cross-check: if upstream names an abstain letter BEYOND the options we parsed,
    # the parse is incomplete and `options` is garbage — do not pass it off as a clean list.
    # (Collision_Level_2_31's question text is corrupted upstream: its "E. R" was eaten, so the
    # strict A,B,C-run parser stops at D and the last "option" is a blob holding D + E + F.)
    upstream_ns = str(row.get("not_sure") or "").strip()
    parse_ok = not (
        upstream_ns in _LETTERS and options and _LETTERS.index(upstream_ns) >= len(options)
    )
    return options, (raw_answer or None), by_letter.get(raw_answer), parse_ok


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
        suspect = 0
        for pfile in sorted(sub_dir.glob("*.parquet")):
            shard = pfile.stem
            pf = pq.ParquetFile(pfile)
            row_idx = 0
            for batch in pf.iter_batches(batch_size=32):
                for row in batch.to_pylist():
                    # row index, NOT the upstream id — see the docstring: the upstream id is
                    # duplicated (e.g. 192 physics rows share one string), and keying the
                    # extracted image on it silently overwrote most of them.
                    key = f"{row_idx:05d}"
                    options, letter, text, parse_ok = _normalise(row)
                    suspect += not parse_ok
                    img_path = materialize_image(
                        row["image"]["bytes"], img_dir / subset / shard / f"{key}.png"
                    )
                    yield Item(
                        id=f"causalspatial/{subset}/{shard}/{key}",
                        images=[img_path],
                        question=row["question"],
                        answer=str(row.get("answer")),
                        meta={
                            "dataset_name": "causalspatial",
                            "answer_type": "mcq",
                            "options": options,
                            "answer_letter": letter,
                            "answer_text": text,
                            # The abstain option, VERIFIED against the option text — never the
                            # raw upstream column, which lies on 54 rows (see _abstain_letter).
                            # A scorer must not count this as a wrong answer.
                            "not_sure_letter": _abstain_letter(options, row.get("not_sure")),
                            "not_sure_upstream": row.get("not_sure"),  # the raw claim
                            # False => the inline-option parse is provably incomplete; the
                            # option list is unreliable, so do not compute chance level from it
                            # or re-present it to a model.
                            "options_parse_ok": parse_ok,
                            "task": row.get("type") or subset,
                            "subset": subset,
                            "source_file": pfile.name,
                            "row_index": row_idx,
                            "original_id": row["id"],  # NOT unique upstream — reference only
                            "original_index": f"{shard}:{row_idx}",
                        },
                    )
                    row_idx += 1
        if suspect:
            log.warning(
                "causalspatial/%s: %d rows have upstream-corrupted option text (options_parse_ok"
                "=False) — their option lists are unreliable; exclude them from any scoring that "
                "depends on the option set.",
                subset,
                suspect,
            )
