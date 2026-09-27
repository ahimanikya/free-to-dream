# Publish selected recordings

Repository: `https://github.com/ahimanikya/free-to-dream`
Site: `https://ahimanikya.github.io/free-to-dream/`

- Source lyrics/styles: `kb/poems/<poem>/languages/<language>.md`
- Catalog: `catalog/recordings.json`
- Inventories: `catalog/media-archive.json` and `catalog/asset-inventory.json`
- Audio: `media/<language>/<unique-recording-id>.mp3` or `.m4a`, Git LFS
- Matching video: `media/<language>/<unique-recording-id>.mp4`, Git LFS
- Optional SRT: same filename stem beside its exact audio take, ordinary Git

Read current repository guides and scripts. `scripts/project.py add-media` registers one audio draft but does not complete publication, all production metadata or version-pinned URLs. It currently assigns the `i-am-free-to-dream` poem ID: do not use unchanged for another poem. A new poem needs a verified schema/build extension rather than being mislabeled as the existing poem.

## Import

In the agreed *I Am Free to Dream* pipeline, an author-selected take triggers publishing its MP3 and matching locally rendered MP4. An earlier audio-only import should be completed by adding the missing video, without re-downloading the MP3. Read [selected-take video](selected-take-video.md) for rendering.

Verify actual audio decoding, duration and SHA-256 with available media tools. Reject LFS pointer text, HTML responses, empty files and duplicate IDs. Preserve earlier media and create a new ID for each version.

Register language, poem ID, title, kind, repo path, duration, credits, Suno source URL and actual review status. Keep archive/inventory entries consistent. A selected recording can be an author-authorized public preview without becoming a reviewed release. For those previews, use `public_preview: true`, record authorization, and retain `publish: false`, `needs-review` and the actual rights status. Set `allow_file_sharing` separately according to authorized distribution and project convention.

Use Git LFS, not ordinary binary Git blobs or base64 media in workflow files. Confirm staged pointers and uploaded object hashes. Keep local source paths, private account evidence and credentials out of public catalogs/workflows.

The established direct streaming URL is:
`https://media.githubusercontent.com/media/ahimanikya/free-to-dream/<media-commit>/media/<language>/<filename>`.
Commit/push media first, then pin catalog URLs to that commit. GitHub blob pages and Suno song pages are not direct media streams.

## Delivery

Prefer an available GitHub connector or authenticated Git/LFS client. Check current capabilities before assuming a browser workaround is needed.

If normal Git write authentication is unavailable, the previously used import pattern is: upload files as Release assets in the signed-in browser; verify size/hash; submit a temporary Actions workflow that downloads only named assets, verifies hashes/text baselines, validates the site, and commits/pushes Git LFS objects and catalog changes; remove the completed workflow. Respect the session's authorization for that write-enabled workflow—this reference grants none. Use preview labels without asserting native review, and protect concurrent changes.

## Completion

Run validation, meaningful import tests, existing site/player tests, the site build and staged LFS check. Do not let a successful later shell command hide an earlier failed check. Verify final GitHub checks and Pages deployment.

Check the live language page, active playlist entry and direct media bytes/seek support; test browser playback when feasible. Archived takes stay outside the active playlist. Refresh local previews if affected. Report exactly which stages finished and link the published pages; do not imply that a public review copy is a verified translation.
