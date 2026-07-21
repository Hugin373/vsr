"""Seeded factorial sampler: stimulus-set config -> balanced list of SceneSpec.

Determinism rule: the entire set is a pure function of (config, seed). ``balanced_on``
factors get near-equal marginal counts; other factors are sampled uniformly at random.

M4a extends the original v0 congruent sampler with continuous lateral positions,
per-image camera jitter, independent per-object size jitter, nuisance variation and
optional distractors, while keeping the v0 config backward-compatible.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from . import geometry
from .scene_spec import CameraSpec, ObjectSpec, SceneSpec


def balanced_levels(n: int, levels: list, rng: np.random.Generator) -> list:
    """A length-n list where each level appears ~n/len(levels) times, shuffled."""
    if not levels:
        raise ValueError("levels must be non-empty")
    L = len(levels)
    base = (levels * (n // L)) if n >= L else []
    remainder = n - len(base)
    if remainder:
        extra_idx = rng.choice(L, size=remainder, replace=False)
        base = base + [levels[i] for i in extra_idx]
    base = list(base)
    rng.shuffle(base)
    return base


def factorial_assignments(
    factors: dict[str, list],
    n: int,
    rng: np.random.Generator,
    balanced_on: list[str] | None = None,
) -> list[dict]:
    """Return n factor-level assignments. ``balanced_on`` factors are marginally balanced."""
    balanced_on = set(balanced_on or [])
    columns: dict[str, list] = {}
    for name in sorted(factors):
        levels = factors[name]
        if name in balanced_on:
            columns[name] = balanced_levels(n, list(levels), rng)
        else:
            idx = rng.integers(0, len(levels), size=n)
            columns[name] = [levels[i] for i in idx]
    return [{name: columns[name][i] for name in columns} for i in range(n)]


def assert_symmetric_pairings(pairs: list[tuple[str, str]]) -> None:
    """Hard-fail unless the generated (near, far) category support is symmetric.

    §5 check B structural requirement: (a, b) ∈ S ⟹ (b, a) ∈ S. This is not an aesthetic
    constraint. `cat_pair` balancing is what gives every category an exact P(near | c) = 0.5
    split, and that split is what closes B2→z (identity priors predicting depth). An asymmetric
    support makes some category preferentially NEAR, rebuilding the confound the balancing exists
    to eliminate.

    Currently the support is built as C × C and is symmetric by construction, so this guard costs
    nothing — it exists because the moment anyone introduces an explicit allowed-pairings list
    (the obvious way to implement a per-pairing restriction) the property stops being automatic
    and starts being an assumption. Assumptions in this project get checked.
    """
    support = {(a, b) for a, b in pairs}
    missing = sorted({(b, a) for a, b in support} - support)
    if missing:
        raise ValueError(
            f"asymmetric category-pair support: {len(missing)} reversed pairing(s) absent, "
            f"e.g. {missing[:3]}. This breaks exact per-category near/far role balance "
            f"(§5 check B). Retained supports must be symmetric — restrict CATEGORIES, not "
            f"individual pairings."
        )


def _rest_height(category: str, size_m: float) -> float:
    """Z of the object centre so it rests on the ground plane (z=0)."""
    return geometry.rest_height(category, size_m)


def _resolve_sizes(obj_cfg: dict, categories: list[str]) -> dict[str, float]:
    """Per-category size_m: inline map, else calibration file, else flat base size."""
    sizes = dict(obj_cfg.get("size_m_by_category") or {})
    if not sizes and obj_cfg.get("size_calibration_file"):
        path = Path(obj_cfg["size_calibration_file"])
        if not path.exists():
            raise FileNotFoundError(
                f"size calibration file not found: {path}. Generate it with "
                f"`uv run --extra stimuli scripts/calibrate_sizes.py --config <stimulus config>`."
            )
        with open(path, encoding="utf-8") as f:
            sizes = dict(yaml.safe_load(f)["size_m_by_category"])
    if not sizes:
        base = float(obj_cfg.get("base_size_m", obj_cfg.get("size_m", 0.6)))
        sizes = {c: base for c in categories}
    missing = [c for c in categories if c not in sizes]
    if missing:
        raise ValueError(f"no calibrated size_m for categories: {missing}")
    return {c: float(sizes[c]) for c in categories}


def _range_or_value(cfg: dict[str, Any], key: str, default: float) -> float:
    value = cfg.get(key, default)
    if isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise ValueError(f"{key} range must be [lo, hi], got {value!r}")
        return float(value[0]), float(value[1])  # type: ignore[return-value]
    return float(value)


def _uniform_range(rng: np.random.Generator, value, default: tuple[float, float]) -> float:
    if value is None:
        lo, hi = default
    elif isinstance(value, (list, tuple)):
        lo, hi = float(value[0]), float(value[1])
    else:
        return float(value)
    return float(rng.uniform(lo, hi))


def _jitter_camera(
    cam_cfg: dict, render_cfg: dict, rng: np.random.Generator
) -> tuple[CameraSpec, dict]:
    """Apply per-image camera jitter around the config camera.

    Height / pitch / yaw pan the camera; ``pos_x_m`` / ``pos_y_m`` TRANSLATE it (lateral dolly +
    depth dolly). Translation is the load-bearing addition (2026-07-18): with the camera fixed at
    x=0 and only panning, image position stays tied to lateral WORLD position (leak-ceiling
    measured world-x still R²≈0.92). Moving the camera laterally injects a per-image offset a
    global probe cannot recover, which is what actually decorrelates image position from world x.
    Absent keys default to 0.0, so a config without them reproduces the old behaviour exactly."""
    base_pos = np.asarray(cam_cfg["pos_world"], dtype=float)
    base_target = np.asarray(cam_cfg["target_world"], dtype=float)
    jitter = cam_cfg.get("jitter", {}) or {}
    dh = _uniform_range(rng, jitter.get("height_m"), (0.0, 0.0))
    dx = _uniform_range(rng, jitter.get("pos_x_m"), (0.0, 0.0))
    dy = _uniform_range(rng, jitter.get("pos_y_m"), (0.0, 0.0))
    dp = math.radians(_uniform_range(rng, jitter.get("pitch_deg"), (0.0, 0.0)))
    dyaw = math.radians(_uniform_range(rng, jitter.get("yaw_deg"), (0.0, 0.0)))

    direction = base_target - base_pos
    dist = float(np.linalg.norm(direction))
    horiz = float(np.hypot(direction[0], direction[1]))
    yaw = math.atan2(direction[0], direction[1]) + dyaw
    pitch = math.atan2(direction[2], horiz) + dp

    pos = base_pos.copy()
    pos[0] += dx
    pos[1] += dy
    pos[2] += dh
    new_dir = np.array(
        [
            math.sin(yaw) * math.cos(pitch),
            math.cos(yaw) * math.cos(pitch),
            math.sin(pitch),
        ]
    )
    target = pos + dist * new_dir
    cam = CameraSpec(
        pos_world=pos.tolist(),
        target_world=target.tolist(),
        f_mm=float(cam_cfg["f_mm"]),
        sensor_width_mm=float(cam_cfg["sensor_width_mm"]),
        res_x=int(render_cfg["res_x"]),
        res_y=int(render_cfg["res_y"]),
    )
    rec = {
        "camera_height_delta_m": dh,
        "camera_x_delta_m": dx,
        "camera_y_delta_m": dy,
        "camera_pitch_delta_deg": math.degrees(dp),
        "camera_yaw_delta_deg": math.degrees(dyaw),
    }
    return cam, rec


def _sample_lateral(fcfg: dict, swap: int, rng: np.random.Generator) -> tuple[float, float, dict]:
    """Return near_x, far_x with balanced side and optional continuous magnitudes."""
    sign = -1.0 if swap == 0 else 1.0
    if "lateral_range" in fcfg:
        lo, hi = map(float, fcfg["lateral_range"])
        near_mag = float(rng.uniform(lo, hi))
        far_mag = float(rng.uniform(lo, hi))
        near_x = sign * near_mag
        far_x = -sign * far_mag
        return near_x, far_x, {"near_lateral_abs": near_mag, "far_lateral_abs": far_mag}
    lateral = float(fcfg["lateral_offset"])
    return (
        sign * lateral,
        -sign * lateral,
        {"near_lateral_abs": lateral, "far_lateral_abs": lateral},
    )


def _projected_box(
    camera: CameraSpec, obj: ObjectSpec, margin_px: float = 0.0
) -> tuple[float, float, float, float] | None:
    """Approximate projected bbox from the object's conservative axis-aligned bounds."""
    K, R, t, _ = geometry.camera_frame(
        camera.pos_world,
        camera.target_world,
        camera.f_mm,
        camera.sensor_width_mm,
        camera.res_x,
        camera.res_y,
    )
    hx, hy, hz = geometry.category_half_sizes(obj.category, obj.size_m)
    cx, cy, cz = obj.pos_world
    corners = np.array(
        [
            [cx + sx * hx, cy + sy * hy, cz + sz * hz]
            for sx in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
            for sz in (-1.0, 1.0)
        ],
        dtype=float,
    )
    proj = geometry.project(K, R, t, corners)
    if np.any(proj[:, 2] <= 0):
        return None
    return (
        float(np.min(proj[:, 0]) - margin_px),
        float(np.min(proj[:, 1]) - margin_px),
        float(np.max(proj[:, 0]) + margin_px),
        float(np.max(proj[:, 1]) + margin_px),
    )


