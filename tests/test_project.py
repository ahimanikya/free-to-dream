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
            shutil.copytree(PROJECT/folder, self.root/folder)
        shutil.copy2(PROJECT/'site-config.json', self.root/'site-config.json')
        self.overrides = patch.multiple(app, ROOT=self.root, KB=self.root/'kb', LANGUAGES=self.root/'kb/poems/i-am-free-to-dream/languages')
        self.overrides.start()

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
        self.assertEqual((self.root/item['local_path']).read_bytes(), source.read_bytes())
        with self.assertRaisesRegex(ValueError, 'already exists'): app.add_media(args)
        with self.assertRaises(ValueError): app.confined('../private.txt')

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
