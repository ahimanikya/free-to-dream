import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_music_queue', ROOT / 'skills/poetry-to-music/scripts/prepare_queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class MusicSettingsTests(unittest.TestCase):
    def test_packets_share_controls_without_changing_language_text(self):
        report = queue.prepare(ROOT, 'i-am-free-to-dream', {'tamil', 'bengali', 'sambalpuri', 'english'}, True)
        policy = report['settings_policy']
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'packets'
            queue.export(report, out)
            for entry in report['entries']:
                _, body = queue.concept(ROOT / entry['source'])
                self.assertEqual(entry['lyrics'], queue.fenced(body, 'Poem / arranged lyrics'))
                self.assertEqual(entry['style'], queue.fenced(body, 'Style prompt'))
                packet = json.loads((out / entry['language'] / 'settings.json').read_text())
                self.assertEqual(packet['settings'], policy['defaults'])
                self.assertEqual(packet['policy_sha256'], policy['source_sha256'])
                self.assertIsNone(packet['settings']['audio_influence'])
                self.assertEqual(packet['reference_cover_overrides'], policy['reference_cover_overrides'])
                self.assertIsNone(entry['selected_candidate'])

    def test_missing_or_incomplete_policy_cannot_silently_inherit_ui_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                queue.settings_policy(root, 'i-am-free-to-dream')
            path = root / 'production/i-am-free-to-dream/settings.json'
            path.parent.mkdir(parents=True)
            policy = json.loads((ROOT / path.relative_to(root)).read_text())
            del policy['defaults']['max_mode']
            path.write_text(json.dumps(policy))
            with self.assertRaises(ValueError):
                queue.settings_policy(root, 'i-am-free-to-dream')
            policy['defaults']['max_mode'] = 'Off'
            path.write_text(json.dumps(policy))
            with self.assertRaises(ValueError):
                queue.settings_policy(root, 'i-am-free-to-dream')

    def test_unrelated_poem_does_not_inherit_this_poems_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(queue.settings_policy(Path(tmp), 'another-poem'))


if __name__ == '__main__':
    unittest.main()
