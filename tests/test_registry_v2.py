"""Synthetic tests of registry statistics, nested fitting, subsets and freeze guards."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import GridSearchCV, KFold, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

from src.stats_utils import holm_adjust, perm_pvalue, pooled_oof_spearman, bootstrap_ci, minimum_detectable_rho
from src.train_regression import fit_ridge, cross_validated_predictions, evaluate, load_analysis
from src.run_registry import verify_freeze, sha256, run

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / 'configs/registry_v1.json').read_text())['settings']


class StatisticsTests(unittest.TestCase):
    def test_holm_hand_example_and_cap(self):
        np.testing.assert_allclose(holm_adjust([0.01, 0.04, 0.03, 0.8]), [0.04, 0.09, 0.09, 0.8])
        np.testing.assert_equal(holm_adjust([0.9, 0.8, 1]), [1, 1, 1])
        self.assertTrue((np.diff(np.sort(holm_adjust([0.02, 0.01, 0.3]))) >= 0).all())
        with self.assertRaises(ValueError):
            holm_adjust([np.nan])

    def test_permutation_ties_tails_and_floor(self):
        self.assertEqual(perm_pvalue(2, [0, 1, 1]), 0.25)
        self.assertEqual(perm_pvalue(1, [1, 1, 0]), 0.75)
        self.assertEqual(perm_pvalue(-2, [-3, 0, 3], 'two-sided'), 0.75)

    def test_spearman_pooled_ties(self):
        y = np.array([1, 2, 2, 4, 5])
        pred = np.array([[2, 1], [3, 3], [1, 3], [5, 4], [4, 2]])
        expected = np.mean([spearmanr(y, pred[:, r]).statistic for r in range(2)])
        self.assertAlmostEqual(pooled_oof_spearman(y, pred), expected)
        with self.assertRaises(ValueError):
            pooled_oof_spearman(y, np.ones((5, 2)))

    def test_bootstrap_and_invalid_policy(self):
        y = np.arange(50.)
        ci = bootstrap_ci(y, y, n_resamples=100, seed=1)
        self.assertTrue(ci['available'])
        self.assertAlmostEqual(ci['low'], 1)
        unavailable = bootstrap_ci(y, np.ones(50), n_resamples=10)
        self.assertFalse(unavailable['available'])
        self.assertEqual(unavailable['invalid'], 10)
        self.assertIsNone(unavailable['low'])

    def test_fisher_power(self):
        self.assertAlmostEqual(minimum_detectable_rho(50), 0.39, delta=0.02)
        self.assertGreater(minimum_detectable_rho(50, 0.05 / 9), minimum_detectable_rho(50))


class RegressionTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(123)
        self.X = rng.normal(size=(30, 7)) * np.geomspace(0.01, 100, 7)
        self.y = self.X[:, 2] + rng.normal(size=30)
        self.classes = (self.y > np.median(self.y)).astype(int)
        self.settings = {**SETTINGS, 'outer_splits': 3, 'outer_repeats': 2, 'inner_splits': 3,
                         'alphas': [0.01, 1, 100], 'permutations': 3, 'bootstrap_resamples': 30}

    def test_optimized_alpha_search_matches_full_pipeline_grid(self):
        model, alpha = fit_ridge(self.X, self.y, self.settings)
        reference = GridSearchCV(Pipeline([('scale', StandardScaler()), ('ridge', Ridge(solver='svd'))]),
            {'ridge__alpha': self.settings['alphas']},
            cv=KFold(3, shuffle=True, random_state=42), scoring='neg_mean_squared_error').fit(self.X, self.y)
        self.assertEqual(alpha, reference.best_params_['ridge__alpha'])
        np.testing.assert_allclose(model.predict(self.X), reference.predict(self.X), atol=1e-10)

    def test_outer_fold_isolation(self):
        result = cross_validated_predictions(self.X, self.y, self.classes, self.settings)
        train, valid = next(RepeatedStratifiedKFold(n_splits=3, n_repeats=2, random_state=42).split(self.X, self.classes))
        model, _ = fit_ridge(self.X[train], self.y[train], self.settings)
        np.testing.assert_allclose(result['predictions'][valid, 0], model.predict(self.X[valid]))
        np.testing.assert_allclose(model['scale'].mean_, self.X[train].mean(axis=0))
        self.assertTrue((result['folds'] >= 0).all())

    def test_joint_permutation_recreates_splits_and_refits(self):
        result = evaluate(self.X, self.y, self.classes, self.settings, 1)
        permutation = np.random.default_rng(self.settings['permutation_seed_base'] + 1).permutation(len(self.y))
        expected = cross_validated_predictions(self.X, self.y[permutation], self.classes[permutation], self.settings)
        self.assertAlmostEqual(result['null'][0], expected['rho'])
        wrong = cross_validated_predictions(self.X, self.y[permutation], self.classes, self.settings)
        self.assertFalse(np.array_equal(expected['folds'], wrong['folds']))

    def test_subset_whitelist_shuffle_and_failures(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'features/v2').mkdir(parents=True)
            ids = [f's-{i}' for i in range(12)]
            pd.DataFrame({'subject_id': ids, 'value': np.arange(12), 'nihss_raw': 999}).to_csv(root / 'features.csv', index=False)
            pd.DataFrame({'subject_id': ids + ['extra'], 'nihss_raw': [1]*6 + [6]*7,
                          'severity_class': ['mild']*6 + ['moderate']*7}).to_csv(root / 'features/v2/subject_meta.csv', index=False)
            spec = {'table': 'features.csv', 'features': ['value'], 'expected_n': 12, 'subject_ids': ids}
            X, y, c, actual, _ = load_analysis(root, spec, shuffle_seed=4)
            self.assertEqual(X.shape, (12, 1))
            np.testing.assert_equal(c, (y >= 5).astype(int))
            with self.assertRaises(ValueError):
                load_analysis(root, {**spec, 'features': ['nihss_raw']})
            with self.assertRaises(ValueError):
                load_analysis(root, {**spec, 'subject_ids': ids[:-1]})


class FreezeGuardTests(unittest.TestCase):
    def test_incomplete_family_withholds_decisions_and_exports_no_models(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'docs').mkdir()
            (root / 'docs/PROGRESS.md').write_text('synthetic')
            (root / 'docs/ANALYSIS_REGISTRY.md').write_text('synthetic')
            (root / 'configs').mkdir()
            (root / 'features/v2').mkdir(parents=True)
            (root / 'features/v2/subject_meta.csv').write_text('synthetic')
            (root / 'features/input.csv').write_text('synthetic')
            config = {'settings': SETTINGS, 'tests': [
                {'id': f'T{i}', 'kind': 'ridge' if i < 7 else 'association', 'table': 'features/input.csv'}
                for i in range(1, 10)]}
            (root / 'configs/registry_v1.json').write_text(json.dumps(config))
            fake = {'summary': {'rho': 0.9, 'p_raw': 0.001}, 'null': np.zeros(3),
                    'bootstrap': np.ones(3), 'output': None, 'repeat_metrics': []}
            outcomes = [copy.deepcopy(fake) for _ in range(8)] + [ValueError('synthetic failure')]
            with patch('src.run_registry.verify_freeze', return_value={}), \
                 patch('src.run_registry.subprocess.check_output', return_value='synthetic'), \
                 patch('src.run_registry.load_analysis', return_value=(np.ones((10, 1)), np.arange(10), np.r_[np.zeros(5),np.ones(5)], ['id']*10, ['feature'])), \
                 patch('src.run_registry.evaluate', side_effect=outcomes):
                with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                    run('real', 'fixture', root=root)
            table = pd.read_csv(root / 'results/v2/runs/fixture/registry_results.csv')
            self.assertEqual(len(table), 9)
            self.assertEqual(set(table.decision), {'withheld_incomplete_family'})
            self.assertFalse((root / 'results/v2/models').exists())

    def test_missing_tags_and_modified_frozen_artifacts(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)
            git('init')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'Synthetic test')
            git('config', 'commit.gpgsign', 'false')
            git('config', 'tag.gpgsign', 'false')
            git('config', 'core.autocrlf', 'false')
            with self.assertRaises(subprocess.CalledProcessError):
                verify_freeze(root)
            paths = ['configs/registry_v1.json', 'docs/ANALYSIS_REGISTRY.md', 'docs/REGISTRY_VALIDATION_RESULTS.json', 'src/stats_utils.py',
                     'src/train_regression.py', 'src/run_registry.py', 'features/figshare_features.csv',
                     'features/figshare_graph_features.csv']
            review = 'docs/reviews/review.json'
            for rel in paths:
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text('{}')
            (root / paths[0]).write_text(json.dumps({'review_file': review, 'tests': []}))
            (root / 'docs/REGISTRY_VALIDATION_RESULTS.json').write_text(json.dumps({'acceptance_passed': True}))
            artifacts = [{'path': p, 'sha256': sha256(root / p)} for p in paths]
            digest = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()
            (root / 'docs/REGISTRY_FREEZE_MANIFEST.json').write_text(json.dumps({'artifacts': artifacts}))
            (root / review).parent.mkdir(exist_ok=True)
            (root / review).write_text(json.dumps({'status': 'approved', 'reviewer': 'synthetic',
                'reviewed_at': 'synthetic', 'artifact_digest': digest}))
            (root / 'features/v2').mkdir()
            (root / 'features/v2/subject_meta.csv').write_text('synthetic')
            manifest = {'label_free_feature_tables': [{'path': 'features/v2/subject_meta.csv',
                         'sha256': sha256(root / 'features/v2/subject_meta.csv')}], 'configs': [], 'implementation_sources': []}
            (root / 'features/v2/MANIFEST.json').write_text(json.dumps(manifest))
            git('add', '.')
            git('commit', '-m', 'synthetic fixture')
            git('tag', 'registry-v1')
            git('tag', 'features-v2')
            self.assertTrue(verify_freeze(root))
            (root / 'src/stats_utils.py').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'artifact changed'):
                verify_freeze(root)
            (root / 'src/stats_utils.py').write_text('{}')
            (root / 'features/v2/subject_meta.csv').write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'Feature artifact changed'):
                verify_freeze(root)
            (root / 'features/v2/subject_meta.csv').write_text('synthetic')
            (root / review).write_text(json.dumps({'status': 'pending'}))
            with self.assertRaises(ValueError):
                verify_freeze(root)


if __name__ == '__main__':
    unittest.main()
