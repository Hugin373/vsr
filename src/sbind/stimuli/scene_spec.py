"""Scene spec: the structured description of a single scene to render.

The factorial sampler (sampler.py) produces a list of ``SceneSpec`` from a stimulus-set
config; the renderer (render_bpy.py) turns each ``SceneSpec`` into an image + a §3
``StimulusAnnotation``. Specs are plain dataclasses with dict round-trips so a whole set
can be dumped to YAML/JSON for exact reproducibility (determinism rule).

All lengths are metres, colours are linear RGB in [0, 1], positions are world coords.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CATEGORIES = ("cube", "sphere", "cylinder")


@dataclass
class ObjectSpec:
    name: str
    category: str  # one of CATEGORIES
    color: list[float]  # linear RGB, 3 floats in [0, 1]
    size_m: float  # characteristic size (cube edge / sphere diameter / cylinder height)
    pos_world: list[float]  # (x, y, z) of the object centre in world coords

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ObjectSpec:
        return cls(
            name=d["name"],
            category=d["category"],
            color=list(d["color"]),
            size_m=d["size_m"],
            pos_world=list(d["pos_world"]),
        )


@dataclass
class CameraSpec:
    pos_world: list[float]
    target_world: list[float]
    f_mm: float
    sensor_width_mm: float
    res_x: int
    res_y: int

    @property
    def height_m(self) -> float:
        return float(self.pos_world[2])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CameraSpec:
        return cls(
            pos_world=list(d["pos_world"]),
            target_world=list(d["target_world"]),
            f_mm=d["f_mm"],
            sensor_width_mm=d["sensor_width_mm"],
            res_x=d["res_x"],
            res_y=d["res_y"],
        )


@dataclass
class SceneSpec:
    """Everything needed to render one deterministic scene."""

    id: str
    camera: CameraSpec
    objects: list[ObjectSpec]
    ground_color: list[float] = field(default_factory=lambda: [0.5, 0.5, 0.5])
    sun_energy: float = 4.0
    sun_direction: list[float] = field(default_factory=lambda: [5.0, -5.0, 8.0])
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "camera": self.camera.to_dict(),
            "objects": [o.to_dict() for o in self.objects],
            "ground_color": self.ground_color,
            "sun_energy": self.sun_energy,
            "sun_direction": self.sun_direction,
            "factors": self.factors,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SceneSpec:
        return cls(
            id=d["id"],
            camera=CameraSpec.from_dict(d["camera"]),
            objects=[ObjectSpec.from_dict(o) for o in d["objects"]],
            ground_color=list(d.get("ground_color", [0.5, 0.5, 0.5])),
            sun_energy=d.get("sun_energy", 4.0),
            sun_direction=list(d.get("sun_direction", [5.0, -5.0, 8.0])),
            factors=d.get("factors", {}),
        )
