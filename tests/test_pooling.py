"""Invariant tests for mask-pooling (M3.2 / M4).

The plan's known gotcha: "visual token <-> image location" differs per model family, so the
mask->token mapping must be tested per family — "render a probe dot, check the pooled token
responds". A mapping that is transposed or flipped still has the RIGHT TOKEN COUNT, so a
count check alone passes while every pooled feature is silently wrong.
"""

import numpy as np
import pytest
import torch

from sbind.extract.pooling import mask_pool, mask_to_token_weights


def _quadrant_mask(size=512, quadrant="tl"):
    m = np.zeros((size, size), dtype=bool)
    h = size // 2
    if quadrant == "tl":
        m[:h, :h] = True
    elif quadrant == "tr":
        m[:h, h:] = True
    elif quadrant == "bl":
        m[h:, :h] = True
    else:
        m[h:, h:] = True
    return m


@pytest.mark.parametrize(
    "quadrant,row_slice,col_slice",
    [("tl", slice(0, 12), slice(0, 12)), ("tr", slice(0, 12), slice(12, 24)),
     ("bl", slice(12, 24), slice(0, 12)), ("br", slice(12, 24), slice(12, 24))],
)
def test_mask_weights_land_in_the_right_quadrant(quadrant, row_slice, col_slice):
    """A top-left mask must weight top-left TOKENS. Catches a transposed or flipped grid."""
    w = mask_to_token_weights(_quadrant_mask(quadrant=quadrant), rows=24, cols=24)
    assert w.shape == (24, 24)
    inside = w[row_slice, col_slice].sum()
    assert inside == pytest.approx(w.sum(), rel=1e-6), (
        f"{quadrant} mask put weight outside its quadrant — the grid is flipped/transposed"
    )


def test_mask_weights_are_coverage_fractions():
    """Half-covered token cells get weight ~0.5, not 0 or 1 (coverage-weighted pooling)."""
    m = np.zeros((512, 512), dtype=bool)
    m[:, :256] = True  # exactly the left half
    w = mask_to_token_weights(m, rows=4, cols=4)
    assert w[:, :2] == pytest.approx(np.ones((4, 2)), abs=1e-3)
    assert w[:, 2:] == pytest.approx(np.zeros((4, 2)), abs=1e-3)

    m2 = np.zeros((512, 512), dtype=bool)
    m2[:, :192] = True  # 1.5 of 4 columns -> the 2nd token column is half covered
    w2 = mask_to_token_weights(m2, rows=4, cols=4)
    assert w2[0, 0] == pytest.approx(1.0, abs=1e-2)
    assert w2[0, 1] == pytest.approx(0.5, abs=0.05), "not an area average"


def test_mask_pool_matches_a_hand_computed_example():
    """Pooling correctness against an example computed by hand (plan §0)."""
    hidden = torch.tensor(
        [[1.0, 0.0], [3.0, 0.0], [5.0, 0.0], [7.0, 0.0]]  # 4 visual tokens, 2 dims
    )
    img_pos = [0, 1, 2, 3]
    w = np.array([[1.0, 0.0], [0.0, 1.0]])  # tokens 0 and 3, equally
    out = mask_pool(hidden, img_pos, w)
    assert out[0] == pytest.approx((1.0 + 7.0) / 2)

    w2 = np.array([[1.0, 1.0], [0.0, 0.0]])  # tokens 0 and 1
    assert mask_pool(hidden, img_pos, w2)[0] == pytest.approx((1.0 + 3.0) / 2)

    w3 = np.array([[0.5, 0.0], [0.0, 1.0]])  # weighted mean, not a plain mean
    assert mask_pool(hidden, img_pos, w3)[0] == pytest.approx((0.5 * 1.0 + 1.0 * 7.0) / 1.5)


def test_mask_pool_refuses_an_empty_mask():
    """A mask covering no token must RAISE, never silently return a zero vector."""
    hidden = torch.zeros(4, 2)
    with pytest.raises(ValueError, match="covers no visual token"):
        mask_pool(hidden, [0, 1, 2, 3], np.zeros((2, 2)))


def test_non_square_mask_is_rejected():
    """Registration assumes a square, un-cropped resize — a non-square input must not slip by."""
    with pytest.raises(ValueError, match="not square"):
        mask_to_token_weights(np.ones((100, 200), dtype=bool), rows=4, cols=4)
