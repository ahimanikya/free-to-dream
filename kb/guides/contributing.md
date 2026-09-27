---
type: Project guide
title: Contribute a voice
status: draft
generated:
  by: process:repository-scaffold
  at: '2026-09-23T02:04:58+00:00'
---
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

## Explain a musical variation

Each language page includes “Why this version sounds this way.” Keep its explanation current when proposing a new arrangement:

1. Identify the local variety or musical influence and the reference that supports it.
2. Explain why the vocal phrasing, melodic shape, rhythm and instruments serve a particular image or movement in this poem. Separate documented practice from a new creative choice.
3. State the vocal choice. Solo is the default for new arrangements; duet, answering voices and group singing are optional proposals for the author to choose. Keep already selected versions as references.
4. Label the variation as proposed, author-selected or checked in a named recording. Give a reason for the change rather than rewriting the language's whole musical direction.
5. Tell a fluent singer or musician what to validate, with the exact take and timestamps when audio exists. Record corrections and the scope of any review.

For example, the Sambalpuri version draws on a specific duet reference and the poem's invitation to share dreams. That explains this arrangement; it does not imply that every Sambalpuri song is a duet. A suggested harmony on another page likewise remains optional until chosen.

## Media and credits

Use the [media guide](add-media.md). Give each take a new ID; retain the old take’s provenance. Track MP3/M4A files under their `media/<language>/` folders using Git LFS. Keep version-specific UTF-8 SRT lyrics beside their audio in ordinary Git; the site generates WebVTT. Existing videos are preserved and may be embedded as explicitly authorized previews. Keep earlier versions under distinct names; do not replace them silently. Ordinary large binary Git blobs and private references are rejected by the repository check. Use direct hosted URLs for released website players.

Do not submit material you are not entitled to share. If any part is someone else’s work, identify the source and applicable permission. Before acceptance, explicitly confirm CC BY 4.0 for text, prompts and artwork you control, or MIT for code. Recording submissions need a separate explicit grant; the content license does not cover their music, performance or third-party elements. Earlier external contributions retain their agreed terms. See [RIGHTS.md](rights.md).

After editing, run the validation, tests and public build described in the README. Maintainers review and merge proposals; generated site and wiki copies should not be edited directly.
