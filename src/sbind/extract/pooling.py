"""Mask-pooling of visual tokens. [GPU-adjacent — pure mapping + pooling, no model calls]

Wang & Gao probe **mask-pooled object tokens** at LM decoder layers. That requires knowing
which visual tokens cover a given object — i.e. the mapping

    image pixel  ->  visual-token index  ->  position in the LM sequence

which is DIFFERENT for every model family (the plan flags this as a known gotcha: LLaVA has a
fixed 24x24 CLIP grid; Qwen2.5-VL uses native-resolution patches with a 2x2 merge; InternVL
tiles). Getting it silently wrong would pool the WRONG tokens and every probe number would be
meaningless while the pipeline ran green — so the grid is *derived* per model and then
CHECKED against the actual number of image tokens in the sequence:

    rows * cols  ==  number of image-token positions in input_ids

If that identity fails, we raise. It is the one thing that cannot be true by accident.
"""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image

from ..utils.logging import get_logger

log = get_logger("sbind.pooling")


def image_token_positions(vlm, inputs: dict) -> list[int]:
    """Positions in the LM sequence that hold image tokens."""
    cfg = vlm.model.config
    tok_id = getattr(cfg, "image_token_index", None)
    if tok_id is None:
        tok_id = getattr(cfg, "image_token_id", None)
    if tok_id is None:  # some configs nest it
        tok_id = getattr(getattr(cfg, "vision_config", object()), "image_token_id", None)
    if tok_id is None:
        raise RuntimeError(
            f"cannot find the image-token id for {type(vlm.model).__name__}. Add it explicitly "
            f"— never guess, or the pooling silently reads text tokens."
        )
    ids = vlm.token_ids(inputs)
    pos = [i for i, t in enumerate(ids) if t == tok_id]
    if not pos:
        raise RuntimeError("no image tokens found in the sequence")
    return pos


def token_grid(vlm, inputs: dict) -> tuple[int, int]:
    """(rows, cols) of the visual-token grid for this model + this input.

    Derived per family, then validated against the sequence — see the module docstring.
    """
    n_tokens = len(image_token_positions(vlm, inputs))

    # Qwen2-VL / Qwen2.5-VL: the processor hands us the patch grid directly, and a 2x2 merge
    # collapses it into the token grid.
    if "image_grid_thw" in inputs:
        thw = inputs["image_grid_thw"][0].tolist()
        _, h, w = int(thw[0]), int(thw[1]), int(thw[2])
        merge = int(getattr(vlm.model.config.vision_config, "spatial_merge_size", 2))
        rows, cols = h // merge, w // merge
    else:
        # CLIP/SigLIP-style fixed square grid (LLaVA-1.5, InternVL with a single tile).
        # NB InternVL's config gives image_size/patch_size as LISTS ([448, 448] / [14, 14]).
        vc = vlm.model.config.vision_config
        img_side = _scalar(vc.image_size)
        patch = _scalar(vc.patch_size)
        side = img_side // patch
        # InternVL pixel-unshuffles by `downsample_ratio` (0.5 -> the side halves)
        ratio = getattr(vlm.model.config, "downsample_ratio", None)
        if ratio:
            side = int(round(side * float(ratio)))
        rows = cols = side

        # InternVL TILES a large image into several 448px crops (+ a thumbnail). Then the
        # token stream is several grids concatenated and a single (rows, cols) is a lie. We
        # refuse to guess: pooling across an unknown tile layout would silently mis-register.
        if n_tokens != rows * cols:
            if rows and cols and n_tokens % (rows * cols) == 0:
                n_tiles = n_tokens // (rows * cols)
                raise RuntimeError(
                    f"{type(vlm.model).__name__} produced {n_tiles} tiles ({n_tokens} tokens "
                    f"= {n_tiles} x {rows}x{cols}). The mask->token mapping across tiles is "
                    f"not implemented. Force a single tile (processor max_num/max_patches = 1) "
                    f"so the grid is unambiguous, and record that as a deviation."
                )

    if rows * cols != n_tokens:
        raise RuntimeError(
            f"visual-token grid {rows}x{cols} = {rows * cols} does not match the "
            f"{n_tokens} image tokens actually in the sequence. The mask->token mapping would "
            f"be wrong and every pooled feature meaningless. Fix the grid derivation for "
            f"{type(vlm.model).__name__}."
        )
    return rows, cols


