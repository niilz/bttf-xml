"""Depth styling must follow the existing geometry, including every label option."""

import pathlib
import unittest
import xml.etree.ElementTree as ET

XML = pathlib.Path(__file__).resolve().parents[2] / "main/res/raw/watchface.xml"


def rectangle_geometry(element):
    return tuple(int(element.attrib[key]) for key in ("x", "y", "width", "height"))


class TestDashboardDepth(unittest.TestCase):
    def setUp(self):
        self.root = ET.parse(XML).getroot()

    def assert_ambient_hidden(self, draw):
        self.assertIsNotNone(
            draw.find("Variant[@mode='AMBIENT'][@target='alpha'][@value='0']")
        )

    def test_all_badges_have_fitted_shadows_and_bevels(self):
        badge_count = 0
        for draw in self.root.iter("PartDraw"):
            children = list(draw)
            for badge in draw.findall("Rectangle"):
                fill = badge.find("Fill")
                if fill is None or fill.attrib["color"] not in ("#FF660000", "#FF222222"):
                    continue
                x, y, width, height = rectangle_geometry(badge)
                if height != 34:
                    continue
                badge_count += 1
                self.assert_ambient_hidden(draw)
                index = children.index(badge)
                shadow, top, bottom = children[index - 1], children[index + 1], children[index + 2]
                self.assertEqual(rectangle_geometry(shadow), (x + 1, y + 2, width, height))
                self.assertEqual(shadow.find("Fill").attrib["color"], "#60000000")
                self.assertEqual(rectangle_geometry(top), (x, y, width, 1))
                self.assertEqual(rectangle_geometry(bottom), (x, y + height - 1, width, 1))
                self.assertEqual(top.find("Fill").attrib["color"], "#20FFFFFF")
                self.assertEqual(bottom.find("Fill").attrib["color"], "#40000000")
        # All branches of all four data types, EMPTY badges, fixed headers and footers.
        self.assertEqual(badge_count, 7 * (4 * 29 + 2) + 9)

    def test_recesses_keep_the_readout_area_clear(self):
        window_count = 0
        for draw in self.root.iter("PartDraw"):
            children = list(draw)
            for box in draw.findall("Rectangle"):
                if box.find("Fill").attrib["color"] not in ("#FF260000", "#FF003300", "#FF333300"):
                    continue
                x, y, width, height = rectangle_geometry(box)
                if height != 84:
                    continue
                window_count += 1
                self.assert_ambient_hidden(draw)
                index = children.index(box)
                top, left, rim = children[index + 1:index + 4]
                self.assertEqual(rectangle_geometry(top), (x, y, width, 3))
                self.assertEqual(rectangle_geometry(left), (x, y + 3, 2, height - 3))
                self.assertEqual(rectangle_geometry(rim), (x - 1, y + height, width + 2, 1))
                self.assertEqual(top.find("Fill").attrib["color"], "#70000000")
                self.assertEqual(left.find("Fill").attrib["color"], "#40000000")
                self.assertEqual(rim.find("Fill").attrib["color"], "#30FFFFFF")
        self.assertEqual(window_count, 6 + 7 * 6)

    def test_grooves_cover_panel_width_at_bitmap_seams(self):
        groove = self.root.find("Scene/PartDraw[@name='chassis_divider_depth']")
        self.assertIsNotNone(groove)
        self.assert_ambient_hidden(groove)
        self.assertEqual(rectangle_geometry(groove), (90, 90, 720, 720))
        rects = groove.findall("Rectangle")
        self.assertEqual(
            [rectangle_geometry(rect) for rect in rects],
            [(0, 241, 720, 3), (0, 244, 720, 3), (0, 253, 720, 1),
             (0, 477, 720, 3), (0, 480, 720, 3), (0, 487, 720, 1)],
        )

    def test_indicator_depth_tracks_both_ampm_states_and_hides_in_aod(self):
        overlays = self.root.findall(".//PartDraw[@name='indicator_depth']")
        self.assertEqual(len(overlays), 6)
        for overlay in overlays:
            self.assert_ambient_hidden(overlay)
            self.assertEqual(rectangle_geometry(overlay), (468, 67, 18, 70))
            ellipses = overlay.findall("Ellipse")
            self.assertEqual(len(ellipses), 4)
            self.assertEqual(
                [rectangle_geometry(ellipse) for ellipse in ellipses],
                [(3, 23, 12, 3), (4, 13, 5, 3), (3, 55, 12, 3), (4, 45, 5, 3)],
            )


if __name__ == "__main__":
    unittest.main()
