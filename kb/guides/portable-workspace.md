---
type: Project guide
title: Work from any computer or a cloud workspace
status: stable
---
# Work from any computer or a cloud workspace

The repository holds the project knowledge and published media. Your laptop is a working copy, not the source of truth. Start with `AGENTS.md`, the project skill in `skills/poetry-to-music/`, and `production/README.md`.

## Cloud workspace

Open this repository in GitHub Codespaces using its Code menu. The checked-in `.devcontainer/` configuration installs Python 3.12, Node.js, Git LFS and FFmpeg, then installs the pinned Python dependencies. Cloud compute may use your account's allowance; creating a workspace is your choice. The same container definition can be used with another compatible development-container host.

From the repository root:

```sh
python scripts/project.py validate
python scripts/check_portability.py
python -m unittest discover -s tests -v
node --test tests/collaboration.test.mjs
python scripts/project.py build
python scripts/project.py serve
```

Open the forwarded port 8765 for a preview. Normal GitHub Actions checks and Pages publication already run in GitHub without your laptop.

## Prepare music

```sh
python skills/poetry-to-music/scripts/prepare_queue.py --repo . --poem i-am-free-to-dream
```

This reports readiness without contacting Suno. To save a packet, add `--languages hindi --out production/i-am-free-to-dream/hindi-new-run`; use a unique directory. Review the packet against current musical decisions before submission, including the solo default and any expressly chosen duet. The helper exports existing text faithfully; it does not decide or silently rewrite vocal treatment.

Use a supported signed-in browser to submit to the author's Suno account. Sign-in, available credits and download permission must be checked afresh. Browser automation depends on tools available in the current agent environment; Codespaces alone does not provide a logged-in Suno browser. Manual submission uses the same packets and tracked records. No undocumented Suno API is required.

## Render and publish media

Git LFS stores the published MP3/MP4 files and shared source video. Retrieve only the inputs needed for the chosen language:

```sh
git lfs pull --include="media/odia/source/melodicpal-original.mp4,media/bengali/i-am-free-to-dream-bengali.mp3"
python scripts/render_song_video.py --audio media/bengali/i-am-free-to-dream-bengali.mp3 --video media/odia/source/melodicpal-original.mp4 --output local-assets/render/bengali-new.mp4 --work-dir local-assets/render/bengali-new-check --title "স্বপ্ন দেখতে আমার মানা নেই" --language ben
```

This example renders an existing track; it neither generates a new song nor publishes it. Inspect the exported frames and validation report. For a new selected take, use its verified MP3 and follow [the production pipeline](music-pipeline.md) for catalog registration, Git LFS upload and live verification. Commit durable media hashes and validation results to its production record; do not retain an essential result only in scratch folders.

## What lives where

| Material | Durable home |
|---|---|
| Custom skill, queue helper, generation/download/publication guidance | `skills/poetry-to-music/` |
| Source poem, adaptations, meanings, musical choices, review guidance | `kb/` |
| Submitted prompts, settings, candidates, selections, current direction | `production/` |
| Public playback records, credits, hashes and versions | `catalog/` |
| Accepted audio/video and shared visual source | `media/`, using Git LFS |
| Art and site code | `media/images/`, `web/`, `scripts/` |
| Reproducible workspace and hosted checks/build | `.devcontainer/`, `.github/workflows/`, `requirements.txt` |

Private paper scans, rights evidence and unpublished personal references are intentionally not in this public repository. Back those up privately if needed; they are not site-build or rendering dependencies. Rejected/unselected takes may exist only as Suno links. The repo preserves their identity and settings where recorded, not a promise that Suno will host them forever.

## Maintenance

Edit the repository skill first. A personal installation is optional convenience and must not become a divergent source of instructions. An agent without automatic skill discovery can read `AGENTS.md` and the linked skill directly. Provider/browser tooling comes from that agent environment; the repo supplies the production procedure, not a copy of proprietary tools or credentials.

Keep production progress committed, and push after validation. A local edit becomes durable in GitHub only after publication. `scripts/check_portability.py` guards the operational records against machine-specific paths and account-session fields. Git history and LFS retain the published archive; retain an independent backup for long-term preservation.
