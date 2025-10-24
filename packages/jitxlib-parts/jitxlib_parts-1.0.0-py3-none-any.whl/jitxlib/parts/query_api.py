"""
Query API for the JITX parts database.

This module provides a Python implementation of the query builder API
for the JITX parts database, translating the Stanza query-api.stanza to Python.
"""

from __future__ import annotations
from dataclasses import dataclass, fields
import logging
from enum import Enum
from collections.abc import Sequence
from typing import (
    Self,
    TypedDict,
    Unpack,
    cast,
)

import jitx
import jitx.container
import jitx.inspect
from jitx.interval import Interval
import jitx.context
import jitx.units
import jitx._structural
from jitx import current


from .commands import PartJSON, dbquery, QueryParamValue
from .convert import convert_component, get_jitxstd_symbol
from ._types.component import Part as PartType
from ._types.resistor import Resistor as ResistorType
from ._types.capacitor import Capacitor as CapacitorType
from ._types.inductor import Inductor as InductorType
from ._types.main import to_component
from ._convert_utils import StdLibSymbolType


# Configure logging
logging = logging.getLogger("jitx_parts_database.query_api")


# Special marker class to denote using distinct on a field
class FindDistinctType:
    """Marker class for FIND_DISTINCT functionality.

    Use the FIND_DISTINCT constant instead of creating instances directly.
    """

    def __repr__(self) -> str:
        return "FIND_DISTINCT"

    def __str__(self) -> str:
        return "FIND_DISTINCT"


# Special marker instance to denote using distinct on a field
FIND_DISTINCT = FindDistinctType()


class AuthorizedVendor(Enum):
    """Authorized vendors for electronic components."""

    JLCPCB = "JLCPCB"
    LCSC = "LCSC"
    DigiKey = "DigiKey"
    Future = "Future"
    Mouser = "Mouser"
    Arrow = "Arrow"
    Avnet = "Avnet"
    Newark = "Newark"


class SortDir(Enum):
    """Sort direction options."""

    INCREASING = "increasing"
    DECREASING = "decreasing"


@dataclass(frozen=True)
class SortKey:
    """Sort key for database queries."""

    key: str
    direction: SortDir


@dataclass(frozen=True)
class DistinctKey:
    """Distinct key for database queries."""

    key: str


@dataclass(frozen=True)
class ExistKeys:
    """Existence keys for database queries."""

    keys: Sequence[str]


class FindOptimum(Enum):
    """Find optimum options."""

    FIND_MAXIMUM = "find_maximum"
    FIND_MINIMUM = "find_minimum"


class PartQueryDict(TypedDict, total=False):
    trust: str | Sequence[str] | FindDistinctType | None
    category: str | Sequence[str] | FindDistinctType | None
    mpn: str | Sequence[str] | FindDistinctType | None
    mounting: str | Sequence[str] | FindDistinctType | None
    manufacturer: str | Sequence[str] | FindDistinctType | None
    description: str | Sequence[str] | FindDistinctType | None
    case: str | Sequence[str] | FindDistinctType | None
    min_stock: int | FindDistinctType | None
    quantity_needed: int | FindDistinctType | None
    price: float | Interval | FindOptimum | Sequence[float] | FindDistinctType | None
    x: float | Interval | Sequence[float] | FindDistinctType | None
    y: float | Interval | Sequence[float] | FindDistinctType | None
    z: float | Interval | Sequence[float] | FindDistinctType | None
    area: float | Interval | FindOptimum | Sequence[float] | FindDistinctType | None
    rated_temperature_min: float | Interval | Sequence[float] | FindDistinctType | None
    rated_temperature_max: float | Interval | Sequence[float] | FindDistinctType | None
    operating_temperature: Interval | FindDistinctType | None
    stock: int | FindDistinctType | None
    sellers: Sequence[str | AuthorizedVendor] | FindDistinctType | None
    sort: SortKey | Sequence[SortKey] | FindDistinctType | None
    exist: ExistKeys | FindDistinctType | None
    distinct: DistinctKey | FindDistinctType | None
    ignore_stock: bool | FindDistinctType | None


class PassiveQueryDict(PartQueryDict, total=False):
    type: str | Sequence[str] | FindDistinctType | None
    tolerance: float | jitx.units.PlainQuantity | FindDistinctType | None
    precision: float | jitx.units.PlainQuantity | FindDistinctType | None
    tolerance_min: float | Interval | FindDistinctType | None
    tolerance_max: float | Interval | FindDistinctType | None
    component_datasheet: str | Sequence[str] | FindDistinctType | None
    metadata_image: str | Sequence[str] | FindDistinctType | None
    metadata_digi_key_part_number: str | Sequence[str] | FindDistinctType | None
    metadata_description: str | Sequence[str] | FindDistinctType | None
    metadata_packaging: str | Sequence[str] | FindDistinctType | None


class ResistorQueryDict(PassiveQueryDict, total=False):
    resistance: (
        float
        | jitx.units.PlainQuantity
        | Interval
        | Sequence[float]
        | FindDistinctType
        | None
    )
    rated_power: float | Interval | Sequence[float] | FindDistinctType | None
    composition: str | FindDistinctType | None
    tcr_pos: float | Interval | FindDistinctType | None
    tcr_neg: float | Interval | FindDistinctType | None
    metadata_series: str | FindDistinctType | None
    metadata_features: str | FindDistinctType | None
    metadata_supplier_device_package: str | FindDistinctType | None
    metadata_number_of_terminations: int | FindDistinctType | None


class CapacitorQueryDict(PassiveQueryDict, total=False):
    capacitance: float | jitx.units.PlainQuantity | Interval | FindDistinctType | None
    anode: str | FindDistinctType | None
    electrolyte: str | FindDistinctType | None
    esr: float | Interval | FindDistinctType | None
    esr_frequency: float | Interval | FindDistinctType | None
    rated_voltage: float | Interval | FindDistinctType | None
    rated_voltage_ac: float | Interval | FindDistinctType | None
    rated_current_pk: float | Interval | FindDistinctType | None
    rated_current_rms: float | Interval | FindDistinctType | None
    temperature_coefficient_code: str | FindDistinctType | None
    temperature_coefficient_raw_data: str | FindDistinctType | None
    temperature_coefficient_tolerance: float | FindDistinctType | None
    temperature_coefficient_lower_temperature: float | FindDistinctType | None
    temperature_coefficient_upper_temperature: float | FindDistinctType | None
    temperature_coefficient_change: float | FindDistinctType | None
    metadata_lifetime_temp: float | Interval | FindDistinctType | None
    metadata_applications: str | FindDistinctType | None
    metadata_ripple_current_low_frequency: float | Interval | FindDistinctType | None
    metadata_ripple_current_high_frequency: float | Interval | FindDistinctType | None
    metadata_lead_spacing: float | Interval | FindDistinctType | None


class InductorQueryDict(PassiveQueryDict, total=False):
    inductance: float | jitx.units.PlainQuantity | Interval | FindDistinctType | None
    material_core: str | FindDistinctType | None
    shielding: str | FindDistinctType | None
    current_rating: float | Interval | FindDistinctType | None
    saturation_current: float | Interval | FindDistinctType | None
    dc_resistance: float | Interval | FindDistinctType | None
    quality_factor: float | Interval | FindDistinctType | None
    quality_factor_frequency: float | Interval | FindDistinctType | None
    self_resonant_frequency: float | Interval | FindDistinctType | None


