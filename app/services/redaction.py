"""Data-minimising trace redaction shared by providers, errors, and audits."""

from __future__ import annotations

from hashlib import sha256
import re
from typing import Any


SENSITIVE_FIELDS = {
    "api_key",
    "authorization",
    "access_token",
    "refresh_token",
    "service_role_key",
    "secret",
    "password",
    "text",
    "question",
    "summary",
    "exact_span",
    "document_text",
    "symptom",
    "symptoms",
    "medication",
    "medications",
    "user_reported_context",
}
IDENTIFIER_FIELDS = {
    "owner_id",
    "owner_user_id",
    "workspace_id",
    "care_episode_id",
    "document_id",
    "user_id",
    "session_subject",
}
TOKEN_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]+\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b"),
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE
)


def _hash_identifier(value: Any) -> str:
    digest = sha256(str(value).encode("utf-8")).hexdigest()[:12]
    return f"redacted:{digest}"


def redact_text(value: str) -> str:
    result = value
    for pattern in TOKEN_PATTERNS:
        result = pattern.sub("[REDACTED_CREDENTIAL]", result)
    result = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", result)
    return result


def redact_for_trace(value: Any, *, field_name: str | None = None) -> Any:
    """Recursively remove content and stable-identify scope without exposing it."""

    key = (field_name or "").casefold()
    if key in SENSITIVE_FIELDS or any(
        marker in key for marker in ("token", "password", "secret", "api_key")
    ):
        return "[REDACTED]"
    if key in IDENTIFIER_FIELDS:
        return _hash_identifier(value)
    if isinstance(value, dict):
        return {
            str(item_key): redact_for_trace(item_value, field_name=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact_for_trace(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_for_trace(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


def provider_trace_metadata(
    *, provider: str, model: str, request: dict[str, Any], error: str | None = None
) -> dict[str, Any]:
    """Return an opt-in trace envelope with content and credentials removed."""

    return {
        "provider": redact_text(provider),
        "model": redact_text(model),
        "request": redact_for_trace(request),
        "error": None if error is None else redact_text(error),
    }


def audit_trace_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Redact State Committer audit metadata before any external trace export."""

    return redact_for_trace(metadata)