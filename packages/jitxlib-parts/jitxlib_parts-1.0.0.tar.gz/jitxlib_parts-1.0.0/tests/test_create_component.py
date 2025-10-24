import unittest
import sys
import argparse
import json

import pytest
from collections.abc import Sequence, Mapping

import jitx._instantiation
from jitx._websocket import set_websocket_uri
from jitx.sample import SampleDesign

from jitxlib.parts.commands import dbquery
from jitxlib.parts._types.main import to_component
from jitxlib.parts._types.component import Part as PartType
from jitxlib.parts.convert import (
    convert_component,
    create_component,
    compile_subclasses_from_file,
)
from jitxlib.parts import Part
from . import builder


class TestCreateComponent(unittest.TestCase):
    port: int

    def setUp(self):
        if hasattr(TestCreateComponent, "port"):
            set_websocket_uri(host="localhost", port=TestCreateComponent.port)
        import jitxlib.parts.commands

        jitxlib.parts.commands.ALLOW_NO_DESIGN_CONTEXT = True

    def test_resistor_component_from_json(self):
        part_json_path = "tests/data/RK73B1FRTTBL103J.resistor.json"
        print(f">>[test_resistor_component_from_json] part_json_path={part_json_path}")
        with open(part_json_path, "r", encoding="utf-8") as file:
            part_json = json.load(file)
        part_obj = to_component(part_json)
        output_path = "output_part.py"
        compiled_component = convert_component(
            part_obj.component, output_path=output_path
        )
        self.assertTrue(issubclass(compiled_component, jitx.Component))
        print(f"    Python file writen to {output_path}")
        print(f"    Component created: {compiled_component.__name__}")
        build_design(compiled_component, "resistor")
        print("<<[test_resistor_component_from_json] Done")

    # Calls download_model_3d
    @pytest.mark.integration
    def test_other_component_from_json(self):
        # - multiple-pins - with Model3D file
        part_json_path = "tests/data/LM317LM.json"
        # - 2-unit symbol - integer bank 0 to 7
        # part_json_path = "tests/data/FDS4935BZ.2units.json"
        # - 8-unit transformer - integer bank 0 to 7
        # part_json_path = "tests/data/PTG-9681.8units.json"
        # - mpn "10132328-10011LF" # 2 lp_pads with 45 degrees; 2 pads with 135 degrees; many pads
        # part_json_path = "tests/data/10132328-10011LF.45-degree-pads.json"
        print(f">>[test_other_component_from_json] part_json_path={part_json_path}")
        with open(part_json_path, "r", encoding="utf-8") as file:
            part_json = json.load(file)
        part_obj = to_component(part_json)
        output_path = "output_part.py"
        compiled_component = convert_component(
            part_obj.component, output_path=output_path
        )
        self.assertTrue(issubclass(compiled_component, jitx.Component))
        print(f"    Python file writen to {output_path}")
        print(f"    Component created: {compiled_component.__name__}")
        build_design(compiled_component, "Other Comp")
        print(">>[test_other_component_from_json] Done")

    # Retrieve the compiled component without build_design()
    def run_dbquery_by_mpn(self, mpn: str) -> type[jitx.Component]:
        print(f">>[run_dbquery_by_mpn] mpn = {mpn}")
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"mpn": mpn}, limit=1)
        self.assertEqual(len(result), 1)
        part_json = result[0]
        write_json_to_file(part_json, "output_part.json")
        part = PartType.from_dict(part_json)

        # also write the Python code to output_part.py for testing
        output_path = "output_part.py"
        compiled_component = convert_component(part.component, output_path=output_path)
        self.assertTrue(issubclass(compiled_component, jitx.Component))
        print(f"    Python file writen to {output_path}")
        print(f"    Component created: {compiled_component.__name__}")
        return compiled_component

    def get_mpn_list(
        self, idx: int | None = None, idx_end: int | None = None
    ) -> Sequence[str]:
        mpn_list = [
            "RK73B1FRTTBL103J",  # 2-pin resistor
            "LM317LM",  # include Model3D
            "LM311DR",  # VCC+/VCC- pinsresult[0])
            "FDS4935BZ",  # 2-unit transistor
            "PTG-9681",  # 8-unit transformer
            "DIO20891CN4",  # one lp_pad is 45 degree. 5 total pads.
            # - Pin "V-" => invalid python in convert_to_ast. Symbol is off in convert.py
            "10132328-10011LF",  # 2 lp_pads with 45 degrees; 2 pads with 135 degrees; many differnt shaped pads
            # - Silkscreen on Bottom side. Transform on Pad. ArcPolygon
            # - Soldermask(Circle(radius=0.55).at((0, 0)), side=Side.Bottom),
            # RectangleSmdPad1().at(Transform((3.75, -1.0005), 45)),
            # Transform((-1, -1)) * rectangle(18.00004, 26.00005),
            "PJ-612",  # 1 lp-pads with 45 degree; 5 total pads; complex symbol
            "EEEFN1A471V",  # two pads, each is polygon, like a cross.
            # - Text on silkscreen, which is not <REF or <VALUE
            "TLC2202ACDR",  # 2-unit symbol, one with many pins, one with few pins
            # - pins "VDD+", "VDD-_GND", "P_2IN-", "P_2IN+". VDD+/VDD- missing on the second unit?
            "OPA4377AIPWR",  # 4-unit symbol, 3 pins plus "V+"" and "V-"" on each unit
            # - "Vp" and Vn" only appear on one unit.
            # - ArcPolyline with one Arc, ArcPolygon with two Arcs
            "DAC3482IZAYR",  # 14 large units. 14x14 grid array
            "10SEV2200M12.5X16",  # include two polygon_with_arcs,
            # - one polygon_with_arcs consiting of points and arcs, and one consisting of only points
            #   => converted to ArcPolygon
            #   => After conversion, there are ArcPolygon containing only points,
            #      and ArcPolyline containing only one Arc. Polyline with only two points.
            # - landpattern has a strange square
            "EEFSX0D331ER",  # include polygon_with_arcs, but only consitsting of points
            "0.1uF 50V 5*11",  # one polygon_with_arcs with only one arc. The others consisting of only points.
            "160ARUP501M55A2E14PFBP26",  # one polygon_with_arcs with only one arc. The others consisting of only points.
            "EC05E1220401",  # switch with polygon_with_arcs, containing arc
            "EC11K1524406",  # switch with polygon_with_arcs
        ]
        if idx is None and idx_end is None:
            return mpn_list
        elif idx is None:  # idx_end is not None
            return mpn_list[0:idx_end]
        elif idx_end is None:  # idx is not None
            return mpn_list[idx:]
        elif idx == idx_end:
            print("idx == idx_end => return [mpn_list[idx]]: ", [mpn_list[idx]])
            return [mpn_list[idx]]
        else:
            return mpn_list[idx:idx_end]

    # Calls dbquery
    @pytest.mark.integration
    def test_dbquery_mpn_list(self):
        # mpn_list = self.get_mpn_list()
        mpn_list = ["LM317LM"]  # include Model3d file
        # mpn_list = ["10132328-10011LF"] # self.get_mpn_list(6,6)
        # mpn_list = ["LM317LM", "PTG-9681", "DIO20891CN4", "10132328-10011LF"]'
        components: dict[str, type[jitx.Component]] = {}
        n_passed = 0
        print(f">>[test_dbquery_mpn_list] mpn_list={mpn_list}")
        for mpn in mpn_list:
            try:
                components[mpn] = self.run_dbquery_by_mpn(mpn)
                n_passed += 1
            except Exception as e:
                print(f"Failed to run_dbquery_by_mpn({mpn}): {e}")
        self.assertTrue(n_passed == len(mpn_list))
        build_design_with_multiple_components(components, "test_dbquery_mpn_list")
        print("<<[test_dbquery_mpn_list] Done")

    # Calls dbquery
    @pytest.mark.integration
    def test_create_component(self):
        # mpn = self.get_mpn_list(6, 6)[0]
        # mpn = "LM317LM"  # include Model3d file
        mpn = "FDS4935BZ"  # include Model3d file
        # mpn = "10132328-10011LF" # self.get_mpn_list(6)
        print(f">>[test_create_component] mpn={mpn}")
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"mpn": mpn}, limit=1)
        self.assertEqual(len(result), 1)
        part_json = result[0]
        write_json_to_file(part_json, "output_part.json")

        # Write the Python code to components/MANUFACTURER/ComponentName.py
        copy_to_clipboard, output_path = create_component(part_json)
        print(f"    Python file writen to {output_path}")
        print(f"    Copy to Clipboard: {copy_to_clipboard}")

        # Verify the generate python code: read from module_path and load the component
        component_subclasses = compile_subclasses_from_file(output_path, jitx.Component)
        self.assertTrue(len(component_subclasses) == 1)
        self.assertTrue(issubclass(component_subclasses[0], jitx.Component))
        compiled_component = component_subclasses[0]
        build_design(compiled_component, compiled_component.__name__)
        print("<<[test_create_component] Done")

    # Calls dbquery
    @pytest.mark.integration
    def test_create_part_instance(self):
        with jitx._instantiation.instantiation.activate():
            # mpn, manufacturer = ("DAC3482IZAYR", "Texas Instruments")
            # mpn, manufacturer = ("OPA4377AIPWR", "Texas Instruments")
            # mpn, manufacturer = ("10132328-10011LF", "Amphenol ICC")
            # mpn, manufacturer = ("TLC2202ACDR", "Texas Instruments")
            mpn, manufacturer = ("U-C-19DD-W-1", "Korean Hroparts Elec")
            print(f">>[test_create_part_instance] mpn={mpn}")
            part_inst = Part(mpn=mpn, manufacturer=manufacturer)
        self.assertTrue(isinstance(part_inst, jitx.Component))
        print(
            f"     Component instance created from component: {part_inst.__class__.__name__}"
        )
        build_design_with_component_instance(part_inst, part_inst.__class__.__name__)
        print("<<[test_create_part_instance] Done")

    # Example in README.md
    # Calls dbquery
    @pytest.mark.integration
    def test_create_resistor(self):
        from jitxlib.parts import ResistorQuery, Resistor

        # Create a query for a resistor
        query = ResistorQuery().update(
            resistance=10e3,  # 10kΩ
            tolerance=0.01,  # 1%
            case="0603",  # 0603 package
        )

        # Create a resistor component
        with jitx._instantiation.instantiation.activate():
            resistor = Resistor(query, comp_name="TestResistor")
        self.assertTrue(isinstance(resistor, jitx.Component))
        build_design_with_component_instance(resistor, resistor.__class__.__name__)


