"""Small defensive unit tests; real database proof is produced by the operator CLI."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.corpus_import import (ImportPlan, TABLE_KEYS, candidate_subject, checked_path,
    import_sql, json_sql, sha256, unique_index, verified_payloads)
from scripts.import_maya_corpus import require_local_database


def package(tmp_path, relative='data/one.json'):
    raw = b'{"preserved":"original source"}'
    target = tmp_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    manifest = json.dumps({'algorithm': 'SHA-256', 'files': {relative: sha256(raw)}}).encode()
    (tmp_path / 'SHA256SUMS.json').write_bytes(manifest)
    return sha256(manifest)


def test_verified_payload_keeps_exact_original_bytes(tmp_path):
    digest = package(tmp_path)
    payloads, actual = verified_payloads(tmp_path, digest)
    assert payloads == {'data/one.json': b'{"preserved":"original source"}'}
    assert actual == digest


def test_changed_manifest_is_not_trusted(tmp_path):
    package(tmp_path)
    with pytest.raises(ValueError, match='manifest hash'):
        verified_payloads(tmp_path, '0' * 64)


def test_changed_payload_fails_even_with_unchanged_manifest(tmp_path):
    digest = package(tmp_path)
    (tmp_path / 'data/one.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='payload checksum'):
        verified_payloads(tmp_path, digest)


@pytest.mark.parametrize('path', ['../outside', 'a/../../outside', '/etc/passwd',
                                 'C:/elsewhere/file', 'a\\b', '.', ''])
def test_package_paths_cannot_escape(tmp_path, path):
    with pytest.raises(ValueError):
        checked_path(tmp_path, path)


def test_missing_payload_fails(tmp_path):
    digest = package(tmp_path)
    (tmp_path / 'data/one.json').unlink()
    with pytest.raises(FileNotFoundError):
        verified_payloads(tmp_path, digest)


def test_duplicate_identity_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        unique_index([{'id': 'same'}, {'id': 'same'}], 'id')


def test_candidate_checksum_covers_evidence_not_derived_review_fields():
    assert candidate_subject({'candidate_id':'c','state':'review_required', 'review_reasons':[],
        'candidate_checksum':'x','original_text':'original','source_block_ids':['b']}) == {
        'original_text':'original','source_block_ids':['b']}


def test_source_text_cannot_become_executable_sql():
    dangerous = {'text': "'); drop table public.guideline_chunks; --\n\\!echo bad\n$import$"}
    encoded = json_sql(dangerous)
    assert 'drop table' not in encoded and '\\!' not in encoded and '$import$' not in encoded
    recovered = json.loads(bytes.fromhex(encoded.split("'")[1]).decode('utf-8'))
    assert recovered == dangerous


def test_non_finite_values_cannot_enter_sql():
    with pytest.raises(ValueError):
        json_sql({'value': float('nan')})


def plan():
    rows = {table: [] for table in TABLE_KEYS}
    rows['public_sources'] = [{'release_id':'r', 'source_id':'s','status':'review_required'}]
    return ImportPlan('r', 'draft', 'a' * 64, rows, {'original': True})


def test_import_is_atomic_conflict_rejecting_and_preserves_review_status():
    sql = import_sql(plan())
    assert sql.startswith('begin;') and sql.endswith('commit;')
    assert 'pg_advisory_xact_lock' in sql and 'CORPUS_IMPORT_CONFLICT:public_sources' in sql
    assert 'update public.' not in sql and 'delete from' not in sql
    assert 't.release_id is not distinct from incoming.release_id' in sql
    assert json_sql(plan().rows['public_sources'][0]) in sql


def test_rollback_and_failure_probes_are_explicit():
    assert import_sql(plan(), commit=False).endswith('rollback;')
    assert 'CORPUS_IMPORT_INJECTED_FAILURE' in import_sql(plan(), fail_after_table='source_blocks')
    with pytest.raises(ValueError, match='Unknown'):
        import_sql(plan(), fail_after_table='any_sql')


def test_import_fingerprint_changes_with_payload_or_provenance():
    original = plan()
    before = original.import_fingerprint
    original.provenance['original'] = False
    assert original.import_fingerprint != before


def test_all_versioned_source_keys_include_release():
    for name in ('public_sources', 'source_blocks', 'ingestion_runs', 'evidence_review_tasks',
                 'weekly_profiles', 'guidance_fragments', 'guideline_chunks'):
        assert 'release_id' in TABLE_KEYS[name]


@pytest.mark.parametrize('change', ['other_project', 'stopped', 'public_port', 'missing_port', 'ok'])
def test_local_operator_cannot_target_unrelated_or_exposed_database(monkeypatch, change):
    container = {'Config': {'Labels': {'com.supabase.cli.project': 'maya-kajal-local'}},
                 'State': {'Running': True},
                 'NetworkSettings': {'Ports': {'5432/tcp': [{'HostIp':'127.0.0.1'}]}}}
    if change == 'other_project':
        container['Config']['Labels']['com.supabase.cli.project'] = 'other'
    elif change == 'stopped':
        container['State']['Running'] = False
    elif change == 'public_port':
        container['NetworkSettings']['Ports']['5432/tcp'][0]['HostIp'] = '0.0.0.0'
    elif change == 'missing_port':
        container['NetworkSettings']['Ports'] = {}
    monkeypatch.setattr('scripts.import_maya_corpus.subprocess.run',
                        lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps([container])))
    if change == 'ok':
        require_local_database()
    else:
        with pytest.raises(RuntimeError, match='isolated'):
            require_local_database()