def _scalar(v) -> int:
    """Config fields are sometimes ints, sometimes [h, w] lists. Squares only — assert it."""
    if isinstance(v, (list, tuple)):
        if len(set(v)) != 1:
            raise ValueError(f"non-square vision config value {v}; the grid math assumes square")
        return int(v[0])
    return int(v)


def mask_to_token_weights(mask: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Coverage weights over the token grid: what fraction of each token's cell the mask covers.

    Area-averaging (not nearest-neighbour): a token whose cell is half covered gets weight
    0.5. This is the coverage-weighted pooling Wang & Gao describe.

    Assumes the processor's resize is aspect-preserving with no crop — true for our square
    (512x512) stimuli. A non-square image would need the processor's exact resize/crop, so
    this raises rather than silently mis-registering.
    """
    if mask.shape[0] != mask.shape[1]:
        raise ValueError(
            f"mask is {mask.shape}, not square — the token-grid registration assumes a square, "
            f"un-cropped resize. Handle the processor's crop explicitly before pooling."
        )
    m = Image.fromarray((mask.astype(np.float32) * 255).astype(np.uint8))
    # BOX = exact area average, which is what "fraction of the cell covered" means
    small = m.resize((cols, rows), Image.BOX)
    w = np.asarray(small, dtype=np.float32) / 255.0
    return w  # [rows, cols], in [0, 1]


def mask_pool(
    hidden: torch.Tensor,
    img_pos: list[int],
    weights: np.ndarray,
    min_weight: float = 1e-3,
) -> np.ndarray:
    """Coverage-weighted mean of the visual tokens a mask covers. hidden: [seq, hidden]."""
    w = weights.reshape(-1)
    if w.sum() < min_weight:
        raise ValueError(
            "mask covers no visual token (total weight ~0) — the object is smaller than one "
            "token cell, or the mapping is wrong. Do not return a zero vector silently."
        )
    idx = torch.tensor(img_pos)
    toks = hidden[idx].float().numpy()  # [n_tokens, hidden]
    return (toks * w[:, None]).sum(0) / w.sum()


def strip_pool(hidden: torch.Tensor, img_pos: list[int], rows: int, cols: int) -> np.ndarray:
    """All-visual-token pooling by horizontal strip -> [rows, hidden].

    Adopted from Dual Mechanisms v2: spatial signal is distributed across BACKGROUND tokens,
    so object-pooled-only probing underestimates what survives. M4's cache must keep this
    variant; M3.2 stores it so the comparison is available without a re-extraction.
    """
    idx = torch.tensor(img_pos)
    toks = hidden[idx].float().numpy().reshape(rows, cols, -1)
    return toks.mean(axis=1)


def check_grid_registration(vlm, inputs: dict, mask: np.ndarray, bbox_px: list[float]) -> dict:
    """INVARIANT: the tokens a mask weights must lie where the object actually is.

    A grid whose row/col count happens to match the token count can still be TRANSPOSED or
    flipped, and nothing downstream would complain — the probe would just quietly read the
    wrong tokens. So: compare the centroid of the mask's token weights against the object's
    bbox centre, both in normalised grid coordinates. They must agree.
    """
    rows, cols = token_grid(vlm, inputs)
    w = mask_to_token_weights(mask, rows, cols)
    if w.sum() <= 0:
        raise ValueError("mask covers no token")
    gy, gx = np.mgrid[0:rows, 0:cols]
    cy = float((gy * w).sum() / w.sum()) / max(rows - 1, 1)
    cx = float((gx * w).sum() / w.sum()) / max(cols - 1, 1)

    H = W = mask.shape[0]
    bx = ((bbox_px[0] + bbox_px[2]) / 2) / W
    by = ((bbox_px[1] + bbox_px[3]) / 2) / H
    return {
        "grid": (rows, cols),
        "token_centroid_xy": (cx, cy),
        "bbox_centre_xy": (bx, by),
        "err_x": abs(cx - bx),
        "err_y": abs(cy - by),
    }
