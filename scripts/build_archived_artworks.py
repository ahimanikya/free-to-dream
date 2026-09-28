"""Build the private art journal from preserved assets; never publish or restore them."""
import argparse
import base64
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(archive_root):
    archive_root = archive_root.resolve()
    data = json.loads((ROOT / 'catalog/archived-artworks.json').read_text())
    works = [work for work in data['artworks'] if work.get('status') == 'archived']
    css = []
    cards = {}
    for work in works:
        source = archive_root / work['image']
        for key in ('image', 'master'):
            path = (archive_root / work[key]).resolve()
            if not path.is_relative_to(archive_root):
                raise ValueError('Archive asset outside preserved root')
            if hashlib.sha256(path.read_bytes()).hexdigest() != work[key + '_sha256']:
                raise ValueError(f'Changed source: {work["id"]} {key}')
        encoded = base64.b64encode(source.read_bytes()).decode()
        mime = 'image/png' if source.suffix.lower() == '.png' else 'image/jpeg'
        width, height = work['width'], work['height']
        fill_size = work['presentation'].get('fill_size', '100% 100%')
        if fill_size not in ('cover', '100% 100%'):
            raise ValueError('Unsupported background sizing')
        props = [f'--art-ratio:{width / height:.12f}', '--fill-softness:1.1px', f'--fill-size:{fill_size}']
        for side, edge in work['edges'].items():
            x, y, w, h = edge['sample']
            if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
                raise ValueError(f'Invalid sample: {work["id"]} {side}')
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                   f'viewBox="{x} {y} {w} {h}" preserveAspectRatio="none">'
                   f'<title>{html.escape(work["label"])}: display background only</title>'
                   f'<image width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/></svg>')
            target = archive_root / edge['asset']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(svg)
            version = hashlib.sha256(svg.encode()).hexdigest()[:10]
            props.append(f'--edge-{side}:url("{edge["asset"]}?v={version}")')
        css.append(f'.archive-{work["id"]}' + '{' + ';'.join(props) + '}')
        variant = 'tall' if width / height < .8 else 'wide'
        title, phrase, narrative = (html.escape(work[k]) for k in ('label', 'caption', 'narrative'))
        master, preview = (html.escape(work[k], quote=True) for k in ('master', 'image'))
        note = html.escape(html.unescape(re.sub(r'<[^>]+>', '', work['selection_note_html'])))
        fill = '<span class="art-edge-fill" aria-hidden="true">' + ''.join(
            f'<span class="art-edge-{side}"></span>' for side in ('left', 'right', 'top', 'bottom')) + '</span>'
        cards[work['id']] = f'''<figure id="{work['id']}">
<a class="art-wall" href="{master}" aria-label="View full-size {title}">
<div class="art-frame archive-{work['id']} frame-{variant} frame-{work['presentation']['frame']} mat-{work['presentation']['mat']}">
<div class="art-mat"><div class="art-window">{fill}<img src="{preview}" width="{width}" height="{height}" loading="lazy" alt="{title}"></div></div></div></a>
<figcaption><h2>{title}</h2><p class="poetic-phrase">{phrase}</p><p class="poetic-description">{narrative}</p>
<a class="full-size" href="{master}">Look closer ↗</a>
<details><summary>Archive note</summary><p>{note}</p><p>Earlier display title: {html.escape(work['previous_display_title'])}. {work['id']}.</p></details></figcaption></figure>'''
    tall = [w for w in works if w['width'] / w['height'] < .8]
    wide = [w for w in works if w['width'] / w['height'] >= .8]
    rows = []
    while tall or wide:
        for group in (tall, wide):
            if group:
                row, group[:3] = group[:3], []
                rows.append('<div class="archive-row">' + ''.join(cards[w['id']] for w in row) + '</div>')
    styles = '''
*{box-sizing:border-box}body{margin:0;background:#f6f2e9;color:#293c35;font:16px/1.7 system-ui,sans-serif}
main{max-width:1180px;margin:auto;padding:40px 26px 80px}header{max-width:740px;margin-bottom:40px}
header small{font-size:11px;letter-spacing:.12em}h1{font:48px/1.15 Georgia,serif;margin:18px 0}
h2{font:27px/1.2 Georgia,serif;margin:22px 0 10px}a{color:inherit;text-underline-offset:4px}
.archive-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:40px 28px;margin-top:40px}
figure{min-width:0;margin:0;border-top:1px solid #d4cbbb;padding-top:16px}
.archive-row .art-wall{padding:26px 20px 34px;--frame-size:8px;--mat-size:16px;height:410px;min-height:410px}
.archive-row .art-wall:has(.frame-wide){height:290px;min-height:290px}
.archive-row .frame-tall{width:225px}.archive-row .frame-wide{width:300px}
.poetic-phrase{font:italic 19px/1.45 Georgia,serif;color:#354c40;margin:0 0 14px}
.poetic-description{font-size:15px;line-height:1.75;color:#52625b;margin:0 0 16px}
.full-size,details{font-size:13px}details{margin-top:16px;color:#696c61}summary{cursor:pointer;padding:6px 0}
details p{line-height:1.65}.archive-footer{margin:56px 0 0;padding-top:24px;border-top:1px solid #d4cbbb;color:#696c61;font-size:13px;max-width:760px}
@media(max-width:850px){.archive-row{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:540px){.archive-row{grid-template-columns:1fr}h1{font-size:38px}main{padding:28px 20px 60px}}
'''
    archive_css = archive_root / 'archived-artworks.css'
    archive_css.write_text(styles + '\n' + '\n'.join(css))
    version = hashlib.sha256(archive_css.read_bytes()).hexdigest()[:10]
    frame_version = hashlib.sha256((ROOT / 'web/art-frames.css').read_bytes()).hexdigest()[:10]
    # Shared framing is copied separately so it also serves the existing review gallery.
    (archive_root / 'art-frames.css').write_text((ROOT / 'web/art-frames.css').read_text().replace(
        'url("../media/', 'url("http://127.0.0.1:8766/media/'))
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Still With Us · Archived art</title><link rel="stylesheet" href="art-frames.css?v={frame_version}"><link rel="stylesheet" href="archived-artworks.css?v={version}"></head>
<body><main><header><small>ART BY AHIMANIKYA SATAPATHY · PRIVATE ARCHIVE</small><h1>Still With Us</h1><p>Some things stay, even when we set them aside.</p><p>{len(works)} works from the archive, with words for the feelings they leave behind.</p><p><a href="ranked-artworks.html?view=poetic-compact">Return to the selected works</a></p></header>
{''.join(rows)}<p class="archive-footer">These works remain outside the public selection. Titles and words are contemporary poetic responses; they do not claim to describe the artist’s original intention. The photographs and full-size originals are preserved unchanged. Earlier selection notes remain available beneath each work.</p></main></body></html>'''
    (archive_root / 'archived-artworks.html').write_text(page)
    print(f'Built private archive: {len(works)} works, {len(rows)} rows; sources verified unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root', type=Path, required=True)
    build(parser.parse_args().archive_root)
