from argparse import Namespace
from functools import partial
from html.parser import HTMLParser
import importlib.util
import json
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
        for folder in ('kb','catalog','web','media'):
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
            self.assertNotIn('<audio ', text)
            links = Links(); links.feed(text)
            for target in links.targets:
                url = urlparse(target)
                if not url.scheme and url.path:
                    self.assertTrue((page.parent/unquote(url.path)).is_file(), f'{page.name}: missing {target}')

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
        expected = {'odia':(1,6), 'tamil':(1,1), 'telugu':(4,4), 'english':(2,2), 'filipino':(1,1)}
        for language, (audio_count, video_count) in expected.items():
            page=(output/f'poems--i-am-free-to-dream--languages--{language}.html').read_text()
            self.assertEqual(page.count('<audio '), audio_count)
            self.assertEqual(page.count('<video '), video_count)
            self.assertIn('Review copy', page)
            self.assertNotIn('LOCAL REVIEW COPY', page)
            self.assertNotIn('autoplay', page)
            self.assertEqual(page.count('preload="none"'), audio_count+video_count)
            self.assertIn('https://media.githubusercontent.com/media/', page)
            for item in (x for x in app.records() if x['language']==language):
                detail=(output/f'recording--{item["id"]}.html').read_text()
                self.assertIn(f'data-share-url="https://ahimanikya.github.io/free-to-dream/recording--{item["id"]}.html"', detail)
                self.assertNotIn('PUBLISHED VERSION', detail)
                self.assertNotIn('data-action="prepare-file"', detail)
        telugu=(output/'poems--i-am-free-to-dream--languages--telugu.html').read_text()
        self.assertIn('Earlier video versions (3)', telugu)
        hindi=(output/'poems--i-am-free-to-dream--languages--hindi.html').read_text()
        self.assertIn('No audio recording is available',hindi)
        self.assertIn('No video recording is available',hindi)
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
