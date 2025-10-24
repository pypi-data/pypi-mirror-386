from jitx.container import inline
from jitx.si import (
    DifferentialRoutingStructure,
    RoutingStructure,
    symmetric_routing_layers,
)
from jitx.stackup import Conductor, Symmetric
from jitx.substrate import Substrate
from jitx.units import ohm
from jitxlib.physics import phase_velocity

from .materials import Dk_7628, Er_7628, Er_core, FR4_7628, FR4_Core
from .vias import JLCPCBVias
from .rules import JLCPCBRules

cu_1oz = Conductor(thickness=0.035)
cu_halfoz = Conductor(thickness=0.0152)

ext_velocity = phase_velocity((Er_7628 + 1) / 2)
int_velocity = phase_velocity((Er_7628 + Er_core) / 2)


class JLC06161H_7628(Substrate, JLCPCBVias):
    """JLC06161H Stackup with 7628 Prepreg"""

    @inline
    class stackup(Symmetric):
        """6 layer stackup with 7628 prepreg"""

        top = cu_1oz
        outer_prepreg = FR4_7628(thickness=0.2104)
        inner_1 = cu_halfoz
        core = FR4_Core(thickness=0.2104)
        inner_2 = cu_halfoz
        middle_prepreg = FR4_7628(thickness=0.2028)

    constraints = JLCPCBRules()

    RS_50 = RoutingStructure(
        impedance=50 * ohm,
        layers=symmetric_routing_layers(
            {
                0: RoutingStructure.Layer(
                    trace_width=0.3421,
                    clearance=0.5,
                    velocity=ext_velocity,
                    insertion_loss=Dk_7628,
                ),
                1: RoutingStructure.Layer(
                    trace_width=0.2230,
                    clearance=0.3,
                    velocity=int_velocity,
                    insertion_loss=Dk_7628,
                ),
            }
        ),
    )

    DRS_100 = DifferentialRoutingStructure(
        impedance=100 * ohm,
        layers=symmetric_routing_layers(
            {
                0: DifferentialRoutingStructure.Layer(
                    trace_width=0.1722,
                    pair_spacing=0.15,
                    clearance=0.3,
                    velocity=ext_velocity,
                    insertion_loss=Dk_7628,
                ),
                1: DifferentialRoutingStructure.Layer(
                    trace_width=0.1298,
                    pair_spacing=0.15,
                    clearance=0.3,
                    velocity=int_velocity,
                    insertion_loss=Dk_7628,
                ),
            }
        ),
        uncoupled_region=RoutingStructure(
            impedance=100 * ohm,
            layers=symmetric_routing_layers(
                {
                    0: RoutingStructure.Layer(
                        trace_width=0.1722,
                        clearance=0.15,
                        velocity=ext_velocity,
                        insertion_loss=Dk_7628,
                    ),
                    1: RoutingStructure.Layer(
                        trace_width=0.1298,
                        clearance=0.15,
                        velocity=int_velocity,
                        insertion_loss=Dk_7628,
                    ),
                }
            ),
        ),
    )
