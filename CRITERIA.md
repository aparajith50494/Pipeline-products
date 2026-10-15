# Launch criteria: Pipeline Products Online sample homepage

All 30 must pass before the page is opened on localhost for review.
Each one names how it is checked. `auto` checks run in `tests/run_tests.py`; `visual` checks are reviewed on the screenshots in `screenshots/`.

## A. Appeal, smoothness and finish (15)

| ID | Criterion | How it is checked |
|----|-----------|-------------------|
| A1 | Only the brief's palette is used: blue #203F99, red #ED1D24 as a small accent, navy #0B2A3F, white, grey #F4F7F9 and their tints. No orange anywhere. | auto: scans every computed colour on the page for orange hues |
| A2 | The self-hosted Archivo typeface loads; body text is at least 16px with line height of at least 1.5; headlines use the condensed width. | auto |
| A3 | Running paragraphs stay under roughly 80 characters per line. | auto: measures paragraph width against font size |
| A4 | Text contrast meets WCAG AA: 4.5:1 for body text, 3:1 for large text. | auto: computes contrast for every visible text element |
| A5 | Sections share one vertical spacing rhythm, taken from design tokens. | auto: compares section padding |
| A6 | The hero headline and both hero actions are fully visible without clipping at 320, 390 and 1280px, and the actions sit above the fold at 390x844 and 1280x800. | auto + visual |
| A7 | Images are never distorted: containers reserve their aspect ratio, product photos use `contain`, the hero uses a controlled crop, and a blocked image becomes a labelled placeholder rather than a broken icon. | auto + visual |
| A8 | Motion durations follow the brief: 160-240ms for hover and press, 300-500ms for reveals. | auto: reads computed transition durations |
| A9 | With reduced motion requested, animation is effectively off and all content is visible immediately. | auto |
| A10 | Buttons have a subtle press and cards a small lift, both done with transform only. | auto: reads `:active` / `:hover` rules |
| A11 | No visible layout shift while the page loads (CLS below 0.05). | auto: PerformanceObserver |
| A12 | No horizontal page overflow at 320, 390 or 1280px. | auto |
| A13 | Every interactive control is at least 44x44px at mobile width. | auto |
| A14 | Every focusable element shows a visible focus ring of at least 2px when reached by keyboard. | auto |
| A15 | No generic tells: no emoji icons, no all-caps eyebrow labels, no gradient washes, no glass effects; screenshots show no clipping or awkward wraps. | auto + visual |

## B. Functionality (15)

| ID | Criterion | How it is checked |
|----|-----------|-------------------|
| F1 | Every button and link has an accessible name, and every in-page link points at an element that exists. | auto |
| F2 | Range filter chips (All, Y, Basket / simplex, Duplex, Automatic) show the right listings (15 / 5 / 4 / 4 / 2), update `aria-pressed`, and update the announced result count. | auto |
| F3 | Every range card's "Add to quote" adds a line to the request sheet; pressing it again removes it; the header count updates. | auto: all 15 cards |
| F4 | The Kraissl "Add to quote" adds a line with size and body material filled in; "Show full details" opens and closes by mouse and keyboard with correct `aria-expanded`. | auto |
| F5 | Material chips list the catalogue listings that mention that material, and each listed item scrolls to and highlights its card. No compatibility advice is given. | auto |
| F6 | Request lines can be edited (size and unit, pressure class, material, quantity stepper with a minimum of 1, notes), removed, and added as custom items. | auto |
| F7 | Inputs are kept while the user filters and navigates; nothing is written to localStorage or sessionStorage. | auto |
| F8 | Reviewing an incomplete request shows inline errors and a summary, sets `aria-invalid`, and moves focus to the first problem. | auto |
| F9 | The contact field accepts a valid email or a usable phone number, and rejects anything else. | auto: 8 sample inputs |
| F10 | The review summary contains every line item and the contact details exactly as entered. | auto |
| F11 | "Copy request" shows "Copied. Nothing has been sent." only after the clipboard succeeds; on failure it shows selectable text. No network request is made at any point in the quote flow. | auto: both paths, network monitored |
| F12 | The mobile menu opens and closes, keeps `aria-expanded` correct, closes on link select and on Escape, and returns focus to the toggle. | auto |
| F13 | The active nav item follows the section in view, and anchor scrolling lands the section heading below the sticky header. | auto |
| F14 | The back-to-top control appears after the hero and returns to the top. | auto |
| F15 | No console errors; with JavaScript off all content and contact details are still readable; a full quote can be built with the keyboard alone. | auto |
