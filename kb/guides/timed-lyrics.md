---
type: Project guide
title: Timed lyrics for each recording
status: draft
---
# Timed lyrics for each recording

An SRT is a text file containing lyrics and their start/end times. It does not contain sound. Keep the MP3 or M4A as the recording and add a separate SRT for that exact take.

## Prepare and review

1. Listen to the exact recording in a subtitle editor. Include the words actually sung, including repetitions. Keep the poem’s unarranged text on its language page.
2. Write UTF-8 SRT with consecutive cue numbers starting at 1 and `HH:MM:SS,mmm --> HH:MM:SS,mmm` timestamps. Use plain lyric text; markup is displayed literally. Keep cues in order, with positive durations and no overlaps.
3. Check the opening, a middle stanza and the ending against playback, then review every cue. Leave intentional instrumental gaps empty. Check native-script shaping and line wrapping on a phone.
4. Attach the SRT to the exact recording ID:

```sh
python scripts/project.py add-lyrics --id english-audio-country --file "/path/to/checked-lyrics.srt"
python scripts/project.py build --local-media
python scripts/project.py serve
```

The command requires an audio record with `repo_path`; use its actual ID from `catalog/recordings.json`. It stores the SRT beside the audio with the same filename stem and binds it to the audio’s SHA-256 checksum. Replacing the audio makes validation fail until the lyrics are checked, retimed and attached again. Prefer a new recording ID for a new take.

Commit the SRT and catalog update through a pull request. Text changes are visible in ordinary Git diffs. Attaching or validating an SRT does not certify its listening accuracy or publish the recording.

## On the website

The build generates WebVTT (`.vtt`) and playback cues from the SRT. The player displays the current lyric using the audio’s playback time, including after seeking or changing playback speed. SRT and WebVTT downloads appear beside each available timed recording. Generated files are not edited or committed separately.

Without an SRT, the player remains usable and shows that timed lyrics are pending. Timings must be measured against the recording; do not estimate them from poem length or another language’s video. No verified SRTs have been added yet.

## Files and hosting

Keep MP3/M4A recordings in Git LFS, and SRT, credits, poems and appropriately sized artwork in regular Git. Existing MP4 exports are retained in the archive; new contributions are audio-first. Do not regenerate a video for every lyric correction.

For a larger public audience, a dedicated media host such as Cloudflare R2 can serve the audio through stable HTTPS URLs in the catalog, while Git remains the source for lyrics and metadata. No external storage migration is configured by this update. Test seeking and browser playback before switching published URLs.
