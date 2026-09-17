"""Canonical authenticated journey context shared by Stages 3, 5, 7 and 10."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.schemas.content import Contract
from app.schemas.orchestration import AuthenticatedContextSnapshot
from app.schemas.retrieval import (
    AuthenticatedRetrievalScope,
    ExactPersonalContext,
    JourneyPosition,
    JourneyStateSnapshot,
)
from app.schemas.state_lifecycle import AuthenticatedCommitScope


class CanonicalConfirmedContext(Contract):
    """Server-derived journey truth; user text cannot supply these fields."""

    schema_version: Literal["canonical-confirmed-context-v1"] = (
        "canonical-confirmed-context-v1"
    )
    workspace_id: str
    care_episode_id: str
    owner_user_id: str
    session_subject: str
    state_version: int = Field(ge=1)
    journey: JourneyPosition | None = None
    timing_source: str | None = None
    provenance: Literal["confirmed_journey_resolver", "missing_or_unconfirmed"]
    confirmation_status: Literal["confirmed", "unconfirmed", "conflicting", "missing"]
    conflict_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    active_condition_keys: list[str] = Field(default_factory=list)
    active_restriction_fact_ids: list[str] = Field(default_factory=list)
    personalization_permitted: bool

    @model_validator(mode="after")
    def status_and_permission_agree(self):
        expected = (
            self.confirmation_status == "confirmed"
            and self.journey is not None
            and not self.conflict_ids
            and not self.missing_fields
            and self.owner_user_id == self.session_subject
            and self.workspace_id == self.care_episode_id
        )
        if self.personalization_permitted != expected:
            raise ValueError(
                "personalization permission must follow confirmed server-derived context"
            )
        return self


def confirmed_journey_position(
    snapshot: JourneyStateSnapshot | None,
) -> JourneyPosition | None:
    """Return a position only from a confirmed, conflict-free resolver snapshot."""

    if snapshot is None or not snapshot.user_confirmed or snapshot.has_dating_conflict:
        return None
    if snapshot.stage == "possible_pregnancy":
        return JourneyPosition(stage="possible_pregnancy", unit="none")
    if snapshot.stage == "pregnancy" and snapshot.gestational_week is not None:
        return JourneyPosition(
            stage="pregnancy", unit="week", exact=snapshot.gestational_week
        )
    if snapshot.stage == "postpartum" and snapshot.postpartum_day is not None:
        return JourneyPosition(
            stage="postpartum", unit="day", exact=snapshot.postpartum_day
        )
    if snapshot.stage == "postpartum" and snapshot.postpartum_week is not None:
        return JourneyPosition(
            stage="postpartum", unit="week", exact=snapshot.postpartum_week
        )
    return None


def _condition_keys(exact: ExactPersonalContext) -> list[str]:
    values: set[str] = set()
    for fact in exact.confirmed_facts:
        if isinstance(fact.value, dict):
            key = fact.value.get("condition_key")
            state = fact.value.get("condition_status", fact.value.get("status"))
            if isinstance(key, str) and state in {"confirmed_present", "present", True}:
                values.add(key)
    return sorted(values)


def _restriction_ids(exact: ExactPersonalContext) -> list[str]:
    return sorted(
        str(fact.fact_id)
        for fact in exact.confirmed_facts
        if fact.fact_type in {"dietary_restriction", "clinician_instruction"}
        or (
            isinstance(fact.value, dict)
            and fact.value.get("condition_key")
            in {
                "movement_restriction",
                "exercise_clearance",
                "feels_ready_for_gentle_activity",
            }
        )
    )


class ConfirmedContextService:
    """Build and validate the one downstream context boundary."""

    @staticmethod
    def from_retrieval(
        scope: AuthenticatedRetrievalScope,
        exact: ExactPersonalContext,
    ) -> CanonicalConfirmedContext:
        journey = confirmed_journey_position(exact.journey_state)
        conflicts = sorted(str(item.conflict_id) for item in exact.unresolved_conflicts)
        missing = sorted({item.field for item in exact.missing_information})
        if exact.journey_state is None:
            status = "missing"
        elif exact.journey_state.has_dating_conflict or conflicts:
            status = "conflicting"
        elif not exact.journey_state.user_confirmed or journey is None:
            status = "unconfirmed"
        else:
            status = "confirmed"
        permitted = (
            status == "confirmed"
            and not missing
            and scope.owner_user_id == scope.session_subject
            and scope.workspace_id == scope.care_episode_id
        )
        return CanonicalConfirmedContext(
            workspace_id=str(scope.workspace_id),
            care_episode_id=str(scope.care_episode_id),
            owner_user_id=str(scope.owner_user_id),
            session_subject=str(scope.session_subject),
            state_version=scope.state_version,
            journey=journey,
            timing_source=(
                exact.journey_state.timing_source if exact.journey_state else None
            ),
            provenance=(
                "confirmed_journey_resolver" if permitted
                else "missing_or_unconfirmed"
            ),
            confirmation_status=status,
            conflict_ids=conflicts,
            missing_fields=missing,
            active_condition_keys=_condition_keys(exact),
            active_restriction_fact_ids=_restriction_ids(exact),
            personalization_permitted=permitted,
        )

    @staticmethod
    def validate_orchestration(
        snapshot: AuthenticatedContextSnapshot,
    ) -> AuthenticatedContextSnapshot:
        if snapshot.owner_user_id != snapshot.session_subject:
            raise ValueError("orchestration context is not owned by the session")
        if snapshot.care_episode_id != snapshot.workspace_id:
            raise ValueError("orchestration context crossed the care-episode boundary")
        if not snapshot.onboarding_confirmed:
            raise ValueError("unconfirmed journey context cannot personalize an agent")
        return snapshot

    @staticmethod
    def validate_commit_scope(
        scope: AuthenticatedCommitScope,
        *,
        expected_workspace_id: str,
        expected_state_version: int,
    ) -> AuthenticatedCommitScope:
        if str(scope.workspace_id) != expected_workspace_id:
            raise ValueError("commit workspace differs from authenticated context")
        if scope.current_state_version != expected_state_version:
            raise ValueError("commit state version differs from authenticated context")
        if scope.care_episode_id != scope.workspace_id:
            raise ValueError("commit care episode differs from its workspace")
        if scope.service_role_used:
            raise ValueError("ordinary state commits cannot use service-role credentials")
        return scope
