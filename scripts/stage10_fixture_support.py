"""Deterministic fictional fixtures for Stage 10 development evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID

from app.schemas.state_lifecycle import (
    ActorConfirmation,
    AuthenticatedCommitScope,
    CommitProvenance,
    DependencyKind,
    FactDecision,
    FactDecisionPayload,
    FollowUpCreatePayload,
    PersistedPlanItemInput,
    PlanCreatePayload,
    PlanDependency,
    PlanLifecycle,
    PlanTransitionPayload,
    ProvenanceKind,
    ReminderIntent,
    ReviewCreatePayload,
    ReviewPacket,
    ReviewState,
    ReviewTransitionPayload,
    StateCommitCommand, ValidatedPlanEdit,
)
from app.services.state_committer import FixtureWorkspaceState, InMemoryStateCommitter


NOW = datetime(2026, 9, 12, 9, 0, tzinfo=timezone.utc)
OWNER_A = UUID("10000000-0000-0000-0000-000000000001")
OWNER_B = UUID("10000000-0000-0000-0000-000000000002")
WORKSPACE_A = UUID("20000000-0000-0000-0000-000000000001")
WORKSPACE_B = UUID("20000000-0000-0000-0000-000000000002")
JOURNEY_A = UUID("30000000-0000-0000-0000-000000000001")
JOURNEY_B = UUID("30000000-0000-0000-0000-000000000002")
DOCUMENT_A = UUID("40000000-0000-0000-0000-000000000001")
CANDIDATE_ALLERGY = UUID("50000000-0000-0000-0000-000000000001")
CANDIDATE_UNRELATED = UUID("50000000-0000-0000-0000-000000000002")
CANDIDATE_CONFLICT = UUID("50000000-0000-0000-0000-000000000003")
RELEASE = UUID("60000000-0000-0000-0000-000000000001")
PLAN_ITEM = UUID("65000000-0000-0000-0000-000000000001")


def fixture_committer() -> InMemoryStateCommitter:
    service = InMemoryStateCommitter([
        FixtureWorkspaceState(WORKSPACE_A, OWNER_A, JOURNEY_A),
        FixtureWorkspaceState(WORKSPACE_B, OWNER_B, JOURNEY_B),
    ])
    service.seed_document_candidate(
        WORKSPACE_A, CANDIDATE_ALLERGY,
        fact_type="allergy", value={"label": "sesame"},
        document_id=DOCUMENT_A, page=1, exact_span="allergy: sesame",
        material_key="sesame",
    )
    service.seed_document_candidate(
        WORKSPACE_A, CANDIDATE_UNRELATED,
        fact_type="medical_history", value={"label": "fictional historical note"},
        document_id=DOCUMENT_A, page=1, exact_span="history: fictional historical note",
        material_key="fictional-history",
    )
    service.seed_document_candidate(
        WORKSPACE_A, CANDIDATE_CONFLICT,
        fact_type="allergy", value={"label": "peanut uncertain"}, status="conflict",
        document_id=DOCUMENT_A, page=2, exact_span="allergy: peanut uncertain",
        material_key="peanut",
    )
    return service


def scope(workspace=WORKSPACE_A, owner=OWNER_A, version=1, journey=JOURNEY_A):
    return AuthenticatedCommitScope(
        workspace_id=workspace, owner_user_id=owner, care_episode_id=workspace,
        current_state_version=version, current_journey_state_id=journey,
        authenticated_at=NOW,
    )


def confirmation(label="explicit-action"):
    return ActorConfirmation(
        confirmed=True, confirmation_id=label, confirmed_at=NOW,
        wording_version="stage10-confirmation-v1",
        consent_scope="Apply this one fictional change",
    )


def document_provenance(candidate_id, page, span):
    return CommitProvenance(
        kind=ProvenanceKind.DOCUMENT_CANDIDATE,
        source_id=f"candidate:{candidate_id}", source_document_id=DOCUMENT_A,
        source_document_fact_id=candidate_id, source_page=page,
        exact_span=span, exact_span_sha256=sha256(span.encode()).hexdigest(),
    )


def fact_command(candidate_id=CANDIDATE_ALLERGY, *, version=1, decision="confirm", key="fact-confirm-0001"):
    spans = {
        CANDIDATE_ALLERGY: (1, "allergy: sesame"),
        CANDIDATE_UNRELATED: (1, "history: fictional historical note"),
        CANDIDATE_CONFLICT: (2, "allergy: peanut uncertain"),
    }
    page, span = spans[candidate_id]
    corrected = {"label": "sesame seeds"} if decision == "correct" else None
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=document_provenance(candidate_id, page, span),
        confirmation=confirmation(),
        payload=FactDecisionPayload(
            document_fact_id=candidate_id, decision=FactDecision(decision),
            corrected_value=corrected,
        ),
    )


def plan_create_command(*, version=1, plan_id=None, key="plan-create-00001", material_key="sesame", edited=False):
    kwargs = {} if plan_id is None else {"plan_id": plan_id}
    payload = PlanCreatePayload(
        **kwargs,
        journey_state_id=JOURNEY_A, journey_week=24, source_release_id=RELEASE,
        user_preferences={"window": "morning"},
        confirmed_constraints=["sesame allergy"],
        component_agent_outputs={"nutrition": "validated fixture contribution"},
        source_evidence_ids=["EVID-STAGE10-001"],
        user_edits=([ValidatedPlanEdit(
            item_id=PLAN_ITEM, field="time_window", previous_value="morning",
            new_value="late_morning", validated=True,
            validation_trace_id=UUID("70000000-0000-0000-0000-000000000001"),
        )] if edited else []),
        items=[PersistedPlanItemInput(
            item_id=PLAN_ITEM, domain="nutrition", title="Fictional breakfast",
            body="Choose the validated sesame-free fictional option.", day="monday",
            time_window="late_morning" if edited else "morning", duration_minutes=20,
            evidence_ids=["EVID-STAGE10-001"], applied_constraint_ids=["allergy:sesame"],
            material_keys=["oats"], excluded_material_keys=["sesame"],
            contributor="nutrition-agent-v1",
        )],
        dependencies=[
            PlanDependency(
                kind=DependencyKind.JOURNEY_STATE, entity_id=str(JOURNEY_A),
                material_key="pregnancy-week-24",
            ),
            PlanDependency(
                kind=DependencyKind.ALLERGY, entity_id="allergy-sesame",
                material_key=material_key, source_item_id=PLAN_ITEM,
            ),
            PlanDependency(
                kind=DependencyKind.EVIDENCE, entity_id="EVID-STAGE10-001",
                material_key="stage10-fixture-v1", source_item_id=PLAN_ITEM,
            ),
        ],
        validation_disposition="pass",
        validation_trace_id=UUID("70000000-0000-0000-0000-000000000001"),
    )
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=CommitProvenance(
            kind=ProvenanceKind.VALIDATED_PLAN, source_id="stage8:validated-fixture",
            trace_id=payload.validation_trace_id,
            validation_policy_version="stage8-validation-v1",
        ),
        confirmation=confirmation("create-draft"), payload=payload,
    )


def plan_transition_command(plan_id, version, from_status, to_status, *, key, replacement=None):
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=CommitProvenance(kind=ProvenanceKind.USER_ACTION, source_id="plan-ui"),
        confirmation=confirmation(f"plan-{to_status}"),
        payload=PlanTransitionPayload(
            plan_id=plan_id, from_status=PlanLifecycle(from_status),
            to_status=PlanLifecycle(to_status), replacement_plan_id=replacement,
        ),
    )


def follow_up_command(version, *, channel="in_app", key="follow-up-create-1"):
    reminder = ReminderIntent(
        opted_in=True, scheduled_for=datetime(2026, 9, 20, 8, 30, tzinfo=timezone.utc),
        timezone="Asia/Kolkata", channel=channel,
    )
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=CommitProvenance(
            kind=ProvenanceKind.VALIDATED_FOLLOW_UP, source_id="followup-agent-fixture",
        ),
        confirmation=confirmation("follow-up-opt-in"),
        payload=FollowUpCreatePayload(
            title="Prepare fictional appointment questions",
            due_at=reminder.scheduled_for, provenance_ids=["question-fixture-1"],
            reminder=reminder,
        ),
    )


def review_create_command(version, *, urgent=False, key="review-create-0001"):
    trace = UUID("80000000-0000-0000-0000-000000000001")
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=CommitProvenance(
            kind=ProvenanceKind.SAFETY_TRACE, source_id="stage6:safety-fixture", trace_id=trace,
        ),
        confirmation=confirmation("offer-simulated-review"),
        payload=ReviewCreatePayload(
            reason="urgent" if urgent else "explicitly_requested",
            packet=ReviewPacket(
                question="Please organize this fictional handoff.", journey_state_id=JOURNEY_A,
                confirmed_fact_ids=[], user_reported_context_ids=["symptom-event-fixture"],
                exact_span_ids=[], trace_reference=trace,
                unresolved_conflict_ids=[], requested_action="Simulated organizational review",
                unrelated_personal_data_included=False,
            ),
            immediate_safety_completed=True,
            safety_result="urgent" if urgent else "non_urgent",
        ),
    )


def review_transition_command(case_id, version, from_state, to_state, *, key, response=None):
    return StateCommitCommand(
        idempotency_key=key, expected_state_version=version, submitted_at=NOW,
        provenance=CommitProvenance(kind=ProvenanceKind.USER_ACTION, source_id="review-ui"),
        confirmation=confirmation(f"review-{to_state}"),
        payload=ReviewTransitionPayload(
            case_id=case_id, from_state=ReviewState(from_state),
            to_state=ReviewState(to_state), simulated_response=response,
        ),
    )





