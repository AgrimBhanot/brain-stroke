"""Continue an interrupted frozen run, preserving completed test bytes.

All fitting, family correction and model export still use run_registry.run.
This adapter only validates/reuses complete saved tests in their original order.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess

import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.model_selection import RepeatedStratifiedKFold

try:
    from . import run_registry as registry
    from .stats_utils import pooled_oof_spearman, perm_pvalue, spearman
    from .train_regression import prediction_metrics
except ImportError:
    import run_registry as registry
    from stats_utils import pooled_oof_spearman, perm_pvalue, spearman
    from train_regression import prediction_metrics

ROOT = Path(__file__).resolve().parents[1]


def validate_saved_test(directory, spec, settings, data):
    X, y, strata, ids, features = data
    directory = Path(directory)
    contract = json.loads((directory / "config.json").read_text())
    if contract != {"settings": settings, "features": features, "subject_ids": ids}:
        raise ValueError("Saved test contract differs from frozen inputs")
    summary = json.loads((directory / "summary.json").read_text())
    null = np.load(directory / "null.npy", allow_pickle=False)
    bootstrap = np.load(directory / "bootstrap.npy", allow_pickle=False)
    if null.shape != (settings["permutations"],) or not np.isfinite(null).all():
        raise ValueError("Incomplete saved permutation distribution")
    if bootstrap.shape != (settings["bootstrap_resamples"],):
        raise ValueError("Incomplete saved bootstrap distribution")
    if spec["kind"] == "ridge":
        frame = pd.read_csv(directory / "oof.csv")
        repeats = settings["outer_repeats"]
        if (len(frame) != len(ids) * repeats or frame.duplicated(["subject_id", "repeat"]).any()
                or sorted(frame.subject_id.unique()) != ids
                or sorted(frame["repeat"].unique()) != list(range(repeats))):
            raise ValueError("Incomplete saved OOF coverage")
        def matrix(name):
            return frame.pivot(index="subject_id", columns="repeat", values=name).loc[ids].to_numpy()
        predictions, dummy, folds = matrix("prediction"), matrix("dummy_prediction"), matrix("fold")
        np.testing.assert_allclose(matrix("target"), np.repeat(y[:, None], repeats, axis=1), rtol=0, atol=0)
        np.testing.assert_array_equal(matrix("stratum"), np.repeat(strata[:, None], repeats, axis=1))
        if not np.isfinite(predictions).all() or not np.isfinite(dummy).all():
            raise ValueError("Nonfinite saved OOF prediction")
        cv = RepeatedStratifiedKFold(n_splits=settings["outer_splits"], n_repeats=repeats,
                                    random_state=settings["split_seed"])
        for k, (train, valid) in enumerate(cv.split(X, strata)):
            r, f = divmod(k, settings["outer_splits"])
            np.testing.assert_array_equal(folds[valid, r], f)
            np.testing.assert_allclose(dummy[valid, r], y[train].mean(), rtol=0, atol=1e-12)
        rho = pooled_oof_spearman(y, predictions)
        output = {"predictions": predictions, "dummy": dummy}
        metrics = prediction_metrics(y, strata, output)
        saved_metrics = pd.read_csv(directory / "repeat_metrics.csv")
        for key in metrics[0]:
            np.testing.assert_allclose(saved_metrics[key], [m[key] for m in metrics], rtol=0, atol=1e-12)
            if key not in ("repeat", "rho"):
                np.testing.assert_allclose(summary[key], np.mean([m[key] for m in metrics]), rtol=0, atol=1e-12)
        alphas = pd.read_csv(directory / "selected_alphas.csv")
        expected = {(r, f) for r in range(repeats) for f in range(settings["outer_splits"])}
        if len(alphas) != len(expected) or set(zip(alphas["repeat"], alphas.fold)) != expected:
            raise ValueError("Incomplete saved alpha selections")
        if not all(np.isclose(a, settings["alphas"], rtol=1e-12, atol=1e-12).any() for a in alphas.alpha):
            raise ValueError("Saved alpha outside frozen grid")
    else:
        rho = spearman(y, X[:, 0])
    alternative = "greater" if spec["kind"] == "ridge" else "two-sided"
    if summary["alternative"] != alternative:
        raise ValueError("Saved permutation tail changed")
    np.testing.assert_allclose(summary["rho"], rho, rtol=0, atol=1e-12)
    np.testing.assert_allclose(summary["p_raw"], perm_pvalue(rho, null, alternative), rtol=0, atol=1e-15)
    if (summary["n"], summary["mild"], summary["moderate"]) != (len(ids), int((strata == 0).sum()), int((strata == 1).sum())):
        raise ValueError("Saved cohort counts changed")
    finite = np.isfinite(bootstrap)
    invalid = int((~finite).sum())
    available = bool(finite.any() and invalid / len(bootstrap) <= settings["bootstrap_max_invalid_fraction"])
    if summary["bootstrap_invalid"] != invalid or summary["ci_available"] != available:
        raise ValueError("Saved bootstrap availability changed")
    if available:
        tail = (1 - settings["confidence"]) / 2
        np.testing.assert_allclose([summary["ci_low"], summary["ci_high"]],
                                   np.quantile(bootstrap[finite], [tail, 1-tail]), rtol=0, atol=1e-12)
    elif summary["ci_low"] is not None or summary["ci_high"] is not None:
        raise ValueError("Unavailable bootstrap has numeric limits")
    return {"summary": summary, "null": null, "bootstrap": bootstrap, "output": None, "repeat_metrics": []}


def prepare_cache(root, previous_id, config):
    root = Path(root)
    previous = root / "results/v2/runs" / previous_id
    metadata = json.loads((previous / "run.json").read_text())
    if metadata["mode"] != "real" or metadata["status"] != "running":
        raise ValueError("Continuation requires an interrupted, unfinished real run")
    if metadata["settings"] != config["settings"]:
        raise ValueError("Original settings changed")
    for key, value in {"python": platform.python_version(), "numpy": np.__version__,
                       "scipy": scipy.__version__, "sklearn": sklearn.__version__}.items():
        if metadata[key] != value:
            raise ValueError("Execution version changed: " + key)
    for relative, key in ((registry.CONFIG, "config_sha256"), ("docs/ANALYSIS_REGISTRY.md", "registry_sha256")):
        if registry.sha256(root / relative) != metadata[key]:
            raise ValueError("Original registered input changed: " + relative)
    commit = subprocess.check_output(["git", "rev-parse", "registry-v1^{commit}"], cwd=root, text=True).strip()
    if metadata["source_commit"] != commit:
        raise ValueError("Original run is not from the registry freeze commit")
    cache, missing = {}, False
    for number, spec in enumerate(config["tests"], 1):
        directory = previous / spec["id"]
        if not directory.exists():
            missing = True
            continue
        if missing:
            raise ValueError("Saved tests are not a complete ordered prefix")
        for relative in (spec["table"], "features/v2/subject_meta.csv"):
            content = (root / relative).read_bytes()
            # An interrupted run retains initial guard hashes: legacy entries
            # are LF-canonical, while feature-manifest entries use raw bytes.
            # The frozen guard has already checked both contents against tags.
            representations = {hashlib.sha256(content).hexdigest(),
                               hashlib.sha256(registry.canonical_bytes(content, "utf8-lf")).hexdigest()}
            if metadata["input_hashes"][relative] not in representations:
                raise ValueError("Original feature/metadata input changed: " + relative)
        data = registry.load_analysis(root, spec)
        result = validate_saved_test(directory, spec, config["settings"], data)
        cache[number] = (spec, data, result)
    if not cache or len(cache) == len(config["tests"]):
        raise ValueError("Expected a nonempty, incomplete saved test prefix")
    return previous, cache


def continue_run(previous_id, run_id, reason, root=ROOT):
    root = Path(root)
    if not reason.strip() or not all(re.fullmatch(r"[A-Za-z0-9_-]+", name) for name in (previous_id, run_id)):
        raise ValueError("A reason and safe run identifiers are required")
    if previous_id == run_id or (root / "results/v2/runs" / run_id).exists():
        raise FileExistsError("Continuation must use a new run directory")
    registry.verify_freeze(root)
    config = json.loads((root / registry.CONFIG).read_text())
    previous, cache = prepare_cache(root, previous_id, config)
    original_hashes = {str(p.relative_to(root)): registry.sha256(p) for p in previous.rglob("*") if p.is_file()}
    provenance = {"previous_run": previous_id, "reason": reason,
                  "reused_tests": [value[0]["id"] for value in cache.values()],
                  "computed_tests": [s["id"] for i, s in enumerate(config["tests"], 1) if i not in cache],
                  "previous_artifact_hashes": original_hashes,
                  "started_at": datetime.now(timezone.utc).isoformat(),
                  "adapter_sha256": registry.sha256(Path(__file__)),
                  "test_sha256": registry.sha256(ROOT / "tests/test_continue_registry_v2.py")}
    original_evaluate, original_save = registry.evaluate, registry.save_test
    def evaluate(X, y, strata, settings, number, kind):
        if number not in cache:
            return original_evaluate(X, y, strata, settings, number, kind)
        spec, data, result = cache[number]
        if kind != spec["kind"] or settings != config["settings"]:
            raise ValueError("Continuation changed test kind/settings")
        for actual, expected in zip((X, y, strata), data[:3]):
            np.testing.assert_array_equal(actual, expected)
        print(spec["id"] + ": reusing verified saved result", flush=True)
        return result
    def save(directory, result, ids, features, settings):
        saved = next((value for value in cache.values() if value[0]["id"] == directory.name), None)
        if saved is None:
            return original_save(directory, result, ids, features, settings)
        if ids != saved[1][3] or features != saved[1][4] or result is not saved[2]:
            raise ValueError("Continuation changed saved artifact contract")
        shutil.copytree(previous / directory.name, directory)
    registry.evaluate, registry.save_test = evaluate, save
    try:
        return registry.run("real", run_id, root=root, rerun_reason=reason)
    finally:
        registry.evaluate, registry.save_test = original_evaluate, original_save
        unchanged = all((root / p).is_file() and registry.sha256(root / p) == value for p, value in original_hashes.items())
        provenance.update(finished_at=datetime.now(timezone.utc).isoformat(), previous_files_unchanged=unchanged)
        directory = root / "results/v2/runs" / run_id
        if directory.exists():
            (directory / "continuation.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        if not unchanged:
            raise RuntimeError("Original interrupted run changed during continuation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-run", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    print(continue_run(args.from_run, args.run_id, args.reason))
