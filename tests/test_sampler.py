"""Factorial sampler: determinism + marginal balance."""

from collections import Counter

import numpy as np

from sbind.stimuli.sampler import balanced_levels, build_scene_specs, factorial_assignments

CONFIG = {
    "n_images": 120,
    "output": {"set_name": "t", "root": "/tmp/x"},
    "render": {"res_x": 256, "res_y": 256, "samples": 4},
    "camera": {
        "pos_world": [0.0, -4.0, 1.5],
        "target_world": [0.0, 1.5, 0.5],
        "f_mm": 35.0,
        "sensor_width_mm": 36.0,
    },
    "scene": {"ground_color": [0.5, 0.5, 0.5], "sun_energy": 4.0, "sun_direction": [5, -5, 8]},
    "objects": {
        "size_m": 0.4,
        "categories": ["cube", "sphere", "cylinder"],
        "colors": {"red": [0.8, 0.05, 0.05], "blue": [0.05, 0.2, 0.8]},
    },
    "factors": {
        "near_depth_bins": [1.5, 2.25, 3.0, 3.75, 4.5],
        "depth_gaps": [0.75, 1.5, 2.25],
        "depth_jitter": 0.15,
        "min_gap": 0.3,
        "lateral_offset": 0.7,
    },
    "condition": {"size_condition": "congruent", "elevation_condition": "congruent"},
}


def test_balanced_levels_even():
    rng = np.random.default_rng(0)
    out = balanced_levels(100, [0, 1], rng)
    counts = Counter(out)
    assert counts[0] == 50 and counts[1] == 50


def test_balanced_levels_remainder_within_one():
    rng = np.random.default_rng(0)
    out = balanced_levels(101, ["a", "b", "c"], rng)
    counts = Counter(out)
    assert max(counts.values()) - min(counts.values()) <= 1
    assert len(out) == 101


def test_factorial_determinism():
    f = {"a": [1, 2, 3], "b": ["x", "y"]}
    a1 = factorial_assignments(f, 50, np.random.default_rng(7), balanced_on=["b"])
    a2 = factorial_assignments(f, 50, np.random.default_rng(7), balanced_on=["b"])
    assert a1 == a2


def test_build_scene_specs_deterministic():
    s1 = build_scene_specs(CONFIG, seed=0)
    s2 = build_scene_specs(CONFIG, seed=0)
    assert [s.to_dict() for s in s1] == [s.to_dict() for s in s2]
    assert len(s1) == 120


def test_build_scene_specs_seed_changes_set():
    s0 = build_scene_specs(CONFIG, seed=0)
    s1 = build_scene_specs(CONFIG, seed=1)
    # same ids (index-based) but different geometry assignments somewhere
    assert [s.to_dict() for s in s0] != [s.to_dict() for s in s1]


def test_closer_object_balanced():
    specs = build_scene_specs(CONFIG, seed=0)
    counts = Counter(s.factors["closer_object"] for s in specs)
    assert counts[0] == counts[1] == 60


def test_near_depth_bin_balanced():
    specs = build_scene_specs(CONFIG, seed=0)
    counts = Counter(s.factors["near_depth_bin"] for s in specs)
    # 120 images / 5 bins = 24 each
    assert all(c == 24 for c in counts.values())
    assert set(counts) == {0, 1, 2, 3, 4}


def test_congruent_geometry_nearer_is_lower_y():
    # the "closer" object must actually have the smaller world-y (nearer the camera)
    specs = build_scene_specs(CONFIG, seed=0)
    for s in specs:
        closer = s.factors["closer_object"]
        other = 1 - closer
        assert s.objects[closer].pos_world[1] < s.objects[other].pos_world[1]


def test_depth_is_continuous_not_binned():
    # jitter must break depth off the discrete bin centres, otherwise ratio/absolute
    # regression targets would collapse onto a handful of values.
    specs = build_scene_specs(CONFIG, seed=0)
    near_ys = {round(s.factors["near_y"], 6) for s in specs}
    assert len(near_ys) > 100  # not just the 5 bin centres
    bins = set(CONFIG["factors"]["near_depth_bins"])
    assert not near_ys.issubset(bins)


