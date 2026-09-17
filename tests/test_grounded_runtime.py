"""Offline contract/negative tests. These doubles are NOT live RAG evidence."""
from copy import deepcopy
from dataclasses import replace
from time import monotonic
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app, STORE
from app.schemas.retrieval import JourneyPosition
from app.services.grounded_runtime import (GroundedProductRuntime, GroundedDraft, GroundedVerdict,
    Claim, Support, OutlineItem, RealResponses, source_bound_draft, configured_runtime)
from app.services.product_runtime import ProductContext, ProductRuntimeUnavailable, get_product_runtime


def context(**changes):
    value=ProductContext(uuid4(),2,JourneyPosition(stage='pregnancy',unit='week',exact=26),
        'Pregnancy week 26',('Vegan',),('Peanut',),())
    return replace(value,**changes)


def hit():
    return dict(id='unit-test-source',text='Grains and pulses are protein sources.',flags=['unpublished_development_evidence'],
        applicability={'unit':'week','start':1,'end':40},required_conditions=[],excluded_conditions=[],
        citation=dict(source_id='test-only',attribution='Test-only source',url='https://example.org/test',
            anchor={'locator':'test paragraph'}))


def draft(text='Grains and pulses provide protein.',source='unit-test-source',horizon='none'):
    return GroundedDraft(claims=[Claim(text=text,supports=[Support(evidence_id=source)])],
        outline=[] if horizon=='none' else [OutlineItem(day=i,claim_index=0) for i in range(7 if horizon=='week' else 1)])


class RetrievalDouble:
    def __init__(self,empty=False): self.queries=[]; self.empty=empty
    def search(self,query,vector):
        self.queries.append(query)
        return {'hits':[] if self.empty else [hit()],'query_context_checksum':'TEST_ONLY'}


class ProviderDouble:
    def __init__(self,*,supported=True): self.calls=[];self.supported=supported
    def embed(self,text):
        self.calls.append(('embedding',text))
        return [1.0]*1536,{'request_id':'TEST_ONLY_embedding','kind':'embedding'}
    def complete(self,instructions,data,schema,**kwargs):
        self.calls.append((schema.__name__,deepcopy(data)))
        if schema is GroundedDraft:
            return draft(horizon=data['horizon']),{'request_id':'TEST_ONLY_generation','kind':'generation'}
        return GroundedVerdict(claims=[dict(claim_index=i,supported=self.supported,respects_context=True,safe_scope=True,reason='Test double',
            supporting_spans=[dict(evidence_id='unit-test-source',span_id='s0')])
            for i in range(len(data['claims']))]),{'request_id':'TEST_ONLY_validation','kind':'semantic_validation'}


def runtime(**kwargs):
    return GroundedProductRuntime(retrieval=RetrievalDouble(),provider=ProviderDouble(**kwargs))


def test_source_id_binding_never_accepts_invented_citation():
    with pytest.raises(ProductRuntimeUnavailable,match='unverifiable citation'):
        source_bound_draft(draft(source='invented'),[hit()],horizon='none',context=context())


def test_live_regression_food_claim_requires_food_in_its_actual_citation():
    source=hit(); source['text']='Ensure that you eat enough protein and iron.'
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        source_bound_draft(draft('Green leafy vegetables provide iron.'),[source],horizon='none',context=context())
    assert exc.value.code=='citation_concept_mismatch'


def test_prefilter_excludes_mixed_incompatible_passages_without_changing_them():
    from app.services.grounded_runtime import nutrition_evidence_filter
    dairy=hit(); dairy['id']='dairy'; dairy['text']='Milk and grains provide protein.'
    kept,removed=nutrition_evidence_filter([dairy,hit()],context())
    assert removed==['dairy'] and kept==[hit()]
    assert dairy['text']=='Milk and grains provide protein.'


