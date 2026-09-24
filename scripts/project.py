#!/usr/bin/env python3
"""Build the listening wiki from the OKF bundle; no external services required."""
import argparse
from functools import partial
import hashlib
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, urlparse, urlencode

import bleach
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'kb'
LANGUAGES = KB / 'poems/i-am-free-to-dream/languages'
esc = html.escape
MEDIA_EXTENSIONS = ('.mp3', '.mp4', '.m4a', '.wav', '.ogg', '.mov', '.webm')


def media_is_available(path):
    if not path.is_file():
        return False
    with path.open('rb') as stream:
        return not stream.read(128).startswith(b'version https://git-lfs.github.com/spec/v1\n')


def read_concept(path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        return {}, text
    pieces = text.split('---\n', 2)
    if len(pieces) != 3:
        raise ValueError(f'Unclosed frontmatter: {path}')
    data = yaml.safe_load(pieces[1])
    if not isinstance(data, dict):
        raise ValueError(f'Frontmatter must be a mapping: {path}')
    return data, pieces[2]


def records():
    return json.loads((ROOT / 'catalog/recordings.json').read_text())


def confined(relative, base=None):
    if base is None:
        base = ROOT
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f'Path escapes project: {relative}')
    return path


def safe_url(url):
    parsed = urlparse(url)
    return parsed.scheme == 'https' and bool(parsed.netloc) and not parsed.username and not parsed.password


def parse_srt(text):
    """Read plain UTF-8 SRT, rejecting ambiguous or overlapping lyric cues."""
    text = text.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text: raise ValueError('SRT must contain timed lyrics')
    stamp = r'(\d{2,}):([0-5]\d):([0-5]\d),(\d{3})'
    cues = []
    for number, block in enumerate(re.split(r'\n[ \t]*\n', text), 1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0].strip() != str(number):
            raise ValueError('SRT cues must be numbered consecutively starting at 1')
        match = re.fullmatch(stamp + r' --> ' + stamp, lines[1].strip())
        if not match: raise ValueError('Use SRT timestamps HH:MM:SS,mmm --> HH:MM:SS,mmm')
        values = list(map(int, match.groups()))
        def milliseconds(parts):
            h, m, sec, ms = parts
            return ((h * 60 + m) * 60 + sec) * 1000 + ms
        start, end = milliseconds(values[:4]), milliseconds(values[4:])
        lyric = '\n'.join(lines[2:]).strip()
        if end <= start or (cues and start < cues[-1]['end']):
            raise ValueError('SRT cues must have positive duration and must not overlap or run backwards')
        if not lyric or '-->' in lyric or any(ord(c) < 32 and c not in '\n\t' for c in lyric):
            raise ValueError('SRT cue needs plain lyric text')
        cues.append({'start': start, 'end': end, 'text': lyric})
    return cues


def vtt_timestamp(ms):
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02}.{ms:03}'


def make_vtt(cues):
    return 'WEBVTT\n\n' + '\n\n'.join(
        f'{i}\n{vtt_timestamp(c["start"])} --> {vtt_timestamp(c["end"])}\n{esc(c["text"], quote=False)}'
        for i, c in enumerate(cues, 1)) + '\n'


def recording_digest(item):
    relative = item.get('repo_path')
    if not relative: raise ValueError('Timed lyrics need an audio file in media/ to identify the exact take')
    source = confined(relative)
    with source.open('rb') as stream:
        header = stream.read(256)
    if header.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        match = re.search(rb'oid sha256:([a-f0-9]{64})\n', header)
        if not match: raise ValueError('Invalid audio LFS pointer')
        return match[1].decode()
    return hashlib.sha256(source.read_bytes()).hexdigest()


def timed_cues(item):
    timing = item.get('timed_lyrics')
    if not timing: return None
    if item['kind'] != 'audio': raise ValueError('Timed lyrics belong to an audio take')
    expected = str(Path(item['repo_path']).with_suffix('.srt'))
    if timing.get('srt_path') != expected: raise ValueError('SRT must sit beside its audio with the same filename stem')
    if timing.get('audio_sha256') != recording_digest(item):
        raise ValueError('Audio changed: retime and reattach the SRT for this take')
    return parse_srt(confined(expected).read_text(encoding='utf-8-sig'))


def add_lyrics(args):
    validate(skip_timing_id=args.id)
    items = records()
    item = next((x for x in items if x['id'] == args.id), None)
    if not item or item['kind'] != 'audio': raise ValueError('Choose an existing audio recording ID')
    source = Path(args.file).expanduser().resolve()
    if source.suffix.lower() != '.srt': raise ValueError('Expected a UTF-8 .srt file')
    text = source.read_text(encoding='utf-8-sig')
    parse_srt(text)
    digest = recording_digest(item)
    target = confined(str(Path(item['repo_path']).with_suffix('.srt')))
    target.write_text(text.replace('\r\n', '\n').replace('\r', '\n').strip()+'\n', encoding='utf-8')
    item['timed_lyrics'] = {'srt_path': str(target.relative_to(ROOT.resolve())), 'audio_sha256': digest}
    (ROOT/'catalog/recordings.json').write_text(json.dumps(items, ensure_ascii=False, indent=2)+'\n')
    print(f'Attached SRT to {args.id}. Check its timing against this exact recording in the local preview.')


