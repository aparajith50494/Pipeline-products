# Test report

Run: 2026-10-15 14:41 with Chromium (Playwright). Result: **30 of 30 criteria passed.**

Catalogue images: 0 of 6 loaded from pipelineproductsonline.com in this run. The rest could not be loaded in this run and showed the labelled placeholder, as the brief requires.

This run was on a machine with no access to pipelineproductsonline.com, so it says nothing about whether the images load in a normal browser. Open the page locally to check.

## Appeal, smoothness and finish

| ID | Result | Criterion | Evidence |
|----|--------|-----------|----------|
| A1 | PASS | Only the brief's palette is used: blue #203F99, red #ED1D24 as a small accent, navy #0B2A3F, white, grey #F4F7F9 and their tints. No orange anywhere. | orange-like computed colours: 0 [] |
| A2 | PASS | The self-hosted Archivo typeface loads; body text is at least 16px with line height of at least 1.5; headlines use the condensed width. | Archivo loaded=True, body 17px / line-height 1.55, h1 width 72% |
| A3 | PASS | Running paragraphs stay under roughly 80 characters per line. | 9 paragraphs checked, longest line about 85 characters ('A curated preview of strainer listings f...') |
| A4 | PASS | Text contrast meets WCAG AA: 4.5:1 for body text, 3:1 for large text. | 426 text elements checked at two widths, 0 below AA [] |
| A5 | PASS | Sections share one vertical spacing rhythm, taken from design tokens. | 5 sections share padding {'112px/112px'} |
| A6 | PASS | The hero headline and both hero actions are fully visible without clipping at 320, 390 and 1280px, and the actions sit above the fold at 390x844 and 1280x800. | 320px: actions bottom 710/640; 390px: actions bottom 634/844; 1280px: actions bottom 678/800 |
| A7 | PASS | Images are never distorted: containers reserve their aspect ratio, product photos use `contain`, the hero uses a controlled crop, and a blocked image becomes a labelled placeholder rather than a broken icon. | 6 images: 0 loaded, 6 labelled placeholders. [] |
| A8 | PASS | Motion durations follow the brief: 160-240ms for hover and press, 300-500ms for reveals. | hover/press [180, 180, 220, 180] ms, reveal 420 ms, details panel 360 ms |
| A9 | PASS | With reduced motion requested, animation is effectively off and all content is visible immediately. | transition 0 ms, reveal classes 0, hidden blocks 0, scroll-behavior auto |
| A10 | PASS | Buttons have a subtle press and cards a small lift, both done with transform only. | press translateY(1px) scale(0.98); card lift translateY(-3px); transform only |
| A11 | PASS | No visible layout shift while the page loads (CLS below 0.05). | CLS desktop 0.0000, mobile 0.0000 |
| A12 | PASS | No horizontal page overflow at 320, 390 or 1280px. | 320px overflow 0px; 390px overflow 0px; 1280px overflow 0px |
| A13 | PASS | Every interactive control is at least 44x44px at mobile width. | 80 controls, 0 under 44px [] |
| A14 | PASS | Every focusable element shows a visible focus ring of at least 2px when reached by keyboard. | 68 focus stops checked, 0 without a visible ring [] |
| A15 | PASS | No generic tells: no emoji icons, no all-caps eyebrow labels, no gradient washes, no glass effects; screenshots show no clipping or awkward wraps. | all-caps 0, gradient washes 0, glass 0, emoji False, arrow-suffixed labels False. Visual review: see screenshots/ |

## Functionality