@pytest.mark.parametrize('food',['peanuts','groundnuts','Milk','cheese','chicken','fish','eggs'])
def test_allergy_aliases_and_vegan_food_conflicts_fail_closed(food):
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        source_bound_draft(draft('Try '+food+' for protein.'),[hit()],horizon='none',context=context())
    assert exc.value.code=='constraint_validation_failed'


def test_no_unsolicited_plan_or_incomplete_week():
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        source_bound_draft(draft(horizon='week'),[hit()],horizon='none',context=context())
    assert exc.value.code=='unsolicited_plan'
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        source_bound_draft(draft(horizon='day'),[hit()],horizon='week',context=context())
    assert exc.value.code=='incomplete_plan'


def test_real_runtime_contract_carries_context_and_original_source_text():
    service=runtime()
    result=service.chat(context=context(symptoms=('back ache',),restrictions=('no impact exercise',)),text='Tell me about protein food options')
    data=service.provider.calls[1][1]
    assert data['context']['diets']==['Vegan']
    assert data['context']['allergies']==['Peanut']
    assert data['context']['symptoms']==['back ache']
    assert data['context']['restrictions']==['no impact exercise']
    assert result['display']['citations'][0]['supporting_passage']==hit()['text']
    assert result['publication_eligible'] is False
    assert len(service.provider.calls)==3


def test_semantic_failure_never_returns_draft():
    service=runtime(supported=False)
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        service.chat(context=context(),text='Tell me about protein food options')
    assert exc.value.code=='semantic_validation_failed'


def test_verifier_cannot_invent_a_source_span():
    service=runtime()
    previous=service.provider.complete
    def invent(instructions,data,schema,**kwargs):
        result,receipt=previous(instructions,data,schema,**kwargs)
        if schema is GroundedVerdict:
            result.claims[0].supporting_spans[0].span_id='nonexistent'
        return result,receipt
    service.provider.complete=invent
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        service.chat(context=context(),text='Tell me about protein food options')
    assert exc.value.code=='semantic_span_validation_failed'


def test_partial_composition_never_displays_rejected_extra_claim():
    service=runtime();previous=service.provider.complete
    def selective(instructions,data,schema,**kwargs):
        result,receipt=previous(instructions,data,schema,**kwargs)
        if schema is GroundedDraft:
            result.claims.append(Claim(text='An extra statement.',supports=[Support(evidence_id='unit-test-source')]))
        if schema is GroundedVerdict:
            result.claims[1].supported=False
        return result,receipt
    service.provider.complete=selective
    response=service.chat(context=context(),text='Tell me about protein food options')
    assert 'extra statement' not in response['display']['summary']
    assert response['trace']['composition']['accepted_original_claim_indices']==[0]
    assert response['trace']['composition']['omitted']==[{'claim_index':1,'reason':'semantic_or_context_failure'}]
    assert len(response['trace']['verified_source_spans'])==1


def test_wrong_extra_citation_is_omitted_after_one_repair_not_published():
    service=runtime();previous=service.provider.complete
    def flawed(instructions,data,schema,**kwargs):
        result,receipt=previous(instructions,data,schema,**kwargs)
        if schema is GroundedDraft:
            result.claims.append(Claim(text='Green leafy vegetables provide iron.',supports=[Support(evidence_id='unit-test-source')]))
        return result,receipt
    service.provider.complete=flawed
    response=service.plan(context=context(),horizon='week',focus='nutrition')
    assert response['trace']['repair_calls']==1
    assert response['trace']['workers'][0]['source_validation_omissions']
    assert all('leafy' not in i['item'] for i in response['schedule']['items'])
    # Live claims still form seven days. Authored meal components have distinct
    # provenance and must not be counted as model-validated corpus claims.
    assert len([item for item in response['schedule']['items'] if item.get('origin') != 'source_linked_catalogue'])==7


