#!/usr/bin/env python3
"""Export exact Suno input packets from the collection without generating music."""
import argparse
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import yaml


def concept(path):
    text = path.read_text(encoding='utf-8')
    parts = text.split('---\n', 2)
    if not text.startswith('---\n') or len(parts) != 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict):
        raise ValueError(f'Invalid metadata in {path.name}')
    return meta, parts[2]


def section(body, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\s*\n(.*?)(?=^## |\Z)', body, re.M | re.S)
    return match[1].strip() if match else ''


def fenced(body, heading):
    match = re.search(r'^```(?:text)?\n(.*?)\n```', section(body, heading), re.M | re.S)
    return match[1] if match else ''


def settings_policy(repo, poem):
    path = repo / 'production' / poem / 'settings.json'
    if not path.exists():
        if poem == 'i-am-free-to-dream':
            raise ValueError('Missing shared generation settings; restore the policy before preparing this poem.')
        return None
    raw = path.read_bytes()
    policy = json.loads(raw)
    if policy.get('schema_version') != 1 or policy.get('poem') != poem or not policy.get('revision'):
        raise ValueError('Invalid settings policy identity or revision')
    defaults = policy.get('defaults', {})
    required = {'model', 'mode', 'weirdness', 'style_influence', 'max_mode',
                'personalize', 'variety', 'duration', 'vocal_gender', 'audio_influence', 'exclude_styles'}
    if set(defaults) != required:
        raise ValueError('Shared settings must name every supported control explicitly')
    for field in ('max_mode', 'personalize'):
        if type(defaults[field]) is not bool:
            raise ValueError(f'{field} must explicitly be true or false')
    for field in ('weirdness', 'style_influence'):
        if type(defaults[field]) is not int or not 0 <= defaults[field] <= 100:
            raise ValueError(f'{field} must be a percentage from 0 to 100')
    if defaults['audio_influence'] is not None:
        raise ValueError('The text-prompt baseline must have no audio reference influence')
    for field in ('model', 'mode', 'variety', 'duration', 'vocal_gender', 'exclude_styles'):
        if not isinstance(defaults[field], str) or not defaults[field].strip():
            raise ValueError(f'{field} must be explicit and nonempty')
    cover = policy.get('reference_cover_overrides', {})
    if set(cover) != {'audio_influence'} or type(cover['audio_influence']) is not int or not 0 <= cover['audio_influence'] <= 100:
        raise ValueError('Reference cover policy must explicitly name its audio influence')
    return dict(policy, source=str(path.relative_to(repo)), source_sha256=hashlib.sha256(raw).hexdigest())


def settings_text(policy, listening_checks):
    if not policy:
        return listening_checks
    lines = ['Intended text-prompt settings; verify in Suno before submission.',
             'Policy: ' + policy['source'] + ' @ ' + policy['revision'], '']
    for key, value in policy['defaults'].items():
        display = 'Not applicable without a reference' if value is None else ('On' if value is True else 'Off' if value is False else str(value))
        lines.append(f'{key}: {display}')
    lines += ['', 'For an author-approved reference cover only: audio_influence ' +
              str(policy['reference_cover_overrides']['audio_influence']) +
              '. Attach the exact reference and preserve its approved prompt/lyrics.',
              'Record any author-approved settings exception in the run.', '', listening_checks]
    return '\n'.join(lines)


def prepare(repo, poem, languages=None, include_recorded=False):
    repo = Path(repo).resolve()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', poem):
        raise ValueError('Use a lowercase poem slug with letters, digits and hyphens.')
    folder = repo / 'kb' / 'poems' / poem / 'languages'
    if not folder.is_dir():
        raise ValueError(f'Language source folder not found: {folder}')
    policy = settings_policy(repo, poem)
    recordings = json.loads((repo / 'catalog/recordings.json').read_text(encoding='utf-8'))
    audio = {r['language'] for r in recordings if r.get('poem') == poem and r.get('kind') == 'audio' and not r.get('archived')}
    entries, known = [], set()
    for path in sorted(folder.glob('*.md')):
        meta, body = concept(path)
        slug = meta.get('slug')
        if not slug:
            continue
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError(f'Invalid language slug in {path.name}')
        if slug in known:
            raise ValueError(f'Duplicate language slug: {slug}')
        known.add(slug)
        if languages and slug not in languages:
            continue
        lyrics = fenced(body, 'Poem / arranged lyrics')
        style = fenced(body, 'Style prompt')
        pending = 'pending' in str(meta.get('lyric_status', '')).lower()
        if pending or not lyrics.strip():
            state = 'lyrics-pending'
        elif not style.strip():
            state = 'style-pending'
        elif slug in audio and not include_recorded:
            state = 'already-recorded'
        else:
            state = 'prepared'
        entries.append(dict(language=slug, language_name=meta.get('language', slug),
            title=meta.get('title', slug), order=meta.get('collection_order', 999),
            source=str(path.relative_to(repo)), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            lyric_status=meta.get('lyric_status'), review_status=meta.get('review_status'),
            existing_audio=slug in audio, status=state, lyrics=lyrics if not pending else '',
            style=style, settings=settings_text(policy, section(body, 'Working settings and listening checks')),
            generation_settings=deepcopy(policy['defaults']) if policy else None,
            candidates=[], selected_candidate=None))
    if languages and languages - known:
        raise ValueError('Unknown language slugs: ' + ', '.join(sorted(languages - known)))
    entries.sort(key=lambda x: (x['order'], x['language']))
    return dict(schema_version=2, poem=poem, prepared_at=datetime.now(timezone.utc).isoformat(),
                settings_policy=policy,
                counts=dict(Counter(x['status'] for x in entries)), entries=entries)


def export(report, out):
    out = Path(out).expanduser()
    # Never overwrite a prior run's take selections or partial progress.
    out.mkdir(parents=True, exist_ok=False)
    (out / 'queue.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Poetry music generation queue', '',
             'Prepared inputs only. No songs generated and no credits used.', '',
             '| Language | Status | Existing audio |', '|---|---|---|']
    for entry in report['entries']:
        lines.append(f"| {entry['language_name']} | {entry['status']} | {'Yes' if entry['existing_audio'] else 'No'} |")
        if entry['status'] != 'prepared':
            continue
        packet = out / entry['language']
        packet.mkdir()
        for name in ('title', 'lyrics', 'style', 'settings'):
            (packet / (name + '.txt')).write_text(entry[name] + '\n', encoding='utf-8')
        if report.get('settings_policy'):
            policy = report['settings_policy']
            planned = dict(status='prepared-not-submitted', settings=entry['generation_settings'],
                           policy_source=policy['source'], policy_revision=policy['revision'],
                           policy_sha256=policy['source_sha256'],
                           reference_cover_overrides=policy['reference_cover_overrides'])
            (packet / 'settings.json').write_text(json.dumps(planned, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'queue.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--poem', default='i-am-free-to-dream')
    parser.add_argument('--languages', help='Comma-separated language slugs')
    parser.add_argument('--include-recorded', action='store_true')
    parser.add_argument('--out', type=Path, help='New directory for packets and a progress manifest')
    args = parser.parse_args()
    languages = {x.strip() for x in args.languages.split(',') if x.strip()} if args.languages else None
    try:
        report = prepare(args.repo, args.poem, languages, args.include_recorded)
        if args.out:
            export(report, args.out)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{exc}\n')
    print(json.dumps({'poem':report['poem'], 'counts':report['counts'],
        'prepared_languages':[x['language_name'] for x in report['entries'] if x['status']=='prepared'],
        'output':str(args.out) if args.out else None}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
