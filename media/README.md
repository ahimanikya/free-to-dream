# Song recordings in Git

The actual song and video files are tracked in these folders using Git LFS. The archive currently contains **23 files: 9 audio files and 14 videos**, including previous revisions and the shared visual source. Historical drafts are labeled in each folder.

- [Odia](odia/README.md)
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

Place each file under its language folder with a new version name. Run `git add` and `git commit` with Git LFS installed, then push. The `.gitattributes` rules route MP3, MP4, M4A, WAV, OGG, MOV and WebM files under `media/` through LFS. The repository check rejects accidentally committed ordinary media blobs.

The listening website only embeds explicitly published recordings; archiving a historical draft does not select it as the current take.

## Unavailable originals

- Two early Odia MP3 takes named with (1) and (2) are no longer present at their supplied paths.
- The original Telugu v1 MP3 is unavailable; its encoded soundtrack is preserved as M4A extracted from the v1 video.
