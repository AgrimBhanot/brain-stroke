"""Label-agnostic registry engine. Real-label orchestration is run_registry.py.

    The inner Ridge path uses one SVD per training fold for all fixed alphas.
    It is algebraically equivalent to full-pipeline GridSearchCV with MSE,
    while keeping the scaler fit strictly inside inner training folds.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, roc_auc_score

try:
    from .stats_utils import bootstrap_ci, perm_pvalue, pooled_oof_spearman, spearman
except ImportError:
    from stats_utils import bootstrap_ci, perm_pvalue, pooled_oof_spearman, spearman


def fit_ridge(X, y, settings):
    X, y = np.asarray(X, float), np.asarray(y, float)
    alphas = np.asarray(settings["alphas"], float)
    if len(alphas) < 1 or (alphas <= 0).any() or not np.isfinite(alphas).all() or (np.diff(alphas) < 0).any():
        raise ValueError("Alphas must be finite, positive, ascending")
    cv = KFold(settings["inner_splits"], shuffle=True, random_state=settings["split_seed"])
    scores = np.zeros(len(alphas))
    for train, valid in cv.split(X):
        scaling = Pipeline([("scale", StandardScaler())])
        a = scaling.fit_transform(X[train])
        b = scaling.transform(X[valid])
        # Ridge fits an intercept after scaling, including round-off centering.
        xmean, ymean = a.mean(axis=0), y[train].mean()
        u, singular, vt = np.linalg.svd(a - xmean, full_matrices=False)
        weights = singular[:, None] / (singular[:, None] ** 2 + alphas[None, :])
        coefficients = vt.T @ (weights * (u.T @ (y[train] - ymean))[:, None])
        predicted = (b - xmean) @ coefficients + ymean
        scores += ((predicted - y[valid, None]) ** 2).mean(axis=0)
    alpha = float(alphas[np.argmin(scores)])
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha, solver="svd"))])
    model.fit(X, y)
    return model, alpha


def validate_arrays(X, y, strata, settings):
    X, y, strata = np.asarray(X, float), np.asarray(y, float), np.asarray(strata)
    if X.ndim != 2 or y.shape != (len(X),) or strata.shape != y.shape or X.shape[1] < 1:
        raise ValueError("Invalid model matrix or target dimensions")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("Nonfinite features/target")
    classes, counts = np.unique(strata, return_counts=True)
    if len(classes) != 2 or counts.min() < settings["outer_splits"]:
        raise ValueError("Need two classes with enough subjects for stratification")
    return X, y, strata


def cross_validated_predictions(X, y, strata, settings, *, details=True):
    X, y, strata = validate_arrays(X, y, strata, settings)
    repeats, folds = settings["outer_repeats"], settings["outer_splits"]
    prediction = np.full((len(y), repeats), np.nan)
    dummy = np.full_like(prediction, np.nan)
    membership = np.full((len(y), repeats), -1, dtype=int)
    alphas = []
    cv = RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=settings["split_seed"])
    for index, (train, valid) in enumerate(cv.split(X, strata)):
        repeat, fold = divmod(index, folds)
        model, alpha = fit_ridge(X[train], y[train], settings)
        prediction[valid, repeat] = model.predict(X[valid])
        membership[valid, repeat] = fold
        alphas.append({"repeat": repeat, "fold": fold, "alpha": alpha})
        if details:
            baseline = DummyRegressor(strategy="mean").fit(X[train], y[train])
            dummy[valid, repeat] = baseline.predict(X[valid])
    rho = pooled_oof_spearman(y, prediction)
    return {"rho": rho, "predictions": prediction, "dummy": dummy, "target": y, "strata": strata,
            "folds": membership, "alphas": alphas}


def prediction_metrics(y, strata, output):
    records = []
    for r in range(output["predictions"].shape[1]):
        pred, base = output["predictions"][:, r], output["dummy"][:, r]
        row = {"repeat": r, "rho": spearman(y, pred),
               "rmse": float(np.sqrt(mean_squared_error(y, pred))),
               "mae": float(mean_absolute_error(y, pred)), "r2": float(r2_score(y, pred)),
               "auc": float(roc_auc_score(strata, pred)),
               "dummy_rmse": float(np.sqrt(mean_squared_error(y, base))),
               "dummy_mae": float(mean_absolute_error(y, base)), "dummy_r2": float(r2_score(y, base))}
        for key in ("rmse", "mae", "r2"):
            row[key + "_minus_dummy"] = row[key] - row["dummy_" + key]
        records.append(row)
    return records


def evaluate(X, y, strata, settings, test_number, kind="ridge"):
    X, y, strata = validate_arrays(X, y, strata, settings)
    if kind not in ("ridge", "association") or (kind == "association" and X.shape[1] != 1):
        raise ValueError("Invalid registered analysis kind")
    output = cross_validated_predictions(X, y, strata, settings) if kind == "ridge" else None
    statistic = output["rho"] if output else spearman(y, X[:, 0])
    if not np.isfinite(statistic):
        raise ValueError("Observed statistic is undefined")
    rng = np.random.default_rng(settings["permutation_seed_base"] + test_number)
    null = np.empty(settings["permutations"])
    for b in range(len(null)):
        permutation = rng.permutation(len(y))
        if kind == "ridge":
            null[b] = cross_validated_predictions(X, y[permutation], strata[permutation], settings, details=False)["rho"]
        else:
            null[b] = spearman(y[permutation], X[:, 0])
    alternative = "greater" if kind == "ridge" else "two-sided"
    p = perm_pvalue(statistic, null, alternative)
    ci = bootstrap_ci(y, output["predictions"] if output else X[:, 0],
                      n_resamples=settings["bootstrap_resamples"],
                      seed=settings["bootstrap_seed_base"] + test_number,
                      confidence=settings["confidence"], max_invalid_fraction=settings["bootstrap_max_invalid_fraction"])
    repeat_metrics = prediction_metrics(y, strata, output) if output else []
    summary = {"rho": statistic, "p_raw": p, "ci_low": ci["low"], "ci_high": ci["high"],
               "ci_available": ci["available"], "bootstrap_invalid": ci["invalid"],
               "n": len(y), "mild": int((strata == 0).sum()), "moderate": int((strata == 1).sum()),
               "alternative": alternative}
    if repeat_metrics:
        summary.update({key: float(np.mean([row[key] for row in repeat_metrics]))
                        for key in repeat_metrics[0] if key not in ("repeat", "rho")})
    return {"summary": summary, "null": null, "bootstrap": ci["values"],
            "output": output, "repeat_metrics": repeat_metrics}


BANNED_PARTS = ("nihss", "severity", "subject", "epoch", "lesion", "paralysis", "age", "sex", "gender", "duration", "onset", "handed", "stroke")


def load_analysis(root, spec, *, shuffle_seed=None):
    """Whitelist-only reads. Shuffling jointly reassigns target/class before use."""
    root = Path(root)
    if "sidecar" in spec:
        contract = json.loads((root / spec["sidecar"]).read_text(encoding="utf-8"))
        columns = contract["columns"]
        if len(columns) != len(set(columns)) or columns[0] != "subject_id":
            raise ValueError("Invalid feature sidecar schema")
        features = columns[1:]
        if list(pd.read_csv(root / spec["table"], nrows=0).columns) != columns:
            raise ValueError("CSV columns/order differ from sidecar")
    else:
        features = spec["features"]
    if not features or len(features) != len(set(features)) or any(any(p in c.lower() for p in BANNED_PARTS) for c in features):
        raise ValueError("Banned, empty or repeated model feature columns")
    table = pd.read_csv(root / spec["table"], usecols=["subject_id"] + features)
    meta = pd.read_csv(root / "features/v2/subject_meta.csv", usecols=["subject_id", "nihss_raw", "severity_class"])
    for frame in (table, meta):
        if frame.subject_id.isna().any() or not frame.subject_id.is_unique:
            raise ValueError("Missing/duplicate subject identifiers")
    expected_ids = spec["subject_ids"]
    if len(expected_ids) != len(set(expected_ids)) or set(table.subject_id) != set(expected_ids):
        raise ValueError("Unexpected subject membership")
    merged = table.merge(meta, on="subject_id", how="left", validate="one_to_one").sort_values("subject_id")
    if len(merged) != spec["expected_n"] or merged.isna().any().any():
        raise ValueError("Missing metadata or unexpected N")
    strata = merged.severity_class.map({"mild": 0, "moderate": 1, "0": 0, "1": 1, 0: 0, 1: 1})
    if strata.isna().any():
        raise ValueError("Invalid severity class")
    X, y, classes = merged[features].to_numpy(float), merged.nihss_raw.to_numpy(float), strata.to_numpy(int)
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("Nonfinite input")
    if (np.ptp(X, axis=0) == 0).any():
        raise ValueError("Constant input feature")
    if not np.array_equal(classes, (y >= 5).astype(int)) or ((y < 1) | (y > 11)).any():
        raise ValueError("Inconsistent target/class encoding")
    if shuffle_seed is not None:
        permutation = np.random.default_rng(shuffle_seed).permutation(len(y))
        y, classes = y[permutation], classes[permutation]
    return X, y, classes, merged.subject_id.tolist(), features
