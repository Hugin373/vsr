"""Cue-constant size-schema handling: three schemas, HARD-FAIL, and no silent fallback.

Blocker #9. The previous derivation read `factors["size_multiplier"]` unconditionally, which
only exists on the shared-multiplier (v0 / natural-congruent) sets. The dangerous fix is a
fallback — `factors.get("size_multiplier", <something shared>)` — because on a counterbalanced
or conflict set it divides the wrong multiplier out and produces a plausible, silently wrong
constant that gates every regime's accepted depth-ratio distribution.

`test_naive_shared_fallback_is_caught` is the AGENTS.md rule-11 positive control: it builds the
old/naive behaviour explicitly and shows these tests REJECT it, so a green suite here means the
instrument can register the failure it claims to prevent.
"""

from __future__ import annotations

import copy

import pytest

from sbind.stimuli.cue_constants import (
    CueConstantSchemaError,
    collect_constants,
    multiplier_worst_case,
    required_ratios,
    resolve_size_schema,
    size_norm,
    target_roles,
)

REF_SIZES = {"cube": 0.666, "sphere": 0.809, "cylinder": 0.666}

SHARED_CONFIG = {
    "objects": {"categories": ["cube", "sphere"], "size_m_by_category": REF_SIZES},
    "factors": {"size_multipliers": [0.92, 1.0, 1.08]},
    "condition": {"size_condition": "congruent"},
}

PER_OBJECT_CONFIG = {
    "objects": {"categories": ["cube", "sphere"], "size_m_by_category": REF_SIZES},
    "factors": {"size_multiplier_range": [0.75, 1.2]},
    "condition": {"size_condition": "independent_jitter"},
}

CONFLICT_CONFIG = {
    "objects": {"categories": ["cube", "sphere"], "size_m_by_category": REF_SIZES},
    "factors": {
        "near_size_multiplier_range": [0.78, 0.94],
        "far_size_multiplier_range": [1.12, 1.3],
    },
    "condition": {"size_condition": "conflict_far_larger"},
}

EXPLICIT_CONFIG = {
    "objects": {"categories": ["cube", "sphere"], "size_m_by_category": REF_SIZES},
    "factors": {},
    "condition": {"size_condition": "explicit_size"},
}


def _object(name, category, mult, depth, px=100.0, area=4000):
    return {
        "name": name,
        "category": category,
        "size_m": REF_SIZES[category] * mult,
        "depth_m": depth,
        "retinal_size_px": px,
        "mask_area_px": area,
    }


def _record(factors, objects, rid="t_00000"):
    return {"id": rid, "objects": objects, "factors": factors}


def shared_record(mult=1.08):
    return _record(
        {
            "closer_object": 0,
            "target_object_indices": [0, 1],
            "size_multiplier": mult,
            "size_multiplier_near": mult,
            "size_multiplier_far": mult,
        },
        [_object("a", "cube", mult, 3.0), _object("b", "sphere", mult, 5.0)],
    )


def per_object_record(near_mult=0.78, far_mult=1.25):
    return _record(
        {
            "closer_object": 0,
            "target_object_indices": [0, 1],
            "size_multiplier_near": near_mult,
            "size_multiplier_far": far_mult,
        },
        [_object("a", "cube", near_mult, 3.0), _object("b", "sphere", far_mult, 5.0)],
    )


# --------------------------------------------------------------------------- schema resolution


def test_resolve_schema_per_size_condition():
    assert resolve_size_schema(SHARED_CONFIG) == "shared"
    assert resolve_size_schema(PER_OBJECT_CONFIG) == "per_object"
    assert resolve_size_schema(CONFLICT_CONFIG) == "per_object"
    assert resolve_size_schema(EXPLICIT_CONFIG) == "explicit"


def test_unknown_size_condition_hard_fails():
    config = copy.deepcopy(SHARED_CONFIG)
    config["condition"]["size_condition"] = "some_new_regime"
    with pytest.raises(CueConstantSchemaError, match="unknown condition.size_condition"):
        resolve_size_schema(config)


