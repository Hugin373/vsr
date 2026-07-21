"""Baseline feature taxonomy for M4a-Solo — with machine checks, because names lie.

Two contaminations were found by eye in two consecutive checkpoints (2026-07-21):

1. The B0/B1/B2 split was conflated: elevation and retinal size (B1 monocular cues, which the
   project's preregistered gate PRESERVES) were lumped into a single "geometry baseline", which
   produced an alarming R² = 0.951 that was not the operative gate at all.
2. `B0_position` contained border distances. `bl = bbox_x0` and `br = res_x − bbox_x1`, so
   `bl + br` algebraically determines the bbox WIDTH — apparent size smuggled into a "position"
   baseline, inflating R²(B0) by up to +0.086.

Both were caught by reading, not by a test. Since the baseline decides what a representation claim
means, it is a load-bearing instrument and gets the same treatment as the stimulus code.

⚠ THE CENTRAL LESSON: a feature cannot be classified by its NAME. It must be classified by what it
algebraically carries. `assert_no_cross_group_reconstruction` is the check that enforces this — it
regresses each feature on the other groups and fails if any is (near-)reconstructible.

GROUPS (solo naming; "B0 selection" is a misnomer here — there is no multi-object selection in a
single-object set, only projected-position coupling):

    B0_position    where the object projects: centroid, ground-contact elevation
    B1_appearance  how big it looks: retinal size, mask area, bbox extent
    B2_semantic    what it is and how big it really is: category, physical size, multiplier
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Pure position. Border distances are DELIBERATELY excluded: bl + br reconstructs bbox width and
# bt + bb reconstructs bbox height, which is B1 information (see module docstring, contamination 2).
B0_POSITION = ("centroid_u", "centroid_v", "ground_contact_v")

# Apparent size / extent — legitimate monocular evidence. The preregistered gate PRESERVES this:
# a depth representation may BE the integration of retinal size and elevation, so the model is not
# required to beat it.
B1_APPEARANCE = ("retinal_size_px", "mask_area_px", "bbox_w", "bbox_h")

# Identity and physical-size priors.
B2_SEMANTIC = ("physical_size_m", "size_multiplier", "category")

GROUPS: dict[str, tuple[str, ...]] = {
    "B0_position": B0_POSITION,
    "B1_appearance": B1_APPEARANCE,
    "B2_semantic": B2_SEMANTIC,
}

# A feature is "reconstructible" from another group if a linear fit recovers it this well. Set high
# on purpose: the target is algebraic identity (bl + br = W − bbox_w is exact), not mere
# correlation. Correlated-but-distinct features are legitimate and must not trip this.
RECONSTRUCTION_R2 = 0.995


class BaselineTaxonomyError(ValueError):
    """A feature group is malformed, duplicated, or algebraically contaminated."""


@dataclass
class FeatureManifest:
    """Exactly what went into a baseline fit — so the taxonomy name and the matrix cannot drift."""

    group_names: list[str]
    feature_names: list[str]
    n_features: int
    n_samples: int
    transforms: dict[str, str] = field(default_factory=dict)
    normalization: str = "zscore(train-fold)"
    estimator: str = ""
    alpha_grid: list[float] = field(default_factory=list)
    alpha_selected: float | None = None
    split: str = ""

    def to_dict(self) -> dict:
        return {
            "group_names": self.group_names,
            "feature_names": self.feature_names,
            "n_features": self.n_features,
            "n_samples": self.n_samples,
            "transforms": self.transforms,
            "normalization": self.normalization,
            "estimator": self.estimator,
            "alpha_grid": self.alpha_grid,
            "alpha_selected": self.alpha_selected,
            "split": self.split,
        }


def assert_groups_disjoint(groups: dict[str, tuple[str, ...]] = GROUPS) -> None:
    """No feature may appear in two groups — an increment over a group containing itself is zero."""
    seen: dict[str, str] = {}
    for gname, feats in groups.items():
        for f in feats:
            if f in seen:
                raise BaselineTaxonomyError(
                    f"feature {f!r} appears in both {seen[f]!r} and {gname!r}; groups must be "
                    f"disjoint or the incremental value is not interpretable"
                )
            seen[f] = gname


def assert_no_border_distances_in_position(
    groups: dict[str, tuple[str, ...]] = GROUPS,
) -> None:
    """Border distances must never sit in the pure-position group (contamination 2, by name)."""
    banned = ("border", "bl", "bt", "br", "bb", "dist_left", "dist_right", "dist_top", "dist_bottom")
    for f in groups["B0_position"]:
        if any(b == f or f.endswith(f"_{b}") for b in banned):
            raise BaselineTaxonomyError(
                f"{f!r} is a border distance and belongs to appearance, not position: paired "
                f"border distances algebraically reconstruct bbox extent"
            )


def assert_no_cross_group_reconstruction(
    X: dict[str, np.ndarray],
    groups: dict[str, tuple[str, ...]] = GROUPS,
    tol: float = RECONSTRUCTION_R2,
) -> dict[str, float]:
    """DATA-driven check: no feature may be linearly reconstructed from a DIFFERENT group.

    This is the check that name-based classification cannot do. `bl + br = W − bbox_w` is an exact
    identity, so border distances in the position group are reconstructible from appearance at
    R² = 1.0 even though nothing in their names says "size".

    Returns the worst reconstruction R² per feature, so the margin is visible rather than a bare
    pass/fail (rule 6).
    """
    worst: dict[str, float] = {}
    for gname, feats in groups.items():
        others = [f for g, fs in groups.items() if g != gname for f in fs if f in X]
        if not others:
            continue
        A = np.column_stack([np.asarray(X[f], dtype=float) for f in others])
        A = np.column_stack([A, np.ones(len(A))])
        for f in feats:
            if f not in X:
                continue
            y = np.asarray(X[f], dtype=float)
            if y.std() == 0:
                continue
            coef, *_ = np.linalg.lstsq(A, y, rcond=None)
            resid = y - A @ coef
            r2 = 1.0 - float(resid.var() / y.var())
            worst[f] = r2
            if r2 >= tol:
                raise BaselineTaxonomyError(
                    f"feature {f!r} in group {gname!r} is reconstructible from other groups at "
                    f"R² = {r2:.4f} >= {tol}. It carries their information, so an increment over "
                    f"{gname!r} would be measuring the wrong thing. Reclassify it."
                )
    return worst


def validate_taxonomy(
    X: dict[str, np.ndarray] | None = None,
    groups: dict[str, tuple[str, ...]] = GROUPS,
) -> dict[str, float]:
    """Run every taxonomy check. Call before any baseline fit that gates a claim."""
    assert_groups_disjoint(groups)
    assert_no_border_distances_in_position(groups)
    return assert_no_cross_group_reconstruction(X, groups) if X is not None else {}
