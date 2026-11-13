# Specification: BTTF DeLorean Dashboard Watch Face (WFF XML Migration)

- **Status:** Approved & Finalized
- **Target Module:** `:watchface` (`de.niilz.watchface.bttfxml`)
- **Source Reference:** [`niilz/bttf-watchface-wearos`](https://github.com/niilz/bttf-watchface-wearos) (`tmp/template`)
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, Wear OS 6+)

---

## 1. Context & Objective

Migrate the existing Kotlin/Canvas-based Back to the Future (DeLorean Time Circuit) Wear OS watch face to the declarative **Watch Face Format (WFF)** using pure XML (`android:hasCode="false"`).

Phase 1 focuses strictly on **visual parity** with the DeLorean time-circuit aesthetic:
- Three stacked horizontal dashboard rows on the metallic circuit background (`bg.png`).
- All three rows initially render the full date/time layout (`MONTH`, `DAY`, `YEAR`, `AM/PM` colon, `HOUR`, `MIN`) in their respective row colors (Red, Green, Yellow).
- No Kotlin code, no background services, no Health Services, and no custom complication slots in Phase 1.
- Modular XML structure prepared so Row 2 can be swapped for `<ComplicationSlot>` elements in Phase 2.

---

## 2. Goals & Non-Goals

### Goals (Phase 1)
1. **Zero-Code WFF Package:** Configure `AndroidManifest.xml` (`hasCode="false"`, WFF version `4`), `res/xml/watch_face_info.xml`, and `res/raw/watchface.xml`.
2. **Authentic DeLorean Time Circuit Visuals:**
   - Metallic 3-tier background (`bg.png`) inscribed into the circular watch canvas.
   - Embossed/framed dark value boxes with darkened row-color backgrounds.
   - 7-segment digital numbers rendered via bundled 7-segment TTF font (`@font/dseg7_classic_bold`) with darkened "ghost `8`" background segments.
   - Red (`#660000`) top labels (`MONTH`, `DAY`, `YEAR`, `HOUR`, `MIN`) and dark (`#222222`) movie-accurate bottom row footers (`DESTINATION TIME`, `PRESENT TIME`, `LAST TIME DEPARTED`).
   - AM/PM indicator dots between `YEAR` and `HOUR`.
3. **Identical 3-Row Structure:** All 3 rows render the same 6-slot layout in Phase 1 (Row 1: Red `#FF0000`, Row 2: Green `#00FF00`, Row 3: Yellow `#FFFF00`).
4. **Ambient Mode Support:** Power-efficient Always-On Display (AOD) variant hiding full-surface backgrounds while keeping time circuit readouts legible.
5. **Automated XML Validation:** Test suite verifying `watchface.xml` well-formedness, WFF schema compliance, and resource references.

### Non-Goals (Phase 1)
- Custom complication slots (`ComplicationSlot`) in Row 2 (deferred to Phase 2).
- `HeartBeatService`, `HeartRateComplicationDSService`, or `DataStore` (eliminated by WFF).
- Companion/wearable configuration activities (`ComplicationConfigActivity`).

---

## 3. Technical Stack & Constraints

| Property | Value |
| :--- | :--- |
| **AGP** | `9.5.1` |
| **Compile SDK / Target SDK** | `37` |
| **Min SDK** | `36` (Wear OS 6+) |
| **WFF Version** | `4` (`com.google.wear.watchface.format.version`) |
| **Kotlin / Java Code** | Disabled (`enableKotlin = false`, `android:hasCode="false"`) |
| **Reference Canvas Size** | `900 × 900 px` (2x HiDPI supersampled circular canvas) |

---

## 4. Architecture & File Map

```text
watchface/
├── build.gradle.kts
└── src/
    ├── main/
    │   ├── AndroidManifest.xml                # WFF v4 metadata, hasCode="false"
    │   └── res/
    │       ├── drawable/
    │       │   ├── bg.png                     # 3-row metallic panel background
    │       │   ├── preview.png                # Circular preview screenshot
    │       │   ├── number_0.png .. number_9.png # 7-segment digit bitmaps (69×109)
    │       │   └── (tinted/ghost digit or font assets depending on Decision D1)
    │       ├── font/                          # Optional TTF font if D1 chooses TTF
    │       ├── raw/
    │       │   └── watchface.xml              # Declarative WFF scene graph
    │       ├── values/
    │       │   └── strings.xml                # Watch face name & static strings
    │       └── xml/
    │           └── watch_face_info.xml        # Links preview & metadata
    └── test/                                  # XML schema & structural validation tests
```

---

## 5. Visual & Layout Specification

### 5.1 Canvas, Automatic Scaling & Inscribed Dashboard Square
In Watch Face Format (WFF), `<WatchFace width="900" height="900">` defines a **2x HiDPI virtual coordinate system (reference canvas)**. Using `900 × 900` (2× the base `450 × 450` grid) ensures all offscreen `<PartText>` and `<PartDraw>` buffers are rasterized at twice the pixel density before the Wear OS WFF runtime scales the scene to the physical display resolution.

