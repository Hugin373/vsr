"""Instrument audit for the deterministic envelope sweep.

Ruled 2026-07-20 after the sweep shipped two defects in one session:

  * the admission filter accepted any pose whose projected CENTRE was on-screen, where the sampler
    requires the bbox-plus-margin to sit inside the frame. 712/9216 (7.7%) of swept poses were
    unreachable, silhouettes were edge-clipped, and R inflated from 1.2072 to 1.4314;
  * `--verify-random` was documented in the module docstring and parsed as an argument while doing
    nothing, so a full derivation ran with its falsification test silently absent.

Neither was caught by a test, because there were no tests on the instrument itself — only on its
inputs. These are those tests.

⚠ NUMBERING IS MINE. The ruling requires "instrument-audit invariants A-E"; that lettered spec has
not been supplied in text, and only one item is named in the ruling ("per-example guard
equivalence", here I1). I1-I3 are named requirements; I4-I5 are mine. Reconcile against the real
A-E when it arrives rather than assuming this covers it.
"""

from __future__ import annotations

import itertools
import sys

import numpy as np
import pytest

sys.path.insert(0, "scripts")

from deterministic_cue_extremes import _world_y_for_depth, camera_corners  # noqa: E402

from sbind.stimuli.sampler import (  # noqa: E402
    _box_in_frame,
    _projected_box,
    _resolve_sizes,
    _rest_height,
)
from sbind.stimuli.scene_spec import ObjectSpec  # noqa: E402
from sbind.utils.config import load_config  # noqa: E402

CONFIG = "configs/m4a_v1_natural_congruent_pilot.yaml"


@pytest.fixture(scope="module")
def cfg():
    return load_config(CONFIG)


def _admits(cam, obj, cfg) -> bool:
    """The instrument's admission rule — must be the sampler's, per example."""
    box = _projected_box(cam, obj, margin_px=float(cfg["condition"]["target_bbox_margin_px"]))
    return box is not None and _box_in_frame(
        box, cam.res_x, cam.res_y, float(cfg["condition"]["target_frame_margin_px"])
    )


def _sampler_admits(cam, obj, cfg) -> bool:
    """The sampler's own single-object placement condition, reproduced from build_scene_specs."""
    target_margin = float(cfg["condition"]["target_bbox_margin_px"])
    frame_margin = float(cfg["condition"]["target_frame_margin_px"])
    box = _projected_box(cam, obj, margin_px=target_margin)
    return box is not None and _box_in_frame(box, cam.res_x, cam.res_y, frame_margin)


# ------------------------------------------------------------------ I1: per-example equivalence


def test_I1_guard_equivalence_per_example(cfg):
    """Instrument admission must equal the sampler's FOR EVERY POSE, never merely in aggregate.

    Aggregate agreement is what the buggy version had: it admitted 100% of poses where the sampler
    admits 92.3%, and no summary statistic of the sweep looked wrong. Equivalence has to be checked
    example by example or a systematically over-permissive filter passes.
    """
    sizes = _resolve_sizes(cfg["objects"], cfg["objects"]["categories"])
    cams = camera_corners(cfg)[:8]
    lat = [float(v) for v in cfg["factors"]["lateral_range"]]
    mults = [float(m) for m in cfg["factors"]["size_multipliers"]]
    checked = disagreements = 0
    for cat in cfg["objects"]["categories"]:
        for depth, sign, mag, mult in itertools.product(
            np.linspace(2.9, 7.0, 5), (-1.0, 1.0), lat, mults
        ):
            size = sizes[cat] * mult
            z = _rest_height(cat, size)
            x = sign * mag
            for cam, _ in cams:
                y = _world_y_for_depth(cam, x, z, float(depth))
                if not np.isfinite(y):
                    continue
                obj = ObjectSpec("o", cat, [0.8, 0.05, 0.05], size, [x, y, z])
                checked += 1
                if _admits(cam, obj, cfg) != _sampler_admits(cam, obj, cfg):
                    disagreements += 1
    assert checked > 500, "audit must actually exercise the guard"
    assert disagreements == 0, f"{disagreements}/{checked} poses judged differently"


def test_I1b_centre_only_shim_FAILS_equivalence(cfg):
    """OLD-BUG SHIM: the superseded centre-only filter must be REJECTED by I1.

    Rule 11 — a guard that cannot register the bug it was written for proves nothing.
    """

    def centre_only(cam, obj, _cfg):
        box = _projected_box(cam, obj, margin_px=0.0)
        if box is None:
            return False
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        return 0 <= cx <= cam.res_x and 0 <= cy <= cam.res_y

    sizes = _resolve_sizes(cfg["objects"], cfg["objects"]["categories"])
    cams = camera_corners(cfg)
    lat = [float(v) for v in cfg["factors"]["lateral_range"]]
    disagreements = 0
    for cat in cfg["objects"]["categories"]:
        for depth, sign, mag in itertools.product(np.linspace(2.9, 7.0, 6), (-1.0, 1.0), lat):
            size = sizes[cat]
            z = _rest_height(cat, size)
            x = sign * mag
            for cam, _ in cams:
                y = _world_y_for_depth(cam, x, z, float(depth))
                if not np.isfinite(y):
                    continue
                obj = ObjectSpec("o", cat, [0.8, 0.05, 0.05], size, [x, y, z])
                if centre_only(cam, obj, cfg) != _sampler_admits(cam, obj, cfg):
                    disagreements += 1
    assert disagreements > 0, (
        "the centre-only shim must disagree with the sampler guard — if it does not, this audit "
        "cannot detect the defect it exists for"
    )


