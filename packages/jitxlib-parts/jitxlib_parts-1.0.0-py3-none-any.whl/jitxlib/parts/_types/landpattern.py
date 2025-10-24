"""ESIR landpattern data"""

from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json, DataClassJsonMixin
from enum import Enum
import dataclasses_json.cfg

from .common import KeyValue


class JitxShape(DataClassJsonMixin):
    pass


# FIXME: not all those shapes have a corresponding class. So they aren't in the actual database?
# FIXME: also Arc isn't actually a first-class shape.
class ShapeByType(str, Enum):
    arc = "arc"
    capsule = "capsule"
    # chamfered_rectangle = "chamfered_rectangle"
    circle = "circle"
    # d_shape = "d_shape"
    difference = "difference"
    # empty = "empty"
    # general_chamfered_rectangle = "general_chamfered_rectangle"
    # general_rounded_rectangle = "general_rounded_rectangle"
    line = "line"
    point = "point"
    polygon = "polygon"
    polygon_with_arcs = "polygon_with_arcs"
    polyline = "polyline"
    rectangle = "rectangle"
    # rounded_rectangle = "rounded_rectangle"
    # segment = "segment"
    text = "text"
    # union = "union"


@dataclass_json
@dataclass(frozen=True)
class Shape[T: JitxShape]:
    type: ShapeByType
    value: T


def shape_decoder(json) -> Shape:
    shape_type = json["type"]
    value_json = json["value"]

    def decode_shape(shape_type, value_json) -> JitxShape:
        if shape_type == ShapeByType.point:
            return Point.from_dict(value_json)
        elif shape_type == ShapeByType.rectangle:
            return Rectangle.from_dict(value_json)
        elif shape_type == ShapeByType.line:
            return Line.from_dict(value_json)
        elif shape_type == ShapeByType.arc:
            return Arc.from_dict(value_json)
        elif shape_type == ShapeByType.polyline:
            return Polyline.from_dict(value_json)
        elif shape_type == ShapeByType.circle:
            return Circle.from_dict(value_json)
        elif shape_type == ShapeByType.capsule:
            return Capsule.from_dict(value_json)
        elif shape_type == ShapeByType.polygon:
            return Polygon.from_dict(value_json)
        elif shape_type == ShapeByType.polygon_with_arcs:
            return Polygon_With_Arcs.from_dict(value_json)
        elif shape_type == ShapeByType.text:
            return Text.from_dict(value_json)
        elif shape_type == ShapeByType.difference:
            return Difference.from_dict(value_json)
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")

    return Shape(shape_type, decode_shape(shape_type, value_json))


dataclasses_json.cfg.global_config.decoders[Shape] = shape_decoder


@dataclass_json
@dataclass(frozen=True, unsafe_hash=True)
class Point(JitxShape):
    x: float
    y: float


@dataclass_json
@dataclass(frozen=True)
class Pose:
    center: Point
    angle: float
    flip_x: bool


@dataclass_json
@dataclass(frozen=True)
class Rectangle(JitxShape):
    width: float
    height: float
    pose: Pose


@dataclass_json
@dataclass(frozen=True)
class Line(JitxShape):
    width: float
    points: tuple[Point, ...]


@dataclass_json
@dataclass(frozen=True)
class Arc(JitxShape):
    center: Point
    radius: float
    start_angle: float
    angle: float


@dataclass_json
@dataclass(frozen=True)
class Polyline(JitxShape):
    width: float
    elements: tuple[Shape[Arc] | Shape[Point], ...] = field(
        metadata=config(decoder=lambda d: tuple(shape_decoder(e) for e in d))
    )


@dataclass_json
@dataclass(frozen=True)
class Circle(JitxShape):
    center: Point
    radius: float


@dataclass_json
@dataclass(frozen=True)
class Capsule(JitxShape):
    width: float
    height: float
    pose: Pose


@dataclass_json
@dataclass(frozen=True)
class Polygon(JitxShape):
    points: tuple[Point, ...]