def _boxes_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _box_in_frame(
    box: tuple[float, float, float, float],
    width: int,
    height: int,
    margin_px: float,
) -> bool:
    return (
        box[0] >= margin_px
        and box[1] >= margin_px
        and box[2] <= width - margin_px
        and box[3] <= height - margin_px
    )


def _size_multipliers(
    cond: dict, fcfg: dict, rng: np.random.Generator
) -> tuple[float, float, dict]:
    """Return near/far physical-size multipliers according to size_condition."""
    size_condition = cond.get("size_condition", "congruent")
    if size_condition in {"independent_jitter", "counterbalanced"}:
        value = fcfg.get("size_multiplier_range") or fcfg.get("size_multipliers", [0.85, 1.15])
        near = _uniform_range(rng, value, (0.85, 1.15))
        far = _uniform_range(rng, value, (0.85, 1.15))
        return near, far, {"size_multiplier_near": near, "size_multiplier_far": far}
    if size_condition in {"far_larger", "conflict_far_larger"}:
        near = _uniform_range(rng, fcfg.get("near_size_multiplier_range"), (0.80, 0.95))
        far = _uniform_range(rng, fcfg.get("far_size_multiplier_range"), (1.15, 1.35))
        return near, far, {"size_multiplier_near": near, "size_multiplier_far": far}
    mults = list(fcfg.get("size_multipliers", [1.0]))
    m = float(mults[int(rng.integers(0, len(mults)))])
    return m, m, {"size_multiplier": m, "size_multiplier_near": m, "size_multiplier_far": m}


