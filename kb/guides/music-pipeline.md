---
type: Project guide
title: From language to song and video
status: stable
---
# From language to song and video

The author directs one language at a time. This is the agreed workflow for **I Am Free to Dream**.

1. **Choose a language.** Check that its lyric adaptation and cultural style prompt exist. A pending adaptation brief is not a finished translation. Prepare one Suno submission, normally two candidate takes, using the existing Pro account.
2. **Review the audio.** Share the candidate links and actual settings. Wait for the author to choose a take before downloading or publishing. Do not generate the next language automatically.
3. **Select a take.** The author's selection authorizes the remaining steps below for this project. A later request such as “audio only,” “hold publication” or “change the visuals” overrides the default.
4. **Download one MP3.** Reuse an existing verified download when it matches the chosen Suno ID. Downloading M4A, WAV or a Suno video is unnecessary for this workflow. Track the source URL, settings and checksum.
5. **Create the MP4.** Combine that exact soundtrack with the existing shared visual sequence, fitting the visuals to the complete song. Preserve audio speed and pitch. This is a soundtrack replacement, not a new lip-synced performance. Add timed lyrics only when checked timings for this exact take exist.
6. **Publish both.** Add separate audio and video records under the language folder using Git LFS. Update the inventories, listening page and audio playlist. Preserve earlier versions and existing translation-review status.
7. **Verify delivery.** Check the complete video decode, matching soundtrack, opening/middle/ending frames, upload checksums, browser playback and seeking, and the final website deployment. Return the listening page and downloads.

Selecting a take approves its publication as an author-selected listening preview. It does not certify the translation or sung pronunciation as reviewed by a fluent speaker.

## Render the selected video

The reusable renderer uses FFmpeg. Retrieve the shared source with Git LFS if needed. Use a new filename and work directory for each take:

```sh
python scripts/render_song_video.py \
  --audio media/bengali/i-am-free-to-dream-bengali.mp3 \
  --video media/odia/source/melodicpal-original.mp4 \
  --output /path/to/output/bengali-take-2.mp4 \
  --work-dir /path/to/private-work/bengali-take-2 \
  --title "স্বপ্ন দেখতে আমার মানা নেই" \
  --language ben
```

Pass `--ffmpeg /path/to/ffmpeg` if FFmpeg is not on PATH. The renderer refuses to overwrite an existing output, preserves the full audio, exports three frames for visual inspection and writes a validation report. Keep work folders and private run manifests out of Git.

This visual source belongs to this poem. A different poem or a request for new visual storytelling needs an appropriate visual choice rather than automatically reusing it.

See [media publishing](add-media.md) for catalog fields and [timed lyrics](timed-lyrics.md) for SRT handling.
