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
| **Reference Canvas Size** | `450 × 450 px` (circular) |

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
In Watch Face Format (WFF), `<WatchFace width="450" height="450">` defines a **virtual coordinate system (reference canvas)**. The Wear OS WFF runtime **automatically scales** all coordinates, shapes, images, and fonts proportionally to the physical pixel resolution of the target watch display (e.g., 384×384, 450×450, 480×480).

Following `MapperUtil.calcTopLeftCornerOnCirlce` from the legacy project, the square dashboard is inscribed inside the `450 × 450` reference circle (`r = 225`):
- **Inner Square Size:** $\lfloor 225 \times \sqrt{2} \rfloor = 318\text{ px}$ (`width="318"`, `height="318"`)
- **Top-Left Origin:** $x = \lfloor 225 - 318 / 2 \rfloor = 66\text{ px}$, $y = 66\text{ px}$
- **Row Height:** $318 / 3 = 106\text{ px}$ per row:
  - **Row 1 (Red):** `y = 66`, `height = 106`
  - **Row 2 (Green):** `y = 172`, `height = 106`
  - **Row 3 (Yellow):** `y = 278`, `height = 106`

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

### 5.3 Row Internal Geometry (Per Row, Relative to Row Origin `318 × 106`)
Derived from `DrawService.updateNumbers(maxNumbersPerRow=19, maxNumbersPerCol=10)` and `DrawableSlot`:
- **Digit Dimensions:**
  - `charWidth` = $\lfloor 318 / 19 \rfloor \approx 16\text{ px}$
  - `charHeight` = $\lfloor 318 / 10 \rfloor \approx 32\text{ px}$
  - Intra-digit `gap` = $2\text{ px}$, box `padding` = $4\text{ px}$
- **Vertical Bands (within each `106 px` row):**
  - **Header Labels (`MONTH`, `DAY`, `YEAR`, `HOUR`, `MIN`):** `y = 6`, `height = 18` (Text `size = 13`, `#FFFFFF` on `#660000` rect)
  - **Value Boxes:** `y = 28`, `height = 40` (Digits at `y = 32`, `height = 32`)
  - **Footer Label:** `y = 74`, `height = 18`, horizontally centered:
    - Row 1: `DESTINATION TIME` (`x = 89`, `width = 140`)
    - Row 2: `PRESENT TIME` (`x = 104`, `width = 110`)
    - Row 3: `LAST TIME DEPARTED` (`x = 79`, `width = 160`)

- **Horizontal Slot Positions (within `318 px` width):**

| Slot | Header Label | Content / Format | Char Count | Box `x` | Box `width` |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **1. Month** | `MONTH` | 3-letter uppercase month (`MMM`) | 3 | `7` | `60` |
| **2. Day** | `DAY` | 2-digit day of month (`dd`) | 2 | `74` | `42` |
| **3. Year** | `YEAR` | 4-digit year (`yyyy`) | 4 | `123` | `78` |
| **4. Colon** | *(none)* | Upper (AM) & Lower (PM) dots (`r = 4 px`) | — | `206` | `10` |
| **5. Hour** | `HOUR` | 2-digit hour (`HH` or `hh`) | 2 | `221` | `42` |
| **6. Minute** | `MIN` | 2-digit minute (`mm`) | 2 | `270` | `42` |

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

- **D1 — 7-Segment Digit Rendering:** Bundled 7-segment TTF font (`res/font/dseg7_classic_bold.ttf`) referenced via `family="dseg7_classic_bold"` in `<Font>`. (Can be swapped to `<BitmapFont>` later if desired).
- **D2 — Footer Text per Row:** Movie-accurate labels:
  - Row 1 (Red): `"DESTINATION TIME"`
  - Row 2 (Green): `"PRESENT TIME"`
  - Row 3 (Yellow): `"LAST TIME DEPARTED"`
- **D3 — Displayed Time in Rows 1, 2, 3 (Phase 1):** All 3 rows display live current date & time (`MMM`, `dd`, `yyyy`, `HH`, `mm`).
- **D4 — Ambient Mode (AOD) Behavior:** Hide `bg.png` and slot box backgrounds in Ambient mode (`alpha="0"`), keeping only the colored digits, dots, and labels on pure black `#000000` to save battery and prevent burn-in.
- **D5 — Screen Size Scaling:** Handled natively by the WFF virtual coordinate canvas (`width="450" height="450"`), which scales vector shapes, fonts, and bitmaps proportionally across all circular Wear OS screen sizes.
