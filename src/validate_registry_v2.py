"""Reproducible synthetic controls and null calibration; never reads cohort labels."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from scipy.stats import binomtest
import scipy
import sklearn
from threadpoolctl import threadpool_limits
try:
    from .train_regression import evaluate
except ImportError:
    from train_regression import evaluate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/REGISTRY_VALIDATION_RESULTS.json"


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def simulation_settings(config, plan):
    return {**config["settings"], **{key: plan[key] for key in
            ("permutations", "outer_repeats", "bootstrap_resamples")}}


def simulated(seed, signal, population_correlation=0.65):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(50, 19))
    # The diagnostic strength is fixed in config, never selected from cohort labels.
    noise = rng.normal(size=50)
    y = population_correlation * X[:, 0] + np.sqrt(1 - population_correlation ** 2) * noise if signal else noise
    strata = (y > np.quantile(y, 0.66)).astype(int)
    return X, y, strata


def null_dataset(args):
    seed, settings = args
    with threadpool_limits(limits=1):
        X, y, strata = simulated(seed, False)
        result = evaluate(X, y, strata, settings, seed, "ridge")
    return {"seed": seed, "p": result["summary"]["p_raw"], "rho": result["summary"]["rho"]}


def signal_dataset(args):
    seed, test_number, correlation, settings = args
    try:
        with threadpool_limits(limits=1):
            X, y, strata = simulated(seed, True, correlation)
            result = evaluate(X, y, strata, settings, test_number, "ridge")
        return {"seed": seed, "test_number": test_number, "p": result["summary"]["p_raw"],
                "rho": result["summary"]["rho"], "null": result["null"].tolist(),
                "failure_reason": None}
    except Exception as exc:
        return {"seed": seed, "test_number": test_number,
                "failure_reason": f"{type(exc).__name__}: {exc}"}


def summarize_power(rows, plan):
    expected_seeds = list(range(plan["seed"], plan["seed"] + plan["datasets"]))
    complete = len(rows) == plan["datasets"] and sorted(row["seed"] for row in rows) == expected_seeds
    complete = complete and all(not row.get("failure_reason") and np.isfinite(row.get("p", np.nan))
                                and 0 <= row["p"] <= 1 for row in rows)
    detected = sum(not row.get("failure_reason") and row.get("p", 1) < plan["alpha"] for row in rows)
    rate = detected / plan["datasets"] if complete else None
    interval = binomtest(detected, plan["datasets"]).proportion_ci() if complete else None
    low, high = plan["expected_rate"]
    return {"datasets_planned": plan["datasets"], "datasets_completed": len(rows),
            "complete": complete, "detections": detected, "alpha": plan["alpha"],
            "detection_rate": rate, "expected_rate": plan["expected_rate"],
            "binomial_exact_95_ci": [float(interval.low), float(interval.high)] if interval else None,
            "passed": bool(complete and low <= rate <= high)}


def update_power_evidence(report, output, root=ROOT):
    evidence_path = Path(root) / "docs/REGISTRY_VALIDATION_RESULTS.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    calibration = evidence["controls"]["null_calibration"]
    source = Path(root) / calibration["path"]
    calibration_ok = (calibration.get("passed") is True and source.is_file()
                      and file_hash(source) == calibration["sha256"])
    tests = evidence.get("unit_tests", {})
    smoke = evidence.get("shuffled_smoke", {})
    prerequisites = {"null_calibration_passed_and_hash_verified": calibration_ok,
                     "recorded_unit_tests_passed": tests.get("total", 0) > 0 and tests.get("passed") == tests.get("total"),
                     "recorded_shuffled_smoke_completed": smoke.get("completed") == smoke.get("tests") == 9}
    evidence["date"] = datetime.now(timezone.utc).date().isoformat()
    evidence["positive_control_policy"] = "Option 3; post-failure amendment 2026-10-19; original controls preserved"
    evidence["power_diagnostic"] = {"path": Path(output).resolve().relative_to(Path(root).resolve()).as_posix(),
                                    "sha256": file_hash(output), "plan": report["plan"],
                                    "gate_a": {k: v for k, v in report["gate_a"].items() if k != "null"},
                                    "gate_b": report["gate_b"], "passed": report["passed"]}
    evidence["prerequisites"] = prerequisites
    evidence["acceptance_passed"] = bool(report["passed"] and all(prerequisites.values()))
    evidence["blocking_reason"] = None if evidence["acceptance_passed"] else "Option 3 gates or validation prerequisites failed/incomplete."
    evidence["review_status"] = "Latest snapshot requires Agrim's owner approval; tags pending."
    evidence_path.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def power_diagnostic(config, output):
    """Run both pre-recorded gates, retaining all 200 outcomes and null statistics."""
    plan = config["validation"]["power_diagnostic"]
    output = Path(output).resolve()
    checkpoint = output.with_suffix(".checkpoint.jsonl")
    if output.exists() or checkpoint.exists():
        raise FileExistsError("Validation output/checkpoint exists; preserve it and use a new explicit output path")
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"mode": "power_diagnostic", "started_at": datetime.now(timezone.utc).isoformat(), "plan": plan,
              "versions": {"python": platform.python_version(), "numpy": np.__version__,
                           "scipy": scipy.__version__, "sklearn": sklearn.__version__},
              "source_hashes": {p: file_hash(ROOT / p) for p in
                                ("configs/registry_v1.json", "src/validate_registry_v2.py", "src/train_regression.py", "src/stats_utils.py")}}
    a, b = plan["gate_a"], plan["gate_b"]
    report["settings_a"], report["settings_b"] = simulation_settings(config, a), simulation_settings(config, b)
    print("Gate A: evaluating fixed strong-signal dataset", flush=True)
    gate_a = signal_dataset((a["seed"], a["test_number"], a["population_correlation"], report["settings_a"]))
    gate_a["passed"] = bool(not gate_a.get("failure_reason") and gate_a["p"] < a["target_p"])
    report["gate_a"] = gate_a
    print(f"Gate A completed: p={gate_a.get('p')}, passed={gate_a['passed']}", flush=True)
    rows = []
    jobs = [(b["seed"] + i, b["seed"] + i, b["population_correlation"], report["settings_b"]) for i in range(b["datasets"])]
    with checkpoint.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"protocol": report}, allow_nan=False) + "\n")
        handle.flush()
        with ProcessPoolExecutor(max_workers=plan["workers"]) as executor:
            for row in executor.map(signal_dataset, jobs):
                rows.append(row)
                handle.write(json.dumps(row, allow_nan=False) + "\n")
                handle.flush()
                print(f"Gate B: {len(rows)}/{len(jobs)} datasets completed", flush=True)
    report["rows"] = rows
    report["gate_b"] = summarize_power(rows, b)
    report["passed"] = gate_a["passed"] and report["gate_b"]["passed"]
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    update_power_evidence(report, output)
    print(json.dumps({"gate_a": {k: v for k, v in gate_a.items() if k != "null"},
                      "gate_b": report["gate_b"], "passed": report["passed"]}, indent=2), flush=True)
    return report


def validate(mode, output):
    config = json.loads((ROOT / "configs/registry_v1.json").read_text(encoding="utf-8"))
    if mode == "power_diagnostic":
        return power_diagnostic(config, output)
    plan = config["validation"][mode]
    settings = {**config["settings"], **{key: plan[key] for key in ("permutations", "outer_repeats", "bootstrap_resamples")}}
    if mode in ("positive", "strong_positive"):
        X, y, strata = simulated(plan["seed"], True, plan["population_correlation"])
        with threadpool_limits(limits=1):
            result = evaluate(X, y, strata, settings, 1)
        report = {"mode": mode, "settings": settings, "seed": plan["seed"], "summary": result["summary"],
                  "passed": result["summary"]["p_raw"] < 0.01}
    else:
        jobs = [(plan["seed"] + i, settings) for i in range(plan["datasets"])]
        rows = []
        with ProcessPoolExecutor(max_workers=plan["workers"]) as executor:
            for row in executor.map(null_dataset, jobs):
                rows.append(row)
                print(f"Null calibration {len(rows)}/{len(jobs)}", flush=True)
        rate = float(np.mean([row["p"] < plan["alpha"] for row in rows]))
        lo, hi = plan["expected_rate"]
        report = {"mode": mode, "settings": settings, "plan": plan, "rows": rows,
                  "false_positive_rate": rate, "passed": lo <= rate <= hi,
                  "interpretation": "Monte Carlo diagnostic, not proof of nominal error control; do not tune seeds or pipeline to force a pass."}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("rows", "settings", "plan")}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("positive", "strong_positive", "calibration", "power_diagnostic"), default="power_diagnostic")
    parser.add_argument("--output", default="results/v2/validation/power_diagnostic_option3_20261019.json")
    args = parser.parse_args()
    report = validate(args.mode, args.output)
    if not report['passed']:
        raise SystemExit(1)
