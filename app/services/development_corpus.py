"""Explicitly authorised, operator-only corpus admission. Never publication.

Reuses the verified handoff, expansion and embedding contracts. Original public
records and review ledgers are not changed. Broad-stage hints stay non-clinical.
"""
from app.services.corpus_import import sha256, json_sql
from app.services.corpus_indexing import indexing_inventory
from app.services.corpus_expansion import reconcile_expansion
from app.services.foundation import fingerprint
from app.services.public_parsers import normalize_text
from app.services.embeddings import validated_embedding_vectors

AUTHORIZATION = 'Kajal-development-indexing-not-publication-20260916'
MODEL = 'text-embedding-3-small'
DIMENSIONS = 1536
ENDPOINT = 'https://api.openai.com/v1/embeddings'
RESERVATION_USD = 0.01
PRICE_PER_MILLION = 0.02

# Scope is original text only. No images, linked third-party publications, or
# clinical endorsement. Policies independently inspected on 2026-09-16.
EXPANSION_PERMISSIONS = {
    'OWH-HEALTH': ('https://womenshealth.gov/about-us/work-us/collaborate-us',
                   'Office on Women\u2019s Health, U.S. Department of Health and Human Services; original federal text, public domain.'),
    'OWH-STAGES': ('https://womenshealth.gov/about-us/work-us/collaborate-us',
                   'Office on Women\u2019s Health, U.S. Department of Health and Human Services; original federal text, public domain.'),
    'NHS-PP-ACTIVE': ('https://www.nhs.uk/our-policies/terms-and-conditions/',
                    'Information from the NHS website, as at 100926. Information from the NHS website is licensed under the Open Government Licence v3.0. https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'),
}


def build_development_packet(plan, expansion, payloads):
    reconciliation = reconcile_expansion(plan, expansion, payloads)
    inventory = indexing_inventory(plan)
    permission = {r['evidence_id']: r['source_embedding_permission'] for r in inventory['records']}
    sources = {s['source_id']: s for s in plan.provenance['authoring']['sources']}
    records, held = [], []
    for run in plan.provenance['runs']:
        for c in run['candidates']:
            if (not permission[c['evidence_id']] or not run['admission']['may_store'] or
                    'store' not in sources[c['source_id']]['allowed_use']):
                held.append(dict(id=c['evidence_id'], source_id=c['source_id'], reason='source_embedding_not_permitted'))
                continue
            source = sources[c['source_id']]
            records.append(dict(id=c['evidence_id'], source_id=c['source_id'],
                text=c['original_text'], search_text=normalize_text(c['original_text']),
                canonical_url=source['canonical_url'], domains=c['domains'],
                stage=c['applies_to']['stage'], applicability=c['applies_to'],
                applicability_status='existing_draft_not_clinically_approved',
                conditions_required=c['conditions_required'], conditions_excluded=c['conditions_excluded'],
                condition_status='existing_draft_not_clinically_approved',
                permission_basis=dict(kind='verified_selected_handoff', source_checksum=fingerprint(source),
                    note=source['license_or_reuse_note'], attribution=source.get('attribution_text') or source['publisher']),
                origin=dict(kind='retained_original_block_selection', candidate=c,
                    artifact=run['artifact']), original_approval_inherited=False,
                overlap_ids=[], publication_eligible=False, review_status='review_required'))
    for unit in expansion['units']:
        sid = unit['source_id']
        if sid not in EXPANSION_PERMISSIONS:
            held.append(dict(id=unit['unit_id'], source_id=sid,
                reason='broader_selection_permission_and_third_party_origin_not_independently_resolved'))
            continue
        policy, attribution = EXPANSION_PERMISSIONS[sid]
        records.append(dict(id=unit['unit_id'], source_id=sid, text=unit['original_text'],
            search_text=unit['normalized_search_text'], canonical_url=unit['canonical_url'],
            domains=unit['domains'], stage=unit['stage_hint'],
            applicability=unit['source_explicit_applicability'],
            applicability_status=('source_literal_unreviewed' if unit['source_explicit_applicability'] else
                                  'broad_stage_hint_only_no_exact_week_claim'),
            conditions_required=[], conditions_excluded=[],
            condition_status='unresolved_read_full_source_not_unconditional',
            permission_basis=dict(kind='publisher_original_text_terms', policy_url=policy,
                checked_on='2026-09-16', attribution=attribution, images_and_third_party_material_excluded=True),
            origin=dict(kind='verified_derivative_not_original_binary', unit=unit),
            original_approval_inherited=False, overlap_ids=unit['overlapping_existing_evidence_ids'],
            publication_eligible=False, review_status='review_required'))
    for r in records:
        if r['search_text'] != normalize_text(r['text']):
            raise ValueError('Embedding input must be source normalization, not generated prose')
        r['text_sha256'] = sha256(r['text'].encode())
        r['record_checksum'] = fingerprint(r)
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate development evidence identifiers')
    result = dict(schema_version='maya-operator-corpus-v1', authorization=AUTHORIZATION,
        manifest_sha256=plan.manifest_hash, original_import_fingerprint=plan.import_fingerprint,
        expansion_checksum=expansion['packet_checksum'], records=sorted(records,key=lambda r:r['id']),
        held=held, publication_eligible=False,
        review_approvals_granted=0, reconciliation_checksum=reconciliation['reconciliation_checksum'])
    return {**result, 'packet_checksum': fingerprint(result)}


