from jitx.container import inline

from jitx.circuit import Circuit
from jitx.sample import SampleDesign
from jitxlib.parts.query_api import CapacitorQuery, ResistorQuery

from jitxexamples.components.transistors.changjiang_electronics_tech_BSS138 import (
    Device as BSS138Device,
)


class BSS138Design(SampleDesign):
    _capacitor_defaults = CapacitorQuery(case=["0402", "0603"])
    _resistor_defaults = ResistorQuery(case=["0402"])

    @inline
    class circuit(Circuit):
        mosfet = BSS138Device()

        def __init__(self):
            # The BSS138 is an N-Channel MOSFET in SOT-23 package
            # It has Drain, Gate, and Source pins
            pass
