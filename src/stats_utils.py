"""Statistics for the fixed v2 registry; no data access or model fitting."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm, rankdata


def holm_adjust(pvalues):
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or not len(p) or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Expected a nonempty vector of finite p-values in [0, 1]")
    order = np.argsort(p, kind="stable")
    adjusted = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    result = np.empty_like(p)
    result[order] = adjusted
    return result


def perm_pvalue(observed, null, alternative="greater"):
    null = np.asarray(null, dtype=float)
    if null.ndim != 1 or not len(null) or not np.isfinite(null).all() or not np.isfinite(observed):
        raise ValueError("Permutation statistics must be finite and nonempty")
    if alternative == "greater":
        exceed = null >= observed
    elif alternative == "two-sided":
        exceed = np.abs(null) >= abs(observed)
    else:
        raise ValueError("Unknown alternative")
    return float((1 + exceed.sum()) / (len(null) + 1))


def spearman(y, predictions):
    """Average-rank Pearson correlation, matching scipy's Spearman ties."""
    y, predictions = np.asarray(y, float), np.asarray(predictions, float)
    if y.ndim != 1 or predictions.shape != y.shape or not np.isfinite(y).all() or not np.isfinite(predictions).all():
        raise ValueError("Spearman requires aligned finite vectors")
    a, b = rankdata(y), rankdata(predictions)
    a, b = a - a.mean(), b - b.mean()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denominator) if denominator else float("nan")


def pooled_oof_spearman(y, predictions):
    predictions = np.asarray(predictions, float)
    if predictions.ndim == 1:
        predictions = predictions[:, None]
    if predictions.ndim != 2 or predictions.shape[0] != len(y) or predictions.shape[1] < 1:
        raise ValueError("Expected N-by-repeats held-out predictions")
    correlations = np.array([spearman(y, predictions[:, r]) for r in range(predictions.shape[1])])
    if not np.isfinite(correlations).all():
        raise ValueError("Undefined pooled Spearman in at least one repeat")
    return float(correlations.mean())


def bootstrap_ci(y, predictions, *, n_resamples=2000, seed=52, confidence=0.95, max_invalid_fraction=0.01):
    """Subject-row percentile CI conditional on supplied predictions.

    Draw exactly B rowsamples; no redraw. Undefined rowsamples are counted.
    Above 1% invalid, return an unavailable CI; otherwise use finite draws.
    This is descriptive and does not alter permutation inference.
    """
    y, predictions = np.asarray(y, float), np.asarray(predictions, float)
    if n_resamples < 1 or len(y) < 3 or not 0 < confidence < 1:
        raise ValueError("Invalid bootstrap dimensions/settings")
    if predictions.shape[0] != len(y) or not np.isfinite(y).all() or not np.isfinite(predictions).all():
        raise ValueError("Bootstrap requires aligned finite inputs")
    rng = np.random.default_rng(seed)
    values = np.full(n_resamples, np.nan)
    for b in range(n_resamples):
        indices = rng.integers(0, len(y), len(y))
        try:
            values[b] = pooled_oof_spearman(y[indices], predictions[indices])
        except ValueError:
            pass
    valid = np.isfinite(values)
    invalid = int((~valid).sum())
    available = invalid / n_resamples <= max_invalid_fraction and valid.any()
    tail = (1 - confidence) / 2
    lo, hi = np.quantile(values[valid], [tail, 1 - tail]) if available else (None, None)
    return {"low": None if lo is None else float(lo), "high": None if hi is None else float(hi),
            "invalid": invalid, "draws": n_resamples, "available": bool(available), "values": values}


def minimum_detectable_rho(n, alpha=0.05, power=0.8):
    if n <= 3 or not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("Invalid power calculation inputs")
    return float(np.tanh((norm.ppf(1 - alpha / 2) + norm.ppf(power)) / np.sqrt(n - 3)))
