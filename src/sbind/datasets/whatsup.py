"""What'sUp (amitakamath/whatsup_vlms, MIT) — qualitative positive control.

Controlled images of one object in a known relation to another, with FOUR caption options
that differ only in the spatial preposition ("A mug ON a table" / "UNDER" / "LEFT OF" /
"RIGHT OF"). This is our qualitative positive control: the relation type that Kang-style
coarse binding is expected to survive. Adapted with attribution (MIT).

Two subsets, per the authors' own loader:
  A — real photographs        (controlled_images_dataset.json + controlled_images/)
  B — CLEVR renders           (controlled_clevr_dataset.json  + controlled_clevr/)

Upstream convention, confirmed in their README: **the FIRST caption option is the correct
one**. Annotation image paths are prefixed "data/", which is the layout of THEIR repo, not
ours, so we strip it and re-anchor to our download root.

Hosted on Google Drive (not HF) — hence gdown. NB the same upstream file also contains
gdown ids for VG_Relation / VG_Attribution; those are inherited ARO datasets, NOT What'sUp.

TODO(M3): the COCO-spatial and GQA-spatial subsets are not loaded here — they reference
the COCO and GQA image corpora (~20 GB) which do not ship with What'sUp. M3 downloads COCO
anyway for the Kang reproduction (COCO-Spatial); once it is on disk, add those subsets
here.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterator
from pathlib import Path

from ..utils.logging import get_logger
from .base import Item, dataset_root, register

log = get_logger("sbind.whatsup")

# subset -> (annotation json, image dir)
SUBSETS = {
    "A": ("controlled_images_dataset.json", "controlled_images"),
    "B": ("controlled_clevr_dataset.json", "controlled_clevr"),
}

DEFERRED_SUBSETS = ("coco_spatial", "gqa_spatial")  # need COCO/GQA corpora — see TODO(M3)

QUESTION = "Which caption correctly describes the spatial relation in the image?"


@register("whatsup")
def load_whatsup(
    config: dict, subset: str | None = None, shuffle_options: bool = True
) -> Iterator[Item]:
    """Yield What'sUp items. ``subset`` in {'A', 'B'}; default: both.

    ⚠ OPTIONS ARE SHUFFLED BY DEFAULT, and this is load-bearing. Upstream puts the correct
    caption FIRST in every one of the 820 items (verified against the relation encoded in each
    image filename: 718/718 agree — the convention is real). If we hand a scorer
    ``meta.options`` in that order, a model with a mere A-bias scores 100% and What'sUp — our
    *qualitative positive control* — passes for entirely the wrong reason.

    So we apply a per-item seeded permutation and record the true position in
    ``meta.answer_index``. The original order is kept in ``meta.options_upstream``. Set
    ``shuffle_options=False`` only to inspect the raw upstream order. The seed is
    config-driven (``datasets.whatsup.option_seed``, else the top-level ``seed``, else 0), so
    the permutation is reproducible.
    """
    if subset in DEFERRED_SUBSETS:
        raise NotImplementedError(
            f"{subset!r} needs the COCO/GQA image corpora, which M3 downloads for the Kang "
            f"reproduction. See the TODO in this module."
        )

    root = dataset_root(config, "whatsup")
    wanted = [subset] if subset else list(SUBSETS)
    entry = (config.get("datasets") or {}).get("whatsup", {})
    seed = int(entry.get("option_seed", config.get("seed", 0)))

    for sub in wanted:
        ann_name, img_dirname = SUBSETS[sub]
        ann_path = root / ann_name
        if not ann_path.exists():
            raise FileNotFoundError(
                f"{ann_path} missing. Run: uv run --extra analysis "
                f"scripts/download_dataset.py --name whatsup"
            )
        with open(ann_path, encoding="utf-8") as f:
            records = json.load(f)

        yielded = 0
        no_path = 0
        no_image = 0
        for i, rec in enumerate(records):
            raw = str(rec.get("image_path", ""))
            if not raw:
                no_path += 1  # counted, never a silent shrink
                continue
            # upstream paths look like "data/controlled_images/beer-bottle_on_armchair.jpeg"
            name = Path(raw).name
            img_path = root / img_dirname / name
            if not img_path.exists():
                no_image += 1
                continue

            upstream = list(rec.get("caption_options") or [])
            answer = upstream[0] if upstream else ""  # upstream: first option is the correct one

            options = list(upstream)
            if shuffle_options and options:
                # seeded on a string -> reproducible regardless of PYTHONHASHSEED
                random.Random(f"{seed}:{sub}:{i}").shuffle(options)
            answer_index = options.index(answer) if answer in options else -1

            yielded += 1
            yield Item(
                id=f"whatsup/{sub}/{i}",
                images=[str(img_path)],
                question=QUESTION,
                answer=answer,
                meta={
                    "dataset_name": "whatsup",
                    "answer_type": "mcq",
                    "options": options,  # shuffled — see the docstring
                    "options_upstream": upstream,  # original order (correct caption first)
                    "answer_text": answer,
                    "answer_index": answer_index,  # position in the SHUFFLED list
                    "options_shuffled": bool(shuffle_options),
                    "option_seed": seed,
                    "subset": sub,
                    "subset_kind": "real_photo" if sub == "A" else "clevr_render",
                    "synthesized_question": True,  # caption-choice task, not native VQA
                    "original_index": i,
                    "image_name": name,
                },
            )

        # An empty subset is a broken layout assumption, not an empty dataset — fail loudly.
        if yielded == 0:
            raise RuntimeError(
                f"whatsup/{sub}: resolved 0 of {len(records)} records to images under "
                f"{root / img_dirname} ({no_path} without a path, {no_image} without an image "
                f"file). The on-disk layout is not what the adapter expects."
            )
        if no_path or no_image:
            log.warning(
                "whatsup/%s: skipped %d records with no image_path and %d whose image file is "
                "missing (%d of %d yielded)",
                sub, no_path, no_image, yielded, len(records),
            )
