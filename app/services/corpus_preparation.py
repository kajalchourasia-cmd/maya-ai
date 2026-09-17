"""Step 4A: lossless, review-only preparation of the pinned recovered text.

No inference of publication permission, clinical validity or exact-week coverage.
Character offsets refer to UTF-8 decoded original derivatives, not missing HTML/PDFs.
The explicit extraction recipes are for this handoff, not a generic web scraper.
"""
from __future__ import annotations

from collections import Counter
import csv
import io
import json
import re

from app.services.corpus_import import sha256
from app.services.corpus_indexing import indexing_inventory


PREFIX = 'recovered-artifacts/supplemental-text-derivatives/'
OWH_END = 'All material contained on these pages are free of copyright restrictions'

# Topic labels are editorial discovery hints, NOT approved applicability metadata.
RECIPES = {
    'owh-health.txt': ('OWH-HEALTH', "Staying healthy and safe Eat this. Don't eat that.", OWH_END, [
        ('Eating for two', ['nutrition']), ('Weight gain', ['nutrition']),
        ('Calorie needs', ['nutrition']), ('Foods good for mom and baby', ['nutrition']),
        ('Food safety', ['nutrition']), ('Fish facts', ['nutrition']),
        ('Vitamins and minerals', ['nutrition']), ("Don't forget fluids", ['nutrition']),
        ('Alcohol There is no known', ['nutrition']), ('Caffeine Moderate', ['nutrition']),
        ('Cravings Many women', ['nutrition', 'symptoms']), ('Keeping fit Fitness', ['movement', 'wellbeing']),
        ('Getting started For most', ['movement']), ('Best activity for moms-to-be', ['movement']),
        ('Tips for safe and healthy physical activity', ['movement', 'symptoms']),
        ('Work out your pelvic floor', ['movement']), ('Oral health Before', ['symptoms']),
        ('Using medicine and herbs', ['medication']), ('Travel Everyday life', ['preparation']),
        ('Environmental risks The environment', ['preparation']), ('Quitting smoking Smoking', ['preparation']),
        ('Substance abuse Using', ['preparation']), ('Abusive relationships', ['wellbeing']),
        ('When to call the doctor When', ['symptoms']),
    ]),
    'owh-stages.txt': ('OWH-STAGES', 'Stages of pregnancy Pregnancy lasts about 40 weeks', OWH_END, [
        ('First trimester (week 1–week 12)', ['symptoms', 'wellbeing']),
        ('Second trimester (week 13–week 28)', ['symptoms']),
        ('Third trimester (week 29–week 40)', ['symptoms']),
        ('Your developing baby', ['development']),
        ('At four to five weeks:', ['development']), ('At eight weeks:', ['development']),
        ('At 12 weeks:', ['development']), ('At 16 weeks:', ['development']),
        ('At 20 weeks:', ['development']), ('At 24 weeks:', ['development']),
        ('At 32 weeks:', ['development']), ('At 36 weeks:', ['development']),
        ('Weeks 37–40 :', ['development']),
    ]),
    'nhs-active.txt': ('NHS-PP-ACTIVE', 'Exercising after having a baby',
                       'Video: how can I lose my pregnancy weight sensibly?', [
        ('When can I start exercising after birth?', ['movement']),
        ('What should I be aware of before exercising?', ['movement']),
        ('Exercise ideas for new mums', ['movement']),
        ('Look after your mental health', ['wellbeing']),
        ('Healthy eating for new parents', ['nutrition']),
        ('Time-saving food tips for new parents', ['nutrition']),
        ('Breastfeeding and your diet', ['nutrition']),
        ('Stop smoking for you and your baby', ['preparation']),
    ]),
}

PDF_PAGES = {
    'nhm-cho-4.txt': ('NHM-CHO', 4, [], 'licence_metadata'),
    'nhm-cho-11.txt': ('NHM-CHO', 11, ['followup'], 'professional_instructions'),
    'nhm-motherhood-4.txt': ('NHM-MOTHERHOOD', 4, ['followup'], 'care_schedule'),
    'nhm-motherhood-5.txt': ('NHM-MOTHERHOOD', 5, ['followup'], 'care_schedule'),
    'nhm-motherhood-8.txt': ('NHM-MOTHERHOOD', 8, ['medication'], 'supplement_schedule'),
    'nhm-motherhood-9.txt': ('NHM-MOTHERHOOD', 9, ['nutrition'], 'general_education'),
    'nhm-motherhood-10.txt': ('NHM-MOTHERHOOD', 10, ['nutrition'], 'flattened_table'),
    'nhm-motherhood-12.txt': ('NHM-MOTHERHOOD', 12, ['movement', 'wellbeing'], 'general_education'),
    'nhm-motherhood-16.txt': ('NHM-MOTHERHOOD', 16, ['nutrition', 'wellbeing', 'symptoms', 'followup'], 'postpartum_care'),
}


