---
type: Project guide
title: Discovery, search and AI readers
status: stable
---
# Discovery, search and AI readers

Make the content useful and verifiable first. Clear source text, internal links, authorship, review status and reuse terms serve both readers and automated tools. No search ranking, AI citation or population-coverage claim follows from the number of language entries.

## What the site publishes

- Static readable HTML and original UTF-8 Markdown, without requiring JavaScript to read a poem or production guide.
- Distinct titles and descriptions, canonical URLs and JSON-LD describing the site, pages, poem and public audio/video. Metadata follows visible content; a pending brief is not labeled a completed translation. No invented publication dates or reviewer identities.
- A sitemap containing canonical public reading pages. Timing tools and contribution forms are marked `noindex`; local previews are also `noindex`. Private media is absent from both the public build and the reference feed.
- Native-language tags around completed poem text where a language code has been verified. The interface remains English. We do not publish misleading `hreflang` alternatives for English-language briefs or claim that the entire UI is translated.
- `reference.json`: source links/hashes, lyric and review status, musical reasoning, effective intended controls and authorized current recordings. It deliberately excludes private file paths and unselected production candidates.
- `llms.txt`: a convenience index following an emerging proposal, not a special ranking mechanism. Structured data and machine-readable text do not guarantee that an AI system will retrieve or cite a page.

## Deployment and owner follow-up

After publication, verify ownership of the site in Google Search Console, submit the sitemap URL and inspect a few language/recording URLs. Indexing depends on the search engine; it can take time or a page may not be selected. Test video pages with the Rich Results Test, but do not fabricate missing upload dates to qualify for a result.

This is a GitHub Pages **project site** under `/free-to-dream/`. Crawlers use `robots.txt` at the domain root, not a file inside this project path. We therefore do not pretend a project-level robots file controls crawling. Any domain-root crawler policy requires the owner of that root site. Page-level robots metadata controls indexing requests for this project’s utility pages. Ordinary content is crawlable; the project itself imposes no crawler-specific block.

## Primary references

- [Google: AI features and your website](https://developers.google.com/search/docs/appearance/ai-features): ordinary SEO practices apply; no special AI file or schema is required.
- [Google: build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
- [Google: localized versions](https://developers.google.com/search/docs/specialty/international/localized-versions).
- [Google: video structured data](https://developers.google.com/search/docs/appearance/structured-data/video).
- [llms.txt proposal](https://llmstxt.org/): optional machine-readable discovery conventions.

These practices were reviewed on 27 September 2026. Keep the technical guidance current without rewriting historical production evidence.
