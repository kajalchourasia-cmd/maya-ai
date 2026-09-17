"""Bounded xAI Responses adapter for the fictional Stage 7 provider benchmark.

The adapter reuses Maya AI's audited summary-only provider boundary. It can
rewrite only an approved deterministic base summary, sends no personal facts or
retrieved evidence, enables no tools, stores no response, and uses low reasoning
effort. xAI's per-request billed-cost field is required and recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from json import JSONDecodeError
import json
import math
import os
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.services.model_provider import ProviderFailure
from app.services.redaction import redact_text
from app.services.openai_model_provider import (
    DATA_MODE,
    MAX_RESPONSE_BYTES,
    LiveProviderStatus,
    OpenAIProviderConfig,
    OpenAIResponsesProvider,
    OpenAITransport,
    _positive_float,
    _present,
)


XAI_RESPONSES_ENDPOINT = "https://api.x.ai/v1/responses"
PROVIDER_ID = "xai"
MODEL_ID = "grok-4.6"
USD_TICKS_PER_DOLLAR = 10_000_000_000


@dataclass(frozen=True)
class XAIProviderConfig(OpenAIProviderConfig):
    endpoint: str = XAI_RESPONSES_ENDPOINT
    data_mode: str = DATA_MODE


def inspect_xai_benchmark_configuration(
    environ: Mapping[str, str] | None = None,
) -> LiveProviderStatus:
    """Return non-secret xAI benchmark readiness without making a call."""

    values = environ if environ is not None else os.environ
    missing: list[str] = []
    model = values.get("NESTLINE_XAI_MODEL", "").strip()
    endpoint = values.get(
        "NESTLINE_XAI_RESPONSES_ENDPOINT", XAI_RESPONSES_ENDPOINT
    ).strip()
    for name in (
        "XAI_API_KEY",
        "NESTLINE_XAI_MODEL",
        "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE",
    ):
        if not _present(values.get(name)):
            missing.append(name)
    if model and model != MODEL_ID:
        missing.append(f"NESTLINE_XAI_MODEL={MODEL_ID}")
    if _positive_float(values, "NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD") is None:
        missing.append("NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD")
    if _positive_float(values, "NESTLINE_XAI_INPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_XAI_INPUT_USD_PER_1M")
    if _positive_float(values, "NESTLINE_XAI_OUTPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_XAI_OUTPUT_USD_PER_1M")
    error = None
    if endpoint != XAI_RESPONSES_ENDPOINT:
        error = "The xAI endpoint must use the fixed official Responses API URL."
    return LiveProviderStatus(
        enabled=True,
        ready=not missing and error is None,
        provider_id=PROVIDER_ID,
        model_id=model or None,
        data_mode=DATA_MODE,
        max_request_cost_usd=_positive_float(
            values, "NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD"
        ),
        missing_fields=tuple(missing),
        error=error,
    )


def inspect_xai_runtime_configuration(
    environ: Mapping[str, str] | None = None,
) -> LiveProviderStatus:
    """Return non-secret xAI runtime readiness without making a call."""

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
    missing: list[str] = []
    provider = values.get("NESTLINE_GENERATION_PROVIDER", "").strip().casefold()
    model = values.get("NESTLINE_GENERATION_MODEL", "").strip()
    data_mode = values.get(
        "NESTLINE_LIVE_PROVIDER_DATA_MODE", ""
    ).strip().casefold()
    endpoint = values.get(
        "NESTLINE_XAI_RESPONSES_ENDPOINT", XAI_RESPONSES_ENDPOINT
    ).strip()
    if provider != PROVIDER_ID:
        missing.append("NESTLINE_GENERATION_PROVIDER=xai")
    for name in (
        "XAI_API_KEY",
        "NESTLINE_GENERATION_MODEL",
        "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE",
    ):
        if not _present(values.get(name)):
            missing.append(name)
    if model and model != MODEL_ID:
        missing.append(f"NESTLINE_GENERATION_MODEL={MODEL_ID}")
    if data_mode != DATA_MODE:
        missing.append("NESTLINE_LIVE_PROVIDER_DATA_MODE=fictional_only")
    if _positive_float(values, "NESTLINE_GENERATION_MAX_COST_USD") is None:
        missing.append("NESTLINE_GENERATION_MAX_COST_USD")
    if _positive_float(values, "NESTLINE_XAI_INPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_XAI_INPUT_USD_PER_1M")
    if _positive_float(values, "NESTLINE_XAI_OUTPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_XAI_OUTPUT_USD_PER_1M")
    error = None
    if endpoint != XAI_RESPONSES_ENDPOINT:
        error = "The xAI endpoint must use the fixed official Responses API URL."
    return LiveProviderStatus(
        enabled=True,
        ready=not missing and error is None,
        provider_id=provider or None,
        model_id=model or None,
        data_mode=data_mode or None,
        max_request_cost_usd=_positive_float(
            values, "NESTLINE_GENERATION_MAX_COST_USD"
        ),
        missing_fields=tuple(missing),
        error=error,
    )


def load_xai_provider_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    transport: OpenAITransport | None = None,
) -> "XAIResponsesProvider":
    values = environ if environ is not None else os.environ
    status = inspect_xai_runtime_configuration(values)
    if not status.enabled:
        raise ProviderFailure("live provider is disabled")
    if not status.ready:
        detail = status.error or "missing or invalid fields: " + ", ".join(
            status.missing_fields
        )
        raise ProviderFailure(f"live provider configuration is not ready ({detail})")
    config = XAIProviderConfig(
        api_key=values["XAI_API_KEY"].strip(),
        model_id=values["NESTLINE_GENERATION_MODEL"].strip(),
        authorization_reference=values[
            "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE"
        ].strip(),
        max_request_cost_usd=float(values["NESTLINE_GENERATION_MAX_COST_USD"]),
        input_usd_per_million_tokens=float(
            values["NESTLINE_XAI_INPUT_USD_PER_1M"]
        ),
        output_usd_per_million_tokens=float(
            values["NESTLINE_XAI_OUTPUT_USD_PER_1M"]
        ),
        endpoint=values.get(
            "NESTLINE_XAI_RESPONSES_ENDPOINT", XAI_RESPONSES_ENDPOINT
        ).strip(),
    )
    return XAIResponsesProvider(config, transport=transport)


def load_xai_benchmark_provider_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    transport: OpenAITransport | None = None,
) -> "XAIResponsesProvider":
    values = environ if environ is not None else os.environ
    status = inspect_xai_benchmark_configuration(values)
    if not status.ready:
        detail = status.error or "missing or invalid fields: " + ", ".join(
            status.missing_fields
        )
        raise ProviderFailure(f"xAI benchmark configuration is not ready ({detail})")
    config = XAIProviderConfig(
        api_key=values["XAI_API_KEY"].strip(),
        model_id=values["NESTLINE_XAI_MODEL"].strip(),
        authorization_reference=values[
            "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE"
        ].strip(),
        max_request_cost_usd=float(
            values["NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD"]
        ),
        input_usd_per_million_tokens=float(
            values["NESTLINE_XAI_INPUT_USD_PER_1M"]
        ),
        output_usd_per_million_tokens=float(
            values["NESTLINE_XAI_OUTPUT_USD_PER_1M"]
        ),
        endpoint=values.get(
            "NESTLINE_XAI_RESPONSES_ENDPOINT", XAI_RESPONSES_ENDPOINT
        ).strip(),
    )
    return XAIResponsesProvider(config, transport=transport)


def _xai_default_transport(
    endpoint: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    request = Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        detail = ""
        try:
            error_payload = json.loads(exc.read(4096).decode("utf-8"))
            error = error_payload.get("error") if isinstance(error_payload, dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            if isinstance(message, str):
                detail = ": " + redact_text(" ".join(message.split())[:300])
        except (OSError, UnicodeDecodeError, JSONDecodeError):
            pass
        raise ProviderFailure(
            f"xAI Responses API returned HTTP {exc.code}{detail}"
        ) from None
    except (URLError, TimeoutError, OSError):
        raise ProviderFailure("xAI Responses API is unavailable") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ProviderFailure("xAI response exceeded the bounded response size")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, JSONDecodeError):
        raise ProviderFailure("xAI response was not valid JSON") from None
    if not isinstance(parsed, dict):
        raise ProviderFailure("xAI response had an invalid top-level shape")
    return parsed


class XAIResponsesProvider(OpenAIResponsesProvider):
    """xAI Grok adapter with exact billed-cost accounting."""

    provider_id = PROVIDER_ID
    provider_label = "xAI"
    responses_endpoint = XAI_RESPONSES_ENDPOINT
    reasoning_effort = "low"

    def __init__(
        self,
        config: XAIProviderConfig,
        *,
        transport: OpenAITransport | None = None,
    ) -> None:
        super().__init__(
            config,
            transport=transport or _xai_default_transport,
        )

    def _charged_cost(
        self,
        usage: dict[str, Any],
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        del input_tokens, output_tokens
        ticks = usage.get("cost_in_usd_ticks")
        if not isinstance(ticks, int) or isinstance(ticks, bool) or ticks < 0:
            raise ProviderFailure("xAI response omitted valid billed-cost ticks")
        cost = ticks / USD_TICKS_PER_DOLLAR
        if not math.isfinite(cost):
            raise ProviderFailure("xAI response returned an invalid billed cost")
        return cost
