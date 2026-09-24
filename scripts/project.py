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
    text = 'Play to follow the lyrics.' if timing else ''
    downloads = f'<div class="action-row"><a href="{base}.srt" download>Download SRT</a><a href="{base}.vtt" download>Download WebVTT</a></div>' if timing else ''
    lyric = f'<p class="current-lyric" dir="auto">{text}</p>' if timing else ''
    return f'<div class="audio-lyrics"{data}>{player}{lyric}{downloads}</div>'


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
<title>{esc(title)} · World is One</title><link rel="stylesheet" href="assets/style.css?v={config.get("_asset_version","1")}"><script type="module" src="assets/site.js?v={config.get("_asset_version","1")}"></script></head>
<body data-repository="{esc(config.get('repository_url', ''), quote=True)}" data-site-url="{esc(config.get('site_url', ''), quote=True)}">{preview}<header><a class="brand" href="index.html"><img src="assets/odia-lotus.svg" alt="" width="38" height="38" aria-hidden="true">WORLD IS ONE<span>A POEM WITHOUT BORDERS</span></a><nav aria-label="Main navigation"><a href="languages.html">Languages</a><a href="poems--i-am-free-to-dream--original.html">The poem</a><a href="contribute.html">Contribute</a></nav></header>
<main>{content}</main>{(ROOT/"web/index-player.html").read_text() if config.get("_has_audio") else ""}<footer>Original poem © Ahimanikya Satapathy · AI-assisted adaptations and generated recordings are identified on their pages.<br><a href="guides--rights.html">Credits &amp; rights</a> · <a href="guides--artwork.html">Art of the site</a> · <a href="contribute.html?type=recording">Submit your version</a> · <a href="kb/index.md">Knowledge base</a></footer></body></html>'''


def share_controls(title, filename, config, local=False, media=None, media_url=None):
    published = not media or publicly_available(media)
    live = bool(config.get('site_url')) and published and not local
    url = config['site_url'].rstrip('/') + '/' + filename if live else ''
    caption = f'{title} — World is One — A Poem Without Borders. Original poem by Ahimanikya Satapathy.'
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
    if slug == 'odia': return ''
    if meta['lyric_status'] == 'Transcription pending':
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


def playlist_picker():
    return '<label class="playlist-picker">Playlist<select data-playlist aria-label="Choose a track from the playlist"><option value="">Choose a track…</option></select></label>'


def resource_panel(meta, items):
    content = '<aside id="resources" class="listening compact-listening" aria-label="Listen and watch">'
    if any(not item['publish'] for item, _ in items):
        content += '<p class="media-status">Working recordings · feedback welcome</p>'
    def card(item, url):
        label = Path(urlparse(url).path).suffix.lstrip('.').upper()
        title = re.sub(r'^(?:I Am Free to Dream|'+re.escape(meta['language'])+r')\s*[·–—-]\s*', '', item['title'])
        return f'<div class="recording"><h4>{esc(title)}</h4>{player_markup(item, url)}<div class="recording-links"><a href="{esc(url, quote=True)}" download>Download {label}</a><a href="recording--{item["id"]}.html">Details &amp; share ↗</a></div></div>'
    for kind, heading, target in [('audio', 'Listen', 'listen'), ('video', 'Watch', 'watch')]:
        current = [(item, url) for item, url in items if item['kind'] == kind and not item.get('archived')]
        older = [(item, url) for item, url in items if item['kind'] == kind and item.get('archived')]
        content += f'<section id="{target}" class="media-group" aria-label="{heading}"><h2>{heading}</h2>'
        if not current and not older:
            content += '<p class="media-empty">'+('A recording is still to come.' if kind=='audio' else 'A video is still to come.')+'</p>'
        if current:
            content += card(*current[0])
            if len(current) > 1:
                content += f'<details class="more-recordings"><summary>More {kind} versions ({len(current)-1})</summary>' + ''.join(card(*pair) for pair in current[1:]) + '</details>'
        if older:
            content += f'<details class="earlier-recordings"><summary>Earlier {kind} versions ({len(older)})</summary>' + ''.join(card(*pair) for pair in older) + '</details>'
        if kind == 'audio' and current:
            content += playlist_picker()
        content += '</section>'
    if not items:
        content += f'<a class="text-link" href="contribute.html?language={quote(meta["slug"])}&amp;type=recording">Share a recording →</a>'
    return content + '</aside>'


def language_content(meta, body, path, items, config, local=False):
    """A reading surface with the full source notes available on demand."""
    slug = meta['slug']
    original = slug == 'odia'
    parts = re.split(r'(?m)^## (.+)\n', body)
    sections = [(parts[i], parts[i+1].split('\n---\n')[0].strip()) for i in range(1, len(parts), 2)]
    by_heading = dict(sections)
    language_name = 'Odia · the original' if original else meta['language']
    status = 'Original poem' if original else ('Adaptation · review welcome' if has_lyrics(meta) else meta['lyric_status'])
    source_link = '' if original else '<a href="poems--i-am-free-to-dream--languages--odia.html">Read the Odia original ↗</a>'
    header = f'<section class="language-heading"><div class="eyebrow">{esc(language_name)}</div><h1 dir="auto">{esc(meta["title"])}</h1><p class="poet-credit">A poem by Ahimanikya Satapathy <span aria-hidden="true">·</span> {esc(status)}</p><div class="reading-links"><a href="#poem-text">Read</a><a href="#listen">Listen</a><a href="#watch">Watch</a>{source_link}</div><details class="page-share"><summary>Share this poem</summary>{share_controls(meta["language"]+" · "+meta["title"], page_name(path), config, local)}</details></section>'
    if original:
        _, source_body = read_concept(KB/'poems/i-am-free-to-dream/original.md')
        poem = re.search(r'```(?:text)?\n(.*?)\n```', source_body, re.S)
        primary = '```text\n'+poem[1]+'\n```' if poem else source_body
    elif has_lyrics(meta) and 'Poem / arranged lyrics' in by_heading:
        primary = re.sub(r'(?m)^[ \t]*\[[^\]\n]+\][ \t]*\n?', '', by_heading['Poem / arranged lyrics'])
    elif meta['lyric_status'] == 'Transcription pending':
        primary = 'Listen to this version while we prepare a checked transcription of the words sung. A fluent speaker can help bring the text to this page.'
    else:
        primary = 'This language’s poem is still taking shape. Read the [Odia original](odia.md) and help carry its feeling into your language. The adaptation brief is available below.'
    primary_html = render_markdown(primary, path)
    if slug in ('arabic','urdu','sindhi','kashmiri','balti'):
        primary_html = primary_html.replace('<pre>', '<pre dir="rtl">')
    reading = f'<article id="poem-text" class="poem-reading"><h2 class="reading-caption">Read</h2>{primary_html}<a class="poem-download" href="kb/poems/i-am-free-to-dream/languages/{quote(slug)}.md" download>Download poem &amp; notes ↓</a></article>'
    content = header + '<div class="language-layout">'+reading+resource_panel(meta, items)+'</div>'
    content += '<section class="language-notes" aria-label="About this version">'
    prompt = re.search(r'```(?:text)?\n(.*?)\n```', by_heading.get('Poem / arranged lyrics', ''), re.S)
    if prompt:
        direction = 'rtl' if slug in ('arabic','urdu','sindhi','kashmiri','balti') else 'auto'
        content += f'<details class="lyrics-prompt"><summary>Lyrics prompt · view &amp; copy</summary><div class="detail-body"><label for="lyrics-prompt-text">Lyrics with song sections</label><textarea id="lyrics-prompt-text" rows="16" readonly dir="{direction}">{esc(prompt[1])}</textarea><button type="button" id="copy-lyrics-prompt">Copy lyrics prompt</button><p id="lyrics-copy-status" class="small" role="status" aria-live="polite"></p></div></details>'
    music_names = {'Why this musical direction','Cultural grounding','Voice, rhythm and arrangement','Emotional shape','Style prompt','Working settings and listening checks','Musical direction'}
    music = '\n\n'.join('## '+heading+'\n\n'+text for heading,text in sections if heading in music_names)
    if music:
        content += '<details><summary>Musical direction &amp; style prompt</summary><div class="detail-body">'+render_markdown(music,path)+'</div></details>'
    if not original:
        extra = '\n\n'.join('## '+heading+'\n\n'+text for heading,text in sections if heading not in music_names and heading != 'Poem / arranged lyrics')
        content += '<details id="translation-check"><summary>Translation &amp; collaboration</summary><div class="detail-body">'+translation_check_panel(meta).replace('id="translation-check"','id="translation-reference"')+render_markdown(extra,path)+'</div></details>'
    contributor = 'Share a performance or a listening note' if original else 'Help this version grow'
    notes_link = f'contribute.html?language={quote(slug)}&amp;type=feedback'
    action = f'<a href="contribute.html?language={quote(slug)}&amp;type=recording">Submit a recording</a><a href="{notes_link}">Leave a listening note</a>'
    if not original: action += f'<a href="contribute.html?language={quote(slug)}&amp;type=lyrics">Suggest a wording change</a>'
    timing_record = next((record for record, _ in items if record['kind']=='audio' and not record.get('archived')), None)
    if timing_record: action += f'<a href="timing.html?recording={quote(timing_record["id"])}">Time the lyrics</a>'
    if original and config.get('preferred_odia_suno_url'):
        action += f'<a href="{esc(config["preferred_odia_suno_url"],quote=True)}">Selected take on Suno ↗</a>'
    content += f'<div class="quiet-contribute"><h2>{contributor}</h2><div class="reading-links">{action}</div></div></section>'
    return f'<a class="back" href="languages.html">← All languages</a><div class="language-page" data-language="{esc(slug,quote=True)}">'+content+'</div>'


def contribution_page(languages, config):
    options = ''.join(f'<option value="{esc(x["slug"],quote=True)}">{esc(x["language"])}</option>' for x in languages)
    setup = '' if config.get('repository_url') else '<p class="setup-notice">Preview: the GitHub repository has not been connected yet. You can prepare and save a proposal here; submission will open once it is connected.</p>'
    return f'''<section class="contribution-intro"><a class="back" href="languages.html">← Browse languages</a><div class="eyebrow">ONE POEM. YOUR VOICE.</div><h1>Help a language<br>find its song.</h1><p>Share a better phrase, a listening note, or a new performance. You do not need to edit code.</p><ol class="steps"><li><strong>Prepare</strong><span>Choose a language and describe your contribution.</span></li><li><strong>Submit on GitHub</strong><span>Sign in, attach your file or link, and submit.</span></li><li><strong>Review together</strong><span>Discuss changes; accepted versions receive credits and a place in the collection.</span></li></ol></section>
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
    config['_has_audio'] = any(item['kind']=='audio' and (publicly_available(item) or (local and item.get('repo_path'))) for item in records())
    output = ROOT / ('site' if local else 'site-public')
    if output.exists(): shutil.rmtree(output)
    output.mkdir()
    shutil.copytree(ROOT / 'web', output / 'assets', ignore=shutil.ignore_patterns('*.html'))
    asset_version = hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'web').iterdir()) if p.is_file())).hexdigest()[:12]
    config['_asset_version'] = asset_version
    for asset in (output/'assets').iterdir():
        if asset.suffix in ('.js','.mjs'):
            asset.write_text(re.sub(r"(['\"])(\./[a-z-]+\.mjs)\1", lambda match: match[1]+match[2]+'?v='+asset_version+match[1], asset.read_text()))

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
            if tag == 'audio':
                if not item.get('archived'): content += playlist_picker()
                content += f'<p><a href="timing.html?recording={quote(item["id"])}">Add or adjust timed lyrics →</a></p>'
            content += share_controls(item['title'], filename, config, local, item, url)
            content += f'<p><a href="contribute.html?language={quote(slug)}&amp;type=feedback&amp;recording={quote(item["id"])}">Leave a listening note for this version</a></p></section>'
            content += collaboration_panel(language_map[slug], config)
            (output/filename).write_text(shell(item['title'], content, config, local, filename, f'{language_map[slug]["language"]} {tag} version of I Am Free to Dream. Listen, share and explore the lyrics.', media=item), encoding='utf-8')
    for path in sorted(KB.rglob('*.md')):
        meta, body = read_concept(path)
        title = meta.get('title', path.parent.name if path.name == 'index.md' else path.stem)
        if path.parent == LANGUAGES and path.name != 'index.md':
            content = language_content(meta, body, path, available.get(meta['slug'], []), config, local)
        elif path == KB/'poems/i-am-free-to-dream/original.md':
            odia_meta, odia_body = read_concept(LANGUAGES/'odia.md')
            content = language_content(odia_meta, odia_body, LANGUAGES/'odia.md', available.get('odia', []), config, local).replace('<a class="back" href="languages.html">← All languages</a>', '<a class="back" href="index.html">← Home</a>')
        else:
            content = '<a class="back" href="index.html">← Home</a><article>'+render_markdown(body,path)+'</article>'
        (output / page_name(path)).write_text(shell(title, content, config, local, page_name(path)), encoding='utf-8')
    lyric_count = sum(has_lyrics(x) for x in languages)
    cards = {}
    for item in languages:
        slug = item['slug']
        listening = slug in available
        status = 'lyrics' if has_lyrics(item) else 'brief'
        page = page_name(LANGUAGES/(slug+'.md'))
        current = [(record, url) for record, url in available.get(slug, []) if not record.get('archived')]
        audio = [(record, url) for record, url in current if record['kind']=='audio']
        video_count = sum(record['kind']=='video' for record, _ in current)
        _, body = read_concept(LANGUAGES/(slug+'.md'))
        direction = re.search(r'\*\*Musical direction:\*\* ([^\n]+)',body)
        direction = direction[1].split(' · ')[0].strip() if direction else 'Musical direction awaiting listening review'
        readiness = 'Odia original' if slug=='odia' else ('Lyrics · review welcome' if status=='lyrics' else ('Transcription pending' if item['lyric_status']=='Transcription pending' else 'Adaptation invited'))
        availability = f'{len(audio)} audio · {video_count} video' if current else 'Recording to come'
        play = ''
        if audio:
            record, url = audio[0]
            seconds = int(record.get('duration_seconds',0))
            duration = f'{seconds//60}:{seconds%60:02}' if seconds else ''
            play = f'<button class="card-play" type="button" data-play-recording="{record["id"]}" aria-label="Play {esc(item["language"],quote=True)}" aria-pressed="false"><span class="play-label">▶ Play</span> <span>{duration}</span></button>'
        cards[slug] = f'''<article class="language-card" data-search="{esc(item['language']+' '+item['title']+' '+direction, quote=True)}" data-status="{status}" data-listen="{str(listening).lower()}"><div class="card-top"><span>{item['collection_order']:03d}</span><span>{esc(readiness)}</span></div><h3><a href="{page}">{esc(item['language'])}</a></h3><p class="card-poem" dir="auto">{esc(item['title'])}</p><p class="card-direction">{esc(direction)}</p><p class="card-availability">{availability}</p><div class="card-bottom">{play}<a href="{page}">Read &amp; explore ↗</a></div></article>'''
    audio_catalog = []
    for slug, entries in available.items():
        _, body = read_concept(LANGUAGES/(slug+'.md'))
        section = re.search(r'## Poem / arranged lyrics\n(.*?)(?=\n## |\Z)',body,re.S)
        draft = re.search(r'```(?:text)?\n(.*?)\n```',section[1],re.S) if section else None
        for record, url in entries:
            if record['kind']!='audio': continue
            audio_catalog.append({'id':record['id'],'language':slug,'language_name':language_map[slug]['language'],'title':record['title'],'url':url,'page':f'recording--{record["id"]}.html','duration_seconds':record.get('duration_seconds'),'draft':draft[1] if draft else '', 'archived':record.get('archived',False), 'srt_url':f'media/lyrics/{record["id"]}.srt' if record.get('timed_lyrics') else None})
    (output/'assets/listening.json').write_text(json.dumps(audio_catalog,ensure_ascii=False),encoding='utf-8')
    (output/'timing.html').write_text(shell('Time the lyrics', (ROOT/'web/timing.html').read_text(), config, local, 'timing.html'),encoding='utf-8')
    directory = f'''<section id="collection" class="language-directory"><div class="section-heading"><a class="back" href="index.html">← Home</a><div class="eyebrow">THE LIVING COLLECTION</div><h1>Find your language.</h1><p>Explore all {len(languages)} language journeys. Listen, read, or help an adaptation find its natural voice.</p></div><div class="filters"><label for="search">Search languages or titles<input id="search" type="search" placeholder="Try Odia, Tamil, Sanskrit…"></label><label for="filter">Show<select id="filter"><option value="all">All languages</option><option value="listen">Ready to listen</option><option value="lyrics">Lyrics available</option><option value="brief">Adaptation briefs</option></select></label></div><p id="result-count" role="status" aria-live="polite">{len(languages)} languages</p><div class="language-grid">{''.join(cards.values())}</div><p id="no-results" hidden>No matching language. Try another name or clear the filter.</p></section>'''
    (output/'languages.html').write_text(shell('Explore the languages', directory, config, local, 'languages.html'), encoding='utf-8')
    featured_slugs = ['odia', 'english', 'tamil', 'telugu', 'filipino', 'sambalpuri']
    journey_order = [slug for slug in featured_slugs if slug in cards] + [slug for slug in cards if slug not in featured_slugs]
    featured = ''.join(cards[slug] for slug in journey_order)
    author_links = ''.join(f'<a href="{esc(link["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{esc(link["label"])} ↗</a>' for link in config.get('author_links',[]) if safe_url(link.get('url','')))
    content = f'''<section class="hero"><div><div class="eyebrow">FROM A COLLEGE NOTEBOOK, INTO THE WORLD</div><h1>I am free<br>to <em>dream.</em></h1><p class="original-title" lang="or">ମୋତେ ସପ୍ନ ଦେଖିବାକୁ ମନା ନାହିଁ</p><p class="intro">Creativity has always been part of my life—in the organisations I shape, the software I build, the poems I write, and the spaces I create. This Odia poem from my college years is now finding its melody, and new voices across languages.</p><div class="action-row"><a class="button" href="#collection">Find a voice ↓</a><a class="text-link" href="#story">The story behind the song →</a></div><p class="byline">A poem by Ahimanikya Satapathy</p></div><figure class="dream-artwork"><img src="media/images/cover.png" width="1254" height="1254" alt="A potter shaping a clay vessel that opens into a moonlit mountain landscape"><figcaption>Shaping a little world. Leaving room for a dream.</figcaption></figure></section>
<section class="stats" aria-label="Collection status"><div><strong>{len(languages)}</strong><span>language journeys</span></div><div><strong>{lyric_count}</strong><span>original &amp; adapted texts</span></div><div><strong>{len(languages)-lyric_count}</strong><span>texts awaiting contributions</span></div><div><strong>{len(available)}</strong><span>languages with {'local media' if local else 'playable media'}</span></div></section>
<section id="collection" class="featured-collection"><div class="featured-heading"><div><div class="eyebrow">FOLLOW THE THREAD</div><h2>Hear the dream travel.</h2><p class="collection-intro">Listen where a song has begun. Help another language find its voice.</p></div><div class="collection-actions"><a class="text-link" href="languages.html">All {len(languages)} languages →</a><div class="card-scroll-controls" hidden><button type="button" id="cards-previous" aria-label="Previous set of languages" aria-controls="featured-cards">←</button><button type="button" id="cards-next" aria-label="Next set of languages" aria-controls="featured-cards">→</button></div></div></div><div id="featured-cards" class="language-grid featured-grid" role="region" aria-label="Language journeys, scroll horizontally" aria-roledescription="carousel" tabindex="0">{featured}</div><p id="carousel-status" class="visually-hidden" role="status" aria-live="polite"></p></section>
<section class="origin-story" id="story" aria-labelledby="story-title"><div class="story-copy"><div class="eyebrow"><span class="north-star" aria-hidden="true">✧</span> WHERE THE DREAM BEGAN</div><h2 id="story-title">The canvas changes.<br>The dream stays.</h2><p>I’ve always nurtured creativity in whatever I do. Shaping an organisation, building software, writing a poem or creating a space all come from the same impulse: to give an idea a form that people can experience.</p><p>A space can speak its own language. I’ve tried to make my office a place that makes people happy. Poetry reaches people in another way, carrying feelings that can bring us closer.</p><p>This poem began in Odia during my college years, before 1993. I later shared my writing on <a href="https://kabitaprusta.blogspot.com/">Ahimanikya Kabita Prusta</a>. With help from AI, the poem has found a new form in music and video. This page invites you to bring your language, your voice and your care to it—so the feeling can travel further.</p></div><aside class="author-bio" aria-labelledby="author-name"><div class="eyebrow">THE PERSON BEHIND THE POEM</div><h3 id="author-name">Ahimanikya Satapathy</h3><p>I’m an entrepreneur, technologist, poet and artist. Creativity runs through how I work and live: designing organisations, building software, writing poems and shaping spaces.</p><p>The form matters less to me than keeping that creativity alive. My college-era poems, my artwork from 1993, and this shared musical experiment are expressions of the same continuing creative life.</p><nav class="author-links" aria-label="Connect with Ahimanikya">{author_links}</nav></aside></section>
<div class="dream-thread" aria-hidden="true"><span>✧</span></div><blockquote class="dream-quote"><p>“free to weave your dreams with mine.”</p><cite>From the English adaptation of <em>I Am Free to Dream</em></cite></blockquote>
<section class="invitation" id="invitation"><div class="invitation-copy"><div class="eyebrow">THIS IS AN INVITATION</div><h2>A language is a living culture.</h2><p>Bring the language you call home. Offer a phrase that feels more natural, share a listening note, or sing the poem in your own way. We’ll shape each version together, with care and credit for every contribution.</p><div class="action-row"><a class="button" href="contribute.html">Suggest a change →</a><a class="button secondary" href="contribute.html?type=recording">Submit your version →</a></div></div><figure class="author-artwork"><a href="media/images/ahimanikya-artwork-1993.png" aria-label="View the full artwork by Ahimanikya Satapathy"><img src="media/images/ahimanikya-artwork-1993.png" width="347" height="640" alt="Hand-painted profile looking upward, in charcoal and blue-grey tones on cream paper; signed by Ahimanikya Satapathy, 1993"></a><figcaption>Artwork by Ahimanikya Satapathy · 1993</figcaption></figure></section>'''
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
    home = ['# World is One — A Poem Without Borders\n\nOne poem. Many voices. Shared dreams.\n']
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
