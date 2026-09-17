"""Actual-source authoring tests; none are evidence of live retrieval or approval."""
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from app.schemas.ingestion import EvidenceCandidate
from app.schemas.corpus_expansion import ExpansionUnit
from app.services.corpus_import import build_plan, verified_payloads, sha256
from app.services.corpus_preparation import build_preparation
from app.services.corpus_expansion import (build_expansion, verified_unit, trimmed_span, hold_reasons,
                                         reconcile_expansion, token_occurrences)
from app.services.foundation import fingerprint
from scripts.prepare_maya_corpus import MANIFEST_HASH
from scripts.verify_maya_recovery import verify_recovery, safe_relative, ZIP_HASH


@pytest.fixture(scope='module')
def actual():
    package = os.environ.get('MAYA_CORPUS_TEST_PACKAGE')
    if not package:
        pytest.skip('Real package not configured')
    payloads,_ = verified_payloads(Path(package),MANIFEST_HASH)
    plan = build_plan(Path(package),MANIFEST_HASH)
    prepared = build_preparation(plan,payloads)
    return payloads,plan,prepared,build_expansion(plan,prepared,payloads)


def test_actual_expansion_is_traceable_deterministic_and_non_production(actual):
    payloads,plan,prepared,packet = actual
    assert build_expansion(plan,prepared,payloads) == packet
    assert packet['summary']['draft_units'] == 46
    assert packet['summary']['draft_words'] == 7991
    assert packet['summary']['explicit_source_ranges'] == 12
    assert packet['summary']['units_needing_interval_authoring'] == 34
    assert len({u['unit_id'] for u in packet['units']}) == 46
    for data in packet['units']:
        unit = verified_unit(data,payloads)
        assert unit.canonical_url.startswith('https://')
        assert not unit.embedding_eligible and not unit.publication_eligible
        assert not unit.original_document_anchor_verified and not unit.inherited_approval
        assert set(unit.required_roles) == {'content','product','clinical','licence','india_localisation'}
        with pytest.raises(ValueError):
            EvidenceCandidate.model_validate(data)
    assert all(c['state']=='review_required' for run in plan.provenance['runs'] for c in run['candidates'])
    assert len(plan.rows['evidence_review_decisions']) == 54


def test_broad_stage_does_not_invent_week_applicability(actual):
    _,_,_,packet = actual
    for u in packet['units']:
        if u['source_explicit_applicability'] is None:
            assert u['applicability_basis'] == 'broad_stage_no_exact_interval'
        else:
            assert u['source_id'] == 'OWH-STAGES'
    second = next(u for u in packet['units'] if u['heading'].startswith('Second trimester'))
    assert second['source_explicit_applicability']['start'] == 13  # Preserve source, not UI convention.
    assert second['source_explicit_applicability']['end'] == 28


@pytest.mark.parametrize('field', ['publication_eligible','embedding_eligible','inherited_approval',
                                 'original_document_anchor_verified','conditions_resolved'])
def test_flags_cannot_be_promoted(actual,field):
    unit = deepcopy(actual[3]['units'][0])
    unit[field] = True
    with pytest.raises(ValueError):
        ExpansionUnit.model_validate(unit)


@pytest.mark.parametrize('field,value', [('original_text','Invented replacement'),('start',1),
    ('text_sha256','0'*64), ('domains',['journey']), ('normalized_search_text','not the source')])
def test_tampering_rejected(actual,field,value):
    payloads,_,_,packet = actual
    unit = deepcopy(packet['units'][0])
    unit[field] = value
    with pytest.raises(ValueError):
        verified_unit(unit,payloads)


def test_source_bytes_and_preparation_tampering_rejected(actual):
    payloads,plan,prepared,_ = actual
    corrupted = dict(payloads)
    first = prepared['sections'][0]
    corrupted[first['input_path']] += b'changed'
    with pytest.raises(ValueError):
        build_expansion(plan,prepared,corrupted)
    edited = deepcopy(prepared)
    edited['sections'][0]['text'] = 'invented'
    with pytest.raises(ValueError):
        build_expansion(plan,edited,payloads)


def test_tables_and_professional_instructions_are_held(actual):
    held = actual[3]['held']
    assert any(h['source_id']=='NHM-CHO' for h in held)
    assert any('table_reconstruction' in reason for h in held for reason in h['reasons'])
    assert any('trailing_next_trimester' in reason for h in held for reason in h['reasons'])


