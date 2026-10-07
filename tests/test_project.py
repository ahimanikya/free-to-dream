from argparse import Namespace
from functools import partial
from html.parser import HTMLParser
import importlib.util
import json
import re
from html import unescape
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('project', PROJECT/'scripts/project.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets=[]
    def handle_starttag(self, tag, attrs):
        self.targets.extend(value for name,value in attrs if name in ('href','src') and value)


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ('kb','catalog','web','media','production'):
            shutil.copytree(PROJECT/folder, self.root/folder, ignore=shutil.ignore_patterns(*(f'*{ext}' for ext in app.MEDIA_EXTENSIONS)))
        shutil.copy2(PROJECT/'site-config.json', self.root/'site-config.json')
        self.overrides = patch.multiple(app, ROOT=self.root, KB=self.root/'kb', LANGUAGES=self.root/'kb/poems/i-am-free-to-dream/languages')
        self.overrides.start()
        # Default fixtures stay private; integration tests opt in to the real catalog.
        items = app.records()
        for item in items:
            item.update(public_preview=False, public_url=None)
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))

    def tearDown(self):
        self.overrides.stop(); self.temp.cleanup()

    def test_public_build_has_working_internal_links_and_excludes_local_media(self):
        (self.root/'local-assets').mkdir()
        (self.root/'local-assets/private-evidence.txt').write_text('PRIVATE SENTINEL')
        app.build(False)
        output = self.root/'site-public'
        self.assertFalse((output/'local-assets').exists())
        self.assertFalse((output/'media/recordings').exists())
        for page in output.glob('*.html'):
            text = page.read_text()
            self.assertNotIn('PRIVATE SENTINEL', text)
            if page.name != 'timing.html':
                # The gallery's empty soundtrack control is populated only from the public catalog.
                checked = re.sub(r'<audio id="slideshow-audio"[^>]*></audio>', '', text)
                self.assertNotIn('<audio ', checked)
                for audio_tag in re.findall(r'<audio id="slideshow-audio"[^>]*>', text):
                    self.assertNotIn('src=', audio_tag)
            links = Links(); links.feed(text)
            for target in links.targets:
                url = urlparse(target)
                if not url.scheme and url.path:
                    self.assertTrue((page.parent/unquote(url.path)).is_file(), f'{page.name}: missing {target}')

    def test_four_times_art_downloads_preserve_sources_and_reject_stale_files(self):
        app.build(False)
        output = self.root/'site-public'
        originals = json.loads((self.root/'catalog/artworks.json').read_text())['artworks']
        refined = json.loads((self.root/'catalog/ai-artworks.json').read_text())['artworks']
        for item in originals:
            edition = item['print_edition']
            page = (output/('artwork--'+item['id']+'.html')).read_text()
            self.assertIn(edition['file'], page)
            self.assertTrue(edition['embedded_text'])
            self.assertEqual(edition['artwork_width'], item['master_width']*4)
            self.assertEqual(edition['artwork_height'], item['master_height']*4)
            self.assertEqual((self.root/edition['file']).read_bytes(), (output/edition['file']).read_bytes())
        for item in refined:
            if not item.get('source_artwork_id'):
                continue
            edition = item['print_download']
            self.assertTrue(edition['file'].endswith('.jpg'))
            self.assertEqual(edition['jpeg_subsampling'], 0)
            self.assertEqual(app.jpeg_dimensions((self.root/edition['file']).read_bytes()), (item['width']*4, item['height']*4))
            page = (output/('artwork--'+item['source_artwork_id']+'.html')).read_text()
            self.assertIn(edition['file'], page)
            self.assertIn('pixels · JPEG', page)
            self.assertEqual((edition['width'], edition['height']), (item['width']*4, item['height']*4))
            self.assertEqual((self.root/edition['file']).read_bytes(), (output/edition['file']).read_bytes())
            self.assertIn('No new artwork detail', (output/('artwork--'+item['source_artwork_id']+'.html')).read_text())
        manifest = self.root/'catalog/artworks.json'
        data = json.loads(manifest.read_text())
        data['artworks'][0]['caption'] += ' A changed caption.'
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Stale original 4x print source or caption'):
            app.validate_art_prints()
        data['artworks'][0]['caption'] = originals[0]['caption']
        manifest.write_text(json.dumps(data))
        enlarged = self.root/refined[1]['print_download']['file']
        enlarged.write_text('version https://git-lfs.github.com/spec/v1\n')
        with self.assertRaisesRegex(ValueError, '4x print is not hydrated'):
            app.validate_art_prints()

    def test_archived_canvas_is_preserved_but_not_published(self):
        app.build(False)
        page = (self.root/'site-public/artwork--art-64.html').read_text()
        archive = self.root/'media/archive/the-witness-canvas'
        self.assertTrue((archive/'ahi-art-canvas-24x48.pdf').is_file())
        self.assertFalse((self.root/'site-public/media/archive').exists())
        self.assertFalse((self.root/'site-public/media/prints/ahi-art-canvas-24x48.pdf').exists())
        self.assertNotIn('canvas-edition', page)
        self.assertNotIn('View PDF', page)
        self.assertIn('<details class="art-print-disclosure" id="refined-download">', page)
        self.assertIn('Download original image', page)

    def test_artwork_galleries_separate_originals_from_verified_ai_images(self):
        app.build(False)
        output = self.root/'site-public'
        works = json.loads((self.root/'catalog/artworks.json').read_text())['artworks']
        self.assertEqual(len({item['master_sha256'] for item in works}), len(works))
        gallery = (output/'original-artworks.html').read_text()
        self.assertEqual(gallery.count('class="portfolio-card"'), len(works))
        self.assertNotIn('id="art-more"', gallery)
        self.assertNotIn('data-page-size', gallery)
        self.assertNotIn('portfolio-narrative', gallery)
        for item in works:
            detail_name = 'artwork--'+item['id']+'.html'
            self.assertIn(detail_name, gallery)
            detail = (output/detail_name).read_text()
            self.assertIn(item['master'], detail)
            self.assertIn(item['detail_reflections'][1], unescape(detail))
            self.assertRegex(detail, r'href="(?:original-)?artworks\.html#'+item['id']+'"')
            self.assertNotIn('art-detail-trail', detail)
            self.assertIn('aria-label="Main navigation"', detail)
            self.assertIn('aria-label="Artwork navigation"', detail)
            self.assertIn('id="art-slideshow-start"', detail)
            self.assertIn('<details class="art-story-more">', detail)
            self.assertNotIn('class="art-detail-heading"', detail)
            self.assertEqual((self.root/item['master']).read_bytes(), (output/item['master']).read_bytes())
        # Previous/next must follow the visible frame groups, including wraparound.
        displayed_ids = re.findall(r'<figure class="portfolio-card" id="([^"]+)"', gallery)
        self.assertEqual(displayed_ids, [item['id'] for item in app.artwork_display_order(works)])
        for position, ident in enumerate(displayed_ids):
            detail = (output/('artwork--'+ident+'.html')).read_text()
            previous = displayed_ids[(position-1) % len(displayed_ids)]
            following = displayed_ids[(position+1) % len(displayed_ids)]
            self.assertIn(f'href="artwork--{previous}.html" aria-label="Previous artwork:', detail)
            self.assertIn(f'href="artwork--{following}.html" aria-label="Next artwork:', detail)
            anchors = set(re.findall(r'\bid="([^"]+)"', detail))
            for target in re.findall(r'href="#([^"]+)"', detail):
                self.assertIn(target, anchors, f'{ident}: missing section {target}')
        art_page = (output/'guides--artwork.html').read_text()
        self.assertNotIn('media/artworks/art-64.png', art_page)
        self.assertNotIn('<figure', art_page)
        self.assertIn('Design roots and credits', art_page)
        self.assertNotIn('artwork--art-64.html#canvas-edition', art_page)
        self.assertIn('href="artworks.html"', art_page)
        self.assertIn('href="guides--brand.html"', art_page)
        self.assertNotIn('the-witness-poster.png', art_page)
        self.assertNotIn('AI-generated potter', art_page)
        self.assertFalse((output/'media/images/the-witness-poster.png').exists())
        ai_page = (output/'artworks.html').read_text()
        ai_image = 'media/ai-artworks/the-witness-refined-print-v2.png'
        self.assertIn(ai_image, ai_page)
        self.assertNotIn(ai_image, art_page)
        self.assertNotIn(ai_image, gallery)
        self.assertIn('AI-assisted cleanup and print preparation', ai_page)
        editions = json.loads((self.root/'catalog/ai-artworks.json').read_text())['artworks']
        original_ids = {item['id'] for item in works}
        refined = [item for item in editions if item.get('source_artwork_id') in original_ids]
        self.assertEqual(ai_page.count('class="portfolio-card"'), len(refined))
        self.assertNotIn('id="potter-dream"', ai_page)
        self.assertNotIn('class="gallery-piece"', ai_page)
        self.assertIn('assets/art-frames.css', ai_page)
        self.assertEqual(ai_page.count('refined-frame'), len(refined))
        self.assertEqual(ai_page.count('data-print-caption'), len(refined))
        self.assertIn('assets/art-caption-layouts.css', ai_page)
        screen_css = (output/'assets/art-caption-layouts.css').read_text()
        for edition in refined:
            self.assertIn('.screen-art-'+edition['source_artwork_id']+' {', screen_css)

        self.assertNotIn('art-story-arrow', ai_page)
        for item in refined:
            self.assertIn(f'href="artwork--{item["source_artwork_id"]}.html#ai-edition"', ai_page)
        self.assertNotIn('class="art-edition-switch"', ai_page)
        self.assertNotIn('href="original-artworks.html"', ai_page)
        self.assertIn('href="original-artworks.html" aria-current="page">Original art', gallery)
        self.assertIn('href="artworks.html"', gallery)
        witness_detail = (output/'artwork--art-64.html').read_text()
        self.assertIn(ai_image, witness_detail)
        self.assertIn('id="ai-edition"', witness_detail)
        self.assertIn('REFINED PRINT EDITION', witness_detail)
        self.assertNotIn('href="ai-artworks.html"', witness_detail)
        self.assertIn('/media/artworks/art-64.png', gallery)
        master = self.root/works[0]['master']
        original = master.read_bytes()
        master.write_text('version https://git-lfs.github.com/spec/v1\n')
        with self.assertRaisesRegex(ValueError, 'not hydrated'):
            app.build(False)
        master.write_bytes(original+b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            app.build(False)

    def test_discovery_exports_truthful_status_sources_and_no_private_recordings(self):
        app.build(False)
        output = self.root/'site-public'
        data = json.loads((output/'reference.json').read_text())
        self.assertEqual(len(data['languages']), 102)
        self.assertEqual(data['counts']['original_or_adapted_texts'], 30)
        for entry in data['languages']:
            self.assertEqual(entry['recordings'], [])
            source = self.root/('kb/poems/i-am-free-to-dream/languages/'+entry['slug']+'.md')
            self.assertEqual(entry['source_sha256'], app.hashlib.sha256(source.read_bytes()).hexdigest())
            if not entry['has_target_lyrics']:
                self.assertIsNone(entry['lyrics'])
            self.assertNotIn('local_path', entry)
        self.assertIn('rights', data)
        self.assertIn('Pending briefs are not target-language poems', (output/'llms.txt').read_text())
        self.assertFalse((output/'robots.txt').exists())

    def test_structured_metadata_canonical_sitemap_and_native_text_agree(self):
        app.build(False)
        output = self.root/'site-public'
        descriptions = set()
        for meta in app.validate():
            page = output/('poems--i-am-free-to-dream--languages--'+meta['slug']+'.html')
            text = page.read_text()
            payload = re.search(r'<script type="application/ld\+json">(.*?)</script>',text).group(1)
            graph = json.loads(payload)['@graph']
            work = [x for x in graph if x['@type']=='CreativeWork']
            self.assertEqual(bool(work), app.has_lyrics(meta))
            description = unescape(re.search(r'<meta name="description" content="([^"]+)"', text).group(1))
            self.assertNotIn(description, descriptions)
            descriptions.add(description)
            if meta['slug']=='tamil':
                self.assertIn('<div lang="ta">', text)
                self.assertEqual(work[0]['inLanguage'], 'ta')
            self.assertIn('Intended settings for a future recording',text)
        ns = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locations = [x.text for x in app.ET.parse(output/'sitemap.xml').findall('.//s:loc',ns)]
        self.assertTrue(locations)
        for url in locations:
            filename = url.rsplit('/',1)[1]
            self.assertTrue((output/filename).is_file())
            self.assertNotIn(filename, ('timing.html','contribute.html'))
        self.assertIn('name="robots" content="noindex,follow"',(output/'timing.html').read_text())

    def test_metadata_escapes_untrusted_titles_and_does_not_license_recordings(self):
        config = json.loads((self.root/'site-config.json').read_text())
        record = dict(id='sample',title='</script><script>alert(1)</script>', kind='audio',
                      notes='A review copy',publish=False,public_preview=True,public_url='https://example.org/song.mp3')
        text = app.shell(record['title'], '<p>A review copy</p>',config, filename='recording--sample.html',media=record)
        payload = re.search(r'<script type="application/ld\+json">(.*?)</script>',text).group(1)
        data = json.loads(payload)
        obj = next(x for x in data['@graph'] if x['@type']=='AudioObject')
        self.assertEqual(obj['name'],record['title'])
        self.assertNotIn('license',obj)
        self.assertNotIn('uploadDate',obj)
        self.assertNotIn('</script>',payload)
        digest = app.base64.b64encode(app.hashlib.sha256(payload.encode()).digest()).decode()
        self.assertIn("'sha256-"+digest+"'",text)

    def test_engagement_is_disconnected_and_dashboard_is_not_indexed(self):
        config_path=self.root/'site-config.json'
        disconnected=json.loads(config_path.read_text())
        disconnected['analytics']={'provider':'none','measurement_id':''}
        config_path.write_text(json.dumps(disconnected))
        app.build(False)
        out=self.root/'site-public'
        home=(out/'index.html').read_text()
        self.assertIn('data-analytics-id=""',home)
        self.assertNotIn('https://www.googletagmanager.com',home)
        panel=(out/'engagement.html').read_text()
        self.assertIn('Not connected',panel)
        self.assertIn('Counts are not loaded yet',panel)
        self.assertIn('name="robots" content="noindex,follow"',panel)
        self.assertNotIn('/engagement.html</loc>',(out/'sitemap.xml').read_text())
        self.assertIn('value="share"',(out/'contribute.html').read_text())
        config=json.loads((self.root/'site-config.json').read_text())
        config['analytics']={'provider':'ga4','measurement_id':'G-ABC1234567'}
        configured=app.shell('Test','',config)
        self.assertIn('data-analytics-id="G-ABC1234567"',configured)
        self.assertNotIn('<script src="https://www.googletagmanager.com',configured)
        self.assertIn('data-analytics-id=""',app.shell('Test','',config,local=True))

    def test_release_requires_review_rights_and_https_url(self):
        items = app.records()
        items[0]['publish'] = True
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        with self.assertRaisesRegex(ValueError, 'public_url'): app.validate()
        items[0].update(public_url='https://media.example.org/odia.mp3', review_status='approved', rights_status='confirmed')
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        app.build(False)
        page = (self.root/'site-public/poems--i-am-free-to-dream--languages--odia.html').read_text()
        self.assertIn('src="https://media.example.org/odia.mp3"', page)
        self.assertNotIn('local-assets/',page)

    def test_untrusted_markdown_is_not_executable_and_unicode_survives(self):
        output = app.render_markdown('<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\nମୋତେ ସପ୍ନ\n\n```text\nநான் ஒரு குயவன்.\n\nnext line\n```', app.KB/'project.md')
        self.assertNotIn('<script',output)
        self.assertNotIn('href="javascript:',output)
        self.assertIn('ମୋତେ ସପ୍ନ',output)
        self.assertIn('நான் ஒரு குயவன்.\n\nnext line',output)

    def test_variations_remain_separate_current_choices(self):
        meta={'language':'Tamil','slug':'tamil'}
        def item(ident, variation=None, archived=False):
            data={'id':ident,'language':'tamil','title':ident,'kind':'audio','publish':False,'archived':archived}
            if variation: data.update(variation=variation,variation_label=variation.title())
            return data, 'https://media.example.org/'+ident+'.mp3'
        html=app.resource_panel(meta,[item('original'),item('duet','duet'),item('duet-old','duet',True)])
        self.assertIn('id="listen-original"',html)
        self.assertIn('id="listen-duet"',html)
        current,older=html.split('<details class="earlier-recordings">')
        self.assertIn('original.mp3',current)
        self.assertIn('duet.mp3',current)
        self.assertNotIn('duet-old.mp3',current)
        self.assertIn('duet-old.mp3',older)
        self.assertNotIn('More audio versions',current)

    def test_new_upload_is_copied_without_publishing_and_duplicate_id_rejected(self):
        source = self.root/'new take.mp3'; source.write_bytes(b'test-only media payload')
        args = Namespace(language='hindi',id='hindi-test-01',kind='audio',title='Test',file=str(source),url=None)
        app.add_media(args)
        item = app.records()[-1]
        self.assertFalse(item['publish'])
        self.assertTrue(item['repo_path'].startswith('media/hindi/'))
        self.assertEqual((self.root/item['repo_path']).read_bytes(), source.read_bytes())
        with self.assertRaisesRegex(ValueError, 'already exists'): app.add_media(args)
        with self.assertRaises(ValueError): app.confined('../private.txt')

    def test_public_build_excludes_archive_media_and_lfs_pointers(self):
        folder=self.root/'media/odia'; folder.mkdir(exist_ok=True)
        (folder/'archive.mp4').write_bytes(b'UNRELEASED ARCHIVE VIDEO')
        (folder/'pointer.mp3').write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+'a'*64+'\nsize 100\n')
        app.build(False)
        self.assertFalse((self.root/'site-public/media/odia/archive.mp4').exists())
        self.assertFalse((self.root/'site-public/media/odia/pointer.mp3').exists())

    def test_local_build_plays_hydrated_archive_but_skips_lfs_pointer(self):
        folder=self.root/'media/odia'; folder.mkdir(exist_ok=True)
        path=folder/'review.mp3'
        items=app.records()
        items[0].update(repo_path='media/odia/review.mp3',local_path=None)
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        path.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+'a'*64+'\nsize 100\n')
        app.build(True)
        self.assertFalse((self.root/'site/recording--odia-audio-01.html').exists())
        path.write_bytes(b'HYDRATED TEST AUDIO')
        app.build(True)
        self.assertEqual((self.root/'site/media/recordings/odia-audio-01.mp3').read_bytes(),b'HYDRATED TEST AUDIO')

    def test_srt_validation_and_safe_webvtt(self):
        text = '1\n00:00:01,000 --> 00:00:02,500\nସାଉଁଟି\nସାଉଁଟି <script> &\n\n2\n00:00:03,000 --> 00:00:04,000\nநான் ஒரு குயவன்.\n'
        cues = app.parse_srt('\ufeff' + text.replace('\n', '\r\n'))
        self.assertEqual(cues[0]['start'], 1000)
        self.assertIn('00:00:01.000 --> 00:00:02.500', app.make_vtt(cues))
        self.assertIn('&lt;script&gt; &amp;', app.make_vtt(cues))
        self.assertIn('நான் ஒரு குயவன்.', app.make_vtt(cues))
        for bad in ['', text.replace('2\n00:', '4\n00:'), text.replace('00:00:03,000', '00:00:02,000'), text.replace('00:00:02,500','00:00:00,500'), text.replace('00:00:01,000','00:61:01,000')]:
            with self.assertRaises(ValueError): app.parse_srt(bad)

    def test_srt_belongs_to_exact_take_and_build_derives_downloads(self):
        item = app.records()[0]
        audio = self.root/item['repo_path']; audio.write_bytes(b'original take')
        srt = self.root/'checked.srt'
        srt.write_text('1\n00:00:01,000 --> 00:00:02,000\nମୋତେ ସପ୍ନ\n', encoding='utf-8')
        args = Namespace(id=item['id'], file=str(srt))
        app.add_lyrics(args)
        app.build(True)
        output = self.root/'site/media/lyrics'
        self.assertTrue((output/'odia-audio-01.srt').is_file())
        self.assertTrue((output/'odia-audio-01.vtt').read_text().startswith('WEBVTT\n'))
        self.assertEqual(json.loads((output/'odia-audio-01.json').read_text())[0]['text'], 'ମୋତେ ସପ୍ନ')
        page = (self.root/'site/recording--odia-audio-01.html').read_text()
        self.assertIn('data-lyrics-url="media/lyrics/odia-audio-01.json"', page)
        app.build(False)
        self.assertFalse((self.root/'site-public/media/lyrics').exists())
        self.assertFalse((self.root/'site-public'/audio.with_suffix('.srt').relative_to(self.root)).exists())
        # LFS pointer checkouts validate against the same content identity.
        digest = app.recording_digest(item)
        audio.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:'+digest+'\nsize 13\n')
        app.validate()
        audio.write_bytes(b'different take')
        with self.assertRaisesRegex(ValueError, 'Audio changed'): app.validate()
        # A checked replacement SRT can repair a stale binding.
        app.add_lyrics(args)
        app.validate()

    def test_archived_videos_stay_out_of_players_and_new_uploads_are_audio(self):
        items = app.records()
        video = next(x for x in items if x['kind']=='video' and x.get('archived'))
        self.assertTrue(video['archived'])
        (self.root/video['repo_path']).write_bytes(b'ARCHIVE VIDEO')
        app.build(True)
        self.assertFalse((self.root/'site'/f'recording--{video["id"]}.html').exists())
        source = self.root/'new.wav'; source.write_bytes(b'master')
        with self.assertRaisesRegex(ValueError, 'Expected one of'):
            app.add_media(Namespace(language='hindi',id='new-take',kind='audio',title='Test',file=str(source),url=None))

    def test_wiki_export_links_to_listening_site(self):
        config = json.loads((self.root/'site-config.json').read_text())
        config['site_url']='https://example.org/world-is-one'
        (self.root/'site-config.json').write_text(json.dumps(config))
        app.export_wiki()
        body = (self.root/'wiki-export/poems--i-am-free-to-dream--languages--tamil.md').read_text()
        self.assertIn('https://example.org/world-is-one/poems--i-am-free-to-dream--languages--tamil.html',body)
        self.assertIn('நான் ஒரு குயவன்.',body)

    def test_published_versions_have_individual_share_pages_and_preview_metadata(self):
        config=json.loads((self.root/'site-config.json').read_text())
        config.update(site_url='https://example.org/poems',repository_url='https://github.com/example/poems')
        (self.root/'site-config.json').write_text(json.dumps(config))
        items=app.records()
        items[0].update(publish=True,public_url='https://media.example.org/odia.mp3',review_status='approved',rights_status='confirmed',allow_file_sharing=True)
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        app.build(False)
        page=(self.root/'site-public/recording--odia-audio-01.html').read_text()
        self.assertIn('property="og:url" content="https://example.org/poems/recording--odia-audio-01.html"',page)
        self.assertIn('data-action="prepare-file"',page)
        self.assertIn('facebook.com/sharer/sharer.php',page)
        self.assertIn('Generated using Suno AI',page)
        self.assertFalse((self.root/'site-public/recording--tamil-audio-01.html').exists())
        contribution=(self.root/'site-public/contribute.html').read_text()
        self.assertIn('data-repository="https://github.com/example/poems"',contribution)
        self.assertIn('Nothing is uploaded from this form.',contribution)

    def test_review_copies_have_no_public_share_link(self):
        item=app.records()[0]
        controls=app.share_controls('Review','recording--test.html',{'site_url':'https://example.org'},True,item,'media/review.mp3')
        self.assertIn('data-share-url=""',controls)
        self.assertIn('data-action="share-link" disabled',controls)
        self.assertNotIn('data-action="prepare-file"',controls)

    def test_all_existing_languages_embed_remote_audio_and_video_with_honest_labels(self):
        shutil.copy2(PROJECT/'catalog/recordings.json', self.root/'catalog/recordings.json')
        app.build(False)
        output = self.root/'site-public'
        expected = {'odia':(3,8), 'sambalpuri':(2,2), 'tamil':(2,2), 'telugu':(4,4), 'english':(2,2), 'filipino':(1,1), 'malayalam':(1,1), 'italian':(1,1), 'bengali':(1,1), 'bhojpuri':(2,2)}
        for language, (audio_count, video_count) in expected.items():
            page=(output/f'poems--i-am-free-to-dream--languages--{language}.html').read_text()
            self.assertEqual(page.count('<audio '), audio_count+2)
            self.assertIn('Slideshow with this song', page)
            self.assertIn('data-slideshow-mode="language"', page)
            self.assertEqual(page.count('id="index-player"'),1)
            self.assertNotIn('id="index-auto"',page)
            self.assertIn('id="index-stop"',page)
            self.assertEqual(page.count('<video '), video_count)
            self.assertIn('Working recordings', page)
            self.assertNotIn('LOCAL REVIEW COPY', page)
            self.assertNotIn('autoplay', page)
            self.assertEqual(page.count('preload="none"'), audio_count+video_count+2)
            self.assertIn('https://media.githubusercontent.com/media/', page)
            for item in (x for x in app.records() if x['language']==language):
                detail=(output/f'recording--{item["id"]}.html').read_text()
                self.assertIn(f'data-share-url="https://kabitawithoutborders.org/recording--{item["id"]}.html"', detail)
                self.assertNotIn('PUBLISHED VERSION', detail)
                self.assertNotIn('data-action="prepare-file"', detail)
        for language, variation in (('tamil', 'duet'), ('odia', 'playful')):
            page=(output/f'poems--i-am-free-to-dream--languages--{language}.html').read_text()
            for section in ('listen', 'watch'):
                self.assertLess(page.index(f'id="{section}-solo"'), page.index(f'id="{section}-{variation}"'))
        bhojpuri=(output/'poems--i-am-free-to-dream--languages--bhojpuri.html').read_text()
        for section in ('listen', 'watch'):
            self.assertLess(bhojpuri.index(f'id="{section}-duet"'), bhojpuri.index(f'id="{section}-playful"'))
        sambalpuri=(output/'poems--i-am-free-to-dream--languages--sambalpuri.html').read_text()
        for section in ('listen', 'watch'):
            self.assertLess(sambalpuri.index(f'id="{section}-duet"'), sambalpuri.index(f'id="{section}-playful"'))
        odia=(output/'poems--i-am-free-to-dream--languages--odia.html').read_text()
        self.assertNotIn('id="listen-duet"', odia)
        self.assertNotIn('id="watch-duet"', odia)
        self.assertIn('recording--odia-duet-audio-01.html', odia)
        tracks=json.loads((output/'assets/listening.json').read_text())
        track_ids={track['id'] for track in tracks if not track.get('archived')}
        self.assertTrue({'odia-playful-audio-01', 'sambalpuri-playful-audio-01'} <= track_ids)
        self.assertNotIn('odia-duet-audio-01', track_ids)
        telugu=(output/'poems--i-am-free-to-dream--languages--telugu.html').read_text()
        self.assertIn('Earlier video versions (3)', telugu)
        hindi=(output/'poems--i-am-free-to-dream--languages--hindi.html').read_text()
        self.assertIn('This language is waiting for its first recording.',hindi)
        self.assertNotIn('aria-label="Watch"',hindi)
        self.assertNotIn('A video is still to come.',hindi)
        self.assertNotIn('<video ', hindi)
        self.assertFalse((output/'media/recordings').exists())

    def test_public_preview_requires_explicit_authorization_without_faking_approval(self):
        items=app.records()
        item=items[0]
        item.update(public_preview=True, public_url='https://example.org/draft.mp3')
        item.pop('preview_authorization', None)
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        with self.assertRaisesRegex(ValueError, 'authorization'): app.validate()
        item['preview_authorization']='Author requested public preview'
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        app.validate()
        self.assertEqual(item['review_status'],'needs-review')
        self.assertEqual(item['rights_status'],'release-details-to-confirm')
        item['publish']=True
        (self.root/'catalog/recordings.json').write_text(json.dumps(items))
        with self.assertRaisesRegex(ValueError, 'approved review'): app.validate()

    def test_reading_pages_are_quiet_and_odia_is_the_original(self):
        shutil.copy2(PROJECT/'catalog/recordings.json', self.root/'catalog/recordings.json')
        app.build(False)
        output=self.root/'site-public'
        for meta in app.validate():
            page=(output/f'poems--i-am-free-to-dream--languages--{meta["slug"]}.html').read_text()
            self.assertEqual(page.count('<h1'),1)
            self.assertNotIn('Shared collection cover · PNG',page)
            self.assertNotIn('class="audio-cover"',page)
            self.assertNotIn('Timed lyrics are not available',page)
            self.assertIn('class="page-share"',page)
            self.assertIn('assets/brand/mark.svg',page)
            self.assertNotIn('<details open',page)
            for target in ['poem-text','listen','watch']:
                self.assertIn(f'id="{target}"',page)
            header = re.search(r'<section class="language-heading">(.*?)</section>', page, re.S)[1]
            self.assertIn('A poem by Ahimanikya Satapathy</p>', header)
            self.assertIn('<summary>Share</summary>', header)
            self.assertNotIn('Adaptation · review welcome', header)
            self.assertNotIn('Read the original poem', header)
            self.assertNotIn('href="#poem-text"', header)
            reading=re.search(r'<article id="poem-text".*?</article>',page,re.S)[0]
            self.assertNotRegex(unescape(reading),r'(?m)^\s*\[[^\]\n]+\]\s*$')
            choices=re.search(r'<details id="musical-choices">(.*?)</details>',page,re.S)
            self.assertIsNotNone(choices, meta['slug'])
            self.assertIn('Arrangement decisions and review', choices[1])
            self.assertIn(f'contribute.html?language={meta["slug"]}&amp;type=culture', choices[1])
            self.assertNotIn('Arrangement decisions and review', reading)
            self.assertEqual(page.count('id="musical-choices"'), 1)
            _, body=app.read_concept(app.LANGUAGES/(meta['slug']+'.md'))
            section=re.search(r'## Poem / arranged lyrics\n(.*?)(?=\n## |\Z)',body,re.S)
            prompt=re.search(r'```(?:text)?\n(.*?)\n```',section[1],re.S) if section else None
            if prompt:
                copied=re.search(r'<textarea id="lyrics-prompt-text"[^>]*>(.*?)</textarea>',page,re.S)
                self.assertEqual(unescape(copied[1]),prompt[1])
                if meta['slug']!='odia':
                    displayed=re.search(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>',reading,re.S)[1]
                    expected=re.sub(r'(?m)^[ \t]*\[[^\]\n]+\][ \t]*\n?', '',prompt[1])
                    self.assertEqual(unescape(displayed).strip(),expected.strip())
            else:
                self.assertNotIn('id="copy-lyrics-prompt"',page)
        odia=(output/'poems--i-am-free-to-dream--languages--odia.html').read_text()
        self.assertNotIn('Odia · the original',odia)
        self.assertIn('Song arrangement',odia)
        self.assertNotIn('How to validate this translation',odia)
        self.assertNotIn('Translation &amp; collaboration',odia)
        self.assertNotIn('needs native review',odia)
        self.assertIn('<summary>Lyrics with song sections</summary>',odia)
        _, original=app.read_concept(app.KB/'poems/i-am-free-to-dream/original.md')
        source=original.split('```text\n')[1].split('\n```')[0]
        reading = odia.split('id="poem-text"')[1].split('</article>')[0]
        self.assertIn('ସାଉଁଟି... ସାଉଁଟି...', reading)
        self.assertEqual(reading.count('ଧୃବତାରା ଖୋଜିଦେବ ରାସ୍ତା'), 2)
        self.assertEqual(reading.count('ତୁମ ସପ୍ନକୁ ମୋ ସପ୍ନରେ'), 2)
        self.assertNotIn('[Chorus]', reading)
        alias=(output/'poems--i-am-free-to-dream--original.html').read_text()
        self.assertIn(source,alias)
        self.assertIn('THE ORIGINAL POEM · ODIA',alias)
        self.assertIn('https://kabitaprusta.blogspot.com/',alias)
        self.assertIn('Original poem © Ahimanikya Satapathy',alias)
        self.assertNotIn('Lyrics with song sections',alias)
        self.assertNotIn('data-language="odia"',alias)
        self.assertNotIn('How to validate this translation',alias)
        tamil=(output/'poems--i-am-free-to-dream--languages--tamil.html').read_text()
        self.assertIn('<summary>Translation &amp; collaboration</summary>',tamil)
        self.assertIn('How to validate this translation',tamil)
        self.assertIn('நான் ஒரு குயவன்.',tamil)
        for heading in ['Style prompt','Cultural grounding','Working settings and listening checks']:
            self.assertIn(heading,tamil)

    def test_index_cards_and_timing_data_only_offer_available_audio(self):
        app.build(False)
        self.assertEqual(json.loads((self.root/'site-public/assets/listening.json').read_text()), [])
        page=(self.root/'site-public/index.html').read_text()
        self.assertNotIn('data-play-recording=',page)
        shutil.copy2(PROJECT/'catalog/recordings.json',self.root/'catalog/recordings.json')
        app.build(False)
        page=(self.root/'site-public/index.html').read_text()
        audio = [x for x in app.records() if x['kind'] == 'audio' and (x.get('public_preview') or x.get('publish'))]
        playing_languages = {x['language'] for x in audio if not x.get('archived')}
        self.assertEqual(page.count('data-play-recording='),len(playing_languages))
        self.assertEqual(page.count('<article class="language-card"'),len(app.validate()))
        self.assertIn('id="story"',page)
        self.assertIn('Ahimanikya Satapathy</h3>',page)
        self.assertIn('https://kabitaprusta.blogspot.com/',page)
        self.assertIn('id="carousel-status"',page)
        self.assertIn('https://www.linkedin.com/in/ahimanikya/',page)
        self.assertIn('https://www.instagram.com/ahimanikya/',page)
        self.assertNotIn('id="search"',page)
        self.assertIn('data-home-art',page)
        self.assertIn('media/ai-artworks/the-witness-refined-print-v2.png',page)
        self.assertNotIn('Artwork by Ahimanikya Satapathy · 1993',page)
        directory=(self.root/'site-public/languages.html').read_text()
        self.assertEqual(directory.count('<article class="language-card"'),len(app.validate()))
        self.assertEqual(directory.count('data-play-recording='),len(playing_languages))
        self.assertIn('id="search"',directory)
        self.assertIn('id="index-player"',directory)
        self.assertIn('href="languages.html"',(self.root/'site-public/timing.html').read_text())
        self.assertNotIn('<a class="language-card"',page)
        self.assertIn('data-play-recording="english-audio-country"',page)
        self.assertIn('Contemporary Nashville country-folk',page)
        self.assertIn('2 audio · 2 video',page)
        self.assertIn('Odia original',page)
        self.assertIn('id="index-player"',page)
        tracks=json.loads((self.root/'site-public/assets/listening.json').read_text())
        self.assertEqual({x['id'] for x in tracks},{x['id'] for x in audio})
        malayalam = next(x for x in tracks if x['id'] == 'malayalam-audio-01')
        self.assertEqual(malayalam['duration_seconds'],162.52)
        malayalam_page = (self.root/'site-public/poems--i-am-free-to-dream--languages--malayalam.html').read_text()
        self.assertIn('<audio',malayalam_page)
        self.assertIn('<video',malayalam_page)
        filipino = next(x for x in tracks if x['language'] == 'filipino')
        self.assertIn("Ako'y magpapalayok.", filipino['draft'])
        self.assertIn('Dahan-dahan kong ihahabi', filipino['draft'])
        filipino_page = (self.root/'site-public/poems--i-am-free-to-dream--languages--filipino.html').read_text()
        self.assertIn('Malaya akong mangarap', filipino_page)
        self.assertIn('id="copy-lyrics-prompt"', filipino_page)
        self.assertIn('<audio', filipino_page)
        self.assertIn('<video', filipino_page)
        self.assertNotIn('Transcription pending', filipino_page)
        self.assertTrue(all(x['duration_seconds'] > 0 for x in tracks))
        odia=next(x for x in tracks if x['id']=='odia-audio-01')
        self.assertIn('ସାଉଁଟି',odia['draft'])
        self.assertEqual(odia['title'],'ମୋତେ ସପ୍ନ ଦେଖିବାକୁ ମନା ନାହିଁ')
        for html in (self.root/'site-public').glob('*.html'):
            self.assertNotIn('Odia · imported recording',html.read_text())
            self.assertNotIn('Odia · original Melodicpal video',html.read_text())
        self.assertIsNone(odia['srt_url'])
        editor=(self.root/'site-public/timing.html').read_text()
        self.assertIn('No timestamps are estimated automatically',editor)
        self.assertIn('Download SRT',editor)
        self.assertNotIn('local-assets/',editor)

    def test_media_server_supports_byte_ranges(self):
        (self.root/'sample.mp3').write_bytes(bytes(range(256)))
        server=app.ThreadingHTTPServer(('127.0.0.1',0),partial(app.MediaHandler,directory=str(self.root)))
        worker=threading.Thread(target=server.serve_forever,daemon=True); worker.start()
        try:
            req=Request(f'http://127.0.0.1:{server.server_port}/sample.mp3',headers={'Range':'bytes=10-19'})
            with urlopen(req) as response:
                self.assertEqual(response.status,206)
                self.assertEqual(response.headers['Content-Range'],'bytes 10-19/256')
                self.assertEqual(response.read(),bytes(range(10,20)))
        finally:
            server.shutdown(); server.server_close(); worker.join()


if __name__ == '__main__': unittest.main()
