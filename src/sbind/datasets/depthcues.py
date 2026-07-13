"""DepthCues (danier97/depthcues) — encoder-level depth-cue PROBING reference.

⚠ This is NOT a VQA benchmark. It ships raw probe targets (an image, a red/green object
mask pair, and a label), designed for training linear probes on encoder features. There is
no natural question/answer text. So:
  * ``answer``  = the raw label rendered as a string (the probe target).
  * ``meta.label`` = the raw structured label — THIS is what consumers should use.
  * ``question`` = a prompt WE synthesize to describe the cue task. It is our wording, not
    the dataset's; do not treat it as an official DepthCues prompt.

Subsets and their schemas differ (elevation: a 2-vector regression target; occlusion/size/
texturegrad/lightshadow: binary targets plus object masks), so image paths are resolved by
trying the known layouts rather than assuming one.

Perspective subset is SKIPPED: its zip on the hub is empty (annotations only) and the
images must be fetched from the original vanishing-point project. TODO(M2+): fetch from
https://zihan-z.github.io/projects/vpdetection/ and drop ava/ + flickr/ into
perspective_v1/images/ if we ever need that cue.

LICENSE/TERMS: the HF card sets no license field and defers to the per-source terms of the
underlying corpora (an HLW_LICENSE.txt ships with the data); the derived annotations are
non-commercial research use. That is compatible with this project. The DepthCues CODE is
MIT and may be adapted with attribution.
"""

from __future__ import annotations

import pickle
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .base import Item, dataset_root, register

# cue -> (annotation file stem per split, synthesized question, answer type)
CUES: dict[str, dict[str, Any]] = {
    "elevation_v1": {
        "files": {"test": ["test_data.pkl"], "train": ["train_data.pkl"], "val": ["val_data.pkl"]},
        "question": "In this scene, what is the ground-plane elevation direction?",
        "answer_type": "regression",
    },
    "lightshadow_v1": {
        "files": {
            "test": ["test_annotations.pkl"],
            "train": ["train_annotations.pkl"],
            "val": ["val_annotations.pkl"],
        },
        "question": "Do the red-marked object and the green-marked shadow belong together?",
        "answer_type": "binary",
    },
    "occlusion_v4": {
        "files": {"test": ["test_data.pkl"], "train": ["train_data.pkl"], "val": ["val_data.pkl"]},
        "question": "Is the red-masked object occluded by the other object?",
        "answer_type": "binary",
    },
    "size_v2": {
        "files": {
            "test": ["test_data_indoor.pkl", "test_data_outdoor.pkl"],
            "train": ["train_data_indoor.pkl", "train_data_outdoor.pkl"],
            "val": ["val_data_indoor.pkl", "val_data_outdoor.pkl"],
        },
        "question": "Which highlighted object is physically larger, the red one or the green one?",
        "answer_type": "binary",
    },
    "texturegrad_v1": {
        "files": {"test": ["test_data.pkl"], "train": ["train_data.pkl"], "val": ["val_data.pkl"]},
        "question": "Which highlighted region is farther away, judging by texture gradient?",
        "answer_type": "binary",
    },
}


def _resolve_image(cue_dir: Path, fname: str, source: str | None) -> str | None:
    """Find the image on disk. Layouts differ per cue, so try the known candidates."""
    if not fname:
        return None
    name = str(fname)
    candidates = [
        cue_dir / name,
        cue_dir / "images" / name,
        cue_dir / f"images_{source}" / name if source else None,
        cue_dir / "images_indoor" / name,
        cue_dir / "images_outdoor" / name,
        cue_dir / "images_BSDS" / name,
        cue_dir / "images_COCO" / name,
    ]
    # lightshadow stores a full relative path like "gen_datasets/<cue>/images/test/x.png"
    parts = Path(name).parts
    if "images" in parts:
        tail = Path(*parts[parts.index("images") :])
        candidates.append(cue_dir / tail)
    for c in candidates:
        if c is not None and c.exists():
            return str(c)
    return None


def _records(path: Path) -> list[tuple[str, dict]]:
    """Normalise both storage shapes (list-of-dicts, dict-of-dicts) to (key, record)."""
    with open(path, "rb") as f:
        data = pickle.load(f)
    if isinstance(data, dict):
        return [(str(k), v) for k, v in data.items()]
    return [(str(i), r) for i, r in enumerate(data)]


@register("depthcues")
def load_depthcues(
    config: dict, split: str = "test", cues: list[str] | None = None
) -> Iterator[Item]:
    """Yield DepthCues probe items. ``cues`` defaults to the five shipped subsets."""
    root = dataset_root(config, "depthcues")
    wanted = cues or list(CUES)

    for cue in wanted:
        spec = CUES[cue]
        cue_dir = root / cue
        if not cue_dir.exists():
            raise FileNotFoundError(
                f"{cue_dir} missing. Run: uv run --extra analysis "
                f"scripts/download_dataset.py --name depthcues"
            )
        for fname in spec["files"].get(split, []):
            ann_path = cue_dir / fname
            if not ann_path.exists():
                continue
            for key, rec in _records(ann_path):
                img_name = rec.get("fname") or rec.get("img_fname")
                img = _resolve_image(cue_dir, img_name, rec.get("source"))
                if img is None:
                    continue  # image not on disk (e.g. an external-source subset)
                label = rec.get("label", rec.get("class"))
                meta = {
                    "dataset_name": "depthcues",
                    "answer_type": spec["answer_type"],
                    "cue": cue,
                    "split": split,
                    "label": label.tolist() if hasattr(label, "tolist") else label,
                    "synthesized_question": True,  # the prompt is OURS, not DepthCues'
                    "original_index": key,
                    "source_file": fname,
                }
                # carry the cue-specific extras a probe may need, minus the bulky masks
                for k, v in rec.items():
                    if k in ("fname", "img_fname", "label", "class"):
                        continue
                    if "mask" in k:
                        meta[f"{k}_present"] = v is not None
                        continue
                    meta[k] = v.tolist() if hasattr(v, "tolist") else v
                yield Item(
                    id=f"depthcues/{cue}/{key}",
                    images=[img],
                    question=spec["question"],
                    answer=str(meta["label"]),
                    meta=meta,
                )