@dataclass(frozen=True, kw_only=True)
class PartQuery(jitx.context.Context):
    """Context for part queries."""

    trust: str | Sequence[str] | FindDistinctType | None = None
    category: str | Sequence[str] | FindDistinctType | None = None
    mpn: str | Sequence[str] | FindDistinctType | None = None
    mounting: str | Sequence[str] | FindDistinctType | None = None
    manufacturer: str | Sequence[str] | FindDistinctType | None = None
    description: str | Sequence[str] | FindDistinctType | None = None
    case: str | Sequence[str] | FindDistinctType | None = None
    min_stock: int | FindDistinctType | None = None
    quantity_needed: int | FindDistinctType | None = None
    price: (
        float | Interval | FindOptimum | Sequence[float] | FindDistinctType | None
    ) = None
    x: float | Interval | Sequence[float] | FindDistinctType | None = None
    y: float | Interval | Sequence[float] | FindDistinctType | None = None
    z: float | Interval | Sequence[float] | FindDistinctType | None = None
    area: float | Interval | FindOptimum | Sequence[float] | FindDistinctType | None = (
        None
    )
    rated_temperature_min: (
        float | Interval | Sequence[float] | FindDistinctType | None
    ) = None
    rated_temperature_max: (
        float | Interval | Sequence[float] | FindDistinctType | None
    ) = None
    # more-intuitive shortcut for specifying the above two
    operating_temperature: Interval | FindDistinctType | None = None
    stock: int | FindDistinctType | None = None
    sellers: Sequence[str | AuthorizedVendor] | FindDistinctType | None = None
    sort: SortKey | Sequence[SortKey] | FindDistinctType | None = None
    exist: ExistKeys | FindDistinctType | None = None
    distinct: DistinctKey | FindDistinctType | None = None
    ignore_stock: bool | FindDistinctType | None = None

    @classmethod
    def from_query(cls, query: PartQuery) -> PartQuery:
        """Create a PartQuery from a PartQuery."""
        # Filter params to only include fields defined in this class
        valid_fields = {field.name for field in fields(cls)}
        all_params = query.params()
        filtered_params = {k: v for k, v in all_params.items() if k in valid_fields}

        # Log warning for dropped parameters
        dropped_params = set(all_params.keys()) - valid_fields
        if dropped_params:
            logging.warning(
                f"Dropped parameters in PartQuery.from_query: {sorted(dropped_params)}"
            )

        return cls(**cast(PartQueryDict, filtered_params))

    def update(self, **kwargs: Unpack[PartQueryDict]) -> PartQuery:
        """Update the context with new values.

        Args:
            **kwargs: Keyword arguments corresponding to dataclass fields

        Returns:
            New PartQuery with updated values
        """
        # Validate that all kwargs are valid field names
        valid_fields = {field.name for field in fields(self)}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields for PartQuery: {invalid_fields}")

        # type(self) is the constructor for the class (`cls` in classmethods). It may be a subclass of PartQuery.
        return type(self)(**cast(PartQueryDict, {**self.params(), **kwargs}))

    def params(self) -> PartQueryDict:
        """Get the parameters for the query."""
        return cast(
            PartQueryDict, {k: v for k, v in self.__dict__.items() if v is not None}
        )


# Context are immutable ("frozen") because when circuits are instantiated, there is memoization,
# the memoization key has all Contexts accessed by the first run of the circuit constructor.
@dataclass(frozen=True, kw_only=True)
class PassiveQuery(PartQuery):
    """Context for passive queries."""

    type: str | Sequence[str] | FindDistinctType | None = None
    tolerance: float | jitx.units.PlainQuantity | FindDistinctType | None = None
    precision: float | jitx.units.PlainQuantity | FindDistinctType | None = (
        None  # stanza version was typed as Percentage (FIXME: review)
    )
    tolerance_min: float | Interval | FindDistinctType | None = None
    tolerance_max: float | Interval | FindDistinctType | None = None
    component_datasheet: str | Sequence[str] | FindDistinctType | None = (
        None  # stanza version was typed as ? (FIXME: review)
    )
    metadata_image: str | Sequence[str] | FindDistinctType | None = (
        None  # stanza version was typed as ? (FIXME: review)
    )
    metadata_digi_key_part_number: str | Sequence[str] | FindDistinctType | None = None
    metadata_description: str | Sequence[str] | FindDistinctType | None = None
    metadata_packaging: str | Sequence[str] | FindDistinctType | None = (
        None  # stanza version was typed as ? (FIXME: review)
    )

    @classmethod
    def from_query(cls, query: PartQuery) -> PassiveQuery:
        """Create a PassiveQuery from a PartQuery."""
        # Filter params to only include fields defined in this class
        valid_fields = {field.name for field in fields(cls)}
        all_params = query.params()
        filtered_params = {k: v for k, v in all_params.items() if k in valid_fields}

        # Log warning for dropped parameters
        dropped_params = set(all_params.keys()) - valid_fields
        if dropped_params:
            logging.warning(
                f"Dropped parameters in PassiveQuery.from_query: {sorted(dropped_params)}"
            )

        return cls(**cast(PassiveQueryDict, filtered_params))

    def update(self, **kwargs: Unpack[PassiveQueryDict]) -> PassiveQuery:
        """Update the context with new values.

        Args:
            **kwargs: Keyword arguments corresponding to dataclass fields

        Returns:
            New PassiveQuery with updated values
        """
        # Validate that all kwargs are valid field names
        valid_fields = {field.name for field in fields(self)}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields for PassiveQuery: {invalid_fields}")

        return type(self)(**cast(PassiveQueryDict, {**self.params(), **kwargs}))

    def params(self) -> PassiveQueryDict:
        """Get the parameters for the query."""
        return cast(
            PassiveQueryDict, {k: v for k, v in self.__dict__.items() if v is not None}
        )


@dataclass(frozen=True, kw_only=True)
class ResistorQuery(PassiveQuery):
    """Context for resistor queries."""

    category: str | Sequence[str] | FindDistinctType | None = "resistor"
    resistance: (
        float
        | jitx.units.PlainQuantity
        | Interval
        | Sequence[float]
        | FindDistinctType
        | None
    ) = None
    rated_power: float | Interval | Sequence[float] | FindDistinctType | None = None
    composition: str | FindDistinctType | None = None
    tcr_pos: float | Interval | FindDistinctType | None = None
    tcr_neg: float | Interval | FindDistinctType | None = None
    metadata_series: str | FindDistinctType | None = None
    metadata_features: str | FindDistinctType | None = (
        None  # stanza version was typed as ? (FIXME: review)
    )
    metadata_supplier_device_package: str | FindDistinctType | None = None
    metadata_number_of_terminations: int | FindDistinctType | None = None

    def __post_init__(self):
        """Validate that category is set to 'resistor'."""
        if not (isinstance(self.category, str) and self.category == "resistor"):
            raise ValueError(
                f'ResistorQuery category must be "resistor", got {self.category!r}'
            )

    @classmethod
    def from_query(cls, query: PartQuery) -> ResistorQuery:
        """Create a ResistorQuery from a PartQuery."""
        # Filter params to only include fields defined in this class
        valid_fields = {field.name for field in fields(cls)}
        all_params = query.params()
        filtered_params = {
            k: v
            for k, v in all_params.items()
            if k in valid_fields and not (k == "category" and v != "resistor")
        }

        # Log warning for dropped parameters
        dropped_params = set(all_params.keys()) - set(filtered_params.keys())
        if dropped_params:
            logging.warning(
                f"Dropped parameters in ResistorQuery.from_query: {sorted(dropped_params)}"
            )

        return cls(**cast(ResistorQueryDict, filtered_params))

    def update(self, **kwargs: Unpack[ResistorQueryDict]) -> ResistorQuery:
        """Update the context with new values.

        Args:
            **kwargs: Keyword arguments corresponding to dataclass fields

        Returns:
            New ResistorQuery with updated values
        """
        # Validate that all kwargs are valid field names
        valid_fields = {field.name for field in fields(self)}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields for ResistorQuery: {invalid_fields}")

        return type(self)(**cast(ResistorQueryDict, {**self.params(), **kwargs}))

    @classmethod
    def refine(cls, **kwargs: Unpack[ResistorQueryDict]) -> ResistorQuery:
        """Refine an existing context with additional values."""
        return cls.require().update(**kwargs)

    def params(self) -> ResistorQueryDict:
        """Get the parameters for the query."""
        return cast(
            ResistorQueryDict, {k: v for k, v in self.__dict__.items() if v is not None}
        )


