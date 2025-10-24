from collections.abc import Sequence, Mapping
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json, DataClassJsonMixin
from enum import Enum
from .common import KeyValue
from .landpattern import PinByTypeCode, Shape, Text

from .landpattern import LandPatternCode, PCBPadCode, Point


class Dir(str, Enum):
    Right = "Right"
    Left = "Left"
    Up = "Up"
    Down = "Down"


@dataclass_json
@dataclass(frozen=True)
class SymbolLayerCode:
    name: str
    shape: Shape


@dataclass_json
@dataclass(frozen=True)
class LayerReference:
    layer: str
    text: Text


@dataclass_json
@dataclass(frozen=True)
class LayerValue:
    layer: str
    text: Text


@dataclass_json
@dataclass(frozen=True)
class SymbolPinCode:
    pin: PinByTypeCode
    point: Point
    direction: Dir
    length: float
    number_size: float | None = None
    name_size: float | None = None


@dataclass_json
@dataclass(frozen=True)
class SymbolCode:
    name: str
    bank: int
    pins: Sequence[SymbolPinCode]
    layer_reference: LayerReference
    layer_value: LayerValue
    layers: Sequence[SymbolLayerCode]


class PinElectricalType(str, Enum):
    UNSPECIFIED = "unspecified"
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER_IN = "power_in"
    PASSIVE = "passive"


@dataclass_json
@dataclass(frozen=True)
class PinPropertyCode:
    pin: PinByTypeCode
    # It seems EasyEDA enforces a 1 to 1 mapping between schematic pins and pads
    pads: Sequence[PinByTypeCode]
    direction: Dir
    electrical_type: PinElectricalType
    bank: int | str


@dataclass_json
@dataclass(frozen=True)
class PowerPinCode:
    pin: PinByTypeCode
    min_voltage: float
    max_voltage: float


@dataclass_json
@dataclass(frozen=True)
class NoConnectCode:
    pin: PinByTypeCode


@dataclass_json
@dataclass(frozen=True)
class PinPropertiesCode:
    pins: Sequence[PinPropertyCode]
    power_pins: Sequence[PowerPinCode]
    no_connects: Sequence[NoConnectCode]


# TODO: Extend to more families (check with stakeholders)
#       Also see: parts_db.scrapers.jlcpcb.types.get_jitx_category_for_jlcpcb_category
class Category(str, Enum):
    ANTENNA = "antenna"
    CAPACITOR = "capacitor"
    CONNECTOR = "connector"
    CRYSTAL = "crystal"
    DIODE = "diode"
    FERRITE_BEAD = "ferrite-bead"
    FUSE = "fuse"
    IC = "ic"
    INDUCTOR = "inductor"
    LED = "led"
    MECHANICAL = "mechanical"
    MICROCONTROLLER = "microcontroller"
    POTENTIOMETER = "potentiometer"
    POWER_SUPPLY_CHIP = "power_supply_chip"
    RESISTOR = "resistor"
    RESONATOR = "resonator"
    SENSOR = "sensor"
    SOCKET = "socket"
    SWITCH = "switch"
    TRANSFORMER = "transformer"
    TRANSISTOR = "transistor"
    VARISTOR = "varistor"


@dataclass_json
@dataclass(frozen=True)
class ResistorEModel:
    #  Nominal resistance in Ohms
    resistance: float | None

    # Resistance tolerance in percent
    tolerance: float | None

    # Maximum power in Watts
    max_power: float | None


@dataclass_json
@dataclass(frozen=True)
class InductorEModel:
    # Nominal inductance in Microhenries
    inductance: float | None

    # Inductance tolerance in percent
    tolerance: float | None

    # Maximum working current in amps
    max_current: float | None


@dataclass_json
@dataclass(frozen=True)
class CapacitorEModel:
    # Nominal capacitance in Farads
    capacitance: float | None

    # Capacitance tolerance in percent
    tolerance: float | None

    # Maximum working voltage in Volts
    max_voltage: float | None

    # True if capacitor is polarized
    polarized: bool | None

    # True if capacitor is low-ESR
    low_esr: bool | None

    # Temperature coefficient designator (`X7R, `X5R)
    temperature_coefficient: str | None

    # Dielectric Designator (`Ceramic, `Tantalum, `Electrolytic)
    dielectric: str | None


@dataclass_json
@dataclass(frozen=True)
class EModel:
    type: Category
    value: ResistorEModel | InductorEModel | CapacitorEModel


@dataclass_json
@dataclass(frozen=True)
class BundleCode:
    name: str


@dataclass_json
@dataclass(frozen=True)
class SupportRequireCode:
    bundle_name: str


@dataclass_json
@dataclass(frozen=True)
class PinMappingCode:
    key: PinByTypeCode
    value: PinByTypeCode


@dataclass_json
@dataclass(frozen=True)
class SupportOptionCode:
    requires: Sequence[SupportRequireCode]
    pin_mappings: Sequence[PinMappingCode]


@dataclass_json
@dataclass(frozen=True)
class SupportCode:
    bundle_name: str
    options: Sequence[SupportOptionCode]


