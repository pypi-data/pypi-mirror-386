import ast
from collections import defaultdict
from enum import Enum
import logging
from typing import (
    Any,
)
from dataclasses import dataclass
from collections.abc import Sequence, Mapping
from ._types.common import KeyValue
from ._sanitize import (
    sanitize_defpad,
    sanitize_pin,
    python_landpattern_name,
    python_symbol_name,
    python_component_name,
)
from ._types.landpattern import (
    PCBLayerCode,
    PCBLayerReference,
    PCBLayerValue,
    PCBPadCode,
    LandPatternPadCode,
    LandPatternCode,
    PinByTypeCode,
    PinByType,
    Side,
    ShapeByType,
    Model3D,
    Vector3D,
    Shape,
    Point,
    Pose,
    Text,
    Line,
    Arc,
    Circle,
    Polygon,
    Polyline,
    Rectangle,
    Capsule,
    Polygon_With_Arcs,
    Difference,
    LayerSpecifierByType,
)
from ._types.component import (
    ComponentCode,
    SymbolCode,
    PinPropertyCode,
    SymbolPinCode,
    ResistorEModel,
    CapacitorEModel,
    InductorEModel,
)

logger = logging.getLogger(__name__)

# exit_when_error = False # => so output_part.py is produced, even with bad shape
exit_when_error = True  # => exit with the first error
conversion_error_count = 0


class StdLibSymbolType(Enum):
    Resistor = "Resistor"
    Capacitor = "Capacitor"
    PolarizedCapacitor = "PolarizedCapacitor"
    Inductor = "Inductor"


# Handle Error when the conversion for 'target_type' from 'code' failed
# Return str with error message
def handle_conversion_error_message(e: Exception, target_type: str, code: Any) -> str:
    global conversion_error_count
    conversion_error_count += 1
    if exit_when_error:
        raise RuntimeError(f"WARNING: Failed to convert {target_type} ({e}): {code}")
    else:
        logger.error(f"WARNING: Failed to convert {target_type} ({e}): {code}")
        return f"<bad {target_type}: {e}>"


# Return a safe ast.expr so the conversion process can continue.
def handle_conversion_error(e: Exception, target_type: str, code: Any) -> ast.expr:
    message = handle_conversion_error_message(e, target_type, code)
    fallback_expr = ast.Constant(message)
    return fallback_expr


# ================ Rounding and Grid Scale ================
# Round to 5 digits after the decimal point
# - return integer (without ".0") if an integer
def round5(value: float) -> float | int:
    rounded = round(value, 5)
    if int(rounded) == rounded:
        return int(rounded)  # remove ".0" for an integer
    else:
        return rounded


# Round to 5 digits after the decimal point and
# normalize an angle to the range [0, 360).
# NOTE: Similar behavior as normalize-angle() in jitpcb/src/jitpcb/code-generator/api.stanza
def angle_round5(angle: float) -> float | int:
    return round5(angle % 360)


SYMBOL_GRID_UNIT = 1.27


def to_grid_int(value: float) -> int:
    return int(round5(value / SYMBOL_GRID_UNIT))


def to_grid_scale(value: float) -> float | int:
    return round5(value / SYMBOL_GRID_UNIT)


def grid_scale(value: float, use_gs: bool) -> float | int:
    if use_gs:
        return to_grid_scale(value)
    else:
        return round5(value)


# ================ Utilities to simplify AST creation ================
#     Functions: to_ast_expr, to_ast_call, to_ast_assign etc.
# ====================================================================
RHSCodeItem = (
    Shape
    | Text
    | PCBLayerCode
    | PCBLayerReference
    | PCBLayerValue
    | LandPatternPadCode
    | SymbolPinCode
    | Model3D
)
ExprItem = RHSCodeItem | Point | Side | float | int | str


# NOTE: For these AST conversion functions, list would get converted to ast.List, dict to ast.Dict and
#       tuple to ast.Tuple. So, Sequence is intentionally not used here.
def to_ast_expr(
    value: ast.expr
    | list[ExprItem]
    | dict[str | int, ExprItem]
    | tuple[ExprItem, ...]
    | ExprItem,
    use_gs: bool = False,
) -> ast.expr:
    if isinstance(value, ast.expr):
        return value
    elif isinstance(value, list):
        elts = [to_ast_expr(v, use_gs) for v in value]
        return ast.List(elts=elts, ctx=ast.Load())
    elif isinstance(value, dict):
        return ast.Dict(
            keys=[to_ast_expr(k) for k in value.keys()],
            values=[to_ast_expr(v, use_gs) for v in value.values()],
        )
    elif isinstance(value, tuple):
        elts = [to_ast_expr(v, use_gs) for v in value]
        return ast.Tuple(elts=elts, ctx=ast.Load())
    elif isinstance(value, Shape):
        return convert_shape_to_ast_expr(value, use_gs)
    elif isinstance(value, Point):
        return convert_point_to_ast_expr(value, use_gs)
    elif isinstance(value, Text):
        return convert_text_to_ast_expr(value, use_gs)
    elif isinstance(value, Side):
        # isinstance(value, str) = true on the enum. So, 'str' must be checked after checking Side.
        return convert_side_to_ast_expr(value)
    elif isinstance(value, (str, int, float, bool, type(None))):
        return ast.Constant(value=value)
    elif isinstance(value, PCBLayerCode):
        return convert_layer_to_ast_expr(value)
    elif isinstance(value, PCBLayerReference | PCBLayerValue):
        return convert_layer_reference_to_ast_expr(value)
    elif isinstance(value, LandPatternPadCode):
        return convert_lp_pad_to_ast_expr(value)
    elif isinstance(value, SymbolPinCode):
        return convert_symbol_pin_code_to_ast_expr(value)
    elif isinstance(value, Model3D):
        return convert_model3d_to_ast_expr(value)


def to_ast_name(identifier: str) -> ast.Name:
    """Create an AST Name node from a string identifier."""
    return ast.Name(id=identifier, ctx=ast.Load())


def to_ast_attribute(value: ast.expr | str, attr: str) -> ast.Attribute:
    """Create an AST Attribute node from a value expr and an attribute name."""
    if isinstance(value, str):
        value = to_ast_name(value)
    return ast.Attribute(value=value, attr=attr, ctx=ast.Load())


def to_ast_subscript(
    value_expr: ast.expr | str, slice_expr: ast.expr | str | int
) -> ast.Subscript:
    """Create an AST Subscript node from a value expr and a slice expr."""
    if isinstance(value_expr, str):
        value_expr = to_ast_name(value_expr)
    if not isinstance(slice_expr, ast.expr):
        slice_expr = to_ast_expr(slice_expr)
    return ast.Subscript(value=value_expr, slice=slice_expr, ctx=ast.Load())


