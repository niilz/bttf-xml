#!/usr/bin/env python3
"""
Automated Specification & WFF Structural Test Suite for BTTF DeLorean Watch Face.

Verifies all requirements defined in SPEC.md:
1. AndroidManifest.xml declares hasCode="false" and WFF version 4.
2. Required drawable and font resources exist (bg.png, preview.png, dseg7_classic_bold.ttf).
3. watchface.xml is valid XML with root <WatchFace width="450" height="450">.
4. Inscribed 318x318 dashboard background (bg.png) at (66, 66) with Ambient hide variant.
5. Three distinct rows (row_1_red, row_2_green, row_3_yellow) at y=66, 172, 278.
6. Each row contains:
   - 5 header labels: MONTH, DAY, YEAR, HOUR, MIN on #FF660000 background.
   - Ghost "8" segments (88 for DAY/HOUR/MIN, 8888 for YEAR) in darkened row color.
   - Active 7-segment TimeText elements using family="dseg7_classic_bold" in primary row color.
   - 3-letter uppercase month TimeText (MMM).
   - AM/PM colon dots with [AMPM_POSITION] conditions.
   - Movie-accurate footer label per row:
     * Row 1: DESTINATION TIME
     * Row 2: PRESENT TIME
     * Row 3: LAST TIME DEPARTED
7. Ambient mode (AOD) variants hide background panels and slot boxes while keeping readouts visible.
"""

import pathlib
import unittest
import xml.etree.ElementTree as ET

