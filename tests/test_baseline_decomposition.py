"""B0/B1/B2 baseline decomposition partition (ruling 3).

The three groups must be DISJOINT in what they represent and the combined matrix must be exactly
their concatenation — otherwise Δ_R|B0,B2 (which preserves B1) is not what it claims to be.
"""

import importlib.util
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location(
    "baseline_decomposition",
    Path(__file__).resolve().parents[1] / "scripts" / "baseline_decomposition.py",
)
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)


def _ann(cat, col, u, size_m, depth, world_x):
    """One-object annotation with the fields _build reads."""
    return {
        "factors": {"camera_yaw_delta_deg": 1.0, "camera_pitch_delta_deg": 0.0,
                    "camera_x_delta_m": 0.2, "camera_y_delta_m": 0.0},
        "objects": [{
            "category": cat, "name": f"{col}_{cat}", "bbox_px": [u, 10.0, u + 20.0, 40.0],
            "mask_area_px": 400.0, "retinal_size_px": 30.0, "elevation_px": 25.0,
            "size_m": size_m, "depth_m": depth, "pos_world": [world_x, depth, 0.4],
        }],
    }


def test_groups_partition_and_concatenate():
    anns = [_ann("cube", "red", 100.0, 0.5, 2.0, 0.3),
            _ann("sphere", "blue", 200.0, 0.8, 3.0, -0.4),
            _ann("cube", "blue", 150.0, 0.6, 2.5, 0.1)]
    feats, targets, groups = bd._build(anns)
    assert feats["B0_selection"].shape == (3, 2)          # centroid u, v
    assert feats["B1_monocular"].shape == (3, 5)          # area, bbox w/h, retinal, elevation
    assert feats["B2_semantic"].shape[1] == 2 + 2 + 1     # 2 cats + 2 cols + size_m
    combined = feats["B0B1B2_all"]
    n_cols = 2 + 5 + feats["B2_semantic"].shape[1]
    assert combined.shape == (3, n_cols), "combined must be exactly B0|B1|B2 concatenated"
    assert np.allclose(combined[:, :2], feats["B0_selection"])
    assert np.allclose(combined[:, 2:7], feats["B1_monocular"])
    assert set(targets) == {"z_depth", "x_world"}


def test_b0_is_position_b1_has_no_position():
    """The partition's whole point: B0 carries image position (centroid u), B1 does not."""
    anns = [_ann("cube", "red", u, 0.5, 2.0, 0.0) for u in (50.0, 250.0, 450.0)]
    feats, _, _ = bd._build(anns)
    # centroid_u varies across the three (50->250->450 gives centres 60,260,460)
    assert feats["B0_selection"][:, 0].std() > 1.0
    # B1 columns are constant ACROSS ROWS here (same size/elevation) -> position is NOT in B1
    assert np.allclose(feats["B1_monocular"].std(axis=0), 0.0)
