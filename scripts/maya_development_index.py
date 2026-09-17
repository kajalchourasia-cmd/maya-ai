"""Local authorised development admission/indexing; no publication or app wiring."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.services.corpus_import import build_plan, verified_payloads, json_sql
from app.services.corpus_preparation import build_preparation
from app.services.corpus_expansion import build_expansion
from app.services.development_corpus import (build_development_packet, validate_packet,
    bounded_inputs, validate_saved_vectors, development_import_sql, development_vector_sql,
    AUTHORIZATION, MODEL, DIMENSIONS, ENDPOINT, PRICE_PER_MILLION, RESERVATION_USD)
from app.services.embeddings import OpenAICompatibleEmbeddingProvider
from app.services.foundation import fingerprint
from scripts.import_maya_corpus import MANIFEST_HASH, require_local_database, sql, verify, snapshot, backup
from scripts.maya_local_database import prepare, cli

OUTPUT = ROOT/'reports/local/development-index'
TABLES = ('development_corpus_batches','development_evidence','development_vectors')


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def isolation_check():
    checks = {}
    for role in ('anon','authenticated','service_role'):
        for table in TABLES:
            sql(f'begin; set local role {role}; select count(*) from private.{table}; rollback;',
                expected_error='permission denied')
            checks[role+'/'+table] = True
    return checks


def stored_packet_check(packet):
    key = packet['packet_checksum']
    result = sql(f"""select jsonb_build_object('batch',(select payload from private.development_corpus_batches
      where packet_checksum='{key}'),'records',(select coalesce(jsonb_agg(payload order by evidence_id),'[]'::jsonb)
      from private.development_evidence where packet_checksum='{key}'));""")[0]
    if result['batch']!=packet or result['records']!=packet['records']:
        raise ValueError('Stored development evidence differs from source-bound packet')
    return dict(exact_batch_and_records=True,record_count=len(result['records']))


def dev_counts(packet):
    key = packet['packet_checksum']
    return sql('select jsonb_build_object('+','.join(
        f"'{table}',(select count(*) from private.{table} where packet_checksum='{key}')" for table in TABLES)+');')[0]


def conflict_checks(packet, saved=None):
    """Alter a value only inside a transaction that MUST fail and roll back."""
    key=packet['packet_checksum']
    perturb=f"""update private.development_evidence set payload=jsonb_set(payload,'{{text}}',
        to_jsonb('TRANSACTION-ONLY-CONFLICT-TEST'::text)) where packet_checksum='{key}'
        and evidence_id=(select min(evidence_id) from private.development_evidence where packet_checksum='{key}');
    """
    statement=development_import_sql(packet,commit=False).replace('do $dev$',perturb+'do $dev$',1)
    sql(statement,expected_error='DEVELOPMENT_RECORD_CONFLICT')
    stored_packet_check(packet)
    checks=dict(record_conflict_rejected_and_rolled_back=True)
    if saved is not None:
        perturb=f"""update private.development_vectors set receipt=jsonb_set(receipt,'{{vector_checksum}}',
            to_jsonb('TRANSACTION-ONLY-CONFLICT-TEST'::text)) where packet_checksum='{key}'
            and evidence_id=(select min(evidence_id) from private.development_vectors where packet_checksum='{key}');
        """
        statement=development_vector_sql(packet,saved,commit=False).replace('do $dev$',perturb+'do $dev$',1)
        sql(statement,expected_error='DEVELOPMENT_VECTOR_CONFLICT')
        vector_check(packet,saved)
        checks['vector_conflict_rejected_and_rolled_back']=True
    return checks


def execute_embedding(packet, directory):
    texts,bound = bounded_inputs(packet)
    cache, ledger_path = directory/'real-vectors.json', directory/'embedding-ledger.json'
    if cache.exists():
        saved = json.loads(cache.read_text(encoding='utf-8'))
        validate_saved_vectors(packet,saved)
        return saved, False
    # Exclusive reservation persists across failures: no automatic paid retries.
    from dotenv import dotenv_values
    key = (dotenv_values(ROOT/'.env',interpolate=False).get('OPENAI_API_KEY') or '').strip()
    if not key:
        raise ValueError('Missing backend provider key; no request sent')
    ledger = dict(authorization=AUTHORIZATION, endpoint=ENDPOINT, model=MODEL,
        dimensions=DIMENSIONS, packet_checksum=packet['packet_checksum'], input_count=len(texts),
        reserved_usd=RESERVATION_USD, conservative_cost_bound_usd=bound,
        project_openai_cap_usd=30, account_wide_balance_verified=False,
        status='reserved_no_automatic_retry', started_at=datetime.now(timezone.utc).isoformat())
    with ledger_path.open('x',encoding='utf-8') as stream:
        json.dump(ledger,stream)
        stream.flush()
        os.fsync(stream.fileno())
    provider = OpenAICompatibleEmbeddingProvider(name='openai',base_url=ENDPOINT,api_key=key,
        model=MODEL,dimensions=DIMENSIONS,timeout_seconds=45)
    try:
        vectors = provider.embed(texts)
        saved = dict(packet_checksum=packet['packet_checksum'],model=MODEL,dimensions=DIMENSIONS,
            ids=[r['id'] for r in packet['records']],vectors=vectors,
            provider_metadata=provider.last_response_metadata)
        saved['checksum']=fingerprint(saved)
        validate_saved_vectors(packet,saved)
        atomic_json(cache,saved)
        usage=saved['provider_metadata']['usage']
        ledger.update(status='passed',provider_metadata=saved['provider_metadata'],
            estimated_cost_usd=usage['prompt_tokens']*PRICE_PER_MILLION/1_000_000,
            cache_checksum=saved['checksum'])
        atomic_json(ledger_path,ledger)
        return saved, True
    except Exception as exc:
        ledger.update(status='stopped_no_automatic_retry',error_type=type(exc).__name__)
        if isinstance(exc,HTTPError):
            ledger['http_status']=exc.code
        atomic_json(ledger_path,ledger)
        raise


def vector_check(packet,saved):
    expected = validate_saved_vectors(packet,saved)
    key=packet['packet_checksum']
    rows=sql(f"""select jsonb_build_object('rows',coalesce(jsonb_agg(r order by r.evidence_id),'[]'::jsonb)) from
      (select evidence_id,model,embedding::text as vector,extensions.vector_dims(embedding) as dimensions,receipt
       from private.development_vectors where packet_checksum='{key}') r;""")[0]['rows']
    if len(rows)!=len(expected):
        raise ValueError('Stored vector count mismatch')
    maximum_error=0.0
    for r,record,vector in zip(rows,packet['records'],expected,strict=True):
        receipt = dict(id=record['id'],record_checksum=record['record_checksum'],
                       vector_checksum=fingerprint(vector),provider_metadata=saved['provider_metadata'])
        if r['evidence_id']!=record['id'] or r['model']!=MODEL or r['dimensions']!=DIMENSIONS or r['receipt']!=receipt:
            raise ValueError('Stored vector provenance mismatch')
        differences=[abs(a-b) for a,b in zip(json.loads(r['vector']),vector,strict=True)]
        maximum_error=max(maximum_error,max(differences))
    if maximum_error>0.000001:
        raise ValueError('Stored vector differs from real provider response')
    # A same-vector round trip tests pgvector integrity, not semantic answer quality.
    distance=sql(f"""select jsonb_build_object('distance',embedding OPERATOR(extensions.<=>) embedding) from private.development_vectors
      where packet_checksum='{key}' order by evidence_id limit 1;""")[0]['distance']
    if abs(distance)>0.000001:
        raise ValueError('Vector cosine round trip failed')
    return dict(stored_vectors=len(rows),dimensions=DIMENSIONS,max_float32_rounding_error=maximum_error,
                same_vector_distance=distance,semantic_retrieval_benchmarked=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','import','embed','verify'))
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--execute-authorized-development',action='store_true')
    args=parser.parse_args()
    payloads,_=verified_payloads(args.package,MANIFEST_HASH)
    plan=build_plan(args.package,MANIFEST_HASH)
    expansion=build_expansion(plan,build_preparation(plan,payloads),payloads)
    packet=build_development_packet(plan,expansion,payloads)
    validate_packet(packet)
    bounded_inputs(packet)
    directory=OUTPUT/packet['packet_checksum']
    directory.mkdir(parents=True,exist_ok=True)
    atomic_json(directory/'admission-packet.json',packet)
    summary=dict(record_count=len(packet['records']),existing_selected=sum(r['origin']['kind']=='retained_original_block_selection' for r in packet['records']),
        expanded_sections=sum(r['origin']['kind']=='verified_derivative_not_original_binary' for r in packet['records']),
        held=packet['held'],packet_checksum=packet['packet_checksum'],publication_eligible=False,
        provider_calls_this_run=0,action=args.action,report_directory=str(directory))
    if args.action=='prepare':
        print(json.dumps(summary,indent=2)); return
    if not args.execute_authorized_development:
        raise ValueError('Explicit development execution flag required')
    require_local_database()
    verify(plan)
    before=snapshot()
    if args.action=='import':
        summary['backup']=backup()
        prepare()
        migrated=cli('migration','up','--local')
        if migrated.returncode:
            raise RuntimeError('Local development migration failed; inspect local migration state')
        prior=dev_counts(packet)
        sql(development_import_sql(packet,fail=True),expected_error='DEVELOPMENT_INJECTED_FAILURE')
        if dev_counts(packet)!=prior:
            raise ValueError('Development import rollback failed')
        sql(development_import_sql(packet))
        stored_packet_check(packet)
        after=dev_counts(packet)
        sql(development_import_sql(packet))
        if dev_counts(packet)!=after:
            raise ValueError('Development repeat import changed counts')
        summary.update(import_rollback_verified=True,repeat_import_verified=True)
    summary['admission']=stored_packet_check(packet)
    if args.action=='embed':
        saved,called=execute_embedding(packet,directory)
        summary['provider_calls_this_run']=int(called)
        prior=dev_counts(packet)
        sql(development_vector_sql(packet,saved,fail=True),expected_error='DEVELOPMENT_INJECTED_FAILURE')
        if dev_counts(packet)!=prior:
            raise ValueError('Vector write rollback failed')
        sql(development_vector_sql(packet,saved))
        first=vector_check(packet,saved)
        sql(development_vector_sql(packet,saved))
        if vector_check(packet,saved)!=first:
            raise ValueError('Vector repeat import changed values')
        summary.update(vector_write_rollback_verified=True,repeat_vector_write_verified=True)
    if args.action in ('embed','verify'):
        saved=json.loads((directory/'real-vectors.json').read_text(encoding='utf-8'))
        summary['vectors']=vector_check(packet,saved)
        summary['embedding_usage']=saved['provider_metadata']['usage']
        summary['embedding_estimated_cost_usd']=saved['provider_metadata']['usage']['prompt_tokens']*PRICE_PER_MILLION/1_000_000
        summary['conflicts']=conflict_checks(packet,saved)
    else:
        summary['conflicts']=conflict_checks(packet)
    summary['role_isolation']=isolation_check()
    summary['public_corpus_unchanged']=snapshot()==before
    if not summary['public_corpus_unchanged']:
        raise ValueError('Public corpus changed during development operation')
    verify(plan)
    verified_payloads(args.package,MANIFEST_HASH)
    summary['checked_at_utc']=datetime.now(timezone.utc).isoformat()
    summary['pass']=True
    atomic_json(directory/(args.action+'-verification.json'),summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print('Development operation stopped: '+type(exc).__name__+'; no raw credentials/provider response printed.')
        raise SystemExit(1)