def test_failed_provider_is_not_replaced_by_fixtures():
    service=runtime()
    def fail(*args,**kwargs):
        raise ProductRuntimeUnavailable('Simulated network failure',code='provider_unavailable')
    service.provider.complete=fail
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        service.chat(context=context(),text='Tell me about protein food options')
    assert exc.value.code=='provider_unavailable'


def test_evidence_gap_makes_no_generation_call():
    service=runtime();service.retrieval.empty=True
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        service.chat(context=context(),text='Tell me about protein food options')
    assert exc.value.code=='evidence_gap'
    assert len(service.provider.calls)==1


def test_symptom_question_cannot_be_replaced_by_unrelated_evidence():
    service=runtime()
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        service.chat(context=context(symptoms=('Heartburn',)),text='What can help with the heartburn I reported?')
    assert exc.value.code=='evidence_gap'
    assert len(service.provider.calls)==1


def test_self_care_request_enables_only_activity_consent_not_medical_clearance():
    service=runtime()
    service.chat(context=context(),text='Give me a self-care idea this week')
    conditions=service.retrieval.queries[0].active_conditions
    assert conditions==['consents_to_wellbeing_activity']


def test_tomorrow_plan_is_one_day_not_unsolicited_week():
    result=runtime().chat(context=context(),text='Create a nutrition plan for tomorrow')
    assert result['schedule']['horizon']=='day'
    assert {i['day'] for i in result['schedule']['items']}=={'1'}


def test_urgent_and_missing_records_do_not_generate():
    service=runtime()
    result=service.chat(context=context(),text='I am bleeding heavily right now')
    assert result['display']['route']=='urgent'
    assert service.provider.calls==[]
    result=service.chat(context=context(),text='Show my uploaded document')
    assert result['display']['route']=='feature_not_available'
    assert service.provider.calls==[]


def test_followup_uses_user_history_not_invented_context():
    service=runtime()
    result=service.chat(context=context(history=(('user','Tell me about protein food options'),('assistant','Some previous answer'))),text='Make that vegan instead')
    assert 'Tell me about protein food options' in service.retrieval.queries[0].question
    assert 'Some previous answer' not in service.retrieval.queries[0].question
    assert result['display']['ordinary_generation_calls']==1


def test_short_nutrient_followup_keeps_recent_vegan_request_and_allergy():
    service=runtime()
    response=service.chat(context=context(diets=('Vegetarian',),allergies=('Dairy',),
        history=(('user','Make those options vegan instead'),('assistant','Previous answer'))),
        text='What about calcium?')
    sent=service.provider.calls[1][1]
    assert 'Vegan' in sent['context']['diets']
    assert sent['context']['allergies']==['Dairy']
    assert 'Allergy: Dairy' in response['display']['applied_constraints']


def test_one_conflicting_food_does_not_erase_independently_valid_claim():
    service=runtime(); previous=service.provider.complete
    def conflicting(instructions,data,schema,**kwargs):
        result,receipt=previous(instructions,data,schema,**kwargs)
        if schema is GroundedDraft:
            result.claims.append(Claim(text='Try cheese for protein.',supports=[Support(evidence_id='unit-test-source')]))
        return result,receipt
    service.provider.complete=conflicting
    response=service.chat(context=context(),text='Tell me about protein food options')
    assert response['display']['summary']=='Grains and pulses provide protein.'
    assert response['trace']['repair_calls']==1
    assert response['trace']['workers'][0]['source_validation_omissions']==[{'claim_index':1,'reason':'constraint_validation_failed'}]


def test_explicit_two_domain_question_uses_two_bounded_specialists():
    service=runtime()
    result=service.chat(context=context(),text='Tell me about nutrition and movement')
    assert [w['domain'] for w in result['trace']['workers']]==['nutrition','movement']
    assert len(service.provider.calls)==4  # one embedding, two workers, one verifier
    assert 'schedule' not in result


