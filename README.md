# World is One, India is One!

**One poem. Many voices. Shared dreams.**

A collaborative home for Ahimanikya Satapathy’s Odia poem **“ମୋତେ ସପ୍ନ ଦେଖିବାକୁ ମନା ନାହିଁ” / “I Am Free to Dream”** and its language adaptations, musical directions and recordings.

The starting collection has **100 language entries: 28 original/adapted lyric texts and 72 adaptation briefs**. They are not 100 finished songs. AI-assisted drafts need native-speaker review; musical prompts are creative proposals, not verified performances.

## Start here

- [Browse the knowledge base](kb/index.md)
- [Original Odia poem](kb/poems/i-am-free-to-dream/original.md)
- [All language entries](kb/poems/i-am-free-to-dream/languages/index.md)
- [Meaning and adaptation guide](kb/poems/i-am-free-to-dream/meaning.md)
- [How to contribute](CONTRIBUTING.md)
- [Audio and video files in Git](media/README.md)
- [Add an audio or video recording](kb/guides/add-media.md)
- [Publish the listening site and export a GitHub wiki](kb/guides/publishing.md)
- [Credits and rights](RIGHTS.md)

## Collaborate through the website

Each language page offers **Suggest a change**, **Submit your version**, and **Review a recording**. Visitors prepare a proposal on the site and continue to GitHub with its details filled in. They sign in there, attach an MP3/WAV/video or paste a hosted link, and submit. No coding or direct repository write access is required. Long proposals remain complete and use an explicit copy/paste step when they will not fit in a URL.

GitHub issues hold the conversation and submission history. Maintainers review contributions, merge lyric changes, and add accepted recordings to the catalog. The site is rebuilt after changes reach `main`. The source Markdown stays in `kb/`; contributors do not overwrite it by submitting a proposal.

Every available recording has its own page with a player, creator credits, a downloadable/openable media link and a listening-feedback action. Published pages offer native sharing, Facebook, WhatsApp and copy-link/caption controls. Social previews use the cover artwork. Media-file sharing can be enabled per released recording using `allow_file_sharing: true`; browsers or media hosts that cannot share a file directly fall back to saving/opening it and attaching it in the social app. Social networks decide how a shared link is displayed; the site cannot promise an inline player in every feed.

### Connect it

Set `repository_url` (for example, `https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY`) and `site_url` in `site-config.json`, enable GitHub Issues, and configure Pages to use GitHub Actions. Until these actual destinations are supplied, the local site lets you prepare and save proposals but does not pretend to submit them or offer public links to unpublished recordings.

This uses GitHub for sign-in, discussions and attachment storage. There are no repository access tokens in the website and no custom upload backend. GitHub attachments have size limits; contributors with large videos can use a hosted link. See the [collaboration and release guide](kb/guides/collaboration.md).

## Listen locally

Requires Python 3.10 or later. From this project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/project.py build --local-media
python scripts/project.py serve
```

Open **http://127.0.0.1:8765**. Search for a language, choose **Ready to listen**, and open its page. Native audio/video players support seeking. Odia and Tamil currently have local recordings; other entries clearly show when no recording is available.

The audio/video archive is tracked with **Git LFS** in language folders under [`media/`](media/README.md). Install Git LFS before cloning, or run `git lfs pull` in an existing checkout, to retrieve the full files. The ignored `local-assets/` folder retains private references and local working copies. Public listening pages still use explicitly approved recording URLs; archived drafts are not automatically promoted to releases.

## Where things live

| Folder | Purpose |
|---|---|
| `kb/` | Editable source: OKF v0.2 Markdown, provenance, language and review status |
| `catalog/recordings.json` | Recording IDs, credits, local paths, public URLs and release flags |
| `catalog/asset-inventory.json` | Checksums, archive paths and filenames of imported assets |
| `catalog/media-archive.json` | Complete versioned recording archive and unavailable originals |
| `catalog/import-provenance.json` | Original language-document body hashes at import |
| `media/<language>/` | Audio/video files tracked with Git LFS, version notes and checksums |
| `media/images/` | Shared cover images and their prompt |
| `local-assets/` | Ignored working media, masters and private reference material |
| `web/` | Listening-site design and search behavior |
| `scripts/` | Validation, site generation, media registration and wiki export |
| `site/` | Generated local listening preview; ignored |
| `site-public/` | Generated public build; ignored |
| `wiki-export/` | Generated GitHub wiki pages; ignored |

The `kb/` folder follows [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md). Its Markdown files are the source of truth. Every concept has YAML frontmatter; reserved `index.md` and `log.md` files follow the format’s separate rules. No human verification is implied by import or automated validation.

## Checks

```sh
python scripts/project.py validate
python -m unittest discover -s tests -v
node --test tests/collaboration.test.mjs
python scripts/project.py build
```

`build` without `--local-media` makes a public-safe site: it excludes archive recordings, LFS pointers, private reference photographs and publication evidence. Only recording entries explicitly approved for release are embedded remotely. Cover artwork and the language drafts remain part of the public build.

The GitHub check workflow validates changes and builds the public site. After Pages is enabled, the deployment workflow runs on pushes/merges to `main` and can also be run manually. Nothing is uploaded merely by preparing this repository locally. JavaScript tests require Node.js 18 or later; the website itself is static HTML/CSS/JavaScript.

## Working principle

Preserve the original; adapt with care; credit the people who help. Each musical setting should name its chosen cultural references while leaving room for other traditions in the same language.