# func(args1, args2, key1=value1, key2=value2)
def to_ast_call(
    func: str | ast.expr,
    args: list[ast.expr | ExprItem] | None = None,
    keywords: list[tuple[str, Any]] | list[ast.keyword] | None = None,
) -> ast.Call:
    if keywords is None:
        keywords = []
    if args is None:
        args = []
    arg_keywords = []
    for item in keywords:
        if isinstance(item, ast.keyword):
            arg_keywords.append(item)
        elif isinstance(item, tuple) and len(item) == 2:
            key, value = item
            arg_keywords.append(ast.keyword(arg=key, value=to_ast_expr(value)))
        else:
            raise TypeError(f"Invalid keyword argument: {item}")
    if isinstance(func, str):
        func = to_ast_name(func)
    return ast.Call(
        func=func,
        args=[to_ast_expr(arg) for arg in args],
        keywords=arg_keywords,
    )


# lhs = rhs
def to_ast_assign(
    lhs: str,
    rhs: ast.expr | list[Any] | dict[str | int, Any] | RHSCodeItem | float | int | str,
    use_gs: bool = False,
) -> ast.Assign:
    target = ast.Name(id=lhs, ctx=ast.Store())
    return ast.Assign(targets=[target], value=to_ast_expr(rhs, use_gs))


# ============== Utilities to convert code items to AST ==============
#     Functions: convert_shape_to_ast_expr, convert_layert_to_ast_expr etc.
# ====================================================================
def convert_point_to_ast_expr(p: Point, use_gs: bool = False) -> ast.expr:
    # (10.0, 3.0)
    px = grid_scale(p.x, use_gs)
    py = grid_scale(p.y, use_gs)
    return to_ast_expr((px, py))


def convert_arc_to_ast_expr(arc: Arc, use_gs: bool) -> ast.expr:
    return to_ast_call(
        "Arc",
        args=[
            convert_point_to_ast_expr(arc.center, use_gs),
            ast.Constant(grid_scale(arc.radius, use_gs)),
            ast.Constant(angle_round5(arc.start_angle)),
            # not normalize the sweep angle ('arc'), which should be in range -360 to 360
            ast.Constant(round5(arc.angle)),
        ],
    )


def no_pose(pose: Pose) -> bool:
    return pose == Pose(center=Point(x=0.0, y=0.0), angle=0.0, flip_x=False)


def convert_pose_to_ast_expr(
    pose: Pose, use_gs: bool, must_transform: bool = False
) -> ast.expr:
    """
    If pose is non-identity (angle ≠ 0 or flip_x), generate:
        Transform((x, y), angle, (-1, 1))
    Otherwise, return:
        (x, y) when not must_transform else Transform((x,y))

    Usage: when used for composite shapes, must_transform = True
    """
    x = grid_scale(pose.center.x, use_gs)
    y = grid_scale(pose.center.y, use_gs)
    args = [(x, y), angle_round5(pose.angle)]
    if pose.flip_x:
        args.append((-1, 1))

    if must_transform or pose.angle != 0.0 or pose.flip_x:
        return to_ast_call("Transform", args=args)
    else:
        return convert_point_to_ast_expr(pose.center, use_gs)


# convert_rectangle or convert_capsule
def convert_composite_to_ast_expr(shape: Capsule | Rectangle, use_gs: bool) -> ast.expr:
    # composite shape with transformation:
    #     Transform((0.0, 0.0), 90.0) * capsule(2.0, 1.0, anchor=Anchor.SE)
    #     Transform((-1.000, -1.000)) * rectangle(18.000, 26.000)
    composite_name = "capsule" if shape is Capsule else "rectangle"
    try:
        shape_call = to_ast_call(
            composite_name,
            args=[
                to_ast_expr(grid_scale(shape.width, use_gs)),
                to_ast_expr(grid_scale(shape.height, use_gs)),
            ],
            # anchor - not supported yet?
            # keywords=[
            #    ast.keyword(
            #        arg="anchor",
            #        value=to_ast_attribute(value="Anchor", attr=shape.anchor.name)
            #    )
            # ]
        )
        if no_pose(shape.pose):
            shape_expr = shape_call
        else:
            # Transform(...) call
            transform_call = convert_pose_to_ast_expr(
                shape.pose, use_gs, must_transform=True
            )
            # Transform(...) * capsule(...)
            shape_expr = ast.BinOp(left=transform_call, op=ast.Mult(), right=shape_call)
    except Exception as e:
        shape_expr = handle_conversion_error(
            e, "composite shape " + composite_name, shape
        )

    return shape_expr


def convert_capsule_to_ast_expr(shape: Capsule | Rectangle, use_gs: bool) -> ast.expr:
    # Circle(radius=1).at(1.0, 0.0) when width == height
    # else use composite shape
    #     Transform(%,%,%) * capsule(2.0, 1.0, anchor=Anchor.SE)
    if shape.width == shape.height:
        shape_expr = convert_circle_to_ast_expr(
            Circle(shape.pose.center, shape.width), use_gs
        )
    else:
        shape_expr = convert_composite_to_ast_expr(shape, use_gs)
    return shape_expr


def convert_circle_to_ast_expr(shape: Circle, use_gs: bool) -> ast.expr:
    # Circle(radius=1).at(1.0, 0.0)
    try:
        circle_call = to_ast_call(
            "Circle",
            args=[],
            keywords=[("radius", ast.Constant(grid_scale(shape.radius, use_gs)))],
        )
        # the Circle(...).at call
        shape_expr = to_ast_call(
            to_ast_attribute(value=circle_call, attr="at"),
            args=[to_ast_expr(shape.center, use_gs)],
        )
    except Exception as e:
        shape_expr = handle_conversion_error(e, "circle", shape)
    return shape_expr


def convert_polygon_polyline_to_ast_expr(
    shape: Line | Polygon | Polyline | Polygon_With_Arcs, use_gs: bool
) -> ast.expr:
    try:
        args = []
        if isinstance(shape, Line):
            elements = shape.points
            args.append(ast.Constant(round5(shape.width)))
        elif isinstance(shape, Polygon):
            elements = shape.points
        elif isinstance(shape, Polyline):
            elements = [elem.value for elem in shape.elements]
            args.append(ast.Constant(round5(shape.width)))
        elif isinstance(shape, Polygon_With_Arcs):
            elements = [elem.value for elem in shape.elements]
        has_arcs = any(isinstance(elem, Arc) for elem in elements)
        has_width = len(args) == 1
        converted_elements = [
            convert_arc_to_ast_expr(elem, use_gs)
            if isinstance(elem, Arc)
            else convert_point_to_ast_expr(elem, use_gs)
            for elem in elements
        ]
        args.append(ast.List(elts=converted_elements, ctx=ast.Load()))
        if has_width and has_arcs:
            func_name = "ArcPolyline"
        elif has_width and not has_arcs:
            func_name = "Polyline"
        elif not has_width and has_arcs:
            func_name = "ArcPolygon"
        elif not has_width and not has_arcs:
            func_name = "Polygon"
        shape_expr = to_ast_call(func_name, args=args)
    except Exception as e:
        shape_expr = handle_conversion_error(e, "polygon_polyline", shape)
    return shape_expr