def test_pair_always_strictly_depth_ordered():
    # jitter must never collapse or invert the near/far ordering
    specs = build_scene_specs(CONFIG, seed=0)
    for s in specs:
        gap = s.factors["far_y"] - s.factors["near_y"]
        assert gap >= CONFIG["factors"]["min_gap"] - 1e-9


def test_pairs_never_identical_in_both_colour_and_category():
    # an identical pair would make "which object is closer?" unanswerable
    specs = build_scene_specs(CONFIG, seed=0)
    for s in specs:
        a, b = s.objects
        assert not (a.category == b.category and a.color == b.color)


def test_pair_constraint_holds_across_seeds():
    for seed in range(5):
        for s in build_scene_specs(CONFIG, seed=seed):
            a, b = s.objects
            assert not (a.category == b.category and a.color == b.color)


def _centre_and_surface_depths(spec):
    from sbind.stimuli import geometry

    K, R, t, _ = geometry.camera_frame(
        spec.camera.pos_world,
        spec.camera.target_world,
        spec.camera.f_mm,
        spec.camera.sensor_width_mm,
        spec.camera.res_x,
        spec.camera.res_y,
    )
    axis = geometry.optical_axis(R)
    out = []
    for o in spec.objects:
        d = geometry.project(K, R, t, o.pos_world)[2]
        h = geometry.half_extent_along(o.category, o.size_m, axis)
        out.append((d, d - h))
    return out


def test_unambiguous_ordinal_centre_and_surface_agree():
    # with the constraint on, the centre-depth order and nearest-surface order must
    # never disagree — otherwise "which is closer?" is perceptually ambiguous
    cfg = {**CONFIG, "constraints": {"unambiguous_ordinal": True, "ordinal_margin_m": 0.15}}
    for seed in range(3):
        for s in build_scene_specs(cfg, seed=seed):
            (d0, s0), (d1, s1) = _centre_and_surface_depths(s)
            assert (d0 < d1) == (s0 < s1), f"{s.id}: centre/surface order disagree"


def test_unambiguous_ordinal_enforces_margin():
    cfg = {**CONFIG, "constraints": {"unambiguous_ordinal": True, "ordinal_margin_m": 0.15}}
    from sbind.stimuli import geometry

    for s in build_scene_specs(cfg, seed=0):
        depths = _centre_and_surface_depths(s)
        (d0, _), (d1, _) = depths
        near, far = (0, 1) if d0 < d1 else (1, 0)
        K, R, t, _ = geometry.camera_frame(
            s.camera.pos_world, s.camera.target_world, s.camera.f_mm,
            s.camera.sensor_width_mm, s.camera.res_x, s.camera.res_y,
        )
        axis = geometry.optical_axis(R)
        h_near = geometry.half_extent_along(s.objects[near].category, s.objects[near].size_m, axis)
        h_far = geometry.half_extent_along(s.objects[far].category, s.objects[far].size_m, axis)
        gap = abs(d1 - d0)
        assert gap >= abs(h_near - h_far) + 0.15 - 1e-6


def test_min_depth_ratio_enforced():
    # every apparent-size cue must be congruent BY CONSTRUCTION: the area cue needs a
    # far/near depth ratio above ~1.158 (worst case), so the sampler floors it at 1.18.
    cfg = {
        **CONFIG,
        "constraints": {"unambiguous_ordinal": True, "ordinal_margin_m": 0.15,
                        "min_depth_ratio": 1.18},
    }
    for seed in range(3):
        for s in build_scene_specs(cfg, seed=seed):
            (d0, _), (d1, _) = _centre_and_surface_depths(s)
            ratio = max(d0, d1) / min(d0, d1)
            assert ratio >= 1.18 - 1e-6, f"{s.id}: depth ratio {ratio:.4f} < 1.18"


def test_constraint_can_be_disabled():
    cfg = {**CONFIG, "constraints": {"unambiguous_ordinal": False}}
    specs = build_scene_specs(cfg, seed=0)
    assert len(specs) == CONFIG["n_images"]  # still produces a full set
