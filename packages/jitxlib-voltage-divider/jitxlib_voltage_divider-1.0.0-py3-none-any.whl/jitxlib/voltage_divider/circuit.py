from typing import Optional

from jitx.component import Component
from jitx.circuit import Circuit
from jitx.inspect import decompose
from jitx.net import Net, Port
from jitx.toleranced import Toleranced
from jitxlib.parts.convert import convert_component

from .solver import VoltageDividerSolution, solve
from .constraints import VoltageDividerConstraints
from .inverse import InverseDividerConstraints


class VoltageDividerCircuit(Circuit):
    """
    Circuit for a voltage divider solution.
    Ports: hi, out, lo
    Instances: r_hi, r_lo
    """

    hi: Port
    out: Port
    lo: Port
    # Make those jitxlib.parts.Resistors for typed attribute accessing.
    r_hi: Component
    r_lo: Component
    nets: list[Net]
    output_voltage: Toleranced

    def __init__(self, sol: VoltageDividerSolution):
        # Ports
        self.hi = Port()
        self.out = Port()
        self.lo = Port()
        # Resistor instances
        self.r_hi = convert_component(sol.R_h.component, component_name="r_hi")()
        self.r_lo = convert_component(sol.R_l.component, component_name="r_lo")()
        # Nets (connections)
        h_p1, h_p2 = decompose(self.r_hi, Port)
        l_p1, l_p2 = decompose(self.r_lo, Port)
        self.nets = [h_p1 + self.hi, h_p2 + l_p1 + self.out, l_p2 + self.lo]
        # FIXME: Properties are a concept of JITX ESIR interface and don't have a port in the python interface.
        self.output_voltage = sol.vo


def _voltage_divider_instantiable(
    name: Optional[str] = None,
) -> type[VoltageDividerCircuit]:
    """
    Construct a voltage divider circuit instantiable from a solution.
    The returned class will have the type name set to `name` if provided.
    """
    base_class = VoltageDividerCircuit
    if name is not None:
        # Dynamically create a subclass with the given name
        return type(name, (VoltageDividerCircuit,), {})
    else:
        return base_class


def voltage_divider(
    sol: VoltageDividerSolution, name: Optional[str] = None
) -> VoltageDividerCircuit:
    """
    Construct a voltage divider circuit from a solution.
    The returned class will be an instantiable subclass of VoltageDividerCircuit.
    The returned class will have the type name set to `name` if provided.
    """
    return _voltage_divider_instantiable(name)(sol)


def voltage_divider_from_constraints(
    cxt: VoltageDividerConstraints, name: Optional[str] = None
) -> VoltageDividerCircuit:
    """
    Construct a voltage divider circuit from constraints (forward or inverse).
    """
    sol = solve(cxt)
    return voltage_divider(sol, name=name)


def forward_divider(
    v_in: Toleranced, v_out: Toleranced, current: float, name: Optional[str] = None
) -> VoltageDividerCircuit:
    """
    Construct a forward voltage divider circuit from basic parameters.
    """
    cxt = VoltageDividerConstraints(v_in=v_in, v_out=v_out, current=current)
    return voltage_divider_from_constraints(cxt, name=name)


def inverse_divider(
    v_in: Toleranced, v_out: Toleranced, current: float, name: Optional[str] = None
) -> VoltageDividerCircuit:
    """
    Construct an inverse voltage divider circuit from basic parameters.
    """
    cxt = InverseDividerConstraints(v_in=v_in, v_out=v_out, current=current)
    return voltage_divider_from_constraints(cxt, name=name)
