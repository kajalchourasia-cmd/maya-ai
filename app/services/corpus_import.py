"""Verified, draft-only corpus mapping into the existing Stage 2/5 schema.

No provider calls, publication, permission bypass or fabricated review decisions.
The operator CLI is separately restricted to the isolated local Docker database.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from uuid import NAMESPACE_URL, uuid5

from app.schemas.ingestion import IngestionRun, EvidenceReviewDecision, EvidenceReviewTask, ParsedBlock
from app.services.content_validation import validate_bundle
from app.services.foundation import fingerprint, review_subject
from app.services.public_ingestion import _best_anchor
from scripts.validate_content import load_bundle


TABLE_KEYS = {
    'content_releases': ('id',), 'public_sources': ('release_id', 'source_id'),
    'source_artifacts': ('id',), 'source_blocks': ('release_id', 'block_id'),
    'ingestion_runs': ('release_id', 'run_id'), 'evidence_review_tasks': ('release_id', 'task_id'),
    'evidence_review_decisions': ('id',), 'weekly_profiles': ('release_id', 'profile_id'),
    'guidance_fragments': ('release_id', 'fragment_id'),
    'guideline_chunks': ('release_id', 'chunk_id'),
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_sql(value) -> str:
    # Source text never appears as executable SQL, psql meta-commands or dollar delimiters.
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    return "convert_from(decode('" + raw.hex() + "','hex'),'UTF8')::jsonb"


def checked_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or '\\' in relative or ':' in relative or '..' in path.parts:
        raise ValueError('Unsafe package path')
    result = root.joinpath(*path.parts).resolve()
    if not result.is_relative_to(root.resolve()) or result == root.resolve():
        raise ValueError('Package path escapes its root')
    return result


def verified_payloads(root: Path, expected_manifest_hash: str) -> tuple[dict[str, bytes], str]:
    manifest_bytes = (root / 'SHA256SUMS.json').read_bytes()
    actual = sha256(manifest_bytes)
    if actual != expected_manifest_hash:
        raise ValueError('Package manifest hash differs from the pinned handoff')
    manifest = json.loads(manifest_bytes)
    if manifest.get('algorithm') != 'SHA-256' or not isinstance(manifest.get('files'), dict):
        raise ValueError('Unsupported discovery manifest')
    payloads = {}
    for name, expected in manifest['files'].items():
        raw = checked_path(root, name).read_bytes()
        if sha256(raw) != expected:
            raise ValueError('Package payload checksum mismatch: ' + name)
        payloads[name] = raw
    return payloads, actual


def candidate_subject(candidate: dict) -> dict:
    return {k: v for k, v in candidate.items()
            if k not in ('candidate_id', 'state', 'review_reasons', 'candidate_checksum')}


def unique_index(items: list[dict], key: str) -> dict:
    indexed = {}
    for item in items:
        if item[key] in indexed:
            raise ValueError('Duplicate ' + key)
        indexed[item[key]] = item
    return indexed


@dataclass
class ImportPlan:
    release_id: str
    corpus_version: str
    manifest_hash: str
    rows: dict[str, list[dict]]
    provenance: dict

    @property
    def import_fingerprint(self) -> str:
        return fingerprint({'rows': self.rows, 'provenance': self.provenance})

    def summary(self) -> dict:
        runs = self.provenance['runs']
        candidates = [c for run in runs for c in run['candidates']]
        return {
            'release_id': self.release_id, 'corpus_version': self.corpus_version,
            'release_status': 'draft', 'import_fingerprint': self.import_fingerprint,
            'package_manifest_sha256': self.manifest_hash,
            'counts': {table: len(rows) for table, rows in self.rows.items()},
            'historical_dry_runs': sum(r['dry_run'] for r in runs),
            'parsed_blocks_reported': sum(r['parsed_block_count'] for r in runs),
            'preserved_block_bodies': len(self.rows['source_blocks']),
            'real_embeddings_imported': 0,
            'published_rows_created': 0,
            'publication_approval_inferred': False,
            'current_source_currency_verified': False,
            'candidate_states': sorted(set(c['state'] for c in candidates)),
            'sources_forbidding_embeddings': [r['artifact']['source_id'] for r in runs
                                              if not r['admission']['may_embed']],
            'empty_profile_count': sum(not p['source_evidence_ids'] for p in self.rows['weekly_profiles']),
            'next_requirement': 'Review/currency/coverage and permitted embeddings; then verify the live retrieval path.',
        }


def build_plan(root: Path, expected_manifest_hash: str) -> ImportPlan:
    payloads, manifest_hash = verified_payloads(root, expected_manifest_hash)
    prefix = 'recovered-artifacts/stage1-audit-v1/'
    run_names = sorted(n for n in payloads if n.startswith(prefix) and n.endswith('.json'))
    if not run_names:
        raise ValueError('No recovered ingestion runs')
    runs = [IngestionRun.model_validate_json(payloads[name]).model_dump(mode='json') for name in run_names]
    # The authoring loader is an existing project contract; every file it reads
    # must be manifest-backed, and its bytes must remain unchanged through parsing.
    data = root / 'public-authoring/data'
    required = ('guidelines/source_registry.csv', 'guidelines/section_manifest.jsonl',
                'guidelines/guidance_fragments.jsonl', 'weekly/weekly_content_manifest.jsonl')
    for name in required:
        if 'public-authoring/data/' + name not in payloads:
            raise ValueError('Unverified authoring input')
    bundle = load_bundle(data)
    for name in required:
        if (data / name).read_bytes() != payloads['public-authoring/data/' + name]:
            raise ValueError('Authoring input changed during preflight')
    report = validate_bundle(bundle)
    if not report.valid:
        raise ValueError('Authoring integrity failed: ' + '; '.join(report.errors))
    source_map = unique_index([s.model_dump(mode='json') for s in bundle.sources], 'source_id')
    candidate_map = unique_index([c for r in runs for c in r['candidates']], 'evidence_id')
    evidence_map = {e.evidence_id: e for e in bundle.evidence}
    unique_index(runs, 'run_id')
    unique_index([b for r in runs for b in r['governed_blocks']], 'block_id')
    tasks = unique_index([t for r in runs for t in r['review_tasks']], 'task_id')
    ledger = json.loads(payloads['public-authoring/data/reviews/ingestion_decisions.json'])
    decisions = [EvidenceReviewDecision.model_validate_json(json.dumps(d)).model_dump(mode='json') for d in ledger['decisions']]
    # Attach only exact-version decisions. Never rebind a signature to a different candidate.
    for task in tasks.values():
        by_role = {d['role']: d for d in task['decisions']}
        for decision in (d for d in decisions if d['task_id'] == task['task_id']):
            previous = by_role.get(decision['role'])
            if previous and previous != decision:
                raise ValueError('Conflicting review decision')
            by_role[decision['role']] = decision
        task['decisions'] = list(by_role.values())
        EvidenceReviewTask.model_validate_json(json.dumps(task))  # pending stays pending when roles are missing
    if any(d['task_id'] not in tasks for d in decisions):
        raise ValueError('Review ledger references an absent/stale task')
    if len({(d['task_id'], d['role']) for d in decisions}) != len(decisions):
        raise ValueError('Duplicate role decision in review ledger')

    corpus_version = 'recovered-draft-' + manifest_hash[:20]
    release_id = str(uuid5(NAMESPACE_URL, 'maya/corpus/' + corpus_version))
    rows = {table: [] for table in TABLE_KEYS}
    rows['content_releases'].append(dict(id=release_id, corpus_version=corpus_version,
        release_fingerprint=manifest_hash, status='draft', embedding_provider=None,
        embedding_model=None, published_at=None))
    sources_seen = set()
    for run in runs:
        artifact = run['artifact']
        if (not artifact or not run['dry_run'] or run['outcome'] != 'review_required'
                or not run['admission']['may_store'] or run['embeddings']):
            raise ValueError('This importer accepts preserved storage-permitted review-required dry runs only')
        sid = artifact['source_id']
        source = source_map[sid]
        if sid in sources_seen:
            raise ValueError('Multiple historical versions require an explicit version migration')
        sources_seen.add(sid)
        if (source['status'] in ('excluded', 'superseded') or source['reuse_status'] != 'permitted'
                or 'store' not in source['allowed_use'] or not source['content_checksum']):
            raise ValueError('Source storage permission absent or source excluded')
        if source['version_or_last_update'] != artifact['source_version']:
            raise ValueError('Source version conflict')
        governance_checksum = fingerprint(review_subject(source))
        rows['public_sources'].append(dict(source_id=sid, release_id=release_id,
            title=source['title'], publisher=source['publisher'], canonical_url=source['canonical_url'],
            jurisdiction=source['jurisdiction'], source_version=source['version_or_last_update'],
            reuse_status=source['reuse_status'], allowed_use=source['allowed_use'],
            attribution_text=source['attribution_text'], status='review_required',
            content_checksum=source['content_checksum']))
        aid = str(uuid5(NAMESPACE_URL, 'maya/artifact/' + release_id + '/' + sid + '/' + artifact['original_sha256']))
        rows['source_artifacts'].append(dict(id=aid, release_id=release_id, source_id=sid,
            logical_version_id=run['logical_version_id'], original_sha256=artifact['original_sha256'],
            document_type=artifact['document_type'], retrieved_at=artifact['retrieved_at'],
            byte_size=artifact['byte_size'], parser_name=artifact['parser_name'],
            parser_version=artifact['parser_version'], storage_object_path=None))
        blocks = {b['block_id']: b for b in run['governed_blocks']}
        for block in blocks.values():
            row = {k: v for k, v in block.items() if k != 'text'}
            row.update(release_id=release_id, source_artifact_id=aid, original_text=block['text'])
            rows['source_blocks'].append(row)
        rows['ingestion_runs'].append(dict(run_id=run['run_id'], release_id=release_id, logical_version_id=run['logical_version_id'],
            source_id=sid, source_artifact_id=aid, evaluated_at=run['evaluated_at'], dry_run=run['dry_run'],
            outcome=run['outcome'], admission=run['admission'], diff=run['diff'], issues=run['issues']))
        for candidate in run['candidates']:
            if (candidate['state'] != 'review_required' or not candidate['source_anchor_verified']
                    or sha256(candidate['original_text'].encode('utf-8')) != candidate['original_text_sha256']
                    or fingerprint(candidate_subject(candidate)) != candidate['candidate_checksum']):
                raise ValueError('Candidate state, source anchor or checksum mismatch: ' + candidate['evidence_id'])
            evidence = evidence_map[candidate['evidence_id']]
            if (candidate['source_governance_checksum'] != governance_checksum
                    or evidence.source_checksum != source['content_checksum']
                    or evidence.source_version != artifact['source_version']
                    or evidence.text_checksum != candidate['original_text_sha256']):
                raise ValueError('Candidate is not bound to the current preserved source metadata')
            selected_blocks = [ParsedBlock.model_validate_json(json.dumps(blocks[b]))
                               for b in candidate['source_block_ids']]
            anchor_ok, _, _ = _best_anchor(selected_blocks, evidence)
            if evidence.text != candidate['original_text'] or not anchor_ok:
                raise ValueError('Candidate text not found within preserved source blocks')
            scope = candidate['applies_to']
            rows['guideline_chunks'].append(dict(chunk_id='CH-' + candidate['candidate_checksum'][:20],
                release_id=release_id, evidence_id=candidate['evidence_id'], source_id=sid,
                candidate_checksum=candidate['candidate_checksum'], text=candidate['original_text'],
                source_block_ids=candidate['source_block_ids'], stage=scope['stage'], unit=scope['unit'],
                range_start=scope['start'], range_end=scope['end'], jurisdiction=candidate['jurisdiction'],
                domains=candidate['domains'], display_slots=candidate['display_slots'],
                conditions_required=candidate['conditions_required'], conditions_excluded=candidate['conditions_excluded'],
                embedding_provider=None, embedding_model=None, embedding_dimensions=None, embedding=None,
                status='review_required'))
        for task in run['review_tasks']:
            rows['evidence_review_tasks'].append({**{k: v for k, v in task.items() if k != 'decisions'},
                                                 'release_id': release_id, 'run_id': run['run_id']})
            for decision in task['decisions']:
                row = {k: v for k, v in decision.items() if k not in ('candidate_id', 'evidence_id', 'source_id')}
                row['release_id'] = release_id
                row['id'] = str(uuid5(NAMESPACE_URL, 'maya/review/' + release_id + '/' + task['task_id'] + '/' + decision['role']))
                rows['evidence_review_decisions'].append(row)
    for item in bundle.fragments:
        fragment = item.model_dump(mode='json')
        if item.status != 'draft':
            raise ValueError('Publication or reviewed state requires a separate approved importer')
        block_ids = sorted({b for e in item.evidence_span_ids for b in candidate_map[e]['source_block_ids']})
        scope = fragment['applies_to']
        rows['guidance_fragments'].append(dict(fragment_id=item.fragment_id, release_id=release_id,
            domain=item.domain, text=item.text, stage=scope['stage'], unit=scope['unit'],
            range_start=scope['start'], range_end=scope['end'], jurisdiction=item.jurisdiction,
            evidence_ids=item.evidence_span_ids, source_block_ids=block_ids,
            conditions_required=item.conditions_required, conditions_excluded=item.conditions_excluded,
            presentation=item.presentation, status='draft', content_checksum=fingerprint(fragment)))
    for item in bundle.profiles:
        profile = item.model_dump(mode='json')
        if item.status != 'draft':
            raise ValueError('Publication or reviewed state requires a separate approved importer')
        if any(e not in candidate_map for e in item.source_evidence_ids):
            raise ValueError('Profile has unrecovered evidence')
        scope = profile['applies_to']
        rows['weekly_profiles'].append(dict(profile_id=item.profile_id, release_id=release_id,
            stage=scope['stage'], unit=scope['unit'], range_start=scope['start'], range_end=scope['end'],
            jurisdiction=item.jurisdiction, hero=profile['hero'], card_slots=profile['card_slots'],
            guidance_fragment_ids=item.guidance_fragment_ids, source_evidence_ids=item.source_evidence_ids,
            content_priority=item.content_priority, status='draft', content_checksum=fingerprint(profile)))
    provenance = dict(manifest_sha256=manifest_hash, verified_payload_count=len(payloads),
        runs=runs, review_ledger=ledger, authoring=bundle.model_dump(mode='json'),
        limitations=['Historical dry runs remain historical dry runs.',
                    'Original PDF/HTML bytes are not imported or claimed restored.',
                    'No embeddings or published release are created by this importer.'])
    return ImportPlan(release_id, corpus_version, manifest_hash, rows, provenance)


def import_sql(plan: ImportPlan, *, commit: bool = True, fail_after_table: str | None = None) -> str:
    if fail_after_table is not None and fail_after_table not in TABLE_KEYS:
        raise ValueError('Unknown failure probe table')
    statements = ["begin; set local statement_timeout='45s'; set local lock_timeout='5s';",
                  "select pg_advisory_xact_lock(1609202601);"]
    for table, keys in TABLE_KEYS.items():
        for row in plan.rows[table]:
            # Columns come from our mapper, never from package-provided SQL identifiers.
            if any(not k.replace('_', '').isalnum() for k in row):
                raise ValueError('Unsafe column name')
            columns = ','.join(row)
            match = ' and '.join(f"t.{key} is not distinct from incoming.{key}" for key in keys)
            statements.append(f"""do $import$
