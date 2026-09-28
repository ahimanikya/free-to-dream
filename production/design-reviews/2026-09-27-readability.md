# Readability review — 27 September 2026

Requested review: test small typography with Lighthouse and inspect the rendered site using the browser.

## Method

Lighthouse 13.5.0, official CLI in an isolated headless Chrome session, against the local production build. Default mobile simulation and desktop preset. One run before and after for the home page, English language page and The Witness detail page; desktop home as an additional check. These are lab results, not real visitor measurements. Performance scores can vary between runs.

## Results

| Page / preset | Performance, before → after | Accessibility, after | Best practices, before → after | SEO, after |
| --- | --- | --- | --- | --- |
| home-mobile | 80 → 83 | 100 | 92 → 100 | 100 |
| english-mobile | 90 → 86 | 100 | 92 → 100 | 100 |
| artwork-mobile | 65 → 65 | 100 | 92 → 100 | 100 |
| home-desktop | 100 → 99 | 100 | 92 → 100 | 100 |

Accessibility and SEO already scored 100 before the changes. Automated scores do not measure reading comfort: computed styles revealed card labels as small as 9px and descriptions of 11px.

## Changes

- Raised card statuses to 12px, descriptions to 14px, poem titles to 15px, and key actions to 14–15px. Increased carousel card space to accommodate the larger text.
- Enlarged music tabs, download controls, metadata and expanded reading notes. Kept 44px targets on the primary music actions.
- Set English reading text to 20px on desktop and 19px on narrow screens, retaining the established script-specific rules.
- Enlarged on-screen artwork titles to 21px and poetic captions to 18px (20px / 17px on narrow screens), with 12px artist credits.
- Enlarged supporting prose and footer text without changing the approved brand, frame geometry, artwork pixels or print downloads.
- Removed unused inline artwork aspect-ratio attributes blocked by Content Security Policy. The external frame stylesheet remains authoritative; CSP was not relaxed.

## Verification

Browser visual review of the home cards, English page and narrow artwork detail page; no document overflow in the measured viewports. The browser viewport control produced a 582px CSS viewport for the narrow check; Lighthouse independently used its standard mobile simulation. Home card actions remained inside their containers.

Three relevant project tests passed: internal page links, quiet language reading pages, and original/refined gallery separation. Static audit of all 189 built pages found no duplicate IDs, missing local links/anchors, missing image alt attributes or incorrect H1 counts. Whitespace validation passed.

## Remaining findings

- Mobile CLS is approximately 0.18. The primary content moves when the navigation collapses after JavaScript initialization. This is separate from font legibility and should be addressed while preserving navigation without JavaScript.
- The Witness mobile LCP is approximately 24.7 seconds under Lighthouse throttling. Its displayed artwork uses a 2.67 MB PNG; Lighthouse estimates about 2.56 MiB of delivery savings. A future responsive screen-only derivative would improve loading while leaving original and print downloads untouched.
- Agentic browsing scored 89 mobile and 100 desktop; this experimental Lighthouse category is separate from accessibility and SEO.

## Reproduce

Run the production build, serve `site-public`, then run:

```sh
npx lighthouse http://127.0.0.1:8766/index.html --chrome-flags='--headless' --output=html --output=json --output-path=./home-mobile
```

Use `--preset=desktop` for the desktop check, and repeat with the English and The Witness URLs. Raw HTML/JSON reports were retained in the task's output/audits/2026-09-27-readability directory. Compact measured results accompany this note for repository portability.

Changes are local; no deployment was performed as part of this review.
