# JITX Parts Database

A Python interface to the JITX parts database allowing you to query and use components from the JITX parts database in your Python scripts.

## Installation

```bash
pip install jitxlib-parts
```

## Usage

```python
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
```

## Features

- Query the JITX parts database for components
- Create components from query results
- Support for resistors, capacitors, inductors, and other components
- Integration with py-jitx for use in designs

## Requirements

- Python 3.12+
- jitx package
