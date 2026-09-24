# Contributing

Help a language version sound natural while keeping the poem’s meaning and tenderness. Native speakers, poets, musicians and listeners are welcome.

1. Find the language’s Markdown file under `kb/poems/i-am-free-to-dream/languages/`.
2. Open an issue describing the passage, suggested change and reason, or edit the file on GitHub and propose a pull request.
3. Name the dialect or regional tradition where relevant. Give a literal English gloss when a change affects meaning.
4. For a recording review, identify its recording ID and give actual timestamps. Distinguish pronunciation or missing words from personal musical preference. Do not claim to have listened when you have not.
5. Tell us the name you would like credited and your role. Do not identify other people without their permission.

## Review

The initial translation texts are AI-assisted drafts. Automated checks establish structure, not language quality. A suggested workflow is draft → native-language review → sung pronunciation/timing review → author or designated maintainer approval → release.

Use `review_status` to record progress and add named review notes in the page body. Never invent a reviewer or mark an entire page verified from a narrow spelling check. Keep OKF `status` for the concept lifecycle (`draft`, `stable`, `deprecated`); it is separate from recording release status.

The original Odia source must remain intact. Discuss any proposed source correction with the author. Preserve the gathering repetition, the pause after the potter declaration, and the final invitation to weave dreams together. Repetition for singing should be identified as arrangement rather than original wording.

A language is not a single musical style. Explain the region, form or instruments you propose and include a reliable reference where possible. Avoid presenting a prompt as proof that a generated track follows the tradition.

## Media and credits

Use the [media guide](kb/guides/add-media.md). Give each take a new ID; retain the old take’s provenance. Track MP3/M4A files under their `media/<language>/` folders using Git LFS. Keep version-specific UTF-8 SRT lyrics beside their audio in ordinary Git; the site generates WebVTT. Existing videos are preserved as archived exports. Keep earlier versions under distinct names; do not replace them silently. Ordinary large binary Git blobs and private references are rejected by the repository check. Use direct hosted URLs for released website players.

Do not submit material you are not entitled to share. If any part is someone else’s work, identify the source and applicable permission. Reuse and distribution terms for contributions must be agreed before release; this repository has no blanket open-content license. See [RIGHTS.md](RIGHTS.md).

After editing, run the validation, tests and public build described in the README. Maintainers review and merge proposals; generated site and wiki copies should not be edited directly.
