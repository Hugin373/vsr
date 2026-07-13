"""Invariant tests for the Kang grid-scene engine (M3.1).

Two properties the whole spatial-ID derivation rests on, both of which were VIOLATED by the
first implementation while it happily produced 640 scenes:

  1. object identity must be decorrelated from grid position — otherwise mean-centering per
     object does not isolate a position code and the derivation is circular;
  2. every scene's gold answer must be DEFINED — a same-column pair has no left/right
     relation, yet `relation_lr` still returns a confident-looking string.
"""

import numpy as np
import pytest

from sbind.stimuli.grid_scenes import (
    GridScene,
    _balanced_placements,
    _compatible,
    _pair_up,
    assert_position_identity_decorrelated,
)


def _scenes_from_pairs(pairs, m=4):
    return [
        GridScene(
            id=f"s{i}", image="x.png",
            obj_a=f"o{a[0]}", obj_b=f"o{b[0]}",
            cell_a=a[1], cell_b=b[1], grid_m=m,
        )
        for i, (a, b) in enumerate(pairs)
    ]


def test_placements_are_exactly_balanced():
    """Every object in every cell exactly `repeats` times — by construction, not by luck."""
    rng = np.random.default_rng(0)
    pl = _balanced_placements(n_objects=8, grid_m=4, repeats=2, rng=rng)
    from collections import Counter

    c = Counter(pl)
    assert set(c.values()) == {2}, "placement counts are not uniform"
    assert len(c) == 8 * 16, "not every (object, cell) combination is present"


def test_pairing_uses_every_placement():
    """Dropping even one placement unbalances identity x position (it did: TV rose to 0.030)."""
    rng = np.random.default_rng(0)
    pl = _balanced_placements(n_objects=10, grid_m=4, repeats=2, rng=rng)
    pairs = _pair_up(pl, rng)
    assert 2 * len(pairs) == len(pl), "pairing dropped placements — balance is broken"
    flat = [p for pair in pairs for p in pair]
    assert sorted(flat) == sorted(pl), "pairing duplicated or lost a placement"


def test_pairs_are_answerable():
    """No pair may share a column or a row, else its gold relation is undefined."""
    rng = np.random.default_rng(0)
    pl = _balanced_placements(n_objects=10, grid_m=4, repeats=2, rng=rng)
    for a, b in _pair_up(pl, rng):
        assert _compatible(a, b)
        assert a[1][0] != b[1][0], "same column -> left/right has no ground truth"
        assert a[1][1] != b[1][1], "same row -> above/below has no ground truth"


def test_decorrelation_check_passes_on_a_balanced_set():
    rng = np.random.default_rng(0)
    pl = _balanced_placements(n_objects=12, grid_m=4, repeats=2, rng=rng)
    scenes = _scenes_from_pairs(_pair_up(pl, rng))
    stats = assert_position_identity_decorrelated(scenes)
    assert stats["worst_tv_from_uniform"] == pytest.approx(0.0, abs=1e-9)
    assert stats["same_column_pairs"] == 0 and stats["same_row_pairs"] == 0


def test_decorrelation_check_CATCHES_identity_predicting_position():
    """The check must FAIL when an object is confined to one region — the circularity trap.

    (The first generator cycled object pairs against cell pairs with modular indexing, which
    tied each object to a cell subset; this check caught it at TV=0.45.)
    """
    scenes = [
        GridScene(
            id=f"s{i}", image="x.png", obj_a="always_left", obj_b="always_right",
            cell_a=(0, i % 4), cell_b=(3, (i + 1) % 4), grid_m=4,
        )
        for i in range(32)
    ]
    with pytest.raises(RuntimeError, match="identity PREDICTS grid position"):
        assert_position_identity_decorrelated(scenes)


def test_undefined_gold_answer_is_rejected():
    """A same-column pair must RAISE, not be silently labelled 'right'."""
    scenes = [
        GridScene(
            id=f"s{i}", image="x.png", obj_a=f"a{i}", obj_b=f"b{i}",
            cell_a=(1, 0), cell_b=(1, 2), grid_m=4,  # SAME column
        )
        for i in range(8)
    ]
    with pytest.raises(RuntimeError, match="share a COLUMN"):
        assert_position_identity_decorrelated(scenes)


def test_relation_lr_matches_the_columns():
    s = GridScene("s", "x.png", "a", "b", cell_a=(0, 1), cell_b=(3, 2), grid_m=4)
    assert s.relation_lr == "left" and s.relation_ab == "above"
    s2 = GridScene("s", "x.png", "a", "b", cell_a=(3, 3), cell_b=(1, 0), grid_m=4)
    assert s2.relation_lr == "right" and s2.relation_ab == "below"