def convert_text_to_ast_expr(shape: Text, use_gs: bool) -> ast.expr:
    # Text("Hello, world!", 1, Anchor.C).at((0, -5))
    try:
        text_call = to_ast_call(
            "Text",
            args=[
                ast.Constant(shape.string),
                ast.Constant(grid_scale(shape.size, use_gs)),
                to_ast_attribute(value="Anchor", attr=shape.anchor.name),
            ],
        )
        # the Text(...).at(...) call
        shape_expr = to_ast_call(
            to_ast_attribute(value=text_call, attr="at"),
            args=[convert_point_to_ast_expr(shape.pose.center, use_gs)],
        )
    except Exception as e:
        shape_expr = handle_conversion_error(e, "text", shape)
    return shape_expr


def convert_shape_to_ast_expr(shape: Shape, use_gs: bool = False) -> ast.expr:
    try:
        val = shape.value
        if isinstance(val, Text):
            # when the shape is for reference or layer
            shape_expr = convert_text_to_ast_expr(val, use_gs)
        elif isinstance(val, Capsule):
            shape_expr = convert_capsule_to_ast_expr(val, use_gs)
        elif isinstance(val, Circle):
            shape_expr = convert_circle_to_ast_expr(val, use_gs)
        elif isinstance(val, (Line, Polygon, Polyline, Polygon_With_Arcs)):
            shape_expr = convert_polygon_polyline_to_ast_expr(val, use_gs)
        elif isinstance(val, Rectangle):
            # shape =  Shape(type='rectangle', value=Rectangle(width=0.22, height=0.10605551275463987,
            #     pose=Pose(center=Point(x=0.0, y=0.0), angle=0.0, flip_x=False)))
            shape_expr = convert_composite_to_ast_expr(val, use_gs)
        elif isinstance(val, Difference):
            raise ValueError("Difference shapes are not supported")
        else:
            raise ValueError(f"Unsupported shape: shape {type(shape)} val {type(val)}")
    except Exception as e:
        shape_expr = handle_conversion_error(e, "shape", shape)
    return shape_expr


# ===============


def convert_layer_to_ast_expr(layer: PCBLayerCode) -> ast.expr:
    """
    Convert a PCBLayerCode object into an AST expression that reconstructs it as
    a Feature call like:
    ```
    Soldermask(shape=..., side=Side.Bottom)
    Cutout(shape=...)
    Custom(shape=..., name="...", side=Side.Bottom)
    ```
    """
    try:
        spec_type = layer.layer_specifier.type
        spec_value = layer.layer_specifier.value

        # layers with "side"
        layer_class = {
            LayerSpecifierByType.cutout: "Cutout",
            LayerSpecifierByType.courtyard: "Courtyard",
            LayerSpecifierByType.silkscreen: "Silkscreen",
            LayerSpecifierByType.solder_mask: "Soldermask",
            LayerSpecifierByType.paste: "Paste",
        }

        # Build AST for the feature constructor
        # Layer with only shape
        if spec_type == LayerSpecifierByType.cutout:
            call_expr = to_ast_call("Cutout", args=[layer.shape])
        # layers with "side" in layer_class
        elif spec_type in layer_class:
            side_is_top = spec_value.side.name == "Top"
            keywords = []
            if not side_is_top:
                keywords = [("side", spec_value.side)]
            call_expr = to_ast_call(
                layer_class[spec_type], args=[layer.shape], keywords=keywords
            )
        elif spec_type == LayerSpecifierByType.custom_layer:
            keywords = [("name", spec_value.name)]
            side_is_top = spec_value.side.name == "Top"
            if not side_is_top:
                keywords.append(("side", spec_value.side))
            call_expr = to_ast_call("Custom", args=[layer.shape], keywords=keywords)
        else:
            # Layers not handled: Glue, Finish, forbid_copper, forbid_via, board_edge
            raise ValueError(f"Unsupported layer type: {spec_type}")
    except Exception as e:
        call_expr = handle_conversion_error(e, "layer", layer)
    return call_expr


def convert_layer_reference_to_ast_expr(
    ref_layer: PCBLayerReference | PCBLayerValue,
) -> ast.expr:
    layer_code = PCBLayerCode(
        layer_specifier=ref_layer.layer_specifier,
        shape=Shape(ShapeByType.text, value=ref_layer.text),
    )
    return convert_layer_to_ast_expr(layer_code)


# ======== Utilities to convert elements in landpattern to AST ========
#     Functions: convert_pad_to_ast_module, convert_lp_pad_to_ast_expr
#     convert_landpattern_to_ast_module etc.
# ======================================================================
def convert_pad_to_ast_module(
    pad: PCBPadCode, class_name: str = "QueryPad"
) -> ast.Module:
    """
    Convert a PCBPadCode object to an ast.Module that defines a QueryPad class.
    Assumes:
    - convert_shape_to_ast_expr(pad.shape) returns an ast.expr for Shape(...)
    - convert_layer_to_ast_expr(layer: PCBLayerCode) returns an ast.expr
    """
    class_body = []

    # shape = Shape(...)
    class_body.append(to_ast_assign("shape", pad.shape))

    # Group layers by type
    # [code] silkscreen = [Silkscreen(...), ...]
    grouped_layers = defaultdict(list)
    for layer in pad.layers:
        spec_type = layer.layer_specifier.type
        grouped_layers[spec_type].append(layer)
    for layer_type in grouped_layers.keys():
        class_body.append(to_ast_assign(layer_type, grouped_layers[layer_type]))

    # Build the class definition
    class_def = ast.ClassDef(
        name=class_name,
        bases=[to_ast_name("Pad")],
        keywords=[],
        body=class_body,
        decorator_list=[],
        type_params=[],
    )

    return ast.Module(body=[class_def], type_ignores=[])


# Convert Side enum Side.Bottom
def convert_side_to_ast_expr(side: Side) -> ast.expr:
    return to_ast_attribute(value="Side", attr=side.name)


def convert_lp_pad_to_ast_expr(pad: LandPatternPadCode) -> ast.expr:
    """
    Convert LandPatternPadCode into AST expression like:
        RectThPad().at((x, y), on=Side.Top)
        or:
        RectThPad().at(Transform((x, y), angle, scale), on=Side.Top)
    Args:
        pad: the pad object
        pad_class: name of the pad class, e.g., "RectThPad"
        use_gs: whether to apply grid scaling
    Returns:
        ast.Call expression for `.at(...)` call
    Note: pad.pin already sanitized in convert_grouped... before calling
    """

    # Convert pose to (x, y) or Transform(...)
    position_expr = convert_pose_to_ast_expr(pad.pose, use_gs=False)

    side_is_top = pad.side.name == "Top"
    keywords = []
    if not side_is_top:
        keywords = [("on", pad.side)]

    # RectangleSmdPad().at(...) call
    return to_ast_call(
        to_ast_attribute(
            value=to_ast_call(pad.pcb_pad_name, args=[], keywords=[]), attr="at"
        ),
        args=[position_expr],
        keywords=keywords,
    )


