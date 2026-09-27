# Selected-take video

For Ahimanikya’s *I Am Free to Dream* collection, a take selection triggers both audio and video publication unless the author overrides that step. Reuse the verified selected MP3; do not regenerate it or download other Suno formats.

The maintained project guide is `kb/guides/music-pipeline.md`. Use the repository’s `scripts/render_song_video.py` with the chosen MP3, `media/odia/source/melodicpal-original.mp4`, a new MP4 output, a new private work directory, the title, and an ISO 639-2 language code. Use `--help` for arguments; provide the locally available FFmpeg path if necessary. Retrieve actual Git LFS media before rendering; pointer files are not inputs.

The renderer fits the visual sequence to the complete audio, preserving the soundtrack’s speed and pitch. It validates full decoding, compares the rendered soundtrack with the original, and exports opening/middle/ending frames. Inspect these frames before uploading. Do not claim the character lip-syncs to the translated vocals or invent timed lyrics. New subtitles require checked timings for that exact take.

Register audio and video separately under the language folder, sharing the selected Suno source URL and preserving credits and review status. Link the video to the selected audio ID in the catalog when useful. If audio was already published, add only the missing video and preserve its existing URL. Continue through Git LFS upload, catalog/inventory updates, live audio/video playback, playlist membership and successful deployment. Record selection, download, render, import and publication progress in the tracked production run manifest so a retry resumes rather than duplicates work.

The established shared visuals apply to this poem. A different poem or requested visual change needs a suitable source rather than automatic reuse.
