"""Prepare selected print editions from unchanged original RGB pixels.

Requires requirements-art-print.txt. Run this, then build_art_prints.py.
--check verifies the artwork region against its original without writing.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = {
    'art-22': {'size': (2688, 4032), 'top': 32, 'title_y': 3608, 'caption_y': 3745, 'rule_y': 3850, 'credit_y': 3895, 'crop': .883},
    'art-17': {'size': (2432, 3648), 'top': 40, 'title_y': 3135, 'caption_y': 3272, 'rule_y': 3380, 'credit_y': 3440, 'crop': .85},
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(root=ROOT, check=False):
    originals=json.loads((root/'catalog/artworks.json').read_text())['artworks']
    path=root/'catalog/ai-artworks.json'
    data=json.loads(path.read_text())
    layouts_path=root/'catalog/artwork-screen-layouts.json'
    screen=json.loads(layouts_path.read_text())
    for ident, layout in LAYOUTS.items():
        art=next(x for x in originals if x['id']==ident)
        source=root/art['master']
        if digest(source)!=art['master_sha256']: raise ValueError('Original checksum mismatch')
        original=Image.open(source).convert('RGB')
        if original.size!=(art['master_width'],art['master_height']): raise ValueError('Original dimensions mismatch')
        width,height=layout['size']
        left=(width-original.width)//2
        top=layout['top']
        box=(left,top,left+original.width,top+original.height)
        if box[3]>=layout['title_y']: raise ValueError('Artwork overlaps caption')
        target=root/f'media/ai-artworks/{ident}-original-prepared-v3.png'
        if not check:
            poster=Image.new('RGB',(width,height),'#f6f1e6')
            poster.paste(original,(left,top))
            draw=ImageDraw.Draw(poster)
            fonts=root/'assets/print-fonts'
            regular=str(fonts/'LiberationSerif-Regular.ttf')
            italic=str(fonts/'LiberationSerif-Italic.ttf')
            def tracked(text,y,size,spacing):
                font=ImageFont.truetype(regular,size)
                length=sum(draw.textlength(c,font=font) for c in text)+spacing*(len(text)-1)
                if length>width*.9: raise ValueError('Title too wide')
                x=(width-length)/2
                for c in text:
                    draw.text((x,y),c,font=font,fill='#263139',anchor='lt')
                    x+=draw.textlength(c,font=font)+spacing
            tracked(art['label'].upper(),layout['title_y'],round(width*.042),round(width*.006))
            caption=ImageFont.truetype(italic,round(width*.03))
            if draw.textlength(art['caption'],font=caption)>width*.9: raise ValueError('Caption too wide')
            draw.text((width/2,layout['caption_y']),art['caption'],font=caption,fill='#263139',anchor='mt')
            draw.line((width*.46,layout['rule_y'],width*.54,layout['rule_y']),fill='#263139',width=2)
            tracked('AHIMANIKYA SATAPATHY',layout['credit_y'],round(width*.021),round(width*.003))
            poster.save(target)
        with Image.open(target) as result:
            if result.size!=(width,height): raise ValueError('Layout dimensions changed')
            if ImageChops.difference(result.crop(box).convert('RGB'),original).getbbox() is not None:
                raise ValueError('Original artwork pixels changed')
        print(f'{art["label"]}: verified identical artwork pixels, no cropping, stretching or retouching.',flush=True)
        if check: continue
        item=next(x for x in data['artworks'] if x.get('source_artwork_id')==ident)
        history=root/f'catalog/{ident}-original-preparation-history.json'
        if not history.exists():
            history.write_text(json.dumps({'date':'2026-09-27','previous_edition':item,'reason':'Artist approved original-based preparation to preserve paint softness and irregular ink.'},ensure_ascii=False,indent=2)+'\n')
        unchanged=item.get('file')==target.relative_to(root).as_posix() and item.get('sha256')==digest(target)
        item.update(file=target.relative_to(root).as_posix(),width=width,height=height,sha256=digest(target),
            description='The original artwork, presented with its title and poetic caption.',
            origin='Prepared directly from the original photograph. Paint, ink and paper texture are unchanged; only the surrounding paper and lettering were added. No generative editing.',
            method='Non-generative layout. Original decoded RGB pixels placed intact without retouching or resizing.',
            refinement_note='Replaces the generated edition to preserve the original marks and texture.',
            preparation_script='scripts/prepare_original_art_editions.py',preparation_source_sha256=art['master_sha256'],
            artwork_box=list(box),review_status='prepared_for_artist_review')
        item.pop('prompt_file',None)
        if not unchanged: item.pop('print_download',None)
        screen['art_bottom_fraction'][ident]=layout['crop']
    if not check:
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        layouts_path.write_text(json.dumps(screen,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    prepare(check=parser.parse_args().check)
