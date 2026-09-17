"""Fail-closed dispatcher for an explicitly selected live summary provider."""

from __future__ import annotations

import os
from typing import Mapping

from app.services.model_provider import ProviderFailure, StructuredProvider
from app.services.openai_model_provider import (
    LiveProviderStatus,
    inspect_live_provider_configuration as inspect_openai_runtime_configuration,
    load_openai_provider_from_env,
)
from app.services.xai_model_provider import (
    inspect_xai_runtime_configuration,
    load_xai_provider_from_env,
)


def inspect_selected_provider_configuration(
    environ: Mapping[str, str] | None = None,
) -> LiveProviderStatus:
    values = environ if environ is not None else os.environ
    enabled = (
        values.get("NESTLINE_ENABLE_LIVE_PROVIDER", "").strip().casefold()
        == "true"
    )
    if not enabled:
        return LiveProviderStatus(
            enabled=False,
            ready=False,
            provider_id=None,
            model_id=None,
            data_mode=None,
            max_request_cost_usd=None,
            missing_fields=(),
        )
    provider = values.get("NESTLINE_GENERATION_PROVIDER", "").strip().casefold()
    if provider == "openai":
        return inspect_openai_runtime_configuration(values)
    if provider == "xai":
        return inspect_xai_runtime_configuration(values)
    return LiveProviderStatus(
        enabled=True,
        ready=False,
        provider_id=provider or None,
        model_id=values.get("NESTLINE_GENERATION_MODEL", "").strip() or None,
        data_mode=values.get(
            "NESTLINE_LIVE_PROVIDER_DATA_MODE", ""
        ).strip().casefold()
        or None,
        max_request_cost_usd=None,
        missing_fields=("NESTLINE_GENERATION_PROVIDER=openai|xai",),
        error="The selected live provider is unsupported.",
    )


def load_selected_provider_from_env(
    environ: Mapping[str, str] | None = None,
) -> StructuredProvider:
    values = environ if environ is not None else os.environ
    status = inspect_selected_provider_configuration(values)
    if not status.enabled:
        raise ProviderFailure("live provider is disabled")
    if not status.ready:
        detail = status.error or "missing or invalid fields: " + ", ".join(
            status.missing_fields
        )
        raise ProviderFailure(f"live provider configuration is not ready ({detail})")
    if status.provider_id == "openai":
        return load_openai_provider_from_env(values)
    if status.provider_id == "xai":
        return load_xai_provider_from_env(values)
    raise ProviderFailure("selected live provider is unsupported")