Following `MapperUtil.calcTopLeftCornerOnCirlce` from the legacy project, the square dashboard is inscribed inside the `900 × 900` reference circle (`r = 450`):
- **Inner Square Size:** $\lfloor 450 \times \sqrt{2} \rfloor = 636\text{ px}$ (`width="636"`, `height="636"`)
- **Top-Left Origin:** $x = \lfloor 450 - 636 / 2 \rfloor = 132\text{ px}$, $y = 132\text{ px}$
- **Panel Tier Height (`204 px` per grey surface between the two divider stripes in `bg.png`):**
  - **Row 1 (Red):** `y = 132`, `height = 204` (Divider 1 at `336..349`)
  - **Row 2 (Green):** `y = 349`, `height = 204` (Divider 2 at `553..564`)
  - **Row 3 (Yellow):** `y = 564`, `height = 204`

### 5.2 Color Palette & Tokens
Derived directly from `WatchFaceColors.kt`, `DrawableNumber.kt`, `DrawableColon.kt`, and `WatchFaceRenderer.kt`:

| Element | Legacy Calculation | Hex Color (ARGB) |
| :--- | :--- | :--- |
| **Header Label BG** | `LabelDefaultBackgroundColor` | `#FF660000` |
| **Header / Footer Text** | `LabelTextColor` | `#FFFFFFFF` |
| **Footer Label BG** | `LabelBackgroundColorDark` | `#FF222222` |
| **Slot Outer Frame** | `frame_color` | `#FF111111` |
| **Row 1 Primary (Red)** | `NumberColorRow1` | `#FFFF0000` |
| **Row 1 Ghost `8` (60% black blend)** | `blendARGB(#FF0000, BLACK, 0.6f)` | `#FF660000` |
| **Row 1 Box BG (80% black blend)** | `darkenColor(#FF0000, 0.8f)` | `#FF330000` |
| **Row 2 Primary (Green)** | `NumberColorRow2` | `#FF00FF00` |
| **Row 2 Ghost `8` (60% black blend)** | `blendARGB(#00FF00, BLACK, 0.6f)` | `#FF006600` |
| **Row 2 Box BG (80% black blend)** | `darkenColor(#00FF00, 0.8f)` | `#FF003300` |
| **Row 3 Primary (Yellow)** | `NumberColorRow3` | `#FFFFFF00` |
| **Row 3 Ghost `8` (60% black blend)** | `blendARGB(#FFFF00, BLACK, 0.6f)` | `#FF666600` |
| **Row 3 Box BG (80% black blend)** | `darkenColor(#FFFF00, 0.8f)` | `#FF333300` |
| **AM/PM Active Dot** | `Color.YELLOW` | `#FFFFFF00` |
| **AM/PM Inactive Dot** | `darkenColor(#FFFF00, 0.7f)` | `#FF4D4D00` |

### 5.3 Row Internal Geometry (Per Row, Relative to Row Origin `636 × 204`)
- **Digit & Letter Dimensions (`size="62"`):**
  - Both `dseg7_classic_bold.ttf` and `dseg14_classic_bold.ttf` are horizontally condensed to `advanceWidth = 613 / 1000` (`charWidth = 38 px` at `charHeight = 62 px`, with `3 px` internal sidebearing).
  - **Symmetric `4 px` Box Padding on All 4 Sides:**
    - Value Box: `y = 66`, `height = 70` (`66 .. 136`)
    - Readouts (`size="62"`): `y = 70`, `height = 62` (`70 .. 132`) → **`4 px` top & `4 px` bottom padding**
    - Box Widths (`38 × N + 2 px`): `1 px` outer margin + `3 px` internal glyph sidebearing → **`4 px` left & `4 px` right padding**
- **Vertical Bands (Equal `24 px` Top & Bottom Margin within each `204 px` panel tier):**
  - **Top Tier Margin:** `24 px` (`0 .. 24`)
  - **Header Labels (`MONTH`, `DAY`, `YEAR`, `HOUR`, `MIN`):** Badge `y = 24`, `height = 34` (Text `size = 30`, `weight = NORMAL`, `#FFFFFF` on `#660000` rect)
  - **Value Boxes:** `y = 66`, `height = 70` (Outer `#111111` frame `y = 64`, `height = 74`)
  - **Footer Label:** Badge `y = 146`, `height = 34` (Text `size = 30`, `weight = NORMAL`), horizontally centered:
    - Row 1: `DESTINATION TIME` (`x = 170`, `width = 296`)
    - Row 2: `PRESENT TIME` (`x = 202`, `width = 232`)
    - Row 3: `LAST TIME DEPARTED` (`x = 150`, `width = 336`)
  - **Bottom Tier Margin:** `24 px` (`180 .. 204`, equal to Top Tier Margin)

- **Horizontal Slot Positions (`28 px` Outer Left/Right Margin & `12 px` Inter-Slot Gaps across `636 px`):**

