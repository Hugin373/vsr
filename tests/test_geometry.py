"""Pure projection math (no bpy): known 3D point -> expected pixel."""

import numpy as np

from sbind.stimuli import geometry


def test_intrinsics_values():
    K = geometry.intrinsics(f_mm=35.0, sensor_width_mm=36.0, res_x=512, res_y=512)
    fx_expected = 35.0 / 36.0 * 512
    assert np.isclose(K[0, 0], fx_expected)
    assert np.isclose(K[1, 1], fx_expected)  # square pixels
    assert np.isclose(K[0, 2], 256.0)
    assert np.isclose(K[1, 2], 256.0)


def test_project_identity_camera():
    # R = I, t = 0: camera at origin looking down +Z, principal point at center.
    K = geometry.intrinsics(35.0, 36.0, 512, 512)
    R = np.eye(3)
    t = np.zeros(3)
    fx = K[0, 0]

    # a point straight ahead lands on the principal point
    u, v, d = geometry.project(K, R, t, [0.0, 0.0, 5.0])
    assert np.allclose([u, v, d], [256.0, 256.0, 5.0])

    # x offset of 1 m at depth 5 -> cx + fx/5 ; y offset likewise
    u, v, d = geometry.project(K, R, t, [1.0, 0.0, 5.0])
    assert np.isclose(u, 256.0 + fx / 5.0)
    assert np.isclose(v, 256.0)
    u, v, d = geometry.project(K, R, t, [0.0, 1.0, 5.0])
    assert np.isclose(v, 256.0 + fx / 5.0)


def test_look_at_rotation_is_proper_orthonormal():
    r_cw = geometry.look_at_rotation([0, -4, 1.5], [0, 1.5, 0.5])
    assert np.allclose(r_cw @ r_cw.T, np.eye(3), atol=1e-9)
    assert np.isclose(np.linalg.det(r_cw), 1.0)


def test_target_projects_to_principal_point():
    # The camera looks AT the target, so the target sits on the optical axis and must
    # project exactly to the principal point (cx, cy). Strong end-to-end check of the
    # whole K[R|t] chain.
    cam_pos = [0.0, -4.0, 1.5]
    target = [0.0, 1.5, 0.5]
    K, R, t, _ = geometry.camera_frame(cam_pos, target, 35.0, 36.0, 512, 512)
    u, v, d = geometry.project(K, R, t, target)
    assert np.isclose(u, 256.0, atol=1e-6)
    assert np.isclose(v, 256.0, atol=1e-6)
    assert d > 0  # target is in front of the camera


def test_points_in_front_have_positive_depth():
    cam_pos = [0.0, -4.0, 1.5]
    target = [0.0, 1.5, 0.5]
    K, R, t, _ = geometry.camera_frame(cam_pos, target, 35.0, 36.0, 512, 512)
    for p in ([0, 0, 0.2], [0.7, 1.5, 0.2], [-0.7, 3.0, 0.2]):
        _, _, d = geometry.project(K, R, t, p)
        assert d > 0


def test_project_batched_matches_single():
    K, R, t, _ = geometry.camera_frame([0, -4, 1.5], [0, 1.5, 0.5], 35.0, 36.0, 512, 512)
    pts = np.array([[0.0, 1.5, 0.5], [1.0, 2.0, 0.2], [-1.0, 3.0, 0.2]])
    batch = geometry.project(K, R, t, pts)
    for i, p in enumerate(pts):
        assert np.allclose(batch[i], geometry.project(K, R, t, p))
