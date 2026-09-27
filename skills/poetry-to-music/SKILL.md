---
name: poetry-to-music
description: Prepare poetry and existing language adaptations for Suno, operate signed-in creation in bounded batches, track candidates and chosen takes, and publish selected songs and matching videos to a Git-hosted listening collection. Use for poetry music production, generation queues, and the author’s language-by-language review and publication workflow.
---

# Poetry to Music

Turn the author's poems into a traceable collection of songs. Preserve source writing and language-specific musical direction. Distinguish generated candidates, selected recordings, reviewed translations, and released songs.

## Context and scope

The established Suno account is `ahimanikya`, with Pro. Verify the current account and allowance in the normal UI; do not create another account, upgrade, or buy credits by default. The project is `ahimanikya/free-to-dream`; use the current repository root (`git rev-parse --show-toplevel`) and verify its remote. This repository copy is authoritative; do not rely on a personal skill installation or remembered laptop path.

For Ahimanikya’s *I Am Free to Dream* project, the agreed pipeline is: the author picks one language; generate one candidate pair from its existing lyric adaptation and local style; return both for review; wait for the author to select a take. That selection authorizes downloading its MP3, creating the matching MP4 from the existing shared visuals, and publishing both to GitHub and the listening site. Complete those steps without asking again. Do not start the next language automatically. “Audio only,” “hold publication,” or another explicit override takes precedence.

Download MP3 only by default; create the MP4 locally. Reuse an already downloaded file after verifying its take ID. Do not spend another download on M4A, WAV or a Suno video unless requested. Preserve the complete soundtrack at its original speed and pitch while fitting the shared visual sequence to it. Read [selected-take video](references/selected-take-video.md) at this stage.

Planning and queue audits do not authorize generation credits. New translations, subscriptions and different poems need their own scope. For other projects, do not infer publication authorization from a take selection alone.

## Prepare the queue

Read repository instructions and the current catalog. A pending adaptation brief may contain the Odia original or English meaning scaffold; never submit these as a target-language translation. Latest user edits supersede older drafts, but do not silently overwrite the original or another poem's arrangement.

For the established Markdown layout, run `python skills/poetry-to-music/scripts/prepare_queue.py --repo . --poem i-am-free-to-dream` from the repository root using the project's Python environment (PyYAML required). It only reports readiness unless given `--out NEW_DIRECTORY`, which writes exact title, lyrics, style, settings and a manifest. `--languages hindi,bengali` narrows the batch; `--include-recorded` explicitly includes languages with existing audio. It never contacts Suno or consumes credits. A new output directory prevents overwriting a prior run.

Source hashes identify stale packets. Preserve blank lines and arrangement labels. Missing lyrics or style blocks generation. Draft translations can be experimental recording candidates while retaining native-review status.

## Preserve each language's musical identity

Treat every language as carrying its own cultures, traditions and local variations, not just a different set of words. This applies to all languages in the collection, Indian and international. Use the language's existing musical direction and the author's chosen take as the baseline. Preserve its regional diction, speech rhythm, melodic phrasing, ornamentation, rhythmic feel and instrumental arrangement unless the author requests a change. Instrument names alone do not establish cultural character; keep local vocal and melodic differences explicit. Follow the chosen local variety rather than treating a language as having one uniform tradition.

For *I Am Free to Dream*, quiet joy, calm soulful delivery, gathering breaths and the fuller potter pause are the shared emotional foundation. They are not a generic musical template to apply across languages. English country and jazz remain distinct alternatives; Tamil and Sambalpuri retain their separately chosen musical variations. Other poems need their own interpretation. Follow the source's style and settings; a past slider value is not a universal preset.

When asked to carry a successful vocal treatment from one language to others, change only that vocal treatment and necessary section directions. Retain each target language's existing style wording and sung lyrics wherever possible; record the exact change before submission. Do not replace local musical direction with the source language's genre or a generic duet prompt.

