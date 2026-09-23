---
type: Project guide
title: Language collaboration and recording releases
status: draft
generated:
  by: process:collaboration-site
  at: '2026-09-23T02:19:02+00:00'
---
# Language collaboration and recording releases

Visitors choose a language, propose a change or submit a recording through the website. GitHub holds the actual submissions, attachments, comments and author identities. A submission is a proposal; it does not automatically replace lyrics or become a published recording.

## Contributor journey

1. Open a language page and choose **Suggest a change**, **Submit your version**, or **Review a recording**.
2. Describe the contribution. Include meaning, dialect, credits and actual listening timestamps where relevant.
3. Prepare the proposal, review the text, and continue on GitHub. Sign in or create your own GitHub account if needed.
4. Attach an MP3, WAV or supported video in the GitHub issue box, or include a public hosted link. For a long proposal, copy and paste the complete prepared text first.
5. Submit the issue and follow the conversation there. The language page links to its suggestions and submitted versions once the repository is connected.

The website never asks for a GitHub password or access token. GitHub handles sign-in and uploads. There is no anonymous on-site upload service.

## Review and publication

Maintainers discuss proposed changes with contributors. For lyrics, update the canonical language Markdown through a reviewed pull request and credit the contributor. For a recording:

1. Check that the supplied link is accessible while signed out and returns the media file, not a login page. Confirm the version's lyrics, credits, pronunciation and release details.
2. Register the accepted media URL with the `add-media` command in the [media guide](add-media.md). Give a new performance or take a new recording ID.
3. Complete the catalog entry. Set `review_status: approved`, `rights_status: confirmed`, and `publish: true` only after the actual review. Add the submission URL to the entry's notes so the decision remains traceable.
4. If the contributor's agreed terms permit file redistribution through social media, enable `allow_file_sharing: true`. This controls the file-sharing UI; record the actual terms separately in the notes or linked contribution record. Sharing a page link does not grant a blanket license over the underlying work.
5. Merge the catalog change to `main`. Once GitHub Pages is configured, the site rebuilds. The new recording appears on its language page and gets an individual `recording--ID.html` page.

Keep contributor submissions separate from releases until reviewed. A public GitHub attachment is already public even before a maintainer adds it to the site; the moderation gate controls inclusion in this collection, not visibility of the issue itself.

## Upload limits and large videos

GitHub's documented limits currently include 25 MB for non-image/video attachments, 10 MB videos on free repositories, and 100 MB videos on paid repositories, with additional account requirements for some larger uploads. MP3 and WAV attachments are supported in repository issue/comment contexts. Contributors should follow the limit GitHub shows for their account; a hosted media link is the fallback for a large video.

For files intended for public playback, test the final URL in the actual site. A storage host must allow playback; preparing a file for native sharing additionally needs browser cross-origin access. Do not use expiring links or private access tokens. An attachment link is not a guarantee of permanent hosting; retain source backups.

## Social sharing

Every published version has a stable page link and cover metadata for social previews, plus creator credits. Use **Share**, **Facebook**, **WhatsApp**, **Copy link**, or **Copy caption & credits**. A shared link leads listeners back to the project. Social networks decide whether to show a preview or player.

When file sharing is enabled, **Prepare file to share** fetches the file only after a click. **Share file** opens the device's share sheet where supported. Otherwise save/open the file and attach it in the social app. Large files and hosts without cross-origin access use that download/open fallback. No social post is made automatically.

Local review copies do not expose public sharing links. Public sharing and online submission require the real repository and site URLs in `site-config.json`.

## References

- [GitHub: static hosting with Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [GitHub: attaching files and current limits](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files)
- [GitHub: creating issues from URL parameters](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query)
- [MDN: Web Share API and browser support](https://developer.mozilla.org/en-US/docs/Web/API/Web_Share_API)