def validate_packet(packet):
    if packet.get('authorization') != AUTHORIZATION or packet.get('publication_eligible') is not False:
        raise ValueError('Not an authorised development-only packet')
    if fingerprint({k:v for k,v in packet.items() if k!='packet_checksum'}) != packet['packet_checksum']:
        raise ValueError('Development packet checksum mismatch')
    records = packet['records']
    if not records or len({r['id'] for r in records}) != len(records):
        raise ValueError('Missing or duplicate development records')
    for r in records:
        if (r['source_id']=='BHC-WEEKS' or r['publication_eligible'] is not False or
                r['review_status']!='review_required' or r['original_approval_inherited'] is not False or
                sha256(r['text'].encode())!=r['text_sha256'] or normalize_text(r['text'])!=r['search_text'] or
                fingerprint({k:v for k,v in r.items() if k!='record_checksum'})!=r['record_checksum']):
            raise ValueError('Invalid development record')
    return records


def bounded_inputs(packet):
    texts = [r['search_text'] for r in validate_packet(packet)]
    # UTF-8 bytes conservatively bound tokens; no tokenizer download is required.
    sizes = [len(text.encode('utf-8')) for text in texts]
    if len(texts)>2048 or any(not size or size>8000 for size in sizes) or sum(sizes)>250000:
        raise ValueError('Embedding input exceeds conservative request bounds')
    bound = sum(sizes)*PRICE_PER_MILLION/1_000_000
    if bound > RESERVATION_USD:
        raise ValueError('Embedding reservation insufficient')
    return texts, bound


def validate_saved_vectors(packet, saved):
    records = validate_packet(packet)
    if (saved.get('packet_checksum')!=packet['packet_checksum'] or saved.get('model')!=MODEL or
            saved.get('dimensions')!=DIMENSIONS or saved.get('ids')!=[r['id'] for r in records]):
        raise ValueError('Vectors do not belong to this packet/model/order')
    if fingerprint({k:v for k,v in saved.items() if k!='checksum'}) != saved.get('checksum'):
        raise ValueError('Saved vector checksum mismatch')
    meta = saved.get('provider_metadata', {})
    usage = meta.get('usage') or {}
    if meta.get('http_status')!=200 or type(usage.get('prompt_tokens')) is not int or usage['prompt_tokens']<1:
        raise ValueError('Successful real provider receipt missing')
    if usage['prompt_tokens']*PRICE_PER_MILLION/1_000_000>RESERVATION_USD:
        raise ValueError('Actual usage exceeds reservation')
    return validated_embedding_vectors(dict(model=saved['model'],data=[dict(index=i,embedding=v)
        for i,v in enumerate(saved['vectors'])]),len(records),MODEL,DIMENSIONS)


def development_import_sql(packet, *, commit=True, fail=False):
    validate_packet(packet)
    end = 'commit;' if commit else 'rollback;'
    return f"""begin; set local statement_timeout='30s'; set local lock_timeout='5s';
select pg_advisory_xact_lock(741604);
do $dev$ declare p jsonb := {json_sql(packet)}; r jsonb; saved jsonb; begin
 select payload into saved from private.development_corpus_batches where packet_checksum=p->>'packet_checksum';
 if found and saved is distinct from p then raise exception 'DEVELOPMENT_BATCH_CONFLICT'; end if;
 insert into private.development_corpus_batches(packet_checksum,payload) values(p->>'packet_checksum',p)
 on conflict do nothing;
 for r in select value from jsonb_array_elements(p->'records') loop
   select payload into saved from private.development_evidence
     where packet_checksum=p->>'packet_checksum' and evidence_id=r->>'id';
   if found and saved is distinct from r then raise exception 'DEVELOPMENT_RECORD_CONFLICT'; end if;
   insert into private.development_evidence(packet_checksum,evidence_id,payload)
     values(p->>'packet_checksum',r->>'id',r) on conflict do nothing;
 end loop;
 {"raise exception 'DEVELOPMENT_INJECTED_FAILURE';" if fail else ''}
end $dev$; {end}"""


def development_vector_sql(packet, saved, *, commit=True, fail=False):
    vectors = validate_saved_vectors(packet, saved)
    rows = [dict(id=r['id'], record_checksum=r['record_checksum'], vector=v,
        vector_checksum=fingerprint(v), provider_metadata=saved['provider_metadata'])
        for r,v in zip(packet['records'],vectors,strict=True)]
    return f"""begin; set local statement_timeout='30s'; set local lock_timeout='5s';
select pg_advisory_xact_lock(741604);
do $dev$ declare r jsonb; saved jsonb; p text := '{packet['packet_checksum']}'; begin
 for r in select value from jsonb_array_elements({json_sql(rows)}) loop
   if not exists(select 1 from private.development_evidence where packet_checksum=p
       and evidence_id=r->>'id' and payload->>'record_checksum'=r->>'record_checksum') then
       raise exception 'DEVELOPMENT_VECTOR_SOURCE_MISMATCH'; end if;
   select receipt into saved from private.development_vectors
     where packet_checksum=p and evidence_id=r->>'id' and model='{MODEL}';
   if found and saved is distinct from (r-'vector') then raise exception 'DEVELOPMENT_VECTOR_CONFLICT'; end if;
   insert into private.development_vectors(packet_checksum,evidence_id,model,embedding,receipt)
     values(p,r->>'id','{MODEL}',(r->'vector')::text::extensions.vector,r-'vector') on conflict do nothing;
 end loop;
 {"raise exception 'DEVELOPMENT_INJECTED_FAILURE';" if fail else ''}
end $dev$; {'commit;' if commit else 'rollback;'}"""
