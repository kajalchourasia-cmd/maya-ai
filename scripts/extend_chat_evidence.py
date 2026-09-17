"""Add attributed NHS heartburn text to a NEW private development packet.

Preserves the existing packet, permissions, sources and database rows. Uses the
existing admission/vector SQL and validators. No publication/review approvals.
Embeddings count against the existing runtime USD 1 cap, not a fresh ledger.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'.local-api-deps'),str(ROOT)]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-authorized-development',action='store_true')
    args=parser.parse_args()
    if not args.execute_authorized_development: parser.error('Explicit development execution required')
    from bs4 import BeautifulSoup
    from dotenv import dotenv_values
    from app.services.grounded_runtime import PACKET, RealResponses
    from app.services.development_corpus import (validate_packet,bounded_inputs,MODEL,DIMENSIONS,ENDPOINT,PRICE_PER_MILLION,development_import_sql,development_vector_sql,validate_saved_vectors)
    from app.services.embeddings import OpenAICompatibleEmbeddingProvider
    from app.services.public_parsers import normalize_text
    from app.services.corpus_import import sha256
    from app.services.foundation import fingerprint
    from scripts.import_maya_corpus import require_local_database,sql
    from scripts.maya_development_index import atomic_json,stored_packet_check,vector_check
    require_local_database()
    base=json.loads((ROOT/'reports/local/development-index'/PACKET/'admission-packet.json').read_text(encoding='utf-8'))
    validate_packet(base)
    if any(r['source_id']=='NHS-HEARTBURN-20260917' for r in base['records']):
        raise SystemExit('Source already present; no duplicate import or paid request.')
    url='https://www.nhs.uk/pregnancy/common-symptoms/indigestion-and-heartburn/'
    with urlopen(Request(url,headers={'User-Agent':'Maya-development-source-check/1.0'}),timeout=30) as response:
        if response.geturl()!=url: raise ValueError('Unexpected source redirect')
        html=response.read(1_000_001)
    if len(html)>1_000_000: raise ValueError('Source exceeds bound')
    soup=BeautifulSoup(html,'html.parser');main=soup.find('main')
    if main is None: raise ValueError('Source main missing')
    for item in main.find_all(['script','style','nav']): item.decompose()
    text=main.get_text('\n',strip=True)
    if 'Indigestion and heartburn in pregnancy' not in text or '14 November 2023' not in text:
        raise ValueError('Source identity/review version needs inspection')
    segments=[('comfort','Things you can do to help with indigestion and heartburn','Stop smoking'),
              ('care','When to get medical help','Medicines for indigestion and heartburn')]
    packet=deepcopy(base);packet.pop('packet_checksum')
    fetched=datetime.now(timezone.utc).isoformat()
    for name,start,end in segments:
        a=text.index(start);b=text.index(end,a)
        original=text[a:b].strip();end_offset=a+len(original)
        record=dict(id='NHS-HB-'+name.upper(),source_id='NHS-HEARTBURN-20260917',text=original,
            search_text=normalize_text(original),canonical_url=url,domains=['symptoms','nutrition'],stage='pregnancy',
            applicability=None,applicability_status='broad_stage_hint_only_no_exact_week_claim',
            conditions_required=[],conditions_excluded=[],condition_status='unresolved_read_full_source_not_unconditional',
            permission_basis=dict(kind='publisher_original_text_terms',policy_url='https://www.nhs.uk/our-policies/terms-and-conditions/',
                checked_on='2026-09-17',images_and_third_party_material_excluded=True,
                attribution='Information from the NHS website, as at 170926. Information from the NHS website is licensed under the Open Government Licence v3.0. https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/'),
            origin=dict(kind='verified_derivative_not_original_binary',unit=dict(locator=start,
                derivative_path='nhs-heartburn-source.txt',derivative_sha256=sha256(text.encode()),start=a,end=end_offset,
                source_version='reviewed-2023-11-14-retrieved-2026-09-17')),
            original_approval_inherited=False,overlap_ids=[],publication_eligible=False,review_status='review_required')
        record['text_sha256']=sha256(original.encode());record['record_checksum']=fingerprint(record)
        packet['records'].append(record)
    packet['records'].sort(key=lambda r:r['id'])
    packet['extension']=dict(base_packet_checksum=base['packet_checksum'],source_url=url,retrieved_at=fetched,
        source_html_sha256=sha256(html),source_text_sha256=sha256(text.encode()),reason='Verified week-22 symptom evidence gap; original text only')
    packet['packet_checksum']=fingerprint(packet)
    validate_packet(packet);inputs,bound=bounded_inputs(packet)
    folder=ROOT/'reports/local/development-index'/packet['packet_checksum'];folder.mkdir(parents=True,exist_ok=False)
    (folder/'nhs-heartburn-source.txt').write_text(text,encoding='utf-8')
    atomic_json(folder/'admission-packet.json',packet)
    config=dotenv_values(ROOT/'.env',interpolate=False)
    key=config.get('OPENAI_API_KEY') or ''
    if not key: raise ValueError('Provider key not configured')
    budget=RealResponses(key,'gpt-5.4-mini');reservation=budget.reserve(.01)
    provider=OpenAICompatibleEmbeddingProvider(name='openai',base_url=ENDPOINT,api_key=key,model=MODEL,dimensions=DIMENSIONS,timeout_seconds=45)
    vectors=provider.embed(inputs);meta=provider.last_response_metadata
    budget.receipt(reservation,dict(kind='corpus_embedding',**meta,estimated_usd=meta['usage']['prompt_tokens']*PRICE_PER_MILLION/1_000_000))
    saved=dict(packet_checksum=packet['packet_checksum'],model=MODEL,dimensions=DIMENSIONS,
        ids=[r['id'] for r in packet['records']],vectors=vectors,provider_metadata=meta)
    saved['checksum']=fingerprint(saved);validate_saved_vectors(packet,saved)
    atomic_json(folder/'real-vectors.json',saved)
    sql(development_import_sql(packet));sql(development_vector_sql(packet,saved))
    verification=dict(records=stored_packet_check(packet),vectors=vector_check(packet,saved),
        base_preserved=stored_packet_check(base),publication_eligible=False)
    atomic_json(folder/'verification.json',verification)
    print(json.dumps(dict(packet_checksum=packet['packet_checksum'],verification=verification,report_directory=str(folder))))

if __name__=='__main__': main()
