"""Prepare Grandmother directly from original pixels; no generative editing.

Run after installing requirements-art-print.txt. The native drawing is pasted
without resizing or retouching; print enlargement is a separate pipeline step.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]

def run(root, check=False):
    originals = json.loads((root/'catalog/artworks.json').read_text())['artworks']
    art = next(x for x in originals if x['id'] == 'art-07')
    source = root/art['master']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == art['master_sha256']
    original = Image.open(source).convert('RGB')
    assert original.size == (1393, 1679)
    target = root/'media/ai-artworks/art-07-original-prepared-v3.png'
    box = (71, 50, 1464, 1729)
    if not check:
        paper = Image.new('RGB', (1536, 2304), '#f6f1e6')
        paper.paste(original, box[:2])
        draw = ImageDraw.Draw(paper)
        fonts = root/'assets/print-fonts'
        regular = str(fonts/'LiberationSerif-Regular.ttf')
        italic = str(fonts/'LiberationSerif-Italic.ttf')
        def tracked(text, y, size, spacing):
            font = ImageFont.truetype(regular, size)
            width = sum(draw.textlength(c,font=font) for c in text) + spacing*(len(text)-1)
            x = (1536-width)/2
            for c in text:
                draw.text((x,y),c,font=font,fill='#263139',anchor='lt')
                x += draw.textlength(c,font=font)+spacing
        tracked(art['label'].upper(),1842,78,11)
        draw.text((768,1966),art['caption'],font=ImageFont.truetype(italic,49),fill='#263139',anchor='mt')
        draw.line((711,2100,825,2100),fill='#263139',width=2)
        tracked('AHIMANIKYA SATAPATHY',2170,33,6)
        paper.save(target)
    with Image.open(target) as result:
        assert result.size == (1536,2304)
        diff = ImageChops.difference(result.crop(box).convert('RGB'),original)
        assert diff.getbbox() is None, 'Artwork pixels changed'
    print('Verified: every artwork pixel is identical to the decoded original; captions are outside the drawing.')
    if check: return
    path = root/'catalog/ai-artworks.json'
    data = json.loads(path.read_text())
    item = next(x for x in data['artworks'] if x.get('source_artwork_id') == 'art-07')
    history = root/'catalog/grandmother-print-history.json'
    if not history.exists():
        history.write_text(json.dumps({'previous_edition':item,'reason':'Artist approved direct preparation from original to preserve facial expression.','date':'2026-09-27'},ensure_ascii=False,indent=2)+'\n')
    item.update(file=target.relative_to(root).as_posix(),width=1536,height=2304,
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        description='Your original drawing, carefully presented with its title and poetic caption.',
        origin='Prepared directly from the original photograph. The drawing is unchanged; only the surrounding paper and lettering were added. No generative editing.',
        method='Non-generative layout. Original decoded RGB pixels placed intact, without retouching or resizing.',
        refinement_note='Replaces the generated portrait with the original expression and marks. Paper texture within the artwork is preserved.',
        preparation_script='scripts/prepare_grandmother_print.py',
        preparation_source_sha256=art['master_sha256'],artwork_box=list(box),
        review_status='prepared_for_artist_review')
    item.pop('prompt_file',None)
    item.pop('print_download',None)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    layout=root/'catalog/artwork-screen-layouts.json'
    data=json.loads(layout.read_text())
    data['art_bottom_fraction']['art-07']=.775
    layout.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    run(ROOT,args.check)
