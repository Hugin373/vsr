# Checkpoint briefing

Date: 2026-07-20 · describes repo state at commit `967fbf4`
This file always holds the LATEST completed checkpoint; git history holds the rest.

**Question.** The shared server's CPU is saturated by another user while four GPUs sit idle, and
the envelope sweep is CPU-only by project policy. Can the sweep render on GPU without changing the
silhouettes it measures — and is that actually faster?

**Method.** Added config-driven `render.device: GPU` with device selection through the existing
GPU guard (aborts if another user holds the device; sets `CUDA_VISIBLE_DEVICES`, so "one GPU only"
is enforced by masking). Validated by replaying two already-CPU-rendered stimulus sets through the
OPTIX path and comparing to their shipped annotations — the same check that validated the CPU path
originally. Then benchmarked 100 scenes.

**Results.**

| check | result |
|---|---|
| natural-congruent pilot, 89 objects | `retinal_size_px` max diff **0.000 px**, `mask_area_px` max diff **0 px** |
| conflict pilot (has distractors), 90 objects | **0.000 px / 0 px** |
| GPU throughput | 0.767 s/scene (78/min) |
| CPU throughput, uncontended | 0.17 s/scene (350/min) |
| CPU throughput, currently contended | ~2.9 s/scene (21/min) |

**Established.** The OPTIX path produces **byte-identical** silhouettes to CPU across 179 objects on
two sets. GPU rendering is therefore scientifically free — it cannot move the envelope.

A silent-fallback trap was closed on the way: setting `scene.cycles.device = "GPU"` alone does *not*
render on GPU. Cycles needs a compute device type selected and devices enabled; without them it
falls back to CPU **silently**, with the config claiming GPU and slowness as the only symptom. That
is the exact shape of this project's recurring bug class, so it now raises.

**NOT established, and it inverts the premise.** **GPU is 4.5× SLOWER than an uncontended CPU.** The
ID pass is one sample with zero bounces, so per-render GPU setup dominates a trivially small render.
GPU is a **contention fallback** (3.7× faster than the CPU is *right now*), not a general speedup.
The idea that moving to GPU would free future refinement cycles from CPU contention is only true
while the box is busy.

**Open decisions.** How to finish pass 2, now at ~45% on contended CPU:

| option | ETA | note |
|---|---|---|
| continue on CPU | 13.5 h contended, ~50 min if `li`'s jobs end | free; hostage to another user |
| restart on GPU | ~6.6 h | forfeits 4 h of completed work |
| run GPU in parallel, take the first to finish | ≤ 6.6 h | uses an idle resource; gives an independent cross-check for free |

**Weakest point.** The validation covers 179 objects from two sets rendered under one config. It
establishes the paths agree on those poses, not that they agree everywhere — in particular the
envelope sweep probes boundary poses that no rendered stimulus set contains, and those are exactly
where a rasterisation difference would be most likely to show. A stronger check would replay
adversarial boundary poses rather than shipped stimuli.

**Next step.** Recommend launching pass 2 on GPU 3 in parallel with the running CPU job (~6.6 h,
uses an otherwise-idle device, and the two runs must agree — free redundancy on a load-bearing
number). Awaiting your call before spending the GPU. Nothing else proceeds until R is ratified.
