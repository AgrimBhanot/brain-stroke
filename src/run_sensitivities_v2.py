"""Registered descriptive sensitivities, run only after the frozen primary run."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import subprocess

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

try:
    from .run_registry import verify_freeze, sha256
    from .stats_utils import pooled_oof_spearman
    from .train_regression import (
        load_analysis, validate_arrays, cross_validated_predictions, prediction_metrics,
    )
except ImportError:
    from run_registry import verify_freeze, sha256
    from stats_utils import pooled_oof_spearman
    from train_regression import (
        load_analysis, validate_arrays, cross_validated_predictions, prediction_metrics,
    )

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/sensitivities_v2.json"


def group_labels(ids, pairs):
    """Map the prespecified pairs; never combine their target values."""
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated subject identifier")
    lookup, seen = {}, set()
    for pair in pairs:
        if len(pair) != 2 or len(set(pair)) != 2 or seen.intersection(pair):
            raise ValueError("Pairs must be disjoint pairs of distinct IDs")
        if not set(pair).issubset(ids):
            raise ValueError("A prespecified pair member is absent")
        seen.update(pair)
        for subject in pair:
            lookup[subject] = "pair:" + "|".join(pair)
    return np.array([lookup.get(subject, "single:" + subject) for subject in ids])


def checked_group_splits(X, strata, groups, n_splits, seed):
    if len(np.unique(groups)) < n_splits:
        raise ValueError("Too few groups for the specified folds")
    coverage = np.zeros(len(X), dtype=int)
    splits = list(StratifiedGroupKFold(
        n_splits=n_splits, shuffle=True, random_state=seed,
    ).split(X, strata, groups))
    for train, valid in splits:
        if not len(train) or not len(valid) or np.intersect1d(train, valid).size:
            raise ValueError("Empty or overlapping grouped fold")
        if set(groups[train]).intersection(groups[valid]):
            raise ValueError("Group crosses training/validation")
        coverage[valid] += 1
    if not np.all(coverage == 1):
        raise ValueError("Grouped folds do not cover every subject exactly once")
    return splits


def fit_grouped_ridge(X, y, strata, groups, settings, seed, n_jobs):
    splits = checked_group_splits(X, strata, groups, settings["inner_splits"], seed)
    search = GridSearchCV(
        Pipeline([("scale", StandardScaler()), ("ridge", Ridge(solver="svd"))]),
        {"ridge__alpha": settings["alphas"]}, cv=splits,
        scoring="neg_mean_squared_error", n_jobs=n_jobs, refit=True, error_score="raise",
    ).fit(X, y)
    return search.best_estimator_, float(search.best_params_["ridge__alpha"]), splits


def empty_output(y, strata, repeats):
    prediction = np.full((len(y), repeats), np.nan)
    return {
        "predictions": prediction, "dummy": np.full_like(prediction, np.nan),
        "folds": np.full(prediction.shape, -1, dtype=int),
        "target": y, "strata": strata, "alphas": [], "fold_audit": [],
    }


def finish_output(output, coverage):
    if not np.all(coverage == 1) or not np.isfinite(output["predictions"]).all():
        raise ValueError("Incomplete or repeated out-of-fold predictions")
    if not np.isfinite(output["dummy"]).all():
        raise ValueError("Incomplete baseline predictions")
    output["rho"] = pooled_oof_spearman(output["target"], output["predictions"])
    return output


def grouped_predictions(X, y, strata, ids, settings, grouped):
    X, y, strata = validate_arrays(X, y, strata, settings)
    if len(ids) != len(y):
        raise ValueError("IDs and arrays are misaligned")
    groups = group_labels(ids, grouped["pairs"])
    out = empty_output(y, strata, settings["outer_repeats"])
    out["groups"] = groups
    coverage = np.zeros_like(out["folds"])
    for r in range(settings["outer_repeats"]):
        splits = checked_group_splits(
            X, strata, groups, settings["outer_splits"], grouped["outer_seed_base"] + r,
        )
        for f, (train, valid) in enumerate(splits):
            model, alpha, inner = fit_grouped_ridge(
                X[train], y[train], strata[train], groups[train], settings,
                grouped["inner_seed_base"] + settings["outer_splits"] * r + f,
                grouped["search_n_jobs"],
            )
            out["predictions"][valid, r] = model.predict(X[valid])
            out["dummy"][valid, r] = y[train].mean()
            out["folds"][valid, r] = f
            coverage[valid, r] += 1
            out["alphas"].append({"repeat": r, "fold": f, "alpha": alpha})
            out["fold_audit"].append({
                "repeat": r, "fold": f,
                "train_ids": [ids[i] for i in train],
                "valid_ids": [ids[i] for i in valid],
                "train_groups": int(len(np.unique(groups[train]))),
                "valid_groups": int(len(np.unique(groups[valid]))),
                "train_class_counts": np.bincount(strata[train], minlength=2).tolist(),
                "valid_class_counts": np.bincount(strata[valid], minlength=2).tolist(),
                "inner": [{
                    "train_ids": [ids[i] for i in train[a]],
                    "valid_ids": [ids[i] for i in train[b]],
                    "train_groups": int(len(np.unique(groups[train[a]]))),
                    "valid_groups": int(len(np.unique(groups[train[b]]))),
                    "train_class_counts": np.bincount(strata[train[a]], minlength=2).tolist(),
                    "valid_class_counts": np.bincount(strata[train[b]], minlength=2).tolist(),
                } for a, b in inner],
            })
    # Count distinct partitions independently of arbitrary fold numbering.
    partitions = {
        tuple(sorted(tuple(np.flatnonzero(out["folds"][:, r] == f))
                     for f in range(settings["outer_splits"])))
        for r in range(settings["outer_repeats"])
    }
    out["distinct_outer_partitions"] = len(partitions)
    return finish_output(out, coverage)


def alternative_predictions(X, y, strata, settings, kind, parameters):
    X, y, strata = validate_arrays(X, y, strata, settings)
    out = empty_output(y, strata, settings["outer_repeats"])
    coverage = np.zeros_like(out["folds"])
    cv = RepeatedStratifiedKFold(
        n_splits=settings["outer_splits"], n_repeats=settings["outer_repeats"],
        random_state=settings["split_seed"],
    )
    for index, (train, valid) in enumerate(cv.split(X, strata)):
        r, f = divmod(index, settings["outer_splits"])
        if kind == "svr":
            model = Pipeline([("scale", StandardScaler()), ("svr", SVR(**parameters))])
        elif kind == "random_forest":
            model = RandomForestRegressor(**parameters)
        else:
            raise ValueError("Unknown prespecified alternative model")
        model.fit(X[train], y[train])
        out["predictions"][valid, r] = model.predict(X[valid])
        out["dummy"][valid, r] = y[train].mean()
        out["folds"][valid, r] = f
        coverage[valid, r] += 1
    return finish_output(out, coverage)


def combine_inputs(left, right, expected_n):
    X1, y1, s1, ids1, features1 = left
    X2, y2, s2, ids2, features2 = right
    if len(set(ids1)) != len(ids1) or len(set(ids2)) != len(ids2):
        raise ValueError("Repeated combined-table ID")
    common = sorted(set(ids1).intersection(ids2))
    if len(common) != expected_n:
        raise ValueError("Unexpected combined-table membership")
    pos1, pos2 = {v: i for i, v in enumerate(ids1)}, {v: i for i, v in enumerate(ids2)}
    a, b = [pos1[v] for v in common], [pos2[v] for v in common]
    if not np.array_equal(y1[a], y2[b]) or not np.array_equal(s1[a], s2[b]):
        raise ValueError("Combined target/class mismatch")
    features = ["spectral:" + f for f in features1] + ["graph:" + f for f in features2]
    return np.column_stack((X1[a], X2[b])), y1[a], s1[a], common, features


def summary_for(output):
    rows = prediction_metrics(output["target"], output["strata"], output)
    summary = {
        "rho": float(output["rho"]), "n": len(output["target"]),
        "mild": int((output["strata"] == 0).sum()),
        "moderate": int((output["strata"] == 1).sum()),
        **{key: float(np.mean([r[key] for r in rows]))
           for key in rows[0] if key not in ("repeat", "rho")},
    }
    if "groups" in output:
        summary["groups"] = int(len(np.unique(output["groups"])))
        summary["distinct_outer_partitions"] = output["distinct_outer_partitions"]
    return summary, rows


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save_output(path, output, ids, features, summary, metrics):
    path.mkdir(exist_ok=False)
    records = []
    for r in range(output["predictions"].shape[1]):
        for i, subject in enumerate(ids):
            records.append({
                "subject_id": subject, "repeat": r, "fold": int(output["folds"][i, r]),
                "target": float(output["target"][i]), "stratum": int(output["strata"][i]),
                "prediction": float(output["predictions"][i, r]),
                "dummy_prediction": float(output["dummy"][i, r]),
                "group": str(output["groups"][i]) if "groups" in output else subject,
            })
    pd.DataFrame(records).to_csv(path / "oof.csv", index=False)
    pd.DataFrame(metrics).to_csv(path / "repeat_metrics.csv", index=False)
    if output["alphas"]:
        pd.DataFrame(output["alphas"]).to_csv(path / "selected_alphas.csv", index=False)
    write_json(path / "summary.json", summary)
    write_json(path / "feature_contract.json", {"subject_ids": ids, "features": features})
    if output.get("fold_audit"):
        write_json(path / "fold_audit.json", output["fold_audit"])


def run(primary_id, run_id, root=ROOT):
    root = Path(root)
    if not all(re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in (primary_id, run_id)):
        raise ValueError("Invalid run identifier")
    hashes = verify_freeze(root)
    primary_dir = root / "results/v2/runs" / primary_id
    primary = json.loads((primary_dir / "run.json").read_text(encoding="utf-8"))
    if primary["mode"] != "real" or primary["status"] != "complete":
        raise ValueError("A completed primary real run is required")
    registry = json.loads((root / "configs/registry_v1.json").read_text(encoding="utf-8"))
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/REGISTRY_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    if config["inference"] is not False or config["primary_artifact_digest"] != manifest["artifact_digest"]:
        raise ValueError("Sensitivity scope or primary digest changed")
    if primary["settings"] != registry["settings"]:
        raise ValueError("Primary settings do not match the frozen registry")
    for path, value in (
        ("configs/registry_v1.json", primary["config_sha256"]),
        ("docs/ANALYSIS_REGISTRY.md", primary["registry_sha256"]),
    ):
        if sha256(root / path) != value:
            raise ValueError("Primary recorded input changed: " + path)
    specs = {spec["id"]: spec for spec in registry["tests"]}
    expected = [spec["id"] for spec in registry["tests"] if spec["kind"] == "ridge"]
    if config["predictive_tests"] != expected:
        raise ValueError("Sensitivity must cover every prespecified predictive test")
    for name in expected:
        spec = specs[name]
        if sha256(root / spec["table"]) != primary["input_hashes"][spec["table"]]:
            raise ValueError("Primary feature input changed")
    if sha256(root / "features/v2/subject_meta.csv") != primary["input_hashes"]["features/v2/subject_meta.csv"]:
        raise ValueError("Primary metadata input changed")
    baseline = pd.read_csv(primary_dir / "registry_results.csv").set_index("test_id")
    if not baseline.index.is_unique or baseline.index.tolist() != [s["id"] for s in registry["tests"]]:
        raise ValueError("Primary result family is incomplete")
    if baseline.failure_reason.notna().any():
        raise ValueError("Primary result contains a failure")
    directory = root / "results/v2/sensitivities" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    provenance_paths = [
        CONFIG, "src/run_sensitivities_v2.py", "tests/test_sensitivities_v2.py",
        f"results/v2/runs/{primary_id}/run.json",
        f"results/v2/runs/{primary_id}/registry_results.csv",
    ]
    for name in expected:
        provenance_paths += [f"results/v2/runs/{primary_id}/{name}/oof.csv",
                             f"results/v2/runs/{primary_id}/{name}/summary.json"]
    metadata = {
        "status": "running", "descriptive_only": True,
        "primary_run": primary_id, "run_id": run_id,
        "primary_artifact_digest": manifest["artifact_digest"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "python": platform.python_version(), "numpy": np.__version__, "sklearn": sklearn.__version__,
        "input_hashes": hashes, "artifact_hashes": {p: sha256(root / p) for p in provenance_paths},
        "settings": registry["settings"], "sensitivity_config": config,
    }
    write_json(directory / "run.json", metadata)
    rows = []

    def execute(name, kind, data, primary_test=None):
        try:
            X, y, strata, ids, features = data()
            if kind == "grouped":
                output = grouped_predictions(X, y, strata, ids, registry["settings"], config["grouped"])
            elif kind == "combined":
                output = cross_validated_predictions(X, y, strata, registry["settings"])
            else:
                output = alternative_predictions(X, y, strata, registry["settings"], kind, config["models"][kind])
            summary, metrics = summary_for(output)
            if primary_test:
                saved = pd.read_csv(primary_dir / primary_test / "oof.csv")
                if sorted(saved.subject_id.unique()) != ids:
                    raise ValueError("Sensitivity membership differs from its primary comparator")
                if kind != "grouped":
                    folds = saved.pivot(index="subject_id", columns="repeat", values="fold").loc[ids].to_numpy()
                    if not np.array_equal(folds, output["folds"]):
                        raise ValueError("Alternative model splits differ from primary")
                summary["primary_rho"] = float(baseline.loc[primary_test, "rho"])
                summary["delta_primary_minus_sensitivity"] = summary["primary_rho"] - summary["rho"]
                summary["absolute_delta"] = abs(summary["delta_primary_minus_sensitivity"])
                if kind == "grouped":
                    summary["material_delta_flag"] = bool(
                        abs(summary["delta_primary_minus_sensitivity"]) > config["grouped"]["material_delta"])
            save_output(directory / name, output, ids, features, summary, metrics)
            rows.append({"analysis": name, "kind": kind, **summary, "failure_reason": ""})
        except Exception as exc:
            rows.append({"analysis": name, "kind": kind, "failure_reason": f"{type(exc).__name__}: {exc}"})
        pd.DataFrame(rows).to_csv(directory / "sensitivity_results.csv", index=False)
        print(name + (": FAILED" if rows[-1]["failure_reason"] else ": completed"), flush=True)

    for name in expected:
        execute("grouped_" + name, "grouped", lambda n=name: load_analysis(root, specs[n]), name)
    for kind in config["models"]:
        for name in expected:
            execute(kind + "_" + name, kind, lambda n=name: load_analysis(root, specs[n]), name)
    combined = config["combined"]
    execute("combined_T2_T5", "combined", lambda: combine_inputs(
        load_analysis(root, specs[combined["left_test"]]),
        load_analysis(root, specs[combined["right_test"]]), combined["expected_n"],
    ))
    failed = any(row["failure_reason"] for row in rows)
    metadata.update(status="failed" if failed else "complete",
                    finished_at=datetime.now(timezone.utc).isoformat(), analyses=len(rows))
    write_json(directory / "run.json", metadata)
    if failed:
        raise RuntimeError("Sensitivity failures recorded; inspect " + str(directory))
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-run", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    print(run(args.primary_run, args.run_id))
