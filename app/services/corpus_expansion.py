"""Build source-bound review units, not published medical advice, from Step 4A."""
from collections import Counter
import re

from app.schemas.corpus_expansion import ExpansionUnit
from app.services.corpus_import import sha256
from app.services.foundation import fingerprint, review_subject
from app.services.public_parsers import normalize_text
from app.services.corpus_indexing import indexing_inventory


SOURCE_RANGES = {
    'First trimester (week 1–week 12)': (1,12),
    'Second trimester (week 13–week 28)': (13,28),
    'Third trimester (week 29–week 40)': (29,40),
    'At four to five weeks:': (4,5), 'At eight weeks:': (8,8),
    'At 12 weeks:': (12,12), 'At 16 weeks:': (16,16), 'At 20 weeks:': (20,20),
    'At 24 weeks:': (24,24), 'At 32 weeks:': (32,32), 'At 36 weeks:': (36,36),
    'Weeks 37–40 :': (37,40),
}
SLOTS = {'nutrition':'nutrition_focus','movement':'movement_focus','symptoms':'symptom_education',
         'wellbeing':'wellbeing_focus','journey':'what_may_change','preparation':'preparation','followup':'followup'}
FACTS = {'nutrition':['diet_preference','allergies','reported_symptoms','reported_supplements'],
         'movement':['activity_background','movement_restrictions','reported_symptoms','recovery_context'],
         'symptoms':['reported_symptoms'], 'wellbeing':['reported_concerns'],
         'journey':['confirmed_timeline'], 'followup':['confirmed_timeline'], 'preparation':['confirmed_timeline']}
ROLES = ['licence','content','clinical','india_localisation','product']
CHECKS = ['source_anchor','domain','stage_and_range','wording','jurisdiction','conditions',
          'development_measurements','profile_links','catalogue_links','reuse_and_attribution']


def trimmed_span(text, start, end):
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end-1].isspace():
        end -= 1
    return start, end


def hold_reasons(section):
    reasons = []
    if not section['domains'] or section['heading'] == 'Your developing baby':
        reasons.append('heading_or_introduction_not_a_standalone_evidence_unit')
    if section['role'] in ('professional_instructions','care_schedule','supplement_schedule','flattened_table'):
        reasons.append('requires_audience_or_table_reconstruction_before_candidate_authoring')
    if 'medication' in section['domains']:
        reasons.append('treatment_content_not_in_initial_nutrition_movement_expansion')
    if len(normalize_text(section['text'])) > 3000:
        reasons.append('manual_context_preserving_split_required_above_existing_3000_character_threshold')
    if section['duplicate_of']:
        reasons.append('exact_duplicate_of_existing_preparation_section')
    return reasons


def verified_unit(data: dict, payloads: dict[str,bytes]) -> ExpansionUnit:
    unit = ExpansionUnit.model_validate(data)
    payload = payloads[unit.derivative_path]
    text = payload.decode('utf-8')
    if sha256(payload) != unit.derivative_sha256 or text[unit.start:unit.end] != unit.original_text:
        raise ValueError('Derivative source anchor mismatch')
    if sha256(unit.original_text.encode('utf-8')) != unit.text_sha256:
        raise ValueError('Evidence text hash mismatch')
    if unit.normalized_search_text != normalize_text(unit.original_text):
        raise ValueError('Search text is not reproducible source normalization')
    subject = unit.model_dump(mode='json', exclude={'unit_checksum'})
    if fingerprint(subject) != unit.unit_checksum:
        raise ValueError('Expansion metadata/checksum mismatch')
    return unit


