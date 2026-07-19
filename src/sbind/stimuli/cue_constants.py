"""Apparent-size cue constants: schema-aware extraction from rendered annotations.

The cue constants are what M4a's CONFLICT designs need in order to invert a cue *on purpose
by a known amount*, and what the `min_depth_ratio` floors are supposed to be derived from.
They are CONSTRUCTED, deterministic quantities, so AGENTS.md rule 7 clause 1 applies: every
threshold comes from the measured WORST CASE, never a mean.

Two constants per (category, near/far role), both with the object's physical size divided out
so that what remains is a property of the SHAPE under the set's pose envelope:

    C_h = retinal_size_px * depth_m      / size_norm       ("height constant")
    C_a = mask_area_px    * depth_m ** 2 / size_norm ** 2  ("area constant")

`size_norm` is the object's physical-size multiplier relative to its calibrated category size.
Recovering it is the whole reason this module exists: THREE size schemas are in use across the
M4a battery, and dividing the wrong one out silently produces a wrong constant that every
downstream check would accept.

    shared      `factors["size_multiplier"]`                       v0, natural_congruent
    per_object  `factors["size_multiplier_near"]` / `..._far`      counterbalanced, conflict
    explicit    each object's own `size_m` (no multiplier at all)  future per-object sizing

⚠ There is NO fallback between schemas. A missing required field raises. The previous version
of this code read `factors["size_multiplier"]` unconditionally; the tempting one-line "fix" is
`factors.get("size_multiplier", <shared value>)`, which on a counterbalanced set would divide a
near object's constant by the far object's multiplier and be off by up to the full
multiplier range (0.75..1.20 -> 60%) with no symptom. Hence, additionally, a hard INVARIANT
CHECK on every object (rule 1, "measured == analytic"):

    size_norm * size_m_by_category[category] == object.size_m

which is false the moment the wrong multiplier is used, whatever the reason.
"""

from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np

# Bumped whenever the derivation changes in a way that would move a committed constant.
# Recorded in every emitted `cue_constants.provenance` block.
DERIVATION_VERSION = "2.0.0"

SIZE_SCHEMAS = ("shared", "per_object", "explicit")

# `condition.size_condition` -> size schema. Deliberately exhaustive and without a default:
# an unrecognised size_condition must stop the derivation, not silently pick a schema.
SIZE_CONDITION_TO_SCHEMA = {
    "congruent": "shared",
    "independent_jitter": "per_object",
    "counterbalanced": "per_object",
    "far_larger": "per_object",
    "conflict_far_larger": "per_object",
    "explicit_size": "explicit",
}

# size_norm * calibrated size must reproduce the rendered object's size_m to this relative
# tolerance. Both sides are float64 products of the same two numbers, so the only slack needed
# is round-trip through JSON.
_SIZE_CONSISTENCY_RTOL = 1e-9


class CueConstantSchemaError(ValueError):
    """A required size-schema field is missing, unknown, or internally inconsistent."""


def resolve_size_schema(config: dict[str, Any]) -> str:
    """Which size schema this stimulus config uses. Raises rather than guessing."""
    cond = config.get("condition") or {}
    explicit = cond.get("size_schema")
    if explicit is not None:
        if explicit not in SIZE_SCHEMAS:
            raise CueConstantSchemaError(
                f"condition.size_schema={explicit!r} is not one of {SIZE_SCHEMAS}"
            )
        return str(explicit)
    size_condition = cond.get("size_condition")
    if size_condition is None:
        raise CueConstantSchemaError(
            "config has neither condition.size_schema nor condition.size_condition, so the "
            "size schema cannot be determined. Refusing to assume a shared multiplier."
        )
    if size_condition not in SIZE_CONDITION_TO_SCHEMA:
        raise CueConstantSchemaError(
            f"unknown condition.size_condition={size_condition!r}; add it to "
            f"SIZE_CONDITION_TO_SCHEMA with its size schema. Known: "
            f"{sorted(SIZE_CONDITION_TO_SCHEMA)}"
        )
    return SIZE_CONDITION_TO_SCHEMA[size_condition]


