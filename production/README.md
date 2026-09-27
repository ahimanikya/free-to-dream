# Production memory

Future-run controls: [shared settings policy](i-am-free-to-dream/settings.json) and [human-readable guide](../kb/guides/generation-settings.md). Verify the current policy against the UI; historical runs retain their actual values.

Current review: [soft-answer duet candidates, 27 September 2026](i-am-free-to-dream/duet-review-2026-09-27.md). Eight candidates await author selection; published recordings remain unchanged.

These records let another maintainer resume without the author's laptop or previous chat.

- `i-am-free-to-dream/*/run.json`: historical submitted lyrics, style, settings, candidate IDs, author selections and publication progress recovered on 27 September 2026.
- `i-am-free-to-dream/direction.json`: the confirmed Tamil/Sambalpuri reference and limited vocal-change scope. It does not authorize another generation.
- `catalog/recordings.json` (at the repository root): authoritative public playback and review status. Earlier published tracks without a run record still have catalog/media provenance; missing generation settings are unknown, not defaults to invent.

Historical duet experiments are not current defaults or approved replacements. Several were superseded by the author's request for a male solo with soft female answering phrases and a tender close-harmony ending. Preserve their IDs to avoid generating duplicates. For a new arrangement, solo is the default; the author must choose any optional variation. Before resuming an old run, reconcile its status with the catalog and latest author direction.

For each new run use `production/<poem>/<unique-run-id>/run.json`. Retain exact submitted title/lyrics/style, source path and hash, actual settings (unknown values explicitly marked), timestamps, candidate IDs/URLs, chosen candidate, stage, media repository paths/hashes, publication commits and verification results. Save prepared packets here too if they are needed to resume. Commit progress after each meaningful stage. A prepared packet or historical authorization is not permission to spend credits again.

Never commit passwords, cookies, tokens, account screenshots, balances, personal download paths or private copyright evidence. Use ignored `local-assets/` only for disposable work and private evidence, with a separately managed private backup if it must be retained. These files are not required to build the site or resume documented production.

The migrated snapshots preserve known facts; they are not listening evaluations. Original local account and quota evidence was deliberately excluded. Unselected candidates remain links hosted by Suno, not archived audio; download/archive only when authorized and permitted.