def build_expansion(plan, preparation, payloads):
    sources = {s['source_id']:s for s in plan.provenance['authoring']['sources']}
    documents = {d['input_path']:d for d in preparation['documents']}
    old = [c for run in plan.provenance['runs'] for c in run['candidates']]
    units, held = [], []
    for section in preparation['sections']:
        original = payloads[section['input_path']].decode('utf-8')
        if sha256(payloads[section['input_path']]) != section['input_sha256'] or original[section['start']:section['end']] != section['text']:
            raise ValueError('Preparation no longer matches the source')
        reasons = hold_reasons(section)
        if reasons:
            held.append(dict(preparation_id=section['id'], source_id=section['source_id'],
                             heading=section['heading'], reasons=reasons))
            continue
        source = sources[section['source_id']]
        start,end = trimmed_span(original, section['start'], section['end'])
        quote = original[start:end]
        # Preserve a heading for the NEXT trimester with that next section instead
        # of incorrectly attaching it to the previous developmental milestone.
        tail = re.search(r'\s+(?:Second|Third) trimester \(week \d+-week \d+\)\s*$', quote)
        tail_hold = None
        if tail:
            tail_hold = dict(preparation_id=section['id'], source_id=section['source_id'],
                             heading=quote[tail.start():].strip(), reasons=['trailing_next_trimester_heading_not_part_of_previous_milestone'])
            end = start + tail.start()
            start,end = trimmed_span(original,start,end)
            quote = original[start:end]
        if tail_hold:
            held.append(tail_hold)
        domains = sorted({'journey' if d == 'development' else d for d in section['domains']})
        digest = sha256(quote.encode('utf-8'))
        explicit = SOURCE_RANGES.get(section['heading']) if section['source_id']=='OWH-STAGES' else None
        interval = dict(stage='pregnancy',unit='week',start=explicit[0],end=explicit[1]) if explicit else None
        related = [c for c in old if c['source_id']==section['source_id']]
        normalized = normalize_text(quote)
        overlap = [c['evidence_id'] for c in related if normalize_text(c['original_text']) in normalized
                   or normalized in normalize_text(c['original_text'])]
        unresolved = sorted(set(section['review_flags'] + [
            'source_registry_selected_scope_not_automatically_extended',
            'original_document_anchor_not_verified_for_this_expansion',
            'clinical_and_localisation_review_missing', 'conditions_require_passage_specific_review',
            'no_previous_decision_applies_to_new_text_or_metadata',
            'source_literal_range_needs_product_mapping' if explicit else 'exact_applicability_interval_not_established']))
        subject = dict(schema_version='1.0.0', unit_id='EXP-'+sha256((section['input_path']+str(start)+digest).encode())[:24],
            source_id=section['source_id'], canonical_url=documents[section['input_path']]['canonical_url'],
            source_version='recovered-derivative-'+section['input_sha256'],
            historical_artifact_sha256=documents[section['input_path']]['historical_artifact_sha256'],
            source_governance_checksum=fingerprint(review_subject(source)),
            derivative_path=section['input_path'], derivative_sha256=section['input_sha256'], start=start,end=end,
            locator=f"Recovered text {section['input_path']}; decoded characters [{start},{end}); {section['heading']}",
            heading=section['heading'], original_text=quote, text_sha256=digest, normalized_search_text=normalized,
            domains=domains, display_slots=sorted({SLOTS[d] for d in domains}),
            source_jurisdiction=source['jurisdiction'], proposed_target_jurisdiction=['IN'], stage_hint=section['stage_hint'],
            source_explicit_applicability=interval,
            applicability_basis='source_literal_range_requires_reconciliation' if explicit else 'broad_stage_no_exact_interval',
            inherited_approval=False,derivative_anchor_verified=True,original_document_anchor_verified=False,
            conditions_resolved=False,publication_eligible=False,embedding_eligible=False,state='draft_expansion',
            required_checks=CHECKS,required_roles=ROLES,unresolved=unresolved,
            personal_fact_dependencies=sorted({fact for d in domains for fact in FACTS[d]}),
            overlapping_existing_evidence_ids=sorted(overlap),
            related_source_condition_keys=sorted({condition for c in related for condition in
                                                 c['conditions_required']+c['conditions_excluded']}))
        unit = verified_unit({**subject,'unit_checksum':fingerprint(subject)}, payloads)
        units.append(unit.model_dump(mode='json'))
    if len({u['unit_id'] for u in units}) != len(units):
        raise ValueError('Duplicate expansion IDs')
    checksum = fingerprint({'units':units,'held':held})
    return dict(schema_version='1.0.0', packet_id='EXPANSION-'+checksum[:24],packet_checksum=checksum,
        origin_manifest_sha256=plan.manifest_hash, original_import_fingerprint=plan.import_fingerprint,
        units=units, held=held,
        summary=dict(draft_units=len(units), draft_words=sum(len(u['original_text'].split()) for u in units),
            source_ids=sorted({u['source_id'] for u in units}), explicit_source_ranges=sum(u['source_explicit_applicability'] is not None for u in units),
            units_needing_interval_authoring=sum(u['source_explicit_applicability'] is None for u in units),
            units_overlapping_old_evidence=sum(bool(u['overlapping_existing_evidence_ids']) for u in units),
            domains=dict(Counter(d for u in units for d in u['domains'])), hold_records=len(held),
            new_approved_candidates=0, new_embeddings=0, database_mutations=0, provider_calls=0),
        scope='Local review authoring only; not production EvidenceCandidate, IngestionRun, release or retrieval input.')


def token_occurrences(haystack, needle):
    """Whole normalized-token matching; do not match 'iron' inside another word."""
    if not needle:
        return []
    return [(i, i + len(needle)) for i in range(len(haystack) - len(needle) + 1)
            if haystack[i:i + len(needle)] == needle]


