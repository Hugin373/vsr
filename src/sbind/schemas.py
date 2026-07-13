"""Frozen core data schemas (IMPLEMENTATION_PLAN §3).

Three formats the whole project agrees on, frozen in M0:

1. Stimulus annotation  -> one JSON line per image in ``annotations.jsonl``.
2. Activation-cache site naming -> ``Site`` helper; the cache stores pooled features
   per (model, stimulus set, site) with a ``meta`` table. M0 fixes only the site
   vocabulary and the meta-row schema; the array storage format lands in M4.
3. Probe-result record -> one tidy parquet row per (model, site, layer, target, ...).

Plain stdlib dataclasses + explicit dict (de)serialization: no third-party schema
dependency, greppable, and round-trip-tested. Nested numeric arrays (camera K/R/t,
positions, bboxes) are stored as lists so the JSON form is exact and lossless.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------------
# 1. Stimulus annotation
# ---------------------------------------------------------------------------------


@dataclass
class Camera:
    """Pinhole camera. K is 3x3 intrinsics; R 3x3 rotation; t 3-vector translation."""

    K: list[list[float]]
    R: list[list[float]]
    t: list[float]
    height_m: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Camera:
        return cls(K=d["K"], R=d["R"], t=d["t"], height_m=d["height_m"])


@dataclass
class ObjectAnnotation:
    """One object instance with world/camera geometry and image-space measurements.

    Two depth notions, deliberately both stored (see PROJECT_MEMORY):
      - ``depth_m``: depth of the object CENTRE along the optical axis. This is the
        continuous regression target the probes use.
      - ``nearest_surface_m``: centre depth minus the object's half-extent along the
        viewing axis, i.e. the depth of its nearest surface. This is what a viewer (and
        the bbox bottom) actually tracks, so verbalized "which is closer?" QA uses it.
    They can disagree for near-equal depths when the objects differ in shape, which is
    why the sampler's ``unambiguous_ordinal`` constraint forces them to agree.
    """

    name: str
    category: str
    size_m: float
    pos_world: list[float]
    pos_cam: list[float]
    depth_m: float
    bbox_px: list[float]  # [x0, y0, x1, y1]
    retinal_size_px: float
    elevation_px: float
    mask: str | None = None  # relative path to the object mask PNG, if rendered
    nearest_surface_m: float = 0.0
    # count of mask pixels — a shape-robust apparent-size measure. retinal_size_px is the
    # mask's pixel HEIGHT, which depends on silhouette shape; area is the alternative.
    mask_area_px: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ObjectAnnotation:
        return cls(
            name=d["name"],
            category=d["category"],
            size_m=d["size_m"],
            pos_world=d["pos_world"],
            pos_cam=d["pos_cam"],
            depth_m=d["depth_m"],
            bbox_px=d["bbox_px"],
            retinal_size_px=d["retinal_size_px"],
            elevation_px=d["elevation_px"],
            mask=d.get("mask"),
            nearest_surface_m=d.get("nearest_surface_m", 0.0),
            mask_area_px=d.get("mask_area_px", 0),
        )


@dataclass
class PairRelation:
    """Pairwise relation between two objects (keyed by "(i,j)" in the annotation).

    ``ordinal_depth`` is centre-based (probe target); ``ordinal_depth_surface`` is
    nearest-surface-based (what a viewer answers, so verbalized QA uses it). With the
    sampler's ``unambiguous_ordinal`` constraint on, the two always agree.
    """

    ordinal_depth: str  # e.g. "0_closer"
    dist_ratio: float
    dist_m: float
    ordinal_depth_surface: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PairRelation:
        return cls(
            ordinal_depth=d["ordinal_depth"],
            dist_ratio=d["dist_ratio"],
            dist_m=d["dist_m"],
            ordinal_depth_surface=d.get("ordinal_depth_surface", ""),
        )


@dataclass
class StimulusAnnotation:
    """One rendered image + full geometry (one JSON line in annotations.jsonl)."""

    id: str
    image: str  # relative path, e.g. "images/set3_00142.png"
    camera: Camera
    objects: list[ObjectAnnotation]
    factors: dict[str, Any] = field(default_factory=dict)
    pair_relations: dict[str, PairRelation] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "image": self.image,
            "camera": self.camera.to_dict(),
            "objects": [o.to_dict() for o in self.objects],
            "factors": self.factors,
            "pair_relations": {k: v.to_dict() for k, v in self.pair_relations.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StimulusAnnotation:
        return cls(
            id=d["id"],
            image=d["image"],
            camera=Camera.from_dict(d["camera"]),
            objects=[ObjectAnnotation.from_dict(o) for o in d["objects"]],
            factors=d.get("factors", {}),
            pair_relations={
                k: PairRelation.from_dict(v) for k, v in d.get("pair_relations", {}).items()
            },
        )


# ---------------------------------------------------------------------------------
# 2. Activation-cache site naming + meta rows
# ---------------------------------------------------------------------------------

# The four probing sites (IMPLEMENTATION_PLAN §3). Visual-token sites are layer-indexed
# in the language model; encoder/projector outputs are single sites.
SITE_ENC_OUT = "enc_out"
SITE_PROJ_OUT = "proj_out"
SITE_LM_VIS = "lm_vis"  # + "_L{k}" per LM layer
SITE_LM_TXT = "lm_txt"  # + "_L{k}" per LM layer

BASE_SITES = (SITE_ENC_OUT, SITE_PROJ_OUT, SITE_LM_VIS, SITE_LM_TXT)

# Pooling variants stored per visual-token site (Dual Mechanisms v2 standard): both
# mask-pooled per-object AND all-token / strip-level, since spatial signal is
# distributed across background tokens.
POOL_OBJECT = "object"  # [n_images, n_objects, hidden_dim]
POOL_STRIP = "strip"  # [n_images, n_strips, hidden_dim]


def lm_site(base: str, layer: int) -> str:
    """Format a layer-indexed LM site, e.g. lm_site(SITE_LM_VIS, 14) -> 'lm_vis_L14'."""
    if base not in (SITE_LM_VIS, SITE_LM_TXT):
        raise ValueError(f"layer index only applies to {SITE_LM_VIS}/{SITE_LM_TXT}, got {base!r}")
    return f"{base}_L{layer}"


@dataclass
class CacheMetaRow:
    """One row of the cache ``meta`` table: locates a pooled feature vector and carries
    every geometry target + factor needed by the probe runner (§3, M4/M5)."""

    image_id: str
    object_id: int  # index into the image's objects; -1 for strip/all-token rows
    row_index: int  # position along the object/strip axis in the feature array
    pool: str  # POOL_OBJECT | POOL_STRIP
    targets: dict[str, float] = field(default_factory=dict)  # depth_m, x, z, dist_ratio, ...
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CacheMetaRow:
        return cls(
            image_id=d["image_id"],
            object_id=d["object_id"],
            row_index=d["row_index"],
            pool=d["pool"],
            targets=d.get("targets", {}),
            factors=d.get("factors", {}),
        )


# ---------------------------------------------------------------------------------
# 3. Probe-result record
# ---------------------------------------------------------------------------------


@dataclass
class ProbeResult:
    """One probe evaluation (§3). Collected into a single tidy parquet for Phase-2 plots."""

    model: str
    site: str
    layer: int
    target: str  # ordinal | ratio | absolute | qualitative | x | z
    axis: str  # depth | lateral
    stimulus_set: str
    seed: int
    split: int
    metric: str  # spearman | r2 | acc
    value: float
    n: int
    control_value: float  # shuffled-label control score

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProbeResult:
        return cls(
            model=d["model"],
            site=d["site"],
            layer=d["layer"],
            target=d["target"],
            axis=d["axis"],
            stimulus_set=d["stimulus_set"],
            seed=d["seed"],
            split=d["split"],
            metric=d["metric"],
            value=d["value"],
            n=d["n"],
            control_value=d["control_value"],
        )
