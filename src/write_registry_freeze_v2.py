"""Prepare/check Group B's content snapshot. Does not commit, tag or approve."""
import argparse
import hashlib
import json
from pathlib import Path
try:
    from .freeze_io_v2 import content_hash, matches_record, feature_records
except ImportError:
    from freeze_io_v2 import content_hash, matches_record, feature_records

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/REGISTRY_FREEZE_MANIFEST.json'


def build(root=ROOT):
    root = Path(root).resolve()
    config = json.loads((root / 'configs/registry_v1.json').read_text(encoding='utf-8'))
    records = {}
    for relative in config['freeze_artifacts']:
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Artifact path escapes repository')
        if relative in records:
            raise ValueError('Duplicate configured artifact')
        records[relative] = {'path': relative, 'hash_mode': 'utf8-lf',
                             'sha256': content_hash(path.read_bytes(), 'utf8-lf')}
    feature_manifest = root / 'features/v2/MANIFEST.json'
    records['features/v2/MANIFEST.json'] = {'path': 'features/v2/MANIFEST.json', 'hash_mode': 'utf8-lf',
                                           'sha256': content_hash(feature_manifest.read_bytes(), 'utf8-lf')}
    old_path = root / 'docs/REGISTRY_FREEZE_MANIFEST.json'
    previous = json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    old_records = {item['path']: item for item in previous.get('artifacts', [])}
    for item in feature_records(json.loads(feature_manifest.read_text(encoding='utf-8'))):
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Feature artifact path escapes repository')
        data = path.read_bytes()
        # First bind to Group A's existing raw bytes. Later LF/CRLF checkouts
        # may reuse an already-reviewed normalization binding, never arbitrary edits.
        prior = old_records.get(item['path'], {})
        verified = content_hash(data) == item['sha256']
        if not verified:
            verified = (prior.get('hash_mode') == 'utf8-lf' and prior.get('source_sha256') == item['sha256']
                        and matches_record(data, prior))
        if not verified:
            raise ValueError(f"Feature bytes do not match Group A provenance: {item['path']}")
        records[item['path']] = {'path': item['path'], 'hash_mode': 'utf8-lf',
                                 'sha256': content_hash(data, 'utf8-lf'), 'source_sha256': item['sha256']}
    records = list(records.values())
    digest = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return {'schema_version': 2, 'status': 'SNAPSHOT ONLY; owner review and tags required',
            'hash_policy': 'UTF-8 content with CRLF converted to LF only; Group A raw hashes retained as source_sha256.',
            'artifact_digest': digest, 'artifacts': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--stdout', action='store_true')
    args = parser.parse_args()
    snapshot = build()
    if args.check:
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != snapshot:
            raise SystemExit('Registry snapshot is stale; regenerate and obtain a new owner review')
        print('Registry snapshot matches all artifacts; this is not owner approval')
    elif args.stdout:
        print(json.dumps(snapshot, indent=2))
    else:
        if OUTPUT.exists():
            old_bytes = OUTPUT.read_bytes()
            old_digest = hashlib.sha256(old_bytes).hexdigest()
            archive = ROOT / 'docs/archive' / f'REGISTRY_FREEZE_MANIFEST_{old_digest}.json'
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archive.exists():
                archive.write_bytes(old_bytes)
            elif archive.read_bytes() != old_bytes:
                raise SystemExit('Archive collision; refusing overwrite')
        OUTPUT.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(OUTPUT)
        print('Review snapshot regenerated; obtain owner approval for digest ' + snapshot['artifact_digest'])