# ==== Model3D ====
def convert_keyvalue_to_ast_expr(keyvalue: KeyValue) -> ast.expr:
    """
    Convert a KeyValue object into an AST expression like:

        KeyValue(key, value)

    Assumes `keyvalue.key` is a string and `keyvalue.value` is JSON-serializable.
    """
    try:
        expr = to_ast_call("KeyValue", args=[keyvalue.key, keyvalue.value])
    except Exception as e:
        expr = handle_conversion_error(e, "KeyValue", keyvalue)
    return expr


def convert_model3d_to_ast_expr(model: Model3D) -> ast.expr:
    """
    model3d = [
        Model3D("../../3d-models/DSUB-25_Female_Horizontal_P2.77x2.84mm_EdgePinOffset9.90mm_Housed_MountingHolesOffset11.32mm.wrl",
            position=(0, 0, 0),
            scale=(1, 1, 1),
            rotation=(0, 0, 0),
    ])
    """

    def convert_vector3d_to_ast_expr(v: Vector3D) -> ast.expr:
        return ast.Tuple(
            elts=[ast.Constant(v.x), ast.Constant(v.y), ast.Constant(v.z)],
            ctx=ast.Load(),
        )

    try:
        # prop_exprs = [convert_keyvalue_to_ast_expr(p) for p in model.properties]
        model_expr = to_ast_call(
            "Model3D",
            args=[model.filename],
            keywords=[
                # Skip fields not exist in jitx.model3d.Model3D
                # ("jitx_model_3d_id", model.jitx_model_3d_id),
                # ("comment", model.comment),
                ("position", convert_vector3d_to_ast_expr(model.position)),
                ("scale", convert_vector3d_to_ast_expr(model.scale)),
                ("rotation", convert_vector3d_to_ast_expr(model.rotation)),
                # TMP: skip properties for now
                # ("properties", prop_exprs)
            ],
        )
    except Exception as e:
        model_expr = handle_conversion_error(e, "Model3D", model)
    return model_expr


# ============ Utilities to handle pin/pad names ============
#     Functions: convert_pin_code_to_ast_expr etc.
#        - to support both landpattern, symbol and component code generation
# =================================================================
# ==== pin name: PinByTypeCode =======
def convert_pin_code_to_str(pin: PinByTypeCode) -> str:
    """
    Convert a PinByTypeCode into a string that represents the pin name
    according to its type:

    - PinByNameCode("p0")           → "GND"
    - PinByBundleCode("VCC", "1")   → "VCC.1"
    - PinByIndexCode("D", 3)        → "D[3]"
    - PinByRequireCode("GND")       → "GND"
    """
    try:
        pin_type = pin.type
        val = pin.value
        if pin_type == PinByType.pin_by_name:  # "GND"
            pin_str = val.pin_name
        elif pin_type == PinByType.pin_by_bundle:  # "A.B"
            pin_str = f"{val.bundle_name}.{val.pin_name}"
        elif pin_type == PinByType.pin_by_index:  # "p[1]"
            pin_str = f"{val.name}[{val.index}]"
        elif pin_type == PinByType.pin_by_require:  # "GND"
            pin_str = val.bundle_name
        else:
            raise ValueError(f"Unsupported PinByType: {pin_type}")
    except Exception as e:
        pin_str = handle_conversion_error_message(e, "PinByType", pin)
    return pin_str


def parse_name_to_ast_target(name: str) -> ast.expr:
    """
    Convert a name like 'GND', 'p[0]', 'A.B', or 'A.B.C' into an AST expression:
    - 'GND'    → ast.Name
    - 'p[0]'   → ast.Subscript
    - 'A.B.C'  → ast.Attribute(Attribute(Name('A'), 'B'), 'C')

    Returns:
        ast.expr suitable for use as assignment target.
    """
    if "[" in name and name.endswith("]"):
        var, index = name[:-1].split("[")
        return to_ast_subscript(var, index)
    elif "." in name:
        parts = name.split(".")
        for attr in parts[1:]:
            base = to_ast_attribute(value=parts[0], attr=attr)
        base.ctx = ast.Store()
        return base
    else:
        return to_ast_name(name)


def convert_pin_code_to_ast_expr(
    pin: PinByTypeCode,
    source_obj: str | None = None,
    bank: int | str | None = None,
) -> ast.expr:
    """
    Build AST expression to access a pin inside symbol["bank"],
    e.g.,
    symbol[1].D[3], symbol[1].A.B, symbol[1].GND
    symbol["A"].D[3], symbol["A"].A.B, symbol["A"].GND

    If source_obj is None, returns D[3], A.B, GND etc directly.
    Otherwise, if bank is None, return source_obj.D[3], source_obj.A.B, source_obj.GND.
    """
    pin = sanitize_pin(pin)
    # Build prefix expression
    if source_obj:
        prefix_expr = (
            to_ast_subscript(source_obj, bank)
            if bank is not None
            else to_ast_name(source_obj)
        )
    else:
        prefix_expr = None

    # Construct full access expression
    if pin.type == PinByType.pin_by_index:
        value_expr = (
            to_ast_attribute(value=prefix_expr, attr=pin.value.name)
            if prefix_expr
            else to_ast_name(pin.value.name)
        )

        return to_ast_subscript(value_expr, pin.value.index)

    elif pin.type == PinByType.pin_by_bundle:
        bundle_expr = (
            to_ast_attribute(value=prefix_expr, attr=pin.value.bundle_name)
            if prefix_expr
            else to_ast_name(pin.value.bundle_name)
        )

        return to_ast_attribute(value=bundle_expr, attr=pin.value.pin_name)

    elif pin.type == PinByType.pin_by_name:
        return (
            to_ast_attribute(value=prefix_expr, attr=pin.value.pin_name)
            if prefix_expr
            else to_ast_name(pin.value.pin_name)
        )

    elif pin.type == PinByType.pin_by_require:
        return (
            to_ast_attribute(value=prefix_expr, attr=pin.value.bundle_name)
            if prefix_expr
            else to_ast_name(pin.value.bundle_name)
        )

    else:
        raise ValueError(f"Unsupported pin type: {pin.type}")


def prepend_source_to_expr(expr: ast.expr, source_obj: str) -> ast.expr:
    """
    Recursively prepend `source_obj.` to a given AST expr.
    Examples: source_obj = "symbol"
    D[3]        → symbol.D[3]
    A.B         → symbol.A.B
    GND         → symbol.GND
    """
    if isinstance(expr, ast.Subscript):
        # e.g. D[3] => symbol.D[3]
        return to_ast_subscript(
            prepend_source_to_expr(expr.value, source_obj), expr.slice
        )
    elif isinstance(expr, ast.Attribute):
        # e.g. A.B => symbol.A.B
        expr_root = expr
        while isinstance(expr_root.value, ast.Attribute):
            expr_root = expr_root.value
        expr_root.value = to_ast_name(source_obj)
        return expr
    elif isinstance(expr, ast.Name):
        # e.g. GND => symbol.GND
        return to_ast_attribute(source_obj, attr=expr.id)
    else:
        raise TypeError(f"Unsupported AST type for source prepend: {type(expr)}")


