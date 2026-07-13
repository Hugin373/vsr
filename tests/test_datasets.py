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


def test_causalspatial_full_scan_ids_and_images_unique(config):
    """FULL scan of CausalSpatial: every item distinct, every item its OWN image file.

    Guards two upstream traps that both caused silent corruption:
      * the upstream `id` is badly non-unique (192 physics rows share one string), so ids
        must be keyed on the row index, not on it;
      * the parquet-embedded images are extracted to disk, and keying those FILENAMES on the
        upstream id overwrote them — 1541 items previously produced only 949 image files, so
        most items pointed at another question's image.
    """
    _skip_if_absent(config, "causalspatial")
    items = list(load("causalspatial", config))

    assert len(items) == 1541, f"expected 1541 items (per the dataset card), got {len(items)}"
    assert len({it.id for it in items}) == len(items), "duplicate item ids"

    # one distinct image file per item — the invariant the overwrite bug violated
    paths = [it.images[0] for it in items]
    assert len(set(paths)) == len(items), (
        f"{len(items)} items share only {len(set(paths))} image files — extraction overwrote"
    )
    for p in set(paths):
        assert Path(p).exists()

    # collision really is two question types over one id namespace (826 = 2 x 413)
    collision = [it for it in items if it.meta["subset"] == "collision"]
    assert len(collision) == 826
    assert len({it.meta["original_id"] for it in collision}) == 413


def test_causalspatial_every_item_has_resolved_options(config):
    """Every CausalSpatial item must expose its options and a resolved answer_text.

    The sim subsets write their choices INTO the question text in two different formats
    ("A. Yes; B. No;" vs "Answer by (A) Yes, (B) No or (C) Not sure."). Parsing only one left
    three of the five subsets with options=[] and answer_text=None — an MCQ you cannot score.
    """
    _skip_if_absent(config, "causalspatial")
    bad = []
    for it in load("causalspatial", config):
        if not it.meta["options"] or it.meta["answer_text"] is None:
            bad.append((it.meta["subset"], it.id))
    assert not bad, f"{len(bad)} items without resolved options/answer_text, e.g. {bad[:3]}"


@pytest.mark.parametrize("name", DATASETS)
def test_full_integrity(config, name):
    """FULL scan of every dataset: unique ids, every media file present, every MCQ scoreable.

    This is the check that caught what the 5-item smoke test could not:
      * depthcues size_v2 loads an indoor AND an outdoor pkl, both indexed from 0 -> id clash
      * mindcube's option parser died on the "C" in "Curtain" (a naive [^A-H] char class)
      * revsi never resolved MCQ answers at all (options ship pre-lettered, answer is a letter)
    """
    _skip_if_absent(config, name)
    ids, unresolved, missing = set(), 0, 0
    n = 0
    for it in load(name, config):
        n += 1
        assert it.id not in ids, f"{name}: duplicate id {it.id}"
        ids.add(it.id)
        if it.video:
            missing += 0 if Path(it.video).exists() else 1
        for p in it.images:
            missing += 0 if Path(p).exists() else 1
        m = it.meta
        if m.get("answer_type") == "mcq" and m.get("options") and m.get("answer_text") is None:
            unresolved += 1
    assert missing == 0, f"{name}: {missing} media files referenced but missing"
    assert unresolved == 0, f"{name}: {unresolved} MCQ items whose answer resolves to no option"
    assert n > 0


@pytest.mark.parametrize("name", DATASETS)
def test_no_silent_record_drops(config, name):
    """An adapter must not silently drop source records.

    DepthCues' occlusion_v4 subset (14,862 records — the largest) resolved to ZERO items for
    a whole milestone because its images nest by split and the resolver quietly `continue`d.
    """
    _skip_if_absent(config, name)
    counts = {
        "cvbench": 2638,
        "mindcube": 1050,  # tinybench split
        "causalspatial": 1541,
        "depthcues": 19235,  # test split, all five shipped cues
        "revsi": 6158,  # 32-frame budget
        "whatsup": 820,  # 412 real photos + 408 CLEVR
    }
    got = sum(1 for _ in load(name, config))
    assert got == counts[name], f"{name}: expected {counts[name]} items, loaded {got}"


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
