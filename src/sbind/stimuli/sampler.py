"""Seeded factorial sampler: stimulus-set config -> balanced list of SceneSpec.

Determinism rule: the entire set is a pure function of (config, seed). ``balanced_on``
factors get near-equal marginal counts (e.g. the pairwise "which object is closer"
label is forced 50/50 so probes can't exploit a class imbalance); other factors are
sampled uniformly at random.

v0 (this milestone): congruent conditions only — two equal-physical-size objects rest
on the ground plane, so vertical position and retinal size both co-vary naturally with
depth. Conflict conditions (fixed-retinal-size, elevation-conflict) arrive in M4.
"""

from __future__ import annotations

import numpy as np

from .scene_spec import CameraSpec, ObjectSpec, SceneSpec


def balanced_levels(n: int, levels: list, rng: np.random.Generator) -> list:
    """A length-n list where each level appears ~n/len(levels) times, shuffled.

    Deterministic given ``rng``. The remainder (when n is not divisible) is spread over
    a random subset of levels, so counts differ by at most one.
    """
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
    """Return n factor-level assignments. ``balanced_on`` factors are marginally balanced.

    Each assignment is a dict mapping factor name -> chosen level. Non-balanced factors
    are sampled i.i.d. uniformly. Column order of RNG draws is fixed (sorted factor
    names) so the output is reproducible.
    """
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


def _rest_height(category: str, size_m: float) -> float:
    """Z of the object centre so it rests on the ground plane (z=0)."""
    # cube edge = sphere diameter = cylinder height = size_m; all sit with centre at
    # half their vertical extent above the ground.
    return size_m / 2.0


def build_scene_specs(config: dict, seed: int) -> list[SceneSpec]:
    """Turn a stimulus-set config dict into a deterministic list of SceneSpec.

    See configs/stimuli_v0_congruent.yaml for the expected shape.
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

    size_m = float(obj_cfg["size_m"])
    categories = list(obj_cfg["categories"])
    color_items = list(obj_cfg["colors"].items())  # [(name, rgb), ...]
    lateral = float(fcfg["lateral_offset"])
    # continuous depth: bin centres are jittered so depth is not a handful of discrete
    # values (a discrete target would make ratio/absolute regression probes artificially
    # easy and would alias with the bin factor).
    jitter = float(fcfg.get("depth_jitter", 0.0))
    min_gap = float(fcfg.get("min_gap", 0.25))

    # Factor levels sampled per image.
    factors = {
        "near_depth_bin": list(range(len(fcfg["near_depth_bins"]))),
        "depth_gap_bin": list(range(len(fcfg["depth_gaps"]))),
        "closer_object": [0, 1],
        "lateral_swap": [0, 1],
        "cat_a": categories,
        "cat_b": categories,
        "color_a": list(range(len(color_items))),
        "color_b": list(range(len(color_items))),
    }
    assignments = factorial_assignments(
        factors, n, rng, balanced_on=["closer_object", "near_depth_bin"]
    )

    specs: list[SceneSpec] = []
    for i, a in enumerate(assignments):
        near_y = float(fcfg["near_depth_bins"][a["near_depth_bin"]]) + rng.uniform(-jitter, jitter)
        gap = float(fcfg["depth_gaps"][a["depth_gap_bin"]]) + rng.uniform(-jitter, jitter)
        gap = max(gap, min_gap)  # keep the pair strictly ordered in depth
        far_y = near_y + gap

        # lateral placement: near object on one side, far on the other (swap by factor)
        near_x = -lateral if a["lateral_swap"] == 0 else lateral
        far_x = -near_x

        # which slot (obj0/obj1) is the nearer object
        closer = a["closer_object"]
        depth_y = {closer: near_y, 1 - closer: far_y}
        xpos = {closer: near_x, 1 - closer: far_x}

        # the two objects must be distinguishable: never identical in BOTH category and
        # colour (an identical pair makes "which object is closer?" unanswerable).
        cat_a, cat_b = a["cat_a"], a["cat_b"]
        col_a, col_b = a["color_a"], a["color_b"]
        if cat_a == cat_b and col_a == col_b:
            alternatives = [c for c in range(len(color_items)) if c != col_a]
            col_b = int(rng.choice(alternatives))

        cats = {0: cat_a, 1: cat_b}
        cols = {0: color_items[col_a], 1: color_items[col_b]}

        objects = []
        for slot in (0, 1):
            cat = cats[slot]
            cname, crgb = cols[slot]
            z = _rest_height(cat, size_m)
            objects.append(
                ObjectSpec(
                    name=f"{cname}_{cat}",
                    category=cat,
                    color=list(crgb),
                    size_m=size_m,
                    pos_world=[xpos[slot], depth_y[slot], z],
                )
            )

        camera = CameraSpec(
            pos_world=list(cam_cfg["pos_world"]),
            target_world=list(cam_cfg["target_world"]),
            f_mm=float(cam_cfg["f_mm"]),
            sensor_width_mm=float(cam_cfg["sensor_width_mm"]),
            res_x=int(render_cfg["res_x"]),
            res_y=int(render_cfg["res_y"]),
        )

        factors_record = {
            "near_depth_bin": a["near_depth_bin"],
            "depth_gap_bin": a["depth_gap_bin"],
            "closer_object": closer,
            "lateral_swap": a["lateral_swap"],
            "near_y": near_y,
            "far_y": far_y,
            "size_condition": cond.get("size_condition", "congruent"),
            "elevation_condition": cond.get("elevation_condition", "congruent"),
        }

        specs.append(
            SceneSpec(
                id=f"{set_name}_{i:05d}",
                camera=camera,
                objects=objects,
                ground_color=list(scene_cfg.get("ground_color", [0.5, 0.5, 0.5])),
                sun_energy=float(scene_cfg.get("sun_energy", 4.0)),
                sun_direction=list(scene_cfg.get("sun_direction", [5.0, -5.0, 8.0])),
                factors=factors_record,
            )
        )
    return specs