def test_model_cannot_turn_a_question_into_a_plan():
    service=runtime();previous=service.provider.complete
    def unsolicited(instructions,data,schema,**kwargs):
        result,receipt=previous(instructions,data,schema,**kwargs)
        if schema is GroundedDraft: result.outline=[OutlineItem(day=0,claim_index=0)]
        return result,receipt
    service.provider.complete=unsolicited
    result=service.chat(context=context(),text='Tell me about food and exercise')
    assert 'schedule' not in result
    assert all(w['unsolicited_outline_discarded'] for w in result['trace']['workers'])
    assert result['trace']['validated_domains']==['movement','nutrition']


def test_week_outline_does_not_invent_clock_times():
    result=runtime().plan(context=context(),horizon='week',focus='nutrition')
    assert {i['day'] for i in result['schedule']['items']}=={str(i) for i in range(1,8)}
    assert all(not i['start'] and not i['end'] for i in result['schedule']['items'])
    assert result['schedule']['save_eligible'] is False


@pytest.mark.parametrize('bad_outline',[[],[OutlineItem(day=0,claim_index=0)],[OutlineItem(day=99,claim_index=999)]])
def test_runtime_owns_week_structure_without_trusting_model_calendar(bad_outline):
    service=runtime()
    original=service.provider.complete
    def broken_calendar(instructions,data,schema,**kwargs):
        value,receipt=original(instructions,data,schema,**kwargs)
        if schema is GroundedDraft: value.outline=bad_outline
        return value,receipt
    service.provider.complete=broken_calendar
    response=service.plan(context=context(),horizon='week',focus='nutrition')
    assert {i['day'] for i in response['schedule']['items']}==set(map(str,range(1,8)))
    assert response['trace']['repair_calls']==0
    assert response['trace']['workers'][0]['outline_origin']=='deterministic_request_horizon'
    assert any(name=='GroundedVerdict' for name,*_ in service.provider.calls)


def test_overlong_claim_is_repaired_without_weakening_validation():
    service=runtime(); original=service.provider.complete; calls=0
    def long_first(instructions,data,schema,**kwargs):
        nonlocal calls
        value,receipt=original(instructions,data,schema,**kwargs)
        if schema is GroundedDraft:
            calls+=1
            if calls==1: value.claims[0].text='Grains and pulses provide protein. '*30
        return value,receipt
    service.provider.complete=long_first
    response=service.plan(context=context(),horizon='week',focus='nutrition')
    assert response['trace']['repair_calls']==1
    assert all(len(i['item'])<=700 for i in response['schedule']['items'] if not i.get('origin'))


def test_numeric_activity_cannot_silently_become_personal_clearance():
    source=hit(); source['text']='General guidance describes 150 minutes of aerobic activity when appropriate.'
    with pytest.raises(ProductRuntimeUnavailable) as exc:
        source_bound_draft(draft('Aim for 150 minutes of aerobic activity this week.'),[source],horizon='none',context=context())
    assert exc.value.code=='activity_context_missing'
    source_bound_draft(draft('A general reference is 150 minutes of aerobic activity; suitability depends on your clinician and symptoms.'),[source],horizon='none',context=context())


def test_durable_budget_cap_and_model_allowlist(tmp_path):
    provider=RealResponses('test-not-a-key','gpt-5.4-mini',ledger_path=tmp_path/'ledger.json')
    from app.services.grounded_runtime import INTEGRATION_CAP_USD
    provider.reserve(INTEGRATION_CAP_USD-.01)
    with pytest.raises(ProductRuntimeUnavailable) as exc: provider.reserve(.02)
    assert exc.value.code=='development_budget_limit'
    with pytest.raises(ProductRuntimeUnavailable): RealResponses('test','unpriced-model')


def enter(client):
    sid=client.post('/v1/session').json()['session_id']
    payload=dict(session_id=sid,name='Test',journey='pregnant',timeline_mode='week',timeline_value='26',diets=['Vegan'],allergies=['Peanut'])
    assert client.post('/v1/onboarding',json=payload).status_code==200
    return sid,payload


