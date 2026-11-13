# Specification (Phase 4): Native Wear OS Complication Slots (`ComplicationSlot`)

- **Status:** Implemented & Verified in Emulator
- **Branch:** `feat/complication-slots`
- **Base Tag:** `v0.4.0-listconfig-slots`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## 1. Overview & Objective

Replace the fixed internal `<ListConfiguration>` metrics with **8 native Wear OS `<ComplicationSlot>` elements** (4 in Middle Row 2, 4 in Bottom Row 3):
- Users get the **complete native Wear OS / Samsung Complication Picker** (Battery, Weather / Feels Like, Sunrise/Sunset, World Clock, Heart Rate BPM, Steps, Day & Date, Unread Notifications, Empty, etc.).
- Complication readouts render in our authentic **14-segment digital font** (`dseg14_classic_bold.ttf`) over full-width ghost segment backgrounds (`~~~` / `~~~~~`).
- Header badges dynamically adapt to the provider's `[COMPLICATION.TITLE]` (truncated gracefully if too long, with automatic fallback when empty).
- Clicking or tapping on a complication slot in the editor opens the full Wear OS `ProviderChooserActivity`.

---

## 2. Slot Layout & Geometry (Row 2 & Row 3)

Across the `636 px` panel width, both Row 2 (`y = 349`, Green `#FF00FF00`) and Row 3 (`y = 564`, Yellow `#FFFFFF00`) provide **4 slots** with `24 px` outer margins and `16 px` inter-slot gaps:

| Slot # | Row | Default Provider | Fallback Badge | Value Box Width | Ghost Text | Supported Complication Types |
| :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | Row 2 | `DAY_OF_WEEK` | `DAY` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **2** | Row 2 | `WATCH_BATTERY` | `BATT` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **3** | Row 2 | `STEP_COUNT` | `STEPS` | `192 px` (5 chars) | `~~~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **4** | Row 2 | `HEART_RATE` | `HEART` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **5** | Row 3 | `DAY_OF_WEEK` | `DAY` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **6** | Row 3 | `DATE` | `DATE` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **7** | Row 3 | `WORLD_CLOCK` | `WORLD` | `192 px` (5 chars) | `~~~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |
| **8** | Row 3 | `UNREAD_NOTIFICATION_COUNT` | `ALRT` | `116 px` (3 chars) | `~~~` | `SHORT_TEXT`, `RANGED_VALUE`, `GOAL_PROGRESS`, `EMPTY` |

---

## 3. Font Enhancements & Punctuation Alignment

1. **Integrated `°` (degree symbol) into `dseg14_classic_bold.ttf`:**
   - Both 7-segment and 14-segment text now support numbers, uppercase letters (`A`–`Z`), `%`, `°`, `:`, `-`, and `.`.
2. **Zero-Width Punctuation (`.`, `:`, `,`):**
   - Inter-digit punctuation (such as `10:10AM` or thousands separators like `8,418`) has its glyph width set to `0` and is centered inside the segment gap so that digits remain perfectly aligned with their ghost segments.

---

## 4. Header Label Formatting & Overlap Prevention

Header labels utilize WFF expressions to handle provider-supplied titles:
1. If `[COMPLICATION.TITLE]` is provided and longer than 6 characters, it is truncated via `subText([COMPLICATION.TITLE], 0, 6)`.
2. If `[COMPLICATION.TITLE]` is empty or equals `"/EMPTY/"`, the fallback label is displayed (`DAY`, `BATT`, `STEPS`, `HEART`, `DATE`, `WORLD`, `ALRT`).
3. Label badges never exceed the value box width (`header_w <= box_w`), guaranteeing zero label overlap.