**Solo is the default for new arrangements.** Duet, answering voices and group vocals are optional variations, not a collection-wide preset. Suggest an option when the poem and a specific local musical practice provide a useful reason; explain that reason and let the author choose before spending generation credits. Preserve already selected versions. Resolve unapproved shared-vocal suggestions in older notes to the solo baseline when preparing a new default packet, keeping the local musical direction intact.

When the author chooses the soft-duet option for *I Am Free to Dream*, use **male solo with soft female answering phrases, tender close-harmony duet at the end**. Keep the opening, verses and first chorus male-led; introduce brief, gentle female replies at the invitation and blend the voices at the final refrain/outro. Do not expand this into equal lead sharing, female-led verses, alternating lead verses or elaborate overlapping vocals unless requested. Sambalpuri is an author-selected variation with a documented duet reference, not evidence that all Sambalpuri music requires two singers.

Every language page must explain its musical decisions so collaborators can assess them: the chosen local variety or influence; why the phrasing, melody, rhythm, instruments and vocal format suit this poem; what is documented cultural context versus a contemporary creative choice; whether a variation is proposed, author-selected or verified in a particular recording; and what a fluent speaker or musician should check. Cite evidence for cultural claims and keep uncertainty explicit. Avoid universal claims about how a whole language or community sings. Preserve the existing language-specific rationale; give each subsequent variation its own reason and listening checks, tied to the exact take where available.

Distinguish preserving a style from preserving an existing recording's tune and backing. If the author asks to keep the published music, identify that exact recording and verify a suitable audio-based editing workflow before generating; a fresh text-only generation does not establish melody or backing preservation. Retain the published version until a replacement is selected. A correction to the production direction or skill alone does not authorize extra generation credits.

## Generate and track progress

Use the available browser skill and supported UI tools with the signed-in session. Read [Suno workflow](references/suno-workflow.md) when generating or downloading songs.

Record submissions, exact prompts/settings, candidate URLs and selected takes in `production/<poem>/<run-id>/run.json`. Commit this portable production record after each meaningful stage. Keep credentials, cookies, balances, account screenshots and temporary download paths out of these records; private temporary work is not the project memory. Read `production/README.md` before resuming. Historical runs record past choices and do not authorize new generation. Reconcile ambiguous submissions against the visible library before retrying. Resume incomplete work instead of creating duplicates. Use the ordinary UI; do not assume undocumented endpoints or a third-party API account are authorized.

File duration, decoding and metadata do not establish pronunciation, vocal warmth or musical quality. If direct audio analysis is unavailable, do not invent listening findings. The author or fluent reviewer selects takes unless the user supplies another rule. Rule-selected first-pass candidates are not pronunciation-approved recordings.

## Import and publish

Read [GitHub publication](references/github-publication.md) for the established collection. Download through Suno's normal permitted controls. Preserve each version and its source link. Import with Git LFS, validate the audio, record credits and actual review status, and update the catalog. Do not fabricate timed lyrics; SRT is optional and tied to the exact take.

When GitHub publication is requested or triggered by the agreed selected-take pipeline, finish both audio and video upload, registration, checks and live playback verification. Preparing files locally is not publication. Report generation, selection, download and publication separately.

Example requests: “Prepare all translated languages missing audio”; “Generate one candidate pair each for Hindi and Bengali”; “Resume the last batch without regenerating completed songs”; “Publish these selected MP3s and update the listening pages.”

## Portable project knowledge

Read `AGENTS.md` and `kb/guides/portable-workspace.md` in a fresh checkout. Skills and supporting scripts live in `skills/`; source meaning, musical decisions and validation guidance live in `kb/`; generation history and current confirmed direction live in `production/`; accepted recordings and their credits live in `catalog/` and Git LFS-backed `media/`. Update the relevant tracked record whenever a production decision changes. Scratch files may be discarded after durable results are saved. A browser-control tool and fresh account sign-in are environment capabilities, not secrets or session data to bundle into Git.
