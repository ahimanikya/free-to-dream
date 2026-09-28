# UI / UX and accessibility review — 27 September 2026

## Scope and method

Browser review of the home page, language directory, English, Odia and Urdu language pages, Art Journal, The Witness detail page and contribution form. This supplements the earlier Lighthouse readability audit.

Keyboard interactions were performed against the rendered site. A temporary same-origin iframe harness tested exact CSS viewport widths of 320px and 390px, plus doubled computed text sizes at 768px. The latter is a text-enlargement stress test, **not a claim that native browser 200% zoom was tested**. The harness was removed from the generated site after review.

## Findings fixed

1. **Home sections overflowed at 320px.** The artwork/reference and invitation grid tracks retained a 320px content minimum inside narrower padded areas. Their mobile tracks now use `minmax(0,1fr)` and children can shrink to the available space. Frames, artwork and captions remain intact.
2. **Fixed-height cards clipped enlarged text.** The carousel and directory cards now grow with their content; title and description line clamps were removed. Grid rows retain uniform alignment. The normal home cards still measure 410px tall; they expand when text needs room. The carousel column also fits a narrow viewport.
3. **The author name overflowed under text enlargement.** The biography heading can wrap a long name when necessary.
4. **The mobile page moved while the menu initialized.** The mobile collapsed layout is reserved using the scripting media query before modules arrive. Browsers with scripting disabled keep the visible navigation fallback. A fresh Lighthouse mobile run measured CLS 0, compared with about 0.186 previously.
5. **Keyboard users faced the full 102-language shelf before reaching the story.** Added a focus-visible “Skip language cards” link, without adding another permanently visible control.
6. **Native-script titles lacked language metadata.** Added existing verified language codes to translated titles, directory poem titles and the copyable lyrics field. English adaptation briefs remain tagged English. Removed the redundant hidden artwork H2, keeping the region's accessible name.

## Verified journeys

| Journey | Result |
| --- | --- |
| Keyboard navigation and Skip to content | Focus reaches main content; visible focus outline |
| Language discovery | Searching English returns one result; keyboard selection opens its page; return link preserves the search |
| Country / Jazz tabs | Arrow Right selects Jazz, Home restores Country; audio and video tabs stay synchronized and inactive panels are hidden |
| Mobile menu | Enter opens, Tab reaches Home, Escape closes and returns focus to Menu |
| Listen from a card | English Country audio loads and playback time advances; this verifies playback behavior, not musical quality |
| Player controls | Pause pauses; arrow-key seeking updates time and accessible time text; Next selects English Jazz; Stop pauses at 0 |
| Lyrics and player close | Lyrics drawer contains the text; Close hides the player and returns focus to the originating Play English button |
| Share | Disclosure opens from the keyboard and exposes platform links, caption actions and Instagram instructions; nothing was posted |
| Art Journal → detail | Artwork opens its story; Original artwork link opens the disclosure; original, refined 4× JPEG and canvas PDF links are present |
| Feedback | Language and review type preselected from English; empty preparation focuses the required title and shows native validation; no submission created |

## Layout results

The eight reviewed page types passed the 320px, 390px and doubled-text checks after fixes: no document overflow and no detected clipping of the tested card/caption text. English, Odia and Urdu provide Latin, Odia and right-to-left script samples. This verifies layout, not translation or pronunciation. Final desktop review confirms aligned home cards and no horizontal document overflow.

The inherited mobile player controls are mostly 40px (mute 36px, secondary links 32px): usable in this review, but a touch-only user session remains valuable. Artwork frame and download pixels were not changed.

## Checks

- 30 existing JavaScript interaction tests passed.
- 3 targeted project tests passed: internal links, reading pages and gallery separation.
- Static audit of all 189 pages: no missing local files/anchors, duplicate IDs, missing image alt attributes or H1-count problems.
- `git diff --check` passed.
- Lighthouse mobile home follow-up: accessibility 100, best practices 100, SEO 100, agentic browsing 100, CLS 0. Performance was 72 in that run; do not treat it as a stable improvement/regression measurement, since concurrent local review and image loading affect lab timing. Large screen artwork assets remain a performance follow-up.

## Remaining validation

- A real VoiceOver / NVDA session is still needed to assess announcements, pronunciation, reading order and verbosity. DOM semantics and keyboard checks are not a substitute.
- Native browser zoom, real touch devices, reduced-motion OS preference and human usability sessions were not performed in this pass. Exact narrow viewports and doubled text were tested as described above.
- Ask native readers to review each script's comfort and wording; only three script layouts were sampled here.
- Screen-only responsive artwork derivatives can improve slow mobile loading while preserving original and print downloads.

All changes are local. No deployment, social post or GitHub feedback submission was performed.
