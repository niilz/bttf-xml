"""Manual temperature labels own their degree suffix, independent of provider text."""

import pathlib
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"


def temperature_prefix(capacity):
    # Stop before an existing unit or intervening whitespace, then reserve
    # the final cell for our own degree sign. No inferred provider identity.
    end = str(capacity - 1)
    for index in reversed(range(capacity - 1)):
        char = f"subText([COMPLICATION.TEXT], {index}, {index + 1})"
        stop = " || ".join(f'{char} == "{separator}"' for separator in ("°", " ", "\u00a0", "\u202f"))
        end = f"({stop}) ? {index} : ({end})"
    return f"subText([COMPLICATION.TEXT], 0, {end})"


class TestTemperatureFormat(unittest.TestCase):
    def test_all_live_types_reserve_one_degree_cell_for_manual_temperature(self):
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            sid = int(slot.attrib["slotId"])
            capacity = 4 if sid <= 2 else 3 if sid <= 5 else 2
            for comp in slot.findall("Complication"):
                if comp.attrib["type"] == "EMPTY":
                    continue
                with self.subTest(slot=sid, type=comp.attrib["type"]):
                    value = comp.find("Condition")
                    name = f"s{sid}_{comp.attrib['type'].lower()}_is_temperature"
                    guard = value.find(f"Expressions/Expression[@name='{name}']")
                    self.assertIsNotNone(guard)
                    self.assertEqual(
                        guard.text,
                        f'[CONFIGURATION.slot_{sid}_label] == "s{sid}_temp" || '
                        f'[CONFIGURATION.slot_{sid}_label] == "s{sid}_feels"',
                    )
                    first_branch = value.find("Compare")
                    self.assertEqual(first_branch.attrib["expression"], name)
                    cells = first_branch.findall("Group")
                    self.assertEqual(len(cells), capacity)
                    for index, cell in enumerate(cells):
                        parameters = cell.findall(".//Parameter")
                        self.assertEqual(len(parameters), 2)
                        expression = parameters[0].attrib["expression"]
                        self.assertEqual(parameters[1].attrib["expression"], expression)
                        if index == capacity - 1:
                            self.assertEqual(expression, '"°"')
                            self.assertEqual(cell.find(".//Default/PartText/Text/Font").attrib["family"], "dseg14_classic_bold")
                        else:
                            self.assertIn(temperature_prefix(capacity), expression)
                    # Never append temperature units in the EMPTY/NO_DATA artwork.
                    empty = slot.find("Complication[@type='EMPTY']")
                    self.assertNotIn('expression="&quot;°&quot;"', ET.tostring(empty, encoding="unicode"))


if __name__ == "__main__":
    unittest.main()
