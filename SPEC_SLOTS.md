# Specification (Phase 2 & 3): Configurable Digital Slots in Middle Row (`row_2_present`) & Bottom Row (`row_3_departed`)

- **Status:** Approved & Finalized (Includes `time`, `slots_3`, `slots_4`, and `slots_5`)
- **Branch:** `feat/phase2-middle-row-slots`
- **Base Tag:** `v0.2.0-digital-month-layout`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## 1. Confirmed Architecture & Decisions

1. **S1 — Configuration Mechanism (`<UserConfigurations>` + Flat `<ListConfiguration>` + `<Editable value="true" />`):**
   - Uses WFF's built-in declarative configuration system (`userConfigurationsElement.xsd` & `groupElement.xsd`).
   - Declares `<Editable value="true" />` in `res/xml/watch_face_info.xml` so Wear OS displays the **"Customize" / "Anpassen"** button in the watch face picker.
   - **Important WFF Runtime Rules (Enforced by Tests):**
     1. In `res/raw/watchface.xml`, `displayName` and `screenReaderText` reference string resources **without** the `@string/` prefix (e.g. `displayName="cfg_slot_1"`).
     2. In `res/values/strings.xml`, configuration display strings must **never** contain unescaped `%` characters (e.g. `"Battery (%)"` causes Android's `Resources.getString()` formatter in `InteractiveWatchFaceImpl.getUserStyleSchema()` to throw `UnknownFormatConversionException: Conversion = ')'`).
   - No Kotlin `Activity` or background service needed; long-pressing the watch face opens the native Wear OS editor.
2. **S2 — Flexible Mode Switchers (`row2_mode` & `row3_mode`) + Individual Slot Selectors (`slot_1..5` & `r3_slot_1..5`):**
   - Outer `<ListConfiguration id="row2_mode">` selects the Row 2 (Green `#FF00FF00`) layout mode (`time`, `slots_3`, `slots_4`, `slots_5`), and `slot_1..slot_5` configure the individual Row 2 slots.
   - Outer `<ListConfiguration id="row3_mode">` selects the Row 3 (Yellow `#FFFFFF00`) layout mode (`r3_time` [default], `r3_slots_3`, `r3_slots_4`, `r3_slots_5`), and `r3_slot_1..r3_slot_5` configure the individual Row 3 slots.
   - Every `<ListOption>` sizes its inner value box to `38 * len(ghost) + 2` so that 2-char, 3-char, 4-char, and 5-char options are always completely filled by their ghost segments with no empty un-shadowed space on the left.
3. **S3 — Units in Digital Font:**
   - `BATTERY`: `[BATTERY_PERCENT]%` rendered in `dseg14_classic_bold` (supports `0-9` and `%`), ghost `888~` (4-char) or `88~` (3-char).
   - `TEMP`: `[WEATHER.TEMPERATURE]°` (degree symbol only, without `C`) rendered in `dseg7_classic_bold` (supports `0-9`, `-`, `°`), ghost `88°`.
   - `STEPS`: `[STEP_COUNT]` rendered in `dseg7_classic_bold`, ghost `88888`.
   - `HEART`: `[HEART_RATE]` rendered in `dseg7_classic_bold`, ghost `888`.
   - `DAY`: `<Upper>[DAY_OF_WEEK_S]</Upper>` rendered in `dseg14_classic_bold`, ghost `~~~`.
4. **S4 — Step Count Digits:** Full 5-digit capacity (`0`–`99999`, box width `192 px`).
5. **S5 — Footer Label:** Always `"PRESENT TIME"` centered at the bottom of Row 2.

---

## 2. S6 — Header Label Naming & Anti-Overlap Guarantee

### Where Do the Header Label Names Come From?
Because each option in `<ListConfiguration>` is a self-contained `<ListOption><Group>`, **the watch face XML itself defines the exact Header Badge `<Rectangle>` and `<PartText>` label for each selected metric**. We do not depend on external complication providers sending titles.

### How Do We Guarantee Labels Never Overlap or Overflow?
**Rule:** Every Header Badge `<Rectangle>` and `<PartText>` has a width **$\le$ the width of its own value box below it**. Because value boxes are separated by $\ge 12\text{ px}$ gaps, adjacent header badges are also separated by $\ge 12\text{ px}$ and can **never** touch or overlap:

