"""RANGED_VALUE slots must survive providers that deliver an empty text.

Weather and battery data often arrive as RANGED_VALUE with the number only
in the value field. The numeric branches render
numberFormat([COMPLICATION.RANGED_VALUE_VALUE], "0.#") through the same
per-character cells as text values, including suffixes for manual labels.
"""

import pathlib
import re
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"

SOURCE = 'numberFormat([COMPLICATION.RANGED_VALUE_VALUE], "0.#")'

EXTRACTION_RE = re.compile(
    r"textLength\((?P<src>.+?)\) > (?P<distance>\d+) \? "
    r"subText\(subText\((?P=src), 0, (?P<limit>\d+)\), "
    r"textLength\(subText\((?P=src), 0, (?P=limit)\)\) - \d+, "
    r"textLength\(subText\((?P=src), 0, (?P=limit)\)\) - \d+\) : \"\""
)


class TestNumericFallback(unittest.TestCase):
    def test_ranged_value_branches_cover_empty_text(self):
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            sid = int(slot.attrib["slotId"])
            capacity = 4 if sid <= 2 else 3 if sid <= 5 else 2
            comp = slot.find("Complication[@type='RANGED_VALUE']")
            with self.subTest(slot=sid):
                value = comp.find("Condition")
                names = [c.attrib["expression"] for c in value.findall("Compare")]
                self.assertEqual(
                    names,
                    [
                        f"s{sid}_ranged_value_is_temperature_l{length}"
                        for length in range(capacity - 1, 0, -1)
                    ]
                    + [
                        f"s{sid}_ranged_value_is_batt_l{length}"
                        for length in range(capacity - 1, 0, -1)
                    ]
                    + [
                        f"s{sid}_ranged_value_is_numeric_temperature",
                        f"s{sid}_ranged_value_is_numeric_batt",
                        f"s{sid}_ranged_value_is_numeric_default",
                    ],
                )
                # 1:1 mapping required by the official DWF validator.
                defined = [e.attrib["name"] for e in value.find("Expressions")]
                self.assertEqual(defined, names)

                for numeric, suffix in (("_is_numeric_temperature", '"°"'),
                                        ("_is_numeric_batt", '"%"'),
                                        ("_is_numeric_default", None)):
                    branch = next(
                        c for c in value.findall("Compare")
                        if c.attrib["expression"].endswith(numeric)
                    )
                    guard = value.find(
                        f"Expressions/Expression[@name='s{sid}_ranged_value{numeric}']"
                    ).text
                    self.assertIn("textLength([COMPLICATION.TEXT]) == 0", guard)
                    cells = branch.findall("Group")
                    self.assertEqual(len(cells), capacity)
                    for index, cell in enumerate(cells):
                        parameters = cell.findall(".//Parameter")
                        if index == capacity - 1 and suffix is not None:
                            # Static suffix cell, as in the text branches.
                            self.assertEqual(len(parameters), 1)
                            self.assertEqual(parameters[0].attrib["expression"], suffix)
                            continue
                        expressions = [p.attrib["expression"] for p in parameters]
                        self.assertEqual(len(expressions), 2)
                        self.assertEqual(expressions[0], expressions[1])
                        match = EXTRACTION_RE.fullmatch(expressions[0])
                        self.assertIsNotNone(match, expressions[0][:120])
                        self.assertEqual(match.group("src"), SOURCE)

    def test_short_text_keeps_text_only_extraction(self):
        # SHORT_TEXT complications always carry text; a numeric fallback
        # would only add dead weight there.
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            comp = slot.find("Complication[@type='SHORT_TEXT']")
            self.assertNotIn("RANGED_VALUE_VALUE", ET.tostring(comp, encoding="unicode"))


if __name__ == "__main__":
    unittest.main()
