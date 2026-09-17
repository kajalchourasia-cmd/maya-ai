"""Read-only recovery integrity checks. No network, decryption, restore or provider calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

DEFAULT_CATALOGUE = Path(__file__).resolve().parents[1] / 'data/recovery/private-runtime-20260917.json'


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def valid_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def check_archive(path: Path, catalogue: dict) -> dict:
    expected = catalogue.get('archive_sha256')
    size = catalogue.get('archive_bytes')
    if not valid_digest(expected) or type(size) is not int or size < 1:
        raise ValueError('Invalid catalogue')
    if path.is_symlink() or not path.is_file():
        raise ValueError('Archive must be a regular file')
    if path.stat().st_size != size or sha256_file(path) != expected:
        raise ValueError('Archive size or checksum mismatch')
    return {'archive_checksum_matches': True, 'bytes_verified': size, 'decrypted': False,
            'database_restored': False, 'network_used': False}


def safe_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe manifest path')
    parts = relative.split('/')
    if PurePosixPath(relative).is_absolute() or any(part in ('', '.', '..') for part in parts):
        raise ValueError('Unsafe manifest path')
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Symlink or junction in payload')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes payload')
    return path


def check_payload(root: Path, catalogue: dict) -> dict:
    if root.is_symlink() or getattr(root, 'is_junction', lambda: False)() or not root.is_dir():
        raise ValueError('Payload must be a regular directory')
    manifest_path = safe_path(root, 'MANIFEST.json')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    entries = manifest.get('files')
    if not isinstance(entries, list) or not entries or len(entries) != catalogue.get('payload_files'):
        raise ValueError('Unexpected manifest file count')
    if manifest.get('source_commit') != catalogue.get('snapshot_code_commit'):
        raise ValueError('Unexpected code snapshot')
    expected = set()
    casefolded = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid manifest entry')
        relative = entry.get('path')
        path = safe_path(root, relative)
        if relative == 'MANIFEST.json' or relative.casefold() in casefolded:
            raise ValueError('Duplicate or reserved manifest path')
        expected.add(relative)
        casefolded.add(relative.casefold())
        size = entry.get('bytes')
        digest = entry.get('sha256')
        if type(size) is not int or size < 0 or not valid_digest(digest):
            raise ValueError('Invalid manifest metadata')
        if not path.is_file() or path.stat().st_size != size or sha256_file(path) != digest:
            raise ValueError('Missing or changed payload file')
    actual = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root).as_posix()
        safe_path(root, relative)
        if path.is_file():
            actual.add(relative)
    if actual != expected | {'MANIFEST.json'}:
        raise ValueError('Unexpected payload files')
    return {'payload_checksums_match': True, 'files_verified': len(entries),
            'database_restored': False, 'network_used': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--archive', type=Path)
    target.add_argument('--payload', type=Path)
    parser.add_argument('--catalogue', type=Path, default=DEFAULT_CATALOGUE)
    args = parser.parse_args()
    try:
        catalogue = json.loads(args.catalogue.read_text(encoding='utf-8'))
        if not isinstance(catalogue, dict) or catalogue.get('schema_version') != 1:
            raise ValueError('Unsupported catalogue')
        result = check_archive(args.archive, catalogue) if args.archive else check_payload(args.payload, catalogue)
        print(json.dumps({'valid': True, **result}, indent=2))
        return 0
    except (OSError, ValueError, TypeError, AttributeError):
        # No paths, file contents or underlying exception text can disclose secrets.
        print(json.dumps({'valid': False, 'message': 'Recovery check failed: inspect paths, catalogue and integrity privately; nothing restored.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
