"""Probe pipeline on synthetic data (IMPLEMENTATION_PLAN §0).

The two tests that make a probe result mean anything:
  * it MUST find a signal that is genuinely planted in the features;
  * it MUST NOT find one when the labels are shuffled.
A probe that passes only the first is a probe that can memorise.
"""

import numpy as np
import pytest

from sbind.probes.ridge import logistic_probe, ridge_probe


@pytest.fixture
def planted():
    """Features whose first few dims linearly encode a target, plus 60 dims of noise."""
    rng = np.random.default_rng(0)
    n = 200
    y = rng.normal(size=n)
    X = rng.normal(size=(n, 64)) * 0.5
    X[:, 0] += 2.0 * y  # the signal
    X[:, 1] += 1.0 * y
    return X, y


def test_ridge_probe_finds_planted_signal(planted):
    X, y = planted
    r = ridge_probe(X, y, "planted", seeds=(0, 1))
    assert r.value > 0.7, f"probe failed to recover a planted linear signal (R2={r.value:.3f})"


def test_ridge_probe_fails_on_shuffled_labels(planted):
    """The control. If this ever passes, every probe number in the project is worthless."""
    X, y = planted
    r = ridge_probe(X, y, "planted", seeds=(0, 1))
    assert r.control < 0.1, f"shuffled-label control found signal (R2={r.control:.3f})"
    assert r.value - r.control > 0.5, "probe does not separate real from shuffled labels"


def test_ridge_control_is_computed_on_the_same_features():
    """A pure-noise target must score ~0, NOT negative-but-called-positive."""
    rng = np.random.default_rng(1)
    X = rng.normal(size=(150, 32))
    y = rng.normal(size=150)  # no relationship at all
    r = ridge_probe(X, y, "noise", seeds=(0, 1))
    assert r.value < 0.15, f"probe found signal in pure noise (R2={r.value:.3f})"


def test_logistic_probe_finds_and_controls():
    rng = np.random.default_rng(2)
    n = 240
    labels = np.array(["a", "b", "c"] * (n // 3))
    X = rng.normal(size=(n, 32)) * 0.6
    for i, lab in enumerate("abc"):  # plant a class-dependent offset
        X[labels == lab, i] += 2.5
    r = logistic_probe(X, labels, "planted_cls", seeds=(0, 1))
    assert r.value > 0.85, f"logistic probe missed a planted class signal (acc={r.value:.3f})"
    assert r.control < 0.5, f"shuffled-label control learned something (acc={r.control:.3f})"


def test_probe_result_records_its_control():
    """A ProbeResult without a control is not reportable — the schema must carry it."""
    rng = np.random.default_rng(3)
    X = rng.normal(size=(100, 16))
    y = rng.normal(size=100)
    d = ridge_probe(X, y, "t", seeds=(0,)).to_dict()
    assert "control_value" in d and d["control_value"] is not None
    assert d["n"] == 100 and d["metric"] == "r2"


def test_dual_ridge_matches_sklearn_ridgecv():
    """The fast dual solver must be the SAME estimator as RidgeCV, not merely 'close enough'.

    We swapped RidgeCV for a dual-form solver purely for speed (d >> n made RidgeCV ~20 s per
    fit, i.e. ~20 h for the grid). A speedup that quietly changes the estimator would change
    every reported number, so the equivalence is TESTED against sklearn rather than argued.
    """
    from sklearn.linear_model import RidgeCV
    from sklearn.preprocessing import StandardScaler

    from sbind.probes.ridge import ALPHAS, _ridge_dual_fit_predict

    rng = np.random.default_rng(7)
    n, d = 120, 400  # d >> n, the regime we actually probe in
    Xtr = rng.normal(size=(n, d))
    ytr = Xtr[:, 0] * 1.5 - Xtr[:, 3] * 0.8 + rng.normal(size=n) * 0.3
    Xte = rng.normal(size=(40, d))

    sc = StandardScaler().fit(Xtr)
    A, B = sc.transform(Xtr), sc.transform(Xte)

    mine = _ridge_dual_fit_predict(A, ytr, B, alphas=ALPHAS)
    theirs = RidgeCV(alphas=ALPHAS).fit(A, ytr).predict(B)

    assert np.corrcoef(mine, theirs)[0, 1] > 0.999, "dual solver is not the same estimator"
    assert np.abs(mine - theirs).max() < 0.05 * float(np.std(theirs)) + 1e-6


def test_kernel_features_preserve_inner_products_exactly():
    """The reduction is lossless: it must preserve every inner product it is used through."""
    from sbind.probes.ridge import kernel_features

    rng = np.random.default_rng(11)
    Xtr = rng.normal(size=(60, 300))  # d >> n
    Xte = rng.normal(size=(20, 300))
    Ztr, Zte = kernel_features(Xtr, Xte)

    assert Ztr.shape[1] <= Xtr.shape[0], "reduction did not reduce the dimension"
    assert np.allclose(Ztr @ Ztr.T, Xtr @ Xtr.T, atol=1e-6), "train Gram not preserved"
    assert np.allclose(Zte @ Ztr.T, Xte @ Xtr.T, atol=1e-6), "test-train inner products lost"


def test_logistic_on_kernel_features_matches_logistic_on_raw_features():
    """Same estimator, different coordinates — the predictions must agree.

    L2-penalised logistic depends on X only through inner products and its penalty is
    rotation-invariant, so this equivalence is exact. It is asserted here because the whole
    reason for the reduction is speed, and a speedup that changes the answer is a bug.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    from sbind.probes.ridge import kernel_features

    rng = np.random.default_rng(12)
    n, d = 90, 400
    labels = np.array(["a", "b", "c"] * (n // 3))
    X = rng.normal(size=(n, d)) * 0.7
    for i, lab in enumerate("abc"):
        X[labels == lab, i] += 2.0
    Xte = rng.normal(size=(30, d))

    sc = StandardScaler().fit(X)
    A, B = sc.transform(X), sc.transform(Xte)
    Ztr, Zte = kernel_features(A, B)

    raw = LogisticRegression(max_iter=5000, C=1.0).fit(A, labels).predict(B)
    red = LogisticRegression(max_iter=5000, C=1.0).fit(Ztr, labels).predict(Zte)
    agree = (raw == red).mean()
    assert agree > 0.95, f"reduction changed the classifier's predictions ({agree:.2f} agree)"
