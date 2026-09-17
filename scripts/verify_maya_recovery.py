"""Read-only verification of the exact Step 4B handoff, not its external claims."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile

PACKAGE_NAME = 'MAYA-FINAL-RECOVERY-AND-DEPENDENCY-CHECK-20260916T114006Z'
ZIP_HASH = 'fd6f8bf83997cebe4f2e17ed15518f73878b7721438ae31ba00ef48b1c14ed2c'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_relative(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe recovery path')
    return path


def verify_recovery(archive: Path, root: Path) -> dict:
    if digest(archive.read_bytes()) != ZIP_HASH:
        raise ValueError('Recovery ZIP differs from supplied pinned checksum')
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
        members = [member for member in zipped.infolist() if not member.is_dir()]
        if len({m.filename for m in members}) != len(members):
            raise ValueError('Duplicate ZIP members')
        archived = {}
        for member in members:
            path = safe_relative(member.filename)
            if path.parts[0] != PACKAGE_NAME or len(path.parts) < 2:
                raise ValueError('Unexpected archive root')
            name = '/'.join(path.parts[1:])
            safe_relative(name)
            local = root.joinpath(*PurePosixPath(name).parts).resolve()
            if not local.is_relative_to(root.resolve()):
                raise ValueError('Extracted file escapes root')
            raw = zipped.read(member)
            if local.read_bytes() != raw:
                raise ValueError('Extracted file differs: ' + name)
            archived[name] = raw
    manifest = json.loads(archived['SHA256SUMS.json'])
    expected = {row['path']:row for row in manifest['files']}
    if len(expected) != len(manifest['files']) or set(archived) != set(expected) | {'SHA256SUMS.json'}:
        raise ValueError('Manifest/archive inventory mismatch')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(archived):
        raise ValueError('Unexpected extracted files')
    for name, row in expected.items():
        if digest(archived[name]) != row['sha256'] or len(archived[name]) != row['bytes']:
            raise ValueError('Manifest payload mismatch: ' + name)
    return dict(archive_sha256=ZIP_HASH, zip_crc_passed=True,
        archived_and_extracted_files=len(archived), manifest_payloads_verified=len(expected),
        manifest_file_bound_by_zip_hash=True, no_extra_extracted_files=True,
        source_binaries_present=False, payload_hashes={k:digest(v) for k,v in archived.items()},
        independently_verified_sender_machine=False,
        scope='Archive integrity and exact extracted bytes only; external account/rights claims not independently verified.')
