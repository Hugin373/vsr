"""Factorial sampler: determinism + marginal balance."""

import copy
from collections import Counter

import numpy as np
import pytest

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


def test_proposal_log_records_every_attempt_without_changing_output():
    """The rejection-bias hook (ruling 2) must log EVERY placement proposal, exactly one ACCEPTED
    per image, and must NOT change the built specs or the RNG stream (it only records)."""
    log: list[dict] = []
    with_log = build_scene_specs(CONFIG, seed=0, proposal_log=log)
    without_log = build_scene_specs(CONFIG, seed=0)
    # logging changes nothing about the output
    assert [s.to_dict() for s in with_log] == [s.to_dict() for s in without_log]
    # exactly one accepted proposal per image, and it is that image's last logged attempt
    accepted = [p for p in log if p["accepted"]]
    assert len(accepted) == len(with_log), "must be exactly one accepted placement per image"
    assert {p["image"] for p in accepted} == set(range(len(with_log)))
    for p in accepted:
        same_img = [q for q in log if q["image"] == p["image"]]
        assert same_img[-1] is p, "accepted proposal must be the last attempt (it breaks the loop)"
        assert not any(q["accepted"] for q in same_img[:-1]), "no accept before the winning attempt"
    # every proposal carries the pose deltas + candidate positions the audit correlates
    for k in ("near_x", "far_x", "camera_x_delta_m", "camera_yaw_delta_deg"):
        assert k in log[0]


def test_placement_params_are_read_from_the_condition_section():
    """Regression: target placement params live under `condition:` in every config, but the code
    read them from `constraints:` — so the documented 14/6-px margins silently defaulted to 0 and
    the attempts knob was stuck at 120 (dead config that LOOKED set, fixed 2026-07-18).

    An IMPOSSIBLE frame margin placed under `condition` must make placement fail. If the param
    were still read only from `constraints`, this margin would be ignored and the set would build
    fine — so this test fails on the old wiring and passes on the fix."""
    cfg = copy.deepcopy(CONFIG)
    cfg["n_images"] = 4
    cfg["condition"] = {
        **cfg["condition"],
        "target_frame_margin_px": 100_000.0,  # no object can be 100k px inside a 256-px frame
        "target_placement_attempts": 5,
    }
    with pytest.raises(RuntimeError, match="could not place non-overlapping target pair"):
        build_scene_specs(cfg, seed=0)


def test_placement_margin_under_condition_actually_pushes_targets_inward():
    """The positive half: a real frame margin read from `condition` keeps target bboxes off the
    frame edge, where a margin of 0 (the old silent default) allowed edge placement. Boxes are
    projected with the sampler's own helper (ObjectSpec carries no bbox until render time)."""
    from sbind.stimuli.sampler import _projected_box

    cfg = copy.deepcopy(CONFIG)
    cfg["n_images"] = 24
    margin = 20.0
    cfg["condition"] = {**cfg["condition"], "target_frame_margin_px": margin}
    res_x, res_y = cfg["render"]["res_x"], cfg["render"]["res_y"]
    for s in build_scene_specs(cfg, seed=0):
        for o in s.objects[:2]:  # the two TARGETS (distractors are exempt)
            box = _projected_box(s.camera, o)
            assert box is not None
            x0, y0, x1, y1 = box
            assert x0 >= margin - 1 and y0 >= margin - 1
            assert x1 <= res_x - margin + 1 and y1 <= res_y - margin + 1


def test_build_scene_specs_seed_changes_set():
    s0 = build_scene_specs(CONFIG, seed=0)
    s1 = build_scene_specs(CONFIG, seed=1)
    # same ids (index-based) but different geometry assignments somewhere
    assert [s.to_dict() for s in s0] != [s.to_dict() for s in s1]


def test_scene_appearance_factors_are_persisted():
    """§4.2 (2026-07-18): ground_color / sun_energy / sun_direction are sampled per image and were
    passed only to the renderer, not recorded — so the DR3 held-out-lighting / held-out-background
    splits could not be built. They must now appear in factors AND actually vary across images."""
    cfg = copy.deepcopy(CONFIG)
    cfg["scene"] = {
        "ground_colors": [[0.4, 0.4, 0.4], [0.5, 0.45, 0.4], [0.4, 0.45, 0.5]],
        "sun_energy_range": [3.0, 5.5],
        "sun_direction": [5, -5, 8],
        "sun_direction_jitter": 0.6,
    }
    specs = build_scene_specs(cfg, seed=0)
    for s in specs:
        for k in ("ground_color", "sun_energy", "sun_direction"):
            assert k in s.factors, f"{k} not persisted to factors"
    # must actually vary (else there is no factor to hold out)
    assert len({s.factors["sun_energy"] for s in specs}) > 1
    assert len({tuple(s.factors["ground_color"]) for s in specs}) > 1


