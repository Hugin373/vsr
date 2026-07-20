"""bpy renderer: SceneSpec -> rendered image + per-object masks + §3 StimulusAnnotation.

[Requires the ``stimuli`` extra — imports bpy.] Rendered headless with Cycles on CPU.

Two renders per scene:
  1. Beauty pass — Principled BSDF materials, config-many samples, 'Standard' view
     transform. This is the stimulus image.
  2. ID pass — each object gets a flat Emission material of a unique pure colour, ground
     black, 1 sample, near-zero pixel filter, 'Raw' view transform (no tone mapping) so
     the saved PNG holds exact colours. Per-object masks are recovered by colour match.

The Blender camera's world matrix is set directly from geometry.look_at_rotation, so the
K[R|t] this pipeline stores matches Blender's rasterisation to sub-pixel (test:
tests/test_render_consistency.py asserts projected centres land within 2 px of rendered
mask centroids).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image

from ..schemas import Camera, ObjectAnnotation, PairRelation, StimulusAnnotation
from ..utils.io import ensure_dir
from ..utils.logging import get_logger
from . import geometry
from .scene_spec import SceneSpec

log = get_logger("sbind.render_bpy")
_GPU_LOGGED = False   # the enable path runs per scene; announce the device once

try:
    import bpy
    import mathutils

    HAS_BPY = True
except ImportError:  # pragma: no cover - import guard for the analysis env
    bpy = None
    mathutils = None
    HAS_BPY = False

# Distinct pure colours for the ID pass (up to 6 objects). Ground/background are black.
_ID_COLORS = [
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (1.0, 1.0, 0.0),
    (1.0, 0.0, 1.0),
    (0.0, 1.0, 1.0),
]


def _require_bpy() -> None:
    if not HAS_BPY:
        raise RuntimeError(
            "render_bpy requires bpy. Sync the stimuli extra: "
            "`uv sync --extra stimuli` (or add --extra stimuli to your run)."
        )


def _reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    # the empty factory scene has no world; create one so both passes can set the sky
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    scene.world = world
    return scene


def _add_ground(color):
    bpy.ops.mesh.primitive_plane_add(size=50.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "ground"
    mat = bpy.data.materials.new("ground_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    plane.data.materials.append(mat)
    return plane


def _cube_part(name, loc, dims):
    """Add an axis-aligned cube part with real dimensions."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def _join_parts(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in parts:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _add_procedural_canonical(obj_spec, idx: int):
    """Procedural canonical-size stand-ins for M4a size-prior categories.

    The project ultimately wants CC0 mesh assets, but no asset bundle is present in this
    repo. These simple joined meshes give the generator non-primitive silhouettes and
    canonical object labels without introducing an unverified download path.
    """
    cat = obj_spec.category
    s = obj_spec.size_m
    x, y, z = tuple(obj_spec.pos_world)
    name = f"obj{idx}_{obj_spec.name}"
    if cat == "chair":
        parts = []
        # Bounding height is s, centre is z. Bottom at z-s/2, top at z+s/2.
        bottom = z - 0.5 * s
        parts.append(
            _cube_part(f"{name}_seat", (x, y, bottom + 0.44 * s), (0.72 * s, 0.62 * s, 0.12 * s))
        )
        parts.append(
            _cube_part(
                f"{name}_back", (x, y + 0.25 * s, bottom + 0.72 * s), (0.72 * s, 0.10 * s, 0.56 * s)
            )
        )
        for sx in (-0.28, 0.28):
            for sy in (-0.22, 0.22):
                parts.append(
                    _cube_part(
                        f"{name}_leg",
                        (x + sx * s, y + sy * s, bottom + 0.20 * s),
                        (0.08 * s, 0.08 * s, 0.40 * s),
                    )
                )
        return _join_parts(parts, name)
    if cat == "mug":
        parts = []
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=48, radius=0.28 * s, depth=0.72 * s, location=(x, y, z - 0.03 * s)
        )
        body = bpy.context.active_object
        body.name = f"{name}_body"
        bpy.ops.object.shade_smooth()
        parts.append(body)
        # A torus handle, rotated into a vertical plane. It is deliberately simple; masks
        # are measured from pixels, not trusted from these dimensions.
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.22 * s,
            minor_radius=0.04 * s,
            location=(x + 0.30 * s, y, z - 0.02 * s),
            rotation=(1.5708, 0.0, 0.0),
        )
        handle = bpy.context.active_object
        handle.name = f"{name}_handle"
        parts.append(handle)
        return _join_parts(parts, name)
    if cat == "bottle":
        parts = []
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=48, radius=0.18 * s, depth=0.62 * s, location=(x, y, z - 0.12 * s)
        )
        body = bpy.context.active_object
        body.name = f"{name}_body"
        bpy.ops.object.shade_smooth()
        parts.append(body)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=40, radius=0.08 * s, depth=0.34 * s, location=(x, y, z + 0.32 * s)
        )
        neck = bpy.context.active_object
        neck.name = f"{name}_neck"
        bpy.ops.object.shade_smooth()
        parts.append(neck)
        return _join_parts(parts, name)
    raise ValueError(f"unknown canonical category: {cat!r}")


