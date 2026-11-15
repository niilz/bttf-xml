# Specification (Phase 4): Native Wear OS Complication Slots with Hardcoded Steps & Split 2-Digit Right Slots

- **Status:** Implemented & Verified in Emulator
- **Branch:** `feat/split-rightmost-slots-2chars`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## Current layout (supersedes the historical Phase 4 layout below)

- Row 2 retains native STEPS, complication 1 (four characters), and a
  merged four-character complication 2 at x=587, width=186. The merged
  slot defaults to EMPTY and uses the same automatic/manual label logic.
  Before a provider is selected, Wear OS can report NO_DATA rather than
  EMPTY. Every slot therefore has a scene-level fallback guarded by its
  explicit `[COMPLICATION.<slotId>.TYPE]` being NO_DATA or NOT_CONFIGURED.
  It duplicates that slot's EMPTY artwork (NONE, dashes, ghost segments,
  frame and depth styling), including its ambient behavior. For a live
  data type the fallback disappears; EMPTY still uses the normal slot branch.
  A selected provider temporarily reporting NO_DATA also shows this fallback.
- Row 3 uses complication IDs 3–7, with capacities 3, 3, 3, 2, 2.
- All seven complications retain provider-title, weekday, and icon
  fallback logic plus the full manual label selection. The automatic
  option is displayed as `Auto`.
- Row 1 retains active `#FFFF2200`, ghosts `#FF580000`, and boxes
  `#FF260000`.
- Renumbering Row 3 IDs can require reselecting existing complications
  and label overrides after updating an already configured watch face.

## Complication representation priority

All seven slots request `SHORT_TEXT` first so providers return compact values
rather than prose that would be truncated to two to four characters.
`LONG_TEXT` remains a fallback for providers without a short representation;
`RANGED_VALUE`, `GOAL_PROGRESS`, and `EMPTY` remain supported. Default provider
policies already request `SHORT_TEXT` (or `EMPTY` for the unassigned slot).
This changes negotiation only, not label selection or per-character fonts.
Existing provider assignments may need to be reselected on the watch if the
runtime retains their previously negotiated `LONG_TEXT` type.

## Per-character segment selection

- For every live complication value (all four supported data types), each
  visible character independently selects its foreground and ghost font:
  ASCII `0`–`9` use `dseg7_classic_bold` with `8`; other characters use
  `dseg14_classic_bold` with `~`. For `85%`, only the percent cell uses
  the 14-segment pair. Letters, minus signs and degree symbols stay 14-segment.
- Preserve the existing battery-percent formatting and value truncation
  before selecting glyphs, including automatically appended percent signs.
- Fixed right-aligned character cells stay within the existing readout area.
  WFF requires integer geometry: four-character cells use a uniform 45 px
  width with alternating 44/45 px advances, avoiding unequal autosizing.
  Leading unused cells retain their existing 14-segment ghost style.
- Native STEPS is always numeric, so both its foreground and five ghosts
  use the 7-segment font. Labels, EMPTY/NO_DATA artwork, colors, depth,
  row positions and ambient hiding of ghosts remain unchanged.
- Run `python3 -m unittest discover -s watchface/src/test/python -v`, including
  the mixed-value, character-selector and geometry checks in
  `test_character_segments.py`, plus WFF v4 XSD validation.

## 1. Historical Phase 4 Overview & Architecture

Full DeLorean visual parity using maximum font size (`size="62"`) and native Wear OS ComplicationSlots:
- **Top Row 1 (Red `#FFFF2200`):** Immutable target time circuit (`DESTINATION TIME`).
- **Middle Row 2 (Green `#FF00FF00`):**
  - **Slot 1 (Fixed Native Steps):** Hardcoded native `[STEP_COUNT]` (5 digits, `192 px`, ghost `~~~~~`).
  - **Slot 2 (ComplicationSlot 1):** 4 chars (`154 px`), default `WATCH_BATTERY` (`100` or `80%`).
  - **AM/PM Indicator Dots:** Aligned at `x = 412..428`.
  - **Slot 3 (ComplicationSlot 2):** 2 chars (`78 px`), default `HEART_RATE` (`BPM`).
  - **Slot 4 (ComplicationSlot 3):** 2 chars (`78 px`), default `UNREAD_NOTIFICATION_COUNT` (`ALRT`).
- **Bottom Row 3 (Yellow `#FFFFFF00`):**
  - **Slot 5 (ComplicationSlot 4):** 3 chars (`116 px`), default `DAY_OF_WEEK` (`DAY`).
  - **Slot 6 (ComplicationSlot 5):** 3 chars (`116 px`), default `DATE` (`NOV 13`).
  - **Slot 7 (ComplicationSlot 6):** 3 chars (`116 px`), default `WATCH_BATTERY` (`BATT`).
  - **AM/PM Indicator Dots:** Aligned at `x = 412..428`.
  - **Slot 8 (ComplicationSlot 7):** 2 chars (`78 px`), default `SUNRISE_SUNSET` (`SUN`).
  - **Slot 9 (ComplicationSlot 8):** 2 chars (`78 px`), default `WORLD_CLOCK` (`NYC`).
- **Total ComplicationSlots:** Exactly 8 (3 in Row 2, 5 in Row 3), adhering to WFF's `maxOccurs="8"` schema constraint.
- **AM/PM Alignment:** Exactly matching `x = 412..428` across all three rows.
- **Battery Formatting:** Digital percent symbol (`80%`) via escaped `<Template>%s%%<Parameter ... /></Template>`.
