"""Explicit LF-only text normalization for portable reviewed artifact hashes."""
import hashlib


def canonical_bytes(data, mode="bytes"):
    if mode == "bytes":
        return data
    if mode != "utf8-lf":
        raise ValueError(f"Unknown artifact hash mode: {mode}")
    data.decode("utf-8")  # Reject binary/invalid text; do not hide encoding changes.
    if b"\x00" in data:
        raise ValueError("NUL in a text artifact")
    return data.replace(b"\r\n", b"\n")


def content_hash(data, mode="bytes"):
    return hashlib.sha256(canonical_bytes(data, mode)).hexdigest()


def matches_record(data, record):
    return content_hash(data, record.get("hash_mode", "bytes")) == record["sha256"]


def feature_records(manifest):
    records = []
    for item in manifest["label_free_feature_tables"]:
        records.append({"path": item["path"], "sha256": item["sha256"]})
        if isinstance(item.get("sidecar"), dict):
            records.append(item["sidecar"])
    return records + manifest["configs"] + manifest["implementation_sources"]