def build_design(component: type[jitx.Component], mpn: str):
    """Build a design from a component and send it to the web socket.

    Args:
        component: The component class to build the design from
        mpn: The mpn of the component
    """

    class QueryCircuit(jitx.Circuit):
        components = {mpn: component()}

        def __init__(self):
            self.place(self.components[mpn], (0, 0))

    build_circuit(QueryCircuit, mpn)


def build_design_with_component_instance(component_instance: jitx.Component, name: str):
    """Build a design from a component instance and send it to the web socket.

    Args:
        component_instance: The component instance to build the design from
        name: The name of the component
    """

    class QueryCircuit(jitx.Circuit):
        components = {name: component_instance}  # not need to add "()"

        def __init__(self):
            self.place(self.components[name], (0, 0))

    build_circuit(QueryCircuit, name)


def build_design_with_multiple_components(
    components: Mapping[str, type[jitx.Component]], name: str
):
    """Build a design from a component instance and send it to the web socket.

    Args:
        component_instance: The component instance to build the design from
        mpn: The mpn of the component
    """

    class QueryCircuit(jitx.Circuit):
        instances = {mpn: component() for mpn, component in components.items()}

        def __init__(self):
            for i, (mpn, _) in enumerate(self.instances.items()):
                self.place(self.instances[mpn], (i * 10, 0))

    build_circuit(QueryCircuit, name)