@dataclass(frozen=True, kw_only=True)
class CapacitorQuery(PassiveQuery):
    """Context for capacitor queries."""

    category: str | Sequence[str] | FindDistinctType | None = "capacitor"
    capacitance: (
        float | jitx.units.PlainQuantity | Interval | FindDistinctType | None
    ) = None
    anode: str | FindDistinctType | None = None
    electrolyte: str | FindDistinctType | None = None
    esr: float | Interval | FindDistinctType | None = None
    esr_frequency: float | Interval | FindDistinctType | None = None
    rated_voltage: float | Interval | FindDistinctType | None = None
    rated_voltage_ac: float | Interval | FindDistinctType | None = None
    rated_current_pk: float | Interval | FindDistinctType | None = None
    rated_current_rms: float | Interval | FindDistinctType | None = None
    temperature_coefficient_code: str | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_code' and typed as ? (FIXME: review)
    )
    temperature_coefficient_raw_data: str | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_raw-data' and typed as ? (FIXME: review). This is user-facing for 'temperature-coefficient.raw_data'.
    )
    temperature_coefficient_tolerance: float | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_tolerance' and typed as ? (FIXME: review)
    )
    temperature_coefficient_lower_temperature: float | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_lower-temperature' and typed as ? (FIXME: review)
    )
    temperature_coefficient_upper_temperature: float | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_upper-temperature' and typed as ? (FIXME: review)
    )
    temperature_coefficient_change: float | FindDistinctType | None = (
        None  # stanza version was 'temperature-coefficient_change' and typed as ? (FIXME: review)
    )
    metadata_lifetime_temp: float | Interval | FindDistinctType | None = None
    metadata_applications: str | FindDistinctType | None = (
        None  # stanza version was typed as ? (FIXME: review)
    )
    metadata_ripple_current_low_frequency: (
        float | Interval | FindDistinctType | None
    ) = None
    metadata_ripple_current_high_frequency: (
        float | Interval | FindDistinctType | None
    ) = None
    metadata_lead_spacing: float | Interval | FindDistinctType | None = None

    def __post_init__(self):
        """Validate that category is set to 'capacitor'."""
        if not (isinstance(self.category, str) and self.category == "capacitor"):
            raise ValueError(
                f'CapacitorQuery category must be "capacitor", got {self.category!r}'
            )

    @classmethod
    def from_query(cls, query: PartQuery) -> CapacitorQuery:
        """Create a CapacitorQuery from a PartQuery."""
        # Filter params to only include fields defined in this class
        valid_fields = {field.name for field in fields(cls)}
        all_params = query.params()
        filtered_params = {
            k: v
            for k, v in all_params.items()
            if k in valid_fields and not (k == "category" and v != "capacitor")
        }

        # Log warning for dropped parameters
        dropped_params = set(all_params.keys()) - set(filtered_params.keys())
        if dropped_params:
            logging.warning(
                f"Dropped parameters in CapacitorQuery.from_query: {sorted(dropped_params)}"
            )

        return cls(**cast(CapacitorQueryDict, filtered_params))

    def update(self, **kwargs: Unpack[CapacitorQueryDict]) -> CapacitorQuery:
        """Update the context with new values.

        Args:
            **kwargs: Keyword arguments corresponding to dataclass fields

        Returns:
            New CapacitorQuery with updated values
        """
        # Validate that all kwargs are valid field names
        valid_fields = {field.name for field in fields(self)}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields for CapacitorQuery: {invalid_fields}")

        return type(self)(**cast(CapacitorQueryDict, {**self.params(), **kwargs}))

    @classmethod
    def refine(cls, **kwargs: Unpack[CapacitorQueryDict]) -> CapacitorQuery:
        """Refine an existing context with additional values."""
        return cls.require().update(**kwargs)

    def params(self) -> CapacitorQueryDict:
        """Get the parameters for the query."""
        return cast(
            CapacitorQueryDict,
            {k: v for k, v in self.__dict__.items() if v is not None},
        )


@dataclass(frozen=True, kw_only=True)
class InductorQuery(PassiveQuery):
    """Context for inductor queries."""

    category: str | Sequence[str] | FindDistinctType | None = "inductor"
    inductance: (
        float | jitx.units.PlainQuantity | Interval | FindDistinctType | None
    ) = None
    material_core: str | FindDistinctType | None = None
    shielding: str | FindDistinctType | None = None
    current_rating: float | Interval | FindDistinctType | None = None
    saturation_current: float | Interval | FindDistinctType | None = None
    dc_resistance: float | Interval | FindDistinctType | None = None
    quality_factor: float | Interval | FindDistinctType | None = None
    quality_factor_frequency: float | Interval | FindDistinctType | None = None
    self_resonant_frequency: float | Interval | FindDistinctType | None = None

    def __post_init__(self):
        """Validate that category is set to 'inductor'."""
        if not (isinstance(self.category, str) and self.category == "inductor"):
            raise ValueError(
                f'InductorQuery category must be "inductor", got {self.category!r}'
            )

    @classmethod
    def from_query(cls, query: PartQuery) -> InductorQuery:
        """Create an InductorQuery from a PartQuery."""
        # Filter params to only include fields defined in this class
        valid_fields = {field.name for field in fields(cls)}
        all_params = query.params()
        filtered_params = {
            k: v
            for k, v in all_params.items()
            if k in valid_fields and not (k == "category" and v != "inductor")
        }

        # Log warning for dropped parameters
        dropped_params = set(all_params.keys()) - set(filtered_params.keys())
        if dropped_params:
            logging.warning(
                f"Dropped parameters in InductorQuery.from_query: {sorted(dropped_params)}"
            )

        return cls(**cast(InductorQueryDict, filtered_params))

    def update(self, **kwargs: Unpack[InductorQueryDict]) -> InductorQuery:
        """Update the context with new values.

        Args:
            **kwargs: Keyword arguments corresponding to dataclass fields

        Returns:
            New InductorQuery with updated values
        """
        # Validate that all kwargs are valid field names
        valid_fields = {field.name for field in fields(self)}
        invalid_fields = set(kwargs.keys()) - valid_fields
        if invalid_fields:
            raise ValueError(f"Invalid fields for InductorQuery: {invalid_fields}")

        return type(self)(**cast(InductorQueryDict, {**self.params(), **kwargs}))

    @classmethod
    def refine(cls, **kwargs: Unpack[InductorQueryDict]) -> InductorQuery:
        """Refine an existing context with additional values."""
        return cls.require().update(**kwargs)

    def params(self) -> InductorQueryDict:
        """Get the parameters for the query."""
        return cast(
            InductorQueryDict, {k: v for k, v in self.__dict__.items() if v is not None}
        )


class TwoPinShortTrace(Enum):
    """Short trace options for two-pin components."""

    SHORT_TRACE_BOTH = "short_trace_both"
    SHORT_TRACE_ANODE = "short_trace_anode"
    SHORT_TRACE_CATHODE = "short_trace_cathode"
    SHORT_TRACE_NEITHER = "short_trace_neither"


# Key name overrides
_key_overrides = {
    "esr-frequency": "esr_frequency",
    "temperature-coefficient_raw-data": "temperature-coefficient.raw_data",
    "quantity-needed": "max-minimum_quantity",
    "stock!": "_stock",
    # Those were handled as overrides in stanza but are now handled in extract.
    # "sellers!": "_sellers",
    # "sort!": "_sort",
    # "exist!": "_exist",
    # "distinct!": "_distinct",
}


def to_db_key(key: str) -> str:
    """Convert a Python key to the correct database key, applying underscore-to-dot mapping and overrides."""
    if key in _key_overrides:
        return _key_overrides[key]
    return key.replace("_", ".")


