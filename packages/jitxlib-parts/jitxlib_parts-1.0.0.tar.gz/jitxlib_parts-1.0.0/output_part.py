# This file is generated based on the parts database query below:
#     from jitx.circuit import Circuit
#     from jitxlib.parts import Part
#     class Example(Circuit):
#         def __init__(self):
#            self.part = Part(mpn="RK73B1FRTTBL103J", manufacturer="KOA")
#
# File Location: components/KOA/RK73B1FRTTBL103J.py
# To use this component:
#     from .components.KOA import RK73B1FRTTBL103J
#     class Example(Circuit):
#         u1 = RK73B1FRTTBL103J.Device()
from jitx.anchor import Anchor
from jitx.component import Component
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad, PadMapping
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Polyline, Text
from jitx.symbol import Direction, Pin, Symbol, SymbolMapping
from jitx.units import ohm


class RectSmdPad(Pad):
    shape = rectangle(0.22, 0.10606)
    paste = [Paste(rectangle(0.22, 0.10606))]
    solder_mask = [Soldermask(rectangle(0.32, 0.20606))]


class Landpattern01005(Landpattern):
    name = "01005"
    p = {1: RectSmdPad().at((0, 0.15697)), 2: RectSmdPad().at((0, -0.15697))}
    pcb_layer_reference = Silkscreen(Text(">REF", 0.6, Anchor.C).at((0.56, 0)))
    pcb_layer_value = Custom(Text(">VALUE", 0.3, Anchor.C).at((0.41, 0)), name="Fab")
    courtyard = [Courtyard(rectangle(0.52, 0.72))]


class Symbolresistor_sym(Symbol):
    p = {1: Pin((0, 2), 0, Direction.Up), 2: Pin((0, -2), 0, Direction.Down)}
    layer_reference = Text(">REF", 1, Anchor.W).at((1, 1))
    layer_value = Text(">VALUE", 1, Anchor.W).at((1, -1))
    draws = [
        Polyline(0.254, [(0, -2), (0, -1.25)]),
        Polyline(
            0.254,
            [
                (0, -1.25),
                (-0.6, -1),
                (0.6, -0.5),
                (-0.6, 0),
                (0.6, 0.5),
                (-0.6, 1),
                (0, 1.25),
            ],
        ),
        Polyline(0.254, [(0, 1.25), (0, 2)]),
    ]


class RK73B1FRTTBL103J(Component):
    manufacturer = "KOA"
    mpn = "RK73B1FRTTBL103J"
    reference_designator_prefix = "R"
    datasheet = "https://www.koaspeer.com/pdfs/RK73-RT.pdf"
    value = 10000.0 * ohm
    p = {1: Port(), 2: Port()}
    landpattern = Landpattern01005()
    symbol = Symbolresistor_sym()
    cmappings = [
        SymbolMapping({p[1]: symbol.p[1], p[2]: symbol.p[2]}),
        PadMapping({p[1]: landpattern.p[1], p[2]: landpattern.p[2]}),
    ]


Device: type[RK73B1FRTTBL103J] = RK73B1FRTTBL103J
