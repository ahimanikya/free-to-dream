"""Behavior checks for resuming production from a clean checkout."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_queue', ROOT / 'skills/poetry-to-music/scripts/prepare_queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class ProductionPortabilityTests(unittest.TestCase):
    def test_ready_packet_retains_exact_lyrics_and_prevents_overwrite(self):
        report = queue.prepare(ROOT, 'i-am-free-to-dream', {'hindi'}, True)
        entry = report['entries'][0]
        self.assertEqual(entry['status'], 'prepared')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run'
            queue.export(report, out)
            self.assertEqual((out / 'hindi/lyrics.txt').read_text(), entry['lyrics'] + '\n')
            self.assertEqual(json.loads((out / 'queue.json').read_text())['entries'][0]['source_sha256'], entry['source_sha256'])
            with self.assertRaises(FileExistsError):
                queue.export(report, out)

    def test_pending_translation_does_not_export_a_song_packet(self):
        report = queue.prepare(ROOT, 'i-am-free-to-dream')
        pending = next(x for x in report['entries'] if x['status'] == 'lyrics-pending')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run'
            queue.export(dict(report, entries=[pending]), out)
            self.assertFalse((out / pending['language']).exists())
            self.assertEqual(pending['lyrics'], '')