# ---------------------------------------------------------------------------------------------
# MANIFEST of the frozen M4a stimulus configs (advisor arbitration item 3, 2026-07-19).
#
# Explicit, not a glob. A glob answers "is everything I found consistent?", which is silently
# vacuous when the thing that went wrong is that a config was never migrated — or, worse, when a
# config is DELETED or RENAMED and the guard simply stops checking it. The manifest turns both
# into failures: `discovered == expected` is asserted before any field is compared.
#
# Adding an M4a config REQUIRES adding it here. That is the point: a new regime must make an
# explicit claim about whether it carries the frozen generator block.
# ---------------------------------------------------------------------------------------------
M4A_CONFIG_MANIFEST = (
    "configs/m4a_v1_conflict.yaml",
    "configs/m4a_v1_conflict_pilot.yaml",
    "configs/m4a_v1_contrastive_pairs.yaml",
    "configs/m4a_v1_counterbalanced.yaml",
    "configs/m4a_v1_counterbalanced_pilot.yaml",
    "configs/m4a_v1_counterbalanced_pilot_j2.yaml",
    "configs/m4a_v1_natural_congruent.yaml",
    "configs/m4a_v1_natural_congruent_pilot.yaml",
)

# `m4a_v1_size_calibration.yaml` is a calibration OUTPUT (per-category size_m), not a stimulus
# config: it has no `factors` / `camera` block, so the frozen-generator fields do not apply.
M4A_NON_STIMULUS_CONFIGS = ("configs/m4a_v1_size_calibration.yaml",)

# M4a-SOLO (Stage 1) configs. Stimulus configs, but NOT pair configs: they deliberately carry no
# near_depth_bins / depth_gaps / min_depth_ratio, because those exist only to make a PAIR's
# apparent-size cues congruent. The pair frozen-generator block therefore does not apply to them.
# They DO share the camera-jitter envelope, so the two arms are comparable in pose statistics —
# that part is checked separately in test_solo_shares_the_frozen_camera_envelope.
M4A_SOLO_CONFIGS = ("configs/m4a_v1_solo.yaml",)

# The canonical frozen generator block (2026-07-18 §4 freeze). Every M4a stimulus config must
# carry it, so a regime differs from another ONLY in its condition/constraints, never in its
# camera envelope, depth bins or placement budget.
FROZEN_NEAR_DEPTH_BINS = [0.65, 1.1, 1.55, 2.0]
# Extended to 1.95 battery-wide (2026-07-20). depth_gaps is SHARED design surface: the three arms
# must span the same depth envelope or the matched three-regime contrast is not depth-matched.
FROZEN_DEPTH_GAPS = [0.45, 0.75, 1.05, 1.35, 1.65, 1.95]
FROZEN_CAMERA_JITTER = {
    "height_m": [-0.16, 0.16],
    "pos_x_m": [-0.3, 0.3],
    "pos_y_m": [-0.2, 0.2],
    "pitch_deg": [-3.0, 3.0],
    "yaw_deg": [-4.0, 4.0],
}
FROZEN_PLACEMENT_ATTEMPTS = 500
# Translation is called out separately from the rest of the jitter because it is the load-bearing
# addition: without it, image position stays tied to lateral world position (leak-ceiling world-x
# R2 ~0.92) and the world-x target is un-decorrelatable.
FROZEN_TRANSLATION_KEYS = ("pos_x_m", "pos_y_m")


def test_m4a_config_manifest_matches_disk():
    """The manifest IS the guard's scope — assert it before checking any field.

    Without this, deleting or renaming a config silently shrinks what every downstream frozen-block
    test covers, and the suite stays green while coverage quietly drops to nothing.
    """
    import glob

    discovered = sorted(glob.glob("configs/m4a_v1_*.yaml"))
    expected = sorted(M4A_CONFIG_MANIFEST + M4A_NON_STIMULUS_CONFIGS + M4A_SOLO_CONFIGS)
    assert discovered == expected, (
        f"M4a config set changed.\n  on disk but not in manifest: "
        f"{sorted(set(discovered) - set(expected))}\n  in manifest but not on disk: "
        f"{sorted(set(expected) - set(discovered))}\n"
        f"Add it to M4A_CONFIG_MANIFEST (pair config, frozen generator block applies), "
        f"M4A_SOLO_CONFIGS (Stage-1 solo config, no pair block), or "
        f"M4A_NON_STIMULUS_CONFIGS (not a stimulus config)."
    )


