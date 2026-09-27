---
type: Project guide
title: A shared baseline, room for every language
status: stable
---
# A shared baseline, room for every language

Start with a shared emotional intention: quiet joy, wonder, affection and the freedom to dream. Keep an unhurried pulse, space between the gathering phrases, a fuller breath after the potter declaration, and a hopeful ending. These are this poem’s creative intentions, not a preset for all poetry.

Each language keeps its own diction, melodic character, rhythm and chosen cultural influences. Controls below are a reproducible starting point; language and arrangement overrides can change them when there is a musical reason. English Country and Jazz, Tamil’s chosen tune and Sambalpuri’s local phrasing remain distinct choices.

| Control | Default |
|---|---|
| Model / creation mode | v6 / Advanced |
| Weirdness | 30% |
| Style Influence | 65% |
| Max Mode | On |
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

## How a language overrides the baseline

Resolve settings in this order: **shared baseline → adopted language overrides → adopted language/arrangement overrides → explicit directions for this run**. A reference cover additionally needs its approved source and applicable Audio Influence. Resolve any conflict before submitting; an unrelated language’s override must never leak into the next packet.

Every override records the changed control, value, musical reason, status (`proposed` or `adopted`) and a decision reference for adopted choices. Describe the expected audible effect and what a fluent speaker or musician should check on the language page. The queue helper exports adopted overrides and their provenance; proposed comparisons remain inactive. `--arrangement country`, for example, selects only that language’s registered control overrides, not a new lyric or style prompt. Review those inputs separately.

The policy currently has no registered language slider overrides. Existing regional prompts and musical reasoning already differ; they remain in place. The earlier English 65/75 comparisons are useful references, not evidence that 75 is best for all English songs. Do not invent a slider difference just to make a language seem distinctive.

An example **proposal**, not an adopted setting:

```json
{
  "language_overrides": {
    "english": {
      "status": "proposed",
      "settings": {"style_influence": 75},
      "reason": "Compare whether the more strongly directed arrangement keeps the poem's intimate delivery.",
      "decision_reference": null
    }
  }
}
```

Arrangement keys use `language/variation`, such as `english/country`. Keep exclusions open to reasoned overrides too: the shared list should not erase a locally appropriate ornament or instrument. Cultural context belongs in the musical explanation, not in assumptions about what every speaker enjoys.

## Why Max Mode is the starting point here

[Suno’s v6 FAQ](https://help.suno.com/en/articles/13924481) describes Max Mode as spending more credits on generation, particularly for longer songs, close-reference covers and consistency of voice and style. That fits the intended full-length songs in this project, so the future baseline is **On**. It does not guarantee a better melody, accurate language or preservation of a backing track. Standard mode remains a reasonable documented override for a short sketch or a budget-limited comparison. Check the current charge before an authorized generation; changing this policy does not authorize spending.

This is a project choice checked on 27 September 2026, not a timeless recommendation for every model. Published recordings and historical settings are not rewritten. Compare takes by listening for meaning, pronunciation, pacing, joy and natural musical expression; vary one control at a time when practical.

## Audit and source of truth

The 27 September audit found 17 tracked run records: 16 explicitly recorded Max Mode Off and one selected-track record had unknown controls. Three earlier runs recorded Weirdness 50; the other 13 known runs recorded 30. Exclusions were empty in several runs and missing from others; only the latest Tamil cover explicitly recorded the full shared list. These records do not establish settings for every older published track, and unknown fields remain unknown.

The machine-readable source is [production settings](https://github.com/ahimanikya/free-to-dream/blob/main/production/i-am-free-to-dream/settings.json). The queue helper resolves those defaults and adopted overrides, and copies their source hash into each prepared packet. Submitted `run.json` settings record what was actually verified in Suno, separately from the intended defaults and any exception.