def _sample_scene_appearance(
    scene_cfg: dict, rng: np.random.Generator
) -> tuple[list[float], float, list[float]]:
    colors = scene_cfg.get("ground_colors") or [scene_cfg.get("ground_color", [0.5, 0.5, 0.5])]
    ground_color = list(colors[int(rng.integers(0, len(colors)))])
    sun_energy = _uniform_range(
        rng,
        scene_cfg.get("sun_energy_range"),
        (float(scene_cfg.get("sun_energy", 4.0)), float(scene_cfg.get("sun_energy", 4.0))),
    )
    direction = np.asarray(scene_cfg.get("sun_direction", [5.0, -5.0, 8.0]), dtype=float)
    jitter = float(scene_cfg.get("sun_direction_jitter", 0.0))
    if jitter > 0:
        direction = direction + rng.normal(0.0, jitter, size=3)
        direction[2] = max(direction[2], 1.0)
    return ground_color, float(sun_energy), direction.tolist()


def _make_distractors(
    cfg: dict,
    size_by_cat: dict[str, float],
    color_items: list,
    rng: np.random.Generator,
    camera: CameraSpec,
    target_objects: list[ObjectSpec],
) -> list[ObjectSpec]:
    dcfg = cfg.get("distractors", {}) or {}
    levels = list(dcfg.get("count_levels", [0]))
    n = int(levels[int(rng.integers(0, len(levels)))])
    if n <= 0:
        return []
    cats = list(dcfg.get("categories") or list(size_by_cat))
    x_range = dcfg.get("x_range", [-1.65, 1.65])
    y_range = dcfg.get("y_range", [2.8, 4.8])
    mult_range = dcfg.get("size_multiplier_range", [0.55, 0.85])
    out: list[ObjectSpec] = []
    K, R, t, _ = geometry.camera_frame(
        camera.pos_world,
        camera.target_world,
        camera.f_mm,
        camera.sensor_width_mm,
        camera.res_x,
        camera.res_y,
    )
    occupied = [geometry.project(K, R, t, o.pos_world)[:2] for o in target_objects]
    # Spread distractors toward the sides/back and reject approximate projected overlaps.
    # Exact mask validation still decides correctness after rendering; this only prevents
    # the common accidental-occlusion cases before we burn render time.
    for k in range(n):
        chosen = None
        for _attempt in range(160):
            cat = cats[int(rng.integers(0, len(cats)))]
            cname, crgb = color_items[int(rng.integers(0, len(color_items)))]
            side = -1.0 if k % 2 == 0 else 1.0
            x = side * float(rng.uniform(abs(float(x_range[0])), abs(float(x_range[1]))))
            y = float(rng.uniform(float(y_range[0]), float(y_range[1])))
            size = size_by_cat[cat] * _uniform_range(rng, mult_range, (0.55, 0.85))
            z = _rest_height(cat, size)
            u, v, d = geometry.project(K, R, t, [x, y, z])
            if d <= 0 or not (35 <= u <= camera.res_x - 35 and 35 <= v <= camera.res_y - 35):
                continue
            if occupied and min(float(np.hypot(u - q[0], v - q[1])) for q in occupied) < 95:
                continue
            chosen = ObjectSpec(f"distractor_{cname}_{cat}", cat, list(crgb), size, [x, y, z])
            occupied.append(np.array([u, v]))
            break
        if chosen is not None:
            out.append(chosen)
    return out


