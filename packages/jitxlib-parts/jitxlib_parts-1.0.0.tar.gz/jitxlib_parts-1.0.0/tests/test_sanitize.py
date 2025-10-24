import unittest
from jitxlib.parts._types.landpattern import (
    PinByType,
    PinByTypeCode,
    PinByNameCode,
    PinByBundleCode,
    PinByIndexCode,
)
from jitxlib.parts._sanitize import (
    sanitize_pin,
    sanitize_defpad,
    python_component_name,
    python_landpattern_name,
    python_symbol_name,
)


class TestSanitizePinByType(unittest.TestCase):
    def test_sanitize_defpad(self):
        self.assertEqual(sanitize_defpad("smd-rec-pad"), "SmdRecPad")
        self.assertEqual(sanitize_defpad("GND"), "Gnd")
        self.assertEqual(sanitize_defpad("A_B_C"), "ABC")
        self.assertEqual(sanitize_defpad("vcc_plus"), "VccPlus")

    def test_python_component_name(self):
        self.assertEqual(python_component_name("LM311DR", ""), "LM311DR")
        self.assertEqual(python_component_name("", "C12597"), "C12597")
        self.assertEqual(python_component_name("", ""), "Comp_")
        self.assertEqual(python_component_name("12-ABC", ""), "Comp_12_ABC")
        self.assertEqual(python_component_name("9*Part", ""), "Comp_9_Part")

    def test_python_landpattern_name(self):
        self.assertEqual(python_landpattern_name("SOIC-8"), "LandpatternSOIC_8")
        self.assertEqual(python_landpattern_name("0603.Cap"), "Landpattern0603_Cap")
        self.assertEqual(python_landpattern_name(""), "Landpattern_")

    def test_python_symbol_name(self):
        self.assertEqual(python_symbol_name("VCC+"), "SymbolVCC_")
        self.assertEqual(python_symbol_name("A.B.C"), "SymbolA_B_C")
        self.assertEqual(python_symbol_name(""), "Symbol_")

    def test_pin_by_name(self):
        pin = PinByTypeCode(
            type=PinByType.pin_by_name, value=PinByNameCode(pin_name="IN+")
        )
        sanitized = sanitize_pin(pin)
        self.assertEqual(sanitized.value.pin_name, "INp")

        pin = PinByTypeCode(
            type=PinByType.pin_by_name, value=PinByNameCode(pin_name="3V3")
        )
        self.assertEqual(sanitize_pin(pin).value.pin_name, "p3V3")

        pin = PinByTypeCode(
            type=PinByType.pin_by_name, value=PinByNameCode(pin_name="GND-")
        )
        self.assertEqual(sanitize_pin(pin).value.pin_name, "GNDn")

        pin = PinByTypeCode(
            type=PinByType.pin_by_name, value=PinByNameCode(pin_name="")
        )
        self.assertEqual(sanitize_pin(pin).value.pin_name, "p")

    def test_pin_by_bundle(self):
        pin = PinByTypeCode(
            type=PinByType.pin_by_bundle,
            value=PinByBundleCode(bundle_name="A.B", pin_name="VCC+"),
        )
        sanitized = sanitize_pin(pin)
        self.assertEqual(sanitized.value.bundle_name, "A_B")
        self.assertEqual(sanitized.value.pin_name, "VCCp")

    def test_pin_by_index(self):
        pin = PinByTypeCode(
            type=PinByType.pin_by_index, value=PinByIndexCode(name="D+", index=3)
        )
        sanitized = sanitize_pin(pin)
        self.assertEqual(sanitized.value.name, "Dp")
        self.assertEqual(sanitized.value.index, 3)

        pin = PinByTypeCode(
            type=PinByType.pin_by_index, value=PinByIndexCode(name="123", index=0)
        )
        self.assertEqual(sanitize_pin(pin).value.name, "p123")

    # def test_pin_by_require(self):
    #    pin = PinByTypeCode(
    #        type=PinByType.pin_by_require,
    #        value=PinByRequireCode(bundle_name="~{RST}")
    #    )
    #    sanitized = sanitize_pin(pin)
    #    self.assertTrue(sanitized.value.bundle_name.startswith("n"))


if __name__ == "__main__":
    import sys
    import argparse
    # unittest.main()

    print(f"Running tests in {__file__}...")
    parser = argparse.ArgumentParser()
    args, unittest_args = parser.parse_known_args()

    # Run unittest with remaining arguments
    unittest.main(argv=sys.argv[:1] + unittest_args)
