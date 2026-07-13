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
from collections.abc import Iterator
from pathlib import Path

from .base import Item, dataset_root, register

# subset -> (annotation json, image dir)
SUBSETS = {
    "A": ("controlled_images_dataset.json", "controlled_images"),
    "B": ("controlled_clevr_dataset.json", "controlled_clevr"),
}

DEFERRED_SUBSETS = ("coco_spatial", "gqa_spatial")  # need COCO/GQA corpora — see TODO(M3)

QUESTION = "Which caption correctly describes the spatial relation in the image?"


@register("whatsup")
def load_whatsup(config: dict, subset: str | None = None) -> Iterator[Item]:
    """Yield What'sUp items. ``subset`` in {'A', 'B'}; default: both."""
    if subset in DEFERRED_SUBSETS:
        raise NotImplementedError(
            f"{subset!r} needs the COCO/GQA image corpora, which M3 downloads for the Kang "
            f"reproduction. See the TODO in this module."
        )

    root = dataset_root(config, "whatsup")
    wanted = [subset] if subset else list(SUBSETS)

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

        for i, rec in enumerate(records):
            raw = str(rec.get("image_path", ""))
            if not raw:
                continue
            # upstream paths look like "data/controlled_images/beer-bottle_on_armchair.jpeg"
            name = Path(raw).name
            img_path = root / img_dirname / name
            if not img_path.exists():
                continue
            options = list(rec.get("caption_options") or [])
            answer = options[0] if options else ""  # first option is the correct caption
            yield Item(
                id=f"whatsup/{sub}/{i}",
                images=[str(img_path)],
                question=QUESTION,
                answer=answer,
                meta={
                    "dataset_name": "whatsup",
                    "answer_type": "mcq",
                    "options": options,
                    "answer_text": answer,
                    "answer_index": 0,  # upstream guarantees the first option is correct
                    "subset": sub,
                    "subset_kind": "real_photo" if sub == "A" else "clevr_render",
                    "synthesized_question": True,  # caption-choice task, not native VQA
                    "original_index": i,
                    "image_name": name,
                },
            )