# Map python keyword argument names to stanza keywords
_key_mapping = {
    "trust": "trust",
    "category": "category",
    "mpn": "mpn",
    "mounting": "mounting",
    "manufacturer": "manufacturer",
    "description": "description",
    "case": "case",
    "min_stock": "min-stock",
    "quantity_needed": "quantity-needed",
    "price": "price",
    "x": "x",
    "y": "y",
    "z": "z",
    "area": "area",
    "rated_temperature_min": "rated-temperature_min",
    "rated_temperature_max": "rated-temperature_max",
    "operating_temperature": "operating-temperature",
    "stock": "stock!",
    "sellers": "sellers!",
    "sort": "sort!",
    "exist": "exist!",
    "distinct": "distinct!",
    "ignore_stock": "ignore-stock",
    # Passive keys
    "type": "type",
    "tolerance": "tolerance",
    "precision": "precision",
    "tolerance_min": "tolerance_min",
    "tolerance_max": "tolerance_max",
    "component_datasheet": "component_datasheet",
    "metadata_image": "metadata_image",
    "metadata_digi_key_part_number": "metadata_digi-key-part-number",
    "metadata_description": "metadata_description",
    "metadata_packaging": "metadata_packaging",
    # Resistor keys
    "resistance": "resistance",
    "rated_power": "rated-power",
    "composition": "composition",
    "tcr_pos": "tcr_pos",
    "tcr_neg": "tcr_neg",
    "metadata_series": "metadata_series",
    "metadata_features": "metadata_features",
    "metadata_supplier_device_package": "metadata_supplier-device-package",
    "metadata_number_of_terminations": "metadata_number-of-terminations",
    # Capacitor keys
    "capacitance": "capacitance",
    "anode": "anode",
    "electrolyte": "electrolyte",
    "esr": "esr",
    "esr_frequency": "esr-frequency",
    "rated_voltage": "rated-voltage",
    "rated_voltage_ac": "rated-voltage-ac",
    "rated_current_pk": "rated-current-pk",
    "rated_current_rms": "rated-current-rms",
    "temperature_coefficient_code": "temperature-coefficient_code",
    "temperature_coefficient_raw_data": "temperature-coefficient_raw-data",
    "temperature_coefficient_tolerance": "temperature-coefficient_tolerance",
    "temperature_coefficient_lower_temperature": "temperature-coefficient_lower-temperature",
    "temperature_coefficient_upper_temperature": "temperature-coefficient_upper-temperature",
    "temperature_coefficient_change": "temperature-coefficient_change",
    "metadata_lifetime_temp": "metadata_lifetime-temp",
    "metadata_applications": "metadata_applications",
    "metadata_ripple_current_low_frequency": "metadata_ripple-current-low-frequency",
    "metadata_ripple_current_high_frequency": "metadata_ripple-current-high-frequency",
    "metadata_lead_spacing": "metadata_lead-spacing",
    # Inductor keys
    "inductance": "inductance",
    "material_core": "material-core",
    "shielding": "shielding",
    "current_rating": "current-rating",
    "saturation_current": "saturation-current",
    "dc_resistance": "dc-resistance",
    "quality_factor": "quality-factor",
    "quality_factor_frequency": "quality-factor-frequency",
    "self_resonant_frequency": "self-resonant-frequency",
}


ProcessedQueryParamValue = (
    DistinctKey
    | ExistKeys
    | Interval
    | SortKey
    | Sequence[SortKey]
    | bool
    | float
    | int
    | str
)


def preprocess_keyword_args(
    kwargs: PartQueryDict,
) -> dict[str, ProcessedQueryParamValue]:
    """Preprocess keyword arguments for queries.

    Args:
        kwargs: Keyword arguments to preprocess

    Returns:
        Preprocessed arguments
    """
    result = {}

    # There can only be one FIND_DISTINCT parameter, otherwise raise an error.
    distinct_params = [
        key for key, value in kwargs.items() if isinstance(value, FindDistinctType)
    ]
    if len(distinct_params) > 1:
        raise ValueError(
            "There can only be one FIND_DISTINCT parameter. Got: {distinct_params}"
        )

    # There can only be one FIND_OPTIMUM parameter, otherwise raise an error.
    find_optimum_params = [
        key for key, value in kwargs.items() if isinstance(value, FindOptimum)
    ]
    if len(find_optimum_params) > 1:
        raise ValueError(
            "There can only be one FIND_OPTIMUM parameter. Got: {find_optimum_params}"
        )

    # There cannot be both tolerance and precision, otherwise raise an error.
    if kwargs.get("tolerance") is not None and kwargs.get("precision") is not None:
        raise ValueError(
            "Cannot specify both 'tolerance' and 'precision' in Parts DB parameters."
        )

    # Special handling for FindOptimum and FindDistinct
    for original_key, value in kwargs.items():
        if original_key not in _key_mapping:
            raise ValueError(f"Unknown Parts DB query parameter: {original_key}")

        # Special handling for FIND_DISTINCT
        if isinstance(value, FindDistinctType):
            result["distinct!"] = DistinctKey(original_key)

        # Special handling for FindOptimum
        elif isinstance(value, FindOptimum):
            direction = (
                SortDir.DECREASING
                if value == FindOptimum.FIND_MAXIMUM
                else SortDir.INCREASING
            )
            result["sort!"] = SortKey(original_key, direction)

        # Special handling for precision (converts to tolerance)
        elif original_key == "precision":
            result["tolerance"] = value
        # Normal case
        else:
            key = _key_mapping[original_key]
            result[key] = value

    return result


def extract(qb: PartQuery) -> dict[str, QueryParamValue]:
    """Extract query parameters for sending to the database.

    Args:
        qb: Query context to extract parameters from

    Returns:
        Extracted parameters
    """
    params = {}

    # Preprocess keyword arguments
    all_params = preprocess_keyword_args(qb.params())

    # Handle special keys and transformations
    for key, value in all_params.items():
        db_key = to_db_key(key)
        if db_key == "operating-temperature":
            # Cannot specify both operating-temperature and rated-temperature
            if (
                "rated-temperature_min" in all_params
                or "rated-temperature_max" in all_params
            ):
                raise ValueError(
                    "Cannot specify both 'rated-temperature' and 'operating-temperature' keys"
                )

            # Extract min and max from interval
            if not isinstance(value, Interval):
                raise ValueError(
                    f"Invalid non-Interval value for 'operating-temperature': {value}"
                )

            if value.min_value is not None:
                params["min-rated-temperature_min"] = value.min_value
            if value.max_value is not None:
                params["max-rated-temperature_max"] = value.max_value

        elif db_key == "sellers!":
            if isinstance(value, Sequence):
                params["_sellers"] = [
                    e.value if isinstance(e, AuthorizedVendor) else e for e in value
                ]

        elif db_key == "distinct!":
            if isinstance(value, DistinctKey):
                params["_distinct"] = to_db_key(_key_mapping[value.key])

        elif db_key == "exist!":
            if isinstance(value, ExistKeys):
                params["_exist"] = [to_db_key(_key_mapping[k]) for k in value.keys]

        elif db_key == "sort!":
            sort_keys: Sequence[SortKey]
            if isinstance(value, SortKey):
                sort_keys = (value,)
            # NOTE: "not isinstance(value, str)" is needed so type checkers do not think 'value' could be 'str'
            #        and then fails at 'sk.key' later.
            elif (
                isinstance(value, Sequence)
                and not isinstance(value, str)
                and all(isinstance(v, SortKey) for v in value)
            ):
                sort_keys = value
            else:
                raise ValueError(f"Invalid sort value: {value}")

            # Format sort keys
            sort_strings = []
            for sk in sort_keys:
                db_sort_key = to_db_key(_key_mapping[sk.key])
                prefix = "" if sk.direction == SortDir.INCREASING else "-"
                sort_strings.append(f"{prefix}{db_sort_key}")

            params["_sort"] = sort_strings

            # Special handling for price sorting
            if any(sk.key == "price" for sk in sort_keys) and not any(
                k in ["stock!", "_stock"] for k in all_params.keys()
            ):
                params["_stock"] = 1

        # Handle general case
        else:
            # Handle intervals
            if isinstance(value, Interval):
                if value.min_value is not None:
                    params[f"min-{db_key}"] = value.min_value
                if value.max_value is not None:
                    params[f"max-{db_key}"] = value.max_value
            else:
                params[db_key] = value

    # Special handling for ignore-stock
    if "ignore-stock" in all_params and all_params["ignore-stock"] is True:
        if "min-stock" in params:
            del params["min-stock"]
        if "_stock" in params:
            del params["_stock"]

    return params


