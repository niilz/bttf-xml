"""Manual temperature labels own their degree suffix, independent of provider text.

The value is never altered: flat prefix-length branches pick the first
fitting character count and render it with the same proven extraction shape
as every other value cell. (The former nested stop-detection ternaries
rendered empty on real hardware, leaving a bare degree sign.)
"""

import pathlib
import re
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"

EXTRACTION_RE = re.compile(
    r"textLength\((?P<src>.+?)\) > (?P<distance>\d+) \? "
    r"subText\(subText\((?P=src), 0, (?P<limit>\d+)\), "
    r"textLength\(subText\((?P=src), 0, (?P=limit)\)\) - \d+, "
    r"textLength\(subText\((?P=src), 0, (?P=limit)\)\) - \d+\) : \"\""
)


class TestTemperatureFormat(unittest.TestCase):
    def test_flat_prefix_length_branches(self):
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            sid = int(slot.attrib["slotId"])
            capacity = 4 if sid <= 2 else 3 if sid <= 5 else 2
            for comp in slot.findall("Complication"):
                if comp.attrib["type"] == "EMPTY":
                    continue
                t = comp.attrib["type"].lower()
                with self.subTest(slot=sid, type=comp.attrib["type"]):
                    value = comp.find("Condition")
                    compares = value.findall("Compare")
                    names = [c.attrib["expression"] for c in compares]
                    expected = [
                        f"s{sid}_{t}_is_temperature_l{length}"
                        for length in range(capacity - 1, 0, -1)
                    ] + [
                        f"s{sid}_{t}_is_batt_l{length}"
                        for length in range(capacity - 1, 0, -1)
                    ]
                    if comp.attrib["type"] == "RANGED_VALUE":
                        expected += [
                            f"s{sid}_{t}_is_numeric_temperature",
                            f"s{sid}_{t}_is_numeric_batt",
                            f"s{sid}_{t}_is_numeric_default",
                        ]
                    self.assertEqual(names, expected)

                    for position, length in enumerate(range(capacity - 1, 0, -1)):
                        name = f"s{sid}_{t}_is_temperature_l{length}"
                        guard = value.find(f"Expressions/Expression[@name='{name}']").text
                        # Label-driven, and the text must hold at least `length`
                        # non-stop characters (stops: degree sign and spaces).
                        self.assertIn(f'[CONFIGURATION.slot_{sid}_label] == "s{sid}_temp"', guard)
                        self.assertIn(f'textLength([COMPLICATION.TEXT]) >= {length}', guard)
                        for i in range(length):
                            self.assertIn(
                                f'subText([COMPLICATION.TEXT], {i}, {i + 1}) != "°"', guard
                            )
                        if length < capacity - 1:
                            # Shorter prefixes only win when the text actually
                            # ends there or a stop character follows.
                            self.assertIn(
                                f'subText([COMPLICATION.TEXT], {length}, {length + 1}) == "°"',
                                guard,
                            )
                            self.assertIn(f'textLength([COMPLICATION.TEXT]) == {length}', guard)

                        cells = compares[position].findall("Group")
                        self.assertEqual(len(cells), capacity)
                        for index, cell in enumerate(cells[:-1]):
                            parameters = cell.findall(".//Parameter")
                            self.assertEqual(len(parameters), 2)
                            expression = parameters[0].attrib["expression"]
                            self.assertEqual(parameters[1].attrib["expression"], expression)
                            match = EXTRACTION_RE.fullmatch(expression)
                            self.assertIsNotNone(match, expression[:120])
                            # The proven shape: crop to `length`, right-aligned
                            # against the reserved degree cell.
                            self.assertEqual(match.group("src"), "[COMPLICATION.TEXT]")
                            self.assertEqual(int(match.group("limit")), length)
                            self.assertEqual(int(match.group("distance")), capacity - 2 - index)
                        # Exactly one static degree cell in the 14-segment font.
                        suffix = cells[-1].findall(".//Parameter")
                        self.assertEqual(len(suffix), 1)
                        self.assertEqual(suffix[0].attrib["expression"], '"°"')
                        fonts = [
                            part.find("Text/Font").attrib["family"]
                            for part in cells[-1].findall("PartText")
                        ]
                        self.assertEqual(fonts, ["dseg14_classic_bold"] * 2)

                    # Never append temperature units in the EMPTY/NO_DATA artwork.
                    empty = slot.find("Complication[@type='EMPTY']")
                    self.assertNotIn(
                        'expression="&quot;°&quot;"',
                        ET.tostring(empty, encoding="unicode"),
                    )

    def test_no_nested_ternary_stop_detection_remains(self):
        # subText(TEXT, 0, (stop) ? 0 : ((stop) ? 1 : ...)) rendered empty on
        # real hardware; flat branches must fully replace that construct.
        self.assertNotIn("? 0 : ((", XML.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
