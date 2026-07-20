"""Two-path forensic reproduction of the depth-4.983 endpoint violation (ruled 2026-07-21).

Evaluate the EXACT violating pose through both the sweep path and the verification path.
Identical C_a -> off-grid-axis hypothesis confirmed, optimizer may proceed.
Divergent C_a -> B16 semantic divergence; HALT and fix before the optimizer would inherit it.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "scripts")

from deterministic_cue_extremes import (  # noqa: E402
    _world_y_for_depth,
    camera_corners,
    reachable_ranges,
)

from sbind.stimuli import render_bpy as rb  # noqa: E402
from sbind.stimuli.sampler import (  # noqa: E402
    _box_in_frame,
    _projected_box,
    _resolve_sizes,
    _rest_height,
)
from sbind.stimuli.scene_spec import ObjectSpec, SceneSpec  # noqa: E402
from sbind.utils.config import load_config  # noqa: E402

e = json.load(open("/tmp/violating_pose.json"))
cfg = load_config("configs/m4a_v1_natural_congruent_pilot.yaml")
sizes = _resolve_sizes(cfg["objects"], cfg["objects"]["categories"])
cat, mult, lat, depth = e["category"], e["multiplier"], e["lateral"], e["depth"]
size = sizes[cat] * mult
z = _rest_height(cat, size)
tmp = Path("/tmp/forensic_id.png")

# find the camera corner matching the recorded axes
target_cam = e["camera"]
def match(rec):
    return all(abs(rec[k]-target_cam[k])<1e-6 for k in target_cam)
cam, cam_rec = next((c,r) for c,r in camera_corners(cfg) if match(r))

def measure(x, depth_val, label):
    y = _world_y_for_depth(cam, x, z, depth_val)
    obj = ObjectSpec(f"o_{cat}", cat, [0.8,0.05,0.05], size, [x, y, z])
    # guard admission (both paths apply it)
    bbox_m = float(cfg["condition"]["target_bbox_margin_px"])
    frame_m = float(cfg["condition"]["target_frame_margin_px"])
    gbox = _projected_box(cam, obj, margin_px=bbox_m)
    admitted = gbox is not None and _box_in_frame(gbox, cam.res_x, cam.res_y, frame_m)
    spec = SceneSpec(id="f", camera=cam, objects=[obj], ground_color=[0.45,0.45,0.48],
                     sun_energy=4.0, sun_direction=[5.,-5.,8.], factors={})
    scene = rb._reset_scene()
    g = rb._add_ground(spec.ground_color)
    objs = [rb._add_object(o,0) for o in spec.objects]
    _K, _R, _t = rb._add_camera(scene, spec)
    s_ = rb._add_sun(scene, spec)
    rb._configure_beauty(scene, cfg["render"])
    from sbind.stimuli import geometry
    masks = rb._render_id_pass(scene, objs, g, [s_], tmp)
    real_depth = float(geometry.project(_K, _R, _t, np.array([x,y,z]))[2])
    area = int(masks[0].sum())
    C_a = area * real_depth**2 / mult**2
    print(f"  {label}: depth_req={depth_val:.9f} real_depth={real_depth:.9f}")
    print(f"       admitted={admitted}  mask_area={area}px  C_a={C_a:.4f}")
    return C_a, area, y

print(f"POSE: {cat} mult={mult} lateral={lat} depth={depth:.9f} camera={target_cam}\n")

# PATH A — sweep: depth comes from the near grid endpoint (rounded to 6dp, as the sweep does)
ranges = reachable_ranges(cfg)
near_grid = np.linspace(*ranges["near"]["depth"], 21)
sweep_depth = round(float(near_grid[-1]), 6)   # exactly what the sweep uses
print("PATH A (sweep): depth = near-grid endpoint, rounded 6dp")
ca_sweep, area_s, y_s = measure(lat, sweep_depth, "sweep")

# PATH B — verification: depth from the 12-pt probe grid endpoint, NOT rounded
probe_depth = float(np.linspace(*ranges["near"]["depth"], 12)[-1])
print("\nPATH B (verification): depth = probe-grid endpoint, unrounded")
ca_verif, area_v, y_v = measure(lat, probe_depth, "verif")

print("\n=== VERDICT ===")
print(f"  sweep depth {sweep_depth:.9f} vs verif {probe_depth:.9f}")
print(f"  C_a sweep {ca_sweep:.4f}  vs C_a verif {ca_verif:.4f}  Δ={abs(ca_sweep-ca_verif):.4f} px")
print(f"  mask area {area_s} vs {area_v}  Δ={abs(area_s-area_v)} px")
print(f"  recorded violation value: {e['value']:.4f}")
if abs(ca_sweep - ca_verif) < 1.0:
    print("  -> PATHS AGREE. Off-grid-axis hypothesis: the sweep and verify measure identically;")
    print("     the sweep simply never evaluated the exact depth the verification did. PROCEED.")
else:
    print("  -> PATHS DIVERGE. B16 semantic divergence — HALT, fix before the optimizer.")
