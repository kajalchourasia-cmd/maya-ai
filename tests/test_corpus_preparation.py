"""Preparation tests distinguish integrity/coverage inventory from medical approval."""
import os
from pathlib import Path

import pytest

from app.services.corpus_import import build_plan, verified_payloads, sha256
from app.services.corpus_preparation import check_partition, split_document, review_flags, build_preparation
from scripts.prepare_maya_corpus import MANIFEST_HASH


def test_pdf_text_is_preserved_without_rewriting_numbers_or_negations():
    text = '9\nDo not change a supplement. 45 grams\n'
    source, spans, removed = split_document('nhm-motherhood-9.txt', text)
    check_partition(text, spans, removed)
    assert source == 'NHM-MOTHERHOOD'
    assert text[spans[0]['start']:spans[0]['end']] == text


def test_licence_page_is_accounted_for_not_health_guidance():
    text = 'Permission subject to attribution.'
    _, spans, removed = split_document('nhm-cho-4.txt', text)
    assert spans == [] and removed[0]['reason'] == 'licence_metadata'
    check_partition(text, spans, removed)


@pytest.mark.parametrize('filename,text', [('unknown.txt','hi'), ('owh-health.txt','missing markers'),
    ('owh-stages.txt','Stages of pregnancy Pregnancy lasts about 40 weeks '*2)])
def test_changed_inputs_fail_closed(filename, text):
    with pytest.raises(ValueError):
        split_document(filename, text)


@pytest.mark.parametrize('spans', [[dict(start=1,end=3)], [dict(start=0,end=2),dict(start=1,end=3)],
                                  [dict(start=0,end=4)]])
def test_source_offsets_must_cover_exactly_once(spans):
    with pytest.raises(ValueError):
        check_partition('abc', spans, [])


def test_risk_flags_do_not_imply_approval():
    flags = review_flags('NHS tablets 10 mg', 'NHS-PP-ACTIVE', 'supplement_schedule')
    assert 'not_approved_for_user_delivery' in flags
    assert 'country_specific_service_or_contact' in flags
    assert 'supplement_schedule_requires_manual_adaptation' in flags


@pytest.mark.skipif(not os.environ.get('MAYA_CORPUS_TEST_PACKAGE'), reason='Actual package not configured')
def test_actual_handoff_preparation():
    root = Path(os.environ['MAYA_CORPUS_TEST_PACKAGE'])
    payloads, _ = verified_payloads(root, MANIFEST_HASH)
    plan = build_plan(root, MANIFEST_HASH)
    report = build_preparation(plan, payloads)
    assert report['payloads_verified'] == 137
    assert report['summary']['input_files'] == 12
    assert report['summary']['sources'] == 5
    assert 0 < report['summary']['retained_words'] < report['summary']['raw_words']
    assert report['summary']['new_approved_chunks'] == report['summary']['provider_calls'] == 0
    for s in report['sections']:
        original = payloads[s['input_path']].decode('utf-8')
        assert original[s['start']:s['end']] == s['text']
        assert sha256(s['text'].encode('utf-8')) == s['text_sha256']
        assert s['exact_week_assignment'] is None
    assert all(c['production_embedding_eligible_count'] == 0 for c in report['coverage'])
    assert report['existing_inventory']['counts']['production_embedding_eligible'] == 0
    assert build_preparation(plan, payloads) == report
    # Real content boundaries: no site-menu boilerplate or video/footer text leaked in.
    health = ''.join(s['text'] for s in report['sections'] if s['source_id']=='OWH-HEALTH')
    assert 'Hidden first column container' not in health
    assert 'When to call the doctor' in health
    assert '800-799-SAFE' in health  # Do not silently delete clinical/support content as navigation.
    assert 'Return to top' not in health
    assert sha256((root/'SHA256SUMS.json').read_bytes()) == MANIFEST_HASH
