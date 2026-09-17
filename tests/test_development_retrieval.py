"""Unit doubles test boundaries only. Real SQL/provider proof is the runner report."""
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.development_retrieval import (
    candidate_filter, checked_vector, source_citation, DevelopmentQuery,
    OperatorDevelopmentRetrieval, DevelopmentRetrievalFailure,
)
from app.services.foundation import fingerprint
from scripts import maya_step5_retrieval as runner


@pytest.fixture(scope='module')
def packet():
    # Real prior Step 4D packet; unavailable checkouts skip rather than invent it.
    path=runner.ROOT/'reports/local/development-index'/runner.PACKET/'admission-packet.json'
    if not path.exists():
        pytest.skip('Step 4D local packet required')
    return json.loads(path.read_text(encoding='utf-8'))


def query(**changes):
    data=dict(question='Exercise after giving birth',domain='movement',
        journey=dict(stage='postpartum',unit='week',exact=2),session_scope='test-a',state_version=1)
    data.update(changes)
    return DevelopmentQuery.model_validate(data)


def record(packet, rid):
    return next(r for r in packet['records'] if r['id']==rid)


def rows(packet):
    return [dict(evidence_id=r['id'],payload=r,vector_record_checksum=r['record_checksum'],
                 fts=0.,similarity=.7) for r in packet['records']]


@pytest.mark.parametrize('bad',[[],[1.]*1535,[0.]*1536,[float('nan')]*1536,[True]*1536,[float('inf')]*1536])
def test_invalid_vectors(bad):
    with pytest.raises(DevelopmentRetrievalFailure,match='invalid_query_embedding'):
        checked_vector(bad)


def test_conditions_are_not_inferred_from_week(packet):
    r=record(packet,'E-PP-GENTLE-MOVEMENT')
    assert candidate_filter(r,query())=='required_condition_not_reported'
    active=['uncomplicated_delivery','feels_ready_for_gentle_activity']
    assert candidate_filter(r,query(active_conditions=active)) is None
    assert candidate_filter(r,query(active_conditions=active+['movement_restriction']))=='excluded_condition_present'


def test_unknown_conditions_are_flagged_not_cleared(packet):
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=lambda _: [{'rows':rows(packet)}])
    result=engine.search(query(limit=20),[.1]*1536)
    h=next(h for h in result['hits'] if h['id']=='EXP-8f326b757356e4bc7faf2988')
    assert 'conditions_unresolved_not_unconditional' in h['flags']
    assert h['eligible_for_generation'] is False


def test_broad_stage_is_retained_not_week_specific(packet):
    r=record(packet,'EXP-14d953673b622d4787cdf161')
    for week in (6,26,36):
        assert candidate_filter(r,query(domain='nutrition',journey=dict(stage='pregnancy',unit='week',exact=week))) is None
    assert r['applicability'] is None


def test_range_requires_entire_interval(packet):
    r=record(packet,'E-P24-DEVELOPMENT')
    q=query(domain='journey',journey=dict(stage='pregnancy',unit='week',range_start=24,range_end=28))
    assert candidate_filter(r,q)=='outside_full_requested_interval'
    assert candidate_filter(r,query(domain='journey',journey=dict(stage='pregnancy',unit='week',exact=24))) is None


def test_cross_stage_unit_and_jurisdiction(packet):
    r=record(packet,'E-P24-DEVELOPMENT')
    assert candidate_filter(r,query(domain='journey'))=='wrong_stage'
    assert candidate_filter(record(packet,'E-IN-PNC-DAY3'),query(domain='followup'))=='different_timing_unit'
    assert candidate_filter(record(packet,'E-PP-DIET'),query(domain='nutrition',jurisdiction='US'))=='jurisdiction_mismatch'


@pytest.mark.parametrize('mutation,code',[
    ('missing','index_incomplete'),('duplicate','index_incomplete'),
    ('text','source_integrity_failure'),('receipt','source_integrity_failure'),
    ('score','invalid_database_score')])
def test_database_corruption_is_rejected(packet,mutation,code):
    result=deepcopy(rows(packet))
    if mutation=='missing': result.pop()
    if mutation=='duplicate': result[-1]=result[0]
    if mutation=='text': result[0]['payload']['text']='altered'
    if mutation=='receipt': result[0]['vector_record_checksum']='wrong'
    if mutation=='score': result[0]['similarity']=float('nan')
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=lambda _: [{'rows':result}])
    with pytest.raises(DevelopmentRetrievalFailure,match=code): engine.search(query(),[.1]*1536)


def test_database_failure_does_not_become_clinical_clarification(packet):
    def failed(_): raise RuntimeError('not exposed')
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=failed)
    with pytest.raises(DevelopmentRetrievalFailure,match='database_unavailable_or_timeout'):
        engine.search(query(),[.1]*1536)


def test_no_fixture_answer_or_implicit_generation(packet):
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=lambda _: [{'rows':rows(packet)}])
    result=engine.search(query(),[.1]*1536)
    assert result['answer_generated'] is False
    assert result['outcome']=='review_restriction'
    assert all(h['text']==record(packet,h['id'])['text'] for h in result['hits'])