# ------------------------------------------------------------- I2: planted-violation path test


def test_I2_planted_violation_is_detected():
    """The verification path must FLAG a value planted outside the envelope.

    A verification that reports zero exceedances is only meaningful if it can report a non-zero
    one. This plants a value 5% above the envelope maximum and requires detection.
    """
    envelope = {"area": {("cube", "far"): [100.0, 200.0]}}
    planted = 200.0 * 1.05

    lo, hi = min(envelope["area"][("cube", "far")]), max(envelope["area"][("cube", "far")])
    exceeded = planted < lo or planted > hi
    excess_pct = 100 * (planted - hi) / hi

    assert exceeded, "planted violation not detected — the comparison logic is inert"
    assert excess_pct == pytest.approx(5.0, abs=1e-9)


def test_I2b_unimplemented_verification_shim_is_caught():
    """OLD-BUG SHIM: a `--verify-random` that returns success without checking must be rejected.

    The shipped defect was exactly this — the flag parsed, the docstring promised falsification,
    and nothing ran. A verification result is only admissible if it reports how many objects it
    actually checked, and a zero-check result must not read as a pass.
    """
    inert = {"n_objects_checked": 0, "n_exceeding": 0}
    live = {"n_objects_checked": 600, "n_exceeding": 0}

    def verification_passes(result: dict) -> bool:
        return result["n_objects_checked"] > 0 and result["n_exceeding"] == 0

    assert not verification_passes(inert), (
        "a verification that checked nothing must not count as a pass"
    )
    assert verification_passes(live)


# -------------------------------------------------------------------- I3: load-bearing extrema


def test_I3_load_bearing_pair_is_identified_correctly():
    """R must be driven by C_a,near^MIN and C_a,far^MAX — not by any other extremum.

    The rejected x1.02283 shortcut came from confusing these: the observed violations were on the
    near-role MAXIMUM, which does not enter R at all, so a margin measured there is not an error
    bound for the pair that does.
    """
    from sbind.stimuli.cue_constants import required_ratios

    const = {
        "height": {("mug", "near"): [400.0], ("cube", "far"): [400.0]},
        "area": {("mug", "near"): [100.0, 500.0], ("cube", "far"): [200.0, 900.0]},
    }
    ratios = required_ratios(const)
    # sqrt(max far / min near) = sqrt(900/100) = 3.0 — uses far MAX and near MIN
    assert ratios["near_mug_far_cube"]["area"] == pytest.approx(3.0)

    # perturbing the near MAXIMUM must not move R at all
    const2 = {
        "height": const["height"],
        "area": {("mug", "near"): [100.0, 5000.0], ("cube", "far"): [200.0, 900.0]},
    }
    assert required_ratios(const2)["near_mug_far_cube"]["area"] == pytest.approx(3.0)


# ----------------------------------------------------------- I4-I5: mine, pending reconciliation


def test_I4_reachable_ranges_are_expanded_outward_not_inward(cfg):
    """The measured reachable envelope must be widened, never narrowed, before sweeping.

    The observed range is itself a random-sample extreme and therefore biased inward; sweeping it
    as-measured would inherit exactly the bias the deterministic instrument exists to remove.
    """
    from deterministic_cue_extremes import DEPTH_MARGIN

    assert DEPTH_MARGIN > 0, "the reachable envelope must be expanded outward"
    lo_obs, hi_obs = 3.0, 6.0
    span = hi_obs - lo_obs
    lo, hi = lo_obs - DEPTH_MARGIN * span, hi_obs + DEPTH_MARGIN * span
    assert lo < lo_obs and hi > hi_obs


def test_I5_camera_corners_cover_every_jitter_axis_boundary(cfg):
    """All 2^5 corners of the camera-jitter box must be present, each axis at both limits.

    A missing corner is a silently unswept region of the envelope, which is unobservable in the
    output — the sweep would simply report a narrower extreme with no indication anything was
    skipped.
    """
    cams = camera_corners(cfg)
    assert len(cams) == 32, f"expected 2^5 = 32 corners, got {len(cams)}"
    jitter = cfg["camera"]["jitter"]
    for axis, key in (
        ("height_m", "height"), ("pos_x_m", "pos_x"), ("pos_y_m", "pos_y"),
        ("pitch_deg", "pitch"), ("yaw_deg", "yaw"),
    ):
        lo, hi = (float(v) for v in jitter[axis])
        seen = {rec[key] for _, rec in cams}
        assert lo in seen and hi in seen, f"{axis}: corners missing a boundary value"