SMD_PKGS = (
    "009005",
    "0301m",
    "01005",
    "0402m",
    "0201",
    "0603m",
    "0202",
    "0606m",
    "0204",
    "0510m",
    "Wide 0402",
    "0306",
    "0816m",
    "Wide 0603",
    "0402",
    "1005m",
    "0505",
    "1414m",
    "0508",
    "1220m",
    "Wide 0805",
    "0603",
    "1608m",
    "0612",
    "1632m",
    "Wide 1206",
    "0805",
    "2012m",
    "1111",
    "2828m",
    "1206",
    "3216m",
    "1210",
    "3225m",
    "1218",
    "3246m",
    "Wide 1812",
    "1225",
    "3263m",
    "Wide 2512",
    "1530",
    "3876m",
    "Wide 3015",
    "1808",
    "4520m",
    "1812",
    "4532m",
    "1825",
    "4564m",
    "1835",
    "4589",
    "Wide 3518",
    "5020m",
    "2010",
    "5025m",
    "2043",
    "Wide 4320",
    "2220",
    "5750m",
    "2225",
    "5763m",
    "2312",
    "6032m",
    "2512",
    "6331m",
    "2725",
    "7142m",
    "2728",
    "7142m",
    "Wide 2827",
    "2816",
    "2817",
    "7142m",
    "2953",
    "Wide 5929",
    "3920",
    "1052m",
)


def is_valid_smd_pkg(pkg: str) -> bool:
    """Check if a package is a valid SMD package."""
    return pkg in SMD_PKGS


# Helper functions for valid packages
def valid_smd_pkgs(min_pkg: str = "0402") -> Sequence[str]:
    """Get a list of valid SMD packages.

    Args:
        min_pkg: Minimum package size

    Returns:
        List of valid SMD packages
    """

    if not is_valid_smd_pkg(min_pkg):
        raise ValueError(
            f"Unknown SMD package requested as minimum: {min_pkg}. The known packages are:\n{SMD_PKGS}"
        )

    start_idx = SMD_PKGS.index(min_pkg)
    return SMD_PKGS[start_idx:]


# Top-level query builder functions
def make_resistor_query(
    qb: PartQuery | None = None, **kwargs: Unpack[ResistorQueryDict]
) -> ResistorQuery:
    """Make a ResistorQuery from a PartQuery or ResistorQuery.

    Args:
        qb: Optional base query context
        **kwargs: Additional query parameters

    Returns:
        ResistorQuery with the specified parameters
    """
    base_query = qb or ResistorQuery.get() or PartQuery.get()
    if isinstance(base_query, ResistorQuery):
        return base_query.update(**kwargs)
    elif isinstance(base_query, PartQuery):
        return ResistorQuery.from_query(base_query).update(**kwargs)
    else:
        return ResistorQuery(**kwargs)


def make_capacitor_query(
    qb: PartQuery | None = None, **kwargs: Unpack[CapacitorQueryDict]
) -> CapacitorQuery:
    """Make a CapacitorQuery from a PartQuery or CapacitorQuery.

    Args:
        qb: Optional base query context
        **kwargs: Additional query parameters

    Returns:
        CapacitorQuery with the specified parameters
    """
    base_query = qb or CapacitorQuery.get() or PartQuery.get()
    if isinstance(base_query, CapacitorQuery):
        return base_query.update(**kwargs)
    elif isinstance(base_query, PartQuery):
        return CapacitorQuery.from_query(base_query).update(**kwargs)
    else:
        return CapacitorQuery(**kwargs)


def make_inductor_query(
    qb: PartQuery | None = None, **kwargs: Unpack[InductorQueryDict]
) -> InductorQuery:
    """Make an InductorQuery from a PartQuery or InductorQuery.

    Args:
        qb: Optional base query context
        **kwargs: Additional query parameters

    Returns:
        InductorQuery with the specified parameters
    """
    base_query = qb or InductorQuery.get() or PartQuery.get()
    if isinstance(base_query, InductorQuery):
        return base_query.update(**kwargs)
    elif isinstance(base_query, PartQuery):
        return InductorQuery.from_query(base_query).update(**kwargs)
    else:
        return InductorQuery(**kwargs)


def make_part_query(
    qb: PartQuery | None = None, **kwargs: Unpack[PartQueryDict]
) -> PartQuery:
    """Make a PartQuery from a PartQuery.

    Args:
        qb: Optional base query context
        **kwargs: Additional query parameters

    Returns:
        PartQuery with the specified parameters
    """
    base_query = qb or PartQuery.get()
    if isinstance(base_query, PartQuery):
        return base_query.update(**kwargs)
    else:
        return PartQuery(**kwargs)


# Internal functions for creating components


def _internal_create_components(qb: PartQuery, limit: int) -> Sequence[PartType]:
    """Internal function to create components from a query.

    Args:
        qb: Query context
        limit: Maximum number of components to create

    Returns:
        List of components

    Raises:
        ValueError: If no components meet the requirements
    """
    params = extract(qb)
    results: Sequence[PartJSON] = dbquery(params, limit)

    if not results:
        raise ValueError(f"No components meeting requirements: {params}")

    return [to_component(result) for result in results]


def _internal_create_component(qb: PartQuery) -> PartType:
    """Internal function to create a single component from a query.

    Args:
        qb: Query context

    Returns:
        PartType

    Raises:
        ValueError: If no components meet the requirements
    """
    comps = _internal_create_components(qb, 1)
    if not comps:
        raise ValueError("Component list is empty")
    return comps[0]


# Public API for creating components


class InsertContainer(jitx.container.Container):
    nets: list[jitx.Net]
    a_short_trace: jitx.net.ShortTrace | None
    c_short_trace: jitx.net.ShortTrace | None


