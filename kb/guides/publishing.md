---
type: Project guide
title: Publish the listening wiki
status: draft
generated:
  by: process:repository-scaffold
  at: '2026-09-23T02:04:58+00:00'
---
# Publish the listening wiki

The project has two complementary views: an editable Markdown knowledge base and a static listening site. GitHub Pages can host the listening site with real audio/video controls. A GitHub wiki can carry a generated copy of the text with links to those players.

## Prepare the repository

1. Create an empty repository in your Git account and push this local project when ready. A remote has not been configured by this scaffold.
2. Confirm the repository visibility and contribution/reuse terms. The collection contains AI-assisted drafts, clearly marked as such.
3. Set `repository_url` and `site_url` in `site-config.json` to your actual repository and eventual HTTPS site address. Leave them blank until known.
4. Track source recordings under `media/<language>/` with Git LFS. Complete recording credits and review, then use stable direct hosted URLs for the website players. Archive storage and website release status are separate; the public build excludes archived binaries and LFS pointers.

## Publish on GitHub Pages

1. In the repository’s Pages settings, choose **GitHub Actions** as the build source.
2. Run the manual **Publish listening wiki** workflow in the Actions tab.
3. Open its deployment URL and verify the language pages, mobile layout and each released player in a signed-out browser.

The regular check workflow builds without deploying. After Pages is enabled, the Pages workflow also deploys changes pushed or merged to `main`, so accepted contributions reach the site. Local recordings remain excluded from every public build. Before a release URL is supplied, the page states that no recording is published; the Odia page also links to the author’s chosen Suno take.

Enable Issues and set the actual `repository_url` to activate the contribution forms. The site prepares an issue; the visitor signs in and submits it on GitHub. See the [collaboration guide](collaboration.md) for reviewing suggestions, accepting uploaded recordings and enabling media sharing.

The static site uses relative asset paths, so it works beneath a repository path as well as a custom domain. A separate media host prevents the website repository from growing with every recording version.

## Optional GitHub wiki mirror

Enable your repository’s wiki and create its first page. After setting `site_url`, run:

```sh
python scripts/project.py export-wiki
```

Copy the generated `wiki-export/` Markdown files into the separate wiki checkout. Commit and push that checkout when ready. These pages link to the published listening site. Edit the canonical `kb/` documents and regenerate the mirror; editing both creates conflicting versions. No automatic wiki push is configured.

## References

- [GitHub Pages: custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub: adding or editing wiki pages](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)
- [GitHub: large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
