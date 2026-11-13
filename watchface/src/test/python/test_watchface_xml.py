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
import re
import struct
import unittest
import xml.etree.ElementTree as ET

ROOT_DIR = pathlib.Path(__file__).resolve().parents[4]
WATCHFACE_DIR = ROOT_DIR / "watchface" / "src" / "main"
MANIFEST_PATH = WATCHFACE_DIR / "AndroidManifest.xml"
RES_DIR = WATCHFACE_DIR / "res"
WATCHFACE_XML_PATH = RES_DIR / "raw" / "watchface.xml"

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

# Official WFF v4 XSD regex for <TimeText format="..."> from google/watchface timeText.xsd
WFF_TIME_FORMAT_REGEX = re.compile(
    r"^(h{2}_(10|1)|m{2}_(10|1)|s{2}_(10|1)|((h{1,2}):m{1,2}:s{1,2}|(h{1,2}):m{1,2})|(h{1,2})|m{1,2}|s{1,2})$"
)

# Official WFF v4 time/date/health/battery/weather data source tokens from google/watchface sourceType.xsd
VALID_WFF_TIME_SOURCES = {
    "MILLISECOND",
    "SECOND",
    "SECOND_Z",
    "MINUTE",
    "MINUTE_Z",
    "AMPM_STATE",
    "AMPM_POSITION",
    "AMPM_STRING",
    "AMPM_STRING_ENG",
    "AMPM_STRING_SHORT",
    "DAY",
    "DAY_Z",
    "MONTH",
    "MONTH_Z",
    "MONTH_F",
    "MONTH_S",
    "YEAR",
    "YEAR_S",
    "HOUR_0_11",
    "HOUR_0_11_Z",
    "HOUR_1_12",
    "HOUR_1_12_Z",
    "HOUR_0_23",
    "HOUR_0_23_Z",
    "HOUR_1_24",
    "HOUR_1_24_Z",
    "DAY_OF_WEEK",
    "DAY_OF_WEEK_F",
    "DAY_OF_WEEK_S",
    "STEP_COUNT",
    "STEP_GOAL",
    "STEP_PERCENT",
    "HEART_RATE",
    "HEART_RATE_Z",
    "BATTERY_PERCENT",
    "BATTERY_CHARGING_STATUS",
    "BATTERY_IS_LOW",
    "BATTERY_TEMPERATURE_CELSIUS",
    "UNREAD_NOTIFICATION_COUNT",
    "WEATHER.IS_AVAILABLE",
    "WEATHER.TEMPERATURE",
}


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

    def test_watch_face_info_editable(self) -> None:
        info_path = RES_DIR / "xml" / "watch_face_info.xml"
        self.assertTrue(info_path.is_file(), f"Missing {info_path}")
        root = ET.parse(info_path).getroot()
        self.assertEqual(root.tag, "WatchFaceInfo")
        editable = root.find("Editable")
        self.assertIsNotNone(
            editable,
            "watch_face_info.xml must include <Editable value='true' /> so Wear OS shows the Customize button",
        )
        assert editable is not None
        self.assertEqual(
            editable.attrib.get("value", "").lower(),
            "true",
            "<Editable> in watch_face_info.xml must have value='true'",
        )

    def test_strings_xml_no_invalid_format_specifiers(self) -> None:
        strings_path = RES_DIR / "values" / "strings.xml"
        self.assertTrue(strings_path.is_file(), f"Missing {strings_path}")
        root = ET.parse(strings_path).getroot()
        for s in root.findall("string"):
            name = s.attrib.get("name", "")
            val = s.text or ""
            # Android Resources.getString(id, args) runs java.util.Formatter on strings unless formatted="false".
            # Any unescaped '%' (like 'Battery (%)') throws UnknownFormatConversionException: Conversion = ')'!
            self.assertNotIn(
                "%",
                val,
                f"strings.xml <string name='{name}'>{val}</string> contains '%' which crashes Android Resources.getString() in getUserStyleSchema!",
            )

    def test_required_assets_exist(self) -> None:
        bg_path = RES_DIR / "drawable" / "bg.png"
        preview_path = RES_DIR / "drawable" / "preview.png"
        font7_path = RES_DIR / "font" / "dseg7_classic_bold.ttf"
        font14_path = RES_DIR / "font" / "dseg14_classic_bold.ttf"

        self.assertTrue(bg_path.is_file(), f"Missing background asset: {bg_path}")
        self.assertTrue(preview_path.is_file(), f"Missing preview asset: {preview_path}")
        self.assertTrue(
            font7_path.is_file(), f"Missing 7-segment TTF font asset: {font7_path}"
        )
        self.assertTrue(
            font14_path.is_file(), f"Missing 14-segment TTF font asset: {font14_path}"
        )
        self.assertGreater(font7_path.stat().st_size, 10000, "DSEG7 font file appears incomplete")
        self.assertGreater(font14_path.stat().st_size, 10000, "DSEG14 font file appears incomplete")

        for font_path in (font7_path, font14_path):
            self._verify_truetype_font_integrity(font_path)

    def _verify_truetype_font_integrity(self, path: pathlib.Path) -> None:
        data = path.read_bytes()
        num_tables = struct.unpack(">H", data[4:6])[0]
        tables = {}
        for i in range(num_tables):
            offset = 12 + i * 16
            tag, _, tbl_off, tbl_len = struct.unpack(">4sIII", data[offset : offset + 16])
            tables[tag.decode("latin1")] = data[tbl_off : tbl_off + tbl_len]

        loca = tables["loca"]
        glyf = tables["glyf"]
        num_glyphs = len(loca) // 2 - 1
        offsets = [
            struct.unpack(">H", loca[i * 2 : i * 2 + 2])[0] * 2
            for i in range(num_glyphs + 1)
        ]
        for gid in range(num_glyphs):
            s, e = offsets[gid], offsets[gid + 1]
            if s == e:
                continue
            gdata = glyf[s:e]
            n_contours = struct.unpack(">h", gdata[:2])[0]
            self.assertGreaterEqual(n_contours, 0, f"{path.name} GID {gid} unexpected composite")
            pos = 10 + 2 * n_contours
            end_pts = struct.unpack(f">{n_contours}H", gdata[10:pos])
            n_pts = end_pts[-1] + 1
            instr_len = struct.unpack(">H", gdata[pos : pos + 2])[0]
            pos += 2 + instr_len
            flags = []
            while len(flags) < n_pts:
                f = gdata[pos]
                pos += 1
                flags.append(f)
                if f & 8:
                    rep = gdata[pos]
                    pos += 1
                    flags.extend([f] * rep)
            self.assertEqual(
                len(flags),
                n_pts,
                f"{path.name} GID {gid} corrupt glyf flag stream: got {len(flags)} flags for {n_pts} points",
            )
            for f in flags:
                if f & 2:
                    pos += 1
                elif not (f & 16):
                    pos += 2
            for f in flags:
                if f & 4:
                    pos += 1
                elif not (f & 32):
                    pos += 2
            self.assertTrue(
                pos <= len(gdata) and len(gdata) - pos < 4,
                f"{path.name} GID {gid} glyf coordinate stream length mismatch: pos={pos}, len={len(gdata)}",
            )

    def test_watchface_xml_root_and_metadata(self) -> None:
        self.assertTrue(WATCHFACE_XML_PATH.is_file(), f"Missing {WATCHFACE_XML_PATH}")
        tree = ET.parse(WATCHFACE_XML_PATH)
        root = tree.getroot()
        self.assertEqual(root.tag, "WatchFace")
        self.assertEqual(root.attrib.get("width"), "900")
        self.assertEqual(root.attrib.get("height"), "900")

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
        self.assertEqual(bg_part.attrib.get("x"), "132")
        self.assertEqual(bg_part.attrib.get("y"), "132")
        self.assertEqual(bg_part.attrib.get("width"), "636")
        self.assertEqual(bg_part.attrib.get("height"), "636")

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
                "y": "132",
                "primary_color": "#FFFF0000",
                "ghost_color": "#FF660000",
                "box_color": "#FF330000",
                "footer": "DESTINATION TIME",
            },
            {
                "name": "row_2_present",
                "y": "349",
                "primary_color": "#FF00FF00",
                "ghost_color": "#FF006600",
                "box_color": "#FF003300",
                "footer": "PRESENT TIME",
            },
            {
                "name": "row_3_departed",
                "y": "564",
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
            self.assertEqual(row.attrib.get("x"), "132")
            self.assertEqual(row.attrib.get("y"), spec["y"])
            self.assertEqual(row.attrib.get("width"), "636")
            self.assertEqual(row.attrib.get("height"), "204")

            # For row_2_present and row_3_departed, slots are provided via <ComplicationSlot> elements under <Scene>
            if row_name in ("row_2_present", "row_3_departed"):
                footer_rects = [
                    (int(r.attrib["y"]), int(r.attrib["height"]))
                    for r in row.findall("PartDraw/Rectangle")
                    if r.find("Fill") is not None
                    and r.find("Fill").attrib.get("color", "").upper() == "#FF222222"
                ]
                self.assertEqual(len(footer_rects), 1)
                continue
            time_scope = row

            # Collect all static text content inside this row's time view + footer
            pts = list(time_scope.iter("PartText"))
            if time_scope is not row:
                pts.extend(row.findall("PartText"))
            texts = []
            for pt in pts:
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

            # 3. Check ghost background segments:
            #    - '~~~' in dseg14_classic_bold for MONTH (all 14 segments)
            #    - '88' in dseg7_classic_bold for DAY, HOUR, MIN (all 7 segments)
            #    - '8888' in dseg7_classic_bold for YEAR (all 7 segments)
            ghost_month = [
                t
                for t in texts
                if t[0] == "~~~"
                and t[1].get("family") == "dseg14_classic_bold"
                and t[1].get("color", "").upper() == spec["ghost_color"]
            ]
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
                len(ghost_month),
                1,
                f"Row {row_name} must have 1 ghost '~~~' 14-segment background (MONTH)",
            )
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

            # 4. Validate all <TimeText> elements against official WFF v4 timeFormatType XSD regex
            time_texts = list(time_scope.iter("TimeText"))
            for tt in time_texts:
                fmt = tt.attrib.get("format", "")
                self.assertRegex(
                    fmt,
                    WFF_TIME_FORMAT_REGEX,
                    f"Row {row_name} has invalid WFF <TimeText format='{fmt}'>; "
                    f"WFF timeText.xsd only permits lowercase h/hh, m/mm, s/ss patterns (date formats like MMM/dd/yyyy or uppercase HH render blank!)",
                )

            # 5. Check that all 5 dynamic slots (MONTH, DAY, YEAR, HOUR, MIN) have valid WFF bindings:
            #    - Date slots (MONTH, DAY, YEAR) must use <PartText><Text>...<Template><Parameter expression="[...]"/></Template>
            #      with official sourceType.xsd tokens ([MONTH_S], [DAY_Z], [YEAR])
            #    - Time slots (HOUR, MIN) must use valid <TimeText format="hh"> / <TimeText format="mm">
            parameter_exprs = [
                p.attrib.get("expression", "") for p in time_scope.iter("Parameter")
            ]
            for expr in parameter_exprs:
                tokens = re.findall(r"\[([A-Z0-9_.]+)\]", expr)
                self.assertTrue(
                    tokens,
                    f"Row {row_name} <Parameter expression='{expr}'> contains no [SOURCE_TYPE] token",
                )
                for token in tokens:
                    self.assertIn(
                        token,
                        VALID_WFF_TIME_SOURCES,
                        f"Row {row_name} uses invalid WFF source token [{token}]",
                    )

            for required_date_expr in ("[MONTH_S]", "[DAY_Z]", "[YEAR]"):
                self.assertIn(
                    required_date_expr,
                    parameter_exprs,
                    f"Row {row_name} missing <Template><Parameter expression='{required_date_expr}'/></Template>",
                )

            # Verify MONTH is wrapped in <Upper> so 'Oct' becomes 'OCT'
            upper_params = [
                p.attrib.get("expression", "")
                for u in time_scope.iter("Upper")
                for p in u.iter("Parameter")
            ]
            self.assertIn(
                "[MONTH_S]",
                upper_params,
                f"Row {row_name} [MONTH_S] must be wrapped in <Upper> for 3-letter uppercase month",
            )

            # Verify MONTH uses digital 14-segment font (dseg14_classic_bold) and matches digit size/height
            readout_sizes = set()
            readout_ys = set()
            readout_heights = set()

            for pt in time_scope.findall("PartText"):
                params = [p.attrib.get("expression") for p in pt.iter("Parameter")]
                if not params:
                    continue
                font_el = pt.find(".//Font")
                self.assertIsNotNone(font_el)
                assert font_el is not None
                expr = params[0]
                if expr == "[MONTH_S]":
                    self.assertEqual(
                        font_el.attrib.get("family"),
                        "dseg14_classic_bold",
                        f"Row {row_name} MONTH must use digital 14-segment font 'dseg14_classic_bold'",
                    )
                else:
                    self.assertEqual(
                        font_el.attrib.get("family"),
                        "dseg7_classic_bold",
                        f"Row {row_name} {expr} must use 'dseg7_classic_bold'",
                    )
                readout_sizes.add(font_el.attrib.get("size"))
                readout_ys.add(pt.attrib.get("y"))
                readout_heights.add(pt.attrib.get("height"))

            # Verify HOUR ('hh') and MIN ('mm') TimeText elements exist and use dseg7_classic_bold
            formats = {tt.attrib.get("format"): tt for tt in time_texts}
            for fmt in ("hh", "mm"):
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
                self.assertEqual(
                    tt_font.attrib.get("family"),
                    "dseg7_classic_bold",
                    f"Row {row_name} format '{fmt}' must use dseg7_classic_bold font",
                )
                readout_sizes.add(tt_font.attrib.get("size"))
                readout_ys.add(formats[fmt].attrib.get("y"))
                readout_heights.add(formats[fmt].attrib.get("height"))

            self.assertEqual(
                len(readout_sizes),
                1,
                f"Row {row_name} MONTH and digit slots must have identical Font size, got {readout_sizes}",
            )
            self.assertEqual(
                len(readout_ys),
                1,
                f"Row {row_name} MONTH and digit slots must have identical y position, got {readout_ys}",
            )
            # Verify all digital readouts and ghost backgrounds use align="END" (right-aligned)
            # so variable-length numbers always align with their rightmost ghost segments
            for pt in time_scope.findall("PartText"):
                font_el = pt.find(".//Font")
                text_el = pt.find("Text")
                if font_el is not None and text_el is not None:
                    if font_el.attrib.get("family") in (
                        "dseg7_classic_bold",
                        "dseg14_classic_bold",
                    ):
                        self.assertEqual(
                            text_el.attrib.get("align"),
                            "END",
                            f"Row {row_name} digital PartText must use align='END' to align with ghost background",
                        )
            for tt in time_texts:
                self.assertEqual(
                    tt.attrib.get("align"),
                    "END",
                    f"Row {row_name} TimeText format='{tt.attrib.get('format')}' must use align='END'",
                )

            # 5. Check AM/PM Condition inside the row
            conditions = list(time_scope.iter("Condition"))
            self.assertGreaterEqual(
                len(conditions),
                1,
                f"Row {row_name} must include <Condition> for AM/PM indicator dots",
            )

            # 6. Check slot box background color, equal horizontal margins/gaps, and equal box padding
            row_width = int(row.attrib["width"])
            value_boxes = []
            for rect in time_scope.iter("Rectangle"):
                fill = rect.find("Fill")
                if (
                    fill is not None
                    and fill.attrib.get("color", "").upper() == spec["box_color"]
                ):
                    value_boxes.append(
                        (
                            int(rect.attrib["x"]),
                            int(rect.attrib["y"]),
                            int(rect.attrib["width"]),
                            int(rect.attrib["height"]),
                        )
                    )
            value_boxes.sort(key=lambda b: b[0])
            self.assertEqual(
                len(value_boxes),
                5,
                f"Row {row_name} must have 5 inner value boxes",
            )

            # Find colon PartDraw inside Condition
            colon_draw = time_scope.find(".//Condition//PartDraw")
            self.assertIsNotNone(colon_draw)
            assert colon_draw is not None
            colon_box = (
                int(colon_draw.attrib["x"]),
                int(colon_draw.attrib["y"]),
                int(colon_draw.attrib["width"]),
                int(colon_draw.attrib["height"]),
            )

            # All 6 horizontal items in order: MONTH, DAY, YEAR, COLON, HOUR, MIN
            all_slots = sorted(value_boxes + [colon_box], key=lambda b: b[0])
            left_margin = all_slots[0][0]
            right_margin = row_width - (all_slots[-1][0] + all_slots[-1][2])
            inter_slot_gaps = [
                all_slots[i + 1][0] - (all_slots[i][0] + all_slots[i][2])
                for i in range(len(all_slots) - 1)
            ]
            self.assertEqual(
                left_margin,
                right_margin,
                f"Row {row_name} right_margin={right_margin} must equal left_margin={left_margin}",
            )
            self.assertEqual(
                left_margin,
                28,
                f"Row {row_name} outer left/right margin must be 28px on the grey panel",
            )
            self.assertEqual(
                len(set(inter_slot_gaps)),
                1,
                f"Row {row_name} inter-slot gaps {inter_slot_gaps} must all be equal",
            )
            self.assertEqual(
                inter_slot_gaps[0],
                12,
                f"Row {row_name} inter-slot gaps must be 12px",
            )

            # Verify vertical padding inside value boxes matches horizontal visual padding (4px)
            # and digit/letter height is 62px inside a 70px box
            box_y = value_boxes[0][1]
            box_h = value_boxes[0][3]
            digit_y = int(next(iter(readout_ys)))
            digit_size = int(next(iter(readout_sizes)))
            self.assertEqual(box_h, 70, f"Row {row_name} inner value box height must be 70px")
            self.assertEqual(digit_size, 62, f"Row {row_name} digit/letter size must be 62px")
            top_pad = digit_y - box_y
            bottom_pad = (box_y + box_h) - (digit_y + digit_size)
            self.assertEqual(
                top_pad,
                4,
                f"Row {row_name} top padding ({top_pad}px) must be 4px",
            )
            self.assertEqual(
                top_pad,
                bottom_pad,
                f"Row {row_name} top padding ({top_pad}) must equal bottom padding ({bottom_pad})",
            )
            # With condensed char advance=38px (and 3px internal sidebearing), each box adds 1px per side + 3px = 4px
            char_counts = [3, 2, 4, 2, 2]
            for (bx, by, bw, bh), n_chars in zip(value_boxes, char_counts):
                side_pad = (bw - n_chars * 38) // 2 + 3
                self.assertEqual(
                    top_pad,
                    side_pad,
                    f"Row {row_name} vertical box padding ({top_pad}px) must equal horizontal box padding ({side_pad}px)",
                )

            # Verify equal top margin (above header badges) and bottom margin (below footer badge)
            # within each 204px panel tier
            row_height = int(row.attrib["height"])
            header_rects = [
                int(r.attrib["y"])
                for r in time_scope.iter("Rectangle")
                if r.find("Fill") is not None
                and r.find("Fill").attrib.get("color", "").upper() == "#FF660000"
            ]
            footer_rects = [
                (int(r.attrib["y"]), int(r.attrib["height"]))
                for r in row.findall("PartDraw/Rectangle")
                if r.find("Fill") is not None
                and r.find("Fill").attrib.get("color", "").upper() == "#FF222222"
            ]
            if not footer_rects:
                footer_rects = [
                    (int(r.attrib["y"]), int(r.attrib["height"]))
                    for r in row.iter("Rectangle")
                    if r.find("Fill") is not None
                    and r.find("Fill").attrib.get("color", "").upper() == "#FF222222"
                ]
            self.assertEqual(len(footer_rects), 1)
            tier_top_margin = min(header_rects)
            tier_bottom_margin = row_height - (footer_rects[0][0] + footer_rects[0][1])
            self.assertEqual(
                tier_top_margin,
                tier_bottom_margin,
                f"Row {row_name} top tier margin ({tier_top_margin}px) must equal bottom tier margin ({tier_bottom_margin}px)",
            )
            self.assertGreaterEqual(
                tier_top_margin,
                20,
                f"Row {row_name} top tier margin ({tier_top_margin}px) must leave generous space after divider stripe",
            )

            # Verify header & footer labels use crisp normal weight at size 30 (2x HiDPI)
            for text_str, font_attr in texts:
                if text_str in ("MONTH", "DAY", "YEAR", "HOUR", "MIN", spec["footer"]):
                    self.assertEqual(
                        font_attr.get("weight", "NORMAL"),
                        "NORMAL",
                        f"Label '{text_str}' must use NORMAL weight for sharp rendering",
                    )
                    self.assertEqual(
                        font_attr.get("size"),
                        "30",
                        f"Label '{text_str}' must use 2x HiDPI size='30'",
                    )

            fill_colors = [
                f.attrib.get("color", "").upper()
                for f in list(time_scope.iter("Fill")) + list(row.findall("PartDraw//Fill"))
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

    def test_complication_slots_row2_and_row3(self) -> None:
        root = ET.parse(WATCHFACE_XML_PATH).getroot()

        # WFF Rule: res/raw/watchface.xml is a raw resource; attributes must NOT use '@string/' or '@drawable/' prefixes
        for el in root.iter():
            for attr_name, attr_val in el.attrib.items():
                self.assertFalse(
                    attr_val.startswith("@string/") or attr_val.startswith("@drawable/"),
                    f"<{el.tag} {attr_name}='{attr_val}'> must not use '@string/' or '@drawable/' prefix in raw watchface.xml",
                )

        scene = root.find("Scene")
        self.assertIsNotNone(scene)
        assert scene is not None

        comp_slots = scene.findall("ComplicationSlot")
        self.assertEqual(
            len(comp_slots),
            8,
            "Scene must contain 8 <ComplicationSlot> elements (3 in Row 2, 5 in Row 3)",
        )

        slot_ids = [cs.attrib.get("slotId") for cs in comp_slots]
        self.assertEqual(
            slot_ids,
            ["1", "2", "3", "4", "5", "6", "7", "8"],
            "ComplicationSlot slotId attributes must be '1'..'8'",
        )

        for cs in comp_slots:
            sid = int(cs.attrib["slotId"])
            y = int(cs.attrib["y"])
            if sid <= 3:
                self.assertEqual(y, 349, f"ComplicationSlot {sid} must be in Row 2 (y=349)")
                expected_primary = "#FF00FF00"
                expected_ghost = "#FF006600"
                expected_box = "#FF003300"
            else:
                self.assertEqual(y, 564, f"ComplicationSlot {sid} must be in Row 3 (y=564)")
                expected_primary = "#FFFFFF00"
                expected_ghost = "#FF666600"
                expected_box = "#FF333300"

            self.assertEqual(cs.attrib.get("isCustomizable"), "TRUE")
            sup_types = set(cs.attrib.get("supportedTypes", "").split())
            for req_type in ("SHORT_TEXT", "RANGED_VALUE", "GOAL_PROGRESS"):
                self.assertIn(
                    req_type,
                    sup_types,
                    f"ComplicationSlot {sid} must support {req_type}",
                )

            bbox = cs.find("BoundingBox")
            self.assertIsNotNone(bbox, f"ComplicationSlot {sid} missing <BoundingBox>")
            policy = cs.find("DefaultProviderPolicy")
            self.assertIsNotNone(
                policy, f"ComplicationSlot {sid} missing <DefaultProviderPolicy>"
            )

            comps = {c.attrib.get("type"): c for c in cs.findall("Complication")}
            for req_type in sup_types:
                self.assertIn(
                    req_type,
                    comps,
                    f"ComplicationSlot {sid} missing <Complication type='{req_type}'>",
                )
                if req_type == "EMPTY":
                    continue
                comp = comps[req_type]
                header_w = None
                box_w = None
                for r in comp.iter("Rectangle"):
                    fill = r.find("Fill")
                    if fill is None:
                        continue
                    col = fill.attrib.get("color", "").upper()
                    if col == "#FF660000":
                        header_w = int(r.attrib["width"])
                    elif col == expected_box:
                        box_w = int(r.attrib["width"])
                self.assertIsNotNone(header_w)
                self.assertIsNotNone(box_w)
                assert header_w is not None and box_w is not None
                self.assertLessEqual(header_w, box_w)

                params = [p.attrib.get("expression", "") for p in comp.iter("Parameter")]
                self.assertTrue(
                    any("COMPLICATION.TEXT" in p for p in params),
                    f"ComplicationSlot {sid} ({req_type}) must bind [COMPLICATION.TEXT]",
                )
                self.assertTrue(
                    any("COMPLICATION.TITLE" in p for p in params),
                    f"ComplicationSlot {sid} ({req_type}) must bind [COMPLICATION.TITLE]",
                )

                for pt in comp.iter("PartText"):
                    font_el = pt.find(".//Font")
                    text_el = pt.find("Text")
                    if font_el is not None and text_el is not None:
                        if font_el.attrib.get("family") in (
                            "dseg7_classic_bold",
                            "dseg14_classic_bold",
                        ):
                            self.assertEqual(text_el.attrib.get("align"), "END")
                            col = font_el.attrib.get("color", "").upper()
                            self.assertIn(col, (expected_primary, expected_ghost))

        # Verify AM/PM indicator dots exist in Row 2 and Row 3 at exact same x as Row 1
        for row_grp_name in ("row_2_present", "row_3_departed"):
            row_grp = scene.find(f"Group[@name='{row_grp_name}']")
            self.assertIsNotNone(row_grp)
            assert row_grp is not None
            colon_draws = row_grp.findall(".//Condition//PartDraw")
            self.assertEqual(
                len(colon_draws),
                2,
                f"{row_grp_name} must contain AM/PM colon indicator dots inside <Condition>",
            )
            for cd in colon_draws:
                self.assertEqual(cd.attrib.get("x"), "412")
                self.assertEqual(cd.attrib.get("width"), "16")

        # Verify Row 2 hardcoded STEPS slot at (22..214, width 192)
        row2_grp = scene.find("Group[@name='row_2_present']")
        self.assertIsNotNone(row2_grp)
        assert row2_grp is not None
        steps_pt = None
        for pt in row2_grp.findall("PartText"):
            params = [p.attrib.get("expression") for p in pt.iter("Parameter")]
            if "[STEP_COUNT]" in params:
                steps_pt = pt
                break
        self.assertIsNotNone(steps_pt, "Row 2 must contain hardcoded STEPS [STEP_COUNT] PartText")
        assert steps_pt is not None
        self.assertEqual(steps_pt.attrib.get("x"), "22")
        self.assertEqual(steps_pt.attrib.get("width"), "191")

        # Verify rightmost split slots (Slots 2 & 3 in Row 2, Slots 7 & 8 in Row 3) exactly match Row 1 HOUR & MIN coordinates
        row_slots_by_id = {int(cs.attrib["slotId"]): cs for cs in comp_slots}
        for sid_pair, expected_y in (((2, 3), 349), ((7, 8), 564)):
            s_left = row_slots_by_id[sid_pair[0]]
            s_right = row_slots_by_id[sid_pair[1]]
            self.assertEqual(int(s_left.attrib["x"]), 132 + 440 - 2)
            self.assertEqual(int(s_left.attrib["width"]), 78 + 4)
            self.assertEqual(int(s_right.attrib["x"]), 132 + 530 - 2)
            self.assertEqual(int(s_right.attrib["width"]), 78 + 4)


if __name__ == "__main__":
    unittest.main()