def test_missing_size_condition_hard_fails_rather_than_assuming_shared():
    config = copy.deepcopy(SHARED_CONFIG)
    config["condition"] = {}
    with pytest.raises(CueConstantSchemaError, match="Refusing to assume a shared multiplier"):
        resolve_size_schema(config)


def test_explicit_size_schema_override_is_validated():
    config = copy.deepcopy(SHARED_CONFIG)
    config["condition"]["size_schema"] = "not_a_schema"
    with pytest.raises(CueConstantSchemaError, match="is not one of"):
        resolve_size_schema(config)


# ------------------------------------------------------------------- the three schemas resolve


def test_shared_schema_divides_out_the_shared_multiplier():
    record = shared_record(mult=1.08)
    for index, role in target_roles(record).items():
        norm = size_norm("shared", record, record["objects"][index], role, REF_SIZES)
        assert norm == pytest.approx(1.08)


def test_per_object_schema_divides_out_the_ROLE_multiplier():
    record = per_object_record(near_mult=0.78, far_mult=1.25)
    roles = target_roles(record)
    assert roles == {0: "near", 1: "far"}
    near = size_norm("per_object", record, record["objects"][0], "near", REF_SIZES)
    far = size_norm("per_object", record, record["objects"][1], "far", REF_SIZES)
    assert near == pytest.approx(0.78)
    assert far == pytest.approx(1.25)


def test_explicit_schema_reads_the_objects_own_size():
    record = per_object_record(near_mult=0.9, far_mult=1.3)
    del record["factors"]["size_multiplier_near"]
    del record["factors"]["size_multiplier_far"]
    near = size_norm("explicit", record, record["objects"][0], "near", REF_SIZES)
    far = size_norm("explicit", record, record["objects"][1], "far", REF_SIZES)
    assert near == pytest.approx(0.9)
    assert far == pytest.approx(1.3)


# --------------------------------------------------------------------- hard-fail on missing fields


def test_shared_schema_hard_fails_when_size_multiplier_is_absent():
    """The exact blocker-#9 input: a counterbalanced record under the old shared assumption."""
    record = per_object_record()
    with pytest.raises(CueConstantSchemaError) as excinfo:
        size_norm("shared", record, record["objects"][0], "near", REF_SIZES)
    assert "size_multiplier" in str(excinfo.value)
    assert "Refusing to substitute" in str(excinfo.value)


def test_per_object_schema_hard_fails_when_role_multiplier_is_absent():
    record = per_object_record()
    del record["factors"]["size_multiplier_far"]
    with pytest.raises(CueConstantSchemaError, match="Refusing to fall back to a shared"):
        size_norm("per_object", record, record["objects"][1], "far", REF_SIZES)


def test_collect_hard_fails_on_a_counterbalanced_set_declared_as_shared():
    """A mislabelled config must stop the derivation, not produce a number."""
    with pytest.raises(CueConstantSchemaError):
        collect_constants([per_object_record()], SHARED_CONFIG, REF_SIZES)


def test_missing_closer_object_hard_fails():
    record = per_object_record()
    del record["factors"]["closer_object"]
    with pytest.raises(CueConstantSchemaError, match="closer_object"):
        target_roles(record)


# ------------------------------------------------- the invariant that makes a fallback impossible


def test_size_consistency_invariant_catches_the_swapped_multiplier():
    """size_norm * calibrated size must reproduce the rendered size_m (rule 1: measured==analytic).

    Reading the FAR multiplier for the NEAR object is exactly what a careless refactor does; the
    identity breaks immediately even though every field it read was present and well-formed.
    """
    record = per_object_record(near_mult=0.78, far_mult=1.25)
    with pytest.raises(CueConstantSchemaError, match="wrong size multiplier is being divided"):
        size_norm("per_object", record, record["objects"][1], "near", REF_SIZES)


