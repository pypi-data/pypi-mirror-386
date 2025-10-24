"""
JITX Parts Database API

This package provides a Python interface to the JITX parts database,
enabling component queries and usage in designs.

Installation
============

Requires Python 3.12+ and can be installed using pip:

.. code-block:: bash

   pip install jitxlib-parts

Usage
=====

Querying Parts
--------------

The primary interface for obtaining components involves creating query objects
and using them to instantiate parts within JITX designs.

.. code-block:: python

   from jitxlib.parts import ResistorQuery, Resistor
   from jitx.design import Design
   from jitx.units import kohm, pct

   # Create a query for a resistor
   query = ResistorQuery(
       resistance=10 * kohm,  # 10kΩ, can also provide a float like 10e3
       tolerance=1 * pct,     # 1%, can also provide a float (unit-less) like 0.01
   )
   # Create another query from an existing query.
   query_with_case = query.update(case="0603")


   class MainCircuit(Circuit):

       # All part queries have to be executed during the instantiation of a JITX design.
       def __init__ (self) :
           # Query a resistor and instantiate it.
           self.resistor = Resistor(query_with_case)

   # Use in a design
   class MyDesign(Design):
       circuit = MainCircuit()
       ...

Searching and Debugging Queries
-------------------------------

The parts database library serves as both a database explorer and parts query interface.
Search functions provide analogous interfaces to query functions but return distinct
values from the database for a given parameter. The functions ``search_resistors``,
``search_capacitors``, ``search_inductors``, and ``search_parts`` accept the same parameters
as their query counterparts, with the addition of ``FIND_DISTINCT`` to retrieve available values.

Note that search performance may be suboptimal when filtering on distinct values with
non-restrictive, unindexed filters, as these operations may require scanning the entire database.

Debugging Example
^^^^^^^^^^^^^^^^^

When a query fails, search functions can help identify valid parameter values:

.. code-block:: python

   capacitor = Capacitor(
       tolerance=20*pct,
       mounting="smd",
       case="0805",
       type="ceramic",
       capacitance=2.2e-05,
       rated_voltage=10.5,
       temperature_coefficient_code="X7R",
   ) # This triggers a runtime error because no part matches the query.

The issue can be debugged by searching for valid rated voltage values:

.. code-block:: python

   rated_voltages = search_capacitors(
       tolerance=20*pct,
       mounting="smd",
       case="0805",
       type="ceramic",
       capacitance=2.2e-05,
       rated_voltage=FIND_DISTINCT,
       temperature_coefficient_code="X7R",
   )
   print(f"Rated voltages: {rated_voltages}") # Rated voltages: [6.3, 10]

In this example, the solution is to specify a rated voltage below 10V to obtain a valid part.
MPNs can be discovered using the same approach.

Query Inheritance from Design Context
-------------------------------------

By default, calls to ``Resistor``, ``Capacitor``, ``Inductor``, and ``Part`` inherit parameters
from the closest preceding ``ResistorQuery``, ``CapacitorQuery``, ``InductorQuery``, and
``PartQuery`` objects respectively, as defined in the design context. This inheritance can be
overridden by explicitly providing a ``query: PartQuery`` argument.

.. code-block:: python

   from jitxlib.parts import (
     PartQuery,
     ResistorQuery,
     CapacitorQuery,
     Part,
     Resistor,
     Capacitor,
     FindOptimum,
     AuthorizedVendor,
   )

   class MyCircuit(jitx.Circuit):
       def __init__(self):
           # Create part with explicit empty query to override design context
           self.FDS4935BZ = Part(PartQuery(), mpn="FDS4935BZ")()
           # Require queries from design context
           resistor_query = ResistorQuery.require()
           special_resistor_query = SpecialResistorQuery.require()

           # Use explicit query with additional parameters
           self.resistor_0402 = Resistor(resistor_query, case="0402")
           # Use ResistorQuery from design context with override parameter
           self.resistor = Resistor(resistance=1000)
           # Use explicit user-defined query
           self.special_resistor = Resistor(special_resistor_query)
           # Use CapacitorQuery from design context
           self.capacitor = Capacitor()

   class SpecialResistorQuery(ResistorQuery):
       pass

   class ExampleDesign(Design):

       part_query = PartQuery(mounting="smd",
                              case=("0402", "0603"),
                              area=FindOptimum.FIND_MINIMUM)
       resistor_query = ResistorQuery.from_query(part_query).update(precision=0.01)
       special_resistor_query = SpecialResistorQuery.from_query(part_query).update(precision=0.05)
       capacitor_query = CapacitorQuery.from_query(part_query) \\
           .update(type="ceramic",
                   temperature_coefficient_code=("X7R", "X5R"),
                   tolerance_max = 0.2,
                   rated_voltage=AtLeast(0.5))

       board = ExampleBoard()
       substrate = ExampleSubstrate()
       circuit = MyCircuit()

Low-Level Parts Database API
----------------------------

Some queryable parameters in the database are not exposed in the high-level ``Part`` API.
You can use the low-level ``dbquery`` API to retrieve parts from our database as JSON.
You can then write part solvers on the low-level datastructure returned by ``to_component``
and then use ``convert_component`` to create a JITX :py:class:`~jitx.component.Component`.
Beware that those Component classes cannot be instantiated several times in a design due to technical limitations of ``convert_component``.

.. code-block:: python

   from jitxlib.parts import dbquery
   from jitxlib.parts.query_api import to_component, convert_component

   def make_part(params) :
       results = dbquery(params)
       if not len(results) >= 1:
           raise ValueError(f"No part found for params: {params}")
       part = to_component(results[0])
       component = convert_component(part.component)
       return component()

   class MyCircuit(Circuit):
       def __init__(self):
           self.led = make_part({"vendor_part_numbers.lcsc": "C2290"})
"""

# TODO: Add images in doc.
# Here's an image:

# .. image:: /_images/parts/pexels-padrinan-343457_350x350.jpg
#    :width: 100
#    :height: 100

# Here's a figure:

# .. figure:: /_images/parts/pexels-padrinan-343457_350x350.jpg
#    :scale: 90 %
#    :alt: A Circuit

#    Here we have a circuit.

from .commands import dbquery
from .query_api import (
    Resistor,
    Capacitor,
    PolarizedCapacitor,
    Inductor,
    Part,
    ResistorQuery,
    CapacitorQuery,
    InductorQuery,
    PartQuery,
    search_resistors,
    search_capacitors,
    search_inductors,
    search_parts,
    valid_smd_pkgs,
    FIND_DISTINCT,
    AuthorizedVendor,
    SortDir,
    SortKey,
    DistinctKey,
    ExistKeys,
    FindOptimum,
)

__all__ = [
    # Commands
    "dbquery",
    "Resistor",
    "Capacitor",
    "PolarizedCapacitor",
    "Inductor",
    "Part",
    "ResistorQuery",
    "CapacitorQuery",
    "InductorQuery",
    "PartQuery",
    "search_resistors",
    "search_capacitors",
    "search_inductors",
    "search_parts",
    "valid_smd_pkgs",
    "FIND_DISTINCT",
    "AuthorizedVendor",
    "SortDir",
    "SortKey",
    "DistinctKey",
    "ExistKeys",
    "FindOptimum",
]
