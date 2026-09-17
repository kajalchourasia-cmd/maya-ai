"""Import the verified recovered corpus into Maya's isolated LOCAL database.

No hosted URL, provider call, approval, publication or application-mode change.
The execute action backs up first, migrates, tests rollback, imports and verifies.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.corpus_import import TABLE_KEYS, build_plan, import_sql, json_sql, sha256
from scripts.maya_local_database import prepare, cli, safe_output

DB = 'supabase_db_maya-kajal-local'
MANIFEST_HASH = '2ebd508df90d7bc32055de176e2e081330a645df5ba83029fffde0f5ad2396b7'
OUTPUT = ROOT / 'reports/local/corpus-import'


def require_local_database() -> None:
    result = subprocess.run(['docker', 'inspect', DB], capture_output=True, text=True, check=True, timeout=20)
    container = json.loads(result.stdout)[0]
    ports = container['NetworkSettings']['Ports'].get('5432/tcp') or []
    if (container['Config'].get('Labels', {}).get('com.supabase.cli.project') != 'maya-kajal-local'
            or not container['State']['Running'] or not ports
            or any(p['HostIp'] != '127.0.0.1' for p in ports)):
        raise RuntimeError('Require the isolated, running, loopback-only Maya database')


def sql(query: str, expected_error: str | None = None) -> list[dict]:
    result = subprocess.run(['docker', 'exec', '-i', DB, 'psql', '-X', '-q', '-A', '-t',
                             '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'postgres'],
                            input=query, capture_output=True, text=True, encoding='utf-8', timeout=120)
    if expected_error:
        if result.returncode == 0 or expected_error not in result.stderr:
            raise RuntimeError('Expected transaction failure was not observed: ' + expected_error)
        return []
    if result.returncode:
        # Do not print SQL payloads, source bodies, credentials or full statements.
        error = next((line for line in result.stderr.splitlines() if 'ERROR:' in line), 'SQL failed')
        raise RuntimeError(safe_output(error[:240]))
    return [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]


def snapshot() -> dict:
    relations = ['public.' + table for table in TABLE_KEYS] + ['private.corpus_import_receipts']
    pieces = []
    for relation in relations:
        pieces.append("'" + relation + "', (select jsonb_build_object('count',count(*),'checksum',"
                      "md5(coalesce(string_agg(to_jsonb(t)::text, '' order by to_jsonb(t)::text),'')))"
                      ' from ' + relation + ' t)')
    return sql('select jsonb_build_object(' + ','.join(pieces) + ');')[0]


def backup() -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / ('before-import-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.dump')
    with path.open('xb') as destination:
        result = subprocess.run(['docker', 'exec', DB, 'pg_dump', '-Fc', '-U', 'postgres', '-d', 'postgres'],
                                stdout=destination, stderr=subprocess.PIPE, timeout=120)
    if result.returncode or path.stat().st_size == 0:
        raise RuntimeError('Local pre-import backup failed; no migration or import attempted')
    # Validate archive readability without restoring or replacing any data.
    checked = subprocess.run(['docker', 'exec', '-i', DB, 'pg_restore', '--list'],
                             input=path.read_bytes(), capture_output=True, timeout=30)
    if checked.returncode:
        raise RuntimeError('Backup archive validation failed')
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha256(path.read_bytes()), archive_list_valid=True)


def verify(plan) -> dict:
    rid = plan.release_id  # generated UUID, never package SQL
    values = []
    for table, rows in plan.rows.items():
        for row in rows:
            keys = ' and '.join(f"to_jsonb(t)->'{key}' = expected->'{key}'" for key in TABLE_KEYS[table])
            values.append(f"(select count(*)=1 and bool_and(not exists(select 1 from jsonb_each(expected) field "
                          f"where to_jsonb(t)->field.key is distinct from field.value)) "
                          f"from public.{table} t, (select {json_sql(row)} as expected) e where {keys})")
    checks = sql('select jsonb_build_object(\'all_mapped_rows_exact\', ' + ' and '.join(values) + ');')[0]
    receipt = sql(f"select jsonb_build_object('receipt_exact',count(*)=1 and bool_and(payload={json_sql(plan.provenance)})) "
                  f"from private.corpus_import_receipts where import_fingerprint='{plan.import_fingerprint}';")[0]
    checks.update(receipt)
    checks.update(sql(f"""select jsonb_build_object(
      'all_55_chunks_review_required',(select count(*)=55 and bool_and(status='review_required' and embedding is null)
        from public.guideline_chunks where release_id='{rid}'),
      'all_55_tasks_still_pending',(select count(*)=55 and bool_and(status='pending')
        from public.evidence_review_tasks where release_id='{rid}'),
      'release_still_draft',(select status='draft' from public.content_releases where id='{rid}'),
      'no_original_document_bytes_claimed',(select bool_and(storage_object_path is null) from public.source_artifacts where release_id='{rid}'));
    """)[0])
    for role in ('anon', 'authenticated'):
        visible = sql('begin; set local role ' + role + '; select jsonb_build_object(' + ','.join(
            f"'{table}',(select count(*) from public.{table} where " +
            (f"id='{rid}'" if table == 'content_releases' else f"release_id='{rid}'") + ')'
            for table in ('content_releases', 'public_sources', 'source_blocks', 'weekly_profiles', 'guidance_fragments', 'guideline_chunks'))
            + '); rollback;')[0]
        checks[role + '_cannot_read_drafts'] = all(value == 0 for value in visible.values())
        sql(f'begin; set local role {role}; select count(*) from private.corpus_import_receipts; rollback;',
            expected_error='permission denied')
        checks[role + '_cannot_read_operator_receipt'] = True
    # A genuine source-bearing SQL search, explicitly in the operator review lane.
    # This is not the published retrieval gateway or an LLM-generated answer.
    search = sql(f"""select jsonb_build_object('operator_fts_results',coalesce(jsonb_agg(r),'[]'::jsonb)) from (
      select c.evidence_id,c.source_id,s.canonical_url,c.source_block_ids,c.status,
        (select count(*)=cardinality(c.source_block_ids) from public.source_blocks b
          where b.block_id=any(c.source_block_ids) and b.release_id=c.release_id and b.source_id=c.source_id) as preserved_anchor_exists
      from public.guideline_chunks c join public.public_sources s on s.source_id=c.source_id and s.release_id=c.release_id
      where c.release_id='{rid}' and c.stage='pregnancy' and c.range_start<=26 and c.range_end>=26
        and c.search_vector @@ websearch_to_tsquery('english','food OR exercise')
      order by c.evidence_id limit 6) r;
    """)[0]['operator_fts_results']
    checks['operator_source_search_has_anchored_results'] = bool(search) and all(x['preserved_anchor_exists'] for x in search)
    if not all(checks.values()):
        raise RuntimeError('Verification failed: ' + ', '.join(k for k,v in checks.items() if not v))
    return dict(checks=checks, operator_review_lane_search=search,
                published_retrieval_verified=False, product_rag_verified=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'execute', 'verify'))
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan(args.package.resolve(), MANIFEST_HASH)
    report = dict(verified_at_utc=datetime.now(timezone.utc).isoformat(), summary=plan.summary(),
                  provider_calls=0, hosted_database_modified=False)
    if args.action == 'preflight':
        print(json.dumps(report, indent=2))
        return
    require_local_database()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.action == 'execute':
        report['backup'] = backup()
        report['prepared'] = prepare()
        migrated = cli('migration', 'up', '--local')
        if migrated.returncode:
            raise RuntimeError('Local migration failed: ' + safe_output(migrated.stderr)[-400:])
        before = snapshot()
        sql(import_sql(plan, fail_after_table='source_blocks'), expected_error='CORPUS_IMPORT_INJECTED_FAILURE')
        if snapshot() != before:
            raise RuntimeError('Injected-failure rollback did not preserve the database')
        report['failed_transaction_rolled_back'] = True
        sql(import_sql(plan))
        after = snapshot()
        sql(import_sql(plan))
        if snapshot() != after:
            raise RuntimeError('Repeat import changed stored rows')
        report['repeat_import_no_changes_or_duplicates'] = True
        conflict = deepcopy(plan)
        conflict.rows['guideline_chunks'][0]['text'] += ' INTENTIONAL TRANSACTION CONFLICT TEST'
        sql(import_sql(conflict), expected_error='CORPUS_IMPORT_CONFLICT:guideline_chunks')
        if snapshot() != after:
            raise RuntimeError('Conflict transaction changed stored data')
        report['conflict_rejected_without_overwrite'] = True
        report['before'] = before
        report['after'] = after
    report['verification'] = verify(plan)
    report['pass'] = True
    path = OUTPUT / (args.action + '-verification-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('Report: ' + str(path))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Corpus import stopped: ' + safe_output(str(exc)))
        raise SystemExit(1)
