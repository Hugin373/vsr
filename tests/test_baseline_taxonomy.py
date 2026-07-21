"""Baseline taxonomy invariants — the check that names cannot provide.

Two contaminations were found by eye in consecutive checkpoints (2026-07-21) and neither was caught
by a test. Since the baseline decides what a representation claim MEANS, it is load-bearing.
"""

from __future__ import annotations

import numpy as np
import pytest

from sbind.probes.baselines import (
    GROUPS,
    BaselineTaxonomyError,
    assert_groups_disjoint,
    assert_no_border_distances_in_position,
    assert_no_cross_group_reconstruction,
    validate_taxonomy,
)


def test_shipped_taxonomy_is_disjoint_and_position_is_pure():
    assert_groups_disjoint()
    assert_no_border_distances_in_position()


def test_duplicate_feature_across_groups_hard_fails():
    bad = {"B0_position": ("centroid_u", "mask_area_px"), "B1_appearance": ("mask_area_px",)}
    with pytest.raises(BaselineTaxonomyError, match="appears in both"):
        assert_groups_disjoint(bad)


def test_border_distance_in_position_hard_fails_BY_NAME():
    """CONTAMINATION 2 SHIM, name-based half."""
    bad = dict(GROUPS)
    bad["B0_position"] = ("centroid_u", "centroid_v", "bl", "br")
    with pytest.raises(BaselineTaxonomyError, match="border distance"):
        assert_no_border_distances_in_position(bad)


def test_border_distance_in_position_hard_fails_BY_ALGEBRA():
    """CONTAMINATION 2 SHIM, the important half: caught by what it CARRIES, not what it is called.

    Rename the border distances to something innocuous — `edge_a`, `edge_b` — so the name check
    cannot see them. The algebraic check must still fire, because edge_a + edge_b = W − bbox_w is
    an exact identity with an appearance feature.
    """
    rng = np.random.default_rng(0)
    n = 400
    W = 512.0
    x0 = rng.uniform(20, 300, n)
    bbox_w = rng.uniform(40, 160, n)
    X = {
        "centroid_u": x0 + bbox_w / 2,
        "centroid_v": rng.uniform(50, 450, n),
        "ground_contact_v": rng.uniform(50, 450, n),
        "edge_a": x0,                       # innocuous name, = bbox left
        "edge_b": W - (x0 + bbox_w),        # innocuous name, = right margin
        "retinal_size_px": rng.uniform(30, 200, n),
        "mask_area_px": rng.uniform(500, 9000, n),
        "bbox_w": bbox_w,
        "bbox_h": rng.uniform(40, 160, n),
        "physical_size_m": rng.uniform(0.4, 1.2, n),
        "size_multiplier": rng.uniform(0.7, 1.4, n),
        "category": rng.integers(0, 4, n).astype(float),
    }
    contaminated = dict(GROUPS)
    contaminated["B0_position"] = ("centroid_u", "centroid_v", "ground_contact_v",
                                   "edge_a", "edge_b")
    with pytest.raises(BaselineTaxonomyError, match="reconstructible from other groups"):
        assert_no_cross_group_reconstruction(X, contaminated)


def test_clean_taxonomy_passes_the_algebraic_check_and_reports_margins():
    """The shipped grouping must PASS on realistic data, and report how close it came (rule 6)."""
    rng = np.random.default_rng(1)
    n = 500
    z = rng.uniform(3.0, 6.6, n)
    phys = rng.choice([0.47, 0.67, 0.93], n)
    X = {
        "centroid_u": rng.uniform(80, 430, n),
        "centroid_v": 300 - 40 * z + rng.normal(0, 25, n),
        "ground_contact_v": 320 - 45 * z + rng.normal(0, 20, n),
        "retinal_size_px": 400 * phys / z + rng.normal(0, 6, n),
        "mask_area_px": 90000 * (phys / z) ** 2 + rng.normal(0, 200, n),
        "bbox_w": 380 * phys / z + rng.normal(0, 6, n),
        "bbox_h": 400 * phys / z + rng.normal(0, 6, n),
        "physical_size_m": phys,
        "size_multiplier": phys / 0.67,
        "category": rng.integers(0, 4, n).astype(float),
    }
    worst = validate_taxonomy(X)
    assert worst, "the check must actually evaluate features"
    # margins, not just pass/fail
    assert max(worst.values()) < 0.995, f"closest reconstruction {max(worst.values()):.4f}"


def test_manifest_records_what_actually_entered_the_fit():
    """The taxonomy name and the design matrix must not be able to drift apart."""
    from sbind.probes.baselines import FeatureManifest

    m = FeatureManifest(
        group_names=["B0_position", "B2_semantic"],
        feature_names=list(GROUPS["B0_position"]) + list(GROUPS["B2_semantic"]),
        n_features=6, n_samples=1200, estimator="RidgeCV",
        alpha_grid=[0.001, 1.0, 1000.0], alpha_selected=1.0, split="held-out category",
    )
    d = m.to_dict()
    assert d["n_features"] == len(d["feature_names"])
    for k in ("normalization", "estimator", "alpha_selected", "split"):
        assert k in d
