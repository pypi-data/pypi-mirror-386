import unittest

import pytest
from pprint import pprint
import argparse
import sys

import jitx._instantiation
from jitx.sample import SampleDesign
from jitx._websocket import set_websocket_uri
from jitxlib.parts.commands import dbquery
from jitxlib.parts._types.capacitor import Capacitor
from jitxlib.parts._types.inductor import Inductor
from jitxlib.parts._types.resistor import Resistor
from jitxlib.parts._types.component import Part
from jitxlib.parts.convert import convert_component
from . import builder


############################
# Run unit tests : hatch test -m "not integration"
# Run integration tests : hatch test -m integration
# Integration tests require a running JITX interactive server and its websocket port passed as cli argument.
############################


class DBQueryTest(unittest.TestCase):
    port: int

    def setUp(self):
        if hasattr(DBQueryTest, "port"):
            set_websocket_uri(host="localhost", port=DBQueryTest.port)
        import jitxlib.parts.commands

        jitxlib.parts.commands.ALLOW_NO_DESIGN_CONTEXT = True

    # Calls dbquery
    @pytest.mark.integration
    def test_query_10k_resistor(self):
        # Instantiation context needed by dbquery to retrieve the design name from the DesignContext.
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"category": "resistor", "resistance": 10000.0}, limit=1)
            # print(result)
        self.assertEqual(len(result), 1)
        # self.assertEqual(result[0]["resistance"], 10000.0)

        # Make a Resistor object
        resistor = Resistor.from_dict(result[0])
        print(
            f"type(resistor = {type(resistor)}"
        )  # => <class 'jitx_parts.types.resistor.Resistor'>
        print("\nResistor Details:")
        print("=" * 50)
        pprint(resistor, width=100)

        component = convert_component(
            resistor.component
        )  # resistor.component is ComponentCode
        build_design(component, resistor.component.mpn)

    # Calls dbquery
    @pytest.mark.integration
    def test_query_100n_capacitor(self):
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"category": "capacitor", "capacitance": 1e-7}, limit=1)
        # print(result)
        self.assertEqual(len(result), 1)
        # self.assertEqual(result[0]["capacitance"], 1e-7)

        # Make a Resistor object
        capacitor = Capacitor.from_dict(result[0])
        print("\nCapacitor Details:")
        print("=" * 50)
        pprint(capacitor, width=100)

        component = convert_component(capacitor.component)
        build_design(component, capacitor.component.mpn)

    # Calls dbquery
    @pytest.mark.integration
    def test_query_inductor(self):
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"category": "inductor", "inductance": 1e-6}, limit=1)
        # print(result)
        self.assertEqual(len(result), 1)
        # self.assertEqual(result[0]["inductance"], 1e-6)

        # Make a Resistor object
        inductor = Inductor.from_dict(result[0])
        print("\nInductor Details:")
        print("=" * 50)
        pprint(inductor, width=100)

        component = convert_component(inductor.component)
        build_design(component, inductor.component.mpn)

    # Calls dbquery
    @pytest.mark.integration
    def test_query_diode(self):
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"category": "diode"}, limit=1)
        # print(result)
        self.assertEqual(len(result), 1)
        # self.assertEqual(result[0]["inductance"], 1e-6)

        # Make a Resistor object
        part = Part.from_dict(result[0])
        print("\nPart Details:")
        print("=" * 50)
        pprint(part, width=100)

        component = convert_component(part.component)
        build_design(component, part.component.mpn)

    # Calls dbquery
    @pytest.mark.integration
    def test_query_multi_unit(self):
        # 2-unit transistor
        with jitx._instantiation.instantiation.activate():
            result = dbquery({"mpn": "FDS4935BZ"}, limit=1)
        # 8-unit transformer
        # result = dbquery({"mpn": "PTG-9681"}, limit=1)
        print(result)
        self.assertEqual(len(result), 1)
        # self.assertEqual(result[0]["inductance"], 1e-6)

        # Make a Resistor object
        part = Part.from_dict(result[0])
        print("\nPart Details:")
        print("=" * 50)
        pprint(part, width=100)

        component = convert_component(part.component)
        build_design(component, part.component.mpn)

    # def test_query_distinct_category(self):
    #     result = dbquery({"_distinct": "category"})
    #     print(result) # What? ['inductor', 'capacitor', 'resistor']
    #     self.assertIsInstance(result, list)
    #     self.assertGreater(len(result), 0)
    #     # Verify each element is a string
    #     for category in result:
    #         self.assertIsInstance(category, str)

    # Example in README.md
    # Calls dbquery
    @pytest.mark.integration
    def test_create_resistor(self):
        from jitxlib.parts.query_api import ResistorQuery, Resistor

        # Create a query for a resistor
        query = ResistorQuery().update(
            resistance=10e3,  # 10kΩ
            tolerance=0.01,  # 1%
            case="0603",  # 0603 package
        )

        # Create a resistor component
        with jitx._instantiation.instantiation.activate():
            resistor = Resistor(query, comp_name="TestResistor")

        build_design_from_instance(resistor, resistor.__class__.__name__)

    # Calls dbquery
    @pytest.mark.integration
    def test_insert_part(self):
        from jitxlib.parts.query_api import ResistorQuery, Resistor

        # Create a query for a resistor
        query = ResistorQuery().update(
            resistance=10e3,  # 10kΩ
            tolerance=0.01,  # 1%
            case="0603",  # 0603 package
        )

        class MyCircuit(jitx.Circuit):
            a = jitx.Port()
            b = jitx.Port()
            c = jitx.Port()

            def __init__(self):
                self.r1 = Resistor(query).insert(self.a, self.b, short_trace=True)
                self.r2 = Resistor(query).insert(self.b, self.c, short_trace=True)
                self.r3 = Resistor(query).insert(self.b, self.c, short_trace=True)

        build_circuit(MyCircuit, "test_insert_part")


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


def build_design_from_instance(instance: jitx.Component, name: str):
    """Build a design from a component and send it to the web socket.

    Args:
        instance: The component instance to build the design from
        name: Design name
    """

    class QueryCircuit(jitx.Circuit):
        components = {name: instance}

        def __init__(self):
            self.place(self.components[name], (0, 0))

    build_circuit(QueryCircuit, name)


def build_circuit(circ: type[jitx.Circuit], name: str):
    """Build a design from a component and send it to the web socket.

    Args:
        circ: The circuit class to build the design from
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="WebSocket port number")
    args, unittest_args = parser.parse_known_args()

    # Set the port in the test class
    DBQueryTest.port = args.port

    # Run unittest with remaining arguments
    unittest.main(argv=sys.argv[:1] + unittest_args)
