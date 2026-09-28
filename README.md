# World is One — A Poem Without Borders

**One poem. Many voices. Shared dreams.**

A collaborative home for Ahimanikya Satapathy’s Odia poem **“ମୋତେ ସପ୍ନ ଦେଖିବାକୁ ମନା ନାହିଁ” / “I Am Free to Dream”** and its language adaptations, musical directions and recordings.

The collection has **102 language entries: 30 original/adapted lyric texts and 72 adaptation briefs**. They are not 102 finished songs. AI-assisted drafts need native-speaker review; musical prompts are creative proposals, not verified performances.

## An open reference for the next creative work

The poem, author artwork and author-controlled reference material are available under CC BY 4.0; code uses MIT. Recordings and third-party material retain separate terms. See [reuse and attribution](RIGHTS.md). The [public reference guide](kb/guides/public-reference.md) explains how to adapt the method for music and film. A shared settings baseline supports documented language and arrangement overrides without flattening cultural choices.

The public build generates a sitemap, page-specific structured metadata, `llms.txt` and `reference.json`. Source text, review status and citations remain readable without JavaScript. Search or AI inclusion is not guaranteed.

## Start here

- [Browse the knowledge base](kb/index.md)
- [Original Odia poem](kb/poems/i-am-free-to-dream/original.md)
- [All language entries](kb/poems/i-am-free-to-dream/languages/index.md)
- [Meaning and adaptation guide](kb/poems/i-am-free-to-dream/meaning.md)
- [How to contribute](CONTRIBUTING.md)
- [Audio and video files in Git](media/README.md)
- [Work from any computer or a cloud workspace](kb/guides/portable-workspace.md)
- [Project skill](skills/poetry-to-music/SKILL.md) · [Production history](production/README.md)
- [Language-to-song-and-video workflow](kb/guides/music-pipeline.md)
- [Add an audio recording](kb/guides/add-media.md)
- [Publish the listening site and export a GitHub wiki](kb/guides/publishing.md)
- [Credits and rights](RIGHTS.md)

## Collaborate through the website

Each language page offers **Suggest a change**, **Submit your version**, and **Review a recording**. Visitors prepare a proposal on the site and continue to GitHub with its details filled in. They sign in there, attach an MP3/M4A recording or paste a hosted link, and submit. No coding or direct repository write access is required. Long proposals remain complete and use an explicit copy/paste step when they will not fit in a URL.

GitHub issues hold the conversation and submission history. Maintainers review contributions, merge lyric changes, and add accepted recordings to the catalog. The site is rebuilt after changes reach `main`. The source Markdown stays in `kb/`; contributors do not overwrite it by submitting a proposal.

Every available recording has its own page with a player, creator credits, a downloadable/openable media link and a listening-feedback action. Published pages offer native sharing, Facebook, WhatsApp and copy-link/caption controls. Social previews use the cover artwork. Media-file sharing can be enabled per released recording using `allow_file_sharing: true`; browsers or media hosts that cannot share a file directly fall back to saving/opening it and attaching it in the social app. Social networks decide how a shared link is displayed; the site cannot promise an inline player in every feed.

### Connect it

Set `repository_url` (for example, `https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY`) and `site_url` in `site-config.json`, enable GitHub Issues, and configure Pages to use GitHub Actions. Until these actual destinations are supplied, the local site lets you prepare and save proposals but does not pretend to submit them or offer public links to unpublished recordings.

This uses GitHub for sign-in, discussions and attachment storage. There are no repository access tokens in the website and no custom upload backend. GitHub attachments have size limits; contributors with large recordings can use a hosted link. See the [collaboration and release guide](kb/guides/collaboration.md).

## Reading experience

Language pages put the poem beside compact audio/video players. Sharing, musical direction, alternate takes and translation guidance open on demand. The Odia page presents the author’s original poem, with its sung arrangement available separately and no translation checklist.

Original decorative drawings reference Odisha’s Pattachitra and palm-leaf traditions. The original-art and AI-image galleries are kept separate. The collection cover remains on the home page, video posters and social previews.