declare expected jsonb := {json_sql(row)}; incoming public.{table}; existing jsonb;
begin
  incoming := jsonb_populate_record(null::public.{table}, expected);
  select to_jsonb(t) into existing from public.{table} t where {match};
  if existing is not null and exists(select 1 from jsonb_each(expected) e where existing->e.key is distinct from e.value) then
    raise exception 'CORPUS_IMPORT_CONFLICT:{table}';
  end if;
  if existing is null then
    insert into public.{table} ({columns}) select {columns}
      from jsonb_populate_record(null::public.{table}, expected);
  end if;
end; $import$;""")
        if table == fail_after_table:
            statements.append("do $probe$ begin raise exception 'CORPUS_IMPORT_INJECTED_FAILURE'; end; $probe$;")
    receipt = dict(import_fingerprint=plan.import_fingerprint, release_id=plan.release_id,
                   package_manifest_sha256=plan.manifest_hash, payload=plan.provenance)
    statements.append(f"""do $receipt$
declare expected jsonb := {json_sql(receipt)}; existing jsonb;
begin
  select to_jsonb(r) into existing from private.corpus_import_receipts r
    where import_fingerprint=expected->>'import_fingerprint';
  if existing is not null and exists(select 1 from jsonb_each(expected) e where existing->e.key is distinct from e.value) then
    raise exception 'CORPUS_IMPORT_RECEIPT_CONFLICT';
  end if;
  if existing is null then
    insert into private.corpus_import_receipts(import_fingerprint,release_id,package_manifest_sha256,payload)
    select import_fingerprint,release_id,package_manifest_sha256,payload
      from jsonb_populate_record(null::private.corpus_import_receipts,expected);
  end if;
end; $receipt$;""")
    statements.append('commit;' if commit else 'rollback;')
    return '\n'.join(statements)