| Slot | Header Label | Content / Format | Char Count | Box `x` | Box `width` |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **1. Month** | `MONTH` | `<PartText>` + `<Upper><Template>%s<Parameter expression="[MONTH_S]"/></Template></Upper>` (`dseg14_classic_bold`, ghost `~~~`) | 3 | `28` | `116` |
| **2. Day** | `DAY` | `<PartText>` + `<Template>%s<Parameter expression="[DAY_Z]"/></Template>` (`dseg7_classic_bold`, ghost `88`) | 2 | `156` | `78` |
| **3. Year** | `YEAR` | `<PartText>` + `<Template>%s<Parameter expression="[YEAR]"/></Template>` (`dseg7_classic_bold`, ghost `8888`) | 4 | `246` | `154` |
| **4. Colon** | *(none)* | Upper (AM) & Lower (PM) dots (`d = 16 px`) | — | `412` | `16` |
| **5. Hour** | `HOUR` | `<DigitalClock>` + `<TimeText format="hh" hourFormat="24">` (`dseg7_classic_bold`, ghost `88`) | 2 | `440` | `78` |
| **6. Minute** | `MIN` | `<DigitalClock>` + `<TimeText format="mm">` (`dseg7_classic_bold`, ghost `88`) | 2 | `530` | `78` |

### 5.4 Component Implementation in WFF XML

1. **Dashboard Background (`bg.png`):**
   ```xml
   <PartImage x="66" y="66" width="318" height="318" alpha="255">
       <Variant mode="AMBIENT" target="alpha" value="0" />
       <Image resource="bg" />
   </PartImage>
   ```
2. **Slot Box & Header Label (`PartDraw` + `PartText`):**
   - Header background drawn via `<PartDraw><Rectangle ...><Fill color="#FF660000"/></Rectangle></PartDraw>` and centered `<PartText>` label.
   - Value box drawn via `<PartDraw>` with outer `#FF111111` frame and inner darkened row color (`#FF330000` / `#FF003300` / `#FF333300`).
3. **7-Segment Digits & Ghost Segments:**
   - **Background Layer (Ghost `8`s):** Static `<PartText>` or `<PartImage>` rendering `88` (Day/Hour/Min) or `8888` (Year) using the 7-segment font/bitmap tinted to the row's ghost color (`#FF660000` / `#FF006600` / `#FF666600`).
   - **Foreground Layer (Active Digits):** `<DigitalClock><TimeText>` or `<PartText><Text><Template>` with `[DAY_Z]`, `[YEAR]`, `[HOUR_0_23_Z]`, `[MINUTE_Z]` rendered in `#FFFF0000` / `#FF00FF00` / `#FFFFFF00` using `<BitmapFont>` (from `number_0..9.png`) or 7-segment `<Font>`.
4. **AM/PM Colon Dots:**
   - Two `<PartDraw>` circles at `cy = 40` (AM) and `cy = 56` (PM), `r = 4`.
   - Controlled via `<Condition>` on `[AMPM_POSITION] == 0` (AM active when `< 12`, PM active when `>= 12`).

---

## 6. Verification & Test Plan (TDD)

1. **XML Schema & Structural Tests:**
   - Validate `watchface/src/main/res/raw/watchface.xml` for XML well-formedness and WFF v4 tag/attribute rules.
   - Assert presence of all 3 rows, 15 header labels (`5 × 3`), 3 footer labels, AM/PM conditions, and Ambient mode variants.
   - Verify all `@drawable/...` and `@string/...` references resolve to existing files in `watchface/src/main/res/`.
2. **Build Verification:**
   - Run `./gradlew :watchface:assembleDebug` to verify AAPT2 resource compilation and APK packaging.

---

## 7. Finalized Design Decisions

- **D1 — 7-Segment & 14-Segment Digit/Month Rendering:** Bundled 14-segment TTF font (`res/font/dseg14_classic_bold.ttf`) for 3-letter `MONTH` readouts (with `~~~` ghost segments) and 7-segment TTF font (`res/font/dseg7_classic_bold.ttf`) for numeric `DAY`/`YEAR`/`HOUR`/`MIN` readouts (with `88`/`8888` ghost segments). Both fonts share identical `unitsPerEm = 1000` and `yMax = 1000` metrics, ensuring identical character height (`size="24"`, `y="32"`, `height="32"`).
- **D2 — Footer Text per Row:** Movie-accurate labels:
  - Row 1 (Red): `"DESTINATION TIME"`
  - Row 2 (Green): `"PRESENT TIME"`
  - Row 3 (Yellow): `"LAST TIME DEPARTED"`
- **D3 — Displayed Time in Rows 1, 2, 3 (Phase 1):** All 3 rows display live current date & time (`MMM`, `dd`, `yyyy`, `HH`, `mm`).
- **D4 — Ambient Mode (AOD) Behavior:** Hide `bg.png` and slot box backgrounds in Ambient mode (`alpha="0"`), keeping only the colored digits, dots, and labels on pure black `#000000` to save battery and prevent burn-in.
- **D5 — Screen Size Scaling:** Handled natively by the WFF virtual coordinate canvas (`width="450" height="450"`), which scales vector shapes, fonts, and bitmaps proportionally across all circular Wear OS screen sizes.
