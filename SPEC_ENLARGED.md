# Specification (Phase 5): Enlarged Dashboard & Oversized Metal Panel (`feat/larger-dashboard-display`)

- **Status:** In Progress
- **Branch:** `feat/larger-dashboard-display`
- **Target Standard:** Android Watch Face Format (WFF v4, `minSdk = 36`, `compileSdk = 37`, `android:hasCode="false"`)

---

## 1. Objective

Enlarge the entire DeLorean dashboard display so all readouts are significantly more legible on the physical watch screen:
1. **Oversized Grey Metal Panel (`bg.png`):**
   - Expand the panel from `636 × 636` to **`720 × 720 px`** (origin `x = 90, y = 90`).
   - The 4 square corners reach **`59 px` outside the circular display edge** ($\sqrt{360^2 + 360^2} = 509\text{ px} > 450\text{ px}$), making the metallic panel fill the screen edge-to-edge without visible black margins on the four sides.
2. **Enlarged Character Cells & Digit Height (+19% larger):**
   - Digit size increased from `size="62"` to **`size="72"`**.
   - Box height increased from `70 px` to **`80 px`** (`frame_h = 84 px`).
   - Character cell width increased from `38 px` to **`44 px`** (`advanceWidth = 613/1000`).
3. **Safe Content Inset (Zero Clipping by Round Bezel):**
   - At `y = 110` (Row 1 top badges), the visible circular chord width is `590 px` (`x = 155 .. 745`).
   - All row contents are centered within `600 px` (`x = 150 .. 750`), ensuring zero clipping by the circular bezel.