| ID | Result | Criterion | Evidence |
|----|--------|-----------|----------|
| F1 | PASS | Every button and link has an accessible name, and every in-page link points at an element that exists. | 63 links and buttons; unnamed 0; broken anchors [] |
| F2 | PASS | Range filter chips (All, Y, Basket / simplex, Duplex, Automatic) show the right listings (15 / 5 / 4 / 4 / 2), update `aria-pressed`, and update the announced result count. | counts y=5, basket=4, duplex=4, automatic=2, all=15; aria-live=polite |
| F3 | PASS | Every range card's "Add to quote" adds a line to the request sheet; pressing it again removes it; the header count updates. | 15 cards added then removed; header count tracked each step. issues [] |
| F4 | PASS | The Kraissl "Add to quote" adds a line with size and body material filled in; "Show full details" opens and closes by mouse and keyboard with correct `aria-expanded`. | line {'name': 'Kraissl double basket strainer, cast iron, NPT threaded, fine screen', 'size': '1-1/2', 'unit': 'in', 'mat': 'Cast iron'}; details open=True, keyboard close=True, keyboard reopen=True |
| F5 | PASS | Material chips list the catalogue listings that mention that material, and each listed item scrolls to and highlights its card. No compatibility advice is given. | listing counts correct for 6 materials; jump un-hid the card, scrolled, highlighted and focused: {'hidden': False, 'flash': True, 'inView': True, 'focus': True}; toggle off clears: True. [] |
| F6 | PASS | Request lines can be edited (size and unit, pressure class, material, quantity stepper with a minimum of 1, notes), removed, and added as custom items. | stepper min 1 enforced=True, qty after +,+,- = 2, numbering ['1', '2'] -> ['1'] after removal, focus kept=True |
| F7 | PASS | Inputs are kept while the user filters and navigates; nothing is written to localStorage or sessionStorage. | after filtering, menu navigation and adding: {'item': 'Ball valve', 'size': '3', 'name': 'Test Buyer', 'contact': 'buyer@example.com', 'lines': 2, 'ls': 0, 'ss': 0, 'writes': 0} |
| F8 | PASS | Reviewing an incomplete request shows inline errors and a summary, sets `aria-invalid`, and moves focus to the first problem. | empty sheet: summary shown with 3 items, focus on add-custom; invalid fields ['l1-name', 'l1-qty', 'c-name', 'c-contact']; focus moved to l1-name; summary links focus fields=True |
| F9 | PASS | The contact field accepts a valid email or a usable phone number, and rejects anything else. | 8 inputs classified correctly=True {}; error text: 'Check the email address, for example name@company.com.' |
| F10 | PASS | The review summary contains every line item and the contact details exactly as entered. | summary has all 12 expected values (missing []); review gets focus; editing hides a stale review=True |
| F11 | PASS | "Copy request" shows "Copied. Nothing has been sent." only after the clipboard succeeds; on failure it shows selectable text. No network request is made at any point in the quote flow. | success: 'Copied. Nothing has been sent.', clipboard matches summary=True; failure: fallback shown and selected=True, no 'Copied' claim; network requests during quote flow: 0 |
| F12 | PASS | The mobile menu opens and closes, keeps `aria-expanded` correct, closes on link select and on Escape, and returns focus to the toggle. | closed->open->link closes->Escape closes (focus back True)->outside click closes: ['false', 'true', 'false', 'false', 'false'] |
| F13 | PASS | The active nav item follows the section in view, and anchor scrolling lands the section heading below the sticky header. | range: heading 127px below header, active #range; featured: heading 165px below header, active #featured; materials: heading 127px below header, active #materials; brands: heading 127px below header, active #brands; contact active=True; none active in hero=True |
| F14 | PASS | The back-to-top control appears after the hero and returns to the top. | hidden at top=True, shown after hero=True, scrollY after click=0 |
| F15 | PASS | No console errors; with JavaScript off all content and contact details are still readable; a full quote can be built with the keyboard alone. | console errors 0, page errors 0 at 3 widths (external catalogue image failures excluded); no-JS: {'cards': 15, 'h1': '1', 'details': True, 'phone': True, 'email': True, 'noscript': True, 'form': False, 'nav': True}; keyboard-only quote completed=True (qty via keyboard stepper=2) |
