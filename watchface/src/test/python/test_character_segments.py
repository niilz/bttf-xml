"""Each displayed character selects matching foreground and ghost fonts."""

import math
import pathlib
import re
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"


class TestCharacterSegments(unittest.TestCase):
    def test_every_value_branch_uses_fixed_right_aligned_character_cells(self):
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            sid = int(slot.attrib["slotId"])
            capacity = 4 if sid <= 2 else 3 if sid <= 5 else 2
            text_width = float(slot.attrib["width"]) - 8
            for complication in slot.findall("Complication"):
                if complication.attrib["type"] == "EMPTY":
                    continue
                with self.subTest(slot=sid, type=complication.attrib["type"]):
                    value = complication.find("Condition")
                    self.assertIsNotNone(value)
                    # Preserve existing battery formatting and truncation order.
                    branches = [
                        branch for branch in value.findall("Compare")
                        if not branch.attrib["expression"].endswith("_is_temperature")
                    ] + value.findall("Default")
                    self.assertEqual(len(branches), 3)
                    for branch in branches:
                        cells = branch.findall("Group")
                        self.assertEqual(len(cells), capacity)
                        for index, cell in enumerate(cells):
                            self.assertEqual(int(cell.attrib["x"]), 4 + math.floor(index * text_width / capacity))
                            self.assertEqual(int(cell.attrib["width"]), math.ceil(text_width / capacity))
                            self.assertEqual(cell.attrib["y"], "64")
                            condition = cell.find("Condition")
                            expression = condition.find("Expressions/Expression")
                            digit = condition.find("Compare")
                            other = condition.find("Default")
                            self.assertEqual(digit.attrib["expression"], expression.attrib["name"])
                            for selected, family, ghost in (
                                (digit, "dseg7_classic_bold", "8"),
                                (other, "dseg14_classic_bold", "~"),
                            ):
                                parts = selected.findall("PartText")
                                self.assertEqual(len(parts), 2)
                                self.assertEqual(parts[0].find("Text/Font").text, ghost)
                                self.assertIsNotNone(parts[0].find("Variant[@mode='AMBIENT'][@value='0']"))
                                for part in parts:
                                    self.assertEqual(part.find("Text").attrib["align"], "END")
                                    self.assertEqual(part.find("Text/Font").attrib["family"], family)
                                    self.assertEqual(part.find("Text/Font").attrib["size"], "76")
                            char_expression = digit.find(".//Parameter").attrib["expression"]
                            self.assertEqual(other.find(".//Parameter").attrib["expression"], char_expression)
                            self.assertEqual(
                                expression.text,
                                " || ".join(f'({char_expression}) == "{number}"' for number in "0123456789"),
                            )
                            # The synthetic percent must go through the same selector,
                            # not inherit the font of the battery's numeric value.
                            if branch is branches[0] and index == capacity - 1:
                                self.assertEqual(char_expression, '"%"')
                            else:
                                self.assertIn("subText([COMPLICATION.TEXT]", char_expression)
                                self.assertIn("clamp(", char_expression)
                                self.assertIn(' : ""', char_expression)

    def test_mixed_values_and_appended_percent_select_per_character(self):
        root = ET.parse(XML).getroot()
        for sid, capacity in ((1, 4), (3, 3), (6, 2)):
            value = root.find(
                f"Scene/ComplicationSlot[@slotId='{sid}']/Complication[@type='SHORT_TEXT']/Condition"
            )
            battery = next(
                branch for branch in value.findall("Compare")
                if branch.attrib["expression"].endswith("_is_batt")
            )
            ordinary = value.find("Default")
            for text, branch, formatted in (
                ("85%", ordinary, "85%"[:capacity]),
                ("-3°", ordinary, "-3°"[:capacity]),
                ("A1", ordinary, "A1"),
                ("12.5", ordinary, "12.5"[:capacity]),
                ("12345", ordinary, "12345"[:capacity]),
                ("0", ordinary, "0"),
                ("", ordinary, ""),
                ("8", battery, "8%"),
            ):
                with self.subTest(slot=sid, input=text, output=formatted):
                    actual = []
                    for cell in branch.findall("Group"):
                        expression = cell.find(".//Compare/PartText[2]//Parameter").attrib["expression"]
                        if expression == '"%"':
                            char = "%"
                        else:
                            match = re.match(
                                r"textLength\(subText\(\[COMPLICATION.TEXT\], 0, (\d+)\)\) > (\d+) \?",
                                expression,
                            )
                            self.assertIsNotNone(match)
                            limit, distance = map(int, match.groups())
                            cropped = text[:limit]
                            length = f"textLength(subText([COMPLICATION.TEXT], 0, {limit}))"
                            self.assertEqual(
                                expression,
                                f"{length} > {distance} ? subText(subText([COMPLICATION.TEXT], 0, {limit}), "
                                f"clamp({length} - {distance + 1}, 0, {limit}), "
                                f"clamp({length} - {distance}, 0, {limit})) : \"\"",
                            )
                            char = cropped[-distance - 1] if len(cropped) > distance else ""
                        actual.append((char, "7" if char in "0123456789" and char else "14"))
                    expected = [
                        (char, "7" if char in "0123456789" and char else "14")
                        for char in [""] * (capacity - len(formatted)) + list(formatted)
                    ]
                    self.assertEqual(actual, expected)

    def test_native_steps_use_numeric_foreground_and_ghosts(self):
        row = ET.parse(XML).getroot().find("Scene/Group[@name='row_2_present']")
        parts = row.findall("PartText")
        active = next(part for part in parts if part.find(".//Parameter[@expression='[STEP_COUNT]']") is not None)
        self.assertEqual(active.find("Text/Font").attrib["family"], "dseg7_classic_bold")
        ghosts = [part.find("Text/Font") for part in parts if part.find("Variant[@mode='AMBIENT']") is not None]
        self.assertTrue(any(font is not None and font.text == "88888" and font.attrib["family"] == "dseg7_classic_bold" for font in ghosts))


if __name__ == "__main__":
    unittest.main()
