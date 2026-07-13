"""Render-consistency: rendered object-centre pixel matches K[R|t] projection < 2 px.

This is the M1.2 acceptance test. It needs bpy, so it is skipped when the stimuli extra
is not installed. Run it live with:  uv run --extra stimuli pytest tests/test_render_consistency.py

Uses small sphere markers so each silhouette's centroid coincides with the projected
centre of the sphere (a large object's silhouette centroid would not).
"""

import numpy as np
import pytest

bpy = pytest.importorskip("bpy")  # noqa: F841  (skip whole module without bpy)

from PIL import Image  # noqa: E402

from sbind.stimuli import geometry  # noqa: E402
from sbind.stimuli.render_bpy import render_scene  # noqa: E402
from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec  # noqa: E402


def _mask_centroid(path):
    arr = np.asarray(Image.open(path).convert("L"))
    ys, xs = np.nonzero(arr > 127)
    return xs.mean(), ys.mean()


def test_projection_matches_render_within_2px(tmp_path):
    cam = CameraSpec(
        pos_world=[0.0, -4.0, 1.5],
        target_world=[0.0, 1.5, 0.5],
        f_mm=35.0,
        sensor_width_mm=36.0,
        res_x=512,
        res_y=512,
    )
    # small sphere markers at known world positions spanning the view
    positions = [[0.0, 1.5, 0.6], [0.9, 2.2, 0.6], [-0.9, 3.2, 0.6]]
    objects = [
        ObjectSpec(f"m{i}", "sphere", [1.0, 1.0, 1.0], 0.08, p)
        for i, p in enumerate(positions)
    ]
    spec = SceneSpec(id="consistency_00000", camera=cam, objects=objects)

    render_cfg = {"engine": "CYCLES", "device": "CPU", "res_x": 512, "res_y": 512, "samples": 4}
    ann = render_scene(spec, tmp_path, render_cfg)

    K = np.array(ann.camera.K)
    R = np.array(ann.camera.R)
    t = np.array(ann.camera.t)

    for i, obj in enumerate(ann.objects):
        assert obj.mask is not None, f"object {i} produced no mask"
        cu, cv = _mask_centroid(tmp_path / obj.mask)
        pu, pv, depth = geometry.project(K, R, t, obj.pos_world)
        err = np.hypot(cu - pu, cv - pv)
        assert err < 2.0, (
            f"object {i}: projection off by {err:.2f}px "
            f"(proj={pu:.1f},{pv:.1f} centroid={cu:.1f},{cv:.1f})"
        )
        assert depth > 0
        # stored depth must equal the CV-frame z
        assert np.isclose(obj.depth_m, depth, atol=1e-4)


def test_render_is_deterministic(tmp_path):
    """Same (config, seed) -> identical pixels. The determinism hard rule.

    Two renderer settings silently broke this: OIDN denoising and adaptive sampling, whose
    thread scheduling perturbed a few pixels by 1 LSB between runs. Both now default OFF.
    """
    import numpy as np
    from PIL import Image

    from sbind.stimuli.scene_spec import CameraSpec, ObjectSpec, SceneSpec

    cam = CameraSpec([0.0, -2.5, 1.4], [0.0, 1.2, 0.35], 35.0, 36.0, 256, 256)
    spec = SceneSpec(
        id="det_a",
        camera=cam,
        objects=[ObjectSpec("c", "cube", [0.8, 0.2, 0.2], 0.6, [-0.7, 1.0, 0.3])],
    )
    rc = {"engine": "CYCLES", "device": "CPU", "res_x": 256, "res_y": 256, "samples": 16}

    a = render_scene(spec, tmp_path, rc)
    pa = np.asarray(Image.open(tmp_path / a.image).convert("RGB")).astype(int)
    spec.id = "det_b"
    b = render_scene(spec, tmp_path, rc)
    pb = np.asarray(Image.open(tmp_path / b.image).convert("RGB")).astype(int)

    assert np.abs(pa - pb).max() == 0, "renderer is not deterministic across runs"
