"""Strict Stage 10 contracts for authorized state and lifecycle commits.

These contracts describe commands presented to the single deterministic write
boundary.  Authenticated identity is carried separately from command payloads so
a model, agent, or client field cannot select an owner or workspace.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.schemas.content import Contract, Text


STAGE10_SCHEMA_VERSION = "10.0.0"
STAGE10_COMMITTER_VERSION = "stage10-state-committer-v1"


class CommandKind(StrEnum):
    FACT_DECISION = "fact_decision"
    PLAN_CREATE = "plan_create"
    PLAN_TRANSITION = "plan_transition"
    FOLLOW_UP_CREATE = "follow_up_create"
    FOLLOW_UP_TRANSITION = "follow_up_transition"
    REVIEW_CREATE = "review_create"
    REVIEW_TRANSITION = "review_transition"


class CommitStatus(StrEnum):
    COMMITTED = "committed"
    REPLAYED = "replayed"
    REJECTED = "rejected"
    STALE = "stale"


class RejectionCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    SERVICE_ROLE_FORBIDDEN = "service_role_forbidden"
    DIRECT_AGENT_WRITE_FORBIDDEN = "direct_agent_write_forbidden"
    STALE_STATE_VERSION = "stale_state_version"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    MISSING_CONFIRMATION = "missing_confirmation"
    INVALID_TRANSITION = "invalid_transition"
    UNSUPPORTED_PROVENANCE = "unsupported_provenance"
    UNRESOLVED_CONFLICT = "unresolved_conflict"
    VALIDATION_FAILED = "validation_failed"
    MISSING_DEPENDENCY = "missing_dependency"
    UNSAFE_CONTENT = "unsafe_content"
    NOT_FOUND = "not_found"


class FactDecision(StrEnum):
    CONFIRM = "confirm"
    CORRECT = "correct"
    REJECT = "reject"


class PlanLifecycle(StrEnum):
    DRAFT = "draft"
    USER_REVIEWED = "user_reviewed"
    SAVED = "saved"
    ACTIVE = "active"
    STALE = "stale"
    REPLACED = "replaced"
    ARCHIVED = "archived"


class FollowUpStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReviewState(StrEnum):
    NOT_REQUIRED = "not_required"
    OFFERED = "offered"
    CONSENTED = "consented"
    QUEUED = "queued"
    REVIEWED = "reviewed"
    RESUMED = "resumed"
    DECLINED = "declined"
    UNAVAILABLE = "unavailable"
    TIMED_OUT = "timed_out"


class DependencyKind(StrEnum):
    JOURNEY_STATE = "journey_state"
    ALLERGY = "allergy"
    RESTRICTION = "restriction"
    CONDITION = "condition"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    SUPPLEMENT = "supplement"
    CLINICIAN_INSTRUCTION = "clinician_instruction"
    EVIDENCE = "evidence"


class ProvenanceKind(StrEnum):
    DOCUMENT_CANDIDATE = "document_candidate"
    VALIDATED_PLAN = "validated_plan"
    USER_ACTION = "user_action"
    VALIDATED_FOLLOW_UP = "validated_follow_up"
    SAFETY_TRACE = "safety_trace"


class AuthenticatedCommitScope(Contract):
    schema_version: Literal["10.0.0"] = STAGE10_SCHEMA_VERSION
    workspace_id: UUID
    owner_user_id: UUID
    care_episode_id: UUID
    current_state_version: int = Field(ge=1)
    current_journey_state_id: UUID
    authenticated_at: datetime
    identity_source: Literal["authenticated_session"] = "authenticated_session"
    database_derived_state: Literal[True] = True
    service_role_used: Literal[False] = False

    @model_validator(mode="after")
    def episode_is_owner_workspace(self) -> Self:
        if self.care_episode_id != self.workspace_id:
            raise ValueError("the owner-only care episode must match its workspace")
        return self


class CommitProvenance(Contract):
    kind: ProvenanceKind
    source_id: Text
    trace_id: UUID | None = None
    source_document_id: UUID | None = None
    source_document_fact_id: UUID | None = None
    source_page: int | None = Field(default=None, ge=1)
    exact_span: str | None = None
    exact_span_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    validation_policy_version: str | None = None

    @model_validator(mode="after")
    def exact_document_provenance(self) -> Self:
        document_values = (
            self.source_document_id, self.source_document_fact_id,
            self.source_page, self.exact_span, self.exact_span_sha256,
        )
        if self.kind == ProvenanceKind.DOCUMENT_CANDIDATE and any(
            value is None for value in document_values
        ):
            raise ValueError("document decisions require document, page, exact span, and checksum")
        if self.kind != ProvenanceKind.DOCUMENT_CANDIDATE and any(
            value is not None for value in document_values
        ):
            raise ValueError("non-document provenance cannot carry a document span")
        if self.kind == ProvenanceKind.VALIDATED_PLAN and not self.validation_policy_version:
            raise ValueError("validated plan provenance requires its validation policy")
        return self


class ActorConfirmation(Contract):
    confirmed: Literal[True]
    confirmation_id: Text
    confirmed_at: datetime
    wording_version: Text
    consent_scope: Text


class PlanDependency(Contract):
    kind: DependencyKind
    entity_id: Text
    material_key: Text
    source_item_id: UUID | None = None


class PersistedPlanItemInput(Contract):
    item_id: UUID
    domain: Literal["nutrition", "movement", "wellbeing", "preparation", "followup"]
    title: Text
    body: Text
    day: Literal[
        "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday",
    ]
    time_window: Text
    duration_minutes: int | None = Field(default=None, ge=1, le=480)
    optional: bool = False
    flexible: bool = False
    record_only: bool = False
    evidence_ids: list[Text] = Field(min_length=1)
    applied_constraint_ids: list[Text] = Field(default_factory=list)
    material_keys: list[Text] = Field(default_factory=list)
    excluded_material_keys: list[Text] = Field(default_factory=list)
    contributor: Text

    @model_validator(mode="after")
    def medication_is_read_only(self) -> Self:
        lowered = f"{self.title} {self.body}".casefold()
        if any(word in lowered for word in ("medicine", "medication", "supplement")) and not self.record_only:
            raise ValueError("medication or supplement plan content must be record-only")
        return self


class FactDecisionPayload(Contract):
    kind: Literal["fact_decision"] = "fact_decision"
    document_fact_id: UUID
    decision: FactDecision
    corrected_value: dict | None = None
    supersedes_health_fact_id: UUID | None = None
    material_dependency_key: str | None = None

    @model_validator(mode="after")
    def correction_shape(self) -> Self:
        if (self.decision == FactDecision.CORRECT) != (self.corrected_value is not None):
            raise ValueError("only a correction supplies corrected_value")
        if self.decision == FactDecision.REJECT and self.supersedes_health_fact_id is not None:
            raise ValueError("a rejection cannot supersede a confirmed fact")
        return self


class ValidatedPlanEdit(Contract):
    item_id: UUID
    field: Literal["title", "body", "day", "time_window", "duration_minutes"]
    previous_value: str | int | None
    new_value: str | int
    validated: Literal[True]
    validation_trace_id: UUID

class PlanCreatePayload(Contract):
    kind: Literal["plan_create"] = "plan_create"
    plan_id: UUID = Field(default_factory=uuid4)
    journey_state_id: UUID
    journey_week: int = Field(ge=1, le=42)
    source_release_id: UUID
    user_preferences: dict = Field(default_factory=dict)
    confirmed_constraints: list[Text] = Field(default_factory=list)
    component_agent_outputs: dict = Field(default_factory=dict)
    source_evidence_ids: list[Text] = Field(min_length=1)
    user_edits: list[ValidatedPlanEdit] = Field(default_factory=list)
    items: list[PersistedPlanItemInput] = Field(min_length=1, max_length=100)
    dependencies: list[PlanDependency] = Field(min_length=1, max_length=200)
    validation_disposition: Literal["pass"]
    validation_trace_id: UUID
    unresolved_conflict_ids: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def save_eligible_draft(self) -> Self:
        if self.unresolved_conflict_ids:
            raise ValueError("a plan with unresolved conflicts cannot enter the lifecycle")
        item_ids = [item.item_id for item in self.items]
        items = {item.item_id: item for item in self.items}
        for edit in self.user_edits:
            if edit.item_id not in items:
                raise ValueError("a validated edit must reference a plan item")
            actual = getattr(items[edit.item_id], edit.field)
            if str(actual) != str(edit.new_value):
                raise ValueError("the persisted plan item must contain the validated edit value")
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("plan item IDs must be unique")
        dependency_keys = [(item.kind, item.entity_id, item.material_key) for item in self.dependencies]
        if len(dependency_keys) != len(set(dependency_keys)):
            raise ValueError("plan dependencies must be unique")
        evidence = set(self.source_evidence_ids)
        if any(not set(item.evidence_ids) <= evidence for item in self.items):
            raise ValueError("every plan-item evidence ID must belong to the validated plan evidence")
        return self


class PlanTransitionPayload(Contract):
    kind: Literal["plan_transition"] = "plan_transition"
    plan_id: UUID
    from_status: PlanLifecycle
    to_status: PlanLifecycle
    replacement_plan_id: UUID | None = None

    @model_validator(mode="after")
    def replacement_shape(self) -> Self:
        if (self.to_status == PlanLifecycle.REPLACED) != (self.replacement_plan_id is not None):
            raise ValueError("replaced transition requires exactly one replacement plan")
        return self


class ReminderIntent(Contract):
    opted_in: Literal[True]
    scheduled_for: datetime
    timezone: Text
    channel: Literal["in_app", "email", "sms", "push"]


class FollowUpCreatePayload(Contract):
    kind: Literal["follow_up_create"] = "follow_up_create"
    task_id: UUID = Field(default_factory=uuid4)
    title: Text
    due_at: datetime | None = None
    provenance_ids: list[Text] = Field(min_length=1)
    reminder: ReminderIntent | None = None


class FollowUpTransitionPayload(Contract):
    kind: Literal["follow_up_transition"] = "follow_up_transition"
    task_id: UUID
    from_status: FollowUpStatus
    to_status: FollowUpStatus


class ReviewPacket(Contract):
    question: Text
    journey_state_id: UUID
    confirmed_fact_ids: list[UUID] = Field(default_factory=list, max_length=12)
    user_reported_context_ids: list[Text] = Field(default_factory=list, max_length=12)
    exact_span_ids: list[Text] = Field(default_factory=list, max_length=12)
    trace_reference: UUID
    unresolved_conflict_ids: list[Text] = Field(default_factory=list, max_length=12)
    requested_action: Text
    unrelated_personal_data_included: Literal[False] = False


class ReviewCreatePayload(Contract):
    kind: Literal["review_create"] = "review_create"
    case_id: UUID = Field(default_factory=uuid4)
    reason: Literal["urgent", "conflicting", "unsupported", "explicitly_requested"]
    packet: ReviewPacket
    immediate_safety_completed: bool
    safety_result: Literal["urgent", "needs_clarification", "non_urgent"]

    @model_validator(mode="after")
    def safety_precedes_review(self) -> Self:
        if self.reason == "urgent" and not self.immediate_safety_completed:
            raise ValueError("urgent safety behavior must complete before review is offered")
        return self


class ReviewTransitionPayload(Contract):
    kind: Literal["review_transition"] = "review_transition"
    case_id: UUID
    from_state: ReviewState
    to_state: ReviewState
    simulated_response: str | None = None

    @model_validator(mode="after")
    def response_is_simulated(self) -> Self:
        if self.to_state == ReviewState.REVIEWED and not self.simulated_response:
            raise ValueError("a reviewed simulated case requires its visible response")
        if self.to_state != ReviewState.REVIEWED and self.simulated_response is not None:
            raise ValueError("only the reviewed transition may carry a simulated response")
        return self


CommitPayload = Annotated[
    FactDecisionPayload | PlanCreatePayload | PlanTransitionPayload |
    FollowUpCreatePayload | FollowUpTransitionPayload |
    ReviewCreatePayload | ReviewTransitionPayload,
    Field(discriminator="kind"),
]


class StateCommitCommand(Contract):
    schema_version: Literal["10.0.0"] = STAGE10_SCHEMA_VERSION
    command_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    expected_state_version: int = Field(ge=1)
    submitted_at: datetime
    caller: Literal["authenticated_ui"] = "authenticated_ui"
    provenance: CommitProvenance
    confirmation: ActorConfirmation
    payload: CommitPayload

    @model_validator(mode="after")
    def provenance_matches_payload(self) -> Self:
        expected = {
            "fact_decision": ProvenanceKind.DOCUMENT_CANDIDATE,
            "plan_create": ProvenanceKind.VALIDATED_PLAN,
            "plan_transition": ProvenanceKind.USER_ACTION,
            "follow_up_create": ProvenanceKind.VALIDATED_FOLLOW_UP,
            "follow_up_transition": ProvenanceKind.USER_ACTION,
            "review_create": ProvenanceKind.SAFETY_TRACE,
            "review_transition": ProvenanceKind.USER_ACTION,
        }[self.payload.kind]
        if self.provenance.kind != expected:
            raise ValueError(f"{self.payload.kind} requires {expected.value} provenance")
        return self


class CommitAuditTrace(Contract):
    trace_id: UUID = Field(default_factory=uuid4)
    command_id: UUID
    committer_version: Literal["stage10-state-committer-v1"] = STAGE10_COMMITTER_VERSION
    workspace_id: UUID
    actor_user_id: UUID
    command_kind: CommandKind
    idempotency_key_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    old_state_version: int = Field(ge=1)
    new_state_version: int = Field(ge=1)
    affected_dependency_ids: list[Text] = Field(default_factory=list)
    generation_call_count: Literal[0] = 0
    direct_agent_write: Literal[False] = False
    service_role_used: Literal[False] = False
    raw_personal_text_logged: Literal[False] = False
    committed_at: datetime


class StateCommitResult(Contract):
    schema_version: Literal["10.0.0"] = STAGE10_SCHEMA_VERSION
    command_id: UUID
    status: CommitStatus
    command_kind: CommandKind
    old_state_version: int = Field(ge=1)
    new_state_version: int = Field(ge=1)
    entity_ids: list[UUID] = Field(default_factory=list)
    affected_plan_ids: list[UUID] = Field(default_factory=list)
    affected_dependency_ids: list[Text] = Field(default_factory=list)
    rejection_code: RejectionCode | None = None
    current_state: dict = Field(default_factory=dict)
    external_delivery_scheduled: Literal[False] = False
    trace: CommitAuditTrace

    @model_validator(mode="after")
    def result_is_coherent(self) -> Self:
        if self.status in {CommitStatus.COMMITTED, CommitStatus.REPLAYED}:
            if self.rejection_code is not None:
                raise ValueError("successful commits cannot carry rejection codes")
        elif self.rejection_code is None:
            raise ValueError("rejected or stale commits require a typed reason")
        if self.status == CommitStatus.COMMITTED and self.new_state_version <= self.old_state_version:
            raise ValueError("a new commit must advance the trusted state version")
        if self.status in {CommitStatus.REPLAYED, CommitStatus.REJECTED, CommitStatus.STALE} and (
            self.new_state_version != self.old_state_version
        ):
            raise ValueError("a replay or rejected write cannot advance state")
        if any((
            self.command_id != self.trace.command_id,
            self.command_kind != self.trace.command_kind,
            self.old_state_version != self.trace.old_state_version,
            self.new_state_version != self.trace.new_state_version,
        )):
            raise ValueError("result and audit trace identities must agree")
        return self


class DurableSnapshot(Contract):
    schema_version: Literal["10.0.0"] = STAGE10_SCHEMA_VERSION
    workspace_id: UUID
    owner_user_id: UUID
    state_version: int = Field(ge=1)
    facts: list[dict] = Field(default_factory=list)
    plans: list[dict] = Field(default_factory=list)
    follow_up_tasks: list[dict] = Field(default_factory=list)
    simulated_review_cases: list[dict] = Field(default_factory=list)
    loaded_from: Literal["storage_layer"] = "storage_layer"





class CapstoneStoryResult(Contract):
    schema_version: Literal["10.0.0"] = STAGE10_SCHEMA_VERSION
    story: Literal["plan-save", "record-continuity", "urgent-review"]
    run: int = Field(ge=1, le=3)
    passed: bool
    state_version: int = Field(ge=1)
    committed_entity_ids: list[UUID] = Field(default_factory=list)
    plan_status: PlanLifecycle | None = None
    fact_status: Literal["confirmed", "corrected", "rejected"] | None = None
    review_state: ReviewState | None = None
    causal_chain: list[Text] = Field(default_factory=list)
    ordinary_generation_calls: Literal[0] = 0
    manual_database_edits: Literal[0] = 0
    external_transmissions: Literal[0] = 0
    fictional: Literal[True] = True
    limitation: Text