def player_markup(item, url):
    kind = item['kind']
    attrs = ' playsinline poster="media/images/cover.png"' if kind == 'video' else ''
    player = f'<{kind} controls preload="none" aria-label="{esc(item["title"], quote=True)}"{attrs} src="{esc(url, quote=True)}"></{kind}>'
    if kind != 'audio': return player
    base = f'media/lyrics/{item["id"]}'
    timing = bool(item.get('timed_lyrics'))
    data = f' data-lyrics-url="{base}.json"' if timing else ''
    text = 'Play to follow the lyrics.' if timing else 'Timed lyrics are not available for this take yet.'
    downloads = f'<div class="action-row"><a href="{base}.srt" download>Download SRT</a><a href="{base}.vtt" download>Download WebVTT</a></div>' if timing else ''
    return f'<div class="audio-lyrics"{data}><img class="audio-cover" src="media/images/cover.png" width="160" alt="Shared collection cover" loading="lazy">{player}<p class="current-lyric" dir="auto">{text}</p>{downloads}</div>'


def publicly_available(item):
    return bool(item.get('publish') or item.get('public_preview'))


def recording_label(item):
    if item.get('publish'): return 'Published version'
    return 'Review copy · pronunciation and timing review open'


def has_lyrics(meta):
    return meta['lyric_status'] not in ('Adaptation pending', 'Transcription pending')


def validate(skip_timing_id=None):
    errors = []
    config = json.loads((ROOT / 'site-config.json').read_text())
    for name in ('site_url', 'repository_url', 'preferred_odia_suno_url'):
        if config.get(name) and not safe_url(config[name]):
            errors.append(f'{name} must be an HTTPS URL without embedded credentials')
    if config.get('repository_url'):
        parsed = urlparse(config['repository_url'])
        if parsed.netloc != 'github.com' or not re.fullmatch(r'/[\w.-]+/[\w.-]+/?', parsed.path) or parsed.query or parsed.fragment:
            errors.append('repository_url must identify a GitHub repository: https://github.com/owner/name')
    languages = []
    for path in sorted(KB.rglob('*.md')):
        try:
            meta, body = read_concept(path)
            if path.name in ('index.md', 'log.md'):
                allowed = {'okf_version'} if path == KB / 'index.md' else set()
                if set(meta) - allowed: raise ValueError('Reserved file has concept metadata')
                if path == KB / 'index.md' and str(meta.get('okf_version')) != '0.2':
                    raise ValueError('Bundle version must be 0.2')
                continue
            if not isinstance(meta.get('type'), str) or not meta['type'].strip():
                raise ValueError('Missing nonempty type')
            if meta.get('status', 'draft') not in ('draft', 'stable', 'deprecated'):
                raise ValueError('Invalid OKF lifecycle status')
            for source in meta.get('sources', []):
                if not source.get('resource'): raise ValueError('Source requires resource')
                resource = source['resource']
                if resource.startswith('/') and not confined(resource.lstrip('/'), KB).is_file():
                    raise ValueError(f'Missing source: {resource}')
            if path.parent == LANGUAGES:
                if meta.get('slug') != path.stem: raise ValueError('Slug must match filename')
                if not meta.get('language') or not meta.get('lyric_status'):
                    raise ValueError('Language and lyric_status are required')
                languages.append(meta)
        except (ValueError, yaml.YAMLError) as error:
            errors.append(f'{path.relative_to(ROOT)}: {error}')
    if not languages: errors.append('No language entries found')
    slugs = {x['slug'] for x in languages}
    ids = set()
    for item in records():
        try:
            ident = item['id']
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', ident) or ident in ids:
                raise ValueError('Invalid or duplicate recording ID')
            ids.add(ident)
            if item['language'] not in slugs: raise ValueError('Unknown language')
            if item['kind'] not in ('audio', 'video'): raise ValueError('Invalid media kind')
            if type(item.get('publish')) is not bool: raise ValueError('publish must be boolean')
            if type(item.get('allow_file_sharing', False)) is not bool: raise ValueError('allow_file_sharing must be boolean')
            if item.get('local_path'):
                confined(item['local_path'])
                if not item['local_path'].startswith('local-assets/'):
                    raise ValueError('Local recordings belong in local-assets/')
            if item.get('repo_path'):
                confined(item['repo_path'])
                if not item['repo_path'].startswith('media/') or Path(item['repo_path']).suffix.lower() not in MEDIA_EXTENSIONS:
                    raise ValueError('Tracked recordings belong under media/ with a supported extension')
            if item.get('public_url') and not safe_url(item['public_url']):
                raise ValueError('Public media URL must use HTTPS without embedded credentials')
            if type(item.get('archived', False)) is not bool: raise ValueError('archived must be boolean')
            if ident != skip_timing_id: timed_cues(item)
            if type(item.get('public_preview', False)) is not bool:
                raise ValueError('public_preview must be boolean')
            if item.get('public_preview'):
                if not item.get('public_url'): raise ValueError('Public preview needs a public_url')
                if not item.get('preview_authorization'): raise ValueError('Public preview needs recorded maintainer authorization')
                if not item.get('credits', {}).get('poem'): raise ValueError('Public preview needs poem credit')
            if item['publish']:
                if not item.get('public_url'): raise ValueError('Publication needs a public_url')
                if item.get('review_status') != 'approved': raise ValueError('Publication needs approved review')
                if item.get('rights_status') != 'confirmed': raise ValueError('Publication needs confirmed release details')
                if not item.get('credits', {}).get('poem'): raise ValueError('Publication needs poem credit')
        except (ValueError, KeyError, OSError) as error:
            errors.append(f'Recording {item.get("id", "?")}: {error}')
    if errors: raise ValueError('\n'.join(errors))
    return sorted(languages, key=lambda x: x['collection_order'])


def page_name(path):
    return str(path.resolve().relative_to(KB.resolve()).with_suffix('.html')).replace('/', '--')


