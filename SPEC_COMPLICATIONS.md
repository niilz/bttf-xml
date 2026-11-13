# Specification (Phase 4): Native Wear OS Complication Slots with Balanced DeLorean Layout

- **Status:** Implemented & Verified in Emulator
- **Branch:** `feat/custom-slot-layout-and-battery-symbol`
- **Base Tag:** `v0.5.0-dynamic-complication-slots`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## 1. Overview & Architecture

Full DeLorean visual parity using maximum font size (`size="62"`) and native Wear OS ComplicationSlots:
- **Top Row 1 (Red `#FFFF0000`):** Immutable target time circuit (`DESTINATION TIME`).
- **Middle Row 2 (Green `#FF00FF00`):** 3 ComplicationSlots (`5, 3, [COLON], 3`) + AM/PM indicator dots.
- **Bottom Row 3 (Yellow `#FFFFFF00`):** 4 ComplicationSlots (`3, 3, 3, [COLON], 3`) + AM/PM indicator dots.
- **Battery Symbol Adaptation:** When battery is `< 100` (e.g. `85`), the readout displays `85°` (using the DeLorean degree symbol) to maintain a complete 3-character readout aligned with the `88°` ghost segments. When battery is `100`, it displays `100`.

---

## 2. Slot Layout & Alignment (`636 px` Panel Tier)

The AM/PM indicator dots in **all three rows** are aligned at the identical horizontal position:
`x = 412..428` (`width = 16 px`).

### Middle Row 2 (`y = 349`, Height `204 px`, Green)
- **Slot 1 (Left, 5 chars, `width = 192 px`, `x = 160`):** Default `STEP_COUNT` (Steps up to `99999`).
- **Slot 2 (Mid-Left, 3 chars, `width = 116 px`, `x = 400`):** Default `WATCH_BATTERY` (`100` or `85°`).
- **AM/PM Indicator Dots:** `x = 544` (`412..428` in row group).
- **Slot 3 (Right, 3 chars, `width = 116 px`, `x = 606`):** Default `HEART_RATE` (e.g. `116` BPM).

### Bottom Row 3 (`y = 564`, Height `204 px`, Yellow)
- **Slot 4 (Left, 3 chars, `width = 116 px`, `x = 148`):** Default `DAY_OF_WEEK` (`FRI`).
- **Slot 5 (Mid-Left 1, 3 chars, `width = 116 px`, `x = 280`):** Default `DATE` (`13`).
- **Slot 6 (Mid-Left 2, 3 chars, `width = 116 px`, `x = 412`):** Default `WATCH_BATTERY` (`100` or `85°`).
- **AM/PM Indicator Dots:** `x = 544` (`412..428` in row group).
- **Slot 7 (Right, 3 chars, `width = 116 px`, `x = 606`):** Default `UNREAD_NOTIFICATION_COUNT` (`ALRT`).

---

## 3. Font Metrics & Ghost Alignment

- All numbers, letters, `%`, and `°` are rendered with maximum size `size="62"` in `dseg14_classic_bold.ttf`.
- Zero-width punctuation (`.`, `,`, `:`) prevents digit shifting.
- Value boxes automatically shrink to `38 * len(ghost) + 2` when fewer characters are returned, preventing blank un-shadowed space.