def reconcile_expansion(plan, packet, payloads):
    """Resolve mechanical overlap, not clinical applicability or publication.

    Existing evidence stays canonical for its existing version. Broader sections
    are kept intact: deleting a matching sentence could remove its qualification.
    No source-wide condition is automatically assigned to an unrelated section.
    """
    if (packet['origin_manifest_sha256'] != plan.manifest_hash or
            packet['original_import_fingerprint'] != plan.import_fingerprint or
            fingerprint({'units': packet['units'], 'held': packet['held']}) != packet['packet_checksum']):
        raise ValueError('Expansion packet does not match its import/source checkpoint')
    ids = [u['unit_id'] for u in packet['units']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate expansion IDs')
    old = [c for run in plan.provenance['runs'] for c in run['candidates']]
    sources = {s['source_id']: s for s in plan.provenance['authoring']['sources']}
    inventory = indexing_inventory(plan)
    records = []
    for data in packet['units']:
        unit = verified_unit(data, payloads)
        source = sources[unit.source_id]
        if fingerprint(review_subject(source)) != unit.source_governance_checksum:
            raise ValueError('Source governance changed since expansion')
        tokens = unit.normalized_search_text.split()
        covered, matches = set(), []
        for candidate in old:
            if candidate['source_id'] != unit.source_id:
                continue
            selected = normalize_text(candidate['original_text']).split()
            spans = token_occurrences(tokens, selected)
            reverse = token_occurrences(selected, tokens)
            if not spans and not reverse:
                continue
            relation = ('same_text' if tokens == selected else
                        'contains_existing_passage' if spans else 'part_of_existing_passage')
            if reverse:
                covered.update(range(len(tokens)))
            for start, end in spans:
                covered.update(range(start, end))
            matches.append(dict(evidence_id=candidate['evidence_id'], relation=relation,
                existing_candidate_checksum=candidate['candidate_checksum'],
                existing_applicability=candidate['applies_to'],
                existing_conditions_required=candidate['conditions_required'],
                existing_conditions_excluded=candidate['conditions_excluded'],
                conditions_are_reference_only=True, inherits_approval=False))
        action = ('retain_existing_candidate_no_automatic_alias' if any(
            m['relation'] in ('same_text', 'part_of_existing_passage') for m in matches) else
            'retain_broader_context_review_before_superseding' if matches else
            'review_as_additional_section_not_proven_new_fact')
        records.append(dict(unit_id=unit.unit_id, source_id=unit.source_id,
            heading=unit.heading, stage=unit.stage_hint, domains=unit.domains,
            unit_checksum=unit.unit_checksum, overlaps=matches, authoring_action=action,
            normalized_tokens=len(tokens), tokens_covered_by_existing_passages=len(covered),
            tokens_outside_existing_passages=len(tokens)-len(covered),
            applicability=dict(source_interval=unit.source_explicit_applicability.model_dump(mode='json')
                if unit.source_explicit_applicability else None,
                general_stage_hint=unit.stage_hint, exact_week_support=bool(unit.source_explicit_applicability),
                inherits_existing_interval=False, admitted=False),
            source_selected_sections=source['selected_sections'],
            source_has_recorded_embedding_permission='embed' in source['allowed_use'],
            expanded_selection_permission_verified=False,
            source_wide_condition_leads_not_applied=unit.related_source_condition_keys,
            embedding_eligible=False, publication_eligible=False))
    coverage = []
    for stage in ('pregnancy', 'postpartum'):
        for domain in SLOTS:
            selected = [r for r in records if r['stage']==stage and domain in r['domains']]
            coverage.append(dict(stage=stage, domain=domain, draft_sections=len(selected),
                explicit_source_intervals=sum(r['applicability']['exact_week_support'] for r in selected),
                broad_stage_sections=sum(not r['applicability']['exact_week_support'] for r in selected),
                unit_ids=[r['unit_id'] for r in selected],
                answerability_tested=False, eligible_expansion_sections=0))
    permitted_ids = {r['evidence_id'] for r in inventory['records'] if r['source_embedding_permission']}
    historical = plan.summary()
    counts = dict(parsed_blocks_reported=historical['parsed_blocks_reported'],
        retained_block_bodies=historical['preserved_block_bodies'],
        bodies_not_in_handoff=historical['parsed_blocks_reported']-historical['preserved_block_bodies'],
        existing_candidates=len(old), source_embedding_permitted_candidates=len(permitted_ids),
        permitted_candidate_words=sum(len(c['original_text'].split()) for c in old if c['evidence_id'] in permitted_ids),
        expansion_sections=len(records), expansion_words=sum(len(u['original_text'].split()) for u in packet['units']),
        sections_overlapping_existing=sum(bool(r['overlaps']) for r in records),
        distinct_existing_passages_matched=len({m['evidence_id'] for r in records for m in r['overlaps']}),
        wholly_contained_sections=sum(r['tokens_outside_existing_passages']==0 for r in records),
        existing_production_embedding_eligible=inventory['counts']['production_embedding_eligible'],
        admitted_expansion_sections=0, vectors_created=0, database_mutations=0)
    result = dict(packet_checksum=packet['packet_checksum'], counts=counts,
        records=records, coverage=coverage,
        limitations=['Counts of parser blocks, selected passages and authoring sections are different units.',
            'Whole-token containment is not semantic deduplication or clinical completeness.',
            'Topic presence is not a passed answerability test or weekly applicability approval.',
            'Source-wide permission does not automatically extend the approved selection.',
            'No previous review, interval or condition is inherited by new text.',
            'Original packets and database records remain unchanged.'])
    return {**result, 'reconciliation_checksum': fingerprint(result)}
