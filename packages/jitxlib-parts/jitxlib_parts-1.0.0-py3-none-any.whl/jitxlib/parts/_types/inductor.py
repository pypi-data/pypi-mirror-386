"""Instantiate an inductor that serializes to the JSON schema."""

from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from .component import (
    InductorMetadata,
    MinMax,
    Part,
)


@dataclass_json
@dataclass(frozen=True)
class Inductor(Part):
    # Type of inductor ["Molded", "Multilayer", "Planar", "Thick Film", "Toroidal", "Wirewound", "adjustable", "fixed"]
    type: str
    # Guaranteed tolerance from manufacture (Henry/Henry)
    tolerance: MinMax | None
    # Nominal inductance (Henry)
    inductance: float
    # Composition of inductor [“ceramic”, “Ferrite”, ...]
    material_core: str | None = field(metadata=config(field_name="material-core"))
    # Magnetic field status [“semi-shielded”, “shielded”, “unshielded”]
    shielding: str | None
    # Maximum steady-state current rating from manufacture (Amperes)
    current_rating: float | None = field(metadata=config(field_name="current-rating"))
    # Percentage inductance drop (typ 20-30%) at peak currents (Amperes)
    saturation_current: float | None = field(
        metadata=config(field_name="saturation-current")
    )
    # Nominal resistance (Ohm)
    dc_resistance: float | None = field(metadata=config(field_name="dc-resistance"))
    # Loss factor inverse - ratio between inductors resistance and inductance (ratio@freq)
    quality_factor: float | None = field(metadata=config(field_name="quality-factor"))
    # Frequency at which inductor impedance becomes very high / open circuit (freq in Hz)
    self_resonant_frequency: float | None = field(
        metadata=config(field_name="self-resonant-frequency")
    )

    rated_power: float | None = field(metadata=config(field_name="rated-power"))

    max_current: float | None = field(metadata=config(field_name="max_current"))

    metadata: InductorMetadata