# ============ Utilities to convert landpattern to AST ============
#     Functions: convert_landpattern_to_ast_module etc.
# =================================================================
# ==== Landpattern: group pads ====
def convert_grouped_landpattern_pads_to_ast_stmts(
    pads: Sequence[LandPatternPadCode],
) -> Sequence[ast.stmt]:
    def sanitize_lp_pad(pad: LandPatternPadCode):
        return LandPatternPadCode(
            sanitize_pin(pad.pin),
            sanitize_defpad(pad.pcb_pad_name),  # e.g., "RectSmdPad_1"
            pad.pose,
            pad.side,
        )

    # Sort by pad names
    sorted_sanitized_pads = sorted(
        [sanitize_lp_pad(pad) for pad in pads],
        key=lambda pad: convert_pin_code_to_str(pad.pin),
    )

    grouped_index = defaultdict(list)
    grouped_bundle = []
    standalone = []

    # Group pads
    for pad in sorted_sanitized_pads:
        pin_type = pad.pin.type
        val = pad.pin.value

        if pin_type == PinByType.pin_by_index:
            grouped_index[val.name].append(pad)
        elif pin_type == PinByType.pin_by_bundle:
            grouped_bundle.append(pad)
        else:
            standalone.append(pad)

    stmts = []
    # 1. Emit index-based grouped dicts
    for name, group in grouped_index.items():
        group = sorted(group, key=lambda pad: pad.pin.value.index)
        dict_expr = {pad.pin.value.index: pad for pad in group}
        stmts.append(to_ast_assign(name, dict_expr))

    # 2. Emit bundle-based grouped dicts
    for pad in grouped_bundle:
        val = pad.pin.value
        pad_name = f"{val.bundle_name}_{val.pin_name}"
        stmts.append(to_ast_assign(pad_name, pad))

    # 3. Emit individual assignments
    for pad in standalone:
        pad_name = convert_pin_code_to_str(pad.pin)
        stmts.append(to_ast_assign(pad_name, pad))
    return stmts


def convert_landpattern_to_ast_module(
    landpattern: LandPatternCode,
    class_name: str = "QueryLandpattern",
    missing_3d_models: tuple[str, ...] = (),
) -> ast.Module:
    """
    Convert a LandPatternCode instance into an AST module defining the class `class_name`.
    """
    class_body = []

    # name = "LP_3216"
    class_body.append(to_ast_assign("name", landpattern.name))

    # pads = [ ... ]
    pads_expr = convert_grouped_landpattern_pads_to_ast_stmts(landpattern.pads)
    class_body.extend(pads_expr)

    # pcb_layer_reference = PCBLayerReference(...)
    class_body.append(
        to_ast_assign("pcb_layer_reference", landpattern.pcb_layer_reference)
    )

    # pcb_layer_value = PCBLayerValue(...)
    class_body.append(to_ast_assign("pcb_layer_value", landpattern.pcb_layer_value))

    # Group layers by type
    # [code] silkscreen = [Silkscreen(...), ...]
    grouped_layers = defaultdict(list)
    for layer in landpattern.layers:
        spec_type = layer.layer_specifier.type
        grouped_layers[spec_type].append(layer)
    for layer_type in grouped_layers.keys():
        class_body.append(to_ast_assign(layer_type, grouped_layers[layer_type]))

    # geometries = [convert_shape_to_ast_expr(...) for ...]
    # class_body.append(ast.Assign("geometries",
    #                              [convert_shape_to_ast_expr(g.shape) for g in landpattern.geometries]))

    # model3ds = [Constant("...")] or fallback
    if landpattern.model3ds:
        filtered_model3ds = [
            m
            for m in landpattern.model3ds
            if getattr(m, "jitx_model_3d_id", None) not in missing_3d_models
        ]

        class_body.append(to_ast_assign("model3ds", list(filtered_model3ds)))

    # Final class definition
    class_def = ast.ClassDef(
        name=class_name,
        bases=[to_ast_name("Landpattern")],
        keywords=[],
        body=class_body,
        decorator_list=[],
        type_params=[],
    )

    return ast.Module(body=[class_def], type_ignores=[])


# ============ Utilities to convert symbol to AST ============
#     Functions: convert_symbol_to_ast_module etc.
# =============================================================
# ==== functions for Symbol: SymbolPinCode, grouped pins ====


def convert_symbol_pin_code_to_ast_expr(pin: SymbolPinCode) -> ast.expr:
    """
    Convert SymbolPinCode to an AST Call expression like:
    Pin(at=(x, y), length=n, direction=Direction.Left, pad_name_size=..., pin_name_size=...)
    All coordinates and lengths are scaled by 1.27 and rounded to integers.
    Note: pin.pin is already sanitized in convert_grouped...
    """
    args = [
        Point(to_grid_int(pin.point.x), to_grid_int(pin.point.y)),
        to_grid_int(pin.length),
        to_ast_attribute(value="Direction", attr=pin.direction.name),
    ]
    keywords = []
    if pin.number_size:
        keywords.append(("pad_name_size", to_grid_scale(pin.number_size)))
    if pin.name_size:
        keywords.append(("pin_name_size", to_grid_scale(pin.name_size)))
    return to_ast_call("Pin", args=args, keywords=keywords)


def find_default_name_sizes_and_sanitize_pins(
    pins: Sequence[SymbolPinCode],
) -> tuple[Sequence[SymbolPinCode], float | None, float | None]:
    pin_size_table: Mapping[float | None, list[SymbolPinCode]] = defaultdict(list)
    pad_size_table: Mapping[float | None, list[SymbolPinCode]] = defaultdict(list)

    for pin in pins:
        pin_size_table[pin.name_size].append(pin)
        pad_size_table[pin.number_size].append(pin)

    def use_default_size(
        size_table: Mapping[float | None, Sequence[SymbolPinCode]],
    ) -> float | None:
        if None in size_table:  # default size already used
            return None
        elif len(size_table) == 1:
            return next(iter(size_table.keys()))
        else:
            # Find the size used most often
            size_counts = {k: len(v) for k, v in size_table.items()}
            max_count = max(size_counts.values())
            total_count = sum(size_counts.values())
            if max_count / total_count >= 0.8:
                # Return the most-used size
                for k, v in size_table.items():
                    if len(v) == max_count:
                        return k
            return None

    pin_name_size_default = use_default_size(pin_size_table)
    pad_number_size_default = use_default_size(pad_size_table)
    sanitized_updated_pins = []
    for pin in pins:
        name_size = (
            None
            if (
                pin_name_size_default is not None
                and pin.name_size == pin_name_size_default
            )
            else pin.name_size
        )

        number_size = (
            None
            if (
                pad_number_size_default is not None
                and pin.number_size == pad_number_size_default
            )
            else pin.number_size
        )

        updated_pin = SymbolPinCode(
            pin=sanitize_pin(pin.pin),
            point=pin.point,
            direction=pin.direction,
            length=pin.length,
            name_size=name_size,
            number_size=number_size,
        )
        sanitized_updated_pins.append(updated_pin)
    return sanitized_updated_pins, pin_name_size_default, pad_number_size_default