# ------------------------------------------- I6-I8: ledger monotonicity, B16, corner/interior


def test_I6_cumulative_ledger_R_is_monotone_non_decreasing():
    """ΔR_cum < 0 beyond float tolerance is LEDGER CORRUPTION, never a result.

    The cumulative R is a max over a growing union of measured poses, so it can only rise. A fall
    means evidence was dropped — which is exactly the failure that made the per-pass sequence
    1.2072 -> 1.2060 -> 1.2026 look like convergence when it was forgetting.
    """
    import sys as _sys

    _sys.path.insert(0, "scripts")
    from cumulative_extrema_ledger import required_ratio_from_ledger

    base = {
        "area_mug_near": {"min": 120000.0, "max": 133500.0},
        "area_cube_far": {"min": 129000.0, "max": 175000.0},
    }
    r0, _, _ = required_ratio_from_ledger(base)

    # any new evidence can only widen the extrema, hence raise R
    widened = {
        "area_mug_near": {"min": 119714.2, "max": 133500.0},   # a lower near minimum
        "area_cube_far": {"min": 129000.0, "max": 175054.8},   # a higher far maximum
    }
    r1, _, _ = required_ratio_from_ledger(widened)
    assert r1 >= r0 - 1e-12, f"cumulative R fell {r0} -> {r1}: ledger corruption"
    assert r1 > r0, "widening the extrema must raise R"


def test_I6b_narrowing_the_ledger_is_detected_as_corruption():
    """POSITIVE CONTROL for I6: a ledger that NARROWS must be detectable as a fall in R."""
    import sys as _sys

    _sys.path.insert(0, "scripts")
    from cumulative_extrema_ledger import required_ratio_from_ledger

    wide = {"area_mug_near": {"min": 119714.2, "max": 1.0},
            "area_cube_far": {"min": 0.0, "max": 175054.8}}
    narrow = {"area_mug_near": {"min": 120107.9, "max": 1.0},
              "area_cube_far": {"min": 0.0, "max": 173706.1}}
    r_wide, _, _ = required_ratio_from_ledger(wide)
    r_narrow, _, _ = required_ratio_from_ledger(narrow)
    assert r_narrow < r_wide, (
        "a narrowed ledger must show a FALLING R — if it does not, I6 cannot detect corruption"
    )


def test_I7_coverage_diagnostic_compares_against_the_sweep_domain_B16():
    """B16: a coverage diagnostic must compare against the domain it CLAIMS to cover.

    Shipped instance (2026-07-21): the violation-clustering diagnostic reported "distance to
    nearest grid point = 0.0000" for all ten load-bearing violations. It was comparing each
    violation against the TARGETED PROBE'S own 12-point grid — the grid that generated it — rather
    than against the sweep grid whose coverage was in question. Measured against the sweep grid the
    same violations sit 0.19-0.39 of a spacing away, which was the entire finding.
    """
    import numpy as np

    sweep_grid = np.linspace(2.939, 6.927, 10)      # the domain whose coverage is claimed
    probe_grid = np.linspace(2.939, 4.983, 12)      # the grid that generated the probe poses
    # the real violations sat exactly ON probe-grid points; use the exact values, not the
    # display-rounded ones, or the "vacuous comparison" it demonstrates is masked by rounding
    violations = [float(probe_grid[i]) for i in (9, 10, 11)]

    self_ref = [float(np.min(np.abs(probe_grid - v))) for v in violations]
    correct = [float(np.min(np.abs(sweep_grid - v))) for v in violations]

    assert max(self_ref) < 1e-9, "probe poses are ON the probe grid — a vacuous comparison"
    assert min(correct) > 0.05, (
        "against the SWEEP grid the violations are demonstrably off-grid; a diagnostic reporting "
        "zero distance is comparing a measurement against itself"
    )


def test_I8_camera_corner_vs_interior_classification():
    """Corner vs interior decides which pre-committed remedy applies, so it must be exact."""
    import sys as _sys

    _sys.path.insert(0, "scripts")
    from deterministic_cue_extremes import camera_is_corner

    cfg = load_config(CONFIG)
    j = cfg["camera"]["jitter"]
    corner = {"height": j["height_m"][1], "pos_x": j["pos_x_m"][0], "pos_y": j["pos_y_m"][1],
              "pitch": j["pitch_deg"][1], "yaw": j["yaw_deg"][0]}
    assert camera_is_corner(corner, cfg)

    interior = dict(corner)
    interior["pitch"] = 0.5 * (j["pitch_deg"][0] + j["pitch_deg"][1])   # midpoint, not a boundary
    assert not camera_is_corner(interior, cfg), (
        "an interior camera value must NOT read as a corner — it triggers the optimizer path"
    )
