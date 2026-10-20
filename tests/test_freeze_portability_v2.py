"""Real temporary-Git integration tests for dirt, EOLs and bound feature bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from src.freeze_io_v2 import canonical_bytes, content_hash
from src.run_registry import verify_freeze
from src.write_registry_freeze_v2 import build


class PortableFreezeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.git('init')
        for key, value in [('user.email', 'test@example.invalid'), ('user.name', 'Synthetic fixture'),
                           ('commit.gpgsign', 'false'), ('tag.gpgsign', 'false'), ('core.autocrlf', 'true')]:
            self.git('config', key, value)
        paths = ['configs/registry_v1.json', 'docs/ANALYSIS_REGISTRY.md',
                 'docs/REGISTRY_VALIDATION_RESULTS.json', 'src/stats_utils.py',
                 'src/train_regression.py', 'src/run_registry.py',
                 'features/figshare_features.csv', 'features/figshare_graph_features.csv']
        self.review = 'docs/reviews/review.json'
        for rel in paths:
            self.write(rel, 'synthetic\n')
        self.write(paths[0], json.dumps({'review_file': self.review, 'tests': [], 'freeze_artifacts': paths}) + '\n')
        self.write(paths[2], json.dumps({'acceptance_passed': True}) + '\n')
        self.write('features/v2/subject_meta.csv', 'subject_id,synthetic\nsub-01,1\n')
        self.write('src/feature_builder_v2.py', 'synthetic_feature_source = 1\n')
        items = [{'path': p, 'sha256': content_hash((self.root / p).read_bytes())}
                 for p in ('features/v2/subject_meta.csv', 'src/feature_builder_v2.py')]
        self.write('features/v2/MANIFEST.json', json.dumps({'label_free_feature_tables': [items[0]],
                   'configs': [], 'implementation_sources': [items[1]]}) + '\n')
        self.snapshot = build(self.root)
        self.write('docs/REGISTRY_FREEZE_MANIFEST.json', json.dumps(self.snapshot) + '\n')
        self.write(self.review, json.dumps({'status': 'approved', 'reviewer': 'synthetic test only',
                   'reviewed_at': 'synthetic', 'artifact_digest': self.snapshot['artifact_digest']}) + '\n')
        self.write('src/unlisted_existing.py', 'synthetic_unlisted = 1\n')
        self.git('add', '.')
        self.git('commit', '-m', 'synthetic fixture only')
        self.git('tag', 'registry-v1')
        self.git('tag', 'features-v2')
        self.assertTrue(verify_freeze(self.root))

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')

    def test_crlf_checkout_matches_lf_tag_and_snapshot(self):
        paths = [r['path'] for r in self.snapshot['artifacts']] + [self.review, 'docs/REGISTRY_FREEZE_MANIFEST.json']
        for rel in paths:
            path = self.root / rel
            path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        self.assertTrue(verify_freeze(self.root))
        self.assertEqual(build(self.root), self.snapshot)

    def test_unlisted_unstaged_staged_and_untracked_code_fail(self):
        self.write('src/unlisted_existing.py', 'synthetic_unlisted = 2\n')
        with self.assertRaisesRegex(ValueError, 'Uncommitted'):
            verify_freeze(self.root)
        self.git('add', 'src/unlisted_existing.py')
        with self.assertRaisesRegex(ValueError, 'Uncommitted'):
            verify_freeze(self.root)
        self.write('src/unlisted_existing.py', 'synthetic_unlisted = 1\n')
        self.git('add', 'src/unlisted_existing.py')
        self.write('tests/untracked.py', 'new_fixture = 1\n')
        with self.assertRaisesRegex(ValueError, 'Uncommitted'):
            verify_freeze(self.root)

    def test_content_change_is_not_normalized_away(self):
        self.write('docs/ANALYSIS_REGISTRY.md', 'modified scientific content\r\n')
        with self.assertRaisesRegex(ValueError, 'Registry artifact changed'):
            verify_freeze(self.root)

    def test_tampered_feature_and_approval_fail(self):
        self.write('features/v2/subject_meta.csv', 'tampered\n')
        with self.assertRaisesRegex(ValueError, 'artifact changed'):
            verify_freeze(self.root)
        self.write('features/v2/subject_meta.csv', 'subject_id,synthetic\nsub-01,1\n')
        review = json.loads((self.root / self.review).read_text())
        review['artifact_digest'] = 'wrong'
        self.write(self.review, json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'Review does not approve'):
            verify_freeze(self.root)

    def test_builder_rejects_unproven_feature_change(self):
        self.write('features/v2/subject_meta.csv', 'altered value\n')
        with self.assertRaisesRegex(ValueError, 'Group A provenance'):
            build(self.root)


class NormalizationTests(unittest.TestCase):
    def test_only_crlf_is_normalized_and_binary_rejected(self):
        self.assertEqual(canonical_bytes(b'a\r\nb\n', 'utf8-lf'), b'a\nb\n')
        self.assertNotEqual(content_hash(b'a \n', 'utf8-lf'), content_hash(b'a\n', 'utf8-lf'))
        self.assertNotEqual(content_hash(b'a\r', 'utf8-lf'), content_hash(b'a\n', 'utf8-lf'))
        with self.assertRaises(ValueError):
            canonical_bytes(b'a\x00b', 'utf8-lf')
        with self.assertRaises(ValueError):
            canonical_bytes(b'\xff', 'utf8-lf')


if __name__ == '__main__':
    unittest.main()
