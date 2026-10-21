"""Synthetic interrupted-run equivalence and corruption tests."""
import copy
import json
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import scipy
import sklearn

from src import continue_registry_v2 as continuation
from src import run_registry as registry
from src.train_regression import evaluate, load_analysis

ROOT = Path(__file__).resolve().parents[1]


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("configs", "docs", "features/v2", "results/v2/runs/old"):
            (self.root / folder).mkdir(parents=True)
        settings = json.loads((ROOT / "configs/registry_v1.json").read_text())["settings"]
        settings.update(outer_splits=2, outer_repeats=2, inner_splits=2,
                        alphas=[.01, 1, 100], permutations=3, bootstrap_resamples=20)
        rng = np.random.default_rng(8210)
        X = rng.normal(size=(20, 3))
        y = np.r_[np.tile([1., 2., 3., 4.], 3)[:12], np.tile([5., 6., 7., 8.], 2)]
        ids = [f"sub-{i:02}" for i in range(1,21)]
        meta = pd.DataFrame({"subject_id": ids, "nihss_raw": y,
                             "severity_class": np.where(y < 5, "mild", "moderate")})
        meta.to_csv(self.root / "features/v2/subject_meta.csv", index=False)
        source = pd.DataFrame(X, columns=["a", "b", "c"])
        source.insert(0, "subject_id", ids)
        source.to_csv(self.root / "features/input.csv", index=False)
        self.config = {"settings": settings, "tests": [
            {"id": f"T{i}", "kind": "ridge" if i < 7 else "association",
             "table": "features/input.csv", "features": ["a", "b", "c"] if i < 7 else ["a"],
             "expected_n": 20, "subject_ids": ids} for i in range(1,10)]}
        (self.root / registry.CONFIG).write_text(json.dumps(self.config))
        (self.root / "docs/ANALYSIS_REGISTRY.md").write_text("synthetic")
        self.old = self.root / "results/v2/runs/old"
        metadata = {"mode": "real", "status": "running", "settings": settings,
                    "python": platform.python_version(), "numpy": np.__version__,
                    "scipy": scipy.__version__, "sklearn": sklearn.__version__,
                    "source_commit": "synthetic", "config_sha256": registry.sha256(self.root / registry.CONFIG),
                    "registry_sha256": registry.sha256(self.root / "docs/ANALYSIS_REGISTRY.md"),
                    "input_hashes": {p:registry.sha256(self.root / p) for p in
                                     ("features/input.csv", "features/v2/subject_meta.csv")}}
        (self.old / "run.json").write_text(json.dumps(metadata))
        spec = self.config["tests"][0]
        data = load_analysis(self.root, spec)
        result = evaluate(*data[:3], settings, 1, spec["kind"])
        registry.save_test(self.old / "T1", result, *data[3:], settings)

    def prepare(self):
        with patch.object(continuation.subprocess, "check_output", return_value="synthetic\n"):
            return continuation.prepare_cache(self.root, "old", self.config)

    def test_saved_test_is_complete_and_has_same_observed_statistics(self):
        previous, cache = self.prepare()
        self.assertEqual(previous, self.old)
        self.assertEqual(list(cache), [1])
        original = json.loads((self.old / "T1/summary.json").read_text())
        self.assertEqual(cache[1][2]["summary"], original)

    def test_continuation_equals_uninterrupted_family_and_preserves_bytes(self):
        before = {p:p.read_bytes() for p in self.old.rglob("*") if p.is_file()}
        with patch.object(registry, "verify_freeze", return_value={}), \
                patch.object(continuation.subprocess, "check_output", return_value="synthetic\n"):
            reference = registry.run("real", "reference", root=self.root, rerun_reason="synthetic reference")
            with patch.object(registry, "evaluate", wraps=evaluate) as compute:
                result = continuation.continue_run("old", "continued", "synthetic interruption", self.root)
                self.assertEqual([call.args[4] for call in compute.call_args_list], list(range(2,10)))
        pd.testing.assert_frame_equal(pd.read_csv(reference / "registry_results.csv"),
                                      pd.read_csv(result / "registry_results.csv"))
        for spec in self.config["tests"]:
            for filename in ("summary.json", "null.npy", "bootstrap.npy"):
                self.assertEqual((reference / spec["id"] / filename).read_bytes(),
                                 (result / spec["id"] / filename).read_bytes())
        self.assertTrue(all(p.read_bytes() == value for p,value in before.items()))
        for p in (self.old / "T1").iterdir():
            self.assertEqual(p.read_bytes(), (result / "T1" / p.name).read_bytes())
        provenance = json.loads((result / "continuation.json").read_text())
        self.assertEqual(provenance["reused_tests"], ["T1"])
        self.assertTrue(provenance["previous_files_unchanged"])

    def test_changed_settings_versions_inputs_and_finished_source_are_rejected(self):
        path = self.old / "run.json"
        original = json.loads(path.read_text())
        for change in ({"status": "complete"}, {"python": "different"},
                       {"source_commit": "different"}, {"config_sha256": "changed"},
                       {"settings": {**original["settings"], "permutations": 99}}):
            path.write_text(json.dumps({**original, **change}))
            with self.assertRaises(ValueError):
                self.prepare()
        path.write_text(json.dumps(original))

    def test_incomplete_null_and_corrupt_folds_are_rejected(self):
        path = self.old / "T1/null.npy"
        original = path.read_bytes()
        np.save(path, np.zeros(2))
        with self.assertRaisesRegex(ValueError, "Incomplete saved permutation"):
            self.prepare()
        path.write_bytes(original)
        frame = pd.read_csv(self.old / "T1/oof.csv")
        frame.loc[0,"fold"] = 99
        frame.to_csv(self.old / "T1/oof.csv", index=False)
        with self.assertRaises(AssertionError):
            self.prepare()

    def test_initial_canonical_hash_accepts_crlf_but_rejects_content_changes(self):
        source = self.root / "features/input.csv"
        canonical = registry.canonical_bytes(source.read_bytes(), "utf8-lf")
        path = self.old / "run.json"
        meta = json.loads(path.read_text())
        meta["input_hashes"]["features/input.csv"] = continuation.hashlib.sha256(canonical).hexdigest()
        path.write_text(json.dumps(meta))
        source.write_bytes(canonical.replace(b"\n", b"\r\n"))
        self.assertEqual(list(self.prepare()[1]), [1])
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "input changed"):
            self.prepare()

    def test_changed_targets_and_incomplete_coverage_are_rejected(self):
        path = self.old / "T1/oof.csv"
        original = pd.read_csv(path)
        changed = original.copy()
        changed.loc[0,"target"] += 1
        changed.to_csv(path,index=False)
        with self.assertRaises(AssertionError):
            self.prepare()
        original.iloc[:-1].to_csv(path,index=False)
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.prepare()

    def test_missing_prefix_and_unsafe_or_existing_destinations_are_rejected(self):
        (self.old / "T3").mkdir()
        with self.assertRaisesRegex(ValueError, "prefix"):
            self.prepare()
        with self.assertRaises(ValueError):
            continuation.continue_run("../old", "new", "reason", self.root)
        with self.assertRaises(FileExistsError):
            continuation.continue_run("old", "old", "reason", self.root)

    def test_adapter_restores_functions_after_execution_failure(self):
        original_evaluate, original_save = registry.evaluate, registry.save_test
        with patch.object(registry, "verify_freeze", return_value={}), \
                patch.object(continuation.subprocess, "check_output", return_value="synthetic\n"), \
                patch.object(registry, "run", side_effect=RuntimeError("synthetic execution failure")):
            with self.assertRaisesRegex(RuntimeError,"synthetic execution failure"):
                continuation.continue_run("old", "failed", "interruption", self.root)
        self.assertIs(registry.evaluate, original_evaluate)
        self.assertIs(registry.save_test, original_save)


if __name__ == "__main__":
    unittest.main()
