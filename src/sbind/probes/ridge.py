"""Ridge / logistic probes with the controls that make a probe result mean anything. [CPU]

Every probe here reports THREE numbers, not one:

  value          the metric on real labels
  control        the SAME probe on SHUFFLED labels (must collapse to chance / R2<=0)
  n              how many samples it saw

A probe score without its shuffled-label control is uninterpretable — a high-dimensional
feature space can fit noise, and this project's whole thesis rests on distinguishing "the
information is there" from "the probe memorised the training set".

Protocol (from IMPLEMENTATION_PLAN M5, applied early here): 5 seeds x 5 folds, ridge alpha
chosen by inner CV, R2 reported out-of-fold. Scaling is fit on TRAIN only — fitting it on the
full set leaks test statistics into training and inflates R2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

ALPHAS = np.logspace(-1, 5, 13)


@dataclass
class ProbeResult:
    target: str
    metric: str  # 'r2' | 'acc'
    value: float
    control: float  # shuffled-label
    per_seed: list[float] = field(default_factory=list)
    n: int = 0

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "metric": self.metric,
            "value": self.value,
            "control_value": self.control,
            "per_seed": self.per_seed,
            "n": self.n,
        }


def _r2(y, yhat) -> float:
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def ridge_probe(
    X: np.ndarray, y: np.ndarray, target: str, seeds=(0, 1, 2, 3, 4), n_folds: int = 5
) -> ProbeResult:
    """Out-of-fold R2 for a continuous target, plus the shuffled-label control."""
    scores, ctrl_scores = [], []
    for seed in seeds:
        for labels, bucket in ((y, scores), (_shuffled(y, seed), ctrl_scores)):
            kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
            oof = np.zeros_like(labels, dtype=float)
            for tr, te in kf.split(X):
                sc = StandardScaler().fit(X[tr])  # TRAIN only — no test leakage
                model = RidgeCV(alphas=ALPHAS).fit(sc.transform(X[tr]), labels[tr])
                oof[te] = model.predict(sc.transform(X[te]))
            bucket.append(_r2(labels, oof))
    return ProbeResult(
        target=target,
        metric="r2",
        value=float(np.mean(scores)),
        control=float(np.mean(ctrl_scores)),
        per_seed=[float(s) for s in scores],
        n=len(y),
    )


def logistic_probe(
    X: np.ndarray, y: np.ndarray, target: str, seeds=(0, 1, 2, 3, 4), n_folds: int = 5
) -> ProbeResult:
    """Out-of-fold accuracy for a categorical target (the SEMANTIC controls), + shuffled ctrl."""
    scores, ctrl_scores = [], []
    for seed in seeds:
        for labels, bucket in ((y, scores), (_shuffled(y, seed), ctrl_scores)):
            skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
            oof = np.empty_like(labels)
            for tr, te in skf.split(X, labels):
                sc = StandardScaler().fit(X[tr])
                clf = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(X[tr]), labels[tr])
                oof[te] = clf.predict(sc.transform(X[te]))
            bucket.append(float((oof == labels).mean()))
    return ProbeResult(
        target=target,
        metric="acc",
        value=float(np.mean(scores)),
        control=float(np.mean(ctrl_scores)),
        per_seed=[float(s) for s in scores],
        n=len(y),
    )


def rsa_spearman(X: np.ndarray, d_true: np.ndarray, seed: int = 0) -> float:
    """RSA: Spearman rho between representational distances and true pairwise distances.

    Wang & Gao report pairwise 3D-distance RSA rho ~= 0.01 (i.e. nothing). ``d_true`` is the
    true pairwise distance for each SAMPLE PAIR; we compare it against the cosine distance
    between the two objects' pooled representations.
    """
    from scipy.stats import spearmanr

    rho, _ = spearmanr(X, d_true)
    return float(rho)


def _shuffled(y: np.ndarray, seed: int) -> np.ndarray:
    """A permutation of the labels. The control that keeps everyone honest."""
    rng = np.random.default_rng(1000 + seed)
    out = y.copy()
    rng.shuffle(out)
    return out