def test_filter_before_limit_and_remove_overlap(packet):
    database=rows(packet)
    for r in database:
        r['fts']=100 if r['evidence_id']=='E-P36-DEVELOPMENT' else 1
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=lambda _: [{'rows':database}])
    q=query(domain='journey',journey=dict(stage='pregnancy',unit='week',exact=24),limit=20)
    result=engine.search(q,[.1]*1536)
    ids={h['id'] for h in result['hits']}
    assert 'E-P36-DEVELOPMENT' not in ids
    assert len(ids & {'E-P24-DEVELOPMENT','EXP-e762566dde661f0f42593100'})==1
    assert result['suppressed_overlaps']


def test_context_version_and_session_do_not_share_identity(packet):
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=lambda _: [{'rows':rows(packet)}])
    a=engine.search(query(diets=['vegan'],allergies=['peanut']),[.1]*1536)
    b=engine.search(query(session_scope='test-b',state_version=2),[.1]*1536)
    assert a['query_context_checksum']!=b['query_context_checksum']
    assert b['constraints']['allergies']==[]
    assert a['constraints_applied_to_generated_answer'] is False


def test_source_anchors_preserved(packet):
    for r in packet['records']:
        c=source_citation(r)
        assert c['url']==r['canonical_url'] and c['text_sha256']==r['text_sha256']
        assert c['anchor']['locator']
        assert c['source_version'] and c['attribution']


def test_injection_is_json_encoded_and_read_only(packet):
    statements=[]
    def db(statement):
        statements.append(statement)
        return [{'rows':rows(packet)}]
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=db)
    attack="'; drop table private.development_vectors; --"
    engine.search(query(question=attack),[.1]*1536)
    assert attack not in statements[0]
    assert 'begin read only' in statements[0] and 'statement_timeout' in statements[0]


def test_schema_rejects_forged_runtime_scope():
    with pytest.raises(ValidationError): query(publication_eligible=True)
    with pytest.raises(ValidationError): query(workspace_id='not-authenticated')


def test_uncertain_paid_attempt_is_not_retried(tmp_path,monkeypatch):
    # No actual key lookup or provider request in this unit test.
    import dotenv
    monkeypatch.setattr(dotenv,'dotenv_values',lambda *a,**k:{'OPENAI_API_KEY':'UNIT_TEST_ONLY'})
    (tmp_path/'query-provider-ledger.json').write_text('{}',encoding='utf-8')
    with pytest.raises(FileExistsError): runner.query_vectors(runner.benchmark_cases(),tmp_path)


def test_exact_query_cache_avoids_key_lookup_or_provider(tmp_path,monkeypatch):
    # Synthetic vectors only test cache plumbing, never substitute for the live run.
    cases=runner.benchmark_cases()
    texts=list(dict.fromkeys(c['query']['question'] for c in cases))
    binding=dict(packet=runner.PACKET,model=runner.MODEL,dimensions=1536,texts=texts)
    saved=dict(binding=binding,binding_checksum=fingerprint(binding),
        vectors=[[.1]*1536 for _ in texts],provider_metadata=dict(http_status=200,
        request_id='UNIT_TEST_ONLY',usage=dict(prompt_tokens=100,total_tokens=100)))
    saved['checksum']=fingerprint(saved)
    (tmp_path/'query-vectors.json').write_text(json.dumps(saved),encoding='utf-8')
    import dotenv
    def forbidden(*a,**k): raise AssertionError('Cache must not call provider or read keys')
    monkeypatch.setattr(dotenv,'dotenv_values',forbidden)
    monkeypatch.setattr(runner,'OpenAICompatibleEmbeddingProvider',forbidden)
    vectors,meta,called=runner.query_vectors(cases,tmp_path)
    assert not called and len(vectors)==len(texts)
    changed=deepcopy(cases)
    changed[0]['query']['question']='Different question'
    with pytest.raises(ValueError,match='binding/integrity'): runner.query_vectors(changed,tmp_path)


def test_routing_uses_existing_logic_and_exposes_catches():
    results=runner.routing_diagnostics()
    assert results[0]['route']['selected_workers']==['nutrition_agent']
    assert 'movement_agent' in results[1]['route']['selected_workers']
    assert 'movement_agent' not in results[2]['route']['selected_workers']
    assert results[3]['safety_route']=='urgent' and not results[3]['route']['selected_workers']
    assert results[4]['route']['selected_workers']==['nutrition_agent']
    assert results[5]['route']['requires_clarification']
    assert all(r['generation_calls']==0 for r in results)


@pytest.mark.parametrize('text,expected',[
    ('What food should I eat?', 'non_urgent'),
    ('Tell me about protein', 'non_urgent'),
    ('How much calcium is in food?', 'non_urgent'),
    ('What exercise options are there?', 'non_urgent'),
    ('What food should I eat? I am bleeding heavily.', 'urgent'),
    ('What food should I eat? I cannot breathe.', 'urgent'),
    ('I feel dizzy and want protein foods.', 'needs_clarification'),
    ('I have abdominal pain after eating food.', 'needs_clarification'),
])
def test_information_recognition_preserves_urgent_precedence(text,expected):
    from app.schemas.safety import SafetyGateInput
    from app.services.safety_gate import evaluate_safety_from_path
    result=evaluate_safety_from_path(SafetyGateInput(input_channel='chat_message',
        content_origin='user_text',text=text),runner.ROOT/'data/safety/rule_spec.yaml',mode='evaluation_only')
    assert result.route==expected
