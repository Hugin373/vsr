"""Re-derive the apparent-size cue constants from RENDERED sets, worst-case not mean.

    uv run --extra analysis scripts/derive_cue_constants.py \
        --set $DATA_ROOT/stimuli/m4a_v1_natural_congruent_pilot \
        --set $DATA_ROOT/stimuli/m4a_v1_conflict_pilot \
        --set $DATA_ROOT/stimuli/m4a_v1_counterbalanced_pilot_j2 \
        --json reports/m4a_cue_constants.json --emit-yaml

Why this exists (AGENTS.md rule 7 clause 1): the constants are consumed by M4a's CONFLICT
designs, which must invert a cue *on purpose by a known amount*, and by the `min_depth_ratio`
floors. A constant recorded as a MEAN cannot support either, and one was:

    height_constant: {cube: 409.3, cylinder: 410.3, sphere: 405.3}   # means
    height_ratio_threshold: 1.016                                    # derived from the means

Measured per near/far ROLE from the rendered images, the cube/cylinder height constant swings
~±13% with image position (under a tilted camera a cube's silhouette HEIGHT grows as it moves
low/near in frame — its top face comes into view), while a sphere's swings ~3%. The true
worst-case height requirement on v0 was 1.0905, not 1.016 — 5x larger in excess-over-1.

Extremes, split by role — never means. See `sbind.stimuli.cue_constants` for the size-schema
handling (three schemas, no fallback, plus a per-object size-consistency invariant).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import yaml

from sbind.stimuli import cue_constants as cue_constants_module
from sbind.stimuli.cue_constants import (
    DERIVATION_VERSION,
    collect_constants,
    merge_constants,
    multiplier_worst_case,
    required_ratios,
)
from sbind.stimuli.sampler import _resolve_sizes
from sbind.utils.config import git_hash
from sbind.utils.io import read_jsonl


def _derivation_source_sha() -> str:
    """Content hash of the code that decides the constants.

    `derived_at_git_hash` records `<commit>-dirty` for any run from a working tree, which is the
    normal case during development — and `-dirty` erases exactly the distinction that matters when
    asking later "was this derived before or after the role/schema fix?" (advisor arbitration item
    4). A content hash of the two files that own the derivation answers that question directly, and
    keeps answering it after the tree is clean again.
    """
    import hashlib

    digest = hashlib.sha256()
    for path in (
        Path(__file__).resolve(),
        Path(cue_constants_module.__file__).resolve(),
    ):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _load_set(set_dir: Path) -> tuple[list[dict], dict, dict]:
    """Return (annotation records, resolved config, run metadata) for a rendered set."""
    records = list(read_jsonl(set_dir / "annotations.jsonl"))
    if not records:
        raise SystemExit(f"no annotations in {set_dir}")
    config_path = set_dir / "config.yaml"
    if not config_path.exists():
        raise SystemExit(
            f"{set_dir} has no config.yaml, so its size schema cannot be resolved. "
            f"Pass --config explicitly."
        )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    meta_path = set_dir / "run_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return records, config, meta


def _summarise(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "min": float(array.min()),
        "max": float(array.max()),
        "mean": float(array.mean()),
        "spread_pct": float(100.0 * (array.max() / array.min() - 1.0)),
    }


def _extreme_growth(values: list[float], rng: np.random.Generator, draws: int = 200) -> dict:
    """How much is this cell's measured extreme still growing with n?

    A worst case is only as good as the pose coverage behind it. Subsample each cell to n/2 and
    n/4 and record how much of the full-sample range those subsets recover: if half the data
    already recovers ~100% of the range, the extremes have converged; if it recovers 90%, the
    true extreme is plausibly still beyond what was measured and the margin must absorb that.
    """
    array = np.asarray(values, dtype=float)
    full_range = float(array.max() - array.min())
    out: dict[str, float] = {"n": int(array.size), "range": full_range}
    if full_range <= 0 or array.size < 8:
        return out
    for frac, label in ((0.5, "half"), (0.25, "quarter")):
        k = max(2, int(round(array.size * frac)))
        recovered = [
            float(np.ptp(rng.choice(array, size=k, replace=False))) for _ in range(draws)
        ]
        out[f"range_recovered_{label}_median_pct"] = float(
            100.0 * np.median(recovered) / full_range
        )
    return out


def _regime_isolation(
    per_set_ratios: dict[str, dict],
    pooled_ratios: dict[str, dict],
    pooled_required: float,
) -> dict[str, dict]:
    """What pooling does to each regime's bound — the diagnostic a pooled run exists to produce.

    Two readings, both useful and neither operative:

    * **Inflation** — how far the pooled bound sits above each regime's own. This is the cost of
      pooling, and the number that justifies the per-regime rule.
    * **Regime isolation** — WHICH pairing drives the divergence, i.e. where one regime's pose or
      size envelope reaches conditions another never produces. A large, pairing-specific
      divergence says the regimes are not exchangeable for that pairing; a uniformly small one
      says the silhouette constants are close to regime-invariant and pooling would have been
      nearly harmless.
    """
    print("\n--- regime isolation (DIAGNOSTIC — pooling cost per regime, never a bound) ---")
    out: dict[str, dict] = {}
    for set_name, own in per_set_ratios.items():
        own_required = max(r["binding"] for r in own.values())
        inflation = 100.0 * (pooled_required / own_required - 1.0)
        divergences = {
            key: pooled_ratios[key]["binding"] - own[key]["binding"]
            for key in own
            if key in pooled_ratios
        }
        worst_key = max(divergences, key=lambda k: divergences[k])
        out[set_name] = {
            "own_required": own_required,
            "pooled_required": pooled_required,
            "inflation_pct": inflation,
            "worst_diverging_pairing": worst_key,
            "worst_divergence": divergences[worst_key],
            "median_divergence": float(np.median(list(divergences.values()))),
        }
        print(
            f"  {set_name:34s} own {own_required:.4f} -> pooled {pooled_required:.4f} "
            f"({inflation:+.2f}%)  worst pairing {worst_key} "
            f"(+{divergences[worst_key]:.4f})  median +{out[set_name]['median_divergence']:.4f}"
        )
    print()
    return out


def _print_cells(title: str, const: dict[tuple[str, str], list[float]]) -> None:
    print(f"--- {title} (min .. max per role; MEANS ARE NOT SAFE TO USE) ---")
    for category in sorted({c for c, _ in const}):
        for role in ("near", "far"):
            key = (category, role)
            if key not in const:
                print(f"  {category:9s} as {role:4s}: NO SAMPLES")
                continue
            s = _summarise(const[key])
            print(
                f"  {category:9s} as {role:4s}: n={s['n']:4d}  min={s['min']:10.1f}  "
                f"max={s['max']:10.1f}  mean={s['mean']:10.1f}  spread={s['spread_pct']:5.1f}%"
            )
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--set",
        dest="sets",
        required=True,
        action="append",
        help="rendered stimulus set dir (repeat to POOL sets into one worst-case envelope)",
    )
    ap.add_argument("--json", help="write the full derivation report here")
    ap.add_argument(
        "--emit-yaml", action="store_true", help="print the cue_constants block for the configs"
    )
    ap.add_argument(
        "--check-floor",
        type=float,
        default=None,
        help="assert a configured min_depth_ratio clears the derived worst case",
    )
    ap.add_argument("--seed", type=int, default=0, help="seed for the extreme-growth subsampling")
    ap.add_argument(
        "--write-config",
        dest="write_configs",
        action="append",
        default=[],
        help="stimulus config to write/replace the derived `cue_constants` block in (repeatable)",
    )
    ap.add_argument(
        "--inherited-note",
        default=None,
        help="provenance note recorded when the written config is NOT the swept regime",
    )
    args = ap.parse_args()

    # FORMAL RULE (advisor arbitration item 2, 2026-07-19): operative cue constants are derived
    # PER REGIME. A pooled run is a cross-regime stress diagnostic — it may never be written into
    # a config, because pooling inflates a regime's requirement with pose conditions that regime
    # never produces (measured: +5.5% for natural-congruent). Enforced here, not just documented.
    if args.write_configs and len(args.sets) > 1:
        ap.error(
            f"--write-config is per-regime only, but {len(args.sets)} sets were pooled. "
            f"A pooled envelope is a DIAGNOSTIC, never the operative bound. Run once per regime "
            f"with a single --set."
        )

    rng = np.random.default_rng(args.seed)
    parts: list[dict] = []
    sources: list[dict] = []
    per_set_ratios: dict[str, dict] = {}

    for raw in args.sets:
        set_dir = Path(raw)
        records, config, meta = _load_set(set_dir)
        ref_sizes = _resolve_sizes(config["objects"], list(config["objects"]["categories"]))
        part = collect_constants(records, config, ref_sizes)
        parts.append(part)
        sources.append(
            {
                "set": str(set_dir),
                "set_name": config["output"]["set_name"],
                "experiment": config.get("experiment"),
                "seed": config.get("seed"),
                "size_schema": part["size_schema"],
                "size_condition": (config.get("condition") or {}).get("size_condition"),
                "n_images": part["n_records"],
                "n_target_objects": part["n_objects"],
                "render_git_hash": meta.get("git_hash"),
                "render_git_dirty": meta.get("git_dirty"),
                "near_depth_bins": config["factors"].get("near_depth_bins"),
                "min_depth_ratio": (config.get("constraints") or {}).get("min_depth_ratio"),
                "multiplier_worst_case": multiplier_worst_case(config),
            }
        )
        per_set_ratios[config["output"]["set_name"]] = required_ratios(part)
        print(
            f"set: {set_dir}  images={part['n_records']}  target objects={part['n_objects']}  "
            f"size_schema={part['size_schema']}  "
            f"(render {meta.get('git_hash', '?')})"
        )

    pooled = merge_constants(parts)
    is_pooled = len(parts) > 1
    if is_pooled:
        print(
            "\n" + "!" * 96 + "\n"
            "POOLED RUN = CROSS-REGIME STRESS DIAGNOSTIC AND REGIME-ISOLATION CHECK ONLY.\n"
            "It is NEVER the operative bound. C_a is not perfectly size-invariant, so pooling\n"
            "imports pose conditions a regime never produces and inflates its requirement.\n"
            "The operative constants are ALWAYS derived per regime, from one --set.\n" + "!" * 96
        )
    print(
        f"\nPOOLED: {pooled['n_records']} images, {pooled['n_objects']} target objects, "
        f"schemas={pooled['size_schema']}\n"
    )

    _print_cells("height  C_h = px*depth / size_norm", pooled["height"])
    _print_cells("area    C_a = px*depth^2 / size_norm^2", pooled["area"])

    print("--- pose-coverage sufficiency: is the measured extreme still growing with n? ---")
    growth: dict[str, dict] = {}
    for name, const in (("height", pooled["height"]), ("area", pooled["area"])):
        for key in sorted(const):
            g = _extreme_growth(const[key], rng)
            growth[f"{name}:{key[0]}:{key[1]}"] = g
            half = g.get("range_recovered_half_median_pct")
            quarter = g.get("range_recovered_quarter_median_pct")
            if half is None:
                continue
            print(
                f"  {name:6s} {key[0]:9s} {key[1]:4s} n={g['n']:4d}  "
                f"half-sample recovers {half:5.1f}% of range, quarter {quarter:5.1f}%"
            )
    recovered = [
        g["range_recovered_half_median_pct"]
        for g in growth.values()
        if "range_recovered_half_median_pct" in g
    ]
    if recovered:
        print(
            f"  worst cell: half the samples recover {min(recovered):.1f}% of the measured "
            f"range -> the extremes have NOT converged; carry a margin.\n"
        )

    ratios = required_ratios(pooled)
    print("--- required min far/near depth ratio, per pairing (WORST case, not mean) ---")
    print(f"  {'near':9s} {'far':9s} {'height':>8s} {'area':>8s} {'binding':>8s}")
    for name in sorted(ratios, key=lambda k: -ratios[k]["binding"]):
        near_cat, far_cat = name[len("near_") :].split("_far_")
        r = ratios[name]
        print(
            f"  {near_cat:9s} {far_cat:9s} {r['height']:8.4f} {r['area']:8.4f} "
            f"{r['binding']:8.4f}"
        )

    worst_h = max(r["height"] for r in ratios.values())
    worst_a = max(r["area"] for r in ratios.values())
    required = max(worst_h, worst_a)
    print(f"\n  WORST-CASE height requirement : {worst_h:.4f}")
    print(f"  WORST-CASE area   requirement : {worst_a:.4f}")
    print(f"  => shape-only min_depth_ratio must exceed : {required:.4f}")

    isolation: dict[str, dict] = {}
    if is_pooled:
        isolation = _regime_isolation(per_set_ratios, ratios, required)

    for source in sources:
        mult = source["multiplier_worst_case"]
        if mult is not None:
            print(
                f"  [{source['set_name']}] per-object multipliers widen this by up to "
                f"x{mult:.3f} -> {required * mult:.4f} (size congruence is broken ON PURPOSE "
                f"in this regime; reported, not enforced)"
            )

    exit_code = 0
    if args.check_floor is not None:
        headroom = 100.0 * (args.check_floor / required - 1.0)
        print(f"  configured floor {args.check_floor:.4f}  headroom {headroom:+.2f}%")
        # Congruence is a REQUIREMENT only where the design claims it. counterbalanced and
        # conflict decorrelate or invert the size cue deliberately, so a floor below the
        # congruence requirement is the intended design there, not a violation — reporting it as
        # one would be a false alarm that trains everyone to ignore the check.
        congruent = all(s["size_schema"] == "shared" for s in sources)
        if not congruent:
            print(
                "  (regimes with per-object size multipliers break size congruence ON PURPOSE; "
                "the congruence floor check is not applicable and is not enforced)"
            )
        elif args.check_floor <= required:
            print("\n  *** THE FLOOR DOES NOT CLEAR THE WORST CASE — raise min_depth_ratio")
            exit_code = 1

    report = {
        "derivation_version": DERIVATION_VERSION,
        "derived_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "derived_at_git_hash": git_hash(),
        "derivation_source_sha": _derivation_source_sha(),
        "sources": sources,
        "pooled": {
            "n_images": pooled["n_records"],
            "n_target_objects": pooled["n_objects"],
            "height_constant": {
                f"{c}_{r}": _summarise(v) for (c, r), v in sorted(pooled["height"].items())
            },
            "area_constant": {
                f"{c}_{r}": _summarise(v) for (c, r), v in sorted(pooled["area"].items())
            },
            "required_ratio_by_pairing": ratios,
            "worst_case_height_ratio": worst_h,
            "worst_case_area_ratio": worst_a,
            "worst_case_binding_ratio": required,
        },
        "pooled_is_diagnostic_only": is_pooled,
        "regime_isolation": isolation,
        "per_set_required_ratio_by_pairing": per_set_ratios,
        "pose_coverage": growth,
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    if args.write_configs:
        block = _yaml_block(report)
        if args.inherited_note:
            block["provenance"]["inherited_note"] = args.inherited_note
        for path in args.write_configs:
            _write_config_block(Path(path), block)
            print(f"wrote cue_constants -> {path}")

    if args.emit_yaml:
        print("\n" + "=" * 78)
        print("# paste into each M4a config as a top-level `cue_constants:` block")
        print("=" * 78)
        print(yaml.safe_dump({"cue_constants": _yaml_block(report)}, sort_keys=False, width=96))

    return exit_code


_BLOCK_START = "# >>> cue_constants — generated by scripts/derive_cue_constants.py >>>"
_BLOCK_END = "# <<< cue_constants <<<"


def _write_config_block(path: Path, block: dict) -> None:
    """Insert/replace the config's `cue_constants` block between sentinel comments.

    Deliberately TEXT surgery, not a YAML round-trip: the frozen pilot configs carry hand-written
    comments recording why each constraint has the value it has (the 0.2 m bin drop, the j2
    translation), and `yaml.safe_dump` would silently delete every one of them. Losing the
    rationale is how a derived constant becomes an unexplained magic number again.
    """
    text = path.read_text(encoding="utf-8")
    rendered = yaml.safe_dump({"cue_constants": block}, sort_keys=False, default_flow_style=False)
    payload = f"{_BLOCK_START}\n{rendered.rstrip()}\n{_BLOCK_END}\n"

    if _BLOCK_START in text and _BLOCK_END in text:
        head, rest = text.split(_BLOCK_START, 1)
        _, tail = rest.split(_BLOCK_END, 1)
        text = head + payload + tail.lstrip("\n")
    else:
        text = text.rstrip("\n") + "\n\n" + payload
    path.write_text(text, encoding="utf-8")

    # The block must parse back as the same mapping, or the surgery corrupted the config.
    written = yaml.safe_load(path.read_text(encoding="utf-8"))["cue_constants"]
    if written != block:
        raise SystemExit(f"{path}: cue_constants block did not round-trip after writing")


def _yaml_block(report: dict) -> dict:
    """The committed form: [min, max] per cell, per-pairing ratios, and full provenance."""
    pooled = report["pooled"]
    return {
        "provenance": {
            "derivation_script": "scripts/derive_cue_constants.py",
            "derivation_version": report["derivation_version"],
            "derived_at_utc": report["derived_at_utc"],
            "derived_at_git_hash": report["derived_at_git_hash"],
            "derivation_source_sha": report["derivation_source_sha"],
            "sources": [
                {
                    "set_name": s["set_name"],
                    "seed": s["seed"],
                    "render_git_hash": s["render_git_hash"],
                    "size_schema": s["size_schema"],
                    "n_images": s["n_images"],
                    "near_depth_bins": s["near_depth_bins"],
                }
                for s in report["sources"]
            ],
            "n_images_pooled": pooled["n_images"],
            "n_target_objects_pooled": pooled["n_target_objects"],
        },
        "height_constant_near": {
            k[: -len("_near")]: [round(v["min"], 1), round(v["max"], 1)]
            for k, v in pooled["height_constant"].items()
            if k.endswith("_near")
        },
        "height_constant_far": {
            k[: -len("_far")]: [round(v["min"], 1), round(v["max"], 1)]
            for k, v in pooled["height_constant"].items()
            if k.endswith("_far")
        },
        "area_constant_near": {
            k[: -len("_near")]: [round(v["min"]), round(v["max"])]
            for k, v in pooled["area_constant"].items()
            if k.endswith("_near")
        },
        "area_constant_far": {
            k[: -len("_far")]: [round(v["min"]), round(v["max"])]
            for k, v in pooled["area_constant"].items()
            if k.endswith("_far")
        },
        "required_ratio_by_pairing": {
            k: round(v["binding"], 4)
            for k, v in sorted(
                pooled["required_ratio_by_pairing"].items(),
                key=lambda kv: -kv[1]["binding"],
            )
        },
        "height_ratio_threshold": round(pooled["worst_case_height_ratio"], 4),
        "area_ratio_threshold": round(pooled["worst_case_area_ratio"], 4),
        "binding_ratio_threshold": round(pooled["worst_case_binding_ratio"], 4),
    }


if __name__ == "__main__":
    sys.exit(main())
