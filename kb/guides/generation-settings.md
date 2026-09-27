---
type: Project guide
title: Shared generation settings
status: stable
---
# Shared generation settings

Use one consistent starting point for future *I Am Free to Dream* recordings. Each language keeps its own lyrics, diction, melodic character, instruments and rhythm. The shared controls also apply to English Country/Jazz and author-requested duet variations.

| Control | Default |
|---|---|
| Model / creation mode | v6 / Advanced |
| Weirdness | 30% |
| Style Influence | 65% |
| Max Mode | Off |
| Personalize | Off |
| Variety | Normal |
| Duration | Auto |
| Vocal Gender control | Unselected; use the language’s vocal prompt |
| Audio Influence | Not applicable without an audio reference; 75% for an approved reference-based cover |

## Excluded styles

```text
EDM, heavy dance beats, aggressive percussion, theatrical belting, excessive vocal runs, vocoder, chopped vocals
```

Enter this list in the Exclude styles field. Keep gentle regional ornaments, local percussion, soft answering voices and close harmony where the arrangement calls for them. “Excessive vocal runs” does not prohibit all ornamentation. Solo remains the default for new arrangements; a duet needs the author’s choice.

## Before each submission

Check the actual visible controls against the prepared settings, including Max Mode, exclusions and Personalize. Recheck after opening Cover, reusing a prompt, switching tabs or loading an older song: a remembered or inherited value is not verification. Set the intended values explicitly, preserve the exact lyric and style, and record the checked settings before clicking Create once. An unavailable control is unknown or unavailable, never silently assumed. Verify a usable model before generating; do not silently substitute another model.

For a cover, identify and attach the exact approved recording. Use its musical prompt and words as the baseline, then apply only the authorized change. Audio Influence 75 is a starting setting, not a promise of identical backing or a percentage of audio retained.

## Deliberate comparisons

An explicit author request or approved comparison can override a default. Record the control, intended value, reason and author decision in the new run, and change one variable at a time where practical. Max Mode stays Off unless the author chooses a separate Max-On trial after its current behavior and charge are checked. A settings update does not authorize generation or spending.

The earlier English 65/75 comparisons remain valid references. Published recordings and historical settings are not rewritten to match today’s baseline. Different languages need different musical prompts, not automatically different sliders.

## Audit and source of truth

The 27 September audit found 17 tracked run records: 16 explicitly recorded Max Mode Off and one selected-track record had unknown controls. Three earlier runs recorded Weirdness 50; the other 13 known runs recorded 30. Exclusions were empty in several runs and missing from others; only the latest Tamil cover explicitly recorded the full shared list. These records do not establish settings for every older published track, and unknown fields remain unknown.

The machine-readable source is [production settings](https://github.com/ahimanikya/free-to-dream/blob/main/production/i-am-free-to-dream/settings.json). The queue helper copies those defaults and their source hash into each prepared packet. Submitted `run.json` settings record what was actually verified in Suno, separately from the intended defaults and any exception.
