# Design System Specification: Orbital Precision & Tonal Depth

## 1. Overview & Creative North Star: "The Orbital Sentinel"
This design system is built to facilitate high-stakes satellite autonomy. The Creative North Star is **"The Orbital Sentinel"**—an aesthetic that balances the cold, vast expanse of space with the surgical precision of mission control. 

To move beyond the "generic dashboard" look, this system rejects the "flat box" mentality. Instead, it utilizes **Intentional Asymmetry** and **Tonal Layering**. We achieve a premium feel by treating the interface not as a screen, but as a sophisticated optical instrument. We avoid loud, sci-fi tropes in favor of "Technical Elegance": high-contrast typography, vast "breathing room," and depth created through light rather than lines.

---

## 2. Colors & Surface Logic

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. They create visual noise that degrades the "premium" feel. Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` component should sit directly on a `surface` background, relying on the tonal shift to define its edge.

### Surface Hierarchy (The Layering Principle)
Treat the UI as a series of physical layers. Use the surface tiers to create a "nested" depth that guides the eye.
*   **Base Layer:** `surface` (#10131a) - The foundation of the viewport.
*   **Sunken Elements:** `surface-container-lowest` (#0b0e14) - For deep utility bars or background canvas areas.
*   **Primary Containers:** `surface-container` (#1d2026) - For standard metric cards and operational tiles.
*   **Elevated Overlays:** `surface-container-highest` (#32353c) - For modals or "active" states.

### The "Glass & Gradient" Rule
To inject "soul" into the technical interface:
*   **Glassmorphism:** Use `surface-container` with a 70-80% opacity and a `20px` backdrop-blur for floating panels. This allows telemetry data to "bleed" through the glass, softening the technical edge.
*   **Signature Glows:** Primary CTAs and critical status indicators should use a subtle radial gradient (e.g., `primary` transitioning to `primary-container`) to simulate the luminescence of high-end hardware.

---

### 3. Typography: Editorial Authority
We use a single typeface—**Inter**—to maintain a monolithic, authoritative voice. The hierarchy is extreme to ensure immediate readability during mission-critical events.

*   **Display (Display-LG: 3.5rem):** Reserved for singular, mission-critical metrics (e.g., Orbital Velocity). Use `on-surface` with high tracking (-0.02em).
*   **Headline (Headline-MD: 1.75rem):** Used for section titles. These should be set in Semi-Bold to provide an "Editorial" weight.
*   **Body (Body-MD: 0.875rem):** The workhorse. Always prioritize line height (1.5) to ensure technical strings are readable.
*   **Labels (Label-SM: 0.6875rem):** Used for metadata and timestamps. Always uppercase with +0.05em letter spacing to mimic aerospace instrumentation.

---

## 4. Elevation & Depth: Tonal Layering
We do not use drop shadows to indicate "height"; we use **Light and Tone**.

*   **Ambient Shadows:** If a floating effect is required (e.g., a critical alert pop-over), use an extra-diffused shadow: `box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4)`. The shadow must feel like an occlusion of light, not a black smudge.
*   **The "Ghost Border" Fallback:** For accessibility in high-density data grids, use a "Ghost Border." Apply the `outline-variant` token at **15% opacity**. It should be felt, not seen.
*   **Inner Glow:** For metric tiles, use a 1px inner-stroke (inset) using `primary` at 10% opacity. This simulates the light-catching edge of a glass lens.

---

## 5. Components & Primitive Logic

### Buttons (Tactile Commands)
*   **Primary:** Background: `primary` (#4fdbc8). Text: `on-primary` (#003731). No border. Use a subtle `primary-container` outer glow on hover to indicate "charged" state.
*   **Secondary:** Background: `surface-container-high`. Border: None. Text: `on-surface`.
*   **Tertiary:** Text only. Use `label-md` styling (Uppercase, tracked out).

### Metric Tiles (The Data Core)
*   **Structure:** No dividers. Use `16px` (Spacing 4) internal padding.
*   **Visuals:** A `surface-container-low` background with a `surface-container-highest` "header" strip. 
*   **Status Glow:** A 4px vertical pill on the left edge using semantic colors (`error` for Danger, `primary` for Nominal) to communicate status without words.

### Status Badges
*   Use a "De-saturated Fill" approach. A `success` badge should have a background of `primary-container` at 20% opacity with `primary` colored text. This keeps the UI technical and prevents it from looking like a "traffic light."

### Input Fields
*   **Base State:** `surface-container-lowest` background. No border.
*   **Focus State:** A 1px `Ghost Border` using `primary` and a subtle 4px `primary` outer blur.

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use `24px` or `32px` gaps between major sections. Space is a luxury; use it to signify importance.
*   **Do** use "Surface Nesting" (e.g., putting a `surface-container-highest` card inside a `surface-container` section) to create hierarchy.
*   **Do** use semi-transparent `secondary-fixed-dim` for inactive telemetry data to keep focus on active "Primary" streams.

### Don't:
*   **Don't** use 100% white (#FFFFFF) for body text. Use `on-surface` (#e1e2eb) to prevent eye strain in dark environments.
*   **Don't** use rounded corners larger than `xl` (12px/0.75rem). Anything rounder loses the "Technical" edge and begins to look "Consumer-soft."
*   **Don't** use dividers or lines to separate list items. Use vertical spacing (`spacing-2` or `spacing-3`) and subtle background alternates if necessary.

---

## 7. Spacing & Geometry
All layouts must adhere to the 8px baseline. 
*   **Micro-spacing (4px, 8px):** Internal component padding and label-to-value relationships.
*   **Macro-spacing (32px, 64px):** Separation between logical modules (e.g., Map View vs. Telemetry Feed).
*   **Corner Radii:** Consistent `lg` (0.5rem / 8px) for all standard cards. Use `sm` (0.125rem / 2px) for small status indicators to maintain a "sharp" feel.