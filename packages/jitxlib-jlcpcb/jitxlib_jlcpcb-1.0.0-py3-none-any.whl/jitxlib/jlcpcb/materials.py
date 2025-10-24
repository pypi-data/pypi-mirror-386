from jitx.stackup import Dielectric

# ----- Prepreg -----

# From Impedance Control Specifications from JLC-PCB
Er_7628 = 4.4
Er_3314 = 4.1
Er_1080 = 3.91
Er_2116 = 4.16

# Based on data provided here:
#    https://github.com/JITx-Inc/jlc-pcb/issues/8
# I'm using an average value for each of the materials
Dk_7628 = 0.0168
Dk_3314 = 0.0168
Dk_1080 = 0.0178
Dk_2116 = 0.0168


class FR4_7628(Dielectric):
    "FR4 Prepreg 7628 - JLC PCB Specified"

    dielectric_coefficient = Er_7628  # @ 1GHz
    loss_tangent = Dk_7628  # @ 1GHz


class FR4_3314(Dielectric):
    "FR4 Prepreg 3314 - JLC PCB Specified"

    dielectric_coefficient = Er_3314  # @ 1GHz
    loss_tangent = Dk_3314  # @ 1GHz


class FR4_1080(Dielectric):
    "FR4 Prepreg 1080 - JLC PCB Specified"

    dielectric_coefficient = Er_1080  # @ 1GHz
    loss_tangent = Dk_1080  # @ 1GHz


class FR4_2116(Dielectric):
    "FR4 Prepreg 2116 - JLC PCB Specified"

    dielectric_coefficient = Er_2116  # @ 1GHz
    loss_tangent = Dk_2116  # @ 1GHz


# ----- Core -----

# From Impedance Control Specifications from JLC-PCB
Er_core = 4.6

# No Specification - This is a guess
Dk_core = 0.0168


class FR4_Core(Dielectric):
    "FR4 Core - JLC PCB Specified"

    dielectric_coefficient = Er_core  # @ 1GHz
    loss_tangent = Dk_core  # @ 1GHz