class Resistor(jitx.Component):
    """Resistor component.

    Args:
        query: query to optionally override the current ResistorQuery or PartQuery from the DesignContext.
        comp_name: name of the component to be created.
        **kwargs: Additional query parameters
    Raises:
        Exception: If no components meet the requirements
    """

    mpn: str
    manufacturer: str
    datasheet: str
    reference_designator_prefix: str
    value: jitx.units.PlainQuantity
    p1: jitx.Port
    p2: jitx.Port
    landpattern: jitx.Landpattern
    symbol: jitx.Symbol
    cmappings: list[jitx.PadMapping | jitx.SymbolMapping]
    data: ResistorType

    def __init__(
        self,
        query: PartQuery | None = None,
        *,
        comp_name: str | None = None,
        **kwargs: Unpack[ResistorQueryDict],
    ):
        rq = make_resistor_query(query, **kwargs)
        if isinstance(rq.resistance, jitx.units.PlainQuantity):
            assert rq.resistance.dimensionality == jitx.units.ohm.dimensionality, (
                f"Resistance Quantity requested by the user from the Parts DB is not in a compatible unit: '{rq.resistance.units}'."
            )
        if isinstance(rq.tolerance, jitx.units.PlainQuantity):
            assert (rq.tolerance.dimensionality, rq.tolerance.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Tolerance Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.tolerance.units}'."
            )
        if isinstance(rq.precision, jitx.units.PlainQuantity):
            assert (rq.precision.dimensionality, rq.precision.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Precision Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.precision.units}'."
            )

        try:
            part = _internal_create_component(rq)
            if not isinstance(part, ResistorType):
                raise TypeError("Component returned is not a Resistor")
            self.data = part

            component = convert_component(
                part.component,
                component_name=comp_name,
                use_jitxstd_symbol=StdLibSymbolType.Resistor,
            )
            instance = component()

            # type(self).__name__ = type(instance).__name__
            assert instance.mpn is not None, (
                "Missing mpn field on part queried from the Parts DB."
            )
            assert instance.manufacturer is not None, (
                "Missing manufacturer field on part queried from the Parts DB."
            )
            assert instance.reference_designator_prefix is not None, (
                "Missing reference_designator_prefix field on part queried from the Parts DB."
            )
            assert isinstance(instance.value, jitx.units.Quantity), (
                "Missing value field on part queried from the Parts DB."
            )
            self.mpn = instance.mpn
            self.manufacturer = instance.manufacturer
            self.reference_designator_prefix = instance.reference_designator_prefix
            # Case: the user queried on a resistance Quantity, keep its formatting untouched.
            if isinstance(rq.resistance, jitx.units.PlainQuantity):
                self.value = rq.resistance
            else:
                assert isinstance(instance.value, jitx.units.Quantity), (
                    "Resistance value from Parts DB is not a Quantity"
                )
                self.value = instance.value.to_compact()

            # Extra Parts DB attributes not part of jitx.Component fields.
            datasheet = getattr(instance, "datasheet", None)
            assert datasheet is not None, (
                "Missing datasheet field on part queried from the Parts DB."
            )
            self.datasheet = datasheet

            landpattern = getattr(instance, "landpattern", None)
            symbol = getattr(instance, "symbol", None)
            cmappings = getattr(instance, "cmappings", None)
            assert isinstance(landpattern, jitx.Landpattern), (
                "Missing landpattern field on part queried from the Parts DB."
            )
            assert isinstance(symbol, jitx.Symbol), (
                "Missing symbol field on part queried from the Parts DB."
            )
            assert isinstance(cmappings, list), (
                "Missing cmappings field on part queried from the Parts DB."
            )
            self.landpattern = landpattern
            self.symbol = symbol
            self.cmappings = cmappings

            self.p1, self.p2 = get_element_ports(instance)

            # Suppress the warning about `instance` being orphaned.
            jitx._structural.dispose(instance)

        except Exception as e:
            arg_list = "\n- ".join(f"{k}: {v}" for k, v in extract(rq).items())
            logging.error(f"Failed to create resistor for query:\n- {arg_list}\n{e}")
            raise

    def insert(
        self,
        pin_a: jitx.Port | jitx.Net,
        pin_b: jitx.Port | jitx.Net,
        *,
        short_trace: TwoPinShortTrace | bool = TwoPinShortTrace.SHORT_TRACE_NEITHER,
    ) -> Self:
        """Insert this resistor between two pins of a circuit.

        Args:
            self: Component
            pin_a: First pin
            pin_b: Second pin
            short_trace: Short trace option

        """

        c = InsertContainer()

        c.nets = [
            pin_a + self.p1,
            pin_b + self.p2,
        ]

        st = to_short_trace_enum(short_trace)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_ANODE
        ):
            if not isinstance(pin_a, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Resistor.insert's pin_a."
                )
            c.a_short_trace = jitx.net.ShortTrace(pin_a, self.p1)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_CATHODE
        ):
            if not isinstance(pin_b, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Resistor.insert's pin_b."
                )
            c.c_short_trace = jitx.net.ShortTrace(pin_b, self.p2)

        circuit = current.circuit
        circuit += c

        return self


class Capacitor(jitx.Component):
    """Capacitor component.

    Args:
        query: query to optionally override the current CapacitorQuery or PartQuery from the DesignContext.
        comp_name: name of the component to be created.
        polarized: whether the capacitor is polarized.
        **kwargs: Additional query parameters

    Raises:
        Exception: If no components meet the requirements
    """

    mpn: str
    manufacturer: str
    datasheet: str
    reference_designator_prefix: str
    value: jitx.units.PlainQuantity
    p1: jitx.Port
    p2: jitx.Port
    landpattern: jitx.Landpattern
    symbol: jitx.Symbol
    cmappings: list[jitx.PadMapping | jitx.SymbolMapping]
    # True if p1 is the anode and p2 is the cathode (pin names a and c in parts db)
    polarized: bool
    data: CapacitorType

    def __init__(
        self,
        query: PartQuery | None = None,
        *,
        comp_name: str | None = None,
        polarized: bool = False,
        **kwargs: Unpack[CapacitorQueryDict],
    ):
        rq = make_capacitor_query(query, **kwargs)
        if isinstance(rq.capacitance, jitx.units.PlainQuantity):
            assert rq.capacitance.dimensionality == jitx.units.F.dimensionality, (
                f"Capacitance Quantity requested by the user from the Parts DB is not in a compatible unit: '{rq.capacitance.units}'."
            )
        if isinstance(rq.tolerance, jitx.units.PlainQuantity):
            assert (rq.tolerance.dimensionality, rq.tolerance.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Tolerance Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.tolerance.units}'."
            )
        if isinstance(rq.precision, jitx.units.PlainQuantity):
            assert (rq.precision.dimensionality, rq.precision.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Precision Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.precision.units}'."
            )

        try:
            part = _internal_create_component(rq)
            if not isinstance(part, CapacitorType):
                raise TypeError("Component returned is not a Capacitor")
            self.data = part

            symbol_type = (
                StdLibSymbolType.PolarizedCapacitor
                if polarized
                else StdLibSymbolType.Capacitor
            )
            component = convert_component(
                part.component,
                component_name=comp_name,
                use_jitxstd_symbol=symbol_type,
            )
            instance = component()

            # type(self).__name__ = type(instance).__name__
            assert instance.mpn is not None, (
                "Missing mpn field on part queried from the Parts DB."
            )
            assert instance.manufacturer is not None, (
                "Missing manufacturer field on part queried from the Parts DB."
            )
            assert instance.reference_designator_prefix is not None, (
                "Missing reference_designator_prefix field on part queried from the Parts DB."
            )
            assert isinstance(instance.value, jitx.units.Quantity), (
                "Missing value field on part queried from the Parts DB."
            )
            self.mpn = instance.mpn
            self.manufacturer = instance.manufacturer
            self.reference_designator_prefix = instance.reference_designator_prefix
            if isinstance(rq.capacitance, jitx.units.PlainQuantity):
                self.value = rq.capacitance
            else:
                assert isinstance(instance.value, jitx.units.Quantity), (
                    "Capacitance value from Parts DB is not a Quantity"
                )
                self.value = instance.value.to_compact()

            # Extra Parts DB attributes not part of jitx.Component fields.
            datasheet = getattr(instance, "datasheet", None)
            assert datasheet is not None, (
                "Missing datasheet field on part queried from the Parts DB."
            )
            self.datasheet = datasheet

            landpattern = getattr(instance, "landpattern", None)
            symbol = getattr(instance, "symbol", None)
            cmappings = getattr(instance, "cmappings", None)
            assert isinstance(landpattern, jitx.Landpattern), (
                "Missing landpattern field on part queried from the Parts DB."
            )
            assert isinstance(symbol, jitx.Symbol), (
                "Missing symbol field on part queried from the Parts DB."
            )
            assert isinstance(cmappings, list), (
                "Missing cmappings field on part queried from the Parts DB."
            )
            self.landpattern = landpattern
            self.symbol = symbol
            self.cmappings = cmappings

            self.p1, self.p2 = get_element_ports(instance)
            # Whether the Parts DB returned a polarized capacitor.
            self.polarized = anode_cathode(instance) is not None
            # If the capacitor was requested as polarized, the Parts DB should have returned a polarized capacitor.
            assert not polarized or self.polarized, (
                f"The Parts DB returned the non-polarized capacitor {instance.mpn} to a PolarizedCapacitor instantiation. Restrict the query further to ensure the matching component is polarized."
            )

            # Suppress the warning about `instance` being orphaned.
            jitx._structural.dispose(instance)

        except Exception as e:
            arg_list = "\n- ".join(f"{k}: {v}" for k, v in extract(rq).items())
            logging.error(f"Failed to create capacitor for query:\n- {arg_list}\n{e}")
            raise

    def insert(
        self,
        pin_a: jitx.Port | jitx.Net,
        pin_b: jitx.Port | jitx.Net,
        *,
        short_trace: TwoPinShortTrace | bool = TwoPinShortTrace.SHORT_TRACE_NEITHER,
    ) -> Self:
        """Insert this capacitor between two pins of a circuit.

        Args:
            self: Component
            pin_a: First pin
            pin_b: Second pin
            short_trace: Short trace option

        """

        c = InsertContainer()

        c.nets = [
            pin_a + self.p1,
            pin_b + self.p2,
        ]

        st = to_short_trace_enum(short_trace)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_ANODE
        ):
            if not isinstance(pin_a, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Capacitor.insert's pin_a."
                )
            c.a_short_trace = jitx.net.ShortTrace(pin_a, self.p1)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_CATHODE
        ):
            if not isinstance(pin_b, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Capacitor.insert's pin_b."
                )
            c.c_short_trace = jitx.net.ShortTrace(pin_b, self.p2)

        circuit = current.circuit
        circuit += c

        return self


