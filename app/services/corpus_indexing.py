"""Read-only indexing eligibility and coverage audit over the verified handoff.

Storage/embedding permission is not a substitute for publication review.
This module does not approve content, call a model, or return user guidance.
"""
from collections import Counter

from app.services.corpus_import import ImportPlan


def indexing_inventory(plan: ImportPlan) -> dict:
    sources = {s['source_id']: s for s in plan.provenance['authoring']['sources']}
    records = []
    for run in plan.provenance['runs']:
        source = sources[run['artifact']['source_id']]
        task_by_candidate = {task['candidate_id']: task for task in run['review_tasks']}
        for candidate in run['candidates']:
            permission = (run['admission']['may_embed'] and source['reuse_status'] == 'permitted'
                          and 'embed' in source['allowed_use'] and source['delivery_mode'] == 'retrievable'
                          and source['status'] not in ('excluded', 'superseded'))
            task = task_by_candidate.get(candidate['candidate_id'])
            accepted = {d['role'] for d in (task or {}).get('decisions', []) if d['decision'] == 'accepted'}
            missing_roles = sorted(set((task or {}).get('required_roles', [])) - accepted)
            eligible = bool(permission and candidate['state'] == 'approved'
                            and (task is None or task['status'] == 'accepted') and not missing_roles)
            records.append(dict(evidence_id=candidate['evidence_id'], source_id=candidate['source_id'],
                candidate_id=candidate['candidate_id'], candidate_checksum=candidate['candidate_checksum'],
                state=candidate['state'], source_embedding_permission=permission,
                production_embedding_eligible=eligible, missing_review_roles=missing_roles,
                applies_to=candidate['applies_to'], domains=candidate['domains'],
                conditions_required=candidate['conditions_required'], conditions_excluded=candidate['conditions_excluded'],
                text_bytes=len(candidate['normalized_search_text'].encode('utf-8')),
                reason=('embedding_not_permitted' if not permission else
                        'approved_for_existing_ingestion' if eligible else 'review_gate_not_satisfied')))
    coverage = []
    for stage, unit, positions in (('pregnancy','week',range(1,43)), ('postpartum','week',range(1,13)),
                                   ('postpartum','day',range(0,8)), ('possible_pregnancy','none',[None])):
        for position in positions:
            domains = {}
            for domain in ('nutrition','movement','symptoms','wellbeing','preparation','followup','journey'):
                matching = [r for r in records if r['applies_to']['stage'] == stage and r['applies_to']['unit'] == unit
                    and (unit == 'none' or r['applies_to']['start'] <= position <= r['applies_to']['end'])
                    and domain in r['domains']]
                domains[domain] = {
                    'draft_candidate_ids': [r['evidence_id'] for r in matching],
                    'unconditional_draft_count': sum(not r['conditions_required'] and not r['conditions_excluded'] for r in matching),
                    'production_embedding_eligible_count': sum(r['production_embedding_eligible'] for r in matching),
                }
            coverage.append(dict(stage=stage,unit=unit,position=position,domains=domains))
    return dict(release_id=plan.release_id, import_fingerprint=plan.import_fingerprint,
        counts={'total_candidates':len(records),
                'source_embedding_permission':sum(r['source_embedding_permission'] for r in records),
                'production_embedding_eligible':sum(r['production_embedding_eligible'] for r in records),
                'embedding_forbidden':sum(not r['source_embedding_permission'] for r in records)},
        review_roles_outstanding=dict(Counter(role for r in records for role in r['missing_review_roles'])),
        blocked_source_ids=sorted({r['source_id'] for r in records if not r['source_embedding_permission']}),
        raw_profile_count=len(plan.rows['weekly_profiles']),
        profiles_without_linked_evidence=[r['profile_id'] for r in plan.rows['weekly_profiles'] if not r['source_evidence_ids']],
        records=records, coverage=coverage,
        caveats=['Draft applicability is not proof of clinical or India-localisation approval.',
                 'A candidate count is not a measure of answer quality or complete nutrient/activity coverage.',
                 'The source registry says may_embed; the existing production ingestion requires approved candidates too.',
                 'No unpublished record is promoted or exposed by this inventory.'])
