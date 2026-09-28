# Simplicity and usability audit — 28 September 2026

Reviewed home, language directory, English, Tamil and Hindi language pages, Art Journal, The Witness detail, design credits, original poem and contribution page. Preserved the approved artwork, palette, typography and restored palm-leaf manuscript decoration.

## Improvements
- Languages without recordings now show one clear invitation instead of separate empty audio and video sections. Existing section links remain valid.
- Artwork details avoid repeating the poetic caption already displayed in the frame. Print downloads show their format and size.
- Refined print/download sections start collapsed on every artwork detail page. Direct download-section links reveal them automatically. Original artwork remains available on demand.
- Hid The Witness canvas PDF panel and removed its guide link, retaining the source file and image downloads.
- Slideshow shows the current song, supports left/right keyboard artwork navigation, and carries the current playback position when opened from a language page while its song is playing in the collection player.
- Portrait slideshows use the phone height; short landscape screens place the caption beside the art. Controls have reserved space below the caption.

## Validation
- Desktop checks on ten representative pages: one main heading, no horizontal overflow, no broken loaded images or visible unnamed buttons.
- Exact 320px and 390px layouts on eight representative pages: all sixteen cases free of page overflow and unintended off-screen primary controls.
- Slideshow layouts at 320×640, 390×844 and 740×360: controls fit; caption and current-song label remain separated. The 320px example increases artwork height from 122px to 280px.
- Verified language filtering, mobile menu and Escape dismissal, original-art disclosure links and collapsed print-download deep links in the browser.
- 32 Python tests and 34 JavaScript tests pass. Structural audit of 189 generated pages checks headings, duplicate IDs, image alternatives, local resources and fragment targets.
- Build and repository portability checks pass.

This is a visual, keyboard, responsive-layout and automated audit, not a screen-reader user study or an acoustic assessment of the songs. Original and refined artwork pixels and download images are unchanged.