def word_count(text: str) -> int:
    return len(text.split())


def unique_offset(text: str, marker: str) -> int:
    if text.count(marker) != 1:
        raise ValueError(f'Expected one exact boundary: {marker!r}')
    return text.index(marker)


def split_document(filename: str, text: str) -> tuple[str, list[dict], list[dict]]:
    """Partition every character into retained review spans or explicit exclusions."""
    if filename in PDF_PAGES:
        source_id, page, domains, role = PDF_PAGES[filename]
        if role == 'licence_metadata':
            return source_id, [], [dict(start=0, end=len(text), reason=role)]
        # Keep original line breaks, numeric labels, headings and caution context.
        return source_id, [dict(start=0, end=len(text), heading=f'Extracted page {page}',
            page_hint=page, domains=domains, role=role)], []
    if filename not in RECIPES:
        raise ValueError(f'No reviewed preparation recipe for {filename}')
    source_id, start_marker, end_marker, headings = RECIPES[filename]
    start, end = unique_offset(text, start_marker), unique_offset(text, end_marker)
    if end <= start:
        raise ValueError('Reversed extraction boundary')
    body = text[start:end]
    positions = [(start, 'Article introduction', [])]
    for heading, domains in headings:
        offset = start + unique_offset(body, heading)
        if offset <= positions[-1][0]:
            raise ValueError(f'Unordered or overlapping heading: {heading}')
        positions.append((offset, heading, domains))
    spans = [dict(start=offset, end=positions[i + 1][0] if i + 1 < len(positions) else end,
                  heading=heading, page_hint=None, domains=domains, role='general_education')
             for i, (offset, heading, domains) in enumerate(positions)]
    removed = []
    if start:
        removed.append(dict(start=0, end=start, reason='site_navigation_and_preamble'))
    if end < len(text):
        removed.append(dict(start=end, end=len(text), reason='footer_licence_dates_links_or_video_metadata'))
    return source_id, spans, removed


def check_partition(text: str, retained: list[dict], excluded: list[dict]) -> None:
    cursor = 0
    for span in sorted(retained + excluded, key=lambda s: s['start']):
        if span['start'] != cursor or span['end'] <= span['start'] or span['end'] > len(text):
            raise ValueError('Lost, overlapping or invalid source offsets')
        cursor = span['end']
    if cursor != len(text):
        raise ValueError('Unaccounted source characters')


def review_flags(text: str, source_id: str, role: str) -> list[str]:
    flags = ['clinical_currency_unverified', 'not_approved_for_user_delivery',
             'new_derivative_anchors_require_review', 'automated_flagging_is_not_exhaustive']
    if source_id.startswith(('OWH', 'NHS')):
        flags.append('non_India_source_requires_localisation')
    if re.search(r'\d', text):
        flags.append('numbers_units_or_schedule_need_context_check')
    if re.search(r'\b(?:tablet|dose|supplement|vitamin|IFA)\w*\b', text, re.I):
        flags.append('separate_food_references_from_treatment_or_supplement_advice')
    if re.search(r'\b(?:NHS|GP|health visitor|Healthy Start|911|helpline|hotline)\b', text, re.I):
        flags.append('country_specific_service_or_contact')
    if role in ('professional_instructions', 'care_schedule', 'supplement_schedule', 'flattened_table'):
        flags.append(role + '_requires_manual_adaptation')
    if 'weeks' in text or 'trimester' in text:
        flags.append('source_timing_not_product_timeline_authority')
    return sorted(set(flags))