def convert_grouped_symbol_pins_to_ast_stmts(
    pins: Sequence[SymbolPinCode],
) -> Sequence[ast.stmt]:
    stmts = []

    sanitized_updated_pins, default_pin_name_size, default_pad_name_size = (
        find_default_name_sizes_and_sanitize_pins(pins)
    )
    if default_pin_name_size:
        # pin_name_size = 0.7874
        stmts.append(
            to_ast_assign("pin_name_size", to_grid_scale(default_pin_name_size))
        )
    if default_pad_name_size:
        # pad_name_size = 0.7874
        stmts.append(
            to_ast_assign("pad_name_size", to_grid_scale(default_pad_name_size))
        )

    grouped_index: Mapping[str, list[SymbolPinCode]] = defaultdict(list)
    grouped_bundle = []
    standalone = []

    # Group pads
    for pin in sanitized_updated_pins:
        pin_type = pin.pin.type
        val = pin.pin.value
        if pin_type == PinByType.pin_by_index:
            grouped_index[val.name].append(pin)
        elif pin_type == PinByType.pin_by_bundle:
            grouped_bundle.append(pin)
        else:
            standalone.append(pin)

    # 1. Emit index-based grouped dicts
    for name, group in grouped_index.items():
        group = sorted(group, key=lambda pin: pin.pin.value.index)
        dict_expr = {pin.pin.value.index: pin for pin in group}
        stmts.append(to_ast_assign(name, dict_expr))

    # 2. Emit bundle-based grouped dicts
    for pin in grouped_bundle:
        val = pin.pin.value
        pin_name = f"{val.bundle_name}_{val.pin_name}"
        stmts.append(to_ast_assign(pin_name, pin))

    # 3. Emit individual assignments
    for pin in standalone:
        pin_name = convert_pin_code_to_str(pin.pin)
        stmts.append(to_ast_assign(pin_name, pin))
    return stmts


# Converts a SymbolCode object into an AST module with a single class definition.
def convert_symbol_to_ast_module(
    symbol: SymbolCode, class_name: str = "QuerySymbol"
) -> ast.Module:
    body = []
    use_gs = True

    # Pins
    pins_expr = convert_grouped_symbol_pins_to_ast_stmts(symbol.pins)
    body.extend(pins_expr)

    # Layer reference
    body.append(to_ast_assign("layer_reference", symbol.layer_reference.text, use_gs))

    # Layer value
    body.append(to_ast_assign("layer_value", symbol.layer_value.text, use_gs))

    # Layers
    shape_exprs = [layer.shape for layer in symbol.layers]
    body.append(to_ast_assign("draws", shape_exprs, use_gs))

    # Class definition
    class_def = ast.ClassDef(
        name=class_name,
        bases=[to_ast_name("Symbol")],
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )
    return ast.Module(body=[class_def], type_ignores=[])


# ============ Utilities to convert component to AST ============
#     Functions: convert_component_to_ast_module etc.
# ===============================================================
# ==== functions for Component: group ports ====
def convert_grouped_ports_to_ast_stmts(
    ports: Sequence[PinPropertyCode],
) -> Sequence[ast.stmt]:
    def sanitize_pin_property_code(port: PinPropertyCode):
        return PinPropertyCode(
            sanitize_pin(port.pin),
            [sanitize_pin(port) for port in port.pads],
            port.direction,
            port.electrical_type,
            port.bank,
        )

    sanitized_ports = [sanitize_pin_property_code(port) for port in ports]

    grouped_index: Mapping[str, list[PinPropertyCode]] = defaultdict(list)
    grouped_bundle = []
    standalone = []

    # Group pads
    for pin in sanitized_ports:
        pin_type = pin.pin.type
        val = pin.pin.value

        if pin_type == PinByType.pin_by_index:
            grouped_index[val.name].append(pin)
        elif pin_type == PinByType.pin_by_bundle:
            grouped_bundle.append(pin)
        else:
            standalone.append(pin)

    results = []

    # 1. Emit index-based grouped dicts
    for name, group in grouped_index.items():
        group = sorted(group, key=lambda port: port.pin.value.index)
        dict_expr = {pin.pin.value.index: to_ast_call("Port") for pin in group}
        results.append(to_ast_assign(name, dict_expr))

    # 2. Emit bundle-based grouped dicts
    for pin in grouped_bundle:
        val = pin.pin.value
        pad_name = f"{val.bundle_name}_{val.pin_name}"
        value_expr = to_ast_call("Port")
        results.append(to_ast_assign(pad_name, value_expr))

    # 3. Emit individual assignments
    for pin in standalone:
        pin_name = convert_pin_code_to_str(pin.pin)
        value = to_ast_call("Port")
        results.append(to_ast_assign(pin_name, value))
    return results


def build_pin_map_entries(
    pin_obj: PinPropertyCode,
    pads: Sequence[PinByTypeCode],
    source_obj: str,
    num_symbols: int = 1,
) -> tuple[ast.expr, ast.expr]:
    """
    Builds (key_expr, value_expr) for a pin:
        key_expr = p[1] or GND or A.B
        value_expr = landpattern.p[2] or [landpattern.p[2], landpattern.p[3]]
    """
    # Key = p[1] or GND or A.B
    key_expr = convert_pin_code_to_ast_expr(pin_obj.pin)

    # Value = single expr or list of exprs
    def pin_code_to_ast(pin: PinByTypeCode) -> ast.expr:
        bank = pin_obj.bank if num_symbols > 1 else None
        return convert_pin_code_to_ast_expr(pin, source_obj, bank)

    value_expr: ast.expr = (
        pin_code_to_ast(pads[0])
        if len(pads) == 1
        else ast.List(elts=[pin_code_to_ast(p) for p in pads], ctx=ast.Load())
    )
    return (key_expr, value_expr)


@dataclass(frozen=True)
class ComponentField:
    db: str
    jitx: str


# Mapping of field names between the json in the Parts DB and the class attribute names in the JITX syntax.
component_fields = [
    ComponentField(db="manufacturer", jitx="manufacturer"),
    ComponentField(db="mpn", jitx="mpn"),
    ComponentField(db="reference_prefix", jitx="reference_designator_prefix"),
    ComponentField(db="datasheet", jitx="datasheet"),
]


