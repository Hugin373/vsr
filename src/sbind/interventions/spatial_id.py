"""Kang et al. spatial IDs: derivation, mirror-swap patching, steering. [GPU]

⚠ REIMPLEMENTED FROM THE PAPER (arXiv 2601.12626). `Raphoo/linear-mech-vlms` has NO LICENSE —
it was read for understanding only; no code copied. (CLAUDE.md hard rule.)

The three claims we reproduce:

1. **Spatial IDs exist.** For object o at grid cell (i,j), take the residual-stream activation
   at o's WORD TOKEN at LM layer L, and mean-centre it per object:

       Δ_L(o, i, j) = φ_L(o | o at (i,j))  −  mean_{cells} φ_L(o | ·)

   Averaging Δ over objects leaves a code for POSITION with object identity cancelled:

       ID_L(i,j) = mean_o Δ_L(o, i, j)

   This is arithmetic, not a trained probe — which is what makes it strong evidence. It is
   only valid if object identity is decorrelated from cell (enforced + checked in
   stimuli/grid_scenes.py); otherwise the "position code" is partly an object code.

2. **They are causal (steering).** Add the mirror-difference direction at the object-word
   token and the model's binary left/right belief flips:

       d = ID_L(i,j) − ID_L(m−1−i, j)        (i = COLUMN, so this mirrors left↔right)
       x_L[q] ← x_L[q] + α · ‖x_L[q]‖ · d/‖d‖      (α = 5 in the paper)

   Control: a random direction of the SAME norm. Paper: 64.4% belief-swap vs 29.5% noise.

3. **They are bound at middle layers (mirror-swap patching).** Run the model on an image and
   on its left-right mirror; patch activations from the mirrored run into the original at one
   (layer, token-group) and measure the normalised belief shift:

       shift = (P_orig(GT) − P_patched(GT)) / (P_orig(GT) − P_mirror(GT))

   0 = no effect, 1 = fully adopts the mirrored belief. Paper's profile: image patches move it
   EARLY, object-word tokens in the MIDDLE, text tokens LATE.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from ..extract.vlm import VLM, Edit
from ..utils.logging import get_logger

log = get_logger("sbind.spatial_id")

# The question the binary belief is read off. Kang ask a forced-choice relation; we keep the
# wording fixed across all conditions so only the intervention varies.
PROMPT_LR = "Is the {a} to the left or right of the {b}? Answer with one word."
OPTIONS_LR = ("left", "right")


@dataclass
class SpatialIDs:
    """ID_L(i,j) for one layer: [m, m, hidden], plus the per-object counts behind it."""

    layer: int
    ids: np.ndarray  # [m, m, hidden]
    grid_m: int
    n_objects: int
    counts: np.ndarray  # [m, m] — how many (object, image) samples per cell

    def direction_mirror_lr(self, col: int, row: int) -> np.ndarray:
        """ID(col,row) − ID(m−1−col, row): the left↔right mirror direction."""
        return self.ids[col, row] - self.ids[self.grid_m - 1 - col, row]


def derive_spatial_ids(
    vlm: VLM,
    scenes: list,
    layers: list[int],
    grid_m: int = 4,
    batch_log_every: int = 100,
) -> dict[int, SpatialIDs]:
    """Mean-centred, object-averaged position code per (layer, cell). One forward per scene.

    Both objects in a scene contribute a sample (each at its own cell, read at its own word
    token), so a scene yields two (object, cell) observations.
    """
    hidden = None
    # sums[object][cell] -> running sum of activations; per-object mean is subtracted after
    acc: dict[int, dict[str, dict[tuple[int, int], list[np.ndarray]]]] = {
        L: {} for L in layers
    }

    for n, sc in enumerate(scenes):
        from PIL import Image

        img = Image.open(sc.image).convert("RGB")
        prompt = PROMPT_LR.format(a=sc.obj_a, b=sc.obj_b)
        inputs = vlm.build_inputs(img, prompt)

        # the word token of each object, in the prompt
        try:
            pos_a = vlm.find_word_positions(inputs, sc.obj_a)[0]
            pos_b = vlm.find_word_positions(inputs, sc.obj_b)[-1]
        except ValueError as e:
            raise RuntimeError(f"{sc.id}: {e}") from e

        _, caps = vlm.forward(inputs, capture_layers=layers)
        for L in layers:
            hs = caps[L][0]  # [seq, hidden]
            hidden = hs.shape[-1]
            for name, pos, cell in ((sc.obj_a, pos_a, sc.cell_a), (sc.obj_b, pos_b, sc.cell_b)):
                acc[L].setdefault(name, {}).setdefault(cell, []).append(
                    hs[pos].numpy().astype(np.float64)
                )
        if batch_log_every and (n + 1) % batch_log_every == 0:
            log.info("spatial-id pass: %d/%d scenes", n + 1, len(scenes))

    out: dict[int, SpatialIDs] = {}
    for L in layers:
        ids = np.zeros((grid_m, grid_m, hidden))
        counts = np.zeros((grid_m, grid_m))
        contrib = np.zeros((grid_m, grid_m))
        for _name, by_cell in acc[L].items():
            # per-object mean over the cells that object was seen in (φ̄_L(o))
            all_vecs = [v for vs in by_cell.values() for v in vs]
            obj_mean = np.mean(all_vecs, axis=0)
            for cell, vs in by_cell.items():
                delta = np.mean(vs, axis=0) - obj_mean  # Δ_L(o, cell)
                ids[cell[0], cell[1]] += delta
                contrib[cell[0], cell[1]] += 1
                counts[cell[0], cell[1]] += len(vs)
        # average over the OBJECTS that visited each cell — identity cancels, position survives
        ids /= np.maximum(contrib[..., None], 1)
        out[L] = SpatialIDs(
            layer=L, ids=ids, grid_m=grid_m, n_objects=len(acc[L]), counts=counts
        )
    return out


def belief(vlm: VLM, inputs: dict, edits=None) -> dict[str, float]:
    """P(left) vs P(right), renormalised over the two options."""
    logits, _ = vlm.forward(inputs, edits=edits)
    lp = vlm.option_logprobs(logits, OPTIONS_LR)
    m = max(lp.values())
    ex = {k: np.exp(v - m) for k, v in lp.items()}
    z = sum(ex.values())
    return {k: v / z for k, v in ex.items()}


def steer_belief_swap(
    vlm: VLM,
    scenes: list,
    sids: dict[int, SpatialIDs],
    layer: int,
    alpha: float = 5.0,
    seed: int = 0,
) -> dict:
    """Steer the object-word token with the mirror direction; count binary belief swaps.

    Reports the paper's headline pair: the spatial-ID swap rate and the NORM-MATCHED NOISE
    control. The control is the whole point — a large-norm perturbation in *any* direction
    disrupts a belief, so an uncontrolled swap rate proves nothing.
    """
    from PIL import Image

    rng = np.random.default_rng(seed)
    sid = sids[layer]

    swapped_id = swapped_noise = 0
    correct_before = 0
    n = 0
    for sc in scenes:
        img = Image.open(sc.image).convert("RGB")
        prompt = PROMPT_LR.format(a=sc.obj_a, b=sc.obj_b)
        inputs = vlm.build_inputs(img, prompt)
        pos_a = vlm.find_word_positions(inputs, sc.obj_a)[0]

        # ONE forward gives both the baseline belief and the activation norm that sets the
        # intervention scale (capture and readout happen in the same pass).
        logits, caps = vlm.forward(inputs, capture_layers=[layer])
        lp = vlm.option_logprobs(logits, OPTIONS_LR)
        mx = max(lp.values())
        ex = {k: np.exp(v - mx) for k, v in lp.items()}
        z = sum(ex.values())
        base = {k: v / z for k, v in ex.items()}
        pred0 = max(base, key=base.get)
        correct_before += pred0 == sc.relation_lr
        n += 1

        x_norm = float(np.linalg.norm(caps[layer][0][pos_a].numpy()))

        d = sid.direction_mirror_lr(*sc.cell_a)
        nd = np.linalg.norm(d)
        if nd < 1e-8:  # a centre column mirrors onto itself -> no direction to steer along
            continue
        v = torch.from_numpy((d / nd) * (alpha * x_norm))
        b_id = belief(vlm, inputs, edits=[Edit(layer, [pos_a], v, "add")])
        swapped_id += max(b_id, key=b_id.get) != pred0

        # NORM-MATCHED NOISE: same magnitude, random direction
        z = rng.normal(size=d.shape)
        z /= np.linalg.norm(z)
        vz = torch.from_numpy(z * (alpha * x_norm))
        b_nz = belief(vlm, inputs, edits=[Edit(layer, [pos_a], vz, "add")])
        swapped_noise += max(b_nz, key=b_nz.get) != pred0

    return {
        "layer": layer,
        "alpha": alpha,
        "n": n,
        "acc_before": correct_before / max(n, 1),
        "swap_spatial_id": swapped_id / max(n, 1),
        "swap_noise": swapped_noise / max(n, 1),
        "above_chance": (swapped_id - swapped_noise) / max(n, 1),
    }


def mirror_swap_patch_profile(
    vlm: VLM,
    scenes: list,
    layers: list[int],
    token_groups: tuple[str, ...] = ("image", "object_word", "text"),
) -> list[dict]:
    """Patch activations from the MIRRORED image's run into the original, per (layer, group).

    Localises where the spatial belief is carried. Normalised belief shift:
        (P_orig(GT) − P_patched(GT)) / (P_orig(GT) − P_mirror(GT))
    """
    from PIL import Image

    # scene-OUTER: the baseline and mirrored beliefs, and the mirrored run's activations at
    # every scanned layer, are computed ONCE per scene and reused across all (layer, group)
    # cells. Recomputing them per cell tripled the forward count for no information.
    shifts: dict[tuple[int, str], list[float]] = {
        (L, g): [] for L in layers for g in token_groups
    }
    skipped_flat = 0

    for n, sc in enumerate(scenes):
        img = Image.open(sc.image).convert("RGB")
        mir = img.transpose(Image.FLIP_LEFT_RIGHT)
        prompt = PROMPT_LR.format(a=sc.obj_a, b=sc.obj_b)

        in_o = vlm.build_inputs(img, prompt)
        in_m = vlm.build_inputs(mir, prompt)
        gt = sc.relation_lr

        p_o = belief(vlm, in_o)[gt]
        p_m = belief(vlm, in_m)[gt]
        denom = p_o - p_m
        if abs(denom) < 0.05:
            # the mirror did not move the belief: the normalised shift would divide by ~0 and
            # explode. Counted and reported — never a silent drop.
            skipped_flat += 1
            continue

        # one pass over the mirrored image captures the patch SOURCE for every layer
        _, caps_m = vlm.forward(in_m, capture_layers=list(layers))
        groups = {g: _group_positions(vlm, in_o, sc, g) for g in token_groups}

        for L in layers:
            src = caps_m[L][0]
            for g, idx in groups.items():
                edits = [Edit(L, [p], src[p], "replace") for p in idx if p < src.shape[0]]
                if not edits:
                    continue
                p_patched = belief(vlm, in_o, edits=edits)[gt]
                shifts[(L, g)].append((p_o - p_patched) / denom)
        if (n + 1) % 20 == 0:
            log.info("patching: %d/%d scenes", n + 1, len(scenes))

    if skipped_flat:
        log.warning(
            "patching: %d/%d scenes skipped — mirroring moved the belief by <0.05, so the "
            "normalised shift is undefined for them",
            skipped_flat, len(scenes),
        )

    rows: list[dict] = []
    for L in layers:
        for g in token_groups:
            v = shifts[(L, g)]
            rows.append(
                {
                    "layer": L,
                    "token_group": g,
                    "n": len(v),
                    "belief_shift": float(np.mean(v)) if v else float("nan"),
                    "belief_shift_median": float(np.median(v)) if v else float("nan"),
                }
            )
    return rows


def _group_positions(vlm: VLM, inputs: dict, scene, group: str) -> list[int]:
    """Token positions of one group: the image patches, the object words, or the text."""
    ids = vlm.token_ids(inputs)
    img_tok = getattr(vlm.model.config, "image_token_index", None)
    if img_tok is None:
        img_tok = getattr(vlm.model.config, "image_token_id", None)
    image_pos = [i for i, t in enumerate(ids) if t == img_tok] if img_tok is not None else []

    if group == "image":
        if not image_pos:
            raise RuntimeError(
                "no image tokens found — the image-token id is not where we expect it. "
                "Fix the mapping rather than silently patching nothing."
            )
        return image_pos
    if group == "object_word":
        return sorted(
            set(
                vlm.find_word_positions(inputs, scene.obj_a)
                + vlm.find_word_positions(inputs, scene.obj_b)
            )
        )
    if group == "text":
        return [i for i in range(len(ids)) if i not in set(image_pos)]
    raise ValueError(f"unknown token group {group!r}")


def positional_basis_rank_r2(sids: SpatialIDs, max_rank: int = 8) -> list[dict]:
    """How much of the spatial-ID structure is a LOW-RANK code over the grid?

    Kang report that spatial IDs are ≈ a **rank-3** linear transform of the encoder's
    positional-encoding basis (R² ≳ 0.85). We test the same shape of claim in the form the
    grid gives us directly: regress ID_L(i,j) onto its own top-k principal components across
    cells and report the variance explained per rank. A sharp elbow at rank ~3 with R² ≳ 0.85
    reproduces the qualitative claim; the numbers are not expected to match to the decimal.
    """
    m = sids.grid_m
    X = sids.ids.reshape(m * m, -1)  # [cells, hidden]
    Xc = X - X.mean(axis=0, keepdims=True)
    total = float((Xc**2).sum())
    if total < 1e-12:
        return [{"rank": r, "r2": 0.0} for r in range(1, max_rank + 1)]
    # SVD over cells: how many components span the position code?
    _, S, _ = np.linalg.svd(Xc, full_matrices=False)
    out = []
    cum = 0.0
    for r in range(1, min(max_rank, len(S)) + 1):
        cum = float((S[:r] ** 2).sum())
        out.append({"rank": r, "r2": cum / total})
    return out