def test_naive_shared_fallback_is_caught(monkeypatch):
    """RULE-11 POSITIVE CONTROL: reproduce the tempting fallback and show it is rejected.

    A test suite that only exercises the new code proves nothing about whether it would have
    caught the old behaviour. So: patch in the naive `factors.get("size_multiplier", near_value)`
    fallback and assert that the constants it produces are wrong AND that the invariant fires.
    Without the check, the derived height constant for the far object is off by far_mult/near_mult
    = 1.60x — a 60% error with no exception and no symptom downstream.
    """
    record = per_object_record(near_mult=0.78, far_mult=1.25)
    far = record["objects"][1]

    # what the naive fallback would have used
    naive_norm = record["factors"].get("size_multiplier", record["factors"]["size_multiplier_near"])
    assert naive_norm == pytest.approx(0.78)

    correct = size_norm("per_object", record, far, "far", REF_SIZES)
    naive_constant = far["retinal_size_px"] * far["depth_m"] / naive_norm
    correct_constant = far["retinal_size_px"] * far["depth_m"] / correct
    assert naive_constant / correct_constant == pytest.approx(1.25 / 0.78, rel=1e-9)
    assert naive_constant / correct_constant > 1.6  # a 60% error, silently

    # and the shipped invariant rejects that very normalizer
    with pytest.raises(CueConstantSchemaError, match="wrong size multiplier"):
        size_norm("per_object", record, far, "near", REF_SIZES)


# ------------------------------------------------------------------------- roles and distractors


def test_distractors_are_excluded_from_the_constants():
    """A distractor can sit nearer than the far target, so argmin-over-depths mislabels roles.

    Distractors also carry their own multiplier (0.45-0.7 of the category size), unrelated to the
    target pair's, so pulling them in corrupts both roles' constants.
    """
    record = per_object_record(near_mult=0.9, far_mult=1.1)
    record["objects"].append(_object("distractor", "cube", 0.5, 3.5))
    record["factors"]["distractor_count"] = 1
    assert target_roles(record) == {0: "near", 1: "far"}

    out = collect_constants([record], PER_OBJECT_CONFIG, REF_SIZES)
    assert out["n_objects"] == 2
    assert set(out["height"]) == {("cube", "near"), ("sphere", "far")}


def test_argmin_over_all_objects_would_have_mislabelled_this_record():
    """Positive control for the role fix: show the old rule picks the distractor as 'near'."""
    record = per_object_record(near_mult=0.9, far_mult=1.1)
    record["objects"][0]["depth_m"] = 4.0  # near target
    record["objects"][1]["depth_m"] = 6.0  # far target
    record["objects"].append(_object("distractor", "cube", 0.5, 2.5))  # nearer than both
    depths = [o["depth_m"] for o in record["objects"]]
    assert depths.index(min(depths)) == 2  # old rule: the distractor is "near"
    assert target_roles(record) == {0: "near", 1: "far"}  # new rule: from the factors


# ------------------------------------------------------------------------------ derived numbers


def test_required_ratio_uses_extremes_not_means():
    records = [
        shared_record(mult=1.0),
        # a far sphere that measures unusually large: it must define the requirement
        _record(
            {
                "closer_object": 0,
                "target_object_indices": [0, 1],
                "size_multiplier": 1.0,
                "size_multiplier_near": 1.0,
                "size_multiplier_far": 1.0,
            },
            [_object("a", "cube", 1.0, 3.0, px=100.0), _object("b", "sphere", 1.0, 5.0, px=140.0)],
            rid="t_00001",
        ),
    ]
    out = collect_constants(records, SHARED_CONFIG, REF_SIZES)
    ratios = required_ratios(out)
    # C_h[sphere far] max = 140*5 = 700 ; C_h[cube near] min = 100*3 = 300
    assert ratios["near_cube_far_sphere"]["height"] == pytest.approx(700.0 / 300.0)
    mean_based = ((100.0 * 5 + 140.0 * 5) / 2) / 300.0
    assert ratios["near_cube_far_sphere"]["height"] > mean_based


def test_multiplier_worst_case_per_schema():
    assert multiplier_worst_case(SHARED_CONFIG) is None
    assert multiplier_worst_case(PER_OBJECT_CONFIG) == pytest.approx(1.2 / 0.75)
    assert multiplier_worst_case(CONFLICT_CONFIG) == pytest.approx(1.3 / 0.78)
