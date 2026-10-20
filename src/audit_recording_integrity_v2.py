"""Compare paired raw EDF signals and whitelisted non-outcome metadata only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import mne
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def compare_arrays(left, right, channel_names):
    if left.shape != right.shape or left.ndim != 2 or len(channel_names) != len(left):
        raise ValueError("Signals must have matching channels and sample dimensions")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("Nonfinite raw signal")
    rows = []
    for name, a, b in zip(channel_names, left, right):
        equal = a == b
        correlation = float(np.corrcoef(a, b)[0, 1]) if np.ptp(a) and np.ptp(b) else None
        rows.append({"channel": name, "samples": len(a), "equal_samples": int(equal.sum()),
                     "exactly_equal": bool(equal.all()), "pearson_correlation": correlation,
                     "max_absolute_difference_in_mne_units": float(np.max(np.abs(a-b)))})
    return rows


def normalized(value):
    return " ".join(str(value).strip().casefold().split())


def audit():
    config_path = ROOT / "configs/recording_integrity_v2.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    fields = config["metadata_fields"]
    # usecols prevents clinical outcome fields from being read into either frame.
    source = pd.read_csv(ROOT / config["participants"], sep="\t", dtype=str,
                         usecols=["Participant_ID", *fields]).fillna("").set_index("Participant_ID", verify_integrity=True)
    meta = pd.read_csv(ROOT / config["subject_meta"], dtype=str,
                       usecols=["subject_id", *fields.values()]).fillna("").set_index("subject_id", verify_integrity=True)
    report = {"date": datetime.now(timezone.utc).isoformat(), "mne_version": mne.__version__,
              "scope": "Exact decoded sample comparison for every signal channel, without filtering, resampling or alignment search; non-outcome metadata only.",
              "config_sha256": sha256(config_path), "source_sha256": sha256(Path(__file__)),
              "metadata_hashes": {p: sha256(ROOT / p) for p in (config["participants"], config["subject_meta"])}, "pairs": []}
    for subjects in config["pairs"]:
        paths = [ROOT / config["edf_template"].format(subject=s) for s in subjects]
        recordings = [mne.io.read_raw_edf(path, preload=False, verbose="ERROR") for path in paths]
        left, right = recordings
        same_names = set(left.ch_names) == set(right.ch_names)
        comparable = bool(same_names and left.n_times == right.n_times and left.info["sfreq"] == right.info["sfreq"])
        pair = {"subjects": subjects, "recordings": [{"path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path), "channels": raw.ch_names, "channel_types": raw.get_channel_types(),
                "sfreq": float(raw.info["sfreq"]), "samples": int(raw.n_times)} for path, raw in zip(paths, recordings)],
                "same_channel_names": same_names, "same_channel_order": left.ch_names == right.ch_names,
                "comparable_all_channels": comparable, "metadata": {}, "source_vs_subject_meta": {}}
        pair["files_byte_identical"] = pair["recordings"][0]["sha256"] == pair["recordings"][1]["sha256"]
        for field, destination in fields.items():
            values = [source.loc[s, field] for s in subjects]
            pair["metadata"][destination] = {"values": values, "match": all(values) and normalized(values[0]) == normalized(values[1])}
            pair["source_vs_subject_meta"][destination] = {
                s: {"source": source.loc[s, field], "stored": meta.loc[s, destination],
                    "match": normalized(source.loc[s, field]) == normalized(meta.loc[s, destination])} for s in subjects}
        if comparable:
            a, b = left.get_data(), right.get_data(picks=left.ch_names)
            pair["channels"] = compare_arrays(a, b, left.ch_names)
            pair["all_decoded_samples_exactly_equal"] = all(row["exactly_equal"] for row in pair["channels"])
            pair["decoded_float64_bitwise_equal"] = a.tobytes() == b.tobytes()
            core = [row for row in pair["channels"] if row["channel"] in config["core_channels"]]
            pair["core_decoded_samples_exactly_equal"] = len(core) == len(config["core_channels"]) and all(row["exactly_equal"] for row in core)
        else:
            pair["channels"] = []
            pair["all_decoded_samples_exactly_equal"] = None
        for raw in recordings:
            raw.close()
        report["pairs"].append(pair)
        print(json.dumps({"subjects": subjects, "channel_count": len(pair["channels"]),
                          "all_samples_equal": pair["all_decoded_samples_exactly_equal"],
                          "metadata_matches": {k: v["match"] for k, v in pair["metadata"].items()}}), flush=True)
    report["interpretation"] = "Signal identity/similarity does not establish participant identity. Metadata disagreement requires source-data review. Retain the user-approved subject IDs/splits; disclose unresolved dependence."
    (ROOT / config["output"]).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    audit()
