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
