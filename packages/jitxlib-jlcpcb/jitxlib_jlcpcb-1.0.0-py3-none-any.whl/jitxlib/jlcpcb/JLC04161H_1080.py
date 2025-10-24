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

from .materials import Dk_1080, Er_1080, FR4_1080, FR4_Core
from .vias import JLCPCBVias
from .rules import JLCPCBRules


cu_1oz = Conductor(thickness=0.035)
cu_halfoz = Conductor(thickness=0.0175)

med_velocity = phase_velocity((Er_1080 + 1) / 2)


class JLC04161H_1080(Substrate, JLCPCBVias):
    """JLC04161H Stackup with 1080 Prepreg"""

    @inline
    class stackup(Symmetric):
        """4 layer stackup with 1080 prepreg"""

        top = cu_1oz
        prepreg = FR4_1080(thickness=0.0764)
        inner = cu_halfoz
        core = FR4_Core(thickness=1.265)

    constraints = JLCPCBRules()

    RS_50 = RoutingStructure(
        impedance=50 * ohm,
        layers=symmetric_routing_layers(
            {
                0: RoutingStructure.Layer(
                    trace_width=0.1176,
                    clearance=0.2,
                    velocity=med_velocity,
                    insertion_loss=Dk_1080,
                )
            }
        ),
    )

    DRS_90 = DifferentialRoutingStructure(
        impedance=90 * ohm,
        name="90 Ohm Differential Routing Structure",
        layers=symmetric_routing_layers(
            {
                0: DifferentialRoutingStructure.Layer(
                    trace_width=0.09,
                    pair_spacing=0.09,
                    clearance=0.2,
                    velocity=med_velocity,
                    insertion_loss=Dk_1080,
                ),
            }
        ),
        uncoupled_region=RoutingStructure(
            impedance=90 * ohm,
            name="90 Ohm Differential Routing Structure, Uncoupled",
            layers=symmetric_routing_layers(
                {
                    0: RoutingStructure.Layer(
                        trace_width=0.09,
                        clearance=0.2,
                        velocity=med_velocity,
                        insertion_loss=Dk_1080,
                    ),
                }
            ),
        ),
    )
    DRS_100 = DifferentialRoutingStructure(
        impedance=100 * ohm,
        name="100 Ohm Differential Routing Structure",
        layers=symmetric_routing_layers(
            {
                0: DifferentialRoutingStructure.Layer(
                    trace_width=0.09,
                    pair_spacing=0.137,
                    clearance=0.2,
                    velocity=med_velocity,
                    insertion_loss=Dk_1080,
                )
            }
        ),
        uncoupled_region=RoutingStructure(
            impedance=100 * ohm,
            name="100 Ohm Differential Routing Structure, Uncoupled",
            layers=symmetric_routing_layers(
                {
                    0: RoutingStructure.Layer(
                        trace_width=0.09,
                        clearance=0.2,
                        velocity=med_velocity,
                        insertion_loss=Dk_1080,
                    )
                }
            ),
        ),
    )
