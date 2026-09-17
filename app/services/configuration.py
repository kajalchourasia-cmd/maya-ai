"""Typed, secret-safe configuration validation for Demo and Personal modes."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Mapping

from pydantic import Field, model_validator

from app.schemas.content import Contract


class ApplicationMode(StrEnum):
    DEMO = "demo"
    PERSONAL = "personal"


class ComponentStatus(Contract):
    component: str
    status: Literal["ready", "disabled", "incomplete", "blocked"]
    provider: str | None = None
    model: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    reason: str | None = None


class ConfigurationReport(Contract):
    schema_version: Literal["nestline-configuration-v1"] = "nestline-configuration-v1"
    mode: ApplicationMode
    valid: bool
    fixture_provider_permitted: bool
    supabase: ComponentStatus
    generation: ComponentStatus
    embedding: ComponentStatus
    document_extraction: ComponentStatus
    scanner: ComponentStatus
    tracing: ComponentStatus
    secret_values_reported: Literal[False] = False
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validity_matches_errors(self):
        if self.valid == bool(self.errors):
            raise ValueError("configuration validity must be the inverse of errors")
        if self.mode == ApplicationMode.PERSONAL and self.fixture_provider_permitted:
            raise ValueError("Personal Mode cannot permit fixture providers")
        return self


def _present(values: Mapping[str, str], name: str) -> bool:
    raw = values.get(name, "").strip()
    if not raw:
        return False
    upper = raw.upper()
    return not any(marker in upper for marker in ("YOUR_", "REPLACE_ME", "CHOOSE_"))


def _component(
    name: str,
    values: Mapping[str, str],
    *,
    enabled: bool,
    required: tuple[str, ...],
    provider_field: str | None = None,
    model_field: str | None = None,
    disabled_reason: str,
) -> ComponentStatus:
    provider = values.get(provider_field, "").strip() if provider_field else None
    model = values.get(model_field, "").strip() if model_field else None
    if not enabled:
        return ComponentStatus(
            component=name,
            status="disabled",
            provider=provider or None,
            model=model or None,
            reason=disabled_reason,
        )
    missing = [field for field in required if not _present(values, field)]
    return ComponentStatus(
        component=name,
        status="incomplete" if missing else "ready",
        provider=provider or None,
        model=model or None,
        missing_fields=missing,
        reason=("Required fields are absent." if missing else None),
    )


def validate_configuration(
    values: Mapping[str, str],
    *,
    mode: ApplicationMode,
) -> ConfigurationReport:
    """Return status names and identities only; never include credential values."""

    errors: list[str] = []
    fixture_permitted = mode == ApplicationMode.DEMO
    supabase = _component(
        "supabase_public",
        values,
        enabled=mode == ApplicationMode.PERSONAL,
        required=("NESTLINE_SUPABASE_URL", "NESTLINE_SUPABASE_PUBLISHABLE_KEY"),
        disabled_reason="Demo Mode uses isolated fictional in-memory storage.",
    )
    live_enabled = values.get("NESTLINE_ENABLE_LIVE_PROVIDER", "").casefold() == "true"
    generation = _component(
        "generation",
        values,
        enabled=live_enabled,
        required=(
            "NESTLINE_GENERATION_PROVIDER",
            "NESTLINE_GENERATION_MODEL",
            "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE",
            "NESTLINE_GENERATION_MAX_COST_USD",
        ),
        provider_field="NESTLINE_GENERATION_PROVIDER",
        model_field="NESTLINE_GENERATION_MODEL",
        disabled_reason="No live provider is selected; deterministic provider is Demo/test-only.",
    )
    embedding_enabled = _present(values, "NESTLINE_EMBEDDING_PROVIDER")
    embedding = _component(
        "embedding",
        values,
        enabled=embedding_enabled,
        required=("NESTLINE_EMBEDDING_PROVIDER", "NESTLINE_EMBEDDING_MODEL"),
        provider_field="NESTLINE_EMBEDDING_PROVIDER",
        model_field="NESTLINE_EMBEDDING_MODEL",
        disabled_reason="Lexical and exact retrieval remain available; semantic retrieval is disabled.",
    )
    document_enabled = (
        values.get("NESTLINE_ENABLE_DOCUMENT_PROVIDER", "").casefold() == "true"
    )
    document = _component(
        "document_extraction",
        values,
        enabled=document_enabled,
        required=(
            "NESTLINE_DOCUMENT_PROVIDER",
            "NESTLINE_DOCUMENT_MODEL",
            "NESTLINE_DOCUMENT_MAX_COST_USD",
        ),
        provider_field="NESTLINE_DOCUMENT_PROVIDER",
        model_field="NESTLINE_DOCUMENT_MODEL",
        disabled_reason="Deterministic fictional document fixtures remain available in Demo Mode only.",
    )
    real_uploads = values.get("NESTLINE_ENABLE_REAL_UPLOADS", "").casefold() == "true"
    scanner_name = values.get("NESTLINE_UPLOAD_SCANNER", "unavailable").strip().casefold()
    scanner_ready = real_uploads and scanner_name not in {"", "unavailable", "disabled"}
    scanner = ComponentStatus(
        component="upload_scanner",
        status="ready" if scanner_ready else ("blocked" if real_uploads else "disabled"),
        provider=scanner_name or None,
        missing_fields=(
            ["NESTLINE_UPLOAD_SCANNER", "NESTLINE_UPLOAD_SCAN_ENDPOINT"]
            if real_uploads and not scanner_ready else []
        ),
        reason=(
            None
            if scanner_ready
            else "Real uploads remain fail-closed pending scanner, privacy, retention, and deletion approval."
        ),
    )
    tracing_enabled = values.get("LANGSMITH_TRACING", "").casefold() == "true"
    tracing = _component(
        "tracing",
        values,
        enabled=tracing_enabled,
        required=("LANGSMITH_API_KEY", "LANGSMITH_WORKSPACE_ID", "LANGSMITH_ENDPOINT"),
        provider_field="LANGSMITH_ENDPOINT",
        disabled_reason="Trace export is opt-in and disabled.",
    )
    if tracing_enabled and values.get("NESTLINE_TRACE_REDACTION", "").casefold() != "true":
        tracing = tracing.model_copy(
            update={
                "status": "blocked",
                "reason": "Trace export requires explicit redaction.",
                "missing_fields": ["NESTLINE_TRACE_REDACTION=true"],
            }
        )

    if mode == ApplicationMode.PERSONAL:
        if supabase.status != "ready":
            errors.append("Personal Mode requires complete public Supabase configuration.")
        if generation.status != "ready":
            errors.append("Personal Mode requires an explicitly enabled configured provider.")
        if generation.provider in {"deterministic_fixture", "scripted_test_fixture", "fixture"}:
            errors.append("Personal Mode cannot select a fixture provider.")
        if values.get("NESTLINE_ALLOW_DEMO_FIXTURES_IN_PERSONAL", "").casefold() == "true":
            errors.append("Demo fixtures cannot enter Personal Mode.")
    if real_uploads and scanner.status != "ready":
        errors.append("Real uploads cannot start without the approved scanner boundary.")
    if tracing.status == "blocked":
        errors.append("Tracing cannot start without redaction.")
    forbidden_names = (
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "NESTLINE_SERVICE_ROLE_KEY",
    )
    if any(_present(values, name) for name in forbidden_names):
        errors.append("Ordinary application configuration must not contain service-role credentials.")

    return ConfigurationReport(
        mode=mode,
        valid=not errors,
        fixture_provider_permitted=fixture_permitted,
        supabase=supabase,
        generation=generation,
        embedding=embedding,
        document_extraction=document,
        scanner=scanner,
        tracing=tracing,
        errors=errors,
    )
