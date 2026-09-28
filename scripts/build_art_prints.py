#!/usr/bin/env python3
"""Create faithful 4x print downloads for refined editions and originals.

Install requirements-art-print.txt, then run from any directory. Refined JPEGs
retain existing lettering; original-photo JPEGs add a caption outside the art.
No AI model, sharpening, cropping or source-file edits are involved.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageCms, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root=ROOT, check=False):
    catalog_path = root / 'catalog/ai-artworks.json'
    data = json.loads(catalog_path.read_text())
    selected = {x['id'] for x in json.loads((root / 'catalog/artworks.json').read_text())['artworks']}
    count = 0
    for item in data['artworks']:
        if item.get('source_artwork_id') not in selected:
            continue
        source = (root / item['file']).resolve()
        if not source.is_relative_to((root / 'media').resolve()):
            raise ValueError('Source must be in media')
        source_hash = digest(source)
        if source_hash != item['sha256']:
            raise ValueError(f'Source changed or not hydrated: {source.name}')
        target = root / 'media/prints' / (source.stem + '-4x.jpg')
        with Image.open(source) as original:
            if original.size != (item['width'], item['height']):
                raise ValueError(f'Incorrect source dimensions: {source.name}')
            size = tuple(n * 4 for n in original.size)
            previous = item.get('print_download', {})
            current = (target.is_file() and previous.get('source_sha256') == source_hash
                       and previous.get('sha256') == digest(target)
                       and previous.get('file') == target.relative_to(root).as_posix()
                       and (previous.get('width'), previous.get('height')) == size
                       and previous.get('scale') == 4
                       and previous.get('jpeg_quality') == 95
                       and previous.get('jpeg_subsampling') == 0)
            if check and not current:
                raise ValueError(f'Missing or stale 4x print: {source.name}')
            if not current:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Untagged generated RGB editions are treated as sRGB. Preserve
                # existing embedded profiles when supplied by a future source.
                profile = original.info.get('icc_profile') or ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
                enlarged = original.resize(size, Image.Resampling.LANCZOS).convert('RGB')
                metadata = Image.Exif()
                metadata[315] = 'Ahimanikya Satapathy'
                metadata[270] = item['title'] + '; 4x captioned print enlargement'
                temporary = target.with_suffix('.tmp')
                enlarged.save(temporary, format='JPEG', quality=95, subsampling=0,
                              optimize=True, dpi=(300, 300), icc_profile=profile, exif=metadata)
                enlarged.close()
                temporary.replace(target)
            with Image.open(target) as result:
                if result.size != size or result.format != 'JPEG':
                    raise ValueError(f'Incorrect print dimensions: {target.name}')
                result.verify()
            if not check:
                item['print_download'] = {
                    'file': target.relative_to(root).as_posix(),
                    'width': size[0], 'height': size[1], 'scale': 4,
                    'method': 'Lanczos enlargement; no generated detail or sharpening',
                    'source_sha256': source_hash, 'sha256': digest(target),
                    'bytes': target.stat().st_size, 'dpi_metadata': 300,
                    'pillow_version': previous.get('pillow_version', pillow_version) if current else pillow_version,
                    'embedded_text': True, 'format': 'JPEG',
                    'jpeg_quality': 95, 'jpeg_subsampling': 0,
                    'colour_profile': 'source_icc' if original.info.get('icc_profile') else 'sRGB_assumed_for_untagged_source',
                }
            count += 1
            print(f'{"Checked" if current else "Created"} {target.name}: {size[0]} x {size[1]}', flush=True)
    if not check:
        temporary = catalog_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(catalog_path)
    print(f'{count} captioned print downloads {"verified" if check else "ready"}.')



def original_layout_key(item):
    return hashlib.sha256(json.dumps([item['master_sha256'], item['label'], item['caption'], ('original-caption-wide-v2' if item['master_width'] > item['master_height'] else 'original-caption-v1')], ensure_ascii=False).encode()).hexdigest()


def original_poster(root, original, item):
    """Enlarge the unmodified photograph 4x; add text in a separate paper margin."""
    from PIL import ImageDraw, ImageFont
    aw, ah = (n * 4 for n in original.size)
    margin = round(aw * .055)
    width = aw + margin * 2
    fonts = root / 'assets/print-fonts'
    regular = fonts / 'LiberationSerif-Regular.ttf'
    italic = fonts / 'LiberationSerif-Italic.ttf'
    type_scale = min(width, ah * 1.25)
    title = item['label'].upper()
    title_size = round(type_scale * .052)
    title_font = ImageFont.truetype(str(regular), title_size)
    while title_font.getlength(title) > width * .84:
        title_size -= 2
        title_font = ImageFont.truetype(str(regular), title_size)
    caption_size = round(type_scale * .032)
    caption_font = ImageFont.truetype(str(italic), caption_size)
    credit_font = ImageFont.truetype(str(regular), round(type_scale * .023))
    lines = []
    line = ''
    for word in item['caption'].split():
        candidate = (line + ' ' + word).strip()
        if line and caption_font.getlength(candidate) > width * .80:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    gap = round(type_scale * .035)
    line_height = round(caption_size * 1.5)
    footer = gap + title_size + gap + len(lines)*line_height + gap + credit_font.size + gap
    height = margin + ah + footer
    poster = Image.new('RGB', (width, height), '#f6f1e6')
    art = original.resize((aw, ah), Image.Resampling.LANCZOS).convert('RGB')
    poster.paste(art, (margin, margin))
    art.close()
    draw = ImageDraw.Draw(poster)
    y = margin + ah + gap
    draw.text((width/2, y), title, font=title_font, fill='#27231f', anchor='mt')
    y += title_size + gap
    for line in lines:
        draw.text((width/2, y), line, font=caption_font, fill='#302b23', anchor='mt')
        y += line_height
    y += gap
    draw.text((width/2, y), 'AHIMANIKYA SATAPATHY', font=credit_font, fill='#302b23', anchor='mt')
    return poster, (margin, margin, margin+aw, margin+ah)


def build_originals(root=ROOT, check=False):
    path = root / 'catalog/artworks.json'
    data = json.loads(path.read_text())
    # Only locally authored, checksum-verified photographs are processed. The
    # largest known file is under 200 megapixels including its new text margin.
    Image.MAX_IMAGE_PIXELS = 250_000_000
    for item in data['artworks']:
        source = (root / item['master']).resolve()
        if not source.is_relative_to((root / 'media/artworks').resolve()):
            raise ValueError('Original source must be in media/artworks')
        if digest(source) != item['master_sha256']:
            raise ValueError(f'Original changed or not hydrated: {source.name}')
        target = root / 'media/prints' / (item['id'] + '-original-captioned-4x.jpg')
        previous = item.get('print_edition', {})
        key = original_layout_key(item)
        current = (target.is_file() and previous.get('layout_key') == key
                   and previous.get('sha256') == digest(target)
                   and previous.get('scale') == 4)
        if check and not current:
            raise ValueError(f'Missing or stale original print: {item["id"]}')
        if not current:
            with Image.open(source) as original:
                if original.size != (item['master_width'], item['master_height']):
                    raise ValueError('Incorrect original dimensions')
                poster, box = original_poster(root, original, item)
                size = poster.size
                kwargs = {'icc_profile': original.info['icc_profile']} if original.info.get('icc_profile') else {}
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix('.tmp')
                poster.save(temporary, format='JPEG', quality=95, subsampling=0, optimize=True, dpi=(300, 300), **kwargs)
                poster.close()
                temporary.replace(target)
            item['print_edition'] = {
                'file': target.relative_to(root).as_posix(), 'width': size[0], 'height': size[1],
                'artwork_width': item['master_width']*4, 'artwork_height': item['master_height']*4,
                'artwork_box': list(box), 'scale': 4, 'layout_key': key,
                'source_sha256': item['master_sha256'], 'sha256': digest(target),
                'bytes': target.stat().st_size, 'dpi_metadata': 300,
                'method_label': '4× original artwork with embedded caption · JPEG',
                'note': 'The original photograph is enlarged 4× in each dimension, with title, poetic caption and artist credit added below. No new artwork detail is generated. Dimensions include the paper margin.',
                'embedded_text': True, 'pillow_version': pillow_version,
                'jpeg_quality': 95, 'jpeg_subsampling': 0,
            }
        with Image.open(target) as result:
            if result.size != (item['print_edition']['width'], item['print_edition']['height']):
                raise ValueError('Incorrect original print dimensions')
            result.verify()
        print(f'{"Checked" if current else "Created"} {target.name}: {target.stat().st_size/1024/1024:.1f} MB', flush=True)
    if not check:
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
        temporary.replace(path)
    print(f'{len(data["artworks"])} original captioned print downloads {"verified" if check else "ready"}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify without generating or modifying files')
    args = parser.parse_args()
    build(check=args.check)
    build_originals(check=args.check)