def test_long_source_requires_split_without_silent_truncation():
    text = 'Source sentence with caution. ' * 150
    section = dict(text=text, domains=['nutrition'], heading='Long source', role='general_education', duplicate_of=None)
    assert any('3000_character' in reason for reason in hold_reasons(section))
    assert section['text'] == text


def test_trim_keeps_real_offsets():
    text = '  Do not remove cautions. \n'
    start,end = trimmed_span(text,0,len(text))
    assert text[start:end] == 'Do not remove cautions.'


@pytest.mark.parametrize('path', ['../bad','/bad','x/../../bad','C:/secret','a\\b'])
def test_recovery_path_safety(path):
    with pytest.raises(ValueError):
        safe_relative(path)


def test_recovery_archive_mismatch_rejected(tmp_path):
    archive = tmp_path/'bad.zip'
    archive.write_bytes(b'not the pinned archive')
    with pytest.raises(ValueError,match='checksum'):
        verify_recovery(archive,tmp_path)


def test_actual_recovery_package():
    archive,root = os.environ.get('MAYA_RECOVERY_TEST_ZIP'),os.environ.get('MAYA_RECOVERY_TEST_ROOT')
    if not archive or not root:
        pytest.skip('Real recovery package not configured')
    result = verify_recovery(Path(archive),Path(root))
    assert result['archive_sha256'] == ZIP_HASH
    assert result['archived_and_extracted_files'] == 7
    assert result['manifest_payloads_verified'] == 6
    assert not result['independently_verified_sender_machine']


def test_whole_token_overlap_does_not_match_fragments():
    assert token_occurrences(['ironic', 'iron', 'iron'], ['iron']) == [(1,2),(2,3)]
    assert token_occurrences(['iron'], []) == []
    assert token_occurrences(['iron'], ['iron', 'food']) == []


def test_actual_reconciliation_preserves_input_and_counts(actual):
    payloads, plan, _, packet = actual
    before = deepcopy(packet)
    result = reconcile_expansion(plan, packet, payloads)
    assert result == reconcile_expansion(plan, packet, payloads)
    assert packet == before
    counts = result['counts']
    assert counts['parsed_blocks_reported'] == 986
    assert counts['retained_block_bodies'] == 72
    assert counts['bodies_not_in_handoff'] == 914
    assert counts['existing_candidates'] == 55
    assert counts['source_embedding_permitted_candidates'] == 53
    assert counts['expansion_sections'] == 46
    assert counts['expansion_words'] == 7991
    assert counts['sections_overlapping_existing'] == 10
    assert counts['existing_production_embedding_eligible'] == 0
    assert counts['vectors_created'] == counts['database_mutations'] == 0
    assert len(result['coverage']) == 14
    assert sum(c['draft_sections'] for c in result['coverage']) >= 46  # Multi-topic sections.
    for record in result['records']:
        assert record['tokens_covered_by_existing_passages'] <= record['normalized_tokens']
        assert not record['applicability']['inherits_existing_interval']
        assert not record['expanded_selection_permission_verified']
        assert not record['embedding_eligible'] and not record['publication_eligible']
        assert all(not m['inherits_approval'] for m in record['overlaps'])
    nutrition = next(r for r in result['records'] if r['heading']=='Foods good for mom and baby')
    assert not nutrition['overlaps']
    assert nutrition['applicability']['source_interval'] is None
    # Old source-wide movement conditions are not nutrition prerequisites.
    assert 'exercise_clearance' in nutrition['source_wide_condition_leads_not_applied']
    assert 'conditions_required' not in nutrition


@pytest.mark.parametrize('field', ['packet_checksum','original_import_fingerprint','origin_manifest_sha256'])
def test_reconciliation_rejects_wrong_checkpoint(actual, field):
    payloads, plan, _, packet = actual
    changed = deepcopy(packet)
    changed[field] = '0'*64
    with pytest.raises(ValueError, match='checkpoint'):
        reconcile_expansion(plan, changed, payloads)


def test_reconciliation_rejects_duplicate_units_even_with_rehashed_packet(actual):
    payloads, plan, _, packet = actual
    changed = deepcopy(packet)
    changed['units'].append(deepcopy(changed['units'][0]))
    changed['packet_checksum'] = fingerprint({'units':changed['units'],'held':changed['held']})
    with pytest.raises(ValueError, match='Duplicate'):
        reconcile_expansion(plan, changed, payloads)
