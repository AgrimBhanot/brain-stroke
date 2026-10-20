"""Synthetic-only tests for the separately registered descriptive analyses."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src import run_sensitivities_v2 as sensitivity
from src.train_regression import cross_validated_predictions

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "configs/registry_v1.json").read_text())
CONFIG = json.loads((ROOT / "configs/sensitivities_v2.json").read_text())


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(6020)
        self.X = rng.normal(size=(30, 4)) * [0.01, 1, 10, 100]
        self.y = self.X[:, 1] + rng.normal(size=30)
        self.strata = (self.y > np.median(self.y)).astype(int)
        self.ids = [f"sub-{i:02}" for i in range(1, 31)]
        self.settings = {
            **REGISTRY["settings"], "outer_splits": 3, "inner_splits": 3,
            "outer_repeats": 2, "alphas": [0.01, 1, 100],
        }
        self.grouped = {
            **CONFIG["grouped"],
            "pairs": [["sub-04", "sub-05"], ["sub-11", "sub-15"]],
        }

    def test_group_mapping_and_strict_failures(self):
        groups = sensitivity.group_labels(self.ids, self.grouped["pairs"])
        self.assertEqual(len(set(groups)), 28)
        self.assertEqual(groups[3], groups[4])
        self.assertNotEqual(groups[0], groups[1])
        for ids, pairs in (
            (self.ids + ["sub-01"], []),
            (self.ids, [["sub-01", "missing"]]),
            (self.ids, [["sub-01", "sub-01"]]),
            (self.ids, [["sub-01", "sub-02"], ["sub-02", "sub-03"]]),
        ):
            with self.assertRaises(ValueError):
                sensitivity.group_labels(ids, pairs)
        with self.assertRaisesRegex(ValueError, "Too few groups"):
            sensitivity.checked_group_splits(self.X, self.strata, np.zeros(30), 3, 42)

    def test_both_cv_levels_isolate_pairs_and_cover_every_subject(self):
        first = sensitivity.grouped_predictions(
            self.X, self.y, self.strata, self.ids, self.settings, self.grouped)
        second = sensitivity.grouped_predictions(
            self.X, self.y, self.strata, self.ids, self.settings, self.grouped)
        np.testing.assert_array_equal(first["folds"], second["folds"])
        np.testing.assert_array_equal(first["predictions"], second["predictions"])
        self.assertTrue(np.isfinite(first["predictions"]).all())
        self.assertEqual(first["predictions"].shape, (30, 2))
        for r in range(2):
            records = [a for a in first["fold_audit"] if a["repeat"] == r]
            self.assertEqual(sorted(s for a in records for s in a["valid_ids"]), self.ids)
        for outer in first["fold_audit"]:
            for fold in [outer] + outer["inner"]:
                train, valid = set(fold["train_ids"]), set(fold["valid_ids"])
                self.assertFalse(train & valid)
                for pair in self.grouped["pairs"]:
                    self.assertFalse(set(pair) & train and set(pair) & valid)
                self.assertGreater(fold["train_groups"], 0)
                self.assertGreater(fold["valid_groups"], 0)
            self.assertEqual(sorted(s for a in outer["inner"] for s in a["valid_ids"]),
                             sorted(outer["train_ids"]))

    def test_inner_scaling_and_alpha_match_manual_fold_local_search(self):
        groups = sensitivity.group_labels(self.ids, self.grouped["pairs"])
        outer = sensitivity.checked_group_splits(self.X, self.strata, groups, 3, 42)
        train, valid = outer[0]
        X, y = self.X[train], self.y[train]
        seed = self.grouped["inner_seed_base"]
        inner = sensitivity.checked_group_splits(X, self.strata[train], groups[train], 3, seed)
        seen = []
        original_fit = StandardScaler.fit

        def capture(scaler, data, *args, **kwargs):
            seen.append(np.asarray(data).copy())
            return original_fit(scaler, data, *args, **kwargs)

        with patch.object(StandardScaler, "fit", capture):
            model, alpha, _ = sensitivity.fit_grouped_ridge(
                X, y, self.strata[train], groups[train], self.settings, seed, 1)
        allowed = [X[a] for a, _ in inner] + [X]
        self.assertTrue(all(any(np.array_equal(data, option) for option in allowed) for data in seen))
        self.assertEqual(len(seen), len(inner) * len(self.settings["alphas"]) + 1)
        errors = []
        for candidate in self.settings["alphas"]:
            losses = []
            for a, b in inner:
                fitted = Pipeline([
                    ("scale", StandardScaler()), ("ridge", Ridge(alpha=candidate, solver="svd")),
                ]).fit(X[a], y[a])
                losses.append(np.mean((fitted.predict(X[b]) - y[b]) ** 2))
            errors.append(np.mean(losses))
        self.assertEqual(alpha, self.settings["alphas"][int(np.argmin(errors))])
        np.testing.assert_allclose(model["scale"].mean_, X.mean(axis=0))
        output = sensitivity.grouped_predictions(
            self.X, self.y, self.strata, self.ids, self.settings, self.grouped)
        np.testing.assert_allclose(output["predictions"][valid, 0], model.predict(self.X[valid]))
        self.assertEqual(model.n_features_in_, self.X.shape[1])

    def test_alternative_models_use_identical_primary_folds_and_dummy(self):
        primary = cross_validated_predictions(self.X, self.y, self.strata, self.settings)
        for kind, options in (
            ("svr", CONFIG["models"]["svr"]),
            ("random_forest", {**CONFIG["models"]["random_forest"], "n_estimators": 5}),
        ):
            output = sensitivity.alternative_predictions(
                self.X, self.y, self.strata, self.settings, kind, options)
            np.testing.assert_array_equal(primary["folds"], output["folds"])
            np.testing.assert_allclose(primary["dummy"], output["dummy"])
            self.assertTrue(np.isfinite(output["predictions"]).all())
        with self.assertRaisesRegex(ValueError, "Unknown"):
            sensitivity.alternative_predictions(
                self.X, self.y, self.strata, self.settings, "unregistered", {})

    def test_combined_join_is_by_id_not_row_and_rejects_mismatches(self):
        left = (self.X, self.y, self.strata, self.ids, ["a", "b", "c", "d"])
        order = np.arange(29, 0, -1)
        right = (self.X[order, :1], self.y[order], self.strata[order],
                 [self.ids[i] for i in order], ["e"])
        X, y, strata, ids, features = sensitivity.combine_inputs(left, right, 29)
        np.testing.assert_array_equal(X[:, :4], self.X[1:])
        np.testing.assert_array_equal(X[:, 4], self.X[1:, 0])
        np.testing.assert_array_equal(y, self.y[1:])
        np.testing.assert_array_equal(strata, self.strata[1:])
        self.assertEqual(ids, self.ids[1:])
        self.assertEqual(features, ["spectral:a", "spectral:b", "spectral:c", "spectral:d", "graph:e"])
        with self.assertRaisesRegex(ValueError, "membership"):
            sensitivity.combine_inputs(left, right, 30)
        bad = list(right)
        bad[1] = right[1] + 1
        with self.assertRaisesRegex(ValueError, "target/class"):
            sensitivity.combine_inputs(left, bad, 29)
        bad = list(right)
        bad[3] = ["same"] * 29
        with self.assertRaisesRegex(ValueError, "Repeated"):
            sensitivity.combine_inputs(left, bad, 29)

    def test_incomplete_primary_is_rejected_before_labels(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            primary = root / "results/v2/runs/primary"
            primary.mkdir(parents=True)
            sensitivity.write_json(primary / "run.json", {"mode": "real", "status": "running"})
            with patch.object(sensitivity, "verify_freeze", return_value={}), \
                    patch.object(sensitivity, "load_analysis") as loader:
                with self.assertRaisesRegex(ValueError, "completed primary"):
                    sensitivity.run("primary", "sensitivity", root)
                loader.assert_not_called()
            self.assertFalse((root / "results/v2/sensitivities").exists())
        with self.assertRaisesRegex(ValueError, "identifier"):
            sensitivity.run("../primary", "sensitivity")

    def test_synthetic_end_to_end_preserves_primary_and_never_infers(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            registry = copy.deepcopy(REGISTRY)
            registry["settings"] = self.settings
            config = copy.deepcopy(CONFIG)
            config["grouped"] = self.grouped
            config["combined"]["expected_n"] = 30
            config["models"]["random_forest"]["n_estimators"] = 5
            config["primary_artifact_digest"] = "synthetic"
            for rel in ("configs", "docs", "features/v2", "src", "tests"):
                (root / rel).mkdir(parents=True)
            sensitivity.write_json(root / "configs/registry_v1.json", registry)
            sensitivity.write_json(root / sensitivity.CONFIG, config)
            sensitivity.write_json(root / "docs/REGISTRY_FREEZE_MANIFEST.json",
                                   {"artifact_digest": "synthetic"})
            for rel in ("docs/ANALYSIS_REGISTRY.md", "src/run_sensitivities_v2.py",
                        "tests/test_sensitivities_v2.py", "features/v2/subject_meta.csv"):
                (root / rel).write_text("synthetic fixture\n")
            for spec in registry["tests"]:
                (root / spec["table"]).parent.mkdir(parents=True, exist_ok=True)
                (root / spec["table"]).write_text("synthetic fixture\n")
            hashes = {spec["table"]: sensitivity.sha256(root / spec["table"])
                      for spec in registry["tests"]}
            hashes["features/v2/subject_meta.csv"] = sensitivity.sha256(root / "features/v2/subject_meta.csv")
            primary = root / "results/v2/runs/primary"
            primary.mkdir(parents=True)
            sensitivity.write_json(primary / "run.json", {
                "mode": "real", "status": "complete", "settings": self.settings,
                "config_sha256": sensitivity.sha256(root / "configs/registry_v1.json"),
                "registry_sha256": sensitivity.sha256(root / "docs/ANALYSIS_REGISTRY.md"),
                "input_hashes": hashes,
            })
            output = cross_validated_predictions(self.X, self.y, self.strata, self.settings)
            summary, metrics = sensitivity.summary_for(output)
            for test in config["predictive_tests"]:
                sensitivity.save_output(primary / test, output, self.ids, ["a", "b", "c", "d"],
                                        summary, metrics)
            pd.DataFrame([{"test_id": s["id"], "rho": output["rho"], "failure_reason": ""}
                          for s in registry["tests"]]).to_csv(primary / "registry_results.csv", index=False)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            data = (self.X, self.y, self.strata, self.ids, ["a", "b", "c", "d"])
            with patch.object(sensitivity, "verify_freeze", return_value=hashes), \
                    patch.object(sensitivity, "load_analysis", return_value=data), \
                    patch.object(sensitivity.subprocess, "check_output", return_value="synthetic\n"):
                destination = sensitivity.run("primary", "descriptive", root)
                with self.assertRaises(FileExistsError):
                    sensitivity.run("primary", "descriptive", root)
            self.assertTrue(all(p.read_bytes() == value for p, value in before.items()))
            result = pd.read_csv(destination / "sensitivity_results.csv")
            self.assertEqual(len(result), 19)
            self.assertFalse(result.failure_reason.notna().any())
            for prohibited in ("p_raw", "p_holm", "decision", "ci_low", "ci_high"):
                self.assertNotIn(prohibited, result.columns)
            self.assertFalse((root / "results/v2/models").exists())
            status = json.loads((destination / "run.json").read_text())
            self.assertEqual(status["status"], "complete")
            self.assertTrue(status["descriptive_only"])
            self.assertEqual(status["analyses"], 19)


if __name__ == "__main__":
    unittest.main()
