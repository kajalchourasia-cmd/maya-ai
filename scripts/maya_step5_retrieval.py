"""Bounded real Step 5 retrieval benchmark; operator-only, never publication.

Synthetic QUESTIONS; genuine provider query vectors and genuine corpus/SQL.
Expectations are fixed before the first retrieval run. No fake answer text.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.development_corpus import MODEL, DIMENSIONS, ENDPOINT, PRICE_PER_MILLION, AUTHORIZATION, validate_packet
from app.services.development_retrieval import DevelopmentQuery, OperatorDevelopmentRetrieval, checked_vector
from app.services.embeddings import OpenAICompatibleEmbeddingProvider, validated_embedding_vectors
from app.services.foundation import fingerprint
from app.services.orchestration import plan_route
from app.schemas.orchestration import ContextKind
from app.schemas.safety import SafetyGateInput
from app.services.safety_gate import evaluate_safety_from_path
from scripts.maya_development_index import atomic_json, stored_packet_check, vector_check, isolation_check
from scripts.import_maya_corpus import require_local_database, sql, snapshot

PACKET = '8ad39c36af0425cf527102a22ea798c5b16ce347bf49fc5d57430d844b5cbed0'


def case(identifier, question, domain, *, stage='pregnancy', week=26, expect=(), absent=(), empty=False, **context):
    return dict(id=identifier, query=dict(question=question, domain=domain,
        journey=dict(stage=stage, unit='week', exact=week), session_scope='synthetic-operator-'+identifier,
        state_version=1, **context), expected_any=list(expect), expected_absent=list(absent), expected_empty=empty)


def benchmark_cases():
    """Small engineering regression set, not a clinical or independent benchmark."""
    return [
        case('wash-produce','How should I clean vegetables before eating them?', 'nutrition',
             expect=('E-FOOD-HYGIENE','E-PREG-FOOD-SAFETY','EXP-13d2006ae009d959cfdebc42')),
        case('plant-protein','Which grains and pulses are sources of protein?', 'nutrition',
             diets=['vegan'], allergies=['peanut'], expect=('E-IN-FOOD-GRAINS',)),
        case('iron-greens','Which leafy vegetables supply iron and folic acid?', 'nutrition',
             diets=['vegetarian'], expect=('E-IN-FOOD-GREENS',)),
        case('fluids','Why is drinking water important during pregnancy?', 'nutrition',
             expect=('EXP-14d953673b622d4787cdf161',)),
        case('movement-consult','Should I discuss exercise with my doctor or midwife?', 'movement',
             expect=('E-MOVEMENT-CONSULT','EXP-ca34cf7284f36c4dd0763116')),
        case('week24','How does my baby develop at 24 weeks?', 'journey', week=24,
             expect=('E-P24-DEVELOPMENT','EXP-e762566dde661f0f42593100'),
             absent=('E-P36-DEVELOPMENT','EXP-18c240e0eed3b8736ba6e913')),
        case('week36','What is happening to my baby at 36 weeks?', 'journey', week=36,
             expect=('E-P36-DEVELOPMENT','EXP-18c240e0eed3b8736ba6e913'),
             absent=('E-P24-DEVELOPMENT','EXP-e762566dde661f0f42593100')),
        case('early-symptoms','What changes can occur in the first trimester?', 'symptoms', week=6,
             expect=('EXP-2f3b4ff9b172c7bb128df422',), absent=('EXP-a0138ab2902b6dc1c42b6b79',)),
        case('late-symptoms','What changes can occur in the third trimester?', 'symptoms', week=36,
             absent=('EXP-2f3b4ff9b172c7bb128df422','EXP-a0138ab2902b6dc1c42b6b79')),
        case('postpartum-unknown','When can I start gentle walking after giving birth?', 'movement', stage='postpartum', week=2,
             absent=('E-PP-GENTLE-MOVEMENT',)),
        case('postpartum-ready','When can I start gentle walking after giving birth?', 'movement', stage='postpartum', week=2,
             active_conditions=['uncomplicated_delivery','feels_ready_for_gentle_activity'],
             expect=('E-PP-GENTLE-MOVEMENT','EXP-8f326b757356e4bc7faf2988')),
        case('postpartum-restricted','When can I start gentle walking after giving birth?', 'movement', stage='postpartum', week=2,
             active_conditions=['uncomplicated_delivery','feels_ready_for_gentle_activity','movement_restriction'],
             restrictions=['clinician has restricted exercise'], absent=('E-PP-GENTLE-MOVEMENT',)),
        case('postpartum-diet','Do I need a special diet when breastfeeding?', 'nutrition', stage='postpartum', week=4,
             active_conditions=['breastfeeding'], expect=('E-PP-DIET','EXP-1cc2446c14514713ee14f48f')),
        case('postpartum-support','Who can help if I am struggling to cope after birth?', 'wellbeing', stage='postpartum', week=4,
             expect=('E-PP-PERSISTENT-CONCERN','EXP-8ef1762b7b7aae36ea4b2cb7')),
        case('strict-jurisdiction','What foods are recommended?', 'nutrition', jurisdiction='US', require_known_jurisdiction=True, empty=True),
        case('unrelated','How do I repair a quantum computer?', 'nutrition', empty=True),
        case('quoted-input',"How do I wash produce? '; SELECT 'not executable'; --", 'nutrition',
             expect=('E-FOOD-HYGIENE','E-PREG-FOOD-SAFETY','EXP-13d2006ae009d959cfdebc42')),
        dict(id='month-uncertainty',query=dict(question='How is my baby developing?',domain='journey',
             journey=dict(stage='pregnancy',unit='week',range_start=24,range_end=28),
             session_scope='synthetic-month',state_version=1),expected_any=[],
             expected_absent=['E-P24-DEVELOPMENT','EXP-e762566dde661f0f42593100'],expected_empty=False),
        dict(id='possible-no-nutrition',query=dict(question='What should I eat?',domain='nutrition',
             journey=dict(stage='possible_pregnancy',unit='none'),session_scope='synthetic-possible',state_version=1),
             expected_any=[],expected_absent=[],expected_empty=True),
    ]


def query_vectors(cases, directory):
    texts=list(dict.fromkeys(c['query']['question'] for c in cases))
    binding=dict(packet=PACKET, model=MODEL, dimensions=DIMENSIONS, texts=texts)
    signature=fingerprint(binding)
    cache=directory/'query-vectors.json'
    ledger_path=directory/'query-provider-ledger.json'
    called=False
    if cache.exists():
        saved=json.loads(cache.read_text(encoding='utf-8'))
    else:
        size=sum(len(t.encode('utf-8')) for t in texts)
        if any(len(t.encode('utf-8'))>8000 for t in texts) or size*PRICE_PER_MILLION/1_000_000>0.01:
            raise ValueError('Query embedding budget exceeded')
        from dotenv import dotenv_values
        key=(dotenv_values(ROOT/'.env',interpolate=False).get('OPENAI_API_KEY') or '').strip()
        if not key:
            raise ValueError('Backend key missing')
        ledger=dict(authorization=AUTHORIZATION,binding_checksum=signature,reserved_usd=.01,
            account_balance_verified=False,status='reserved_no_automatic_retry',
            started_at=datetime.now(timezone.utc).isoformat())
        with ledger_path.open('x',encoding='utf-8') as stream:
            json.dump(ledger,stream); stream.flush(); os.fsync(stream.fileno())
        provider=OpenAICompatibleEmbeddingProvider(name='openai',base_url=ENDPOINT,
            api_key=key,model=MODEL,dimensions=DIMENSIONS,timeout_seconds=45)
        try:
            vectors=provider.embed(texts)
            saved=dict(binding=binding,binding_checksum=signature,vectors=vectors,
                       provider_metadata=provider.last_response_metadata)
            saved['checksum']=fingerprint(saved)
            atomic_json(cache,saved)
            ledger.update(status='completed',provider_metadata=saved['provider_metadata'],
                estimated_cost_usd=saved['provider_metadata']['usage']['prompt_tokens']*PRICE_PER_MILLION/1_000_000)
            atomic_json(ledger_path,ledger)
            called=True
        except Exception as exc:
            ledger.update(status='stopped_no_automatic_retry',error_type=type(exc).__name__)
            atomic_json(ledger_path,ledger)
            raise
    if (saved['binding']!=binding or saved['binding_checksum']!=signature or
            saved['checksum']!=fingerprint({k:v for k,v in saved.items() if k!='checksum'})):
        raise ValueError('Query cache binding/integrity mismatch')
    meta=saved['provider_metadata']
    if meta.get('http_status')!=200 or not meta.get('request_id') or meta['usage']['prompt_tokens']<1:
        raise ValueError('Missing real query embedding receipt')
    if meta['usage']['prompt_tokens']*PRICE_PER_MILLION/1_000_000>.01:
        raise ValueError('Query usage exceeds reservation')
    vectors=validated_embedding_vectors(dict(model=MODEL,data=[dict(index=i,embedding=v)
        for i,v in enumerate(saved['vectors'])]),len(texts),MODEL,DIMENSIONS)
    return dict(zip(texts,vectors,strict=True)),meta,called


def routing_diagnostics():
    output=[]
    for text,symptoms,horizon in (
        ('What food should I eat?',[], 'none'),
        ('Create a weekly nutrition and exercise plan',[], 'week'),
        ('Create a weekly nutrition and exercise plan',['backache'],'week'),
        ('I am bleeding heavily',[], 'none'),
        ('Tell me about protein',[], 'none'),
        ('Tell me about food and exercise',[], 'none'),
    ):
        safety=evaluate_safety_from_path(SafetyGateInput(input_channel='chat_message',
            content_origin='user_text',text=text),ROOT/'data/safety/rule_spec.yaml',mode='evaluation_only')
        route=plan_route(text=text,safety_route=safety.route,requested_horizon=horizon,
            context_kinds={ContextKind.SYMPTOM} if symptoms else set(),
            current_symptom=bool(symptoms),max_total_steps=16)
        output.append(dict(text=text,synthetic_symptoms=symptoms,safety_route=safety.route,
            route=route.model_dump(mode='json'),workers_executed=False,generation_calls=0,
            safety_spec_evaluation_only=True))
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-authorized-development',action='store_true')
    args=parser.parse_args()
    if not args.execute_authorized_development:
        raise ValueError('Explicit development execution flag required')
    require_local_database()
    packet_dir=ROOT/'reports/local/development-index'/PACKET
    packet=json.loads((packet_dir/'admission-packet.json').read_text(encoding='utf-8'))
    validate_packet(packet)
    stored_packet_check(packet)
    integrity=vector_check(packet,json.loads((packet_dir/'real-vectors.json').read_text(encoding='utf-8')))
    before=snapshot()
    cases=benchmark_cases()
    directory=ROOT/'reports/local/step5-retrieval'/fingerprint(cases)
    directory.mkdir(parents=True,exist_ok=True)
    # Persist before any paid request / ranking to prevent silent target changes.
    expected_path=directory/'predeclared-cases.json'
    if expected_path.exists() and json.loads(expected_path.read_text(encoding='utf-8'))!=cases:
        raise ValueError('Benchmark expectations changed')
    atomic_json(expected_path,cases)
    vectors,metadata,called=query_vectors(cases,directory)
    engine=OperatorDevelopmentRetrieval(packet=packet,execute_sql=sql)
    results=[]
    for c in cases:
        query=DevelopmentQuery.model_validate(c['query'])
        result=engine.search(query,vectors[query.question])
        ids={r['id'] for r in result['hits']}
        checks=dict(expected_evidence=(not c['expected_any'] or bool(ids&set(c['expected_any']))),
            excluded_evidence=not bool(ids&set(c['expected_absent'])),
            empty_case=(not c['expected_empty'] or not ids),
            no_publication_or_generation=not result['publication_eligible'] and not result['answer_generated'],
            constraints_preserved=all(result['constraints'][key]==getattr(query,key)
                for key in ('diets','allergies','symptoms','restrictions','active_conditions')),
            traceable_sources=all(h['citation']['anchor']['locator'] and h['citation']['text_sha256'] for h in result['hits']))
        results.append(dict(id=c['id'],checks=checks,passed=all(checks.values()),result=result))
        print(json.dumps(dict(case=c['id'],passed=all(checks.values()),ids=sorted(ids))))
    roles=isolation_check()
    if snapshot()!=before:
        raise ValueError('Original public corpus changed')
    stored_packet_check(packet)
    report=dict(executed_at=datetime.now(timezone.utc).isoformat(),packet_checksum=PACKET,
        benchmark_checksum=fingerprint(cases),cases=results,total=len(results),passed=sum(r['passed'] for r in results),
        provider_calls_this_run=int(called),provider_metadata=metadata,
        estimated_query_cost_usd=metadata['usage']['prompt_tokens']*PRICE_PER_MILLION/1_000_000,
        corpus_integrity=integrity,role_isolation=roles,original_public_corpus_unchanged=True,
        routing_diagnostics=routing_diagnostics(),normal_product_runtime_connected=False,
        step5_complete=False,publication_eligible=False)
    path=directory/('verification-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    atomic_json(path,report)
    print(json.dumps(dict(report=str(path),passed=report['passed'],total=report['total'],
        provider_calls_this_run=int(called),provider_metadata=metadata)))
    return 0 if report['passed']==report['total'] else 2


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps(dict(status='stopped',error_type=type(exc).__name__)))
        sys.exit(1)
