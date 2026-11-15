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
                    # Flat prefix-length branches: temperature strips units,
                    # battery strips spaces/percent; both append exactly one
                    # suffix. RANGED_VALUE additionally carries numeric fallbacks
                    # for providers that deliver an empty text (value-only data).
                    branches = value.findall("Compare") + value.findall("Default")
                    kinds = [
                        (f"_is_temperature_l{length}", '"°"')
                        for length in range(capacity - 1, 0, -1)
                    ] + [
                        (f"_is_batt_l{length}", '"%"')
                        for length in range(capacity - 1, 0, -1)
                    ]
                    if complication.attrib["type"] == "RANGED_VALUE":
                        kinds += [
                            ("_is_numeric_temperature", '"°"'),
                            ("_is_numeric_batt", '"%"'),
                            ("_is_numeric_default", None),
                        ]
                    kinds.append((None, None))
                    self.assertEqual(len(branches), len(kinds))
                    for branch, (kind, literal) in zip(branches, kinds):
                        if kind is None:
                            self.assertEqual(branch.tag, "Default")
                        else:
                            self.assertTrue(branch.attrib["expression"].endswith(kind))
                        cells = branch.findall("Group")
                        self.assertEqual(len(cells), capacity)
                        for index, cell in enumerate(cells):
                            self.assertEqual(int(cell.attrib["x"]), 4 + math.floor(index * text_width / capacity))
                            self.assertEqual(int(cell.attrib["width"]), math.ceil(text_width / capacity))
                            self.assertEqual(cell.attrib["y"], "64")
                            condition = cell.find("Condition")
                            if condition is None:
                                # Constant suffix cell (synthetic "%" or "°").
                                # Its selector compared a literal against digits and
                                # was therefore unreachable; the cell now statically
                                # renders the 14-segment pair, so the suffix can
                                # never inherit the numeric font.
                                self.assertEqual(index, capacity - 1)
                                self.assertIsNotNone(
                                    literal,
                                    "only suffix branches may drop the selector",
                                )
                                parts = cell.findall("PartText")
                                self.assertEqual(len(parts), 2)
                                self.assertEqual(parts[0].find("Text/Font").text, "~")
                                self.assertIsNotNone(parts[0].find("Variant[@mode='AMBIENT'][@value='0']"))
                                for part in parts:
                                    self.assertEqual(part.find("Text").attrib["align"], "END")
                                    self.assertEqual(part.find("Text/Font").attrib["family"], "dseg14_classic_bold")
                                    self.assertEqual(part.find("Text/Font").attrib["size"], "76")
                                self.assertEqual(
                                    parts[1].find(".//Parameter").attrib["expression"], literal
                                )
                                continue
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
                            # Empty cells select the simpler "8" ghost; the dense
                            # "~" shadow is reserved for letters and other non-digits.
                            self.assertEqual(
                                expression.text,
                                " || ".join(f'({char_expression}) == "{number}"' for number in "0123456789")
                                + f' || ({char_expression}) == ""',
                            )
                            # The guard already bounds the substring length, so the
                            # extraction must not carry provably redundant clamps.
                            self.assertIn("subText(", char_expression)
                            self.assertNotIn("clamp(", char_expression)
                            self.assertIn(' : ""', char_expression)

    def test_mixed_values_and_appended_percent_select_per_character(self):
        root = ET.parse(XML).getroot()
        for sid, capacity in ((1, 4), (3, 3), (6, 2)):
            value = root.find(
                f"Scene/ComplicationSlot[@slotId='{sid}']/Complication[@type='SHORT_TEXT']/Condition"
            )
            battery = next(
                branch for branch in value.findall("Compare")
                if branch.attrib["expression"].endswith("_is_batt_l1")
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
                        expression = cell.findall(".//Parameter")[0].attrib["expression"]
                        if expression == '"%"':
                            char = "%"
                        else:
                            match = re.match(
                                r"textLength\(\[COMPLICATION.TEXT\]\) > (\d+) \? "
                                r"subText\(subText\(\[COMPLICATION.TEXT\], 0, (\d+)\), ",
                                expression,
                            )
                            self.assertIsNotNone(match)
                            distance, limit = map(int, match.groups())
                            cropped = text[:limit]
                            length = f"textLength(subText([COMPLICATION.TEXT], 0, {limit}))"
                            self.assertEqual(
                                expression,
                                f"textLength([COMPLICATION.TEXT]) > {distance} ? "
                                f"subText(subText([COMPLICATION.TEXT], 0, {limit}), "
                                f"{length} - {distance + 1}, {length} - {distance}) : \"\"",
                            )
                            char = cropped[-distance - 1] if len(cropped) > distance else ""
                        actual.append((char, "7" if char == "" or char in "0123456789" else "14"))
                    expected = [
                        (char, "7" if char == "" or char in "0123456789" else "14")
                        for char in [""] * (capacity - len(formatted)) + list(formatted)
                    ]
                    self.assertEqual(actual, expected)

    def test_battery_suffix_is_label_driven_and_never_doubled(self):
        root = ET.parse(XML).getroot()
        for slot in root.findall("Scene/ComplicationSlot"):
            sid = slot.attrib["slotId"]
            capacity = 4 if sid in ("1", "2") else 3 if sid in ("3", "4", "5") else 2
            for comp in slot.findall("Complication"):
                if comp.attrib["type"] == "EMPTY":
                    continue
                with self.subTest(slot=sid, type=comp.attrib["type"]):
                    for length in range(capacity - 1, 0, -1):
                        guard = comp.find(
                            f"Condition/Expressions/Expression"
                            f"[@name='s{sid}_{comp.attrib['type'].lower()}_is_batt_l{length}']"
                        )
                        self.assertIsNotNone(guard)
                        # Provider titles are localized (e.g. German "Batterie"), so the
                        # percent suffix must also fire for the manual BATT label.
                        self.assertIn(
                            f'[CONFIGURATION.slot_{sid}_label] == "s{sid}_batt"', guard.text
                        )
                        self.assertIn('"Battery"', guard.text)
                        self.assertIn(
                            f"textLength([COMPLICATION.TEXT]) >= {length}", guard.text
                        )
                        # The prefix stops at spaces AND at an existing percent
                        # sign, so the synthetic suffix is appended exactly once
                        # and '80 %' renders flush as '80%'.
                        for i in range(length):
                            self.assertIn(
                                f'subText([COMPLICATION.TEXT], {i}, {i + 1}) != "%"',
                                guard.text,
                            )
                            self.assertIn(
                                f'subText([COMPLICATION.TEXT], {i}, {i + 1}) != " "',
                                guard.text,
                            )
                        # Battery prefixes are always bounded: longer numbers
                        # fall through to the raw Default rendering instead of
                        # being truncated into a misleading value.
                        self.assertIn(
                            f'textLength([COMPLICATION.TEXT]) == {length}', guard.text
                        )

    def test_native_steps_use_numeric_foreground_and_ghosts(self):
        row = ET.parse(XML).getroot().find("Scene/Group[@name='row_2_present']")
        parts = row.findall("PartText")
        active = next(part for part in parts if part.find(".//Parameter[@expression='[STEP_COUNT]']") is not None)
        self.assertEqual(active.find("Text/Font").attrib["family"], "dseg7_classic_bold")
        ghosts = [part.find("Text/Font") for part in parts if part.find("Variant[@mode='AMBIENT']") is not None]
        self.assertTrue(any(font is not None and font.text == "88888" and font.attrib["family"] == "dseg7_classic_bold" for font in ghosts))


if __name__ == "__main__":
    unittest.main()