def test_private_operator_mode_requires_token_and_loopback(monkeypatch):
    monkeypatch.setenv('MAYA_RUNTIME_MODE','private_development')
    monkeypatch.setenv('MAYA_OPERATOR_TOKEN','x'*36)
    client=TestClient(app,client=('127.0.0.1',1234)); sid,_=enter(client)
    result=client.post('/v1/chat',json={'session_id':sid,'text':'Tell me about food'})
    assert result.status_code==403 and result.json()['code']=='review_restriction'
    remote=TestClient(app,client=('203.0.113.3',1234)); sid,_=enter(remote)
    assert remote.post('/v1/chat',headers={'X-Maya-Operator':'x'*36},json={'session_id':sid,'text':'Tell me about food'}).status_code==403


def test_urgent_http_never_initialises_database_even_with_valid_operator(monkeypatch):
    monkeypatch.setenv('MAYA_RUNTIME_MODE','private_development')
    monkeypatch.setenv('MAYA_OPERATOR_TOKEN','x'*36)
    import app.services.grounded_runtime as module
    def fail(): raise AssertionError('Urgent request touched database/provider')
    monkeypatch.setattr(module,'_connected_runtime',fail)
    client=TestClient(app,client=('127.0.0.1',1234));sid,_=enter(client)
    response=client.post('/v1/chat',headers={'X-Maya-Operator':'x'*36},json={'session_id':sid,'text':'I cannot breathe right now'})
    assert response.status_code==200 and response.json()['display']['ordinary_generation_calls']==0
    assert 'Compass' not in response.json()['display']['summary']


def test_general_category_request_does_not_hide_current_reduced_movement():
    service=runtime()
    result=service.chat(context=context(),text='Tell me about movement; I feel reduced movement right now')
    assert result['display']['ordinary_generation_calls']==0
    assert service.provider.calls==[]


def test_session_expiry_and_origin_restriction():
    client=TestClient(app);sid,_=enter(client)
    assert client.get('/v1/context/'+sid,headers={'Origin':'https://evil.example'}).status_code==403
    STORE.get(UUID(sid)).expires_at=monotonic()-1
    assert client.get('/v1/context/'+sid).status_code==404


def test_new_journey_does_not_reuse_previous_session_cookie():
    client=TestClient(app);sid,_=enter(client)
    client.post('/v1/session')
    assert client.get('/v1/context/'+sid).status_code==403


def test_context_edit_invalidates_inflight_answer_and_history():
    client=TestClient(app);sid,payload=enter(client)
    class EditingRuntime:
        def chat(self,**kwargs):
            response=client.post('/v1/onboarding',json={**payload,'timeline_value':'6'})
            assert response.status_code==200
            return {'display':{'summary':'stale answer','validation_display_allowed':True}}
    app.dependency_overrides[get_product_runtime]=lambda:EditingRuntime()
    try:
        response=client.post('/v1/chat',json={'session_id':sid,'text':'Tell me about protein'})
        assert response.status_code==409
        assert STORE.get(UUID(sid)).history==[]
        assert STORE.get(UUID(sid)).busy is False
    finally:
        app.dependency_overrides.pop(get_product_runtime,None)


def test_concurrent_duplicate_turn_is_rejected_without_second_generation():
    client=TestClient(app);sid,_=enter(client)
    class ConcurrentRuntime:
        def chat(self,**kwargs):
            second=client.post('/v1/chat',json={'session_id':sid,'text':'Tell me about protein'})
            assert second.status_code==409
            return {'display':{'summary':'Contract-only test','validation_display_allowed':True}}
    app.dependency_overrides[get_product_runtime]=lambda:ConcurrentRuntime()
    try:
        assert client.post('/v1/chat',json={'session_id':sid,'text':'Tell me about protein'}).status_code==200
        assert len(STORE.get(UUID(sid)).history)==2
    finally:
        app.dependency_overrides.pop(get_product_runtime,None)
