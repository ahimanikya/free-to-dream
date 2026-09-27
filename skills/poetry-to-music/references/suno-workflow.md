# Suno browser workflow

Use the browser skill for setup and interaction; this reference adds production context, not an alternate automation interface.

## Before generation

Confirm the visible profile matches the intended account (`ahimanikya` in the established project). Inspect current credits, download allowance, model and controls. Do not hard-code plan quotas. Do not silently enable higher-cost modes. If the exact charge is unavailable, say so and keep the run bounded by authorized submissions.

Check packet source hashes against current Markdown. Reconcile updated user text before generating. Keep the lyrics fixed during style comparisons unless the user requested an arrangement change.

For *I Am Free to Dream*, resolve intended controls from `production/i-am-free-to-dream/settings.json`, resolving baseline → adopted language → adopted language/arrangement controls and exclusions. Load the current revision rather than copying a historical run. Reference covers apply the policy's cover override only after the author chooses that workflow and the exact source is attached. Explicit author instructions can override the baseline; document the exception before spending. Verify Max Mode against the resolved policy; do not inherit it from browser state or silently change model. Record unavailable controls honestly and resolve any material mismatch before submitting.

## One submission

1. Locate custom/advanced creation in the live UI. Use observed fields, not assumed historical selectors.
2. Enter title, complete lyrics, style and chosen controls. Preserve native-script punctuation and stanza breaks. Check actual field contents and limits before submitting. Shorten an over-limit style carefully; do not silently truncate lyrics or invoke lyric rewriting.
3. Compare every applicable visible control with the packet after the final form change: model/mode, Weirdness, Style Influence, Max Mode, Personalize, Variety, duration, Vocal Gender, exclusions and Audio Influence when a reference is attached. Record the verified actual values, policy revision/hash, any exception, submitted text, time and intended output count. Never treat browser defaults or retained settings as verification. Record UI defaults as defaults, not as author preferences.
4. Click Create once. A submission may generate multiple candidates; discover its actual results.
5. Record candidate links/IDs and visible completion/error states. On an ambiguous result, inspect the library before retrying. If still uncertain, stop that item and preserve its state rather than add duplicate charges.
6. Preserve earlier takes. Identify recordings by poem, language and take ID rather than title alone.

Login prompts, CAPTCHA, payment screens, exhausted allowance and unavailable download permissions stop the dependent action. Request the specific user action only when needed. Do not solve challenges, buy allowance or bypass download controls.

## Review and download

Present candidate links without unsupported musical rankings. Select only from the user's choice or explicit rule, such as “download the first completed take as a review candidate.” Selection by rule does not imply pronunciation or musical approval.

Use normal Download MP3 controls and supported browser download handling. Confirm a completed audio file arrived and match it to the candidate ID. If download quota blocks it, retain the link and mark it download-pending.

The run manifest should retain: language, source hash, submitted text/settings, timestamp, candidate IDs/URLs, chosen candidate, repository media path, audio hash/duration, publication commit and public URL. Stages include prepared, submitted, generated, selection-pending, download-pending, downloaded, imported and published. Record failures alongside the last verified state for safe resumption.

A paid subscription or successful generation is not proof of all copyright or pronunciation checks. Preserve existing collection flags; keep permitted-download evidence and account-plan details in private production notes when available.