# Use exact values of enum names, so it's easier to tell where it came from in jitx-client
# (if we just used "bool" we might be scratching out heads).
class JITXValueByType(str, Enum):
    TypeBoolean = "TypeBoolean"
    TypeInt = "TypeInt"
    TypeDouble = "TypeDouble"
    TypeString = "TypeString"
    TypeSymbol = "TypeSymbol"
    TypeToleranced = "TypeToleranced"
    TypeKeyValue = "TypeKeyValue"
    TypeMetadata = "TypeMetadata"
    TypeTupleValueByType = "TypeTupleValueByType"


@dataclass_json
@dataclass(frozen=True)
class TolerancedCode:
    typical: float
    plus: float
    minus: float


JITXValue = (
    bool
    | int
    | float
    | str
    | TolerancedCode
    | Sequence[KeyValue]
    | Sequence["JITXValueByTypeCode"]
)


@dataclass_json
@dataclass(frozen=True)
class JITXValueByTypeCode:
    type: JITXValueByType
    # The Tuple should be replaced by the following, but Python can't self-reference:
    #   - Tuple[KeyValue]
    #   - Tuple[JITXValueByTypeCode]
    value: JITXValue


@dataclass_json
@dataclass(frozen=True)
class ComponentPropertyCode:
    name: str
    value: JITXValueByTypeCode


@dataclass_json
@dataclass(frozen=True)
class DimensionsCode:
    x: float
    y: float
    z: float | None
    area: float


@dataclass_json
@dataclass(frozen=True)
class MinMax:
    min: float
    max: float


@dataclass_json
@dataclass(frozen=True)
class SellerOfferPrice:
    quantity: int
    converted_price: float


@dataclass_json
@dataclass(frozen=True)
class SellerOffer:
    inventory_level: int
    prices: Sequence[SellerOfferPrice]


@dataclass_json
@dataclass(frozen=True)
class Seller:
    updated_at: str
    company_name: str
    resolved_price: float
    offers: Sequence[SellerOffer]
    # Introduced after initial population.
    # If missing, this means the source was before Cofactr integration, and can be derived from "git_sha".
    source: str | None = None


@dataclass_json
@dataclass(frozen=True)
class ComponentCode:
    name: str
    description: str
    manufacturer: str
    mpn: str
    datasheet: str
    reference_prefix: str
    emodel: EModel | None
    pin_properties: PinPropertiesCode
    pcb_pads: Sequence[PCBPadCode]
    landpattern: LandPatternCode | None
    symbols: Sequence[SymbolCode]
    metadata: Sequence[KeyValue]
    properties: Sequence[ComponentPropertyCode]
    bundles: Sequence[BundleCode]
    supports: Sequence[SupportCode]


@dataclass_json
@dataclass(frozen=True)
class Part(DataClassJsonMixin):
    git_sha: str
    updated_at: str
    component: ComponentCode
    description: str
    manufacturer: str
    manufacturer_aliases: Sequence[str]
    mpn: str
    mpn_aliases: Sequence[str]
    cofactr_id: str | None
    vendor_part_numbers: Mapping[str, str]
    category: Category | None
    trust: str
    mounting: str | None
    case: str | None
    dimensions: DimensionsCode
    sellers: Sequence[Seller]
    price: float | None
    resolved_price: float | None
    minimum_quantity: int
    stock: int
    rated_temperature: MinMax | None = field(
        metadata=config(field_name="rated-temperature")
    )
    # Power dissipation limit as rated by manufacturer. One value, or PWL function (W | [degC, W])
    rated_power: float | None = field(metadata=config(field_name="rated-power"))

    @property
    def x(self) -> float:
        return self.dimensions.x

    @property
    def y(self) -> float:
        return self.dimensions.y

    @property
    def z(self) -> float | None:
        return self.dimensions.z

    @property
    def area(self) -> float:
        return self.dimensions.area


@dataclass(frozen=True)
class CapacitorTemperatureCoefficent:
    code: str
    raw_data: str | None
    lower_temperature: float | None = field(
        metadata=config(field_name="lower-temperature")
    )
    upper_temperature: float | None = field(
        metadata=config(field_name="upper-temperature")
    )


@dataclass_json()
@dataclass(frozen=True)
class CapacitorMetadata:
    description: str | None
    packaging: str | None
    ripple_current_low_frequency: str | None = field(
        metadata=config(field_name="ripple-current-low-frequency")
    )
    ripple_current_high_frequency: str | None = field(
        metadata=config(field_name="ripple-current-high-frequency")
    )
    lifetime_temp: str | None = field(metadata=config(field_name="lifetime-temp"))
    applications: str | None
    lead_spacing: str | None = field(metadata=config(field_name="lead-spacing"))


@dataclass_json()
@dataclass(frozen=True)
class InductorMetadata:
    description: str | None
    packaging: str | None


@dataclass_json()
@dataclass(frozen=True)
class ResistorMetadata:
    description: str | None
    series: str | None
    packaging: str | None
    features: str | None
    supplier_device_package: str | None = field(
        metadata=config(field_name="supplier-device-package")
    )
    number_of_terminations: float | None = field(
        metadata=config(field_name="number-of-terminations")
    )


@dataclass(frozen=True)
class ResistorTCR:
    pos: float
    neg: float