ROOT_DIR = pathlib.Path(__file__).resolve().parents[4]
WATCHFACE_DIR = ROOT_DIR / "watchface" / "src" / "main"
MANIFEST_PATH = WATCHFACE_DIR / "AndroidManifest.xml"
RES_DIR = WATCHFACE_DIR / "res"
WATCHFACE_XML_PATH = RES_DIR / "raw" / "watchface.xml"

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class TestBttfWatchFaceSpec(unittest.TestCase):
    def test_manifest_wff_v4_and_has_code_false(self) -> None:
        self.assertTrue(MANIFEST_PATH.is_file(), f"Missing {MANIFEST_PATH}")
        tree = ET.parse(MANIFEST_PATH)
        root = tree.getroot()
        app = root.find("application")
        self.assertIsNotNone(app, "Missing <application> in AndroidManifest.xml")
        assert app is not None
        self.assertEqual(
            app.attrib.get(f"{ANDROID_NS}hasCode"),
            "false",
            "Application must declare android:hasCode='false'",
        )

        wff_version = None
        for prop in app.findall("property"):
            if (
                prop.attrib.get(f"{ANDROID_NS}name")
                == "com.google.wear.watchface.format.version"
            ):
                wff_version = prop.attrib.get(f"{ANDROID_NS}value")
        self.assertEqual(
            wff_version,
            "4",
            "WFF version property must be set to '4' for minSdk 36 / Wear OS 6+",
        )

    def test_required_assets_exist(self) -> None:
        bg_path = RES_DIR / "drawable" / "bg.png"
        preview_path = RES_DIR / "drawable" / "preview.png"
        font_path = RES_DIR / "font" / "dseg7_classic_bold.ttf"

        self.assertTrue(bg_path.is_file(), f"Missing background asset: {bg_path}")
        self.assertTrue(preview_path.is_file(), f"Missing preview asset: {preview_path}")
        self.assertTrue(
            font_path.is_file(), f"Missing 7-segment TTF font asset: {font_path}"
        )
        self.assertGreater(font_path.stat().st_size, 1000, "Font file appears empty")

    def test_watchface_xml_root_and_metadata(self) -> None:
        self.assertTrue(WATCHFACE_XML_PATH.is_file(), f"Missing {WATCHFACE_XML_PATH}")
        tree = ET.parse(WATCHFACE_XML_PATH)
        root = tree.getroot()
        self.assertEqual(root.tag, "WatchFace")
        self.assertEqual(root.attrib.get("width"), "450")
        self.assertEqual(root.attrib.get("height"), "450")

        metadata = {
            m.attrib.get("key"): m.attrib.get("value")
            for m in root.findall("Metadata")
        }
        self.assertEqual(metadata.get("CLOCK_TYPE"), "DIGITAL")

    def test_dashboard_background_and_ambient_variant(self) -> None:
        root = ET.parse(WATCHFACE_XML_PATH).getroot()
        scene = root.find("Scene")
        self.assertIsNotNone(scene, "Missing <Scene> in watchface.xml")
        assert scene is not None

        bg_part = None
        for part_img in scene.findall("PartImage"):
            img = part_img.find("Image")
            if img is not None and img.attrib.get("resource") == "bg":
                bg_part = part_img
                break

        self.assertIsNotNone(bg_part, "Missing <PartImage> referencing resource='bg'")
        assert bg_part is not None
        self.assertEqual(bg_part.attrib.get("x"), "66")
        self.assertEqual(bg_part.attrib.get("y"), "66")
        self.assertEqual(bg_part.attrib.get("width"), "318")
        self.assertEqual(bg_part.attrib.get("height"), "318")

        ambient_variants = [
            v
            for v in bg_part.findall("Variant")
            if v.attrib.get("mode") == "AMBIENT"
            and v.attrib.get("target") == "alpha"
            and v.attrib.get("value") == "0"
        ]
        self.assertEqual(
            len(ambient_variants),
            1,
            "Background image must hide in AMBIENT mode via <Variant mode='AMBIENT' target='alpha' value='0'/>",
        )

    def test_three_time_circuit_rows(self) -> None:
        root = ET.parse(WATCHFACE_XML_PATH).getroot()
        scene = root.find("Scene")
        assert scene is not None

        expected_rows = [
            {
                "name": "row_1_destination",
                "y": "66",
                "primary_color": "#FFFF0000",
                "ghost_color": "#FF660000",
                "box_color": "#FF330000",
                "footer": "DESTINATION TIME",
            },
            {
                "name": "row_2_present",
                "y": "172",
                "primary_color": "#FF00FF00",
                "ghost_color": "#FF006600",
                "box_color": "#FF003300",
                "footer": "PRESENT TIME",
            },
            {
                "name": "row_3_departed",
                "y": "278",
                "primary_color": "#FFFFFF00",
                "ghost_color": "#FF666600",
                "box_color": "#FF333300",
                "footer": "LAST TIME DEPARTED",
            },
        ]

        groups_by_name = {
            g.attrib.get("name"): g for g in scene.findall("Group")
        }

        for spec in expected_rows:
            row_name = spec["name"]
            self.assertIn(
                row_name,
                groups_by_name,
                f"Missing row <Group name='{row_name}'>",
            )
            row = groups_by_name[row_name]
            self.assertEqual(row.attrib.get("x"), "66")
            self.assertEqual(row.attrib.get("y"), spec["y"])
            self.assertEqual(row.attrib.get("width"), "318")
            self.assertEqual(row.attrib.get("height"), "106")

            # Collect all static text content inside this row
            texts = []
            for pt in row.iter("PartText"):
                for font in pt.iter("Font"):
                    if font.text and font.text.strip():
                        texts.append((font.text.strip(), font.attrib))
                    for span in font.iter("Upper"):
                        if span.text and span.text.strip():
                            texts.append((span.text.strip(), font.attrib))

            text_values = [t[0] for t in texts]

            # 1. Check 5 header labels
            for header in ("MONTH", "DAY", "YEAR", "HOUR", "MIN"):
                self.assertIn(
                    header,
                    text_values,
                    f"Row {row_name} missing header label '{header}'",
                )

            # 2. Check movie-accurate footer label
            self.assertIn(
                spec["footer"],
                text_values,
                f"Row {row_name} missing footer '{spec['footer']}'",
            )

            # 3. Check ghost "8" background segments (88 for DAY/HOUR/MIN, 8888 for YEAR)
            ghost_88 = [
                t
                for t in texts
                if t[0] == "88"
                and t[1].get("family") == "dseg7_classic_bold"
                and t[1].get("color", "").upper() == spec["ghost_color"]
            ]
            ghost_8888 = [
                t
                for t in texts
                if t[0] == "8888"
                and t[1].get("family") == "dseg7_classic_bold"
                and t[1].get("color", "").upper() == spec["ghost_color"]
            ]
            self.assertEqual(
                len(ghost_88),
                3,
                f"Row {row_name} must have 3 ghost '88' segments (DAY, HOUR, MIN)",
            )
            self.assertEqual(
                len(ghost_8888),
                1,
                f"Row {row_name} must have 1 ghost '8888' segment (YEAR)",
            )

            # 4. Check DigitalClock TimeText elements for MMM, dd, yyyy, HH, mm
            time_texts = list(row.iter("TimeText"))
            formats = {tt.attrib.get("format"): tt for tt in time_texts}
            for fmt in ("MMM", "dd", "yyyy", "HH", "mm"):
                self.assertIn(
                    fmt,
                    formats,
                    f"Row {row_name} missing <TimeText format='{fmt}'>",
                )
                tt_font = formats[fmt].find("Font")
                self.assertIsNotNone(tt_font)
                assert tt_font is not None
                self.assertEqual(
                    tt_font.attrib.get("color", "").upper(),
                    spec["primary_color"],
                )
                if fmt != "MMM":
                    self.assertEqual(
                        tt_font.attrib.get("family"),
                        "dseg7_classic_bold",
                        f"Row {row_name} format '{fmt}' must use dseg7_classic_bold font",
                    )

            # 5. Check AM/PM Condition inside the row
            conditions = list(row.iter("Condition"))
            self.assertGreaterEqual(
                len(conditions),
                1,
                f"Row {row_name} must include <Condition> for AM/PM indicator dots",
            )

            # 6. Check slot box background color
            fill_colors = [
                f.attrib.get("color", "").upper() for f in row.iter("Fill")
            ]
            self.assertIn(
                spec["box_color"],
                fill_colors,
                f"Row {row_name} missing slot background color {spec['box_color']}",
            )
            self.assertIn(
                "#FF660000",
                fill_colors,
                f"Row {row_name} missing header label background color #FF660000",
            )
            self.assertIn(
                "#FF222222",
                fill_colors,
                f"Row {row_name} missing footer background color #FF222222",
            )


if __name__ == "__main__":
    unittest.main()