def target_roles(record: dict[str, Any]) -> dict[int, str]:
    """Map object index -> "near"/"far" for the TARGET pair only.

    Read from the recorded factors, never inferred by argmin over depths: distractors sit at
    world-y 2.7..4.4 and can be nearer than the far target, so an argmin over all objects both
    mislabels roles and pulls distractors (which carry an unrelated size multiplier of their
    own) into the constants.
    """
    factors = record.get("factors") or {}
    indices = factors.get("target_object_indices")
    if indices is None:
        # v0 sets predate the field and contain exactly the target pair, nothing else.
        if len(record["objects"]) != 2:
            raise CueConstantSchemaError(
                f"record {record.get('id')!r}: factors.target_object_indices is missing and the "
                f"record has {len(record['objects'])} objects, so the target pair is ambiguous"
            )
        indices = [0, 1]
    if "closer_object" not in factors:
        raise CueConstantSchemaError(
            f"record {record.get('id')!r}: factors.closer_object is required to assign "
            f"near/far roles"
        )
    closer = int(factors["closer_object"])
    if closer not in indices:
        raise CueConstantSchemaError(
            f"record {record.get('id')!r}: closer_object={closer} is not among "
            f"target_object_indices={indices}"
        )
    return {int(i): ("near" if int(i) == closer else "far") for i in indices}


def size_norm(
    schema: str,
    record: dict[str, Any],
    obj: dict[str, Any],
    role: str,
    ref_sizes: dict[str, float],
) -> float:
    """The object's physical size as a multiple of its calibrated category size.

    Raises `CueConstantSchemaError` on any missing field. There is no cross-schema fallback,
    by design: see the module docstring.
    """
    factors = record.get("factors") or {}
    rid = record.get("id")
    if schema == "shared":
        key = "size_multiplier"
        if key not in factors:
            raise CueConstantSchemaError(
                f"record {rid!r}: size schema 'shared' requires factors[{key!r}], which is "
                f"absent. Present size fields: {sorted(k for k in factors if 'size' in k)}. "
                f"Refusing to substitute a per-object multiplier."
            )
        norm = float(factors[key])
    elif schema == "per_object":
        key = f"size_multiplier_{role}"
        if key not in factors:
            raise CueConstantSchemaError(
                f"record {rid!r}: size schema 'per_object' requires factors[{key!r}], which is "
                f"absent. Present size fields: {sorted(k for k in factors if 'size' in k)}. "
                f"Refusing to fall back to a shared multiplier."
            )
        norm = float(factors[key])
    elif schema == "explicit":
        if "size_m" not in obj:
            raise CueConstantSchemaError(
                f"record {rid!r}: size schema 'explicit' requires each object to carry 'size_m'"
            )
        ref = _ref_size(ref_sizes, obj, rid)
        norm = float(obj["size_m"]) / ref
    else:
        raise CueConstantSchemaError(f"unknown size schema {schema!r}; expected {SIZE_SCHEMAS}")

    _check_size_consistency(schema, norm, obj, ref_sizes, rid, role)
    return norm


def _ref_size(ref_sizes: dict[str, float], obj: dict[str, Any], rid: Any) -> float:
    category = obj["category"]
    if category not in ref_sizes:
        raise CueConstantSchemaError(
            f"record {rid!r}: no calibrated size_m for category {category!r}; known: "
            f"{sorted(ref_sizes)}"
        )
    return float(ref_sizes[category])


def _check_size_consistency(
    schema: str,
    norm: float,
    obj: dict[str, Any],
    ref_sizes: dict[str, float],
    rid: Any,
    role: str,
) -> None:
    """`size_norm * calibrated size == rendered size_m`, or the wrong multiplier was used.

    This is the check that makes a silent cross-schema fallback impossible rather than merely
    forbidden: reading a far object's multiplier for a near object, or a shared multiplier on a
    per-object set, breaks this identity immediately. Vacuous for the 'explicit' schema, where
    `norm` is defined as the ratio being checked.
    """
    if schema == "explicit" or "size_m" not in obj:
        return
    expected = norm * _ref_size(ref_sizes, obj, rid)
    actual = float(obj["size_m"])
    if abs(expected - actual) > _SIZE_CONSISTENCY_RTOL * max(1.0, abs(actual)):
        raise CueConstantSchemaError(
            f"record {rid!r} object {obj.get('name')!r} ({role}): size schema {schema!r} gives "
            f"size_norm={norm!r}, which implies size_m={expected!r}, but the object was rendered "
            f"at size_m={actual!r}. The wrong size multiplier is being divided out — the derived "
            f"constant would be wrong by a factor of {actual / expected:.4f}."
        )


