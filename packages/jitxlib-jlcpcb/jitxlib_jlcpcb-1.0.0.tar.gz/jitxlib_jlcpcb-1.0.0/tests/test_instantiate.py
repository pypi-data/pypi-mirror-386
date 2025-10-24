import jitx.test
import jitx
import jitx.sample
from jitx._translate.design import package_design

from jitxlib.jlcpcb import JLC06161H_7628, JLC04161H_7628, JLC04161H_1080


class Main(jitx.Circuit):
    pass


class Design04161H_7628(jitx.sample.SampleDesign):
    substrate = JLC04161H_7628()
    circuit = Main()


class Design04161H_1080(jitx.sample.SampleDesign):
    substrate = JLC04161H_1080()
    circuit = Main()


class Design06161H_7628(jitx.sample.SampleDesign):
    substrate = JLC06161H_7628()
    circuit = Main()


class TestInstantiate(jitx.test.TestCase):
    def test_jlc06161h_7628(self):
        package_design(Design06161H_7628())

    def test_jlc04161h_7628(self):
        package_design(Design04161H_7628())

    def test_jlc04161h_1080(self):
        package_design(Design04161H_1080())
