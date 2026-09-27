---
type: Project guide
title: Listening, sharing and community engagement
status: stable
---
# Listening, sharing and community engagement

The [engagement workspace](https://ahimanikya.github.io/free-to-dream/engagement.html) brings together the reporting setup and public GitHub inbox. Private analytics remain in the account you connect. This is a public static page, not a password-protected admin dashboard.

**Current state:** a dedicated **World is One** GA4 account and **World is One — Free to Dream** property were configured on 27 September 2026. The web stream uses measurement ID `G-GHF6GM8X6F`. Reporting uses India time and INR. Optional account data sharing and enhanced measurement are off; the site supplies its explicitly scoped events after visitor consent. Visits and plays before connection are not backfilled.

[Open World is One in Google Analytics](https://analytics.google.com/analytics/web/#/a409658719p556135543/reports/intelligenthome). Sign in with the owner’s Google account; the reports are private.

## What a number means

| Event | Meaning | Important limit |
|---|---|---|
| `page_view` | One page load after analytics consent | Reloads count; declined or blocked tracking is absent |
| `play_start` | A recording actually begins playing | Pause/resume does not create another start in the same playback cycle |
| `play_30s` | At least 30 seconds of observed playback in that cycle | Seeks do not add skipped time; short tracks may never reach this threshold |
| `listen_progress` | Observed listening reaches 25%, 50% or 75% of duration | Percentage is listened time relative to duration, not merely the seek position |
| `listen_complete` | Observed listening reaches 90% of duration | A project engagement measure, not a royalty or platform-certified stream |
| `share_intent` | Visitor opens a share action or chooses copy link/caption | Does not prove a post was published or reveal the sharer’s account |
| `download_click` | Visitor chooses a download/open link | Does not prove the transfer completed |
| `contribution_handoff` | Visitor continues from the prepared form to GitHub | The GitHub issue, not this click, proves a submission was created |

Audio and video use separate recording IDs and `media_kind` values. Count `play_start` or `play_30s` explicitly; do not add both and call the result plays. A repeat cycle is a new play. Metrics describe playback observed by the browser, including muted playback; they cannot prove someone heard it. Review copies retain their review status regardless of popularity.

## Connection and report setup

1. Create or choose a GA4 web property you control and a web data stream for the public site. The standard Analytics product can collect custom events; no analytics credentials belong in this repository.
2. In `site-config.json`, set `analytics.provider` to `ga4` and `analytics.measurement_id` to the stream’s public `G-…` identifier. Keep it `none` until the account is ready. The measurement ID is public; a reporting API secret or service-account key is not.
3. Disable enhanced measurement for automatic outbound clicks, downloads and form interactions in the GA4 stream so it does not duplicate or broaden the deliberately scoped events here. Leave advertising and Google signals disabled. Configure retention and access for your account.
4. Rebuild and deploy. Open the public site, allow optional analytics, play a track and check GA4 Realtime/DebugView. Local previews and a different host are excluded. Declining consent or blocking analytics must leave music playback usable.
5. Register event-scoped custom dimensions for `recording_id`, `language`, `media_kind`, `method`, and `contribution_type`. Use event count with event-name filters for views, starts, 30-second listens, completion and shares. `progress_percent` and `listen_seconds` can be registered as custom metrics if useful. Create report explorations after those definitions exist; custom definitions are not retroactive.
6. Build a listening report with recording/language rows and start, qualified-listen and completion counts; a sharing report with `method` and recording rows; and a page report with page path, source and date. Compare equal date ranges. Export aggregate results if you later want a public statistics section; do not publish credentials to query private reports from a static page.

The supplied tag loads only after opt-in and respects Do Not Track / Global Privacy Control. Read [privacy details](privacy.md). Connecting analytics later does not recover earlier visits or plays.

## Feedback that needs attention

New issues and contributor replies receive `needs-author`. A reply from the repository owner switches the issue to `awaiting-contributor`. Closing it clears both attention labels. Reopening recalculates the state from the latest human comment. Bot comments and pull requests are excluded. This is reply routing, not automatic acceptance of a translation or recording.

The workflow reads current issue state so delayed events do not override a newer reply. It creates its two labels when first needed; it does not post comments or change permissions. It runs only on future issue/reply events. Existing unlabelled issues appear as **Not yet triaged**; label these deliberately when reviewing the backlog. Manually use GitHub assignees, milestones and labels for accepted work, production and release. Pull requests remain in GitHub’s review queue.

The workspace fetches public issues on request, excludes pull requests, and marks a snapshot partial if its pagination limit is reached. Refresh errors and rate limits are displayed, not converted to zero counts. Comment authors and issue reporters are visible on GitHub. Sharing reports supplied by contributors remain separate from anonymous click metrics.

## Primary documentation

- [Google: custom event implementation](https://developers.google.com/analytics/devguides/collection/ga4/events).
- [Google: consent mode](https://developers.google.com/tag-platform/security/guides/consent).
- [GitHub: repository issues API](https://docs.github.com/en/rest/issues/issues#list-repository-issues).
- [Media Session API](https://developer.mozilla.org/en-US/docs/Web/API/Media_Session_API): browser/OS playback controls where supported.
