# Specification (Phase 4): Native Wear OS Complication Slots with Hardcoded Steps & Split 2-Digit Right Slots

- **Status:** Implemented & Verified in Emulator
- **Branch:** `feat/split-rightmost-slots-2chars`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## Current layout (supersedes the historical Phase 4 layout below)

- Row 2 retains native STEPS, complication 1 (four characters), and a
  merged four-character complication 2 at x=587, width=186. The merged
  slot defaults to EMPTY and uses the same automatic/manual label logic.
- Row 3 uses complication IDs 3–7, with capacities 3, 3, 3, 2, 2.
- All seven complications retain provider-title, weekday, and icon
  fallback logic plus the full manual label selection. The automatic
  option is displayed as `Auto`.
- Row 1 retains active `#FFFF2200`, ghosts `#FF580000`, and boxes
  `#FF260000`.
- Renumbering Row 3 IDs can require reselecting existing complications
  and label overrides after updating an already configured watch face.

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
