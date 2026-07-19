"""§5 machine-checked invariants — symmetry, role balance, and manifest/config agreement.

Ruled 2026-07-19: these are implemented as invariants, NOT as prose in a doc. The eligibility
manifest (`configs/m4a_eligibility_manifest.yaml`) is a pre-registration artifact, so a config
that silently drifts from it would invalidate the pre-registration while every other test stayed
green — the project's signature failure shape.

Placement matters here. `P(near | category)` is checked at BOTH levels because placement is a
selection operator: exact balance over factorial assignments does not imply exact balance over
the images that actually placed. "Realized" means PLACED, not rendered, so both levels are
reachable without the renderer (§5 boundary).
"""

from __future__ import annotations

from collections import Counter

import pytest
import yaml

from sbind.stimuli.sampler import assert_symmetric_pairings, build_scene_specs
from sbind.utils.config import load_config

MANIFEST_PATH = "configs/m4a_eligibility_manifest.yaml"

# Placed-level tolerance, pre-registered in the criteria block. Assignment level must be EXACT.
PLACED_BALANCE_TOL = 0.02


@pytest.fixture(scope="module")
def manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------------- symmetry


def test_symmetry_guard_accepts_a_full_product_support():
    cats = ["cube", "sphere", "mug"]
    assert_symmetric_pairings([(a, b) for a in cats for b in cats])


def test_symmetry_guard_hard_fails_on_a_missing_reverse_pairing():
    """The failure this exists to catch: restricting individual PAIRINGS rather than categories.

    Dropping (bottle, cube) while keeping (cube, bottle) makes bottle preferentially FAR, which
    breaks the exact per-category role balance that closes B2->z.
    """
    cats = ["cube", "bottle"]
    pairs = [(a, b) for a in cats for b in cats if (a, b) != ("bottle", "cube")]
    with pytest.raises(ValueError, match="asymmetric category-pair support"):
        assert_symmetric_pairings(pairs)


def test_every_m4a_config_generates_symmetric_support(manifest):
    for regime, entry in manifest["generated"].items():
        cats = entry["categories"]
        assert entry["symmetric"] is True, regime
        assert_symmetric_pairings([(a, b) for a in cats for b in cats])


# ------------------------------------------------------------------- manifest <-> config agreement


CONFIG_FOR_REGIME = {
    "natural_congruent": [
        "configs/m4a_v1_natural_congruent.yaml",
        "configs/m4a_v1_natural_congruent_pilot.yaml",
    ],
    "counterbalanced": [
        "configs/m4a_v1_counterbalanced.yaml",
        "configs/m4a_v1_counterbalanced_pilot.yaml",
        "configs/m4a_v1_counterbalanced_pilot_j2.yaml",
    ],
    "conflict": [
        "configs/m4a_v1_conflict.yaml",
        "configs/m4a_v1_conflict_pilot.yaml",
    ],
}


@pytest.mark.parametrize(
    ("regime", "config_path"),
    [(r, p) for r, paths in CONFIG_FOR_REGIME.items() for p in paths],
)
def test_config_matches_the_eligibility_manifest(manifest, regime, config_path):
    """A config drifting from the pre-registered manifest invalidates the pre-registration."""
    entry = manifest["generated"][regime]
    cfg = load_config(config_path)
    assert sorted(cfg["objects"]["categories"]) == sorted(entry["categories"]), config_path
    assert sorted(cfg["objects"]["size_m_by_category"]) == sorted(entry["categories"]), (
        f"{config_path}: size_m_by_category must cover exactly the generated categories — a "
        f"leftover entry for a dropped category is dead config that looks set"
    )
    assert cfg["constraints"]["min_depth_ratio"] == pytest.approx(entry["min_depth_ratio"]), (
        config_path
    )


def test_natural_congruent_generates_the_four_set_and_not_six(manifest):
    """The binding disambiguation, asserted directly rather than left to the manifest round-trip.

    A six-category congruent arm is realizable only via per-pairing clamping, which measurably
    rebuilds the B15 confound in the reference arm (always-clamped band 1.665-1.850 disjoint from
    1.171-1.474; eta2(pairing -> ratio) = 0.865). See docs/REJECTED_DESIGNS.md R2.
    """
    assert manifest["generated"]["natural_congruent"]["categories"] == [
        "cube",
        "cylinder",
        "mug",
        "sphere",
    ]
    for path in CONFIG_FOR_REGIME["natural_congruent"]:
        cats = load_config(path)["objects"]["categories"]
        assert "bottle" not in cats and "chair" not in cats, path


# ------------------------------------------------------------------------------- role balance


def _role_counts(specs) -> dict[str, Counter]:
    out: dict[str, Counter] = {}
    for s in specs:
        out.setdefault(s.factors["near_category"], Counter())["near"] += 1
        out.setdefault(s.factors["far_category"], Counter())["far"] += 1
    return out


@pytest.mark.parametrize("config_path", ["configs/m4a_v1_natural_congruent_pilot.yaml"])
def test_role_balance_at_placed_level(config_path):
    """P(near | category) = 0.5 +/- tol over the PLACED set, not only over assignments.

    Assignment-level balance is exact by construction (`balanced_on: cat_pair`). Placement is a
    selection operator applied afterwards, so it can bias the realized marginals even when the
    assignments were perfect — which is precisely why the criteria block gates both levels.
    """
    cfg = load_config(config_path)
    cfg["n_images"] = 2000
    specs = build_scene_specs(cfg, seed=9001, raise_on_placement_failure=False)
    counts = _role_counts(specs)
    assert set(counts) == set(cfg["objects"]["categories"])
    for cat, c in counts.items():
        total = c["near"] + c["far"]
        p_near = c["near"] / total
        assert abs(p_near - 0.5) <= PLACED_BALANCE_TOL, (
            f"{cat}: placed P(near) = {p_near:.4f}, outside 0.5 +/- {PLACED_BALANCE_TOL} "
            f"(n = {total})"
        )


