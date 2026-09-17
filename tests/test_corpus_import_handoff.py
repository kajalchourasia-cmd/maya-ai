"""Optional local tests of the real transferred package, not a generated corpus.

Set MAYA_CORPUS_TEST_PACKAGE to the extracted discovery package directory.
Mutation tests change in-memory snapshots only; the transferred files stay intact.
"""
import json
import os
from pathlib import Path

import pytest

import app.services.corpus_import as importer
from scripts.import_maya_corpus import MANIFEST_HASH
from app.services.corpus_indexing import indexing_inventory

PACKAGE = os.environ.get('MAYA_CORPUS_TEST_PACKAGE')
pytestmark = pytest.mark.skipif(not PACKAGE, reason='Real handoff package not configured on this machine')


def test_real_handoff_mapping_preserves_data_and_existing_approvals():
    plan = importer.build_plan(Path(PACKAGE), MANIFEST_HASH)
    summary = plan.summary()
    assert summary['counts'] == {'content_releases':1, 'public_sources':14, 'source_artifacts':14,
        'source_blocks':72, 'ingestion_runs':14, 'evidence_review_tasks':55,
        'evidence_review_decisions':54, 'weekly_profiles':63, 'guidance_fragments':56, 'guideline_chunks':55}
    assert summary['empty_profile_count'] == 46
    assert summary['real_embeddings_imported'] == summary['published_rows_created'] == 0
    assert {r['role'] for r in plan.rows['evidence_review_decisions']} == {'content', 'product'}
    assert all(r['status'] == 'pending' for r in plan.rows['evidence_review_tasks'])
    assert all(r['release_id'] == plan.release_id for rows in plan.rows.values() for r in rows if 'release_id' in r)
    assert all(r['dry_run'] for r in plan.rows['ingestion_runs'])
    assert plan.provenance['verified_payload_count'] == 137


def test_real_indexing_inventory_distinguishes_permission_from_approval():
    report = indexing_inventory(importer.build_plan(Path(PACKAGE), MANIFEST_HASH))
    assert report['counts'] == {'total_candidates':55,'source_embedding_permission':53,
                                'production_embedding_eligible':0,'embedding_forbidden':2}
    assert report['blocked_source_ids'] == ['BHC-WEEKS']
    assert len(report['profiles_without_linked_evidence']) == 46
    assert len(report['coverage']) == 63
    assert report['review_roles_outstanding']['clinical'] == 55
    assert report['review_roles_outstanding']['product'] == 28
    week26 = next(r for r in report['coverage'] if r['stage']=='pregnancy' and r['position']==26)
    assert 'E-IN-FOOD' in week26['domains']['nutrition']['draft_candidate_ids']
    assert week26['domains']['nutrition']['production_embedding_eligible_count']==0


@pytest.mark.parametrize('mutation', ['candidate_text', 'wrong_decision_checksum', 'duplicate_decision', 'no_storage_permission'])
def test_real_mapper_rejects_changed_evidence_or_reviews(monkeypatch, mutation):
    payloads, digest = importer.verified_payloads(Path(PACKAGE), MANIFEST_HASH)
    if mutation in ('wrong_decision_checksum', 'duplicate_decision'):
        name = 'public-authoring/data/reviews/ingestion_decisions.json'
        obj = json.loads(payloads[name])
        if mutation == 'duplicate_decision':
            obj['decisions'].append(obj['decisions'][0])
        else:
            obj['decisions'][0]['candidate_checksum'] = '0' * 64
    else:
        name = next(n for n in payloads if n.startswith('recovered-artifacts/stage1-audit-v1/') and n.endswith('.json'))
        obj = json.loads(payloads[name])
        if mutation == 'candidate_text':
            obj['candidates'][0]['original_text'] += ' changed'
        else:
            obj['admission']['may_store'] = False
    payloads[name] = json.dumps(obj).encode('utf-8')
    # Unit-test the mapping boundary separately from the checksum boundary.
    monkeypatch.setattr(importer, 'verified_payloads', lambda *args: (payloads, digest))
    with pytest.raises(ValueError):
        importer.build_plan(Path(PACKAGE), MANIFEST_HASH)