def _m4a_configs():
    """The manifested M4a stimulus configs — never a glob.

    See test_m4a_config_manifest_matches_disk for why the manifest is asserted first.
    """
    return list(M4A_CONFIG_MANIFEST)


def test_frozen_m4a_configs_place_at_scale():
    """§4 freeze (2026-07-18): the closest depth bin (0.2 m) was un-placeable under +/-0.3 m camera
    translation — the near object clips the frame regardless of lateral sampling, and MORE ATTEMPTS
    never helped (500 vs 2000 gave the same failures). Fixed by dropping the closest bin. Guards it:
    no frozen M4a translation config may reintroduce a near bin close enough to fail placement.

    ⚠ Widened 2026-07-19 (blocker #9 §4). This test used to glob only `*_pilot*` AND skip any
    config without `pos_x_m`, so it passed while all five NON-pilot M4a configs still carried the
    dropped 0.2 m bin and the pre-freeze pan-only jitter — the guard skipped exactly the configs
    that were wrong. A guard whose scope excludes the un-migrated cases certifies nothing."""
    from sbind.utils.config import load_config

    configs = _m4a_configs()
    assert configs, "no M4a configs found"
    for f in configs:
        cfg = load_config(f)
        b0 = min(cfg["factors"]["near_depth_bins"])
        assert b0 >= 0.5, f"{f}: closest near_depth_bin {b0} < 0.5 — un-placeable under translation"


@pytest.mark.parametrize("config_path", M4A_CONFIG_MANIFEST)
def test_frozen_generator_block_per_config(config_path):
    """Every freeze-critical field of every manifested config, checked against the canonical block.

    Bins, camera jitter, translation and the placement budget are properties of the FROZEN
    GENERATOR, not of a regime. Any divergence means two regimes were rendered under different
    scene statistics, which silently breaks every cross-regime comparison the M4a gate is built on.
    Parametrised per config so a failure names the offending file rather than the first one checked.
    """
    from sbind.utils.config import load_config

    cfg = load_config(config_path)

    assert cfg["factors"]["near_depth_bins"] == FROZEN_NEAR_DEPTH_BINS, (
        f"{config_path}: near_depth_bins diverge from the frozen block"
    )
    assert cfg["factors"]["depth_gaps"] == FROZEN_DEPTH_GAPS, (
        f"{config_path}: depth_gaps diverge from the frozen block — the envelope is battery-wide, "
        f"so one regime drifting breaks the matched three-regime contrast"
    )

    jitter = cfg["camera"]["jitter"]
    assert set(jitter) == set(FROZEN_CAMERA_JITTER), (
        f"{config_path}: camera jitter keys {sorted(jitter)} != {sorted(FROZEN_CAMERA_JITTER)}"
    )
    for key, want in FROZEN_CAMERA_JITTER.items():
        assert [float(v) for v in jitter[key]] == want, f"{config_path}: camera jitter {key}"

    # translation, called out explicitly — it is what decorrelates world-x from image position
    for key in FROZEN_TRANSLATION_KEYS:
        assert key in jitter, f"{config_path}: camera translation {key} missing (pan-only config)"
        lo, hi = (float(v) for v in jitter[key])
        assert lo < 0.0 < hi, f"{config_path}: camera translation {key} does not straddle zero"

    assert cfg["condition"]["target_placement_attempts"] == FROZEN_PLACEMENT_ATTEMPTS, (
        f"{config_path}: target_placement_attempts diverge from the frozen block"
    )


def test_category_role_balanced_at_scale():
    """§3 (2026-07-18): the ordered (near,far)-pair balancing must give each category a ~50/50
    near/far split AT SCALE — the mechanism that keeps identity priors from predicting depth (B2).
    At the pilot n=120 a residual imbalance is expected (incomplete factorial); it must vanish by
    n>=2000. This guards against the 55.1% shape-only class of confound re-appearing."""
    from collections import Counter

    cats = list(CONFIG["objects"]["categories"])
    cat_pairs = [(a, b) for a in cats for b in cats]
    ncol = len(CONFIG["objects"]["colors"])
    factors = {
        "near_depth_bin": list(range(len(CONFIG["factors"]["near_depth_bins"]))),
        "depth_gap_bin": list(range(len(CONFIG["factors"].get("depth_gaps", [1])))),
        "closer_object": [0, 1], "lateral_swap": [0, 1],
        "cat_pair": list(range(len(cat_pairs))), "color_pair": list(range(ncol * ncol)),
    }
    bon = ["closer_object", "near_depth_bin", "cat_pair", "color_pair", "lateral_swap"]
    a = factorial_assignments(factors, 4000, np.random.default_rng(0), balanced_on=bon)
    near, far = Counter(), Counter()
    for r in a:
        nc, fc = cat_pairs[r["cat_pair"]]
        near[nc] += 1
        far[fc] += 1
    worst = max(abs(near[c] / (near[c] + far[c]) - 0.5) for c in cats)
    assert worst < 0.02, f"category-role imbalance {worst:.3f} at n=4000 — B2->depth confound risk"


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