def render_markdown(body, path):
    def resolve(match):
        label, target = match.group(1), match.group(2)
        if '://' in target or target.startswith('#') or target.startswith('mailto:'):
            return match.group(0)
        target_path = target.split('#', 1)[0]
        candidate = (KB / target_path.lstrip('/')) if target.startswith('/') else (path.parent / target_path)
        candidate = candidate.resolve()
        if candidate.is_relative_to(KB.resolve()) and candidate.is_file() and candidate.suffix == '.md':
            anchor = '#' + target.split('#', 1)[1] if '#' in target else ''
            return f'[{label}]({page_name(candidate)}{anchor})'
        return match.group(0)
    body = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', resolve, body)
    output = markdown.markdown(body, extensions=['fenced_code', 'tables', 'toc', 'sane_lists'])
    tags = {'p','br','hr','h1','h2','h3','h4','h5','h6','ul','ol','li','strong','em','a','blockquote','pre','code','table','thead','tbody','tr','th','td','sup'}
    return bleach.clean(output, tags=tags, attributes={'a':['href','title'], '*':['id'], 'code':['class']}, protocols=['https','http','mailto'], strip=True)


def shell(title, content, config, local=False, filename='index.html', description=None, media=None):
    preview = '<div class="preview">Local listening preview · recordings still need review</div>' if local else ''
    description = description or 'One poem, a hundred language journeys. Read, listen and help shape each adaptation.'
    metadata = ''
    if config.get('site_url'):
        canonical = config['site_url'].rstrip('/') + '/' + filename
        cover = config['site_url'].rstrip('/') + '/media/images/cover.png'
        metadata = f'<link rel="canonical" href="{esc(canonical, quote=True)}"><meta property="og:url" content="{esc(canonical, quote=True)}"><meta property="og:image" content="{esc(cover, quote=True)}"><meta name="twitter:card" content="summary_large_image">'
    if not local and media and publicly_available(media) and safe_url(media.get('public_url') or ''):
        kind = media['kind']
        source = media['public_url']
        mime = mimetypes.guess_type(urlparse(source).path)[0]
        metadata += f'<meta property="og:{kind}" content="{esc(source, quote=True)}"><meta property="og:{kind}:secure_url" content="{esc(source, quote=True)}">'
        if mime and mime.startswith(kind + '/'):
            metadata += f'<meta property="og:{kind}:type" content="{esc(mime, quote=True)}">'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description, quote=True)}"><meta property="og:title" content="{esc(title, quote=True)} · World is One"><meta property="og:description" content="{esc(description, quote=True)}"><meta property="og:type" content="website">{metadata}
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'self' https:; img-src 'self'; media-src 'self' https: blob:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<title>{esc(title)} · World is One</title><link rel="stylesheet" href="assets/style.css"><script type="module" src="assets/site.js"></script></head>
<body data-repository="{esc(config.get('repository_url', ''), quote=True)}" data-site-url="{esc(config.get('site_url', ''), quote=True)}">{preview}<header><a class="brand" href="index.html">WORLD IS ONE<span>INDIA IS ONE</span></a><nav aria-label="Main navigation"><a href="index.html#collection">Languages</a><a href="poems--i-am-free-to-dream--original.html">The poem</a><a href="contribute.html">Contribute</a></nav></header>
<main>{content}</main><footer>Original poem © Ahimanikya Satapathy · AI-assisted adaptations and generated recordings are identified on their pages.<br><a href="guides--rights.html">Credits &amp; rights</a> · <a href="contribute.html?type=recording">Submit your version</a> · <a href="kb/index.md">Knowledge base</a></footer></body></html>'''


def share_controls(title, filename, config, local=False, media=None, media_url=None):
    published = not media or publicly_available(media)
    live = bool(config.get('site_url')) and published and not local
    url = config['site_url'].rstrip('/') + '/' + filename if live else ''
    caption = f'{title} — World is One, India is One! Original poem by Ahimanikya Satapathy.'
    if media:
        if not media['publish']: caption += ' Review copy; pronunciation and timing review open.'
        caption += ' ' + ' · '.join(f'{key.replace("_", " ").title()}: {value}' for key,value in media.get('credits', {}).items() if key != 'poem')
    buttons = f'<button type="button" data-action="share-link" {"" if live else "disabled"}>Share</button><button type="button" data-action="copy-link" {"" if live else "disabled"}>Copy link</button><button type="button" data-action="copy-caption">Copy caption &amp; credits</button>'
    instagram = ''
    if live:
        buttons += f'<a class="action" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/sharer/sharer.php?{urlencode({"u":url})}">Facebook ↗</a><a class="action" target="_blank" rel="noopener noreferrer" href="https://wa.me/?{urlencode({"text":caption+" "+url})}">WhatsApp ↗</a>'
        x_text = 'I Am Free to Dream — one poem, many languages. Original poem by Ahimanikya Satapathy.'
        buttons += f'<a class="action" target="_blank" rel="noopener noreferrer" href="https://twitter.com/intent/tweet?{esc(urlencode({"text":x_text,"url":url}), quote=True)}">X ↗</a><a class="action" target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/sharing/share-offsite/?{urlencode({"url":url})}">LinkedIn ↗</a><a class="action" href="#instagram-sharing">Instagram · how to share ↓</a>'
        media_step = 'Save the cover image below for a photo post. To share the song itself, choose a published video version when one is available.'
        if media and media_url and media['kind'] == 'video':
            media_step = 'Use “Download / open video” above to save the video, then upload it in Instagram. If “Share file” is available, you can also try selecting Instagram from your device’s share menu.'
        elif media and media_url:
            media_step = 'Save the cover image below for a photo post. To include the audio in a Reel, first combine it with an image or video in a video editor; an MP3 alone is not a video post.'
        instagram = f'''<section id="instagram-sharing" class="upload-explainer" aria-label="Share on Instagram"><h3>Share on Instagram</h3><p>Prepare your post here, then finish it in Instagram. This does not post automatically.</p><ol><li>{media_step}</li><li>Copy the caption and credits, then paste them into your post.</li><li>Copy this page’s link for a Story link sticker or your profile link, where available.</li></ol><div class="action-row"><a class="action" href="media/images/cover.png" download="free-to-dream-cover.png">Save cover image</a><button type="button" data-action="copy-caption">Copy Instagram caption &amp; credits</button><button type="button" data-action="copy-link">Copy page link</button><a class="action" target="_blank" rel="noopener noreferrer" href="https://www.instagram.com/">Open Instagram ↗</a></div><p class="small">For LinkedIn, use Copy caption &amp; credits above and paste it into the sharing window.</p></section>'''
    if media and media_url:
        buttons += f'<a class="action" href="{esc(media_url, quote=True)}" download>Download / open {media["kind"]}</a>'
        if published and media.get('allow_file_sharing', False):
            buttons += '<button type="button" data-action="prepare-file">Prepare file to share</button><button type="button" data-action="share-file" hidden>Share file…</button><a class="action prepared-download" hidden>Save file</a>'
    note = '' if live else '<p class="share-note">Public sharing becomes available when this page is published.</p>'
    if live:
        note += '<p class="share-note">For video playback in a social feed, download the MP4 and upload it with your post. Sharing a page link does not upload its media. Autoplay and sound depend on the platform and each viewer’s settings.</p>'
    extension = Path(urlparse(media_url or '').path).suffix.lower()
    if extension not in ('.mp3','.mp4','.m4a','.wav','.ogg','.webm'):
        extension = '.mp4' if media and media['kind'] == 'video' else '.mp3'
    mime = mimetypes.guess_type('file'+extension)[0] or 'application/octet-stream'
    file_name = (media['id'] + extension) if media else ''
    return f'<section class="sharing" data-share-url="{esc(url, quote=True)}" data-share-title="{esc(title, quote=True)}" data-caption="{esc(caption, quote=True)}" data-media-url="{esc(media_url or "", quote=True)}" data-media-kind="{media["kind"] if media else ""}" data-file-name="{esc(file_name, quote=True)}" data-mime="{mime}"><div class="action-row">{buttons}</div>{note}{instagram}<p class="share-result" role="status" aria-live="polite"></p></section>'


def collaboration_panel(meta, config):
    slug = meta['slug']
    threads = ''
    if config.get('repository_url'):
        url = config['repository_url'].rstrip('/') + '/issues?' + urlencode({'q':f'is:issue [{slug}] in:title'})
        threads = f'<a class="action" target="_blank" rel="noopener noreferrer" href="{esc(url, quote=True)}">Suggestions &amp; submitted versions ↗</a>'
    return f'''<section class="collaborate" aria-label="Collaborate on this language"><div><div class="eyebrow">MAKE THIS VERSION YOUR OWN</div><h2>Bring your language to life.</h2><p>Suggest a phrase, explain a musical tradition, or contribute your own performance.</p></div><div class="action-row"><a class="button" href="contribute.html?language={quote(slug)}&amp;type=lyrics">Suggest a change</a><a class="button secondary" href="contribute.html?language={quote(slug)}&amp;type=recording">Submit your version</a><a class="action" href="contribute.html?language={quote(slug)}&amp;type=feedback">Review a recording</a>{threads}</div><p class="small">Contributions continue on GitHub. New versions are reviewed before joining the collection.</p></section>'''


def translation_check_panel(meta):
    slug = meta['slug']
    if slug == 'odia':
        context = 'This is the original Odia source. Check transcription and sung delivery; discuss changes to the source wording with the author.'
    elif meta['lyric_status'] == 'Transcription pending':
        context = 'The recording is available; a checked transcription is still needed. Write out the words actually sung, then compare their meaning with the source poem.'
    elif meta['lyric_status'] == 'Adaptation pending':
        context = 'Lyrics are still pending. Use this checklist when preparing the first adaptation; the brief is not a verified translation.'
    else:
        context = 'Use this checklist alongside the review status above. A fluent review of the text and a listening review are separate steps.'
    return f'''<section id="translation-check" class="collaborate" aria-labelledby="translation-check-title">
