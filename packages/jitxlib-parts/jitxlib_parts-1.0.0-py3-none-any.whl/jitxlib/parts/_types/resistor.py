"""Instantiate a resistor that serializes to the JSON schema."""

from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json
from .component import (
    MinMax,
    Part,
    ResistorMetadata,
    ResistorTCR,
)


# Exclude a field from JSON serialization if it is None.
def exclude_from_json(value):
    return value is None


@dataclass_json
@dataclass(frozen=True)
class Resistor(Part):
    type: str
    # Guaranteed tolerance from manufacture (Ohm/Ohm)
    tolerance: MinMax | None
    # Nominal resistance (Ohm)
    resistance: float
    composition: str | None
    series: str | None
    metadata: ResistorMetadata
    # Temperature coefficient of resistance (ohms/ohm*degC)
    tcr: ResistorTCR | None = field(
        default=None,
        metadata=config(exclude=exclude_from_json),
    )