def _add_object(obj_spec, idx: int):
    cat = obj_spec.category
    s = obj_spec.size_m
    loc = tuple(obj_spec.pos_world)
    if cat == "cube":
        bpy.ops.mesh.primitive_cube_add(size=s, location=loc)
    elif cat == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=s / 2.0, location=loc)
    elif cat == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=s / 2.0, depth=s, location=loc)
    elif cat in ("chair", "mug", "bottle"):
        ob = _add_procedural_canonical(obj_spec, idx)
    else:
        raise ValueError(f"unknown category: {cat!r}")
    if cat not in ("chair", "mug", "bottle"):
        ob = bpy.context.active_object
    ob.name = f"obj{idx}_{obj_spec.name}"
    # smooth spheres/cylinders a touch for a cleaner beauty render
    if cat in ("sphere", "cylinder"):
        bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.new(f"mat_obj{idx}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*obj_spec.color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    ob.data.materials.append(mat)
    return ob


def _emission_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def _add_camera(scene, spec: SceneSpec):
    K, R, t, r_cw = geometry.camera_frame(
        spec.camera.pos_world,
        spec.camera.target_world,
        spec.camera.f_mm,
        spec.camera.sensor_width_mm,
        spec.camera.res_x,
        spec.camera.res_y,
    )
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = spec.camera.f_mm
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = spec.camera.sensor_width_mm
    cam_data.shift_x = 0.0
    cam_data.shift_y = 0.0
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)

    mat = mathutils.Matrix.Identity(4)
    for r in range(3):
        for c in range(3):
            mat[r][c] = float(r_cw[r][c])
    for r in range(3):
        mat[r][3] = float(spec.camera.pos_world[r])
    cam.matrix_world = mat
    scene.camera = cam
    return K, R, t


def _add_sun(scene, spec: SceneSpec):
    light_data = bpy.data.lights.new("Sun", type="SUN")
    light_data.energy = spec.sun_energy
    light = bpy.data.objects.new("Sun", light_data)
    scene.collection.objects.link(light)
    d = np.asarray(spec.sun_direction, dtype=float)
    d = d / (np.linalg.norm(d) + 1e-9)
    # point the sun so it shines from sun_direction toward the origin
    z = d  # sun local -Z is the light direction; +Z points back toward the source
    up = np.array([0.0, 0.0, 1.0])
    x = np.cross(up, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0.0, 0.0])
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    m = mathutils.Matrix.Identity(4)
    for r in range(3):
        m[r][0], m[r][1], m[r][2] = float(x[r]), float(y[r]), float(z[r])
    light.matrix_world = m
    return light


def _disable_metadata_stamping(scene) -> None:
    """Stop Blender writing Date / RenderTime into the PNG's tEXt chunks.

    Those chunks make every render byte-different even when the pixels are IDENTICAL, which
    breaks the determinism rule (and any content-hash provenance we key caches on later).
    """
    r = scene.render
    r.use_stamp = False  # no burn-in
    for prop in (
        "use_stamp_date",
        "use_stamp_time",
        "use_stamp_render_time",
        "use_stamp_frame",
        "use_stamp_scene",
        "use_stamp_camera",
        "use_stamp_lens",
        "use_stamp_filename",
        "use_stamp_hostname",
        "use_stamp_memory",
        "use_stamp_note",
        "use_stamp_marker",
        "use_stamp_sequencer_strip",
        "use_stamp_frame_range",
    ):
        if hasattr(r, prop):
            setattr(r, prop, False)


