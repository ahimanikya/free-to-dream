---
type: Project guide
title: Add audio, timed lyrics or artwork
status: draft
generated:
  by: process:repository-scaffold
  at: '2026-09-23T02:04:58+00:00'
---
# Add audio, timed lyrics or artwork

Each take gets its own recording ID. The editable language page remains independent of any particular audio take.

## Add an MP3 or M4A locally

From the repository folder, with the Python environment activated:

```sh
python scripts/project.py add-media --language hindi --id hindi-audio-01 --title "Hindi · first take" --file "/path/to/song.mp3"
python scripts/project.py build --local-media
python scripts/project.py serve
```

Language slugs match the filenames under `kb/poems/i-am-free-to-dream/languages/`. The command copies the file into `media/<language>/`, records its checksum and `repo_path`, and creates a review draft. These folders are tracked with Git LFS. Install Git LFS (`git lfs install`) before staging/committing, then commit the media and catalog changes and push. Existing takes are retained; use a new ID for a new take. Run `git lfs pull` after cloning to retrieve the full recordings.

New recordings accept MP3 or M4A. Keep the original format; do not convert MP3 to M4A just to duplicate it. Existing videos remain in Git LFS and can be embedded alongside audio; earlier versions are grouped separately. Keep lossless masters in a separate backup. Actual playback depends on the codec and browser.

## Add timed lyrics

Follow the [SRT timing guide](timed-lyrics.md). Each recording gets its own UTF-8 SRT beside its audio file. The build derives WebVTT and the synchronized on-screen lyrics from that source. Country, jazz and regenerated takes must have separate timings.

## Add hosted media

Upload a release copy to a media host you control, then register its direct HTTPS file URL:

```sh
python scripts/project.py add-media --language hindi --id hindi-audio-02 --title "Hindi · reviewed take" --url "https://media.example.org/hindi-audio-02.mp3"
```

The example URL is a placeholder. A normal Suno, Drive or YouTube sharing page is not a direct audio/video file URL. Such pages can be linked in the language Markdown instead. Use stable URLs without expiring private access tokens. Test the URL in a signed-out browser; the host should serve the correct media type and support byte ranges for seeking. Some hosts redirect to forced downloads or block embedding, so verify actual playback before publishing.

In `catalog/recordings.json`, complete the credits and notes. After actual review and release checks, set `review_status` to `approved`, `rights_status` to `confirmed`, and `publish` to `true`. These are deliberate maintainer decisions; the import tool never applies them automatically.

Rebuild with `python scripts/project.py build` to see the public version. The public build embeds only author-authorized previews or release-approved remote media and never copies `local-assets/`.

## Share a review copy with inline players

When the author or designated maintainer explicitly requests a public listening preview, set `public_preview: true`, supply a stable direct HTTPS `public_url`, and record that authorization in `preview_authorization`. Keep `publish: false` and the actual review/rights statuses until release checks are complete. The website labels it as a review copy, offers playback and a shareable page, and does not imply translation or pronunciation approval.

Every language page has **Listen** and **Watch** sections. Authorized audio/video recordings appear automatically; `archived: true` groups a take under **Earlier versions** without deleting its files. Unlisted/private records remain hidden from the public site. Set `allow_file_sharing` separately only when redistribution terms are established.

The existing collection uses Git LFS media URLs pinned to the commit containing each take. Keep an MP3/M4A URL and MP4 URL as separate catalog records; a GitHub blob page or LFS pointer is not a playable recording. Test play and seek in a browser before publishing a new host URL.

## Add an image

Put a reasonably sized JPG, PNG or WebP under `media/images/`. Record its creator, generation method and permissions alongside it. Do not add personal reference photos or private evidence there. The current site uses `cover.png` for its collection artwork and video posters. `social-cover.jpg` preserves the existing Odia social cover. Replace shared artwork deliberately if changing the design.

## Backups

Files under `media/<language>/` are backed by Git LFS; `catalog/media-archive.json` records the initial archive, and `catalog/asset-inventory.json` records hashes and original filenames. GitHub Releases provide additional full-file downloads. Keep a separate backup of ignored `local-assets/` private references and local working copies. Source ZIPs may contain LFS pointers; use an LFS-enabled clone for the complete archive.
