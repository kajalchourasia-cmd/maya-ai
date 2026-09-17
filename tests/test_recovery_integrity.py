"""Synthetic-file tests only; no real backups, secrets, Docker or network required."""
import hashlib
import json

import pytest

from scripts.check_maya_recovery import check_archive, check_payload, safe_path


@pytest.fixture
def payload(tmp_path):
    root = tmp_path / 'payload'
    root.mkdir()
    data = b'synthetic recovery content'
    (root / 'record.txt').write_bytes(data)
    manifest = {'source_commit': 'fixture-commit', 'files': [
        {'path': 'record.txt', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}
    (root / 'MANIFEST.json').write_text(json.dumps(manifest))
    catalogue = {'snapshot_code_commit': 'fixture-commit', 'payload_files': 1}
    return root, manifest, catalogue


def test_archive_hash_and_size(tmp_path):
    path = tmp_path / 'fixture.maya'
    path.write_bytes(b'synthetic archive')
    catalogue = {'archive_bytes': path.stat().st_size, 'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    assert check_archive(path, catalogue)['archive_checksum_matches']
    path.write_bytes(b'Synthetic archive')
    with pytest.raises(ValueError):
        check_archive(path, catalogue)


def test_payload_checks_all_files(payload):
    root, _, catalogue = payload
    assert check_payload(root, catalogue)['files_verified'] == 1


@pytest.mark.parametrize('change', ['missing', 'changed', 'extra', 'bad_commit', 'duplicate'])
def test_payload_rejects_mismatch(payload, change):
    root, manifest, catalogue = payload
    if change == 'missing':
        (root / 'record.txt').unlink()
    elif change == 'changed':
        (root / 'record.txt').write_text('changed fixture content')
    elif change == 'extra':
        (root / 'extra.txt').write_text('extra fixture file')
    elif change == 'bad_commit':
        manifest['source_commit'] = 'different-fixture'
    elif change == 'duplicate':
        manifest['files'].append(dict(manifest['files'][0]))
        catalogue['payload_files'] = 2
    (root / 'MANIFEST.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        check_payload(root, catalogue)


@pytest.mark.parametrize('relative', ['../escape', '/absolute', 'C:/absolute', 'a\\b', 'a/../b', 'a//b', './a', 'file:stream', ''])
def test_unsafe_paths_rejected(tmp_path, relative):
    with pytest.raises(ValueError):
        safe_path(tmp_path, relative)


def test_symlink_rejected(payload, tmp_path):
    root, _, catalogue = payload
    target = tmp_path / 'outside.txt'
    target.write_text('outside fixture')
    (root / 'record.txt').unlink()
    try:
        (root / 'record.txt').symlink_to(target)
    except OSError:
        pytest.skip('Host does not permit unprivileged symlink creation')
    with pytest.raises(ValueError):
        check_payload(root, catalogue)
