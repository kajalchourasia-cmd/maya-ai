"""Mode-safe application facade for the single Stage 10 write boundary."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from app.schemas.state_lifecycle import (
    AuthenticatedCommitScope,
    DurableSnapshot,
    StateCommitCommand,
    StateCommitResult,
)
from app.services.confirmed_context import ConfirmedContextService
from app.services.state_committer import (
    InMemoryStateCommitter,
    SupabaseStateCommitterClient,
)


class StateServiceMode(StrEnum):
    DEMO = "demo"
    PERSONAL = "personal"


class PersonalCommitClient(Protocol):
    def load_snapshot(self, workspace_id: UUID) -> dict[str, Any]: ...
    def commit(
        self, workspace_id: UUID, command: StateCommitCommand
    ) -> dict[str, Any]: ...


ScopeResolver = Callable[[UUID], AuthenticatedCommitScope]


class ModeSafeStateService:
    """Select exactly one committer from authenticated mode, never from UI state."""

    def __init__(
        self,
        *,
        mode: StateServiceMode,
        scope_resolver: ScopeResolver,
        demo_committer: InMemoryStateCommitter | None = None,
        personal_client: PersonalCommitClient | None = None,
        fixture_workspace_ids: frozenset[UUID] = frozenset(),
    ) -> None:
        self.mode = mode
        self._resolve_scope = scope_resolver
        self._demo = demo_committer
        self._personal = personal_client
        self._fixture_ids = fixture_workspace_ids
        if mode == StateServiceMode.DEMO:
            if demo_committer is None or personal_client is not None:
                raise ValueError("Demo Mode requires only the in-memory fixture committer")
            if not fixture_workspace_ids:
                raise ValueError("Demo Mode requires an explicit fixture workspace allowlist")
        else:
            if personal_client is None or demo_committer is not None:
                raise ValueError("Personal Mode requires only an authenticated Supabase client")
            if isinstance(personal_client, InMemoryStateCommitter):
                raise ValueError("Personal Mode cannot use the fixture committer")
            if fixture_workspace_ids:
                raise ValueError("Personal Mode cannot receive fixture workspace IDs")

    @classmethod
    def demo(
        cls,
        *,
        committer: InMemoryStateCommitter,
        scope_resolver: ScopeResolver,
        fixture_workspace_ids: frozenset[UUID],
    ) -> "ModeSafeStateService":
        return cls(
            mode=StateServiceMode.DEMO,
            scope_resolver=scope_resolver,
            demo_committer=committer,
            fixture_workspace_ids=fixture_workspace_ids,
        )

    @classmethod
    def personal(
        cls,
        *,
        client: SupabaseStateCommitterClient,
        scope_resolver: ScopeResolver,
    ) -> "ModeSafeStateService":
        return cls(
            mode=StateServiceMode.PERSONAL,
            scope_resolver=scope_resolver,
            personal_client=client,
        )

    def _trusted_scope(
        self,
        requested_workspace_id: UUID,
        *,
        expected_state_version: int | None = None,
    ) -> AuthenticatedCommitScope:
        scope = self._resolve_scope(requested_workspace_id)
        if scope.workspace_id != requested_workspace_id:
            raise PermissionError(
                "client workspace cannot override authenticated scope resolution"
            )
        if self.mode == StateServiceMode.DEMO:
            if scope.workspace_id not in self._fixture_ids:
                raise PermissionError("Demo Mode cannot access a personal workspace")
        elif scope.workspace_id in self._fixture_ids:
            raise PermissionError("Personal Mode cannot access a Demo workspace")
        # Ownership is checked here; optimistic concurrency is checked inside the
        # committer transaction so a stale caller receives the typed current-state
        # response rather than a facade exception.
        ConfirmedContextService.validate_commit_scope(
            scope,
            expected_workspace_id=str(scope.workspace_id),
            expected_state_version=scope.current_state_version,
        )
        return scope

    def load_snapshot(
        self, requested_workspace_id: UUID
    ) -> DurableSnapshot | dict[str, Any]:
        scope = self._trusted_scope(requested_workspace_id)
        if self.mode == StateServiceMode.DEMO:
            assert self._demo is not None
            return self._demo.load_snapshot(scope)
        assert self._personal is not None
        value = self._personal.load_snapshot(scope.workspace_id)
        returned_workspace = value.get("workspace_id")
        returned_owner = value.get("owner_user_id")
        if returned_workspace is not None and str(returned_workspace) != str(scope.workspace_id):
            raise PermissionError("database snapshot returned another workspace")
        if returned_owner is not None and str(returned_owner) != str(scope.owner_user_id):
            raise PermissionError("database snapshot returned another owner")
        if value.get("database_derived_state") is not True:
            raise RuntimeError("Personal Mode requires database-derived durable truth")
        return value

    def commit(
        self,
        requested_workspace_id: UUID,
        command: StateCommitCommand,
    ) -> StateCommitResult | dict[str, Any]:
        scope = self._trusted_scope(requested_workspace_id)
        if self.mode == StateServiceMode.DEMO:
            assert self._demo is not None
            return self._demo.commit(scope, command)
        assert self._personal is not None
        # The authenticated database RPC re-resolves ownership and version inside
        # its transaction; the client never sends an owner identity.
        return self._personal.commit(scope.workspace_id, command)