# ---------------------------------------------------- M4a-SOLO (Stage 1) invariants


def test_solo_has_exactly_one_object_and_no_pair_machinery():
    """Solo scenes carry ONE object and none of the pair-only fields.

    The pair fields exist only to make a PAIR's apparent-size cues congruent; their presence in a
    solo record would mean the Stage-1 set had inherited Stage-2 machinery it does not need.
    """
    from sbind.stimuli.sampler import build_solo_scene_specs
    from sbind.utils.config import load_config

    cfg = load_config("configs/m4a_v1_solo.yaml")
    cfg["n_images"] = 60
    specs = build_solo_scene_specs(cfg, seed=420)
    assert len(specs) == 60
    for s in specs:
        assert len(s.objects) == 1, "solo scenes must contain exactly one object"
        for pair_only in ("near_category", "far_category", "closer_object", "depth_gap_bin"):
            assert pair_only not in s.factors, f"{pair_only} is pair-only, not a solo factor"
        for needed in ("category", "world_x", "physical_size_m", "target_depth"):
            assert needed in s.factors


def test_solo_decouples_depth_from_apparent_size():
    """Depth must NOT be a near-deterministic function of apparent size (the v0 failure).

    v0's pair set measured r(depth, retinal) = -0.93 — depth ~86% predictable from apparent size
    alone. Solo varies physical size independently and widely so that coupling is broken. This is
    the design metric; without it, a 'depth probe' on solo would mostly be reading retinal size.

    ⚠ Solo does NOT remove monocular geometric baselines generally (centroid, bbox, area, height,
    elevation still predict depth). It removes multi-object SELECTION ambiguity. Elevation (image
    v) legitimately stays correlated with depth — it is a real monocular cue, controlled by
    held-out splits and the incremental-value baseline, not by design.
    """
    import numpy as np

    from sbind.stimuli import geometry
    from sbind.stimuli.sampler import build_solo_scene_specs
    from sbind.utils.config import load_config

    cfg = load_config("configs/m4a_v1_solo.yaml")
    cfg["n_images"] = 600
    specs = build_solo_scene_specs(cfg, seed=420)
    depth, apparent, phys = [], [], []
    for s in specs:
        _, R, t, _ = geometry.camera_frame(
            s.camera.pos_world, s.camera.target_world, s.camera.f_mm,
            s.camera.sensor_width_mm, s.camera.res_x, s.camera.res_y,
        )
        o = s.objects[0]
        d = float((R @ np.asarray(o.pos_world) + t)[2])
        depth.append(d)
        apparent.append(o.size_m / d)
        phys.append(o.size_m)
    r_apparent = float(np.corrcoef(depth, apparent)[0, 1])
    r_phys = float(np.corrcoef(depth, phys)[0, 1])
    assert r_apparent > -0.80, (
        f"r(depth, apparent size) = {r_apparent:.3f} is too close to v0's -0.93; depth would be "
        f"largely readable from apparent size alone"
    )
    assert abs(r_phys) < 0.15, (
        f"physical size must be independent of depth, got r = {r_phys:.3f}"
    )


def test_solo_shares_the_frozen_camera_envelope():
    """Solo must use the SAME camera-jitter envelope as the pair battery.

    Solo is exempt from the pair frozen block (no depth_gaps / near_depth_bins / floor — those
    exist only for pair congruence). But the camera envelope must match, or Stage-1 and Stage-2
    are measured under different pose statistics and their layer results are not comparable.
    """
    from sbind.utils.config import load_config

    for path in M4A_SOLO_CONFIGS:
        cfg = load_config(path)
        jitter = cfg["camera"]["jitter"]
        assert set(jitter) == set(FROZEN_CAMERA_JITTER), f"{path}: camera jitter keys diverge"
        for key, want in FROZEN_CAMERA_JITTER.items():
            assert [float(v) for v in jitter[key]] == want, f"{path}: camera jitter {key}"
        # and it must NOT carry the pair-only factors
        for pair_only in ("near_depth_bins", "depth_gaps"):
            assert pair_only not in cfg["factors"], f"{path}: {pair_only} is pair-only"
        assert "min_depth_ratio" not in (cfg.get("constraints") or {}), (
            f"{path}: min_depth_ratio is a pair-congruence device, not a solo parameter"
        )
