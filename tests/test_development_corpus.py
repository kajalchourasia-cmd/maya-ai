"""Development-only admission tests. Synthetic vectors below are NOT live proof."""
from copy import deepcopy
import os
from pathlib import Path
import pytest

from app.services.corpus_import import build_plan, verified_payloads
from app.services.corpus_preparation import build_preparation
from app.services.corpus_expansion import build_expansion
from app.services.development_corpus import (build_development_packet, validate_packet, bounded_inputs,
    validate_saved_vectors, development_import_sql, development_vector_sql, MODEL,DIMENSIONS)
from app.services.foundation import fingerprint
from scripts.prepare_maya_corpus import MANIFEST_HASH
from scripts import maya_development_index as runner
import json


@pytest.fixture(scope='module')
def actual():
    root=os.environ.get('MAYA_CORPUS_TEST_PACKAGE')
    if not root:
        pytest.skip('Real source package required')
    payloads,_=verified_payloads(Path(root),MANIFEST_HASH)
    plan=build_plan(Path(root),MANIFEST_HASH)
    expansion=build_expansion(plan,build_preparation(plan,payloads),payloads)
    return plan,expansion,payloads,build_development_packet(plan,expansion,payloads)


def fixture_saved(packet):
    saved=dict(packet_checksum=packet['packet_checksum'],model=MODEL,dimensions=DIMENSIONS,
        ids=[r['id'] for r in packet['records']],vectors=[[0.1]*DIMENSIONS for _ in packet['records']],
        provider_metadata=dict(http_status=200,request_id='TEST_ONLY',usage=dict(prompt_tokens=100,total_tokens=100)))
    return {**saved,'checksum':fingerprint(saved)}


def test_actual_admission_is_deterministic_and_not_publication(actual):
    plan, expansion, payloads, packet=actual
    before=fingerprint(plan.provenance)
    assert packet==build_development_packet(plan,expansion,payloads)
    assert len(validate_packet(packet))==96
    assert len([r for r in packet['records'] if r['origin']['kind']=='verified_derivative_not_original_binary'])==43
    assert len(packet['held'])==5  # Two restricted selections + three broader NHM sections.
    assert not any(r['source_id']=='BHC-WEEKS' for r in packet['records'])
    assert all(r['review_status']=='review_required' and not r['publication_eligible'] for r in packet['records'])
    assert before==fingerprint(plan.provenance)
    nutrition=next(r for r in packet['records'] if r['origin'].get('unit',{}).get('heading')=='Foods good for mom and baby')
    assert nutrition['applicability'] is None
    assert nutrition['condition_status']=='unresolved_read_full_source_not_unconditional'
    assert nutrition['conditions_required']==[]  # No unrelated source-wide exercise precondition.
    assert 'source_wide_condition_leads_not_applied' not in nutrition


def test_inputs_are_real_source_normalization_and_bounded(actual):
    packet=actual[3]
    texts,bound=bounded_inputs(packet)
    assert texts==[r['search_text'] for r in packet['records']]
    assert 0<bound<0.01
    assert max(len(t.encode()) for t in texts)<=8000


@pytest.mark.parametrize('field,value',[('publication_eligible',True),('authorization','unapproved'),
                                       ('packet_checksum','0'*64)])
def test_packet_tampering_rejected(actual,field,value):
    packet=deepcopy(actual[3]);packet[field]=value
    with pytest.raises(ValueError): validate_packet(packet)


def test_source_and_candidate_mutation_rejected(actual):
    packet=deepcopy(actual[3]);packet['records'][0]['text']='invented'
    packet['packet_checksum']=fingerprint({k:v for k,v in packet.items() if k!='packet_checksum'})
    with pytest.raises(ValueError): validate_packet(packet)


def test_restricted_source_cannot_be_rehashed_into_eligibility(actual):
    packet=deepcopy(actual[3]);r=packet['records'][0];r['source_id']='BHC-WEEKS'
    r['record_checksum']=fingerprint({k:v for k,v in r.items() if k!='record_checksum'})
    packet['packet_checksum']=fingerprint({k:v for k,v in packet.items() if k!='packet_checksum'})
    with pytest.raises(ValueError): validate_packet(packet)


@pytest.mark.parametrize('mutation',['model','dimensions','order','zero','nan','receipt','hash'])
def test_cached_vector_mismatch_rejected(actual,mutation):
    packet=actual[3];saved=fixture_saved(packet)
    if mutation=='model': saved['model']='wrong'
    if mutation=='dimensions': saved['dimensions']=32
    if mutation=='order': saved['ids'].reverse()
    if mutation=='zero': saved['vectors'][0]=[0.0]*DIMENSIONS
    if mutation=='nan': saved['vectors'][0][0]=float('nan')
    if mutation=='receipt': saved['provider_metadata']['http_status']=500
    saved['checksum']=fingerprint({k:v for k,v in saved.items() if k!='checksum'})
    if mutation=='hash': saved['checksum']='0'*64
    with pytest.raises(ValueError): validate_saved_vectors(packet,saved)


def test_sql_targets_private_lane_only_and_rollback_exists(actual):
    packet=actual[3]
    for statement in (development_import_sql(packet,commit=False,fail=True),
                      development_vector_sql(packet,fixture_saved(packet),commit=False,fail=True)):
        assert 'rollback;' in statement
        assert 'DEVELOPMENT_INJECTED_FAILURE' in statement
        assert 'pg_advisory_xact_lock' in statement
        assert 'insert into public.' not in statement
        assert 'update public.' not in statement
        assert 'on conflict do nothing' in statement


def test_migration_does_not_grant_application_access():
    root=Path(__file__).resolve().parents[1]
    text=(root/'supabase/migrations/20260916000200_operator_development_index.sql').read_text()
    assert text.count('enable row level security')==3
    assert 'from public,anon,authenticated,service_role' in text
    assert 'create policy' not in text
    assert 'create function' not in text
    assert 'alter table public.' not in text


def test_cached_run_does_not_call_provider_or_read_key(actual,tmp_path,monkeypatch):
    saved=fixture_saved(actual[3])  # Synthetic cache only for this unit test.
    (tmp_path/'real-vectors.json').write_text(json.dumps(saved),encoding='utf-8')
    def forbidden(*args,**kwargs):
        raise AssertionError('Cached resume must not access a provider or credential')
    monkeypatch.setattr(runner,'OpenAICompatibleEmbeddingProvider',forbidden)
    import dotenv
    monkeypatch.setattr(dotenv,'dotenv_values',forbidden)
    restored,called=runner.execute_embedding(actual[3],tmp_path)
    assert restored==saved and called is False


def test_uncertain_request_reservation_prevents_automatic_retry(actual,tmp_path,monkeypatch):
    (tmp_path/'embedding-ledger.json').write_text('{"status":"reserved_no_automatic_retry"}',encoding='utf-8')
    def forbidden(*args,**kwargs):
        raise AssertionError('An uncertain earlier call must not be retried')
    monkeypatch.setattr(runner,'OpenAICompatibleEmbeddingProvider',forbidden)
    import dotenv
    monkeypatch.setattr(dotenv,'dotenv_values',lambda *args,**kwargs: {'OPENAI_API_KEY':'TEST_ONLY_NOT_A_KEY'})
    with pytest.raises(FileExistsError): runner.execute_embedding(actual[3],tmp_path)
