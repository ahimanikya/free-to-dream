# Audio recordings and video archive

The actual song and video files are tracked in these folders using Git LFS. The archive currently contains **29 files: 12 audio files and 17 videos**, including previous revisions and the shared visual source. Historical drafts are labeled in each folder.

- [Odia](odia/README.md)
- [Bengali](bengali/README.md)
- [Italian](italian/README.md)
- [Malayalam](malayalam/README.md)
- [Tamil](tamil/README.md)
- [Telugu](telugu/README.md)
- [English · Country](english/country/README.md)
- [English · Jazz](english/jazz/README.md)
- [Filipino / Tagalog](filipino/README.md)

## Download a working copy

Install [Git LFS](https://git-lfs.com/), then run:

```sh
git lfs install
git clone https://github.com/ahimanikya/free-to-dream.git
```

For an existing checkout:

```sh
git pull
git lfs pull
```

GitHub Releases provide separate download links. A source ZIP may contain LFS pointers rather than full media; use an LFS-enabled clone or the download links.

## Add future versions

The author’s [production workflow](../kb/guides/music-pipeline.md) uses **one selected MP3 + a matching MP4**, with cover artwork and checked version-specific SRT when available. Community recordings can also use M4A. Follow the [audio import guide](../kb/guides/add-media.md) and [timed lyrics guide](../kb/guides/timed-lyrics.md). New matching MP4s and earlier exports remain in their language folders. No files or history have been deleted.

SRT stays in ordinary Git beside its matching audio. The website derives WebVTT and follows audio playback time; each country, jazz or regenerated take needs its own timings. Suno downloads default to MP3 only; the broader LFS rules below preserve the older archive.

Place each file under its language folder with a new version name. Run `git add` and `git commit` with Git LFS installed, then push. The `.gitattributes` rules route MP3, MP4, M4A, WAV, OGG, MOV and WebM files under `media/` through LFS. The repository check rejects accidentally committed ordinary media blobs.

The listening website embeds explicitly authorized previews and approved releases. Historical takes appear under Earlier versions; archiving does not delete a take or certify it as a release.

## Unavailable originals

- Two early Odia MP3 takes named with (1) and (2) are no longer present at their supplied paths.
- The original Telugu v1 MP3 is unavailable; its encoded soundtrack is preserved as M4A extracted from the v1 video.