def convert_component_to_ast_module(
    component: ComponentCode,
    class_name: str = "QueryComponent",
    use_jitxstd_symbol: StdLibSymbolType | None = None,
) -> ast.Module:
    """Convert a ComponentCode object to an ast.Module.
    Args:
        component: ComponentCode
        class_name: Name of the generated class
    Returns:
        ast.Module
    Fields Not Handled:
        emodel: EModel | None
        metadata: Sequence[KeyValue]
        properties: Sequence[ComponentPropertyCode]
        bundles: Sequence[BundleCode]
        supports: Sequence[SupportCode]
    """
    body = []
    # --- Simple string fields ---
    for field in component_fields:
        val = getattr(component, field.db)
        # If this is ever triggered, update the typing of _types.component.ComponentCode as well as query_api.Resistor/Inductor/Capacitor/Part to allow it.
        assert val is not None, (
            f"Field {field.db} is missing on part {component.mpn} from the Parts DB."
        )
        body.append(to_ast_assign(field.jitx, val))

    # --- Value assignment ---
    if component.emodel:
        emodel = component.emodel.value
        if isinstance(emodel, ResistorEModel):
            resistance = emodel.resistance
            if isinstance(resistance, float):
                value_expr = ast.BinOp(
                    left=ast.Constant(value=resistance),
                    op=ast.Mult(),
                    right=to_ast_name("ohm"),
                )
                body.append(to_ast_assign("value", value_expr))
        elif isinstance(emodel, InductorEModel):
            inductance = emodel.inductance
            if isinstance(inductance, float):
                value_expr = ast.BinOp(
                    left=ast.Constant(value=inductance),
                    op=ast.Mult(),
                    right=to_ast_name("H"),
                )
                body.append(to_ast_assign("value", value_expr))
        elif isinstance(emodel, CapacitorEModel):
            capacitance = emodel.capacitance
            if isinstance(capacitance, float):
                value_expr = ast.BinOp(
                    left=ast.Constant(value=capacitance),
                    op=ast.Mult(),
                    right=to_ast_name("F"),
                )
                body.append(to_ast_assign("value", value_expr))

    # --- Port dictionary ---
    # GND = Port()
    if hasattr(component.pin_properties, "pins"):
        ports = component.pin_properties.pins
        ports_expr = convert_grouped_ports_to_ast_stmts(ports)
        body.extend(ports_expr)

    # --- Landpattern assignment ---
    if component.landpattern:
        landpattern_class = python_landpattern_name(component.landpattern.name)
        value_expr = to_ast_call(landpattern_class)
        body.append(to_ast_assign("landpattern", value_expr))

    # --- Symbol(s) assignment ---
    if use_jitxstd_symbol is not None:
        symbol_expr = get_jitxstd_symbol_expr(use_jitxstd_symbol)
        body.append(to_ast_assign("symbol", symbol_expr))
    else:
        if component.symbols:
            if len(component.symbols) == 1:
                symbol_class = python_symbol_name(component.symbols[0].name)
                value_expr = to_ast_call(symbol_class)
                body.append(to_ast_assign("symbol", value_expr))
            else:
                value_expr = {
                    symbol.bank: to_ast_call(python_symbol_name(symbol.name))
                    for symbol in component.symbols
                }
                value_expr = ast.Dict(
                    keys=[ast.Constant(symbol.bank) for symbol in component.symbols],
                    values=[
                        to_ast_call(python_symbol_name(symbol.name))
                        for symbol in component.symbols
                    ],
                )
                body.append(to_ast_assign("symbol", value_expr))

    # --- cmappings ---
    pin_map_entries = get_symbol_mapping_expr(component, use_jitxstd_symbol)
    lp_map_entries = (
        [
            build_pin_map_entries(pin, pin.pads, "landpattern")
            for pin in component.pin_properties.pins
        ]
        if component.landpattern
        else None
    )
    value_expr = []
    if pin_map_entries:
        value_expr.append(
            to_ast_call(
                "SymbolMapping",
                args=[
                    ast.Dict(
                        keys=[k for (k, v) in pin_map_entries],
                        values=[v for (k, v) in pin_map_entries],
                    )
                ],
            )
        )
    if lp_map_entries:
        value_expr.append(
            to_ast_call(
                "PadMapping",
                args=[
                    ast.Dict(
                        keys=[k for (k, v) in lp_map_entries],
                        values=[v for (k, v) in lp_map_entries],
                    )
                ],
            )
        )
    body.append(to_ast_assign("cmappings", value_expr))

    # --- Create the class ---
    class_def = ast.ClassDef(
        name=class_name,
        bases=[to_ast_name("Component")],
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )

    return ast.Module(body=[class_def], type_ignores=[])


def get_jitxstd_symbol_expr(use_jitxstd_symbol: StdLibSymbolType) -> ast.expr:
    match use_jitxstd_symbol:
        case StdLibSymbolType.Resistor:
            return to_ast_call("ResistorSymbol")
        case StdLibSymbolType.Inductor:
            return to_ast_call("InductorSymbol")
        case StdLibSymbolType.Capacitor:
            return to_ast_call("CapacitorSymbol")
        case StdLibSymbolType.PolarizedCapacitor:
            return to_ast_call("PolarizedCapacitorSymbol")
        case _:
            raise ValueError(f"Unknown StdLibSymbolType: {use_jitxstd_symbol}")


def sorted_pin_name_representations(component: ComponentCode) -> list[str]:
    return sorted(
        convert_pin_code_to_str(pin.pin) for pin in component.pin_properties.pins
    )


def get_symbol_mapping_expr(
    component: ComponentCode, use_jitxstd_symbol: StdLibSymbolType | None
) -> list[tuple[ast.expr, ast.expr]] | None:
    if use_jitxstd_symbol is not None:
        assert len(component.pin_properties.pins) == 2, (
            "Only two pins are supported for using a jitx standard library symbol for returned components of Parts DB queries."
        )

        # Case: PolarizedCapacitor - maps pins (a, c) to single symbol with pins (a, c)
        if use_jitxstd_symbol == StdLibSymbolType.PolarizedCapacitor:
            pin_name_representations = sorted_pin_name_representations(component)
            assert pin_name_representations == ["a", "c"], (
                f"PolarizedCapacitor symbol requires pins named 'a', 'c' but pins of returned part are {', '.join(pin_name_representations)}"
            )

            pins = (to_ast_name("a"), to_ast_name("c"))
            symbol_pins = (
                to_ast_attribute("symbol", "a"),
                to_ast_attribute("symbol", "c"),
            )
            return list(zip(pins, symbol_pins, strict=True))
        # Case: Resistor, Capacitor, Inductor - maps 2 pins to 2 symbol pins. The order does not matter. The statement could be omitted as JITX would create a default mapping.
        else:
            pins = [
                convert_pin_code_to_ast_expr(pin.pin)
                for pin in component.pin_properties.pins
            ]
            symbol_pins = [
                to_ast_subscript(to_ast_attribute("symbol", "p"), i) for i in (1, 2)
            ]
            return list(zip(pins, symbol_pins, strict=True))
    # Otherwise case : note that build_pin_map_entries handles multi-unit components.
    elif component.symbols:
        return [
            build_pin_map_entries(pin, [pin.pin], "symbol", len(component.symbols))
            for pin in component.pin_properties.pins
        ]
    return None


