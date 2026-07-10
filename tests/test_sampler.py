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
