"""M2 smoke tests: every adapter loads 5 well-formed items.

Data lives outside git, so each test SKIPS when its dataset is not downloaded — the suite
stays green on a laptop. On the server (where the data is), they run for real.
"""

from pathlib import Path

import pytest

from sbind.datasets import available, load, take
from sbind.datasets.base import Item
from sbind.utils.config import load_config

DATASETS = ["cvbench", "mindcube", "causalspatial", "depthcues", "revsi", "whatsup"]


@pytest.fixture(scope="module")
def config():
    return load_config("configs/datasets.yaml")


def _skip_if_absent(config, name):
    root = Path(config["root"]) / name
    if not root.exists() or not any(root.iterdir()):
        pytest.skip(f"{name} not downloaded (run scripts/download_dataset.py --name {name})")


def test_all_adapters_registered():
    assert set(DATASETS) == set(available())


@pytest.mark.parametrize("name", DATASETS)
def test_loads_five_items(config, name):
    _skip_if_absent(config, name)
    items = take(load(name, config), 5)
    assert len(items) == 5, f"{name} yielded {len(items)} items"

    for it in items:
        assert isinstance(it, Item)
        # stable, origin-carrying id so eval results can be joined back to source
        assert it.id.startswith(f"{name}/"), it.id
        assert it.meta["dataset_name"] == name
        assert it.question, f"{name}: empty question"
        assert str(it.answer) != "", f"{name}: empty answer"
        assert it.meta.get("original_index") is not None

        # media: either real image files, or a video with frame indices
        if it.video:
            assert Path(it.video).exists(), f"{name}: video missing {it.video}"
            assert it.frame_indices, f"{name}: video item with no frame indices"
        else:
            assert it.images, f"{name}: no images"
            for p in it.images:
                assert Path(p).exists(), f"{name}: image missing {p}"


@pytest.mark.parametrize("name", DATASETS)
def test_item_round_trip(config, name):
    _skip_if_absent(config, name)
    it = take(load(name, config), 1)[0]
    assert Item.from_dict(it.to_dict()) == it


@pytest.mark.parametrize("name", DATASETS)
def test_ids_are_unique(config, name):
    """Item.id must be unique — it is the join key back to the source item.

    This test previously only covered cvbench, and so missed that CausalSpatial's upstream
    `id` is NOT unique: its `collision` subset is 826 samples = two question types over the
    same 413 scenes, and BOTH reuse the same id string with different questions/answers.
    """
    _skip_if_absent(config, name)
    ids = [it.id for it in take(load(name, config), 400)]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"{name}: duplicate ids, e.g. {sorted(dupes)[:3]}"


def test_causalspatial_collision_has_both_question_types(config):
    """The full collision subset: 826 items over 413 scenes, all ids distinct.

    Guards the specific upstream trap — two question types ("will it collide?" and "which
    object to remove?") share one id namespace.
    """
    _skip_if_absent(config, "causalspatial")
    items = list(load("causalspatial", config, subsets=["collision"]))
    assert len(items) == 826, f"expected 826 collision samples, got {len(items)}"
    assert len({it.id for it in items}) == 826, "collision ids are not unique"
    # the same upstream id is reused by the two question types
    originals = [it.meta["original_index"] for it in items]
    assert len(set(originals)) == 413, "expected 413 distinct upstream ids reused twice"


def test_mcq_answers_resolve_to_an_option(config):
    """An MCQ answer must map to one of its options — the join that silently breaks."""
    for name in ("cvbench", "causalspatial", "whatsup", "mindcube"):
        _skip_if_absent(config, name)
        for it in take(load(name, config), 5):
            if it.meta.get("answer_type") != "mcq":
                continue
            options = it.meta.get("options") or []
            if not options:
                continue
            text = it.meta.get("answer_text")
            assert text is None or text in options, f"{name}/{it.id}: answer_text not in options"


def test_revsi_decodes_frames_lazily(config):
    _skip_if_absent(config, "revsi")
    from sbind.datasets.base import decode_frames

    it = take(load("revsi", config), 1)[0]
    assert it.video and it.frame_indices
    frames = decode_frames(it.video, it.frame_indices[:3])
    assert len(frames) == 3
    assert frames[0].size[0] > 0
