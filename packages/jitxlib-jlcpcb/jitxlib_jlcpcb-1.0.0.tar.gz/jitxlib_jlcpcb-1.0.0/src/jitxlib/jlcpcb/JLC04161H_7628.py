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

from jitxlib.jlcpcb.materials import Dk_7628

from .materials import Er_7628, FR4_7628, FR4_Core
from .rules import JLCPCBRules
from .vias import JLCPCBVias

cu_1oz = Conductor(thickness=0.035)
cu_halfoz = Conductor(thickness=0.0152)

med_velocity = phase_velocity((Er_7628 + 1) / 2)


class JLC04161H_7628(Substrate, JLCPCBVias):
    """JLC04161H Stackup with 7628 Prepreg"""

    @inline
    class stackup(Symmetric):
        """4 layer stackup with 7628 prepreg"""

        top = cu_1oz
        prepreg = FR4_7628(thickness=0.2104)
        inner = cu_halfoz
        core = FR4_Core(thickness=1.065)

    constraints = JLCPCBRules()

    RS_50 = RoutingStructure(
        impedance=50 * ohm,
        layers=symmetric_routing_layers(
            {
                0: RoutingStructure.Layer(
                    trace_width=0.3244,
                    clearance=0.3,
                    velocity=med_velocity,
                    insertion_loss=Dk_7628,
                )
            }
        ),
    )

    DRS_90 = DifferentialRoutingStructure(
        impedance=90 * ohm,
        layers=symmetric_routing_layers(
            {
                0: DifferentialRoutingStructure.Layer(
                    trace_width=0.2332,
                    pair_spacing=0.15,
                    clearance=0.3,
                    velocity=med_velocity,
                    insertion_loss=Dk_7628,
                )
            },
        ),
        uncoupled_region=RoutingStructure(
            impedance=90 * ohm,
            layers=symmetric_routing_layers(
                {
                    0: RoutingStructure.Layer(
                        trace_width=0.2332,
                        clearance=0.15,
                        velocity=med_velocity,
                        insertion_loss=Dk_7628,
                    )
                }
            ),
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
                    velocity=med_velocity,
                    insertion_loss=Dk_7628,
                )
            }
        ),
        uncoupled_region=RoutingStructure(
            impedance=100 * ohm,
            layers=symmetric_routing_layers(
                {
                    0: RoutingStructure.Layer(
                        trace_width=0.1722,
                        clearance=0.15,
                        velocity=med_velocity,
                        insertion_loss=Dk_7628,
                    )
                }
            ),
        ),
    )
