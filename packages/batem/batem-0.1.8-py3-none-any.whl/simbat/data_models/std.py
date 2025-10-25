from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://simbat.fr/std"


@dataclass
class Direction:
    exposure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    horizontal_tilt: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    vertical_tilt: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )


@dataclass
class Glazing:
    glazing_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    percentage: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
            "max_inclusive": 100.0,
        },
    )
    composition_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )


@dataclass
class Layer:
    material: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    thickness: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )


@dataclass
class Mask:
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )
    width: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )
    distance_to_ground_gravity_m: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )
    exposure: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    slope: Optional[float] = field(
        default=90.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    rotation: Optional[float] = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    elevation: Optional[float] = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )


@dataclass
class Perimeter:
    offset_x: float = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    offset_y: float = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    xy_gps_id: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 3,
        },
    )


@dataclass
class Side:
    xy_id: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 2,
            "max_occurs": 2,
        },
    )
    composition_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    glazing: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
        },
    )


@dataclass
class XyGps:
    class Meta:
        name = "XY_GPS"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    x: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    y: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )


@dataclass
class Composition:
    composition_id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    layer: list[Layer] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 1,
        },
    )


@dataclass
class Coordinates:
    offset_x: float = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    offset_y: float = field(
        default=0.0,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    xy_gps: list[XyGps] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 3,
        },
    )


@dataclass
class Masks:
    mask: list[Mask] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 1,
        },
    )


@dataclass
class Sides:
    side: list[Side] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 3,
        },
    )


@dataclass
class Surrounding:
    mask: list[Mask] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 1,
        },
    )


@dataclass
class Compositions:
    composition: list[Composition] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "min_occurs": 1,
        },
    )


@dataclass
class Site1:
    class Meta:
        name = "Site"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    latitude: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    longitude: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    height: Optional[float] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 0.0,
        },
    )
    perimeter: Optional[Perimeter] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    n_floors: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
            "min_inclusive": 1,
        },
    )
    roof_composition: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    ground_composition: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    floor_composition: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
        },
    )
    sides: Optional[Sides] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    surrounding: Optional[Surrounding] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
        },
    )
    coordinates: Optional[Coordinates] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    compositions: Optional[Compositions] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
            "required": True,
        },
    )
    masks: Optional[Masks] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://simbat.fr/std",
        },
    )


@dataclass
class Site(Site1):
    class Meta:
        name = "site"
        namespace = "http://simbat.fr/std"
