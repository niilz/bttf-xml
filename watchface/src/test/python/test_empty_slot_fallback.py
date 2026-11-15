"""Unconfigured slots must render even before Wear OS sends EMPTY data."""

import pathlib
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"


def structure(element):
    # Ignore indentation, but compare all visual content and attributes.
    return (
        element.tag,
        element.attrib,
        (element.text or "").strip(),
        [structure(child) for child in element],
    )


class TestEmptySlotFallback(unittest.TestCase):
    def test_every_slot_has_a_type_guarded_scene_fallback(self):
        scene = ET.parse(XML).getroot().find("Scene")
        slots = scene.findall("ComplicationSlot")
        self.assertEqual(len(slots), 7)
        for slot in slots:
            sid = slot.attrib["slotId"]
            with self.subTest(slot=sid):
                fallback = scene.find(f"Condition/Compare/Group[@name='slot_{sid}_no_data']")
                self.assertIsNotNone(fallback)
                for key in ("x", "y", "width", "height"):
                    self.assertEqual(fallback.attrib[key], slot.attrib[key])
                empty = slot.find("Complication[@type='EMPTY']")
                self.assertEqual(
                    [structure(child) for child in fallback],
                    [structure(child) for child in empty],
                    "NO_DATA must look exactly like EMPTY, including depth and AOD",
                )
                expression = scene.find(
                    f"Condition/Expressions/Expression[@name='slot_{sid}_needs_placeholder']"
                )
                self.assertIsNotNone(expression)
                self.assertEqual(
                    expression.text,
                    f"[COMPLICATION.{sid}.TYPE] == NO_DATA || "
                    f"[COMPLICATION.{sid}.TYPE] == NOT_CONFIGURED",
                )
                condition = next(
                    condition for condition in scene.findall("Condition")
                    if condition.find(f"Compare[@expression='slot_{sid}_needs_placeholder']")
                    is not None
                )
                self.assertIsNone(condition.find("Default"))
                # Put the fallback before its slot so the system editor hitbox
                # and the live rendering stay above it in scene order.
                self.assertLess(list(scene).index(condition), list(scene).index(slot))


if __name__ == "__main__":
    unittest.main()