class PolarizedCapacitor(Capacitor):
    """Polarized capacitor component."""

    a: jitx.Port
    c: jitx.Port

    def __init__(self, *args, **kwargs):
        super().__init__(*args, polarized=True, **kwargs)
        assert self.polarized, (
            "PolarizedCapacitor must be polarized, it is not a polarized capacitor in the parts DB."
        )
        # Port aliases
        self.a = jitx._structural.Proxy.create(self.p1, ref=True)
        self.c = jitx._structural.Proxy.create(self.p2, ref=True)


class Inductor(jitx.Component):
    """Inductor component.

    Args:
        query: query to optionally override the current InductorQuery or PartQuery from the DesignContext.
        comp_name: name of the component to be created.
        **kwargs: Additional query parameters

    Raises:
        Exception: If no components meet the requirements
    """

    mpn: str
    manufacturer: str
    datasheet: str
    reference_designator_prefix: str
    value: jitx.units.PlainQuantity
    p1: jitx.Port
    p2: jitx.Port
    landpattern: jitx.Landpattern
    symbol: jitx.Symbol
    cmappings: list[jitx.PadMapping | jitx.SymbolMapping]
    data: InductorType

    def __init__(
        self,
        query: PartQuery | None = None,
        *,
        comp_name: str | None = None,
        **kwargs: Unpack[InductorQueryDict],
    ):
        rq = make_inductor_query(query, **kwargs)
        if isinstance(rq.inductance, jitx.units.PlainQuantity):
            assert rq.inductance.dimensionality == jitx.units.H.dimensionality, (
                f"Inductance Quantity requested by the user from the Parts DB is not in a compatible unit: '{rq.inductance.units}'."
            )
        if isinstance(rq.tolerance, jitx.units.PlainQuantity):
            assert (rq.tolerance.dimensionality, rq.tolerance.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Tolerance Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.tolerance.units}'."
            )
        if isinstance(rq.precision, jitx.units.PlainQuantity):
            assert (rq.precision.dimensionality, rq.precision.units) == (
                jitx.units.percent.dimensionality,
                jitx.units.percent,
            ), (
                f"Precision Quantity requested by the user from the Parts DB only support a dimensionless percentage, got: '{rq.precision.units}'."
            )

        try:
            part = _internal_create_component(rq)
            if not isinstance(part, InductorType):
                raise TypeError("Component returned is not a Inductor")
            self.data = part

            component = convert_component(
                part.component,
                component_name=comp_name,
                use_jitxstd_symbol=StdLibSymbolType.Inductor,
            )
            instance = component()

            # type(self).__name__ = type(instance).__name__
            assert instance.mpn is not None, (
                "Missing mpn field on part queried from the Parts DB."
            )
            assert instance.manufacturer is not None, (
                "Missing manufacturer field on part queried from the Parts DB."
            )
            assert instance.reference_designator_prefix is not None, (
                "Missing reference_designator_prefix field on part queried from the Parts DB."
            )
            assert isinstance(instance.value, jitx.units.Quantity), (
                "Missing value field on part queried from the Parts DB."
            )
            self.mpn = instance.mpn
            self.manufacturer = instance.manufacturer
            self.reference_designator_prefix = instance.reference_designator_prefix
            if isinstance(rq.inductance, jitx.units.PlainQuantity):
                self.value = rq.inductance
            else:
                assert isinstance(instance.value, jitx.units.Quantity), (
                    "Inductance value from Parts DB is not a Quantity"
                )
                self.value = instance.value.to_compact()

            # Extra Parts DB attributes not part of jitx.Component fields.
            datasheet = getattr(instance, "datasheet", None)
            assert datasheet is not None, (
                "Missing datasheet field on part queried from the Parts DB."
            )
            self.datasheet = datasheet

            landpattern = getattr(instance, "landpattern", None)
            symbol = getattr(instance, "symbol", None)
            cmappings = getattr(instance, "cmappings", None)
            assert isinstance(landpattern, jitx.Landpattern), (
                "Missing landpattern field on part queried from the Parts DB."
            )
            assert isinstance(symbol, jitx.Symbol), (
                "Missing symbol field on part queried from the Parts DB."
            )
            # FIXME: not always set? Check if symbols or landpattern can actually be None? (not assumed in convert_utils)
            assert isinstance(cmappings, list), (
                "Missing cmappings field on part queried from the Parts DB."
            )
            self.landpattern = landpattern
            self.symbol = symbol
            self.cmappings = cmappings

            self.p1, self.p2 = get_element_ports(instance)

            # Suppress the warning about `instance` being orphaned.
            jitx._structural.dispose(instance)

        except Exception as e:
            arg_list = "\n- ".join(f"{k}: {v}" for k, v in extract(rq).items())
            logging.error(f"Failed to create inductor for query:\n- {arg_list}\n{e}")
            raise

    def insert(
        self,
        pin_a: jitx.Port | jitx.Net,
        pin_b: jitx.Port | jitx.Net,
        *,
        short_trace: TwoPinShortTrace | bool = TwoPinShortTrace.SHORT_TRACE_NEITHER,
    ) -> Self:
        """Insert this inductor between two pins of a circuit.

        Args:
            self: Component
            pin_a: First pin
            pin_b: Second pin
            short_trace: Short trace option

        """

        c = InsertContainer()

        c.nets = [
            pin_a + self.p1,
            pin_b + self.p2,
        ]

        st = to_short_trace_enum(short_trace)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_ANODE
        ):
            if not isinstance(pin_a, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Inductor.insert's pin_a."
                )
            c.a_short_trace = jitx.net.ShortTrace(pin_a, self.p1)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_CATHODE
        ):
            if not isinstance(pin_b, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Inductor.insert's pin_b."
                )
            c.c_short_trace = jitx.net.ShortTrace(pin_b, self.p2)

        circuit = current.circuit
        circuit += c

        return self