| Metric ID | Header Label Text | Label Badge Width (`size="30"`) | Value Box Width | Margin Inside Box Width |
| :--- | :---: | :---: | :---: | :---: |
| `steps` | `STEPS` | `108 px` | `192 px` (5 chars) | `+84 px` (`42 px` left/right) |
| `battery` (4-char) | `BATTERY` | `144 px` | `154 px` (4 chars, `100%`) | `+10 px` (`5 px` left/right) |
| `battery` (3-char) | `BATT` | `92 px` | `116 px` (3 chars, `85%`) | `+24 px` (`12 px` left/right) |
| `temp` | `TEMP` | `96 px` | `116 px` (3 chars, `21°`) | `+20 px` (`10 px` left/right) |
| `heart` | `HEART` | `108 px` | `116 px` (3 chars, `072`) | `+8 px` (`4 px` left/right) |
| `day` | `DAY` | `78 px` | `116 px` (3 chars, `SUN`) | `+38 px` (`19 px` left/right) |

---

## 3. Exact Horizontal Coordinates per Mode (`636 px` Row Width)

### Mode 1: `time` (Default 5-Slot DeLorean Time)
Identical to Row 1 & Row 3 (`28 px` outer margins, `12 px` gaps):
- `MONTH` (`116 px`), `DAY` (`78 px`), `YEAR` (`154 px`), `COLON` (`16 px`), `HOUR` (`78 px`), `MIN` (`78 px`).

### Mode 2: `slots_4` (4 Custom Slots — Default: `STEPS`, `BATTERY`, `TEMP`, `HEART`)
All 4 primary metrics displayed simultaneously across `636 px`:
- **Outer Left/Right Margins:** `14 px` (`0..14` and `622..636`)
- **Inter-Slot Gaps (3 gaps):** `10 px` each
- **Slot 1 (5 chars, `width = 192`, `x = 14`):** Default `STEPS` (`[STEP_COUNT]`, label `STEPS`)
- **Slot 2 (4 chars, `width = 154`, `x = 216`):** Default `BATTERY` (`[BATTERY_PERCENT]%`, label `BATTERY`)
- **Slot 3 (3 chars, `width = 116`, `x = 380`):** Default `TEMP` (`[WEATHER.TEMPERATURE]°`, label `TEMP`)
- **Slot 4 (3 chars, `width = 116`, `x = 506`):** Default `HEART` (`[HEART_RATE]`, label `HEART`)
*(Total width: $14 + 192 + 10 + 154 + 10 + 116 + 10 + 116 + 14 = 636\text{ px}$)*

### Mode 3: `slots_3` (3 Custom Slots — Default: `STEPS`, `BATTERY`, `TEMP`)
3 slots with extra-wide breathing room across `636 px`:
- **Outer Left/Right Margins:** `36 px` (`0..36` and `600..636`)
- **Inter-Slot Gaps (2 gaps):** `51 px` each
- **Slot 1 (5 chars, `width = 192`, `x = 36`):** Default `STEPS` (`[STEP_COUNT]`, label `STEPS`)
- **Slot 2 (4 chars, `width = 154`, `x = 279`):** Default `BATTERY` (`[BATTERY_PERCENT]%`, label `BATTERY`)
- **Slot 3 (3 chars, `width = 116`, `x = 484`):** Default `TEMP` (`[WEATHER.TEMPERATURE]°`, label `TEMP`)
### Mode 4: `slots_5` (5 Custom Slots — Default: `BATT`, `TEMP`, `STEPS`, `HOUR`, `MIN`)
5 slots across `636 px` with `28 px` outer margins and `12 px` gaps:
- **Outer Left/Right Margins:** `28 px` (`0..28` and `608..636`)
- **Inter-Slot Gaps (4 gaps):** `12 px` each
- **Slot 1 (3 chars, `width = 116`, `x = 28`):** Default `BATT` (`[BATTERY_PERCENT]%`)
- **Slot 2 (2 chars, `width = 78`, `x = 156`):** Default `TEMP` (`[WEATHER.TEMPERATURE]°`)
- **Slot 3 (5 chars, `width = 182`, `x = 246`):** Default `STEPS` (`[STEP_COUNT]`)
- **Slot 4 (2 chars, `width = 78`, `x = 440`):** Default `HOUR` (`hh`)
- **Slot 5 (2 chars, `width = 78`, `x = 530`):** Default `MIN` (`mm`)
*(Total width: $28 + 116 + 12 + 78 + 12 + 182 + 12 + 78 + 12 + 78 + 28 = 636\text{ px}$)*
