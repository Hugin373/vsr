"""Camera geometry: pinhole intrinsics + world->pixel projection (Blender conventions).

Pure NumPy, no bpy — so it imports and tests on a laptop. The renderer (render_bpy.py)
builds the Blender camera from the SAME parameters used here, so the projection this
module computes matches where Blender actually rasterizes a point (verified to <2 px in
tests/test_render_consistency.py).

Conventions
-----------
World: right-handed, Z up (Blender default).
Blender camera object: looks down its local -Z, local +Y is up, local +X is right.
Stored extrinsics (K, R, t) use the standard computer-vision convention: a world point
X projects as ``x_cam = R @ X + t`` with the camera looking down +Z, +X right, +Y DOWN,
and pixel ``(u, v) = (fx * x/z + cx, fy * y/z + cy)`` with the origin at the top-left.
``depth_m`` is ``x_cam.z`` (distance along the optical axis; positive in front).

The mapping from Blender-camera axes (X right, Y up, -Z forward) to CV-camera axes
(X right, Y down, +Z forward) is the flip ``diag(1, -1, -1)``.
"""

from __future__ import annotations

import numpy as np

# Blender-cam -> CV-cam axis flip (Y down, Z forward).
_FLIP = np.diag([1.0, -1.0, -1.0])
_WORLD_UP = np.array([0.0, 0.0, 1.0])


def intrinsics(f_mm: float, sensor_width_mm: float, res_x: int, res_y: int) -> np.ndarray:
    """3x3 pinhole intrinsics K for a Blender camera with sensor_fit=HORIZONTAL.

    fx = fy = f_mm / sensor_width_mm * res_x (square pixels), principal point at the
    image center. Matches Blender's projection when the camera uses HORIZONTAL sensor
    fit, zero lens shift, and unit pixel aspect.
    """
    fx = f_mm / sensor_width_mm * res_x
    fy = fx
    cx = res_x / 2.0
    cy = res_y / 2.0
    return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])


def look_at_rotation(cam_pos, target, world_up=_WORLD_UP) -> np.ndarray:
    """Blender camera-to-world rotation R_cw for a camera at ``cam_pos`` facing ``target``.

    Columns of R_cw are the camera's local +X (right), +Y (up), +Z axes in world coords.
    The camera looks down -Z, so +Z points from the target back to the camera.
    """
    cam_pos = np.asarray(cam_pos, dtype=float)
    target = np.asarray(target, dtype=float)
    world_up = np.asarray(world_up, dtype=float)

    z_axis = cam_pos - target  # camera looks down -Z, so +Z points away from target
    z_norm = np.linalg.norm(z_axis)
    if z_norm < 1e-9:
        raise ValueError("camera position coincides with target")
    z_axis = z_axis / z_norm

    x_axis = np.cross(world_up, z_axis)
    x_norm = np.linalg.norm(x_axis)
    if x_norm < 1e-9:
        raise ValueError("view direction is parallel to world_up (degenerate look-at)")
    x_axis = x_axis / x_norm

    y_axis = np.cross(z_axis, x_axis)  # already unit-length (orthonormal)
    return np.column_stack([x_axis, y_axis, z_axis])


def extrinsics(cam_pos, r_cw) -> tuple[np.ndarray, np.ndarray]:
    """CV-convention (R, t) from a Blender camera-to-world rotation R_cw and position.

    x_cam = R @ X_world + t, with R = flip @ R_cw^T and t = -R @ cam_pos.
    """
    cam_pos = np.asarray(cam_pos, dtype=float)
    r_cw = np.asarray(r_cw, dtype=float)
    R = _FLIP @ r_cw.T
    t = -R @ cam_pos
    return R, t


def project(K, R, t, points_world) -> np.ndarray:
    """Project world point(s) to pixels. Returns [..., 3] rows of (u, v, depth).

    Accepts a single (3,) point or an (N, 3) array. ``depth`` is the CV camera-frame z
    (metres); points behind the camera have depth <= 0.
    """
    K = np.asarray(K, dtype=float)
    R = np.asarray(R, dtype=float)
    t = np.asarray(t, dtype=float)
    pts = np.asarray(points_world, dtype=float)
    single = pts.ndim == 1
    pts = np.atleast_2d(pts)

    cam = pts @ R.T + t  # (N, 3) in CV camera frame
    depth = cam[:, 2]
    # guard against divide-by-zero for points on the image plane
    safe_z = np.where(np.abs(depth) < 1e-12, 1e-12, depth)
    u = K[0, 0] * cam[:, 0] / safe_z + K[0, 2]
    v = K[1, 1] * cam[:, 1] / safe_z + K[1, 2]
    out = np.column_stack([u, v, depth])
    return out[0] if single else out


def optical_axis(R) -> np.ndarray:
    """Unit world-space direction along which ``depth_m`` is measured.

    depth = (R @ X + t)[2], so the gradient of depth w.r.t. X — i.e. the direction that
    increases depth — is the third row of R.
    """
    return np.asarray(R, dtype=float)[2]


def half_extent_along(category: str, size_m: float, axis) -> float:
    """Half-extent of a primitive along a world direction (its support function).

    Used to turn a centre depth into a nearest-surface depth: the object's surface is
    ``half_extent_along`` metres nearer than its centre along the viewing axis. Objects
    are axis-aligned in world; ``size_m`` is the cube edge / sphere diameter / cylinder
    height (cylinder axis = world Z, radius = size_m/2).
    """
    a = np.abs(np.asarray(axis, dtype=float))
    h = size_m / 2.0
    if category == "sphere":
        return h  # isotropic: same half-extent in every direction
    if category == "cube":
        # support function of an axis-aligned box with half-sizes (h, h, h)
        return float(h * (a[0] + a[1] + a[2]))
    if category == "cylinder":
        # radius in the XY plane, half-height along Z
        return float(h * np.hypot(a[0], a[1]) + h * a[2])
    raise ValueError(f"unknown category: {category!r}")


def camera_frame(cam_pos, target, f_mm, sensor_width_mm, res_x, res_y, height_m=None):
    """Convenience: build (K, R, t, R_cw) for a look-at camera in one call.

    R_cw is returned too so the renderer can set the Blender camera's world matrix
    identically. height_m defaults to the camera's world z if not given.
    """
    K = intrinsics(f_mm, sensor_width_mm, res_x, res_y)
    r_cw = look_at_rotation(cam_pos, target)
    R, t = extrinsics(cam_pos, r_cw)
    return K, R, t, r_cw
