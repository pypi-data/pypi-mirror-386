from jitx.via import Via, ViaType


class JLCPCBVias:
    """Various via definitions provided by JLCPCB. By default when using one of
    the substrates in this package, all vias will be available for use, be
    aware that some may incur an extra cost.

    The :py:class:`StdViaPreferred` and :py:class:`StdViaTentedFilled` vias are
    options for all boards, and as of 10/23/2024 do not have any up-charge for
    processing."""

    class StdVia(Via):
        """Standard Via with minimum pad size"""

        name = "Standard Via Aggressive - No Extra Cost"
        start_layer = 0
        stop_layer = -1
        diameter = 0.4
        hole_diameter = 0.3
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class StdViaPreferred(Via):
        """Standard Via with preferred pad size (larger)

        This via definition uses the preferred +0.15mm
        for the pad diameter which JLC-PCB recommends
        """

        name = "Standard Via - No Extra Cost"
        start_layer = 0
        stop_layer = -1
        diameter = 0.45
        hole_diameter = 0.3
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia1(Via):
        """Multi-layer (6+) via with extra cost + 1.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        first layer.
        This via definitions uses the standard +0.1mm for the pad diameter
        """

        name = "Multi-Layer Via Aggressive - Cost + 1"
        start_layer = 0
        stop_layer = -1
        diameter = 0.35
        hole_diameter = 0.25
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia1Preferred(Via):
        """Multi-layer (6+) via with extra cost + 1.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        first layer.
        This via definitions uses the preferred +0.15mm for the pad diameter
        """

        name = "Multi-Layer Via - Cost + 1"
        start_layer = 0
        stop_layer = -1
        diameter = 0.4
        hole_diameter = 0.25
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia2(Via):
        """Multi-layer (6+) via with extra cost + 2.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        second layer.
        This via definitions uses the standard +0.1mm for the pad diameter
        """

        name = "Multi-Layer Via Aggressive - Cost + 2"
        start_layer = 0
        stop_layer = -1
        diameter = 0.3
        hole_diameter = 0.2
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia2Preferred(Via):
        """Multi-layer (6+) via with extra cost + 2.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        second layer.
        This via definitions uses the preferred +0.15mm for the pad diameter
        """

        name = "Multi-Layer Via - Cost + 2"
        start_layer = 0
        stop_layer = -1
        diameter = 0.35
        hole_diameter = 0.2
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia3(Via):
        """Multi-layer (6+) via with extra cost + 3.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        third layer.
        This via definitions uses the standard +0.1mm for the pad diameter
        """

        name = "Multi-Layer Via Aggressive - Cost + 3"
        start_layer = 0
        stop_layer = -1
        diameter = 0.25
        hole_diameter = 0.15
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class MultiLayerVia3Preferred(Via):
        """Multi-layer (6+) via with extra cost + 3.

        There are multiple levels of extra cost that
        JLCPCB supports for smaller vias. This is the
        third layer.
        This via definitions uses the preferred +0.15mm for the pad diameter
        """

        name = "Multi-Layer Via - Cost + 3"
        start_layer = 0
        stop_layer = -1
        diameter = 0.3
        hole_diameter = 0.15
        type = ViaType.MechanicalDrill
        via_in_pad = False

    class StdViaTentedFilled(Via):
        """Standard Tented and Filled Via

        This via is suitable for via-in-pad applications
        and use the preferred +0.15mm for the pad diameter
        which JLC-PCB recommends
        """

        name = "Tented/Filled Standard Via"
        start_layer = 0
        stop_layer = -1
        diameter = 0.45
        hole_diameter = 0.3
        type = ViaType.MechanicalDrill
        tented = True
        filled = True
        via_in_pad = True
