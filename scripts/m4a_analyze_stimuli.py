"""M4a stimulus analysis: decorrelations, leak ceiling, and identifiability gate.

This is CPU-only and reads rendered annotations/masks. It deliberately analyzes the
OUTPUT of a stimulus set rather than assuming the sampler achieved its requested factors.

Examples:
  uv run --extra analysis scripts/m4a_analyze_stimuli.py \
    --set $DATA_ROOT/stimuli/m4a_v1_counterbalanced \
    --out reports/m4a_counterbalanced_analysis.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import GroupKFold, KFold
from sklearn.preprocessing import StandardScaler

from sbind.utils.io import read_jsonl

ALPHAS = np.logspace(-1, 5, 13)


def _centroid(o: dict) -> tuple[float, float]:
    x0, y0, x1, y1 = o["bbox_px"]
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def _object_rows(anns: list[dict]) -> list[dict]:
    rows = []
    for ann in anns:
        fac = ann.get("factors", {})
        targets = fac.get("target_object_indices", [0, 1])
        for slot in targets:
            o = ann["objects"][slot]
            cu, cv = _centroid(o)
            role = "near" if slot == fac.get("closer_object") else "far"
            rows.append(
                {
                    "image_id": ann["id"],
                    "slot": slot,
                    "role": role,
                    "category": o["category"],
                    "color": o["name"].split("_")[0],
                    "depth_m": float(o["depth_m"]),
                    "x_cam": float(o["pos_cam"][0]),
                    "size_m": float(o["size_m"]),
                    "centroid_u": cu,
                    "centroid_v": cv,
                    "mask_area_px": float(o["mask_area_px"]),
                    "bbox_w": float(o["bbox_px"][2] - o["bbox_px"][0]),
                    "bbox_h": float(o["bbox_px"][3] - o["bbox_px"][1]),
                    "retinal_size_px": float(o["retinal_size_px"]),
                    "elevation_px": float(o["elevation_px"]),
                    "near_depth_bin": fac.get("near_depth_bin"),
                    "depth_gap_bin": fac.get("depth_gap_bin"),
                    "camera_yaw_bin": _bin_value(
                        float(fac.get("camera_yaw_delta_deg", 0.0)), [-1.5, 0.0, 1.5]
                    ),
                    "camera_pitch_bin": _bin_value(
                        float(fac.get("camera_pitch_delta_deg", 0.0)), [-1.25, 0.0, 1.25]
                    ),
                }
            )
    return rows


def _pair_rows(anns: list[dict]) -> list[dict]:
    rows = []
    for ann in anns:
        if len(ann["objects"]) < 2:
            continue
        fac = ann.get("factors", {})
        a, b = ann["objects"][0], ann["objects"][1]
        rel = ann["pair_relations"]["(0,1)"]
        fa, fb = _object_feature_dict(a), _object_feature_dict(b)
        feat = {f"a_{k}": v for k, v in fa.items()} | {f"b_{k}": v for k, v in fb.items()}
        for k in (
            "centroid_u",
            "centroid_v",
            "mask_area_px",
            "bbox_w",
            "bbox_h",
            "retinal_size_px",
            "elevation_px",
        ):
            feat[f"diff_{k}"] = fa[k] - fb[k]
            feat[f"absdiff_{k}"] = abs(fa[k] - fb[k])
        rows.append(
            {
                "image_id": ann["id"],
                "features": feat,
                "ordinal": rel["ordinal_depth_surface"],
                "ratio": float(rel["dist_ratio"]),
                "near_depth_bin": fac.get("near_depth_bin"),
                "depth_gap_bin": fac.get("depth_gap_bin"),
                "category_pair": f"{a['category']}|{b['category']}",
                "cue_combo": (
                    f"{fac.get('near_category')}->{fac.get('far_category')}"
                    f"|{fac.get('size_condition')}"
                ),
            }
        )
    return rows


def _object_feature_dict(o: dict) -> dict:
    cu, cv = _centroid(o)
    return {
        "centroid_u": cu,
        "centroid_v": cv,
        "mask_area_px": float(o["mask_area_px"]),
        "bbox_w": float(o["bbox_px"][2] - o["bbox_px"][0]),
        "bbox_h": float(o["bbox_px"][3] - o["bbox_px"][1]),
        "retinal_size_px": float(o["retinal_size_px"]),
        "elevation_px": float(o["elevation_px"]),
        "size_m": float(o["size_m"]),
        "category=" + o["category"]: 1.0,
        "color=" + o["name"].split("_")[0]: 1.0,
    }


def _bin_value(x: float, cuts: list[float]) -> int:
    return int(np.searchsorted(np.asarray(cuts), x, side="right"))


def _matrix(rows: list[dict], names: list[str]) -> np.ndarray:
    return np.asarray([[float(r[n]) for n in names] for r in rows], dtype=float)


def _corr_report(rows: list[dict]) -> dict:
    names = [
        "depth_m",
        "x_cam",
        "elevation_px",
        "retinal_size_px",
        "mask_area_px",
        "size_m",
        "centroid_u",
        "centroid_v",
    ]
    X = _matrix(rows, names)
    C = np.corrcoef(X, rowvar=False)
    out = {}
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if j <= i:
                continue
            out[f"{a}__{b}"] = float(C[i, j]) if np.isfinite(C[i, j]) else None
    return out


def _design_object(
    rows: list[dict],
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    feats = []
    for r in rows:
        d = {
            k: r[k]
            for k in [
                "centroid_u",
                "centroid_v",
                "mask_area_px",
                "bbox_w",
                "bbox_h",
                "retinal_size_px",
                "elevation_px",
                "size_m",
            ]
        }
        d["category=" + r["category"]] = 1.0
        d["color=" + r["color"]] = 1.0
        feats.append(d)
    X = DictVectorizer(sparse=False).fit_transform(feats)
    targets = {
        "x_lateral": np.asarray([r["x_cam"] for r in rows], dtype=float),
        "z_depth": np.asarray([r["depth_m"] for r in rows], dtype=float),
        "role": np.asarray([r["role"] for r in rows], dtype=object),
    }
    groups = {
        "heldout_object_identity": np.asarray([r["category"] for r in rows], dtype=object),
        "heldout_camera_pose": np.asarray(
            [f"{r['camera_yaw_bin']}|{r['camera_pitch_bin']}" for r in rows], dtype=object
        ),
        "heldout_depth_range": np.asarray([r["near_depth_bin"] for r in rows], dtype=object),
    }
    return X, targets, groups


def _design_pair(
    rows: list[dict],
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    X = DictVectorizer(sparse=False).fit_transform([r["features"] for r in rows])
    targets = {
        "ordinal_depth": np.asarray([r["ordinal"] for r in rows], dtype=object),
        "ratio_depth": np.asarray([r["ratio"] for r in rows], dtype=float),
    }
    groups = {
        "heldout_object_pair": np.asarray([r["category_pair"] for r in rows], dtype=object),
        "heldout_depth_gap": np.asarray([r["depth_gap_bin"] for r in rows], dtype=object),
        "heldout_cue_combo": np.asarray([r["cue_combo"] for r in rows], dtype=object),
    }
    return X, targets, groups


def _splitter(groups: np.ndarray, n: int):
    unique = np.unique(groups)
    if len(unique) >= 3:
        return GroupKFold(n_splits=min(5, len(unique))).split(np.zeros(n), groups=groups)
    return KFold(n_splits=min(5, n), shuffle=True, random_state=0).split(np.zeros(n))


def _reg_score(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    pred = np.zeros_like(y, dtype=float)
    for tr, te in _splitter(groups, len(y)):
        sc = StandardScaler().fit(X[tr])
        model = RidgeCV(alphas=ALPHAS).fit(sc.transform(X[tr]), y[tr])
        pred[te] = model.predict(sc.transform(X[te]))
    return float(r2_score(y, pred))


def _cls_score(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    pred = np.empty_like(y)
    for tr, te in _splitter(groups, len(y)):
        if len(np.unique(y[tr])) < 2:
            # Tiny smoke subsets can produce a degenerate train fold. Report the
            # majority-class baseline rather than crashing; real pilots should have
            # enough strata that this path is not used.
            values, counts = np.unique(y[tr], return_counts=True)
            pred[te] = values[int(np.argmax(counts))]
            continue
        sc = StandardScaler().fit(X[tr])
        model = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(X[tr]), y[tr])
        pred[te] = model.predict(sc.transform(X[te]))
    return float(accuracy_score(y, pred))


def analyze(set_dir: Path, args) -> dict:
    anns = list(read_jsonl(set_dir / "annotations.jsonl"))
    if not anns:
        raise ValueError(f"no annotations in {set_dir}")
    obj_rows = _object_rows(anns)
    pair_rows = _pair_rows(anns)
    Xo, obj_targets, obj_groups = _design_object(obj_rows)
    Xp, pair_targets, pair_groups = _design_pair(pair_rows)

    scores = {}
    for split_name, g in obj_groups.items():
        scores[f"x_lateral/{split_name}/r2"] = _reg_score(Xo, obj_targets["x_lateral"], g)
        scores[f"z_depth/{split_name}/r2"] = _reg_score(Xo, obj_targets["z_depth"], g)
        scores[f"role/{split_name}/acc"] = _cls_score(Xo, obj_targets["role"], g)
    for split_name, g in pair_groups.items():
        scores[f"ordinal_depth/{split_name}/acc"] = _cls_score(Xp, pair_targets["ordinal_depth"], g)
        scores[f"ratio_depth/{split_name}/r2"] = _reg_score(Xp, pair_targets["ratio_depth"], g)

    gate = {}
    for k, v in scores.items():
        if k.endswith("/acc"):
            gate[k] = "PASS" if v >= args.min_acc else "FAIL"
        else:
            gate[k] = "PASS" if v >= args.min_r2 else "FAIL"
    return {
        "set": str(set_dir),
        "n_images": len(anns),
        "n_target_objects": len(obj_rows),
        "regime_counts": dict(Counter(a.get("factors", {}).get("regime", "unknown") for a in anns)),
        "distractor_count_distribution": dict(
            Counter(a.get("factors", {}).get("distractor_count", 0) for a in anns)
        ),
        "target_category_role_counts": _role_counts(obj_rows),
        "decorrelation_pearson": _corr_report(obj_rows),
        "oracle_feature_scores": scores,
        "gate_thresholds": {"min_acc": args.min_acc, "min_r2": args.min_r2},
        "gate": gate,
    }


def _role_counts(rows: list[dict]) -> dict:
    c = defaultdict(Counter)
    for r in rows:
        c[r["role"]][r["category"]] += 1
    return {k: dict(v) for k, v in c.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze M4a rendered stimulus outputs.")
    ap.add_argument("--set", action="append", required=True, help="rendered set directory")
    ap.add_argument("--out", help="write JSON report")
    ap.add_argument(
        "--min-acc",
        type=float,
        default=0.70,
        help="provisional gate threshold for classification targets",
    )
    ap.add_argument(
        "--min-r2",
        type=float,
        default=0.20,
        help="provisional gate threshold for regression targets",
    )
    args = ap.parse_args()
    reports = [analyze(Path(s), args) for s in args.set]
    text = json.dumps(reports if len(reports) > 1 else reports[0], indent=2, sort_keys=True)
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