@dataclass_json
@dataclass(frozen=True)
class Polygon_With_Arcs(JitxShape):
    elements: tuple[Shape[Arc] | Shape[Point], ...] = field(
        metadata=config(decoder=lambda d: tuple(shape_decoder(e) for e in d))
    )


class Anchor(str, Enum):
    W = "W"
    C = "C"
    E = "E"


@dataclass_json
@dataclass(frozen=True)
class Text(JitxShape):
    string: str
    size: float
    anchor: Anchor
    pose: Pose


@dataclass_json
@dataclass(frozen=True)
class Difference(JitxShape):
    shape1: Shape
    shape2: Shape


class JitxPinByType(DataClassJsonMixin):
    pass


@dataclass_json
@dataclass(frozen=False)
class PinByNameCode(JitxPinByType):
    pin_name: str


@dataclass_json
@dataclass(frozen=True)
class PinByBundleCode(JitxPinByType):
    bundle_name: str
    pin_name: str


@dataclass_json
@dataclass(frozen=False)
class PinByIndexCode(JitxPinByType):
    name: str
    index: int


@dataclass_json
@dataclass(frozen=True)
class PinByRequireCode(JitxPinByType):
    bundle_name: str


class PinByType(str, Enum):
    pin_by_name = "pin_by_name"
    pin_by_bundle = "pin_by_bundle"
    pin_by_index = "pin_by_index"
    pin_by_require = "pin_by_require"


@dataclass_json
@dataclass(frozen=False)
class PinByTypeCode[P: JitxPinByType]:
    type: PinByType
    value: P


def pin_by_type_code_decoder(json) -> PinByTypeCode:
    type_json = json["type"]
    value_json = json["value"]

    def decode_pin_by_type(type_json, value_json) -> JitxPinByType:
        if type_json == PinByType.pin_by_name:
            return PinByNameCode.from_dict(value_json)
        elif type_json == PinByType.pin_by_bundle:
            return PinByBundleCode.from_dict(value_json)
        elif type_json == PinByType.pin_by_index:
            return PinByIndexCode.from_dict(value_json)
        elif type_json == PinByType.pin_by_require:
            return PinByRequireCode.from_dict(value_json)
        else:
            raise ValueError(f"Unknown pin by type: {type_json}")

    return PinByTypeCode(type_json, decode_pin_by_type(type_json, value_json))


dataclasses_json.cfg.global_config.decoders[PinByTypeCode] = pin_by_type_code_decoder


class Side(str, Enum):
    Top = "Top"
    Bottom = "Bottom"


@dataclass_json
@dataclass(frozen=True)
class LandPatternPadCode:
    pin: PinByTypeCode
    pcb_pad_name: str
    pose: Pose
    side: Side


#####################################


class PadType(str, Enum):
    SMD = "SMD"
    TH = "TH"


class SolidType(str, Enum):
    SOLID = "solid"
    NONPLATED_THROUGHHOLE = "npth"


class JitxLayer(DataClassJsonMixin):
    pass


@dataclass_json
@dataclass(frozen=True)
class Courtyard(JitxLayer):
    side: Side


@dataclass_json
@dataclass(frozen=True)
class CustomLayer(JitxLayer):
    name: str
    side: Side


# This is a geom, not a layer specifier
# @dataclass_json
# @dataclass(frozen=True)
# class LayerIndex(JitxLayer):
#     index: int
#     side: Side


@dataclass_json
@dataclass(frozen=True)
class Silkscreen(JitxLayer):
    name: str
    side: Side


@dataclass_json
@dataclass(frozen=True)
class Paste(JitxLayer):
    side: Side


@dataclass_json
@dataclass(frozen=True)
class SolderMask(JitxLayer):
    side: Side


@dataclass_json
@dataclass(frozen=True)
class Cutout(JitxLayer):
    pass


