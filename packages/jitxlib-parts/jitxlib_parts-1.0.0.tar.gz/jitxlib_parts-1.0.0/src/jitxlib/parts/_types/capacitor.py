"""Instantiate a capacitor that serializes to the JSON schema."""

from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from .component import (
    CapacitorMetadata,
    CapacitorTemperatureCoefficent,
    ComponentCode,
    MinMax,
    Part,
)


@dataclass_json
@dataclass(frozen=True)
class Capacitor(Part):
    type: str
    tolerance: MinMax | None
    # Nominal capacitance (Farad)
    capacitance: float
    # Anode material of electrolytic capacitor [“aluminum”, “tantalum”, “niobium-oxide”]
    anode: str | None
    # Electrolyte material of electrolytic capacitor [“polymer”, “manganese-dioxide”, “hybrid”, “non-solid”]
    electrolyte: str | None
    # Temperature coefficient code of capacitance [“X7R”, ...]
    temperature_coefficient: CapacitorTemperatureCoefficent | None = field(
        metadata=config(field_name="temperature-coefficient")
    )
    esr: float | None
    esr_frequency: float | None
    rated_voltage: float | None = field(metadata=config(field_name="rated-voltage"))
    rated_voltage_ac: float | None = field(
        metadata=config(field_name="rated-voltage-ac")
    )
    # Maximum peak current rating from manufacturer (Amperes)
    rated_current_pk: float | None = field(
        metadata=config(field_name="rated-current-pk")
    )
    # Maximum rms current rating from manufacturer (Amperes)
    rated_current_rms: float | None = field(
        metadata=config(field_name="rated-current-rms")
    )
    # Note: This was optional in stanza version but it was probaly an error as it was made mandatory for the other part types.
    component: ComponentCode
    metadata: CapacitorMetadata
