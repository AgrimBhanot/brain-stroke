"""Guarded one-shot registry runner; smoke mode always jointly shuffles labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn

try:
    from .freeze_io_v2 import canonical_bytes, matches_record, feature_records
    from .stats_utils import holm_adjust
    from .train_regression import evaluate, fit_ridge, load_analysis
except ImportError:
    from freeze_io_v2 import canonical_bytes, matches_record, feature_records
    from stats_utils import holm_adjust
    from train_regression import evaluate, fit_ridge, load_analysis

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/registry_v1.json"
FREEZE_CONTRACT = "docs/REGISTRY_FREEZE_MANIFEST.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_path(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Path escapes repository")
    return path


def git_bytes(root, ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=root, stderr=subprocess.PIPE)


def manifest_records(manifest):
    return feature_records(manifest)


def verify_clean_execution_tree(root):
    """Reject unstaged, staged, unmerged and untracked executable inputs."""
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "src/", "configs/", "tests/"],
        cwd=root, stderr=subprocess.PIPE)
    for entry in status.split(b"\x00"):
        if not entry:
            continue
        # Some Windows configurations still report EOL-only checkout changes.
        # Exempt only a pure CRLF/LF difference against the index; every other
        # unstaged/staged/untracked state fails. The tag checks follow below.
        if entry[:2] == b" M":
            relative = entry[3:].decode("utf-8")
            path = safe_path(root, relative)
            if path.is_file():
                data = path.read_bytes()
                indexed = git_bytes(root, "", relative)
                if data != indexed and canonical_bytes(data, "utf8-lf") == canonical_bytes(indexed, "utf8-lf"):
                    continue
        paths = status.decode("utf-8", errors="replace").replace("\x00", "; ")
        raise ValueError(f"Uncommitted source/config/test artifact changed: {paths}")


def verify_freeze(root=ROOT):
    """Fail closed on missing tags, changed contents, hashes or approvals."""
    root = Path(root)
    verify_clean_execution_tree(root)
    for tag in ("registry-v1", "features-v2"):
        subprocess.check_output(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], cwd=root, stderr=subprocess.PIPE)
    contract_path = safe_path(root, FREEZE_CONTRACT)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    mode = "utf8-lf" if contract.get("schema_version", 1) >= 2 else "bytes"
    if canonical_bytes(contract_path.read_bytes(), mode) != canonical_bytes(git_bytes(root, "registry-v1", FREEZE_CONTRACT), mode):
        raise ValueError("Registry freeze manifest differs from registry-v1")
    required = {CONFIG, "docs/ANALYSIS_REGISTRY.md", "docs/REGISTRY_VALIDATION_RESULTS.json", "src/stats_utils.py", "src/train_regression.py",
                "src/run_registry.py", "features/figshare_features.csv", "features/figshare_graph_features.csv"}
    listed = {item["path"] for item in contract["artifacts"]}
    if len(listed) != len(contract["artifacts"]):
        raise ValueError("Repeated registry artifact")
    if not required.issubset(listed):
        raise ValueError("Incomplete registry freeze contract")
    hashes = {}
    bindings = {item["path"]: item for item in contract["artifacts"]}
    for item in contract["artifacts"]:
        path = safe_path(root, item["path"])
        if not matches_record(path.read_bytes(), item) or not matches_record(git_bytes(root, "registry-v1", item["path"]), item):
            raise ValueError(f"Registry artifact changed: {item['path']}")
        hashes[item["path"]] = item["sha256"]
    manifest_path = root / "features/v2/MANIFEST.json"
    if canonical_bytes(manifest_path.read_bytes(), mode) != canonical_bytes(git_bytes(root, "features-v2", "features/v2/MANIFEST.json"), mode):
        raise ValueError("Feature manifest differs from features-v2")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    if not set(config.get("freeze_artifacts", [])).issubset(listed):
        raise ValueError("Registry contract omits configured artifacts")
    if mode == "utf8-lf" and "features/v2/MANIFEST.json" not in listed:
        raise ValueError("Registry contract omits feature-manifest binding")
    validation = json.loads((root / "docs/REGISTRY_VALIDATION_RESULTS.json").read_text(encoding="utf-8"))
    if validation.get("acceptance_passed") is not True:
        raise ValueError("Synthetic validation acceptance is not complete; review the recorded failures")
    feature_paths = {item["path"] for item in manifest_records(manifest)}
    expected = {"features/v2/subject_meta.csv"}
    for spec in config["tests"]:
        if spec["table"].startswith("features/v2/"):
            expected.add(spec["table"])
            if "sidecar" in spec:
                expected.add(spec["sidecar"])
    if not expected.issubset(feature_paths):
        raise ValueError("Feature manifest omits registered inputs")
    for item in manifest_records(manifest):
        path = safe_path(root, item["path"])
        bound = bindings.get(item["path"]) if mode == "utf8-lf" else None
        if mode == "utf8-lf" and (not bound or bound.get("source_sha256") != item["sha256"]):
            raise ValueError(f"Feature artifact lacks reviewed byte-hash binding: {item['path']}")
        expected_record = bound or item
        if not matches_record(path.read_bytes(), expected_record) or not matches_record(git_bytes(root, "features-v2", item["path"]), expected_record):
            raise ValueError(f"Feature artifact changed: {item['path']}")
        hashes[item["path"]] = item["sha256"]
    artifact_digest = hashlib.sha256(json.dumps(contract["artifacts"], sort_keys=True).encode()).hexdigest()
    if contract.get("artifact_digest", artifact_digest) != artifact_digest:
        raise ValueError("Registry artifact digest is inconsistent")
    review_file = config["review_file"]
    path = safe_path(root, review_file)
    review = json.loads(path.read_text(encoding="utf-8"))
    if review.get("status") != "approved" or not review.get("reviewer") or not review.get("reviewed_at"):
        raise ValueError(f"Owner review missing: {review_file}")
    if review.get("artifact_digest") != artifact_digest or canonical_bytes(path.read_bytes(), mode) != canonical_bytes(git_bytes(root, "registry-v1", review_file), mode):
        raise ValueError(f"Review does not approve these artifacts: {review_file}")
    hashes["features/v2/MANIFEST.json"] = sha256(manifest_path)
    return hashes


def log_invocation(root, message):
    with (Path(root) / "docs/PROGRESS.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\n- Registry invocation {datetime.now(timezone.utc).isoformat()}: {message}\n")


def save_test(directory, result, ids, features, settings):
    directory.mkdir()
    np.save(directory / "null.npy", result["null"])
    np.save(directory / "bootstrap.npy", result["bootstrap"])
    (directory / "config.json").write_text(json.dumps({"settings": settings, "features": features, "subject_ids": ids}, indent=2) + "\n", encoding="utf-8")
    (directory / "summary.json").write_text(json.dumps(result["summary"], indent=2, allow_nan=False) + "\n", encoding="utf-8")
    output = result["output"]
    if output is not None:
        records = []
        for r in range(output["predictions"].shape[1]):
            for i, subject in enumerate(ids):
                records.append({"subject_id": subject, "repeat": r, "fold": int(output["folds"][i, r]),
                                "prediction": output["predictions"][i, r], "dummy_prediction": output["dummy"][i, r],
                                "target": output["target"][i], "stratum": output["strata"][i]})
        pd.DataFrame(records).to_csv(directory / "oof.csv", index=False)
        pd.DataFrame(result["repeat_metrics"]).to_csv(directory / "repeat_metrics.csv", index=False)
        pd.DataFrame(output["alphas"]).to_csv(directory / "selected_alphas.csv", index=False)


def run(mode, run_id, *, root=ROOT, rerun_reason=None):
    root = Path(root)
    if mode not in ("smoke", "real") or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid mode or run ID")
    if mode == "real":
        # Log attempts, including guard failures, without reading any labels.
        log_invocation(root, f"START real run={run_id}; rerun_reason={rerun_reason!r}")
        try:
            hashes = verify_freeze(root)
        except Exception as exc:
            log_invocation(root, f"REFUSED real run={run_id}: {type(exc).__name__}: {exc}")
            raise
    else:
        hashes = {}
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    if [s["id"] for s in config["tests"]] != [f"T{i}" for i in range(1, 10)]:
        raise ValueError("The frozen family must contain exactly T1-T9 in order")
    settings = dict(config["settings"])
    if mode == "smoke":
        smoke = config["validation"]["smoke"]
        settings.update({k: smoke[k] for k in ("permutations", "outer_repeats", "bootstrap_resamples")})
    base = root / "results/v2" / ("runs" if mode == "real" else "smoke")
    previous = list(base.glob("*/run.json")) if base.exists() else []
    if mode == "real" and previous and not rerun_reason:
        log_invocation(root, f"REFUSED real run={run_id}: rerun requires a documented bug reason")
        raise ValueError("Rerun requires --rerun-reason and preservation of prior runs")
    directory = base / run_id
    directory.mkdir(parents=True, exist_ok=False)
    metadata = {"mode": mode, "run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "running", "input_hashes": hashes, "config_sha256": sha256(root / CONFIG),
                "registry_sha256": sha256(root / "docs/ANALYSIS_REGISTRY.md"), "settings": settings,
                "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                "sklearn": sklearn.__version__, "rerun_reason": rerun_reason,
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
    (directory / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    rows = []
    for number, spec in enumerate(config["tests"], 1):
        try:
            seed = config["validation"]["smoke"]["shuffle_seed_base"] + number if mode == "smoke" else None
            X, y, strata, ids, features = load_analysis(root, spec, shuffle_seed=seed)
            hashes[spec["table"]] = sha256(root / spec["table"])
            hashes["features/v2/subject_meta.csv"] = sha256(root / "features/v2/subject_meta.csv")
            result = evaluate(X, y, strata, settings, number, spec["kind"])
            save_test(directory / spec["id"], result, ids, features, settings)
            rows.append({"test_id": spec["id"], "kind": spec["kind"], **result["summary"], "failure_reason": ""})
        except Exception as exc:
            rows.append({"test_id": spec["id"], "kind": spec["kind"], "failure_reason": f"{type(exc).__name__}: {exc}"})
        print(f"{mode} {spec['id']}: {'FAILED' if rows[-1]['failure_reason'] else 'completed'}", flush=True)
    failed = any(row["failure_reason"] for row in rows)
    # Failed tests retain their slots (placeholder p=1); inference is withheld.
    adjusted = holm_adjust([row.get("p_raw", 1) for row in rows])
    for row, p in zip(rows, adjusted):
        row["p_holm"] = None if row["failure_reason"] else float(p)
        rho = row.get("rho", 0)
        effect = abs(rho) if row["kind"] == "association" else rho
        row["decision"] = ("development_only" if mode == "smoke" else "withheld_incomplete_family" if failed else
                           "signal_detected" if p < settings["holm_alpha"] and effect >= settings["rho_threshold"] else "no_effect_detected")
        if mode == "real" and not failed and row["kind"] == "ridge" and row["decision"] == "signal_detected":
            spec = next(s for s in config["tests"] if s["id"] == row["test_id"])
            X, y, strata, ids, features = load_analysis(root, spec)
            model, alpha = fit_ridge(X, y, settings)
            model_dir = root / "results/v2/models" / run_id
            model_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, model_dir / f"{row['test_id']}.joblib")
            (model_dir / f"{row['test_id']}.meta.json").write_text(json.dumps({"test": spec, "alpha": alpha,
                "feature_order": features, "subject_ids": ids, "input_hashes": hashes}, indent=2) + "\n", encoding="utf-8")
    table = pd.DataFrame(rows)
    table.to_csv(directory / "registry_results.csv", index=False)
    metadata.update(status="failed" if failed else "complete", input_hashes=hashes, finished_at=datetime.now(timezone.utc).isoformat())
    (directory / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if mode == "real":
        # Each prior version remains in its immutable run directory.
        table.to_csv(root / "results/v2/registry_results.csv", index=False)
        log_invocation(root, f"{metadata['status'].upper()} real run={run_id}; outputs={directory.relative_to(root)}")
    if failed:
        raise RuntimeError(f"Registry family incomplete; inspect {directory}")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "real"), default="smoke")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--rerun-reason")
    args = parser.parse_args()
    print(run(args.mode, args.run_id, rerun_reason=args.rerun_reason))