def _configure_beauty(scene, render_cfg):
    scene.render.engine = render_cfg.get("engine", "CYCLES")
    scene.render.resolution_x = int(render_cfg["res_x"])
    scene.render.resolution_y = int(render_cfg["res_y"])
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    scene.render.image_settings.file_format = "PNG"
    if scene.render.engine == "CYCLES":
        device = str(render_cfg.get("device", "CPU")).upper()
        if device == "GPU":
            _enable_gpu_devices(render_cfg)
        scene.cycles.device = device
        scene.cycles.samples = int(render_cfg.get("samples", 32))
        scene.cycles.seed = int(render_cfg.get("cycles_seed", 0))
        # TWO sources of render non-determinism, both default OFF so that identical
        # (config, seed) reproduces byte-identical images (CLAUDE.md determinism rule):
        #   - denoising (OIDN): thread scheduling perturbs ~0.01% of pixels by 1 LSB;
        #   - adaptive sampling: per-pixel stopping depends on thread timing, leaving a
        #     few 1-LSB pixels different between runs.
        # Compensate with more `samples` rather than by denoising.
        scene.cycles.use_denoising = bool(render_cfg.get("denoise", False))
        scene.cycles.use_adaptive_sampling = bool(render_cfg.get("adaptive_sampling", False))
    scene.view_settings.view_transform = "Standard"
    scene.render.film_transparent = False
    _disable_metadata_stamping(scene)


def _enable_gpu_devices(render_cfg) -> None:
    """Enable exactly the CUDA_VISIBLE_DEVICES-masked GPU for Cycles, and VERIFY it is on.

    ⚠ Setting `scene.cycles.device = "GPU"` alone is NOT enough. Cycles renders on GPU only if a
    compute device type is selected in preferences AND at least one device of that type is
    enabled. With neither done, Blender falls back to CPU **silently** — the render succeeds, the
    config says GPU, and the only symptom is that it is slow. That is exactly the shape of every
    bug this project has caught, so the fallback is turned into a hard error here.

    CUDA_VISIBLE_DEVICES must already be set (by the GPU guard) before this runs: Blender
    enumerates whatever the mask exposes, so masking is how "never claim more than one GPU" is
    enforced rather than by picking indices here.
    """
    prefs = bpy.context.preferences.addons["cycles"].preferences
    wanted = str(render_cfg.get("compute_device_type", "OPTIX")).upper()
    available = [t[0] for t in prefs.get_device_types(bpy.context)]
    if wanted not in available:
        raise RuntimeError(
            f"compute_device_type {wanted!r} not available; this build offers {available}"
        )
    prefs.compute_device_type = wanted
    prefs.get_devices()

    enabled = []
    for dev in prefs.devices:
        dev.use = dev.type == wanted
        if dev.use:
            enabled.append(dev.name)
    if not enabled:
        raise RuntimeError(
            f"no {wanted} devices enabled — Cycles would fall back to CPU silently. "
            f"Devices seen: {[(d.name, d.type) for d in prefs.devices]}"
        )
    global _GPU_LOGGED
    if not _GPU_LOGGED:
        log.info("Cycles GPU: %s device(s) enabled via %s: %s", len(enabled), wanted, enabled)
        _GPU_LOGGED = True


