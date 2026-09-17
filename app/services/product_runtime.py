"""Normal UI integration boundary, independent of fixture setup code.

This carries ephemeral user input; it is NOT an authenticated Supabase scope.
The existing Stage 5-8 stack must be bound here after corpus and database-session
access are available. Until then ordinary requests fail explicitly, not via
fixture answers or invented clinical clarification.
"""
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID
from fastapi import Request

from app.schemas.retrieval import JourneyPosition


@dataclass(frozen=True)
class ProductContext:
    session_id: UUID
    state_version: int
    journey: JourneyPosition
    journey_label: str
    diets: tuple[str, ...]
    allergies: tuple[str, ...]
    symptoms: tuple[str, ...]
    origin: Literal["user_entered_session"] = "user_entered_session"
    restrictions: tuple[str, ...] = ()
    active_conditions: tuple[str, ...] = ()
    activity_background: str = ""
    history: tuple[tuple[str, str], ...] = ()


class ProductRuntimeUnavailable(RuntimeError):
    code = "corpus_not_connected"

    def __init__(self, message: str, *, code: str = "corpus_not_connected", status_code: int = 503):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class ProductRuntime(Protocol):
    def chat(self, *, context: ProductContext, text: str) -> dict: ...
    def plan(self, *, context: ProductContext, horizon: str, focus: str) -> dict: ...


class UnconnectedProductRuntime:
    @staticmethod
    def _unavailable():
        raise ProductRuntimeUnavailable(
            "Live answer generation is not activated for this session. "
            "Your onboarding information is retained for this session. This is a "
            "setup issue, not a medical safety restriction. Dashboard reference "
            "guidance remains available; live answers and plans require the configured runtime and its access policy."
        )

    def chat(self, *, context: ProductContext, text: str) -> dict:
        return self._unavailable()

    def plan(self, *, context: ProductContext, horizon: str, focus: str) -> dict:
        return self._unavailable()


def get_product_runtime(request: Request) -> ProductRuntime:
    # Same dependency for normal HTTP and private end-to-end tests. No fixture
    # overrides are used by the live verifier. Activation is explicit server config.
    from app.services.grounded_runtime import configured_runtime
    return configured_runtime(request)
