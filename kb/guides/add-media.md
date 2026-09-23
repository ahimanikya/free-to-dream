---
type: Project guide
title: Add a recording or image
status: draft
generated:
  by: process:repository-scaffold
  at: '2026-09-23T02:04:58+00:00'
---
# Add a recording or image

Each take gets its own recording ID. The editable language page remains independent of any particular audio/video take.

## Add an MP3 or MP4 locally

From the repository folder, with the Python environment activated:

```sh
python scripts/project.py add-media --language hindi --id hindi-audio-01 --kind audio --title "Hindi · first take" --file "/path/to/song.mp3"
python scripts/project.py build --local-media
python scripts/project.py serve
```

For video, use `--kind video` and an MP4 file. Language slugs match the filenames under `kb/poems/i-am-free-to-dream/languages/`. The command copies the file into the ignored local archive, records its checksum and creates a review draft. Existing takes are retained. Use a new ID for a new take.

Audio options accepted: MP3, M4A, WAV, OGG. Video: MP4, WebM. MP3 and MP4 are practical preview formats; keep lossless audio masters in your archive. Actual playback depends on the codec and browser.

## Add hosted media

Upload a release copy to a media host you control, then register its direct HTTPS file URL:

```sh
python scripts/project.py add-media --language hindi --id hindi-audio-02 --kind audio --title "Hindi · reviewed take" --url "https://media.example.org/hindi-audio-02.mp3"
```

The example URL is a placeholder. A normal Suno, Drive or YouTube sharing page is not a direct audio/video file URL. Such pages can be linked in the language Markdown instead. Use stable URLs without expiring private access tokens. Test the URL in a signed-out browser; the host should serve the correct media type and support byte ranges for seeking. Some hosts redirect to forced downloads or block embedding, so verify actual playback before publishing.

In `catalog/recordings.json`, complete the credits and notes. After actual review and release checks, set `review_status` to `approved`, `rights_status` to `confirmed`, and `publish` to `true`. These are deliberate maintainer decisions; the import tool never applies them automatically.

Rebuild with `python scripts/project.py build` to see the public version. The public build embeds only release-approved remote media and never copies `local-assets/`.

## Add an image

Put a reasonably sized JPG, PNG or WebP under `media/images/`. Record its creator, generation method and permissions alongside it. Do not add personal reference photos or private evidence there. The current site uses `cover.png` for its collection artwork and video posters. `social-cover.jpg` preserves the existing Odia social cover. Replace shared artwork deliberately if changing the design.

## Backups

Git does not back up ignored media. Keep a separate backup of `local-assets/` and your masters. `catalog/asset-inventory.json` records hashes and original filenames so copies can be identified and deduplicated.