<div class="eyebrow">QUICK REFERENCE</div><h2 id="translation-check-title">How to validate this translation</h2>
<p>{context}</p>
<p>Keep the <a href="poems--i-am-free-to-dream--original.html">original Odia poem</a> and <a href="poems--i-am-free-to-dream--meaning.html">meaning &amp; poetic intent</a> beside you.</p>
<ol>
<li><strong>Compare the meaning.</strong> Paraphrase each stanza in plain English or Odia and compare it with the source. Preserve freedom to dream and lose the way, the North Star, gathering and embracing the world, the potter, sowing a smile, mountains and moon, clouds and rain, and weaving your dreams into mine. Flag omissions, additions or changed relationships.</li>
<li><strong>Read it aloud.</strong> Ask a fluent speaker of the intended dialect to check grammar, idioms, spelling, script and natural poetic phrasing. A literal word-for-word match is not the goal.</li>
<li><strong>Check cultural fit.</strong> Confirm that imagery, terms of affection and musical suggestions suit the chosen region and tradition. Explain any intentional adaptation without changing the poem’s tenderness or meaning.</li>
<li><strong>Check the sung version, if available.</strong> Listen against the exact lyrics for skipped or added words, pronunciation and unnatural word breaks. Keep a breath between the repeated gathering phrases and a fuller pause after “I am a potter.” Label extra repetitions as song arrangement.</li>
<li><strong>Leave a review others can use.</strong> Quote the line, suggest a replacement, give its literal meaning and explain why. Include your dialect, name to credit, the version reviewed and any unresolved doubts; add timestamps only for audio you actually heard.</li>
</ol>
<p class="small">AI suggestions and back-translation can help find questions; neither proves accuracy. Keep drafts marked for review until a fluent speaker has checked them and the author or a designated maintainer has accepted the changes. Note exactly what was reviewed.</p>
<div class="action-row"><a class="action" href="contribute.html?language={quote(slug)}&amp;type=lyrics">Share a translation review →</a><a href="guides--contributing.html">Full review process</a></div>
</section>'''


def resource_panel(meta, items):
    counts = {kind: sum(item['kind'] == kind for item, _ in items) for kind in ('audio', 'video')}
    content = f'<section id="resources" class="listening" aria-labelledby="resources-title"><div class="eyebrow">LISTEN, WATCH &amp; DOWNLOAD</div><h2 id="resources-title">Available resources</h2><p>{counts["audio"]} audio · {counts["video"]} video · poem / brief · shared cover image</p>'
    def card(item, url):
        suffix = Path(urlparse(url).path).suffix.lower()
        label = {'.mp3':'MP3', '.mp4':'MP4', '.m4a':'M4A', '.wav':'WAV', '.ogg':'OGG', '.webm':'WebM'}.get(suffix, item['kind'].title())
        return f'<div class="recording"><p class="eyebrow">{label} · {esc(recording_label(item))}</p><h4>{esc(item["title"])}</h4>{player_markup(item, url)}<p>{esc(item["notes"])}</p><div class="action-row"><a class="action" href="{esc(url, quote=True)}" download>Download / open {label}</a><a class="action" href="recording--{item["id"]}.html">Share this version &amp; credits →</a></div></div>'
    for kind, heading in [('audio', 'Listen'), ('video', 'Watch')]:
        content += f'<section class="media-group" aria-labelledby="{kind}-heading"><h3 id="{kind}-heading">{heading}</h3>'
        current = [(item, url) for item, url in items if item['kind'] == kind and not item.get('archived')]
        older = [(item, url) for item, url in items if item['kind'] == kind and item.get('archived')]
        content += ''.join(card(item, url) for item, url in current)
        if older:
            content += f'<details class="earlier-recordings"><summary>Earlier {kind} versions ({len(older)})</summary>' + ''.join(card(item, url) for item, url in older) + '</details>'
        if not current and not older:
            content += f'<p>No {kind} recording is available for this language yet.</p><a href="contribute.html?language={quote(meta["slug"])}&amp;type=recording">Contribute a version →</a>'
        content += '</section>'
    content += f'<div class="recording"><h3>Poem &amp; musical direction</h3><div class="action-row"><a class="action" href="#poem-text">Read on this page</a><a class="action" href="kb/poems/i-am-free-to-dream/languages/{quote(meta["slug"])}.md" download>Download text (Markdown)</a></div></div>'
    content += '<div class="recording"><h3>Shared collection cover · PNG</h3><a href="media/images/cover.png"><img src="media/images/cover.png" width="160" loading="lazy" alt="Collection cover: hands shaping a pot beneath a moonlit mountain landscape"></a><p>This artwork is shared across the collection.</p><a class="action" href="media/images/cover.png" download="free-to-dream-cover.png">Save cover image</a></div></section>'
    return content


def contribution_page(languages, config):
    options = ''.join(f'<option value="{esc(x["slug"],quote=True)}">{esc(x["language"])}</option>' for x in languages)
    setup = '' if config.get('repository_url') else '<p class="setup-notice">Preview: the GitHub repository has not been connected yet. You can prepare and save a proposal here; submission will open once it is connected.</p>'
    return f'''<section class="contribution-intro"><a class="back" href="index.html#collection">← Browse languages</a><div class="eyebrow">ONE POEM. YOUR VOICE.</div><h1>Help a language<br>find its song.</h1><p>Share a better phrase, a listening note, or a new performance. You do not need to edit code.</p><ol class="steps"><li><strong>Prepare</strong><span>Choose a language and describe your contribution.</span></li><li><strong>Submit on GitHub</strong><span>Sign in, attach your file or link, and submit.</span></li><li><strong>Review together</strong><span>Discuss changes; accepted versions receive credits and a place in the collection.</span></li></ol></section>
{setup}<form id="contribution-form" class="contribution-form"><div class="form-grid"><label for="contribution-language">Language<select required id="contribution-language" name="language"><option value="">Choose a language</option>{options}</select></label><label for="contribution-type">I would like to<select id="contribution-type" name="type"><option value="lyrics">Suggest a lyric change</option><option value="recording">Submit my song</option><option value="feedback">Review a recording</option><option value="culture">Suggest a musical direction</option></select></label></div>
<label for="contribution-title">A short title<input id="contribution-title" name="title" required maxlength="100" placeholder="A more natural phrase, a new acoustic version…"></label>
<div id="recording-fields" hidden><p class="upload-explainer"><strong>Have an MP3 or M4A recording?</strong> Attach it in the GitHub submission box on the next step. If its format or size is not accepted, paste a public listening link below. Nothing is uploaded from this form.</p><label for="recording-link">Recording link (optional if attaching a file on GitHub)<input type="url" id="recording-link" name="recording_link" placeholder="https://…"></label><label for="recording-credits">Music, voice and production credits<textarea id="recording-credits" name="credits" rows="3" maxlength="2500" placeholder="Who sang, translated or arranged it? Name any AI tools used."></textarea></label></div>
<div id="lyric-fields"><label for="current-phrase">Current wording or passage<textarea id="current-phrase" name="current" rows="3" maxlength="4000" dir="auto"></textarea></label><label for="proposed-phrase">Suggested wording<textarea id="proposed-phrase" name="proposed" rows="3" maxlength="4000" dir="auto"></textarea></label></div>
<label for="contribution-details">Your notes and reason<textarea id="contribution-details" name="details" required rows="5" maxlength="6000" placeholder="Explain the meaning or tradition. For listening feedback, include the version and timestamps you checked."></textarea></label><div class="form-grid"><label for="contribution-dialect">Dialect or region (optional)<input id="contribution-dialect" name="dialect" maxlength="150"></label><label for="contribution-credit">Name to credit (optional)<input id="contribution-credit" name="credit" maxlength="150"></label></div>
<p class="small">Your proposal will be visible on GitHub after you submit it. Keep personal contact details out of it. For recordings, identify the creators and permission to share.</p><button class="button" type="submit">Prepare GitHub submission →</button><p id="contribution-status" role="status" aria-live="polite"></p>
<section id="proposal-preview" hidden><h2>Your proposal</h2><p>Review the text below. Continue on GitHub to attach your recording and submit.</p><label for="proposal-text">Submission text<textarea id="proposal-text" rows="14" readonly></textarea></label><div class="action-row"><button type="button" id="copy-proposal">Copy proposal</button><button type="button" id="save-proposal">Save proposal</button><a id="github-submit" class="button" target="_blank" rel="noopener noreferrer" hidden>Continue on GitHub ↗</a></div><p id="proposal-handoff" class="small"></p></section></form><noscript><p>JavaScript is needed to prepare a proposal. You can also follow the <a href="guides--contributing.html">contribution guide</a>.</p></noscript>'''


def build(local=False):
    languages = validate()
    config = json.loads((ROOT / 'site-config.json').read_text())
    output = ROOT / ('site' if local else 'site-public')
    if output.exists(): shutil.rmtree(output)
    output.mkdir()
    shutil.copytree(ROOT / 'web', output / 'assets')
    # Only explicitly authorized previews/releases are embedded remotely.
    # Never ship archive binaries or unhydrated pointers in the Pages build.
    shutil.copytree(ROOT / 'media', output / 'media', ignore=shutil.ignore_patterns(*(f'*{ext}' for ext in MEDIA_EXTENSIONS), '*.srt', '*.vtt'))
    shutil.copytree(KB, output / 'kb')
    (output / 'contribute.html').write_text(shell('Contribute your voice', contribution_page(languages, config), config, local, 'contribute.html'), encoding='utf-8')
    available = {}
    for item in records():
        if item.get('archived', False) and not publicly_available(item): continue
        url = item.get('public_url') if publicly_available(item) else None
        if local and (item.get('repo_path') or item.get('local_path')):
            candidates = [confined(item[key]) for key in ('repo_path', 'local_path') if item.get(key)]
            source = next((path for path in candidates if media_is_available(path)), None)
            if source is not None:
                relative = f'media/recordings/{item["id"]}{source.suffix.lower()}'
                target = output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                try: os.link(source, target)
                except OSError: shutil.copy2(source, target)
                url = relative
        if url:
            available.setdefault(item['language'], []).append((item, url))
            cues = timed_cues(item)
            if cues is not None:
                base = output / f'media/lyrics/{item["id"]}'
                base.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(confined(item['timed_lyrics']['srt_path']), base.with_suffix('.srt'))
                base.with_suffix('.vtt').write_text(make_vtt(cues), encoding='utf-8')
                base.with_suffix('.json').write_text(json.dumps(cues, ensure_ascii=False), encoding='utf-8')
    language_map = {x['slug']:x for x in languages}
    for slug, items in available.items():
        for item, url in items:
            filename = f'recording--{item["id"]}.html'
            tag = item['kind']
            poster = ' playsinline poster="media/images/cover.png"' if tag == 'video' else ''
            credits = ''.join(f'<dt>{esc(key.replace("_", " ").title())}</dt><dd>{esc(value)}</dd>' for key,value in item.get('credits',{}).items())
            content = f'<a class="back" href="{page_name(LANGUAGES/(slug+".md"))}">← All {esc(language_map[slug]["language"])} versions and lyrics</a><section class="recording-detail"><div class="eyebrow">{esc(language_map[slug]["language"])} · {esc(recording_label(item))}</div><h1>{esc(item["title"])}</h1>{player_markup(item, url)}<p>{esc(item["notes"])}</p><dl class="credits">{credits}</dl>'
            content += share_controls(item['title'], filename, config, local, item, url)
            content += f'<p><a href="contribute.html?language={quote(slug)}&amp;type=feedback&amp;recording={quote(item["id"])}">Leave a listening note for this version</a></p></section>'
            content += collaboration_panel(language_map[slug], config)
            (output/filename).write_text(shell(item['title'], content, config, local, filename, f'{language_map[slug]["language"]} {tag} version of I Am Free to Dream. Listen, share and explore the lyrics.', media=item), encoding='utf-8')
    for path in sorted(KB.rglob('*.md')):
        meta, body = read_concept(path)
        title = meta.get('title', path.parent.name if path.name == 'index.md' else path.stem)
        extras = ''
        if path.parent == LANGUAGES and path.name != 'index.md':
            slug = meta['slug']
            extras = f'<div class="eyebrow">{esc(meta["language"])} / I AM FREE TO DREAM</div><p class="status">{esc(meta["lyric_status"])} · {esc(meta["review_status"].replace("-", " "))}</p>'
            extras += '<div class="page-actions"><a class="button" href="contribute.html?language='+quote(slug)+'&amp;type=lyrics">Suggest a change</a><a class="button secondary" href="contribute.html?language='+quote(slug)+'&amp;type=recording">Submit your version</a><a href="#poem-text">Read the lyrics ↓</a><a href="#translation-check">Translation check ↓</a></div>'
            extras += '<p><a class="action" href="#resources">Available resources ↓</a></p>'
            extras += resource_panel(meta, available.get(slug, []))
            if slug == 'odia':
                extras += f'<p><a href="{esc(config["preferred_odia_suno_url"], quote=True)}">Listen to the author’s selected Odia take on Suno ↗</a></p>'
            if config.get('repository_url'):
                extras += f'<p><a href="{esc(config["repository_url"].rstrip("/") + "/issues", quote=True)}">Suggest a change or share a review ↗</a></p>'
        rendered = render_markdown(body, path)
        if meta.get('slug') in ('arabic','urdu','sindhi'):
            rendered = rendered.replace('<pre>', '<pre dir="rtl">', 1)
        content = '<a class="back" href="index.html#collection">← Browse languages</a>' + extras + f'<article id="poem-text">{rendered}</article>'
        if path.parent == LANGUAGES and path.name != 'index.md':
            content += translation_check_panel(meta)
            content += share_controls(meta['language']+' · '+meta['title'], page_name(path), config, local)
            content += collaboration_panel(meta, config)
        (output / page_name(path)).write_text(shell(title, content, config, local, page_name(path)), encoding='utf-8')
    lyric_count = sum(has_lyrics(x) for x in languages)
    cards = []
    for item in languages:
        slug = item['slug']
        listening = slug in available
        status = 'lyrics' if has_lyrics(item) else 'brief'
        label = 'Listen & explore' if listening else ('Read the lyrics' if status == 'lyrics' else 'Help shape this version')
        cards.append(f'''<a class="language-card" data-search="{esc(item['language']+' '+item['title'], quote=True)}" data-status="{status}" data-listen="{str(listening).lower()}" href="{page_name(LANGUAGES / (slug+'.md'))}"><span class="card-top">{item['collection_order']:03d}<span>{'♫ LISTEN' if listening else ('LYRICS' if status == 'lyrics' else 'OPEN INVITATION')}</span></span><h3>{esc(item['language'])}</h3><p dir="auto">{esc(item['title'])}</p><span class="card-action">{label} <span aria-hidden="true">↗</span></span></a>''')
    content = f'''<section class="hero"><div><div class="eyebrow">A POEM WITHOUT BORDERS</div><h1>I am free<br>to <em>dream.</em></h1><p class="original-title" lang="or">ମୋତେ ସପ୍ନ ଦେଖିବାକୁ ମନା ନାହିଁ</p><p class="intro">One poem. Many voices. Shared dreams.<br>An invitation to carry an Odia poem into the languages and musical traditions we call home.</p><a class="button" href="#collection">Explore the collection ↓</a><p class="byline">A poem by Ahimanikya Satapathy</p></div><figure><img src="media/images/cover.png" alt="Hands shaping a clay pot beneath a dreamlike moonlit mountain landscape"><figcaption>Gathering the world. Giving dreams a form.</figcaption></figure></section>