def collect_constants(
    records: list[dict[str, Any]],
    config: dict[str, Any],
    ref_sizes: dict[str, float],
) -> dict[str, Any]:
    """Per-(category, role) C_h and C_a samples over the TARGET pairs of a rendered set."""
    schema = resolve_size_schema(config)
    height: dict[tuple[str, str], list[float]] = {}
    area: dict[tuple[str, str], list[float]] = {}
    n_objects = 0
    for record in records:
        roles = target_roles(record)
        for index, role in roles.items():
            obj = record["objects"][index]
            norm = size_norm(schema, record, obj, role, ref_sizes)
            if norm <= 0:
                raise CueConstantSchemaError(
                    f"record {record.get('id')!r}: non-positive size_norm {norm!r}"
                )
            depth = float(obj["depth_m"])
            key = (obj["category"], role)
            height.setdefault(key, []).append(float(obj["retinal_size_px"]) * depth / norm)
            area.setdefault(key, []).append(float(obj["mask_area_px"]) * depth**2 / norm**2)
            n_objects += 1
    return {
        "size_schema": schema,
        "height": height,
        "area": area,
        "n_records": len(records),
        "n_objects": n_objects,
    }


def merge_constants(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool per-set samples into one envelope. Worst case over a UNION of pose envelopes."""
    height: dict[tuple[str, str], list[float]] = {}
    area: dict[tuple[str, str], list[float]] = {}
    for part in parts:
        for key, values in part["height"].items():
            height.setdefault(key, []).extend(values)
        for key, values in part["area"].items():
            area.setdefault(key, []).extend(values)
    return {
        "size_schema": sorted({p["size_schema"] for p in parts}),
        "height": height,
        "area": area,
        "n_records": sum(p["n_records"] for p in parts),
        "n_objects": sum(p["n_objects"] for p in parts),
    }


def required_ratios(constants: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Worst-case far/near depth ratio at which each cue stops favouring the near object.

    Height congruence needs `retinal_near > retinal_far`, i.e.

        depth_far / depth_near  >  C_h[far_cat as FAR].max / C_h[near_cat as NEAR].min

    and area congruence the same with a square root, since C_a carries depth squared. Both use
    max-as-far over min-as-near: the extremes, exactly as measured, never the means.

    ⚠ This is the requirement for EQUAL physical-size multipliers. Regimes that vary size per
    object (counterbalanced, conflict) break size congruence deliberately, so for them the
    number below is descriptive — the ratio at which the shape alone stops inverting the cue —
    and `multiplier_worst_case` in the report carries the multiplier term separately.
    """
    height, area = constants["height"], constants["area"]
    categories = sorted({c for c, _ in height})
    out: dict[str, dict[str, float]] = {}
    for near_cat, far_cat in product(categories, categories):
        near_key, far_key = (near_cat, "near"), (far_cat, "far")
        if near_key not in height or far_key not in height:
            continue
        req_h = max(height[far_key]) / min(height[near_key])
        req_a = float(np.sqrt(max(area[far_key]) / min(area[near_key])))
        out[f"near_{near_cat}_far_{far_cat}"] = {
            "height": float(req_h),
            "area": float(req_a),
            "binding": float(max(req_h, req_a)),
        }
    return out


def multiplier_worst_case(config: dict[str, Any]) -> float | None:
    """Worst-case far/near physical-size multiplier ratio the config can draw.

    For per-object schemas the size cue is additionally scaled by `m_far / m_near`, so the
    depth ratio required for a congruent apparent size is the shape requirement times this.
    Returns None for the shared schema, where the multiplier cancels exactly.
    """
    if resolve_size_schema(config) != "per_object":
        return None
    fcfg = config["factors"]
    near_range = fcfg.get("near_size_multiplier_range")
    far_range = fcfg.get("far_size_multiplier_range")
    if near_range is None or far_range is None:
        shared = fcfg.get("size_multiplier_range") or fcfg.get("size_multipliers")
        if shared is None:
            raise CueConstantSchemaError(
                "per_object size schema needs factors.size_multiplier_range (or the "
                "near_/far_ pair) to bound the multiplier ratio"
            )
        near_range = far_range = shared
    return float(max(far_range)) / float(min(near_range))