# --------------------------------------------------------------------------------- clamp audit


def test_ratio_log_records_the_clamp_and_matches_the_realized_geometry():
    """The clamp audit must record what §5 check C is defined on, and agree with the output.

    `clamped_fraction = #{r_raw < r_floor} / N` cannot be recovered from the built specs after the
    fact, and re-running with a non-binding floor changes placement rather than giving a paired
    comparison — so the sampler records it inline. This checks the record is (a) one row per
    placed image, (b) consistent with the realized geometry, and (c) that `clamped` means what it
    says.
    """
    import numpy as np

    from sbind.stimuli import geometry

    cfg = load_config("configs/m4a_v1_natural_congruent_pilot.yaml")
    cfg["n_images"] = 200
    log: list[dict] = []
    specs = build_scene_specs(cfg, seed=9001, ratio_log=log)

    assert len(log) == len(specs), "exactly one accepted-placement row per image"

    floor = cfg["constraints"]["min_depth_ratio"]
    jitter = cfg["constraints"]["min_depth_ratio_jitter"]
    for spec, row in zip(specs, log, strict=True):
        _, R, t, _ = geometry.camera_frame(
            spec.camera.pos_world,
            spec.camera.target_world,
            spec.camera.f_mm,
            spec.camera.sensor_width_mm,
            spec.camera.res_x,
            spec.camera.res_y,
        )
        depths = [float((R @ np.asarray(o.pos_world) + t)[2]) for o in spec.objects[:2]]
        near_i = int(spec.factors["closer_object"])
        realized = depths[1 - near_i] / depths[near_i]
        assert realized == pytest.approx(row["ratio_realized"], rel=1e-9), spec.id
        assert row["ratio_realized"] >= row["ratio_raw"] - 1e-12, "the floor may only raise"
        assert floor <= row["floor"] <= floor * (1.0 + jitter) + 1e-12
        assert row["clamped"] == (row["floor"] > row["ratio_raw"] + 1e-12)

    # and the floor must actually bite sometimes, or this audit proves nothing
    assert any(r["clamped"] for r in log), "no image clamped — the audit has no positive case"
    assert not all(r["clamped"] for r in log), "every image clamped — the 4-set fix did not take"


def test_ratio_log_does_not_perturb_the_output():
    cfg = load_config("configs/m4a_v1_natural_congruent_pilot.yaml")
    cfg["n_images"] = 60
    log: list[dict] = []
    with_log = build_scene_specs(cfg, seed=9001, ratio_log=log)
    without = build_scene_specs(cfg, seed=9001)
    assert [s.to_dict() for s in with_log] == [s.to_dict() for s in without]


# ------------------------------------------------------- known blocker, self-destructing


@pytest.mark.xfail(
    strict=True,
    reason=(
        "BLOCKER 2026-07-20, awaiting ratification. natural-congruent's PRE-REGISTERED floor is "
        "1.1707, but re-deriving the cue constants over the regime's OWN 4-set envelope gives a "
        "worst-case area-congruence requirement of 1.1761 — the floor is short by 0.46%. The "
        "1.1707 came from constants measured on the SIX-category envelope, which this regime no "
        "longer generates. A self-consistent floor is 1.2320 (requirement re-measures to 1.1601 "
        "there, +6.20% headroom), at a real cost: r(ratio, depth_gap_bin) 0.75 -> 0.50 and "
        "clamped_fraction 0.50 -> 0.72. Changing a pre-registered value is a ratification "
        "decision, not a fix to apply unilaterally, so the config still carries 1.1707 and this "
        "test records the violation. strict=True: it FAILS the moment the floor is raised, forcing "
        "this marker to be removed rather than left behind."
    ),
)
def test_congruent_floor_clears_its_own_committed_requirement():
    """A regime claiming area congruence must have a floor above its own derived requirement.

    The requirement is read from the `cue_constants` block committed in the config, so this cannot
    drift out of sync with the constants themselves.
    """
    cfg = load_config("configs/m4a_v1_natural_congruent_pilot.yaml")
    floor = cfg["constraints"]["min_depth_ratio"]
    required = cfg["cue_constants"]["binding_ratio_threshold"]
    assert floor > required, (
        f"floor {floor} does not clear the derived worst-case requirement {required} — area "
        f"congruence is a HARD validator check for this regime"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ATOMIC WORK ITEM IN PROGRESS 2026-07-20. The depth-gap envelope was extended to 1.95 "
        "battery-wide, which invalidates every regime's cue constants: the constants are a "
        "function of the depth distribution. Ruling 5 makes envelope change + re-derivation ONE "
        "work item, but they cannot land in one commit — the natural-congruent floor must first "
        "come from the deterministic envelope derivation, and constants can only be derived once "
        "the floor is fixed. This records the incomplete state as a machine check rather than a "
        "comment. strict=True: it FAILS as soon as all constants are re-derived, forcing removal."
    ),
)
@pytest.mark.parametrize(
    "config_path", [p for paths in CONFIG_FOR_REGIME.values() for p in paths]
)
def test_cue_constants_are_not_envelope_stale(config_path):
    """Committed constants must have been derived over the config's CURRENT depth envelope."""
    cfg = load_config(config_path)
    live = cfg["factors"]["depth_gaps"]
    for src in cfg["cue_constants"]["provenance"]["sources"]:
        assert src.get("depth_gaps") == live, (
            f"{config_path}: constants derived over depth_gaps={src.get('depth_gaps')} but the "
            f"config now uses {live} — envelope-stale"
        )
