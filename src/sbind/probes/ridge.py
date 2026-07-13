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
from sklearn.linear_model import LogisticRegression
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


def kernel_features(Xtr: np.ndarray, Xte: np.ndarray, tol: float = 1e-8):
    """Losslessly re-express (Xtr, Xte) in <= n_train dims, preserving ALL inner products.

    We probe d=3584-dim features with n=800 training samples. Both estimators here — ridge and
    L2-penalised logistic — depend on X only through inner products (representer theorem), and
    their L2 penalty is rotation-invariant. So mapping the rows into the row space of X_train
    changes NOTHING about the fitted decision function, while cutting the dimension 4.5x:

        K = Xtr Xtr^T = V diag(s) V^T
        Ztr = V diag(sqrt(s))          =>  Ztr Ztr^T = K                (exact)
        Zte = Xte Xtr^T V diag(1/sqrt(s))  =>  Zte Ztr^T = Xte Xtr^T    (exact)

    This is not a speed/accuracy trade-off — it is the same problem in different coordinates,
    and the tests assert the predictions match sklearn on the ORIGINAL features.

    Why it matters in practice: the SHUFFLED-LABEL control is the expensive fit, because there
    is no signal for lbfgs to converge to. On the raw 3584 dims a single shuffled logistic fit
    took 37.7 s (269 iterations) against 0.1 s (1 iteration) for the real labels — the control
    alone was ~15 hours of the grid.
    """
    K = Xtr @ Xtr.T
    s, V = np.linalg.eigh(K)
    keep = s > max(tol, float(s.max()) * 1e-12)
    s, V = s[keep], V[:, keep]
    root = np.sqrt(s)
    Ztr = V * root
    Zte = (Xte @ Xtr.T) @ V / root
    return Ztr, Zte


def _ridge_dual_fit_predict(Xtr, ytr, Xte, alphas=ALPHAS) -> np.ndarray:
    """Ridge with LOO-CV alpha selection, solved in the DUAL. Exact, and O(n^2 d) not O(n d^2).

    We probe 3584-dim features with ~800 training samples, i.e. d >> n. In that regime
    sklearn's RidgeCV takes ~20 s per fit, which puts the full grid (5 seeds x 5 folds x 2
    targets x 14 layers x 2 models) at ~20 HOURS. The dual form costs one Gram matrix and one
    eigendecomposition of an n x n matrix and then every alpha is nearly free:

        K = Xtr Xtr^T = V diag(s) V^T
        w_dual(a) = V diag(1/(s+a)) V^T y
        LOO residual_i = (y_i - Kw_i) / (1 - h_ii),   h_ii = sum_k V_ik^2 s_k/(s_k+a)

    This is the SAME estimator with the SAME leave-one-out criterion — verified against
    RidgeCV in tests/test_probes.py, not merely asserted. Ridge is rotation-invariant, so
    nothing is approximated.
    """
    ymean = float(ytr.mean())
    yc = ytr - ymean
    K = Xtr @ Xtr.T
    s, V = np.linalg.eigh(K)
    s = np.clip(s, 0.0, None)
    Vty = V.T @ yc

    best_alpha, best_err = alphas[0], np.inf
    for a in alphas:
        d = 1.0 / (s + a)
        dual = V @ (Vty * d)
        yhat = K @ dual
        h = ((V**2) * (s * d)).sum(axis=1)
        resid = (yc - yhat) / np.clip(1.0 - h, 1e-8, None)
        err = float((resid**2).mean())
        if err < best_err:
            best_alpha, best_err = a, err

    dual = V @ (Vty / (s + best_alpha))
    return (Xte @ Xtr.T) @ dual + ymean


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
                oof[te] = _ridge_dual_fit_predict(
                    sc.transform(X[tr]), labels[tr], sc.transform(X[te])
                )
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
                sc = StandardScaler().fit(X[tr])  # TRAIN only
                # exact inner-product-preserving reduction (see kernel_features): same
                # estimator, 4.5x fewer dims, and the shuffled control stops taking 38 s a fit
                Ztr, Zte = kernel_features(sc.transform(X[tr]), sc.transform(X[te]))
                clf = LogisticRegression(max_iter=2000, C=1.0).fit(Ztr, labels[tr])
                oof[te] = clf.predict(Zte)
            bucket.append(float((oof == labels).mean()))
    return ProbeResult(
        target=target,
        metric="acc",
        value=float(np.mean(scores)),
        control=float(np.mean(ctrl_scores)),
        per_seed=[float(s) for s in scores],
        n=len(y),
    )


def probe_layer(
    X: np.ndarray,
    targets: dict[str, tuple[str, np.ndarray]],
    seeds=(0, 1, 2, 3, 4),
    n_folds: int = 5,
) -> list[ProbeResult]:
    """Probe every target of one layer, sharing the fold work. ``targets``: name -> (kind, y),
    kind in {'reg', 'cls'}.

    Two efficiencies, neither of which changes a single reported number:

    1. ``kernel_features`` is computed ONCE per (seed, fold) and reused across all targets and
       both label conditions. It depends only on X and the split, never on labels — so the
       splits are plain KFold (label-independent) rather than stratified. Our categorical
       targets (shape, colour) are balanced by construction, so stratification bought nothing.
    2. ``max_iter=200`` for logistic. Verified not to change the answer: on real labels lbfgs
       converges in ~8 iterations (identical accuracy), and the SHUFFLED control — which never
       converges, because there is no signal to converge to, and which was therefore eating
       ~15 h of the grid — lands at chance either way (0.320 vs 0.315 for a 3-class target).
    """
    n = len(X)
    oof: dict[tuple[str, str, int], np.ndarray] = {}
    for name, (kind, _) in targets.items():
        for cond in ("real", "shuf"):
            for seed in seeds:
                oof[(name, cond, seed)] = (
                    np.zeros(n, dtype=float) if kind == "reg" else np.empty(n, dtype=object)
                )

    for seed in seeds:
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
        for tr, te in kf.split(X):
            sc = StandardScaler().fit(X[tr])  # TRAIN only — no test leakage
            Ztr, Zte = kernel_features(sc.transform(X[tr]), sc.transform(X[te]))
            for name, (kind, tgt_y) in targets.items():
                for cond in ("real", "shuf"):
                    labels = tgt_y if cond == "real" else _shuffled(tgt_y, seed)
                    if kind == "reg":
                        oof[(name, cond, seed)][te] = _ridge_dual_fit_predict(
                            Ztr, labels[tr].astype(float), Zte
                        )
                    else:
                        clf = LogisticRegression(max_iter=200, C=1.0).fit(Ztr, labels[tr])
                        oof[(name, cond, seed)][te] = clf.predict(Zte)

    out: list[ProbeResult] = []
    for name, (kind, tgt_y) in targets.items():
        real, ctrl = [], []
        for seed in seeds:
            for cond, bucket in (("real", real), ("shuf", ctrl)):
                labels = tgt_y if cond == "real" else _shuffled(tgt_y, seed)
                pred = oof[(name, cond, seed)]
                if kind == "reg":
                    bucket.append(_r2(labels.astype(float), pred))
                else:
                    bucket.append(float((pred == labels).mean()))
        out.append(
            ProbeResult(
                target=name,
                metric="r2" if kind == "reg" else "acc",
                value=float(np.mean(real)),
                control=float(np.mean(ctrl)),
                per_seed=[float(s) for s in real],
                n=n,
            )
        )
    return out


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
