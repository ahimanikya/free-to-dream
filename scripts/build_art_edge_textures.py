"""Rebuild display-only edge samples, preserving every source artwork byte."""
import base64
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    metadata = json.loads((ROOT / 'catalog/artwork-textures.json').read_text())
    catalog = json.loads((ROOT / 'catalog/artworks.json').read_text())
    items = catalog if isinstance(catalog, list) else catalog['artworks']
    dimensions = {i['id']: (i['width'], i['height']) for i in items}
    for artwork in metadata['textures']:
        source = ROOT / artwork['source']
        mime = 'image/png' if source.suffix == '.png' else 'image/jpeg'
        encoded = base64.b64encode(source.read_bytes()).decode()
        width, height = dimensions[artwork['id']]
        for side, edge in artwork['edges'].items():
            x, y, w, h = edge['sample']
            parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">',
                     f'<title>{html.escape(artwork["id"])} {side} background sample</title>',
                     f'<defs><image id="source" width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/></defs>',
                     f'<svg width="{w}" height="{h}" viewBox="{x} {y} {w} {h}" preserveAspectRatio="none"><use href="#source"/></svg>']
            for n, patch in enumerate(edge.get('patches', [])):
                tx, ty, tw, th = patch['target']
                sx, sy, sw, sh = patch['source']
                # A short source-space feather softens the replacement only.
                horizontal = w > h
                fade = min(0.12, 8 / (tw if horizontal else th))
                gradient_axis = 'x2="1" y2="0"' if horizontal else 'x2="0" y2="1"'
                parts.append(f'<defs><linearGradient id="fade-{n}" {gradient_axis}><stop stop-color="white" stop-opacity="0"/><stop offset="{fade}" stop-color="white"/><stop offset="{1-fade}" stop-color="white"/><stop offset="1" stop-color="white" stop-opacity="0"/></linearGradient><mask id="patch-{n}" maskUnits="userSpaceOnUse" x="{tx}" y="{ty}" width="{tw}" height="{th}"><rect x="{tx}" y="{ty}" width="{tw}" height="{th}" fill="url(#fade-{n})"/></mask></defs>')
                parts.append(f'<g mask="url(#patch-{n})"><svg x="{tx}" y="{ty}" width="{tw}" height="{th}" viewBox="{sx} {sy} {sw} {sh}" preserveAspectRatio="none"><use href="#source"/></svg></g>')
            parts.append('</svg>')
            (ROOT / edge['asset']).write_text(''.join(parts))


if __name__ == '__main__':
    build()