# ============ Utilities to create imports in AST ============
#     Functions: prepare_ast_module_with_imports etc.
# ===============================================================
# ==== prepare imports for AST =====
symbols_to_import = {
    # == shapes
    "Anchor": "jitx.anchor",
    "Shape": "jitx.shapes",
    "Arc": "jitx.shapes.primitive",
    "ArcPolygon": "jitx.shapes.primitive",
    "ArcPolyline": "jitx.shapes.primitive",
    "capsule": "jitx.shapes.composites",
    "Circle": "jitx.shapes.primitive",
    "Polygon": "jitx.shapes.primitive",
    "PolygonSet": "jitx.shapes.primitive",
    "Polyline": "jitx.shapes.primitive",
    "Text": "jitx.shapes.primitive",
    "rectangle": "jitx.shapes.composites",
    "Transform": "jitx.transform",
    # == layers
    "Soldermask": "jitx.feature",
    "Paste": "jitx.feature",
    "Cutout": "jitx.feature",
    "Silkscreen": "jitx.feature",
    "Courtyard": "jitx.feature",
    "Custom": "jitx.feature",
    "KeepOut": "jitx.feature",
    "LayerSet": "from jitx.layerindex",
    "Model3D": "jitx.model3d",
    # == landpatterns
    "Pad": "jitx.landpattern",
    "PadType": "jitx.landpattern",
    "Side": "jitx.layerindex",
    "Landpattern": "jitx.landpattern",
    # == symbols
    "Direction": "jitx.symbol",
    "Symbol": "jitx.symbol",
    "Pin": "jitx.symbol",
    # == components
    "Component": "jitx.component",
    "Port": "jitx.net",
    "PadMapping": "jitx.landpattern",
    "SymbolMapping": "jitx.symbol",
    # == units
    "ohm": "jitx.units",
    "F": "jitx.units",
    "H": "jitx.units",
    # == jitxlib
    "ResistorSymbol": "jitxlib.symbols.resistor",
    "InductorSymbol": "jitxlib.symbols.inductor",
    "CapacitorSymbol": "jitxlib.symbols.capacitor",
    "PolarizedCapacitorSymbol": "jitxlib.symbols.capacitor",
}


def extract_ast_names(node: ast.AST) -> set[str]:
    names = set()

    class NameVisitor(ast.NodeVisitor):
        def visit_Name(self, n: ast.Name):
            if isinstance(n.ctx, ast.Load):
                names.add(n.id)
            self.generic_visit(n)

        def visit_Attribute(self, n: ast.Attribute):
            # Walk down to the root of an attribute chain like Anchor.W or Direction.Up
            current = n
            while isinstance(current.value, ast.Attribute):
                current = current.value
            if isinstance(current.value, ast.Name):
                names.add(current.value.id)
            self.generic_visit(n)

        def visit_Call(self, n: ast.Call):
            # Handle function name like Pin(...)
            if isinstance(n.func, ast.Name):
                names.add(n.func.id)
            elif isinstance(n.func, ast.Attribute):
                self.visit_Attribute(n.func)
            # Also check all arguments
            for arg in n.args:
                self.visit(arg)
            for kw in n.keywords:
                self.visit(kw.value)

    NameVisitor().visit(node)
    return names


def add_imports_to_ast_module(module: ast.Module) -> ast.Module:
    """
    Add deduplicated grouped import-from statements to the AST module.
    Uses extract_ast_names and symbols_to_import map.
    """

    def group_imports_by_module(symbols: set[str]) -> Mapping[str, Sequence[str]]:
        """
        Given a set of symbol names and a mapping from symbol → module,
        return a dict of module → list of symbols to import from it.
        """
        grouped: Mapping[str, list[str]] = {}
        for name in symbols:
            if name in symbols_to_import:
                module = symbols_to_import[name]
                grouped.setdefault(module, []).append(name)
        return grouped

    used_symbols = extract_ast_names(module)
    grouped_imports = group_imports_by_module(used_symbols)

    import_nodes = []
    for module_path, names in sorted(grouped_imports.items()):
        aliases = [ast.alias(name=n, asname=None) for n in sorted(set(names))]
        import_nodes.append(ast.ImportFrom(module=module_path, names=aliases, level=0))

    module.body = import_nodes + module.body
    return module


def prepare_ast_module_with_imports(ast_module: ast.Module) -> ast.Module:
    """
    Injects imports, fixes locations, and formats the AST module.

    Returns:
        The resulting Python source code as a string.
    """
    # Insert imports like: from jitx.feature import Soldermask, Paste
    ast_module = add_imports_to_ast_module(ast_module)

    # Ensure all line numbers are present
    ast.fix_missing_locations(ast_module)
    return ast_module


# ======== MAIN FUNCTION ========
# Create one combined AST Module for all defs for the Component File
def component_code_to_ast_module(
    component_code: ComponentCode,
    component_name: str | None = None,
    use_jitxstd_symbol: StdLibSymbolType | None = None,
    missing_3d_models: tuple[str, ...] = (),
) -> ast.Module:
    global conversion_error_count
    all_defs = []
    conversion_error_count = 0
    # === Collect all pad class definitions ===
    pad_class_names = []
    for pad in component_code.pcb_pads:
        class_name = sanitize_defpad(pad.name)
        pad_ast = convert_pad_to_ast_module(pad, class_name)
        all_defs.extend(pad_ast.body)
        pad_class_names.append(class_name)
    # === Add landpattern class definition ===
    if component_code.landpattern:
        class_name = python_landpattern_name(component_code.landpattern.name)
        land_ast = convert_landpattern_to_ast_module(
            component_code.landpattern, class_name, missing_3d_models
        )
        all_defs.extend(land_ast.body)
    # === Write all symbol definitions ===
    if use_jitxstd_symbol is None:
        for symbol in component_code.symbols:
            class_name = python_symbol_name(symbol.name)
            symbol_ast = convert_symbol_to_ast_module(symbol, class_name)
            all_defs.extend(symbol_ast.body)
    # === Add top-level component class definition
    if isinstance(component_name, str):
        class_name = component_name
    else:
        class_name = python_component_name(component_code.mpn, component_code.name)
    component_ast = convert_component_to_ast_module(
        component_code, class_name, use_jitxstd_symbol=use_jitxstd_symbol
    )
    all_defs.extend(component_ast.body)
    # === Add alias for class Conn_12: Device: type[Conn_12] = Conn_12
    device_alias_stmt = ast.AnnAssign(
        target=ast.Name(id="Device", ctx=ast.Store()),
        annotation=ast.Subscript(
            value=ast.Name(id="type", ctx=ast.Load()),
            slice=ast.Name(id=class_name, ctx=ast.Load()),
            ctx=ast.Load(),
        ),
        value=ast.Name(id=class_name, ctx=ast.Load()),
        simple=1,
    )
    all_defs.append(device_alias_stmt)

    if conversion_error_count > 0:
        raise RuntimeError(
            f"{conversion_error_count} AST conversion error(s) encountered."
        )

    full_ast = ast.Module(body=all_defs, type_ignores=[])
    return prepare_ast_module_with_imports(full_ast)