<section class="stats" aria-label="Collection status"><div><strong>{len(languages)}</strong><span>language journeys</span></div><div><strong>{lyric_count}</strong><span>original &amp; adapted texts</span></div><div><strong>{len(languages)-lyric_count}</strong><span>texts awaiting contributions</span></div><div><strong>{len(available)}</strong><span>languages with {'local media' if local else 'playable media'}</span></div></section>
<section id="collection"><div class="section-heading"><div class="eyebrow">THE LIVING COLLECTION</div><h2>Find your language.<br>Bring your voice.</h2><p>Read the poem, explore its musical direction, or help an adaptation find its natural voice. Drafts remain marked until reviewed.</p></div><div class="filters"><label for="search">Search languages or titles<input id="search" type="search" placeholder="Try Odia, Tamil, Sanskrit…"></label><label for="filter">Show<select id="filter"><option value="all">All languages</option><option value="listen">Ready to listen</option><option value="lyrics">Lyrics available</option><option value="brief">Adaptation briefs</option></select></label></div><p id="result-count" role="status" aria-live="polite">{len(languages)} languages</p><div class="language-grid">{''.join(cards)}</div><p id="no-results" hidden>No matching language. Try another name or clear the filter.</p></section>
<section class="invitation"><div class="eyebrow">THIS IS AN INVITATION</div><h2>A language is a living culture.</h2><p>Suggest a lyric change, share a listening note, or submit your own song. Collaborate through GitHub; accepted versions join the collection with credits and a shareable page.</p><div class="action-row"><a class="button" href="contribute.html">Suggest a change →</a><a class="button secondary" href="contribute.html?type=recording">Submit your version →</a></div></section>'''
    (output / 'index.html').write_text(shell('I Am Free to Dream', content, config, local), encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Built {output.name}: {len(languages)} languages; {sum(map(len, available.values()))} playable media items')


def add_media(args):
    validate()
    if args.kind != 'audio': raise ValueError('New recordings use MP3 or M4A audio; existing videos remain archived')
    if not (LANGUAGES / f'{args.language}.md').is_file(): raise ValueError('Unknown language slug')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.id): raise ValueError('Use lowercase letters, numbers and hyphens for ID')
    items = records()
    if any(x['id'] == args.id for x in items): raise ValueError('Recording ID already exists; use a new version ID')
    entry = {'id':args.id, 'language':args.language, 'poem':'i-am-free-to-dream', 'kind':args.kind,
             'title':args.title, 'local_path':None, 'repo_path':None, 'public_url':None, 'publish':False,
             'allow_file_sharing':False,
             'review_status':'needs-review', 'notes':'New upload; review pronunciation, completeness, timing and credits.',
             'credits':{'poem':'Ahimanikya Satapathy','music_and_vocals':'To be supplied'}, 'rights_status':'release-details-to-confirm'}
    if args.url:
        if not safe_url(args.url) or Path(urlparse(args.url).path).suffix.lower() not in ('.mp3', '.m4a'): raise ValueError('Use a direct HTTPS MP3 or M4A URL')
        entry['public_url'] = args.url
    else:
        source = Path(args.file).expanduser().resolve()
        allowed = ('.mp3', '.m4a')
        if source.suffix.lower() not in allowed: raise ValueError(f'Expected one of {allowed}')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        relative = f'media/{args.language}/{args.id}{source.suffix.lower()}'
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('Target already exists with different content; use a new version ID')
        if source != target: shutil.copy2(source, target)
        entry['repo_path'] = relative
        inventory = json.loads((ROOT / 'catalog/asset-inventory.json').read_text())
        if not any(x.get('repo_path') == relative for x in inventory):
            inventory.append({'sha256':digest,'repo_path':relative,'bytes':source.stat().st_size,'source_names':[source.name],'role':'working-asset','published':False})
            (ROOT / 'catalog/asset-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    items.append(entry)
    (ROOT / 'catalog/recordings.json').write_text(json.dumps(items, ensure_ascii=False, indent=2)+'\n')
    print(f'Added {args.id} as a review draft. Files under media/ are tracked with Git LFS when committed. Rebuild the local preview to listen.')


def export_wiki():
    config = json.loads((ROOT / 'site-config.json').read_text())
    if not safe_url(config['site_url']): raise ValueError('Set the HTTPS site_url in site-config.json first')
    validate()
    dest = ROOT / 'wiki-export'
    dest.mkdir(exist_ok=True)
    pages = list(KB.rglob('*.md'))
    home = ['# World is One, India is One!\n\nOne poem. Many voices. Shared dreams.\n']
    for path in pages:
        meta, body = read_concept(path)
        filename = page_name(path).removesuffix('.html')
        link = config['site_url'].rstrip('/') + '/' + page_name(path)
        # The hosted site is the listening surface; wiki pages preserve the text.
        body = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', lambda m: rewrite_wiki_link(m, path), body)
        (dest / f'{filename}.md').write_text(f'[Listen / view this page]({link})\n\n'+body, encoding='utf-8')
        if path.parent == LANGUAGES and meta.get('language'):
            home.append(f'- [{meta["language"]}]({filename}) — {meta["lyric_status"]}\n')
    (dest / 'Home.md').write_text(''.join(home), encoding='utf-8')
    print('Created wiki-export/. Copy these pages into your repository’s separate wiki checkout; do not edit generated copies.')


def rewrite_wiki_link(match, path):
    label, target = match.groups()
    if '://' in target or target.startswith('#'): return match.group(0)
    candidate = (KB / target.lstrip('/')) if target.startswith('/') else path.parent / target
    candidate = candidate.resolve()
    if candidate.is_relative_to(KB.resolve()) and candidate.is_file():
        return f'[{label}]({page_name(candidate).removesuffix(".html")})'
    return match.group(0)


class MediaHandler(SimpleHTTPRequestHandler):
    """Support byte ranges so long audio/video can be scrubbed locally."""
    def send_head(self):
        self.byte_range = None
        path = Path(self.translate_path(self.path))
        header = self.headers.get('Range')
        if not header or not path.is_file(): return super().send_head()
        size = path.stat().st_size
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', header)
        if not match or not any(match.groups()):
            self.send_error(416); return None
        first, last = match.groups()
        start = int(first) if first else max(0, size-int(last))
        end = min(int(last), size-1) if first and last else size-1
        if start > end or start >= size:
            self.send_response(416); self.send_header('Content-Range', f'bytes */{size}'); self.end_headers(); return None
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end-start+1))
        self.end_headers()
        stream = path.open('rb'); stream.seek(start)
        self.byte_range = end-start+1
        return stream

    def copyfile(self, source, outputfile):
        if self.byte_range is None: return super().copyfile(source, outputfile)
        remaining = self.byte_range
        while remaining:
            block = source.read(min(65536, remaining))
            if not block: break
            outputfile.write(block); remaining -= len(block)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate')
    build_parser = commands.add_parser('build'); build_parser.add_argument('--local-media', action='store_true')
    serve_parser = commands.add_parser('serve'); serve_parser.add_argument('--port', type=int, default=8765)
    commands.add_parser('export-wiki')
    media = commands.add_parser('add-media')
    for key in ('language','id','title'): media.add_argument('--'+key, required=True)
    media.add_argument('--kind', choices=['audio'], default='audio')
    source = media.add_mutually_exclusive_group(required=True); source.add_argument('--file'); source.add_argument('--url')
    lyrics = commands.add_parser('add-lyrics')
    lyrics.add_argument('--id', required=True); lyrics.add_argument('--file', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'validate': print(f'Validated {len(validate())} language concepts and {len(records())} recording records.')
        elif args.command == 'build': build(args.local_media)
        elif args.command == 'add-media': add_media(args)
        elif args.command == 'add-lyrics': add_lyrics(args)
        elif args.command == 'export-wiki': export_wiki()
        elif args.command == 'serve':
            if not (ROOT/'site/index.html').is_file(): raise ValueError('Run build --local-media first')
            print(f'Listening wiki: http://127.0.0.1:{args.port}', flush=True)
            ThreadingHTTPServer(('127.0.0.1', args.port), partial(MediaHandler, directory=str(ROOT/'site'))).serve_forever()
    except (ValueError, OSError, yaml.YAMLError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__': main()
