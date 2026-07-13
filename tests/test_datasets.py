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
    # $DATA_ROOT unset is the normal state on a laptop, and load_config rightly REFUSES to
    # guess a path for it. That must be a skip, not 35 errors: the suite has to stay green off
    # the server. (It did not — the "skips cleanly when data is absent" claim only held if the
    # var was set to a nonexistent path.)
    try:
        return load_config("configs/datasets.yaml")
    except ValueError as e:
        pytest.skip(f"dataset config needs $DATA_ROOT exported: {e}")


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
    """An MCQ answer must map to one of its options — the join that silently breaks.

    Written to be non-vacuous: the previous version skipped items with `options == []` and
    accepted `answer_text is None`, i.e. it excused exactly the two failures it existed to
    catch. Both are now hard errors, over the FULL dataset.
    """
    for name in ("cvbench", "causalspatial", "whatsup", "mindcube"):
        _skip_if_absent(config, name)
        for it in load(name, config):
            if it.meta.get("answer_type") != "mcq":
                continue
            options = it.meta.get("options") or []
            assert options, f"{name}/{it.id}: MCQ item with an EMPTY option list"
            text = it.meta.get("answer_text")
            assert text is not None, f"{name}/{it.id}: MCQ answer resolved to nothing"
            assert text in options, f"{name}/{it.id}: answer_text {text!r} not in options"


def test_revsi_decodes_frames_lazily(config):
    _skip_if_absent(config, "revsi")
    from sbind.datasets.base import decode_frames

    it = take(load("revsi", config), 1)[0]
    assert it.video and it.frame_indices
    frames = decode_frames(it.video, it.frame_indices[:3])
    assert len(frames) == 3
    assert frames[0].size[0] > 0


def test_probe_only_datasets_are_barred_from_behavioral_claims():
    """DepthCues must never be scored as a verbalized-answer benchmark.

    Its questions are SYNTHESIZED by us and its answers are raw probe targets, so a model's
    "accuracy" on them is not a behavioral result about anything. What'sUp, by contrast, has
    a NATIVE task and answer key (pick the correct caption of 4) — only our prompt wording is
    synthesized — so it stays behavioral-safe. `meta.synthesized_question` alone is too blunt
    to separate the two; that is what this classification is for.
    """
    from sbind.datasets.base import (
        BEHAVIORAL_SAFE,
        PROBE_ONLY,
        assert_behavioral_safe,
    )

    assert PROBE_ONLY == {"depthcues"}
    assert BEHAVIORAL_SAFE == {"cvbench", "mindcube", "causalspatial", "revsi", "whatsup"}
    assert set(DATASETS) == BEHAVIORAL_SAFE | PROBE_ONLY  # every dataset is classified

    with pytest.raises(ValueError, match="PROBE_ONLY"):
        assert_behavioral_safe("depthcues")
    for name in BEHAVIORAL_SAFE:
        assert_behavioral_safe(name)  # must not raise


def test_split_and_budget_are_recorded_on_every_item(config):
    """A dev-speed default split must never slip silently into a reported result.

    MindCube's split (tinybench=1,050 vs the full ~21k) and ReVSI's frame budget are
    SCIENTIFIC parameters — ReVSI's whole point is that conclusions change with the budget.
    Both are logged at load and recorded per item so a result can always be traced to them.
    """
    _skip_if_absent(config, "mindcube")
    for it in take(load("mindcube", config), 3):
        assert it.meta["split"] == "tinybench"
    _skip_if_absent(config, "revsi")
    for it in take(load("revsi", config), 3):
        assert it.meta["frame_budget"] == "32"
    for it in take(load("revsi", config, frame_budget=16), 3):
        assert it.meta["frame_budget"] == "16"


# --- invariant tests: one per bug found in the M3 retro-audit (reports/m0_m2_audit.md) ------


def test_mindcube_unknown_split_raises_instead_of_silently_using_tinybench(config):
    """An unknown split must be an ERROR, never a silent fallback to the dev default.

    `SPLITS.get(split, tinybench)` returned tinybench's 1,050 items STAMPED with the split you
    asked for — so `split="val"` produced the wrong population under the right-looking label,
    inverting the very rule it was meant to enforce.
    """
    _skip_if_absent(config, "mindcube")
    with pytest.raises(KeyError, match="unknown mindcube split"):
        take(load("mindcube", config, split="val"), 1)

    # and a split set in the CONFIG must be honoured (§2.5: it has to be settable there)
    cfg = dict(config)
    cfg["datasets"] = dict(config.get("datasets", {}))
    cfg["datasets"]["mindcube"] = {**cfg["datasets"].get("mindcube", {}), "split": "train"}
    it = take(load("mindcube", cfg), 1)[0]
    assert it.meta["split"] == "train"


