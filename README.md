# Pipeline Products Online: sample homepage concept

A private, one-page homepage concept built from the handover brief dated 15 October 2026. Not the live company website, not deployed, and nothing on the page sends data anywhere.

## Run it on localhost

You need Python 3 (already on macOS and most Linux; on Windows install it from python.org).

```
cd ~/Desktop/pipeline-products-sample
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser. Stop the server with Ctrl+C.
On Windows use `py -m http.server 8000` in the folder.

Opening `index.html` by double-clicking mostly works too, but "Copy request" needs `localhost` (a secure context) to use the clipboard. Without it you get the select-and-copy fallback.

## Run the tests

```
pip install playwright pillow
python3 -m playwright install chromium
python3 tests/run_tests.py
```

The script starts its own local server, checks all 30 criteria in `CRITERIA.md`, rewrites `TEST-REPORT.md` and refreshes `screenshots/`. Run one check with, for example, `python3 tests/run_tests.py F11`.

## Files

| Path | What it is |
|------|------------|
| `index.html` | The page: semantic HTML, all content readable without JavaScript |
| `styles.css` | Design tokens, layout, states and motion (reduced motion respected) |
| `script.js` | Vanilla JS: filter, materials lookup, details panel, request sheet, validation, copy, navigation |
| `assets/fonts/` | Archivo variable font, self-hosted (SIL Open Font License, included) |
| `CRITERIA.md` | The 30 launch criteria: 15 appeal, 15 function |
| `TEST-REPORT.md` | Latest results with evidence for every criterion |
| `screenshots/` | Desktop, mobile and interaction-state captures from the last test run |
| `tests/run_tests.py` | Playwright test suite |

## What works

- Sticky header with active-section underline, offset anchor scrolling, and a mobile menu (`aria-expanded`, closes on link, Escape or outside click, focus returns to the toggle). The quote button stays visible on mobile with a live item count.
- Range explorer: 15 curated listings, filter chips with a sliding selected indicator, announced result count, hero shortcuts that preset the filter.
- Every listing and the four other product lines can be added to or removed from the request sheet.
- Kraissl featured product: spec table, "Add to quote" pre-fills 1-1/2 inch and cast iron, accessible details panel listing what the catalogue does not state.
- Material chips show which listings mention a material and jump to them, with no compatibility advice.
- Request sheet: numbered lines, size with unit, pressure class, material, quantity stepper, notes, custom lines, removal with focus kept. Inline validation, an error summary with links, email or phone accepted.
- Review then "Copy request". "Copied. Nothing has been sent." appears only after the clipboard succeeds; otherwise the text is shown pre-selected. No storage, no network requests, no submission.
- Back-to-top control, one orchestrated hero entrance, quiet reveals, press and lift feedback.

## Before anything goes public

These are open items from the brief and cannot be settled in code:

1. **Images.** The six image URLs point at pipelineproductsonline.com. The brief notes that an automated download got HTTP 406, and my build environment could not reach the site at all, so I have not seen them render. If they load in your browser, they appear; if the server refuses, a labelled placeholder appears instead. Image rights also need the owner's confirmation.
2. **Name.** "Pipeline Products Online" is provisional; the final trading and legal name needs confirming.
3. **Logo.** A text wordmark is used because the only logo found was 140 x 100.
4. **Primary contact.** websales@pipelineproductsonline.com is the sample's quote address; confirm it is the one the business wants.
5. **Claims.** No distributor, delivery, stock, price, certification or response-time claims are made. Brands are labelled "listed in the range". Keep it that way until the business confirms otherwise.
6. **Kraissl image.** The source filename says "duplex" while the listing says "double basket". The page uses the listing's wording.
