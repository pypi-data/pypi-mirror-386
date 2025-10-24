import unittest

import pytest
import sys
import argparse

import jitx
from jitx import Port
from jitx.inspect import decompose
import jitx._instantiation

from jitxlib.parts import (
    PartQuery,
    ResistorQuery,
    CapacitorQuery,
    Resistor,
    Part,
    Capacitor,
    search_resistors,
    search_capacitors,
    FindOptimum,
    FIND_DISTINCT,
    AuthorizedVendor,
    valid_smd_pkgs,
    SortDir,
    SortKey,
)
from jitx._websocket import set_websocket_uri
from jitx.toleranced import Toleranced
from jitx.interval import AtLeast
from jitx.sample import SampleDesign
from . import builder


class TestPartsAPI(unittest.TestCase):
    port: int

    def setUp(self):
        if hasattr(TestPartsAPI, "port"):
            set_websocket_uri(host="localhost", port=TestPartsAPI.port)

        import jitxlib.parts.commands

        jitxlib.parts.commands.ALLOW_NO_DESIGN_CONTEXT = True

    # Calls dbquery
    @pytest.mark.integration
    def test_query_api_example(self):
        """Test the comprehensive query API example from the documentation."""

        # A basic query context to build off of. Note the usage of a special value marker, FindOptimum.FIND_MINIMUM.
        # Instead of setting the parameter it is given with, it sets the 'sort!' parameter (aka '_sort' in low-level
        # query interface). This is meant to replace the OPTIMIZE-FOR functionality from OCDB.
        general_query = PartQuery(
            min_stock=1,
            quantity_needed=10,
            price=FindOptimum.FIND_MINIMUM,
            sellers=(
                AuthorizedVendor.JLCPCB,
                AuthorizedVendor.LCSC,
                AuthorizedVendor.DigiKey,
                AuthorizedVendor.Future,
                AuthorizedVendor.Mouser,
                AuthorizedVendor.Arrow,
                AuthorizedVendor.Avnet,
                AuthorizedVendor.Newark,
            ),
        )

        # A more specialized, but still basic query context to build off of.
        # This includes all parameters from the previous one.
        smd_query = general_query.update(mounting="smd", case=valid_smd_pkgs("0402"))

        # Create a ResistorQuery, which allows us to set keys specific to resistor category.
        q1 = ResistorQuery.from_query(smd_query).update(
            resistance=Toleranced(8000.0, 500.0),
            rated_power=AtLeast(0.1),
            precision=0.05,  # (5 %) - converts to tolerance = 0.05
        )

        # Variant with different resistance.
        q2 = q1.update(resistance=Toleranced(1000.0, 500.0))

        # Build the circuit with the created components
        class MainCircuit(jitx.Circuit):
            def __init__(self):
                # Create instances of the components
                self.r1_inst = Resistor(q1)
                # We can also override any key we want at the last minute.
                self.r2_inst = Resistor(q2, resistance=12000.0)
                # Here we create a resistor directly from a base query and some explicit resistor keys.
                self.r3_inst = Resistor(smd_query, resistance=100.0, rated_power=0.25)
                # Caution: here we do not use a query object, so the only keys respected are the global defaults
                # and the ones explicitly given. This may well return a through-hole resistor from a seller not on our list.
                self.r4_inst = Resistor(resistance=100.0)
                # Quickly create a component whose MPN and manufacturer are known, without regard to its category.
                self.r5_inst = Part(mpn="RT1206CRB0782RL", manufacturer="YAGEO")

                # Decompose the pins of the resistors
                r1_p1, r1_p2 = decompose(self.r1_inst, Port)
                r2_p1, r2_p2 = decompose(self.r2_inst, Port)
                r3_p1, r3_p2 = decompose(self.r3_inst, Port)
                r4_p1, r4_p2 = decompose(self.r4_inst, Port)

                # Connect the resistors in series using nets
                self.nets = [r1_p2 + r2_p1, r2_p2 + r3_p1, r3_p2 + r4_p1]

                # Add a capacitor between the first and last resistor
                cap_query = CapacitorQuery.from_query(smd_query).update(
                    type="electrolytic"
                )
                self.cap_inst = Capacitor(cap_query, capacitance=1e-6).insert(
                    r1_p1, r4_p2
                )

        # Build the design
        build_circuit(MainCircuit, "test_query_api_example")

    # Calls dbquery
    @pytest.mark.integration
    def test_search_functionality(self):
        """Test the search functionality with FindDistinct."""

        # Create the base SMD query
        general_query = PartQuery(
            price=FindOptimum.FIND_MINIMUM,
            sellers=(
                AuthorizedVendor.JLCPCB,
                AuthorizedVendor.LCSC,
                AuthorizedVendor.DigiKey,
                AuthorizedVendor.Future,
                AuthorizedVendor.Mouser,
                AuthorizedVendor.Arrow,
                AuthorizedVendor.Avnet,
                AuthorizedVendor.Newark,
            ),
        )

        smd_query = general_query.update(mounting="smd", case=valid_smd_pkgs("0402"))

        # Here we show use of the special value marker FIND_DISTINCT, which maps to '_distinct'
        # in the low-level dbquery interface. This will give us all the possible values of rated-power
        # for 1000Ω resistors with our basic smd-query parameters.
        print("searching for possible values of rated-power...")

        with jitx._instantiation.instantiation.activate():
            distinct_results = search_resistors(
                smd_query, rated_power=FIND_DISTINCT, resistance=1000.0
            )
            print(f"Distinct rated-power values: {distinct_results}")
            # Expected output: [0.0625, 0.063, 0.1, 0.125, 0.25, 0.2, 0.5, 0.333333, 0.75, 0.333, 0.6]

        # We can also just do a raw search. This will return the JSON from the lower-level dbquery call directly.
        # In this case the 'limit' keyword is helpful.
        print("Searching for 1MΩ resistors...")

        with jitx._instantiation.instantiation.activate():
            search_results = search_resistors(smd_query, resistance=1e6, limit=1)
            print(f"Search results for 1MΩ resistors: {search_results}")
            # Expected output: a boatload of json which I will not copy here

        # Verify we got some results
        self.assertIsInstance(distinct_results, list)
        self.assertIsInstance(search_results, list)
        if search_results:
            self.assertIsInstance(search_results[0], dict)

    def test_dropping_parameters(self):
        """Test that parameters are dropped when they are not valid for the query."""

        resistor_query = ResistorQuery(
            price=FindOptimum.FIND_MINIMUM,
            resistance=8000.0,
        )

        # Create a resistor query
        other_resistor_query = ResistorQuery.from_query(resistor_query)

        # Create a capacitor query
        capacitor_query = CapacitorQuery.from_query(resistor_query).update(
            type="electrolytic"
        )

        # Create a part query
        part_query = PartQuery.from_query(resistor_query).update(
            mpn="RT1206CRB0782RL", manufacturer="YAGEO"
        )

        # Check the parameters of each query
        self.assertDictEqual(
            other_resistor_query.params(),
            {
                "category": "resistor",
                "price": FindOptimum.FIND_MINIMUM,
                "resistance": 8000.0,
            },
        )
        self.assertDictEqual(
            capacitor_query.params(),
            {
                "category": "capacitor",
                "price": FindOptimum.FIND_MINIMUM,
                "type": "electrolytic",
            },
        )
        self.assertDictEqual(
            part_query.params(),
            {
                "category": "resistor",
                "price": FindOptimum.FIND_MINIMUM,
                "mpn": "RT1206CRB0782RL",
                "manufacturer": "YAGEO",
            },
        )

    # Calls dbquery
    @pytest.mark.integration
    def test_list_of_values(self):
        """Test that list of values are handled correctly."""

        with jitx._instantiation.instantiation.activate():
            mountings = search_resistors(mounting=FIND_DISTINCT)
            self.assertEqual(set(mountings), {"smd", "through-hole"})

            mountings = ["smd", "through-hole"]
            print(f"Mountings: {mountings}")
            resistor = Resistor(mounting=mountings)
            print(f"Resistor: {resistor}")

    # Calls dbquery
    @pytest.mark.integration
    def test_list_tolerances(self):
        """Test that list of tolerances are handled correctly."""

        with jitx._instantiation.instantiation.activate():
            tolerances = search_capacitors(
                tolerance=FIND_DISTINCT,
                mounting="smd",
                case="0805",
                type="ceramic",
                capacitance=2.2e-05,
                rated_voltage=6.6,
                temperature_coefficient_code="X7R",
            )
            print(f"Tolerances: {tolerances}")

            rated_voltages = search_capacitors(
                mounting="smd",
                case="0805",
                type="ceramic",
                capacitance=2.2e-05,
                rated_voltage=FIND_DISTINCT,
                temperature_coefficient_code="X7R",
            )
            print(f"Rated voltages: {rated_voltages}")

            capacitor = Capacitor(
                mounting="smd",
                case="0805",
                type="ceramic",
                capacitance=2.2e-05,
                rated_voltage=6.6,
                temperature_coefficient_code="X7R",
                tolerance=0.2,
            )
            print(f"Capacitor: {capacitor}")

    @pytest.mark.integration
    def test_sort_query_by_area(self):
        """Test sorting by area."""

        with jitx._instantiation.instantiation.activate():
            CASES = ("0402", "0603", "0805", "1206")
            capacitor_defaults = CapacitorQuery(
                case=CASES,
                sort=SortKey("area", SortDir.INCREASING),
            )

            areas = search_capacitors(capacitor_defaults, area=FIND_DISTINCT)
            print(f"Areas: {areas}")

            # Stress test, probably would timeout with the DB index for "case". Returns almost 1000 cases.
            cases = search_capacitors(capacitor_defaults, case=FIND_DISTINCT)
            print(f"Case count: {len(cases)}")

            capacitor = Capacitor(capacitor_defaults)
            smallest_area = capacitor.data.area
            print(
                f"Smallest capacitor for the 4 cases has case={capacitor.data.case} and area={smallest_area}"
            )

            case_areas = []
            for case in CASES:
                capacitor = Capacitor(capacitor_defaults, case=case)
                area = capacitor.data.area
                case_areas.append(area)
                print(f"Got capacitor with case={case} and area={area}")

            # Check that the smallest area from the sorted query matches the minimum area from individual case queries
            min_case_area = min(case_areas)
            self.assertEqual(
                smallest_area,
                min_case_area,
                f"Smallest area from sorted query ({smallest_area}) should match minimum area from case queries ({min_case_area})",
            )


def build_circuit(circuit: type[jitx.Circuit], name: str):
    """Build a design from a component and send it to the web socket.

    Args:
        circuit: The circuit class to build the design from
        name: Design name
    """

    class TestDesign(SampleDesign):
        main = circuit()

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
    TestPartsAPI.port = args.port

    # Run unittest with remaining arguments
    unittest.main(argv=sys.argv[:1] + unittest_args)