def test_causalspatial_abstain_option_really_reads_like_an_abstain(config):
    """`not_sure_letter` must name an option that IS an abstain — never the upstream claim.

    Upstream's `not_sure` column is the constant 'C' for all 189 occlusion rows, but 54 of them
    have four SEMANTIC options and no abstain at all, and on 11 of those C is the GOLD answer.
    Trusting the column told a scorer to discard the correct answer as a non-answer.
    """
    _skip_if_absent(config, "causalspatial")
    n_abstain = 0
    for it in load("causalspatial", config):
        letter = it.meta.get("not_sure_letter")
        if letter is None:
            continue
        n_abstain += 1
        options = it.meta["options"]
        idx = "ABCDEFGH".index(letter)
        assert idx < len(options), f"{it.id}: abstain letter {letter} beyond {len(options)} options"
        assert "not sure" in options[idx].lower(), (
            f"{it.id}: not_sure_letter {letter} names {options[idx]!r}, which is not an abstain"
        )
        # the gold answer must never BE the abstain we advertise
        assert it.meta["answer_letter"] != letter, f"{it.id}: gold answer is the abstain option"
    assert n_abstain > 0, "no abstain options found at all — the detector is broken"


def test_causalspatial_corrupt_option_rows_are_flagged_not_hidden(config):
    """Upstream-corrupted option text must be FLAGGED, not passed off as a clean option list.

    Collision_Level_2_31's question lost its "E. R" upstream, so the strict A,B,C-run parser
    stops at D and the last "option" is a blob holding D + E + F. Gold is 'A', so every other
    check passes. A scorer computing chance level as 1/len(options) gets it wrong.
    """
    _skip_if_absent(config, "causalspatial")
    items = list(load("causalspatial", config))
    suspect = [it for it in items if not it.meta.get("options_parse_ok", True)]
    # exactly the one known-corrupt upstream row — a golden count, so a regression moves it
    assert len(suspect) == 1, f"expected 1 corrupt-option row, found {len(suspect)}"
    assert all(it.meta["options_parse_ok"] for it in items if it not in suspect)


def test_whatsup_gold_answer_is_not_always_option_a(config):
    """The correct caption is FIRST in all 820 upstream items. If we hand a scorer that order,
    a model with a mere A-bias scores 100% and the qualitative positive control passes for the
    wrong reason. The adapter must shuffle and record the true index."""
    _skip_if_absent(config, "whatsup")
    items = list(load("whatsup", config))
    idxs = [it.meta["answer_index"] for it in items]
    assert all(i >= 0 for i in idxs), "some gold caption is not present in its own option list"
    assert len(set(idxs)) > 1, "gold answer is at a constant position — options were not shuffled"
    # every position should be used; nothing should be wildly over-represented
    for pos in range(4):
        share = idxs.count(pos) / len(idxs)
        assert 0.15 < share < 0.35, f"answer position {pos} has share {share:.2f} — not shuffled"

    # the shuffle must be REPRODUCIBLE (same seed -> same permutation)
    again = list(load("whatsup", config))
    assert [it.meta["options"] for it in again] == [it.meta["options"] for it in items]

    # and the upstream order must still be recoverable, with its correct-caption-first rule
    for it in items:
        assert it.meta["answer_text"] == it.meta["options_upstream"][0]
        assert it.meta["options"][it.meta["answer_index"]] == it.meta["answer_text"]


def test_revsi_every_documented_frame_budget_loads(config):
    """All four budgets in BUDGETS must actually load. 'all' was dead: the parquet's
    `num_frames` column is a budget LABEL (literally the string 'all'), not a count, so
    int() raised — and ReVSI's entire thesis is that conclusions change with the budget."""
    _skip_if_absent(config, "revsi")
    from sbind.datasets.revsi import BUDGETS

    for budget in BUDGETS:
        it = take(load("revsi", config, frame_budget=budget), 1)[0]
        assert it.meta["frame_budget"] == str(budget)
        assert it.frame_indices, f"budget {budget}: item has no frame indices"
        # n_frames must be the REAL clip length, not the upstream label
        assert isinstance(it.meta["n_frames"], int) and it.meta["n_frames"] > 0
        assert len(it.frame_indices) == it.meta["n_frames"]
        if str(budget) != "all":
            assert it.meta["n_frames"] == int(budget)


def test_decode_frames_raises_rather_than_returning_fewer_frames(config):
    """A short read must be an error. It used to silently return fewer images than requested,
    so the model saw a different input than the record claimed and the contact sheet captioned
    the wrong frames."""
    _skip_if_absent(config, "revsi")
    from sbind.datasets.base import decode_frames

    it = take(load("revsi", config), 1)[0]
    with pytest.raises(IndexError, match="shorter than the annotation claims"):
        decode_frames(it.video, [0, 1, 999_999])