def build_scene_specs(
    config: dict,
    seed: int,
    proposal_log: list[dict] | None = None,
    raise_on_placement_failure: bool = True,
    placement_failures: list[dict] | None = None,
    ratio_log: list[dict] | None = None,
) -> list[SceneSpec]:
    """Turn a stimulus-set config dict into a deterministic list of SceneSpec.

    If ``proposal_log`` is given, every target-placement proposal (accepted and rejected) is
    appended to it for the rejection-sampling bias audit (ruling 2). This never changes the
    output or the RNG stream — it only records.

    ``raise_on_placement_failure`` defaults True (a rendering run must place EVERY image, or the
    factor balance is broken). Set False for a DRY-RUN AUDIT: an un-placeable image is skipped and
    omitted from the result (the RNG has already consumed its attempts, so the remaining images are
    unaffected), letting an audit measure the placement-failure RATE instead of crashing.

    If ``ratio_log`` is given, the ACCEPTED placement of each image appends its pre-floor and
    post-floor depth ratio, the floor value drawn, and whether the floor moved it. This is what
    §5 check C's ``clamped_fraction`` is computed from. Like ``proposal_log`` it only records:
    no RNG draw, no change to the output.
    """
    rng = np.random.default_rng(seed)
    n = int(config["n_images"])
    set_name = config["output"]["set_name"]

    cam_cfg = config["camera"]
    render_cfg = config["render"]
    obj_cfg = config["objects"]
    scene_cfg = config.get("scene", {})
    cond = config.get("condition", {})
    fcfg = config["factors"]
    constraints = config.get("constraints", {})

    categories = list(obj_cfg["categories"])
    size_by_cat = _resolve_sizes(obj_cfg, categories)
    color_items = list(obj_cfg["colors"].items())

    cat_pairs = [(a, b) for a in categories for b in categories]
    assert_symmetric_pairings(cat_pairs)
    color_pairs = [(a, b) for a in range(len(color_items)) for b in range(len(color_items))]
    factors = {
        "near_depth_bin": list(range(len(fcfg["near_depth_bins"]))),
        "depth_gap_bin": list(range(len(fcfg["depth_gaps"]))),
        "closer_object": [0, 1],
        "lateral_swap": [0, 1],
        "cat_pair": list(range(len(cat_pairs))),
        "color_pair": list(range(len(color_pairs))),
    }
    balanced_on = list(
        config.get(
            "balanced_on",
            ["closer_object", "near_depth_bin", "cat_pair", "color_pair", "lateral_swap"],
        )
    )
    assignments = factorial_assignments(factors, n, rng, balanced_on=balanced_on)

    jitter = float(fcfg.get("depth_jitter", 0.0))
    min_gap = float(fcfg.get("min_gap", 0.25))
    unambiguous = bool(constraints.get("unambiguous_ordinal", True))
    ordinal_margin = float(constraints.get("ordinal_margin_m", 0.15))
    min_depth_ratio = float(constraints.get("min_depth_ratio", 1.0))
    ratio_floor_jitter = float(constraints.get("min_depth_ratio_jitter", 0.0))

    specs: list[SceneSpec] = []
    for i, a in enumerate(assignments):
        camera, camera_record = _jitter_camera(cam_cfg, render_cfg, rng)
        _, R_cv, t_cv, _ = geometry.camera_frame(
            camera.pos_world,
            camera.target_world,
            camera.f_mm,
            camera.sensor_width_mm,
            camera.res_x,
            camera.res_y,
        )
        axis = geometry.optical_axis(R_cv)
        t2 = float(t_cv[2])

        axis_bound = axis.copy()
        t2_bound = t2

        def _depth(
            x: float,
            y: float,
            z: float,
            *,
            axis: np.ndarray = axis_bound,
            t2: float = t2_bound,
        ) -> float:
            return float(axis[0]) * x + float(axis[1]) * y + float(axis[2]) * z + t2

        near_y_base = float(fcfg["near_depth_bins"][a["near_depth_bin"]]) + rng.uniform(
            -jitter, jitter
        )
        gap = float(fcfg["depth_gaps"][a["depth_gap_bin"]]) + rng.uniform(-jitter, jitter)
        gap = max(gap, min_gap)

        closer = a["closer_object"]
        farther = 1 - closer
        near_cat, far_cat = cat_pairs[a["cat_pair"]]
        near_col, far_col = color_pairs[a["color_pair"]]
        if near_cat == far_cat and near_col == far_col:
            alternatives = [c for c in range(len(color_items)) if c != near_col]
            far_col = int(rng.choice(alternatives))

        cats = {closer: near_cat, farther: far_cat}
        cols = {closer: color_items[near_col], farther: color_items[far_col]}
        near_mult, far_mult, size_record = _size_multipliers(cond, fcfg, rng)
        mult_by_role = {closer: near_mult, farther: far_mult}
        obj_size = {slot: size_by_cat[cats[slot]] * mult_by_role[slot] for slot in (0, 1)}

        # ⚠ These live under `condition:` in every config, NOT `constraints:` — read from cond
        # FIRST (constraints as fallback). They were read from `constraints` alone until 2026-07-18,
        # so the documented margins (bbox 14 px / frame 6 px) silently defaulted to 0 and the
        # attempts knob was stuck at 120: dead config that LOOKED set. Classic wrong-section bug.
        target_margin_px = float(cond.get("target_bbox_margin_px",
                                          constraints.get("target_bbox_margin_px", 0.0)))
        target_frame_margin_px = float(cond.get("target_frame_margin_px",
                                                constraints.get("target_frame_margin_px", 0.0)))
        max_attempts = int(cond.get("target_placement_attempts",
                                    constraints.get("target_placement_attempts", 120)))
        objects: list[ObjectSpec] = []
        placement_attempt = -1
        for attempt in range(max_attempts):
            near_y = near_y_base
            far_y = near_y + gap
            near_x, far_x, lateral_record = _sample_lateral(fcfg, a["lateral_swap"], rng)

            z_near = _rest_height(cats[closer], obj_size[closer])
            z_far = _rest_height(cats[farther], obj_size[farther])
            d_near = _depth(near_x, near_y, z_near)
            required_d_far = _depth(far_x, far_y, z_far)

            if unambiguous:
                h_near = geometry.half_extent_along(cats[closer], obj_size[closer], axis)
                h_far = geometry.half_extent_along(cats[farther], obj_size[farther], axis)
                required_d_far = max(required_d_far, d_near + abs(h_near - h_far) + ordinal_margin)
            # Pre-floor state, captured for the §5 clamp audit (check C). `clamped_fraction` is
            # defined as #{r_raw < r_floor} / N, so the RAW ratio has to be observed per image —
            # it cannot be recovered afterwards from the output, and re-running with a
            # non-binding floor produces different placements rather than a paired comparison.
            d_far_pre_floor = required_d_far
            floor = float("nan")
            if min_depth_ratio > 1.0:
                floor = min_depth_ratio * (1.0 + rng.uniform(0.0, ratio_floor_jitter))
                required_d_far = max(required_d_far, floor * d_near)
            if abs(axis[1]) > 1e-9:
                far_y = (
                    required_d_far - t2 - float(axis[0]) * far_x - float(axis[2]) * z_far
                ) / float(axis[1])

            depth_y = {closer: near_y, farther: far_y}
            xpos = {closer: near_x, farther: far_x}
            candidate: list[ObjectSpec] = []
            for slot in (0, 1):
                cat = cats[slot]
                cname, crgb = cols[slot]
                s = obj_size[slot]
                z = _rest_height(cat, s)
                candidate.append(
                    ObjectSpec(f"{cname}_{cat}", cat, list(crgb), s, [xpos[slot], depth_y[slot], z])
                )
            box0 = _projected_box(camera, candidate[0], margin_px=target_margin_px)
            box1 = _projected_box(camera, candidate[1], margin_px=target_margin_px)
            ok = (
                box0 is not None
                and box1 is not None
                and _box_in_frame(box0, camera.res_x, camera.res_y, target_frame_margin_px)
                and _box_in_frame(box1, camera.res_x, camera.res_y, target_frame_margin_px)
                and not _boxes_overlap(box0, box1)
            )
            if proposal_log is not None:
                # Rejection-sampling bias audit (ruling 2): the placement guard is a selection
                # operator, so log EVERY proposal (pose fixed per image, positions re-drawn per
                # attempt) with its accept/reject verdict. A pose↔position correlation that is ~0
                # over proposals but nonzero over accepted-only means the guard re-introduced the
                # correlation the camera jitter removed. Logging never consumes RNG.
                proposal_log.append(
                    {"image": i, "attempt": attempt, "near_x": near_x, "far_x": far_x,
                     "accepted": ok, **camera_record}
                )
            if ok:
                objects = candidate
                placement_attempt = attempt
                if ratio_log is not None:
                    ratio_log.append(
                        {
                            "image": i,
                            "near_category": cats[closer],
                            "far_category": cats[farther],
                            "depth_gap_bin": a["depth_gap_bin"],
                            "near_depth_bin": a["near_depth_bin"],
                            "depth_near": d_near,
                            "ratio_raw": d_far_pre_floor / d_near,
                            "ratio_realized": required_d_far / d_near,
                            "floor": floor,
                            "clamped": bool(
                                floor == floor and floor * d_near > d_far_pre_floor
                            ),
                        }
                    )
                break
        if not objects:
            if raise_on_placement_failure:
                raise RuntimeError(
                    f"could not place non-overlapping target pair after {max_attempts} attempts "
                    f"for {set_name}_{i:05d}; loosen lateral_range or size_multiplier_range"
                )
            if placement_failures is not None:
                placement_failures.append(
                    {"image": i, "near_depth_bin": a["near_depth_bin"],
                     "depth_gap_bin": a["depth_gap_bin"], "near_cat": near_cat, "far_cat": far_cat,
                     "size_mult_near": near_mult, "size_mult_far": far_mult}
                )
            continue  # DRY-RUN AUDIT: skip the un-placeable image and keep going
        distractors = _make_distractors(config, size_by_cat, color_items, rng, camera, objects)
        objects.extend(distractors)

        ground_color, sun_energy, sun_direction = _sample_scene_appearance(scene_cfg, rng)
        factors_record = {
            "regime": cond.get("regime", cond.get("name", "natural_congruent")),
            "near_depth_bin": a["near_depth_bin"],
            "depth_gap_bin": a["depth_gap_bin"],
            "closer_object": closer,
            "target_object_indices": [0, 1],
            "lateral_swap": a["lateral_swap"],
            "near_category": cats[closer],
            "far_category": cats[farther],
            "near_color": cols[closer][0],
            "far_color": cols[farther][0],
            "near_y": near_y,
            "far_y": far_y,
            "near_x": near_x,
            "far_x": far_x,
            "target_placement_attempt": placement_attempt,
            "size_condition": cond.get("size_condition", "congruent"),
            "elevation_condition": cond.get("elevation_condition", "congruent"),
            "distractor_count": len(distractors),
            # §4.2 (2026-07-18): PERSIST the scene-appearance factors that were sampled and
            # discarded — without them the DR3 held-out-lighting / held-out-background splits are
            # not constructible (a probe cannot be tested for generalization across a factor the
            # annotation does not record).
            "ground_color": list(ground_color),
            "sun_energy": float(sun_energy),
            "sun_direction": list(sun_direction),
            **lateral_record,
            **size_record,
            **camera_record,
        }

        specs.append(
            SceneSpec(
                id=f"{set_name}_{i:05d}",
                camera=camera,
                objects=objects,
                ground_color=ground_color,
                sun_energy=sun_energy,
                sun_direction=sun_direction,
                factors=factors_record,
            )
        )
    return specs