def build_circuit(circ: type[jitx.Circuit], name: str):
    """Build a design from a component and send it to the web socket.

    Args:
        circuit: The circuit class to build the design from
        name: Design name
    """

    class TestDesign(SampleDesign):
        circuit = circ()

    TestDesign.__name__ = name

    builder.build(
        name=name, design=TestDesign, formatter=text_formatter, dump=f"{name}.json"
    )


def text_formatter(ob, file=sys.stdout, indent=0):
    # not great but better than nothing, could use yaml or something.
    ind = "  " * indent
    if isinstance(ob, dict):
        for key, value in ob.items():
            if isinstance(value, (list, dict)):
                print(ind + key + ":", file=file)
                text_formatter(value, file, indent + 1)
            else:
                print(ind + key + ":" + " " + str(value), file=file)
    elif isinstance(ob, list):
        if not ob:
            print(ind + "[]", file=file)
        for el in ob:
            if isinstance(el, (list, dict)):
                text_formatter(el, file, indent + 1)
            else:
                text_formatter(el, file, indent)
    else:
        print(ind + str(ob), file=file)


def write_json_to_file(data, path):
    print(f"    JSON written to '{path}'")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="WebSocket port number")
    args, unittest_args = parser.parse_known_args()

    # Set the port in the test class
    TestCreateComponent.port = args.port

    # Run unittest with remaining arguments
    unittest.main(argv=sys.argv[:1] + unittest_args)
