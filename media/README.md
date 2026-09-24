# Audio recordings and video archive

The actual song and video files are tracked in these folders using Git LFS. The archive currently contains **25 files: 10 audio files and 15 videos**, including previous revisions and the shared visual source. Historical drafts are labeled in each folder.

- [Odia](odia/README.md)
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

The active workflow uses **MP3 or M4A + cover artwork + version-specific SRT**. Follow the [audio import guide](../kb/guides/add-media.md) and [timed lyrics guide](../kb/guides/timed-lyrics.md). Existing MP4s remain archival exports in their current folders. No files or history have been deleted.

SRT stays in ordinary Git beside its matching audio. The website derives WebVTT and follows audio playback time; each country, jazz or regenerated take needs its own timings. Audio uploads default to MP3/M4A; the broader LFS rules below preserve the older archive.

Place each file under its language folder with a new version name. Run `git add` and `git commit` with Git LFS installed, then push. The `.gitattributes` rules route MP3, MP4, M4A, WAV, OGG, MOV and WebM files under `media/` through LFS. The repository check rejects accidentally committed ordinary media blobs.

The listening website embeds explicitly authorized previews and approved releases. Historical takes appear under Earlier versions; archiving does not delete a take or certify it as a release.

## Unavailable originals

- Two early Odia MP3 takes named with (1) and (2) are no longer present at their supplied paths.
- The original Telugu v1 MP3 is unavailable; its encoded soundtrack is preserved as M4A extracted from the v1 video.