# =============================================================================================
# M4a-SOLO — Stage 1: single-object stimuli for representation LOCALIZATION
# =============================================================================================


def build_solo_scene_specs(
    config: dict,
    seed: int,
    raise_on_placement_failure: bool = True,
    placement_failures: list[dict] | None = None,
) -> list[SceneSpec]:
    """One object per image: category x depth x world-x x physical size x camera pose.

    CANONICAL FRAMING (ruled 2026-07-21, use verbatim):
        M4a-Solo isolates single-object depth availability without pairwise binding or congruence
        machinery. It removes multi-object selection ambiguity, but NOT monocular geometric
        confounds. Its role is to localize and characterize candidate depth representations before
        testing object binding and relational use in the pair battery.

    What solo does NOT need, because these exist only to make a PAIR's apparent-size cues
    congruent: near/far roles · `min_depth_ratio` floor · the congruence requirement R · depth
    ratio targets · category pairing · distractors · target-selection masks. The entire
    floor/envelope/R programme is a Stage-2 concern and is off this path.

    ⚠ WHAT SOLO DOES **NOT** REMOVE (correction, 2026-07-21). Monocular geometric baselines remain
    and must still be controlled: mask centroid (u, v), bbox position, projected area, apparent
    height/width, elevation, image-border distance, and camera-pose projection regularities all
    predict depth from a single object. Solo removes multi-object SELECTION AMBIGUITY, not image
    geometry.

    ⚠ AND CENTERING WOULD MAKE IT WORSE. Pinning the object to the image centre removes positional
    variation and thereby couples depth to retinal size MORE tightly. So this sampler deliberately
    varies world-x, camera translation/pitch/yaw, and PHYSICAL SIZE independently, so that
    retinal size is not a deterministic function of depth. `r(depth, retinal_size)` is the design
    metric to report: v0's pair set sat at -0.93, i.e. depth was ~86% predictable from apparent
    size alone, and that is exactly what solo must avoid re-creating.
    """
    rng = np.random.default_rng(seed)
    n = int(config["n_images"])
    set_name = config["output"]["set_name"]

    cam_cfg = config["camera"]
    render_cfg = config["render"]
    obj_cfg = config["objects"]
    scene_cfg = config.get("scene", {})
    cond = config.get("condition", {})
    fcfg = config["factors"]

    categories = list(obj_cfg["categories"])
    size_by_cat = _resolve_sizes(obj_cfg, categories)
    color_items = list(obj_cfg["colors"].items())

    depth_bins = list(fcfg["depth_bins"])            # camera-frame depth targets
    x_bins = list(fcfg["world_x_bins"])              # world-x, INDEPENDENT of depth
    size_mults = list(fcfg["size_multipliers"])      # physical size, INDEPENDENT of depth
    depth_jitter = float(fcfg.get("depth_jitter", 0.0))
    x_jitter = float(fcfg.get("world_x_jitter", 0.0))

    factors = {
        "category": list(range(len(categories))),
        "depth_bin": list(range(len(depth_bins))),
        "x_bin": list(range(len(x_bins))),
        "size_mult_bin": list(range(len(size_mults))),
        "color": list(range(len(color_items))),
    }
    balanced_on = list(
        config.get("balanced_on", ["category", "depth_bin", "x_bin", "size_mult_bin", "color"])
    )
    assignments = factorial_assignments(factors, n, rng, balanced_on=balanced_on)

    frame_margin = float(cond.get("target_frame_margin_px", 6.0))
    max_attempts = int(cond.get("target_placement_attempts", 200))

    specs: list[SceneSpec] = []
    for i, a in enumerate(assignments):
        cat = categories[a["category"]]
        cname, crgb = color_items[a["color"]]
        mult = float(size_mults[a["size_mult_bin"]])
        size = size_by_cat[cat] * mult
        z = _rest_height(cat, size)

        placed = None
        for attempt in range(max_attempts):
            camera, camera_record = _jitter_camera(cam_cfg, render_cfg, rng)
            _, R_cv, t_cv, _ = geometry.camera_frame(
                camera.pos_world, camera.target_world, camera.f_mm,
                camera.sensor_width_mm, camera.res_x, camera.res_y,
            )
            axis = geometry.optical_axis(R_cv)
            target_depth = float(depth_bins[a["depth_bin"]]) + rng.uniform(
                -depth_jitter, depth_jitter
            )
            x = float(x_bins[a["x_bin"]]) + rng.uniform(-x_jitter, x_jitter)
            if abs(float(axis[1])) < 1e-9:
                continue
            y = (
                target_depth - float(t_cv[2]) - float(axis[0]) * x - float(axis[2]) * z
            ) / float(axis[1])
            obj = ObjectSpec(f"{cname}_{cat}", cat, list(crgb), size, [x, y, z])
            box = _projected_box(camera, obj, margin_px=0.0)
            if box is None or not _box_in_frame(box, camera.res_x, camera.res_y, frame_margin):
                continue
            placed = (camera, camera_record, obj, target_depth, x, attempt)
            break

        if placed is None:
            if raise_on_placement_failure:
                raise RuntimeError(
                    f"could not place solo object after {max_attempts} attempts for "
                    f"{set_name}_{i:05d}; widen the frame margin or narrow depth/x bins"
                )
            if placement_failures is not None:
                placement_failures.append(
                    {"image": i, "category": cat, "depth_bin": a["depth_bin"],
                     "x_bin": a["x_bin"], "size_mult_bin": a["size_mult_bin"]}
                )
            continue

        camera, camera_record, obj, target_depth, x, attempt = placed
        ground_color, sun_energy, sun_direction = _sample_scene_appearance(scene_cfg, rng)
        factors_record = {
            "regime": cond.get("regime", "solo"),
            "category": cat,
            "color": cname,
            "depth_bin": a["depth_bin"],
            "x_bin": a["x_bin"],
            "size_mult_bin": a["size_mult_bin"],
            "target_depth": target_depth,
            "world_x": x,
            "world_y": float(obj.pos_world[1]),
            "size_multiplier": mult,
            "physical_size_m": size,
            "target_object_indices": [0],
            "placement_attempt": attempt,
            "ground_color": list(ground_color),
            "sun_energy": float(sun_energy),
            "sun_direction": list(sun_direction),
            **camera_record,
        }
        specs.append(
            SceneSpec(
                id=f"{set_name}_{i:05d}",
                camera=camera,
                objects=[obj],
                ground_color=ground_color,
                sun_energy=sun_energy,
                sun_direction=sun_direction,
                factors=factors_record,
            )
        )
    return specs