def _render_to(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def _load_rgb(path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"))


def _render_id_pass(scene, objects, ground, lights, tmp_path) -> list[np.ndarray]:
    """Swap to emission materials, render a flat ID pass, return per-object bool masks.

    Every surface must be a pure emitter and there must be NO indirect light. Otherwise a
    red emissive object bounces red light onto the ground beneath it, that lit floor falls
    within the ID colour's match tolerance, and the mask bleeds downward — silently
    inflating bbox bottoms and retinal_size_px. Hence: ground -> black emission, lights
    off, max_bounces = 0.
    """
    id_colors = _ID_COLORS[: len(objects)]
    for i, ob in enumerate(objects):
        idmat = _emission_material(f"id_{i}", id_colors[i])
        ob.data.materials.clear()
        ob.data.materials.append(idmat)
    # ground emits pure black: it can neither be lit nor bounce colour onto anything
    black = _emission_material("id_ground", (0.0, 0.0, 0.0))
    ground.data.materials.clear()
    ground.data.materials.append(black)
    for light in lights:
        light.data.energy = 0.0

    # crisp, un-tone-mapped, single-sample, zero-bounce render
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    # near-zero box pixel filter -> point sampling, so ID colours stay crisp (no AA bleed)
    scene.cycles.pixel_filter_type = "BOX"
    scene.cycles.filter_width = 0.01
    scene.view_settings.view_transform = "Raw"
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    _render_to(scene, tmp_path)

    rgb = _load_rgb(tmp_path).astype(np.int16)
    masks = []
    for c in id_colors:
        target = np.array([round(c[0] * 255), round(c[1] * 255), round(c[2] * 255)])
        dist = np.abs(rgb - target).sum(axis=2)
        masks.append(dist < 60)  # tolerant colour match; ID colours are far apart
    return masks


def _render_solo_id_masks(spec: SceneSpec, out_dir: Path, render_cfg: dict) -> list[np.ndarray]:
    """Render each object alone to get its amodal mask.

    M4a scenes contain no occlusion condition, so visible and amodal masks should match.
    Still doing the solo pass now is the cheap prerequisite M4.5 needs, and it validates
    that later occlusion ratios will be measured from pixels rather than inferred.
    """
    masks: list[np.ndarray] = []
    for i, _ in enumerate(spec.objects):
        solo = SceneSpec(
            id=f"{spec.id}_solo{i}",
            camera=spec.camera,
            objects=[spec.objects[i]],
            ground_color=spec.ground_color,
            sun_energy=spec.sun_energy,
            sun_direction=spec.sun_direction,
            factors=spec.factors,
        )
        scene = _reset_scene()
        ground = _add_ground(solo.ground_color)
        objects = [_add_object(o, 0) for o in solo.objects]
        _add_camera(scene, solo)
        sun = _add_sun(scene, solo)
        _configure_beauty(scene, render_cfg)
        tmp_id = out_dir / f".{spec.id}_solo{i}_id.png"
        one = _render_id_pass(scene, objects, ground, [sun], tmp_id)[0]
        if tmp_id.exists():
            os.remove(tmp_id)
        masks.append(one)
    return masks


def _mask_geometry(mask: np.ndarray):
    """Return (bbox_px [x0,y0,x1,y1], height_px) from a boolean mask, or None if empty."""
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return None
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    return [x0, y0, x1 + 1.0, y1 + 1.0], (y1 - y0 + 1.0)


def render_scene(spec: SceneSpec, out_dir, render_cfg: dict) -> StimulusAnnotation:
    """Render one scene: writes images/<id>.png + masks/<id>_obj*.png, returns annotation."""
    _require_bpy()
    out_dir = Path(out_dir)
    img_dir = ensure_dir(out_dir / "images")
    mask_dir = ensure_dir(out_dir / "masks")

    scene = _reset_scene()
    ground = _add_ground(spec.ground_color)
    objects = [_add_object(o, i) for i, o in enumerate(spec.objects)]
    K, R, t = _add_camera(scene, spec)
    sun = _add_sun(scene, spec)
    _configure_beauty(scene, render_cfg)

    img_path = img_dir / f"{spec.id}.png"
    _render_to(scene, img_path)

    tmp_id = out_dir / f".{spec.id}_id.png"
    masks = _render_id_pass(scene, objects, ground, [sun], tmp_id)
    if tmp_id.exists():
        os.remove(tmp_id)
    amodal_masks = _render_solo_id_masks(spec, out_dir, render_cfg)

    axis = geometry.optical_axis(R)  # world direction along which depth_m is measured

    obj_anns: list[ObjectAnnotation] = []
    for i, o in enumerate(spec.objects):
        p_world = np.asarray(o.pos_world, dtype=float)
        uvd = geometry.project(K, R, t, p_world)
        pos_cam = (R @ p_world + t).tolist()
        depth_m = float(uvd[2])
        # nearest surface: centre depth minus the half-extent along the viewing axis.
        # This is what the bbox bottom / a human viewer tracks; depth_m is the centre.
        half_ext = geometry.half_extent_along(o.category, o.size_m, axis)
        nearest_surface_m = depth_m - half_ext
        # elevation_px = v-pixel of the ground-contact point below the object centre
        # (the "relative height" depth cue). Strictly monotonic with depth on the ground
        # plane, and the quantity M4's elevation-conflict condition will manipulate.
        base_world = np.array([p_world[0], p_world[1], 0.0])
        elevation_px = float(geometry.project(K, R, t, base_world)[1])

        mg = _mask_geometry(masks[i])
        area_px = int(masks[i].sum())
        if mg is None:
            bbox = [0.0, 0.0, 0.0, 0.0]
            retinal = 0.0
            mask_rel = None
        else:
            bbox, retinal = mg
            mask_rel = f"masks/{spec.id}_obj{i}.png"
            mask_img = Image.fromarray((masks[i] * 255).astype(np.uint8))
            mask_img.save(mask_dir / f"{spec.id}_obj{i}.png")

        amg = _mask_geometry(amodal_masks[i])
        amodal_area_px = int(amodal_masks[i].sum())
        if amg is None:
            bbox_amodal = [0.0, 0.0, 0.0, 0.0]
            retinal_amodal = 0.0
            mask_amodal_rel = None
        else:
            bbox_amodal, retinal_amodal = amg
            mask_amodal_rel = f"masks/{spec.id}_obj{i}_amodal.png"
            Image.fromarray((amodal_masks[i] * 255).astype(np.uint8)).save(
                mask_dir / f"{spec.id}_obj{i}_amodal.png"
            )
        occlusion_ratio = 0.0
        if amodal_area_px > 0:
            occlusion_ratio = max(0.0, 1.0 - area_px / amodal_area_px)

        obj_anns.append(
            ObjectAnnotation(
                name=o.name,
                category=o.category,
                size_m=o.size_m,
                pos_world=p_world.tolist(),
                pos_cam=pos_cam,
                depth_m=depth_m,
                bbox_px=bbox,
                retinal_size_px=retinal,
                elevation_px=elevation_px,
                mask=mask_rel,
                nearest_surface_m=nearest_surface_m,
                mask_area_px=area_px,
                mask_amodal=mask_amodal_rel,
                bbox_px_amodal=bbox_amodal,
                retinal_size_px_amodal=retinal_amodal,
                mask_area_px_amodal=amodal_area_px,
                occlusion_ratio=occlusion_ratio,
            )
        )

    camera = Camera(K=K.tolist(), R=R.tolist(), t=t.tolist(), height_m=spec.camera.height_m)
    pair_relations = _pair_relations(obj_anns)
    questions = _questions(obj_anns, pair_relations)

    return StimulusAnnotation(
        id=spec.id,
        image=f"images/{spec.id}.png",
        camera=camera,
        objects=obj_anns,
        factors=dict(spec.factors),
        pair_relations=pair_relations,
        questions=questions,
    )


def _questions(objs: list[ObjectAnnotation], rels: dict[str, PairRelation]) -> list[dict]:
    """Record balanced, deterministic task templates for the first target pair.

    The generator keeps the first two objects as the target pair; later distractors are
    annotated but are not the pair used for the M4a gate.
    """
    if len(objs) < 2 or "(0,1)" not in rels:
        return []
    rel = rels["(0,1)"]
    near = 0 if rel.ordinal_depth_surface == "0_closer" else 1
    left = 0 if objs[0].pos_cam[0] < objs[1].pos_cam[0] else 1
    return [
        {
            "type": "qualitative_lateral",
            "question": f"Is the {objs[0].name} to the left or right of the {objs[1].name}?",
            "options": ["left", "right"],
            "answer": "left" if left == 0 else "right",
        },
        {
            "type": "ordinal_depth",
            "question": "Which target object is closer to the camera?",
            "options": [objs[0].name, objs[1].name],
            "answer_index": near,
            "answer": objs[near].name,
        },
        {
            "type": "ratio_depth",
            "question": "What is the far/near camera-depth ratio for the target pair?",
            "answer": rel.dist_ratio,
        },
        {
            "type": "absolute_depth",
            "question": "What are the target objects camera-depths in metres?",
            "answer": [objs[0].depth_m, objs[1].depth_m],
        },
    ]


def _pair_relations(objs: list[ObjectAnnotation]) -> dict[str, PairRelation]:
    rels: dict[str, PairRelation] = {}
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            di, dj = objs[i].depth_m, objs[j].depth_m
            near, far = (di, dj) if di <= dj else (dj, di)
            ordinal = f"{i}_closer" if di < dj else f"{j}_closer"
            # surface-based ordinal: what a viewer (and the bbox bottom) actually reads
            si, sj = objs[i].nearest_surface_m, objs[j].nearest_surface_m
            ordinal_surface = f"{i}_closer" if si < sj else f"{j}_closer"
            dist_ratio = float(far / near) if near > 1e-9 else float("inf")
            dist_m = float(
                np.linalg.norm(np.asarray(objs[i].pos_world) - np.asarray(objs[j].pos_world))
            )
            rels[f"({i},{j})"] = PairRelation(
                ordinal_depth=ordinal,
                dist_ratio=dist_ratio,
                dist_m=dist_m,
                ordinal_depth_surface=ordinal_surface,
            )
    return rels