# FIXME: glue, finish, forbid_copper, forbid_via, board_edge don't have a corresponding class. So they aren't in the actual database?
class LayerSpecifierByType(str, Enum):
    cutout = "cutout"
    courtyard = "courtyard"
    solder_mask = "solder_mask"
    paste = "paste"
    # glue = "glue"
    # finish = "finish"
    silkscreen = "silkscreen"
    # forbid_copper = "forbid_copper"
    # forbid_via = "forbid_via"
    # board_edge = "board_edge"
    custom_layer = "custom_layer"


@dataclass_json
@dataclass(frozen=True)
class LayerSpecifier[L: JitxLayer]:
    type: LayerSpecifierByType
    value: L  # Compared to db population script: added Courtyard, removedLayerIndex


def layer_specifier_decoder(json) -> LayerSpecifier:
    layer_type = json["type"]
    value_json = json["value"]

    def decode_layer_specifier(layer_type, value_json) -> JitxLayer:
        if layer_type == LayerSpecifierByType.cutout:
            return Cutout.from_dict(value_json)
        elif layer_type == LayerSpecifierByType.courtyard:
            return Courtyard.from_dict(value_json)
        elif layer_type == LayerSpecifierByType.solder_mask:
            return SolderMask.from_dict(value_json)
        elif layer_type == LayerSpecifierByType.paste:
            return Paste.from_dict(value_json)
        elif layer_type == LayerSpecifierByType.silkscreen:
            return Silkscreen.from_dict(value_json)
        elif layer_type == LayerSpecifierByType.custom_layer:
            return CustomLayer.from_dict(value_json)
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

    return LayerSpecifier(layer_type, decode_layer_specifier(layer_type, value_json))


dataclasses_json.cfg.global_config.decoders[LayerSpecifier] = layer_specifier_decoder


@dataclass_json
@dataclass(frozen=True)
class PCBLayerCode:
    layer_specifier: LayerSpecifier
    shape: Shape


@dataclass_json
@dataclass(frozen=True)
class PCBPadCode:
    name: str
    type: PadType
    shape: Shape
    layers: tuple[PCBLayerCode, ...]


@dataclass_json
@dataclass(frozen=True)
class Vector3D:
    x: float
    y: float
    z: float


@dataclass_json
@dataclass(frozen=False)
class Model3D:
    jitx_model_3d_id: str
    comment: str
    filename: str
    position: Vector3D
    scale: Vector3D
    rotation: Vector3D
    properties: tuple[KeyValue, ...]


@dataclass_json
@dataclass(frozen=True)
class PCBLayerReference:
    layer_specifier: LayerSpecifier
    text: Text


@dataclass_json
@dataclass(frozen=True)
class PCBLayerValue:
    layer_specifier: LayerSpecifier
    text: Text


@dataclass_json
@dataclass(frozen=True)
class LandPatternCode:
    name: str
    pads: tuple[LandPatternPadCode, ...]
    pcb_layer_reference: PCBLayerReference
    pcb_layer_value: PCBLayerValue
    layers: tuple[PCBLayerCode, ...]
    # TODO: Model geometries and populate
    # geometries: Tuple[GeomCode]
    geometries: tuple[object, ...]  # FIXME: object isn't good enough typing!
    model3ds: tuple[Model3D, ...]


# Shape type aliases
PointShape = Shape[Point]
RectangleShape = Shape[Rectangle]
LineShape = Shape[Line]
ArcShape = Shape[Arc]
PolylineShape = Shape[Polyline]
CircleShape = Shape[Circle]
CapsuleShape = Shape[Capsule]
PolygonShape = Shape[Polygon]
PolygonWithArcsShape = Shape[Polygon_With_Arcs]
TextShape = Shape[Text]
DifferenceShape = Shape[Difference]

# Any shape type
AnyShape = Shape[
    Point
    | Rectangle
    | Line
    | Arc
    | Polyline
    | Circle
    | Capsule
    | Polygon
    | Polygon_With_Arcs
    | Text
    | Difference
]
