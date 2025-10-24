from jitx.substrate import FabricationConstraints


class JLCPCBRules(FabricationConstraints):
    """JLCPCB Fabrication Constraints for 1oz Copper on 4-6 layer boards."""

    # copper rules
    min_copper_width = 0.09
    min_copper_copper_space = 0.09
    min_copper_hole_space = 0.254
    min_copper_edge_space = 0.3
    # soldermask rules
    solder_mask_registration = 0.05
    min_soldermask_opening = 0.0
    min_soldermask_bridge = 0.08
    # silkscreen rules
    min_silkscreen_width = 0.153
    min_silk_solder_mask_space = 0.15
    min_silkscreen_text_height = 1.0
    # via rules
    min_annular_ring = 0.13
    min_drill_diameter = 0.3
    # pitch rules
    min_pitch_leaded = 0.127 + 0.09
    min_pitch_bga = 0.377
    # pad rules
    min_hole_to_hole = 0.5  # Pad to pad clearance (pad with hole, different nets)
    min_pth_pin_solder_clearance = 0  # Soldermask expansion - None required
    min_th_pad_expand_outer = 0.2  # Minimum Clearance -> Pad to Track
    # board size => Max dimensions under "PCB specification"
    max_board_width = 500
    max_board_height = 400
