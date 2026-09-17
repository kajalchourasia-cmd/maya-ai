"""Deterministic Stage 10 write boundary and provider-neutral repository contract.

The in-memory repository is used only for fictional deterministic evaluation.
`SupabaseStateCommitterClient` calls the same authenticated database boundary
using a user's access token; it never accepts or uses a service-role secret.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from app.schemas.state_lifecycle import (
    AuthenticatedCommitScope,
    CommandKind,
    CommitAuditTrace,
    CommitStatus,
    DependencyKind,
    DurableSnapshot,
    FactDecision,
    FactDecisionPayload,
    FollowUpCreatePayload,
    FollowUpStatus,
    FollowUpTransitionPayload,
    PlanCreatePayload,
    PlanLifecycle,
    PlanTransitionPayload,
    RejectionCode,
    ReviewCreatePayload,
    ReviewState,
    ReviewTransitionPayload,
    StateCommitCommand,
    StateCommitResult,
)


PLAN_TRANSITIONS: dict[PlanLifecycle, set[PlanLifecycle]] = {
    PlanLifecycle.DRAFT: {PlanLifecycle.USER_REVIEWED, PlanLifecycle.ARCHIVED},
    PlanLifecycle.USER_REVIEWED: {PlanLifecycle.SAVED, PlanLifecycle.ARCHIVED},
    PlanLifecycle.SAVED: {PlanLifecycle.ACTIVE, PlanLifecycle.REPLACED, PlanLifecycle.ARCHIVED},
    PlanLifecycle.ACTIVE: {PlanLifecycle.REPLACED, PlanLifecycle.ARCHIVED},
    PlanLifecycle.STALE: {PlanLifecycle.REPLACED, PlanLifecycle.ARCHIVED},
    PlanLifecycle.REPLACED: {PlanLifecycle.ARCHIVED},
    PlanLifecycle.ARCHIVED: set(),
}

FOLLOW_UP_TRANSITIONS: dict[FollowUpStatus, set[FollowUpStatus]] = {
    FollowUpStatus.PROPOSED: {FollowUpStatus.CONFIRMED, FollowUpStatus.CANCELLED},
    FollowUpStatus.CONFIRMED: {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED},
    FollowUpStatus.COMPLETED: set(),
    FollowUpStatus.CANCELLED: set(),
}

REVIEW_TRANSITIONS: dict[ReviewState, set[ReviewState]] = {
    ReviewState.NOT_REQUIRED: set(),
    ReviewState.OFFERED: {
        ReviewState.CONSENTED, ReviewState.DECLINED,
        ReviewState.UNAVAILABLE, ReviewState.TIMED_OUT,
    },
    ReviewState.CONSENTED: {
        ReviewState.QUEUED, ReviewState.DECLINED, ReviewState.UNAVAILABLE,
    },
    ReviewState.QUEUED: {
        ReviewState.REVIEWED, ReviewState.UNAVAILABLE, ReviewState.TIMED_OUT,
    },
    ReviewState.REVIEWED: {ReviewState.RESUMED},
    ReviewState.RESUMED: set(),
    ReviewState.DECLINED: set(),
    ReviewState.UNAVAILABLE: set(),
    ReviewState.TIMED_OUT: set(),
}


class StateCommitRepository(Protocol):
    def commit(
        self, scope: AuthenticatedCommitScope, command: StateCommitCommand,
    ) -> StateCommitResult: ...

    def load_snapshot(self, scope: AuthenticatedCommitScope) -> DurableSnapshot: ...


@dataclass
class FixtureWorkspaceState:
    workspace_id: UUID
    owner_user_id: UUID
    journey_state_id: UUID
    journey_state_version: int = 1
    version: int = 1
    document_candidates: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    facts: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    plans: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    follow_up_tasks: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    review_cases: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    audit_events: list[dict[str, Any]] = field(default_factory=list)
    idempotency: dict[str, tuple[str, StateCommitResult]] = field(default_factory=dict)


class InMemoryStateCommitter:
    """Atomic controlled-fixture implementation of the Stage 10 contract."""

    def __init__(self, workspaces: list[FixtureWorkspaceState]) -> None:
        self._workspaces = {item.workspace_id: deepcopy(item) for item in workspaces}
        self._lock = RLock()

    def seed_document_candidate(
        self,
        workspace_id: UUID,
        candidate_id: UUID,
        *,
        fact_type: str,
        value: dict[str, Any],
        status: str = "proposed",
        document_id: UUID,
        page: int,
        exact_span: str,
        material_key: str,
    ) -> None:
        with self._lock:
            self._workspaces[workspace_id].document_candidates[candidate_id] = {
                "id": candidate_id,
                "fact_type": fact_type,
                "value": deepcopy(value),
                "status": status,
                "document_id": document_id,
                "page": page,
                "exact_span": exact_span,
                "exact_span_sha256": sha256(exact_span.encode()).hexdigest(),
                "material_key": material_key,
            }

    def load_snapshot(self, scope: AuthenticatedCommitScope) -> DurableSnapshot:
        with self._lock:
            state = self._authorized(scope)
            return DurableSnapshot(
                workspace_id=state.workspace_id,
                owner_user_id=state.owner_user_id,
                state_version=state.version,
                facts=_json_records(state.facts.values()),
                plans=_json_records(state.plans.values()),
                follow_up_tasks=_json_records(state.follow_up_tasks.values()),
                simulated_review_cases=_json_records(state.review_cases.values()),
            )

    def commit(
        self, scope: AuthenticatedCommitScope, command: StateCommitCommand,
    ) -> StateCommitResult:
        with self._lock:
            state = self._workspaces.get(scope.workspace_id)
            if state is None or state.owner_user_id != scope.owner_user_id:
                return self._rejected(scope, command, 1, RejectionCode.UNAUTHORIZED)
            if scope.service_role_used:
                return self._rejected(scope, command, state.version, RejectionCode.SERVICE_ROLE_FORBIDDEN)
            if command.caller != "authenticated_ui":
                return self._rejected(scope, command, state.version, RejectionCode.DIRECT_AGENT_WRITE_FORBIDDEN)

            fingerprint = _command_fingerprint(command)
            if command.idempotency_key in state.idempotency:
                previous_hash, previous = state.idempotency[command.idempotency_key]
                if previous_hash != fingerprint:
                    return self._rejected(
                        scope, command, state.version, RejectionCode.IDEMPOTENCY_CONFLICT,
                    )
                trace = self._trace(command, state, state.version, state.version, [])
                return StateCommitResult(
                    command_id=previous.command_id,
                    status=CommitStatus.REPLAYED,
                    command_kind=previous.command_kind,
                    old_state_version=state.version,
                    new_state_version=state.version,
                    entity_ids=previous.entity_ids,
                    affected_plan_ids=previous.affected_plan_ids,
                    affected_dependency_ids=previous.affected_dependency_ids,
                    current_state=self._current_state(state),
                    trace=trace,
                )
            if command.expected_state_version != state.version:
                return self._rejected(
                    scope, command, state.version, RejectionCode.STALE_STATE_VERSION,
                    status=CommitStatus.STALE,
                )

            candidate = deepcopy(state)
            outcome = self._apply(candidate, command)
            if isinstance(outcome, RejectionCode):
                return self._rejected(scope, command, state.version, outcome)

            entity_ids, affected_plans, dependencies = outcome
            old_version = candidate.version
            candidate.version += 1
            trace = self._trace(
                command, candidate, old_version, candidate.version, dependencies,
            )
            result = StateCommitResult(
                command_id=command.command_id,
                status=CommitStatus.COMMITTED,
                command_kind=CommandKind(command.payload.kind),
                old_state_version=old_version,
                new_state_version=candidate.version,
                entity_ids=entity_ids,
                affected_plan_ids=affected_plans,
                affected_dependency_ids=dependencies,
                current_state=self._current_state(candidate),
                trace=trace,
            )
            candidate.audit_events.append(trace.model_dump(mode="json"))
            candidate.idempotency[command.idempotency_key] = (fingerprint, result)
            self._workspaces[scope.workspace_id] = candidate
            return result

    def _apply(
        self, state: FixtureWorkspaceState, command: StateCommitCommand,
    ) -> tuple[list[UUID], list[UUID], list[str]] | RejectionCode:
        payload = command.payload
        if isinstance(payload, FactDecisionPayload):
            return self._apply_fact(state, payload, command)
        if isinstance(payload, PlanCreatePayload):
            return self._apply_plan_create(state, payload, command)
        if isinstance(payload, PlanTransitionPayload):
            return self._apply_plan_transition(state, payload, command)
        if isinstance(payload, FollowUpCreatePayload):
            return self._apply_follow_up_create(state, payload, command)
        if isinstance(payload, FollowUpTransitionPayload):
            return self._apply_follow_up_transition(state, payload, command)
        if isinstance(payload, ReviewCreatePayload):
            return self._apply_review_create(state, payload, command)
        if isinstance(payload, ReviewTransitionPayload):
            return self._apply_review_transition(state, payload, command)
        return RejectionCode.VALIDATION_FAILED

    def _apply_fact(self, state, payload, command):
        candidate = state.document_candidates.get(payload.document_fact_id)
        if not candidate:
            return RejectionCode.NOT_FOUND
        provenance = command.provenance
        if any((
            provenance.source_document_id != candidate["document_id"],
            provenance.source_document_fact_id != candidate["id"],
            provenance.source_page != candidate["page"],
            provenance.exact_span != candidate["exact_span"],
            provenance.exact_span_sha256 != candidate["exact_span_sha256"],
        )):
            return RejectionCode.UNSUPPORTED_PROVENANCE
        if candidate["status"] == "conflict" and payload.decision != FactDecision.REJECT:
            return RejectionCode.UNRESOLVED_CONFLICT
        if candidate["status"] != "proposed" and not (
            candidate["status"] == "conflict" and payload.decision == FactDecision.REJECT
        ):
            return RejectionCode.INVALID_TRANSITION

        if payload.decision == FactDecision.REJECT:
            candidate["status"] = "rejected"
            return [candidate["id"]], [], []

        superseded_material = None
        if payload.supersedes_health_fact_id:
            prior = state.facts.get(payload.supersedes_health_fact_id)
            if not prior or prior["status"] != "confirmed":
                return RejectionCode.UNSUPPORTED_PROVENANCE
            superseded_material = str(prior["value"].get("label", "")).casefold() or None
            prior["status"] = "superseded"
            prior["valid_to"] = command.submitted_at

        fact_id = uuid4()
        fact_value = payload.corrected_value if payload.decision == FactDecision.CORRECT else candidate["value"]
        state.facts[fact_id] = {
            "id": fact_id,
            "type": candidate["fact_type"],
            "value": deepcopy(fact_value),
            "status": "confirmed",
            "source_document_fact_id": candidate["id"],
            "supersedes_fact_id": payload.supersedes_health_fact_id,
            "valid_from": command.submitted_at,
            "valid_to": None,
        }
        candidate["status"] = "confirmed"
        candidate["committed_health_fact_id"] = fact_id
        material_key = payload.material_dependency_key or candidate["material_key"]
        affected, dependency_ids = self._invalidate_plans(
            state, candidate["fact_type"], material_key,
            f"confirmed_{candidate['fact_type']}_changed:{fact_id}",
        )
        if superseded_material and superseded_material != material_key.casefold():
            old_affected, old_dependencies = self._invalidate_plans(
                state, candidate["fact_type"], superseded_material,
                f"confirmed_fact_superseded:{payload.supersedes_health_fact_id}",
            )
            affected = sorted(set([*affected, *old_affected]), key=str)
            dependency_ids = sorted(set([*dependency_ids, *old_dependencies]))
        return [candidate["id"], fact_id], affected, dependency_ids

    def _apply_plan_create(self, state, payload, command):
        if payload.plan_id in state.plans:
            return RejectionCode.IDEMPOTENCY_CONFLICT
        if payload.journey_state_id != state.journey_state_id:
            return RejectionCode.STALE_STATE_VERSION
        personal_kinds = {"allergy", "dietary_restriction", "clinician_instruction"}
        active_constraints = {
            str(fact["value"].get("label", "")).casefold(): str(fact_id)
            for fact_id, fact in state.facts.items()
            if fact["status"] == "confirmed" and fact["type"] in personal_kinds
            and str(fact["value"].get("label", "")).strip()
        }
        dependency_keys = {item.material_key.casefold() for item in payload.dependencies}
        if any(material_key not in dependency_keys for material_key in active_constraints):
            return RejectionCode.MISSING_DEPENDENCY
        for material_key, fact_id in active_constraints.items():
            for item in payload.items:
                included = {value.casefold() for value in item.material_keys}
                excluded = {value.casefold() for value in item.excluded_material_keys}
                if material_key in included and material_key not in excluded:
                    return RejectionCode.VALIDATION_FAILED
                if material_key in included | excluded and (
                    material_key not in dependency_keys
                    or not ({fact_id, f"allergy:{material_key}", f"restriction:{material_key}"}
                            & set(item.applied_constraint_ids))
                ):
                    return RejectionCode.MISSING_DEPENDENCY
        state.plans[payload.plan_id] = {
            "id": payload.plan_id,
            "owner_user_id": state.owner_user_id,
            "workspace_id": state.workspace_id,
            "journey_state_id": payload.journey_state_id,
            "journey_state_version": state.journey_state_version,
            "journey_week": payload.journey_week,
            "source_release_id": payload.source_release_id,
            "status": PlanLifecycle.DRAFT.value,
            "created_at": command.submitted_at,
            "reviewed_at": None,
            "saved_at": None,
            "user_preferences": deepcopy(payload.user_preferences),
            "confirmed_constraints": list(payload.confirmed_constraints),
            "component_agent_outputs": deepcopy(payload.component_agent_outputs),
            "source_evidence_ids": list(payload.source_evidence_ids),
            "user_edits": deepcopy(payload.user_edits),
            "items": [item.model_dump(mode="json") for item in payload.items],
            "dependencies": [item.model_dump(mode="json") for item in payload.dependencies],
            "stale_reasons": [],
            "replacement_plan_id": None,
            "validation_trace_id": payload.validation_trace_id,
        }
        return [payload.plan_id], [], [f"plan:{payload.plan_id}:dependencies"]

    def _apply_plan_transition(self, state, payload, command):
        plan = state.plans.get(payload.plan_id)
        if not plan:
            return RejectionCode.NOT_FOUND
        current = PlanLifecycle(plan["status"])
        if current != payload.from_status or payload.to_status not in PLAN_TRANSITIONS[current]:
            return RejectionCode.INVALID_TRANSITION
        if payload.to_status in {PlanLifecycle.SAVED, PlanLifecycle.ACTIVE}:
            if plan["journey_state_id"] != state.journey_state_id:
                return RejectionCode.STALE_STATE_VERSION
            if plan["stale_reasons"]:
                return RejectionCode.VALIDATION_FAILED
        if payload.to_status == PlanLifecycle.REPLACED:
            replacement = state.plans.get(payload.replacement_plan_id)
            if not replacement or replacement["status"] not in {
                PlanLifecycle.SAVED.value, PlanLifecycle.ACTIVE.value,
            }:
                return RejectionCode.INVALID_TRANSITION
            plan["replacement_plan_id"] = payload.replacement_plan_id
        plan["status"] = payload.to_status.value
        if payload.to_status == PlanLifecycle.USER_REVIEWED:
            plan["reviewed_at"] = command.submitted_at
        if payload.to_status == PlanLifecycle.SAVED:
            if plan["reviewed_at"] is None:
                return RejectionCode.MISSING_CONFIRMATION
            plan["saved_at"] = command.submitted_at
        return [payload.plan_id], [], []

    def _apply_follow_up_create(self, state, payload, command):
        if payload.task_id in state.follow_up_tasks:
            return RejectionCode.IDEMPOTENCY_CONFLICT
        reminder_state = "not_requested"
        if payload.reminder:
            reminder_state = (
                "in_app_confirmed" if payload.reminder.channel == "in_app"
                else "external_delivery_unavailable"
            )
        state.follow_up_tasks[payload.task_id] = {
            "id": payload.task_id,
            "title": payload.title,
            "status": FollowUpStatus.CONFIRMED.value,
            "due_at": payload.due_at,
            "provenance_ids": list(payload.provenance_ids),
            "reminder": payload.reminder.model_dump(mode="json") if payload.reminder else None,
            "reminder_state": reminder_state,
            "external_delivery_scheduled": False,
            "created_at": command.submitted_at,
        }
        return [payload.task_id], [], []

    def _apply_follow_up_transition(self, state, payload, command):
        task = state.follow_up_tasks.get(payload.task_id)
        if not task:
            return RejectionCode.NOT_FOUND
        current = FollowUpStatus(task["status"])
        if current != payload.from_status or payload.to_status not in FOLLOW_UP_TRANSITIONS[current]:
            return RejectionCode.INVALID_TRANSITION
        task["status"] = payload.to_status.value
        task["updated_at"] = command.submitted_at
        return [payload.task_id], [], []

    def _apply_review_create(self, state, payload, command):
        if payload.case_id in state.review_cases:
            return RejectionCode.IDEMPOTENCY_CONFLICT
        if payload.reason == "urgent" and not payload.immediate_safety_completed:
            return RejectionCode.UNSAFE_CONTENT
        state.review_cases[payload.case_id] = {
            "id": payload.case_id,
            "state": ReviewState.OFFERED.value,
            "reason": payload.reason,
            "packet": payload.packet.model_dump(mode="json"),
            "simulated": True,
            "label": "Simulated review",
            "consented_at": None,
            "reviewed_at": None,
            "immediate_safety_completed": payload.immediate_safety_completed,
            "urgent_generation_call_count": 0,
        }
        return [payload.case_id], [], []

    def _apply_review_transition(self, state, payload, command):
        case = state.review_cases.get(payload.case_id)
        if not case:
            return RejectionCode.NOT_FOUND
        current = ReviewState(case["state"])
        if current != payload.from_state or payload.to_state not in REVIEW_TRANSITIONS[current]:
            return RejectionCode.INVALID_TRANSITION
        case["state"] = payload.to_state.value
        if payload.to_state == ReviewState.CONSENTED:
            case["consented_at"] = command.submitted_at
        if payload.to_state == ReviewState.REVIEWED:
            if case["consented_at"] is None:
                return RejectionCode.MISSING_CONFIRMATION
            case["reviewed_at"] = command.submitted_at
            case["response"] = payload.simulated_response
            case["response_label"] = "Simulated response"
        return [payload.case_id], [], []

    def _invalidate_plans(self, state, fact_type, material_key, reason):
        kind = {
            "allergy": DependencyKind.ALLERGY.value,
            "dietary_restriction": DependencyKind.RESTRICTION.value,
            "medical_history": DependencyKind.CONDITION.value,
            "medication": DependencyKind.MEDICATION.value,
            "clinician_instruction": DependencyKind.CLINICIAN_INSTRUCTION.value,
        }.get(fact_type, fact_type)
        affected: list[UUID] = []
        dependencies: list[str] = []
        for plan_id, plan in state.plans.items():
            matches = [
                item for item in plan["dependencies"]
                if item["kind"] == kind and item["material_key"] == material_key
            ]
            if not matches:
                continue
            if plan["status"] in {
                PlanLifecycle.DRAFT.value, PlanLifecycle.USER_REVIEWED.value,
                PlanLifecycle.SAVED.value, PlanLifecycle.ACTIVE.value,
            }:
                plan["status"] = PlanLifecycle.STALE.value
                plan["stale_reasons"] = sorted(set(plan["stale_reasons"] + [reason]))
                affected.append(plan_id)
                dependencies.extend(
                    f"{item['kind']}:{item['entity_id']}:{item['material_key']}" for item in matches
                )
        return affected, sorted(set(dependencies))

    def _authorized(self, scope):
        state = self._workspaces.get(scope.workspace_id)
        if not state or state.owner_user_id != scope.owner_user_id:
            raise PermissionError("authenticated owner workspace required")
        return state

    @staticmethod
    def _current_state(state):
        return {
            "workspace_id": str(state.workspace_id),
            "state_version": state.version,
            "journey_state_id": str(state.journey_state_id),
        }

    def _rejected(self, scope, command, version, code, status=CommitStatus.REJECTED):
        state = self._workspaces.get(scope.workspace_id)
        trace = CommitAuditTrace(
            command_id=command.command_id,
            workspace_id=scope.workspace_id,
            actor_user_id=scope.owner_user_id,
            command_kind=CommandKind(command.payload.kind),
            idempotency_key_hash=sha256(command.idempotency_key.encode()).hexdigest(),
            old_state_version=version,
            new_state_version=version,
            committed_at=datetime.now(timezone.utc),
        )
        return StateCommitResult(
            command_id=command.command_id,
            status=status,
            command_kind=CommandKind(command.payload.kind),
            old_state_version=version,
            new_state_version=version,
            rejection_code=code,
            current_state=self._current_state(state) if state else {},
            trace=trace,
        )

    @staticmethod
    def _trace(command, state, old_version, new_version, dependencies):
        return CommitAuditTrace(
            command_id=command.command_id,
            workspace_id=state.workspace_id,
            actor_user_id=state.owner_user_id,
            command_kind=CommandKind(command.payload.kind),
            idempotency_key_hash=sha256(command.idempotency_key.encode()).hexdigest(),
            old_state_version=old_version,
            new_state_version=new_version,
            affected_dependency_ids=dependencies,
            committed_at=datetime.now(timezone.utc),
        )


class SupabaseStateCommitterClient:
    """Authenticated PostgREST adapter for `public.stage10_commit`."""

    def __init__(self, url: str, publishable_key: str, user_access_token: str) -> None:
        if "service_role" in user_access_token.casefold():
            raise ValueError("service-role credentials are forbidden for ordinary state commits")
        self._url = url.rstrip("/")
        self._publishable_key = publishable_key
        self._token = user_access_token

    def load_snapshot(self, workspace_id: UUID) -> dict[str, Any]:
        """Reload authenticated durable truth; no session-state value is trusted."""
        body = json.dumps({"requested_workspace_id": str(workspace_id)}).encode()
        request = Request(
            f"{self._url}/rest/v1/rpc/stage10_durable_state",
            method="POST",
            data=body,
            headers={
                "apikey": self._publishable_key,
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:  # noqa: S310 - configured Supabase endpoint
                value = json.loads(response.read().decode())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"authenticated snapshot load failed: {exc.code} {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("authenticated snapshot storage is temporarily unavailable") from exc
        if not isinstance(value, dict) or not value.get("database_derived_state"):
            raise RuntimeError("authenticated snapshot was unavailable or not database-derived")
        return value
    def commit(self, workspace_id: UUID, command: StateCommitCommand) -> dict[str, Any]:
        body = json.dumps({
            "requested_workspace_id": str(workspace_id),
            "requested_command": command.model_dump(mode="json"),
        }).encode()
        request = Request(
            f"{self._url}/rest/v1/rpc/stage10_commit",
            method="POST",
            data=body,
            headers={
                "apikey": self._publishable_key,
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:  # noqa: S310 - configured Supabase endpoint
                return json.loads(response.read().decode())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"authenticated State Committer failed: {exc.code} {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("authenticated State Committer is temporarily unavailable") from exc


def _command_fingerprint(command: StateCommitCommand) -> str:
    payload = command.model_dump(mode="json", exclude={"command_id"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode()).hexdigest()


def _json_records(records) -> list[dict[str, Any]]:
    return json.loads(json.dumps(list(records), default=str))