The index cards show lyric status, musical direction, current audio/video availability and a play button where audio exists. A shared player offers alternate takes without leaving the index. The [timing workspace](https://poemwithoutborders.org/timing.html) lets contributors mark or correct lyric cues and export an SRT for review.

## Audio-first collection

For the author’s production workflow, choosing a language starts one candidate pair; selecting a take triggers its **MP3 download, matching MP4 creation, and publication of both**. See the [production workflow](kb/guides/music-pipeline.md).

Community recordings may use MP3 or M4A. Keep cover artwork and any checked SRT separate for each take. Audio remains in Git LFS; poems, credits and SRTs use ordinary Git. The site generates WebVTT and displays timed lyrics using the audio player’s position. Missing timings are clearly marked. See the [timed lyrics guide](kb/guides/timed-lyrics.md).

Language pages embed the available audio and video recordings. Earlier takes appear under expandable “Earlier versions” sections; all original files remain preserved. A dedicated media host can be connected later for public streaming; no storage migration is configured yet.

## Listen locally

Requires Python 3.10 or later. From this project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/project.py build --local-media
python scripts/project.py serve
```

Open **http://127.0.0.1:8765**. Search for a language, choose **Ready to listen**, and open its page. Native audio/video players support seeking. Odia, Tamil, Telugu, Malayalam, English (country and jazz), Filipino / Tagalog, Italian, Bengali, and Sambalpuri have embedded recordings. Other pages show separate audio/video availability messages.

The audio/video archive is tracked with **Git LFS** in language folders under [`media/`](media/README.md). Install Git LFS before cloning, or run `git lfs pull` in an existing checkout, to retrieve the full files. The ignored `local-assets/` folder retains private references and local working copies. Public players use explicitly authorized review-copy URLs or approved release URLs. Sharing a review copy does not mark its translation, pronunciation or release checks complete.

The existing 13 audio files and 18 videos are available as author-authorized review copies. The site streams them from version-pinned Git LFS URLs; loading starts when the visitor presses play. No media binaries are copied into the Pages deployment.

## Where things live

| Folder | Purpose |
|---|---|
| `kb/` | Editable source: OKF v0.2 Markdown, provenance, language and review status |
| `catalog/recordings.json` | Recording IDs, credits, local paths, public URLs and release flags |
| `catalog/asset-inventory.json` | Checksums, archive paths and filenames of imported assets |
| `catalog/media-archive.json` | Complete versioned recording archive and unavailable originals |
| `catalog/import-provenance.json` | Original language-document body hashes at import |
| `media/<language>/` | Audio/video files tracked with Git LFS, version notes and checksums |
| `media/images/` | Shared cover images and their prompt |
| `local-assets/` | Ignored working media, masters and private reference material |
| `skills/` | Maintained project skill, references and preparation helper |
| `production/` | Portable prompts, settings, candidate history and decisions |
| `.devcontainer/` | Cloud/development-container setup |
| `web/` | Listening-site design and search behavior |
| `scripts/` | Validation, site generation, media registration and wiki export |
| `site/` | Generated local listening preview; ignored |
| `site-public/` | Generated public build; ignored |
| `wiki-export/` | Generated GitHub wiki pages; ignored |

The `kb/` folder follows [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). Its Markdown files are the source of truth. Every concept has YAML frontmatter; reserved `index.md` and `log.md` files follow the format’s separate rules. No human verification is implied by import or automated validation.

## Checks

```sh
python scripts/project.py validate
python -m unittest discover -s tests -v
node --test tests/collaboration.test.mjs
python scripts/project.py build
```

`build` without `--local-media` makes a public-safe site: it excludes archive recordings, LFS pointers, private reference photographs and publication evidence. Only recording entries explicitly authorized as public previews or approved for release are embedded remotely. Cover artwork and the language drafts remain part of the public build.

The GitHub check workflow validates changes and builds the public site. After Pages is enabled, the deployment workflow runs on pushes/merges to `main` and can also be run manually. Nothing is uploaded merely by preparing this repository locally. JavaScript tests require Node.js 18 or later; the website itself is static HTML/CSS/JavaScript.

## Working principle

Preserve the original; adapt with care; credit the people who help. Each musical setting should name its chosen cultural references while leaving room for other traditions in the same language.

The homepage tells the story of the author’s college-era poem and introduces all languages in a compact, continuously looping row below the statistics. Arrow buttons move one visible group at a time; swipe and keyboard navigation also work. The scrollbar is hidden; the separate Languages page provides the full searchable directory. The full searchable collection lives at `languages.html`. Cards share a fixed height, and the potter artwork opens the collection. The author’s signed 1993 artwork sits to the right of the closing invitation, with its signature intact.

Language pages separate **Read**, **Listen** and **Watch**. Reading hides standalone arrangement labels without changing the source lyrics or stanza spacing. The full text, including song sections, is available under **Lyrics prompt · view & copy**. Odia continues to show the author’s original poem.

The author bio uses background supplied by the author. Profile links are configured in `site-config.json` under `author_links`; add only confirmed public profiles. Motion is user-controlled and respects reduced-motion preferences.

The collection identity is **World is One — A Poem Without Borders**. The listening player offers Previous and Next across current audio recordings, including alternate styles. After a listener starts a song, the playlist automatically advances and stops at the final track. Pause keeps the current position; Stop returns the current track to the beginning. Language and recording pages offer a Playlist dropdown alongside their inline players. The shared player uses the same dropdown to choose any current track across languages and styles. Back links follow a valid parent page when possible and keep useful destinations for direct visits.

The player shows a single track-title dropdown, icon controls, a keyboard-accessible seek slider, elapsed time, duration, Stop, volume and mute. When it is open, the inline playlist selector is hidden to avoid duplicate lists. A current lyric line follows the recording’s audio clock only when that take has checked SRT timings; otherwise the player links to the poem. Switching tracks clears the previous cues, including late loading responses.

## Engagement and the listening player

The player includes shuffle, repeat off/all/one, an Up next queue, in-player lyric drafts and supported lock-screen/media-key controls. Lyrics stay readable without leaving the song. Native inline players remain available; opening a different full page can interrupt playback, so player detail links open separately.

The [engagement workspace](https://poemwithoutborders.org/engagement.html) combines reporting setup with a public GitHub feedback inbox. A dedicated **World is One** GA4 account is connected for consented page, listening and sharing events. The tag stays off until a visitor opts in. Share clicks never imply confirmed social posts or identified sharers. [Measurement definitions and setup](kb/guides/engagement.md) · [Privacy](kb/guides/privacy.md).

The contribution-attention workflow labels new issues/replies for the author and marks owner replies as awaiting the contributor. Existing unlabelled issues remain visible for manual triage. It never accepts creative changes or sends replies automatically.

## Canvas print files

The art gallery offers the author-supplied canvas PDF in `media/prints/`. These files use Git LFS. Before building the gallery after cloning, run `git lfs pull --include="media/prints/*.pdf" --exclude=""`. Site and check workflows retrieve only these print files; audio and video continue to stream remotely. A build rejects an unhydrated PDF instead of offering a broken download.

### Artwork collection

`catalog/artworks.json` defines the original-art gallery at `artworks.html`, with source filenames, original dimensions and SHA-256 checksums. Full-size sources in `media/artworks/` are unchanged uploads tracked with Git LFS. Small previews extracted from the supplied poster PDFs live in `media/images/art-archive/`. Gallery captions are contemporary reflections, not historical inscriptions. Retired layouts and alternate captures are not shipped to the site.

Retrieve artwork and print files before building: `git lfs pull --include="media/prints/*,media/artworks/*,media/ai-artworks/*" --exclude=""`. The build rejects unhydrated or modified artwork sources.

The personal art pages present the author’s artwork. The site’s decorative SVGs are contemporary digital interpretations informed by Odisha’s Pattachitra and palm-leaf traditions, not historical artifacts or artisan reproductions. The potter cover is AI-generated and remains separately credited under `RIGHTS.md`.

The Art Journal at `artworks.html` opens with refined prints; the edition switch offers originals at `original-artworks.html`. Refined print editions belong alongside their source artwork on `artwork--<id>.html#ai-edition`, clearly identified and separately downloadable. `catalog/ai-artworks.json` connects an edition to its original through `source_artwork_id`. Both indexes share the gallery renderer, two frame sizes and edition switch. The old `ai-artworks.html` URL remains a compatibility page with its canonical pointing to `artworks.html`. It includes only editions linked to selected originals, excluding standalone generated illustrations; each card links to the matching detail-page print section. `guides--artwork.html` is a text-only guide to decorative design roots and credits. Personal artwork lives in the Art Journal; The Witness’s canvas metadata is in `catalog/artworks.json` and its PDF, print notes and preview appear on its detail page.

The original-art gallery is a selected artist portfolio presented as a visual journal: a compact index with every selected artwork visible, grouped in rows of three tall and three wide frames. Each framed image and title opens its own detail page; only the poetic line accompanies the index card. Longer reflections and downloads live on the detail pages. Returning to the index lands at the same artwork. No pagination or “Show more” control is used. Captions and narratives are contemporary AI-assisted readings, not invented biographical memories or claims about original intent. Choose works for compositional strength, expressive gesture, distinct contribution and readable presentation; do not add every source study or repeated motif. Quiet and abstract work can qualify without a literal story. Preserve unchanged source files when archiving works. `catalog/artwork-review.json` records curatorial decisions, source checksums, signature context and sources awaiting review. BAPU/bapu is the artist’s family nickname, confirmed by him; that inscription alone is not an attribution concern.

The artist describes the grouped, softly bounded figures as an assembly of people in an inner sense. Preserve this inward-assembly strand in the portfolio; do not frame it as ghosts or exclude it merely for low contrast. `catalog/artwork-review.json` distinguishes that artist explanation from contemporary companion readings.

Artwork framing is presentation-only: `presentation.frame` and `presentation.mat` in `catalog/artworks.json` select oak, walnut or charcoal frames and ivory, linen or mist mats. `web/art-frames.css` creates the wall, bevels and shadows without changing source images or download files.

Artwork uses exactly two fixed outer frame sizes per display context, matching the approved preview: tall (2:3) and wide (4:3). The index uses 225 × 337.5 pixel tall frames and 300 × 225 pixel wide frames. Detail and language pages scale those same two variants for their available space. Never resize the outer frame to an individual artwork’s proportions.

Inner openings fit their original images except for eight artist-approved works using the fuller fixed opening and sampled background: The Witness (`art-64`), Ember (`art-47`), Remembered (`art-21`), The Gathering (`art-22`), Held (`art-20`), Grandmother (`art-07`), The Offering (`art-01`) and Together (`art-15`). The artist approved the first four after review and requested restoring filler for the latter four. All other works, including Resolve and The Balance, retain image-fitted inner openings.

Constrain fitted openings by both available width and height, center them, and let the neutral woven-cloth mount fill the remaining space. Preserve the wood and fine inner border. Images and downloadable originals remain uncropped, unstretched and unchanged. Sampled background extensions are hidden for fitted openings; source rectangles and generated assets remain available for fuller openings. Desktop rows retain the approved tall/wide grouping; tablet cards flow continuously into two columns, and phones use one column.

Artwork journal voice: write the feeling that remains after looking away—the emotional aftertaste. Keep titles short and phrases memorable. Descriptions should evoke recognition, tenderness, joy, longing or belonging, without explaining colours, shapes or technique. These are contemporary poetic readings, not biographical claims. The editorial direction is also recorded in `catalog/artworks.json`.

Multiple named music versions use accessible tabs in the Listen and Watch panels. Choosing a version synchronizes the matching audio/video tabs and pauses hidden players; direct version links reveal their tab. Without JavaScript all versions remain available.

Each language page includes one available refined print beneath its listening/video panel. The homepage uses the same edition pool: The Witness remains fixed in the invitation and the centre chooses another print per visit. `web/language-art.mjs` chooses a work once per page load; it stays still during playback and uses no cookies or visitor tracking. A language-specific fallback remains visible without JavaScript. Titles come from `catalog/artworks.json`; refined images and dimensions come from the matching `source_artwork_id` entries in `catalog/ai-artworks.json`. Archived works and standalone generated illustrations are excluded. Captions stay inside the print, with one image link to its detail-page edition. The artwork links to `artwork--<id>.html`, its Art Journal entry. Each selected work has a longer poetic reflection, the unchanged full-resolution original download, adjacent-work navigation and artwork-specific social metadata. Existing AI editions are linked by `source_artwork_id` in the AI catalog and shown separately. The Witness retains its artist-prepared canvas PDF.


The private archived-art journal is defined in `catalog/archived-artworks.json`. Rebuild it with `python scripts/build_archived_artworks.py --archive-root /path/to/preserved-archive`. The builder verifies both preview and master checksums, preserves historical selection notes, and writes `archived-artworks.html` only into the supplied archive folder. It does not restore works to the public portfolio. Tall and wide works alternate in groups of three; wide rows use compact wall containers. Clean background samples use proportional `cover` sizing in the inner gaps, while the shared gallery default remains unchanged. The photographs remain separate, untouched files.

AI refinement direction: preserve the original composition, pose, contours, brushwork and emotional character as closely as possible. Limit changes to gentle photographic cleanup and print presentation, using The Witness as the presentation reference. Do not regenerate or restyle the subject. Held is artist-approved. Twenty further editions are prepared for review, each with its source, exact prompt and method recorded in the catalog. Together with The Witness, 22 of the 24 selected artworks have a refined print edition. Unwatched was prepared on 2026-09-27 with its exact prompt retained. The Balance and Remembered remain pending: their latest image-tool attempts were rejected; their original captioned 4× JPEGs remain available. Originals are unchanged. These are edited editions, not pixel-identical restorations; actual output dimensions are displayed and are not described as 4× high-resolution originals.

Print-edition credit: the artist is Ahimanikya Satapathy. Use “Refined print edition” for these source-based refinements and a small “AI-assisted cleanup and print preparation” process note. Do not headline refinements as AI-generated art. The independently generated potter illustration retains its separate AI-generated provenance.

### Readable artwork captions

Gallery, detail, home and language-page frames use live HTML titles and poetic captions from `catalog/artworks.json`. Refined image files remain unchanged: `catalog/artwork-screen-layouts.json` records the display-only lower boundary above each print's raster title. The build generates CSP-compatible `assets/art-caption-layouts.css`; the illustrated region and signature remain visible, while live type replaces the small printed footer on screen. Downloads still link to the full print edition.

When adding a refined edition, inspect its boundary visually, preserve all illustrated content, and add its screen layout before using it in the shared art pool. Check the longest caption and landscape works at narrow mobile widths. Random art selection must update the image, display boundary, title, caption and link together. All gallery frames keep one size per viewport; captions must not be clipped or reduced below 15px.

Grandmother now uses a non-generative print prepared directly from `media/artworks/art-07.jpg`, superseding its generated v1/v2 portraits. `python scripts/prepare_grandmother_print.py` rebuilds the native captioned layout; `--check` verifies that the entire drawing region is pixel-identical to the decoded original. No paper cleanup, sharpening or facial retouching is applied inside that region. Run the print-download builder afterward. Earlier editions are preserved, with their metadata in `catalog/grandmother-print-history.json`. The active entry remains in the shared edition catalog for compatibility, with its non-generative method explicitly recorded.

The Gathering and The Hollow also use unchanged original pixels, replacing their generated editions. Reproduce with `python scripts/prepare_original_art_editions.py`, or verify with `--check`, then run the print builder. Native prepared PNGs preserve every decoded source pixel; 4× JPEG downloads use conventional resampling and lossy JPEG encoding, not pixel identity. No generated detail, sharpening, paint filling or contour correction is applied. Prior generated editions and metadata remain preserved.

### Four-times print downloads

Each available refined edition has a separate high-quality JPEG download under `media/prints/`, enlarged 4× in **each dimension** with Lanczos resampling. The entire existing captioned print is retained, including its title, poetic line, signature and artist credit. Source editions and originals are never overwritten. Gallery and language-page previews continue to use small source images; only the explicit download uses the large file.

To prepare new editions or refresh an edition after its source changes:

```sh
python -m pip install -r requirements-art-print.txt
python scripts/build_art_prints.py
python scripts/build_art_prints.py --check
python scripts/project.py build
```

The script derives paths from the repository, verifies source checksums, writes outputs atomically and reuses unchanged downloads. `print_download` records source and output checksums, exact dimensions, method, file size and the Pillow version in `catalog/ai-artworks.json`. The site build rejects missing, stale, altered or unhydrated print downloads. JPEG print files use Git LFS and both workflows retrieve them. No model, API or paid generation is involved.

The stored 300 ppi metadata is a print-sizing hint, not new detail. A typical 4096 × 6144 file corresponds to approximately 13.7 × 20.5 inches at 300 ppi or 27.3 × 41 inches at 150 ppi. Larger canvas quality depends on the source, material and viewing distance; inspect a sample at the intended print size. The artist-supplied Witness canvas PDF remains unchanged and separately available.

Originals also receive separate captioned 4× downloads: all selected original photographs are enlarged at their full native resolution, then placed on an ivory paper layout with title, poetic line and credit rendered at output resolution. Their `print_edition` records the exact enlarged art region and the larger final canvas dimensions. They use JPEG quality 95 with no chroma subsampling to keep very large original-photo downloads manageable. The unchanged original remains available separately. Refined JPEGs preserve their already-embedded lettering. The script processes both collections and bundles its print fonts and notices under `assets/print-fonts/`, without a dependency on the author’s laptop fonts.

All 4× downloads now use JPEG quality 95 and 4:4:4 colour sampling (no chroma subsampling). Refined RGB editions without a profile are treated as sRGB and tagged accordingly; existing source ICC profiles are retained. The small lossless refined PNG sources remain unchanged for future exports. JPEG is a delivery format; regenerate from the source instead of repeatedly re-saving a JPEG.