class Part(jitx.Component):
    """Part component.

    Args:
        query: query to optionally override the current PartQuery from the DesignContext.
        comp_name: name of the component to be created.
        **kwargs: Additional query parameters

    Raises:
        Exception: If no components meet the requirements
    """

    mpn: str
    manufacturer: str
    datasheet: str
    reference_designator_prefix: str
    landpattern: jitx.Landpattern
    symbol: jitx.Symbol
    cmappings: list[jitx.PadMapping | jitx.SymbolMapping]
    data: PartType

    def __init__(
        self,
        query: PartQuery | None = None,
        *,
        comp_name: str | None = None,
        **kwargs: Unpack[PartQueryDict],
    ):
        rq = make_part_query(query, **kwargs)

        try:
            part = _internal_create_component(rq)
            self.data = part

            component = convert_component(
                part.component,
                component_name=comp_name,
                use_jitxstd_symbol=get_jitxstd_symbol(part.category),
            )
            instance = component()

            # type(self).__name__ = type(instance).__name__
            assert instance.mpn is not None, (
                "Missing mpn field on part queried from the Parts DB."
            )
            assert instance.manufacturer is not None, (
                "Missing manufacturer field on part queried from the Parts DB."
            )
            assert instance.reference_designator_prefix is not None, (
                "Missing reference_designator_prefix field on part queried from the Parts DB."
            )
            self.mpn = instance.mpn
            self.manufacturer = instance.manufacturer
            self.reference_designator_prefix = instance.reference_designator_prefix

            # Extra Parts DB attributes not part of jitx.Component fields.
            datasheet = getattr(instance, "datasheet", None)
            assert datasheet is not None, (
                "Missing datasheet field on part queried from the Parts DB."
            )
            self.datasheet = datasheet

            landpattern = getattr(instance, "landpattern", None)
            symbol = getattr(instance, "symbol", None)
            cmappings = getattr(instance, "cmappings", None)
            assert isinstance(landpattern, jitx.Landpattern), (
                "Missing landpattern field on part queried from the Parts DB."
            )
            assert isinstance(symbol, jitx.Symbol), (
                "Missing symbol field on part queried from the Parts DB."
            )
            assert isinstance(cmappings, list), (
                "Missing cmappings field on part queried from the Parts DB."
            )
            self.landpattern = landpattern
            self.symbol = symbol
            self.cmappings = cmappings

            for trace, obj in jitx.inspect.visit(instance, jitx.Port):
                # print(trace.path, jitx._structural.pathstring(trace.path), obj)

                if len(trace.path) == 1:
                    field_name = trace.path[0]
                    assert isinstance(field_name, str)
                    setattr(self, field_name, obj)
                elif len(trace.path) == 2:
                    [a, b] = trace.path
                    assert isinstance(a, str)
                    # Case: Tuple / list attribute
                    if isinstance(b, int):
                        if not hasattr(self, a):
                            setattr(self, a, [])
                        getattr(self, a).append(obj)
                    elif isinstance(b, jitx._structural.Item):
                        if not hasattr(self, a):
                            setattr(self, a, {})
                        getattr(self, a)[b.value] = obj
                    else:
                        raise ValueError(
                            f"Unexpected field of component from parts database at {trace.path}"
                        )
                else:
                    raise ValueError(
                        f"Unexpected field of component from parts database with more than 2 elements: {trace.path}"
                    )

            # Suppress the warning about `instance` being orphaned.
            jitx._structural.dispose(instance)

        except Exception as e:
            arg_list = "\n- ".join(f"{k}: {v}" for k, v in extract(rq).items())
            logging.error(f"Failed to create part for query:\n- {arg_list}\n{e}")
            raise

    def insert(
        self,
        pin_a: jitx.Port | jitx.Net,
        pin_b: jitx.Port | jitx.Net,
        *,
        short_trace: TwoPinShortTrace | bool = TwoPinShortTrace.SHORT_TRACE_NEITHER,
    ) -> Self:
        """Insert this part between two pins of a circuit.

        Args:
            self: Component
            pin_a: First pin
            pin_b: Second pin
            short_trace: Short trace option

        Raises:
            AssertionError: If the part does not have exactly 2 pins.
        """

        c = InsertContainer()

        ports = tuple(jitx.inspect.decompose(self, jitx.Port))
        assert len(ports) == 2, "Part must have exactly 2 pins to be inserted."
        p1, p2 = ports

        c.nets = [
            pin_a + p1,
            pin_b + p2,
        ]

        st = to_short_trace_enum(short_trace)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_ANODE
        ):
            if not isinstance(pin_a, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Part.insert's pin_a."
                )
            c.a_short_trace = jitx.net.ShortTrace(pin_a, p1)
        if (
            st == TwoPinShortTrace.SHORT_TRACE_BOTH
            or st == TwoPinShortTrace.SHORT_TRACE_CATHODE
        ):
            if not isinstance(pin_b, jitx.Port):
                raise ValueError(
                    "Cannot make a shortrace with a net. Give a port to Part.insert's pin_b."
                )
            c.c_short_trace = jitx.net.ShortTrace(pin_b, p2)

        circuit = current.circuit
        circuit += c

        return self


# Functions for searching components


def search_resistors(
    qb: PartQuery | None = None,
    *,
    limit: int = 1000,
    **kwargs: Unpack[ResistorQueryDict],
) -> Sequence[PartJSON]:
    """Search for resistors.

    Args:
        qb: Query context
        limit: Maximum number of results
        **kwargs: Additional query parameters

    Returns:
        List of resistors
    """
    rq = make_resistor_query(qb, **kwargs)
    params = extract(rq)
    results = dbquery(params, limit)

    return results


def search_capacitors(
    qb: PartQuery | None = None,
    *,
    limit: int = 1000,
    **kwargs: Unpack[CapacitorQueryDict],
) -> Sequence[PartJSON]:
    """Search for capacitors.

    Args:
        qb: Query context
        limit: Maximum number of results
        **kwargs: Additional query parameters

    Returns:
        List of capacitors
    """
    cq = make_capacitor_query(qb, **kwargs)
    params = extract(cq)
    results = dbquery(params, limit)

    return results


def search_inductors(
    qb: PartQuery | None = None,
    *,
    limit: int = 1000,
    **kwargs: Unpack[InductorQueryDict],
) -> Sequence[PartJSON]:
    """Search for inductors.

    Args:
        qb: Query context
        limit: Maximum number of results
        **kwargs: Additional query parameters

    Returns:
        List of inductors
    """
    iq = make_inductor_query(qb, **kwargs)
    params = extract(iq)
    results = dbquery(params, limit)

    return results


def search_parts(
    qb: PartQuery | None = None,
    *,
    limit: int = 1000,
    **kwargs: Unpack[PartQueryDict],
) -> Sequence[PartJSON]:
    """Search for parts.

    Args:
        qb: Query context
        limit: Maximum number of results
        **kwargs: Additional query parameters

    Returns:
        List of parts
    """
    pq = make_part_query(qb, **kwargs)
    params = extract(pq)
    results = dbquery(params, limit)

    return results


# Insert utility functions for two-pin components


def to_short_trace_enum(short_trace: TwoPinShortTrace | bool) -> TwoPinShortTrace:
    """Convert a short trace parameter to a TwoPinShortTrace enum."""
    # compatibility conversions for old interface
    if isinstance(short_trace, bool):
        return (
            TwoPinShortTrace.SHORT_TRACE_ANODE
            if short_trace
            else TwoPinShortTrace.SHORT_TRACE_NEITHER
        )
    return short_trace


def get_element_ports(inst: jitx.Component) -> tuple[jitx.Port, jitx.Port]:
    """Get the ports of an element."""
    mAC = anode_cathode(inst)
    if mAC:
        return mAC
    else:
        a, b, *_ = jitx.inspect.decompose(inst, jitx.Port)
        assert len(_) == 0, (
            f"Expected passive components from the Parts DB to have two ports, got {a}, {b} and extra ports: {_}"
        )
        return a, b


def anode_cathode(inst: jitx.Component) -> tuple[jitx.Port, jitx.Port] | None:
    """Get the anode and cathode ports of an element."""
    a = getattr(inst, "a", None)
    c = getattr(inst, "c", None)
    if a and c:
        return a, c