def build_preparation(plan, payloads: dict[str, bytes]) -> dict:
    sources = {s['source_id']: s for s in plan.provenance['authoring']['sources']}
    linkage = {s['source_id']: s for s in json.loads(payloads['verification/SOURCE-LINKAGE.json'])}
    docs, sections = [], []
    seen = {}
    for path in sorted(name for name in payloads if name.startswith(PREFIX) and name.endswith('.txt')):
        filename = path.removeprefix(PREFIX)
        raw = payloads[path]
        text = raw.decode('utf-8')  # strict: never silently replace corrupt text
        source_id, retained, removed = split_document(filename, text)
        check_partition(text, retained, removed)
        source = sources[source_id]
        source_link = linkage[source_id]
        for span in retained:
            exact = text[span['start']:span['end']]
            digest = sha256(exact.encode('utf-8'))
            identifier = 'PREP-' + sha256((path + ':' + str(span['start']) + ':' + digest).encode())[:20]
            duplicate = seen.get(digest)
            seen.setdefault(digest, identifier)
            stage_hint = 'postpartum' if source_id == 'NHS-PP-ACTIVE' or filename == 'nhm-motherhood-16.txt' else 'pregnancy'
            sections.append(dict(id=identifier, input_path=path, input_sha256=sha256(raw),
                source_id=source_id, canonical_url=source_link['canonical_url'], **span,
                text=exact, text_sha256=digest, words=word_count(exact),
                stage_hint=stage_hint, applicability_status='editorial_hint_only_not_approved',
                exact_week_assignment=None, status='preparation_only_not_ingestion_candidate',
                duplicate_of=duplicate, review_flags=review_flags(exact, source_id, span['role'])))
        docs.append(dict(input_path=path, input_sha256=sha256(raw), source_id=source_id,
            canonical_url=source_link['canonical_url'], raw_words=word_count(text),
            retained_words=sum(word_count(text[s['start']:s['end']]) for s in retained),
            retained_section_count=len(retained), exclusions=removed,
            source_binding_basis='explicit_filename_recipe_and_handoff_source_inventory',
            derivative_to_original_byte_reproduction_verified=False,
            historical_artifact_sha256=source_link['artifact_sha256'],
            exact_original_found_on_sender=source_link['exact_raw_original_found'],
            source_registry={k: source.get(k) for k in ('jurisdiction','reuse_status','allowed_use',
                'commercial_permission','paraphrase_permission','delivery_mode','status')},
            character_partition_verified=True))
    expected = set(RECIPES) | set(PDF_PAGES)
    if {d['input_path'].removeprefix(PREFIX) for d in docs} != expected:
        raise ValueError('Supplemental input set differs from reviewed recipe set')

    inventory = indexing_inventory(plan)
    catalogues = {}
    for name, raw in payloads.items():
        if name.startswith('public-authoring/data/catalogues/') and name.endswith('.csv'):
            rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            catalogues[name.rsplit('/', 1)[-1]] = dict(rows=len(rows),
                statuses=dict(Counter(r.get('status', 'unspecified') for r in rows)),
                quantity_bases=dict(Counter(json.loads(r.get('details') or '{}').get('quantity_basis', 'unspecified') for r in rows)))

    # Existing applicability remains separate from unapproved supplemental discovery hints.
    coverage = []
    for stage, first, last in [('pregnancy',1,13),('pregnancy',14,27),('pregnancy',28,40),
                               ('pregnancy',41,42),('postpartum',1,6),('postpartum',7,12)]:
        for domain in ('nutrition','movement','symptoms','wellbeing','journey','followup'):
            found = [r for r in inventory['records'] if r['applies_to']['stage'] == stage
                     and r['applies_to']['unit'] == 'week' and domain in r['domains']
                     and r['applies_to']['start'] <= last and r['applies_to']['end'] >= first]
            uncovered = [week for week in range(first,last+1) if not any(
                r['applies_to']['start'] <= week <= r['applies_to']['end'] for r in found)]
            coverage.append(dict(stage=stage, unit='week', start=first, end=last, domain=domain,
                status='draft_candidates_present_not_coverage_approval' if found else 'no_existing_candidate',
                existing_evidence_ids=[r['evidence_id'] for r in found], weeks_without_existing_candidate=uncovered,
                supplemental_discovery_ids=[s['id'] for s in sections if s['stage_hint']==stage
                    and (domain in s['domains'] or domain == 'journey' and 'development' in s['domains'])],
                supplemental_timing='stage_hint_only_no_week_coverage_inferred',
                production_embedding_eligible_count=sum(r['production_embedding_eligible'] for r in found)))

    return dict(schema_version=1, manifest_hash=plan.manifest_hash,
        import_fingerprint=plan.import_fingerprint, payloads_verified=len(payloads),
        summary=dict(input_files=len(docs), raw_words=sum(d['raw_words'] for d in docs),
            retained_words=sum(d['retained_words'] for d in docs), review_sections=len(sections),
            exact_duplicate_sections=sum(s['duplicate_of'] is not None for s in sections),
            sources=len({d['source_id'] for d in docs}), new_approved_chunks=0,
            database_mutations=0, provider_calls=0),
        documents=docs, sections=sections, coverage=coverage, catalogues=catalogues,
        existing_inventory=inventory,
        limitations=['Offsets anchor to transferred derivatives, not unrecovered original documents.',
            'Section boundaries preserve context and may exceed final retrieval chunk sizes.',
            'Exact duplicate sections are tagged; near-duplicate or overlapping advice is not silently deleted.',
            'Source/candidate review status and source currency are not changed or approved.',
            'Supplemental stage/topic hints are discovery aids, not verified week applicability.',
            'Weekly matrix excludes postpartum day overlays; original inventory retains them.',
            'No clinical reconciliation, real embeddings, database import or live RAG is performed.'])
