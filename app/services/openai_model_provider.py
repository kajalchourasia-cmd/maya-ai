"""Explicit, bounded OpenAI Responses adapter for fictional Stage 7 evaluation.

The adapter is deliberately narrow: the model may rewrite only the already
validated summary. Facts, citations, constraints, actions and schedules remain
the deterministic draft created by Maya AI. No live call is possible until an
operator enables it, selects an exact model, records authorization and supplies
an explicit request-cost ceiling and current token prices.
"""

from __future__ import annotations

from dataclasses import dataclass
from json import JSONDecodeError
import json
import math
import os
from time import perf_counter
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.orchestration import AgentBudget, AgentName
from app.services.model_provider import ProviderFailure, ProviderResponse
from app.services.redaction import redact_text


OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
PROVIDER_ID = "openai"
DATA_MODE = "fictional_only"
MAX_SUMMARY_CHARACTERS = 600
MAX_RESPONSE_BYTES = 1_000_000
ALLOWED_BASE_SUMMARIES = {
    AgentName.RECORD: "This document says the following. Please check the source details and confirmation state.",
    AgentName.MEDICATION: "Here is the chronological medication and supplement information documented in your record.",
    AgentName.SYMPTOM: "I can help organize a cautious next step, but I cannot diagnose or confirm that a symptom is safe.",
    AgentName.NUTRITION: "Here is a practical option after applying your confirmed food constraints.",
    AgentName.MOVEMENT: "Here is a conservative movement option based on the cited stage-applicable material.",
    AgentName.WELLBEING: "It makes sense to want support. You can choose whether this brief option feels useful.",
    AgentName.FOLLOWUP: "Here is a concise appointment and follow-up brief, separated by when each task belongs.",
    AgentName.PLAN_COMPOSER: (
        "I arranged the validated contributions into an editable proposal. "
        "Please review every constraint and uncertainty before choosing what to do next."
    ),
}


class _SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    summary: str = Field(min_length=1, max_length=MAX_SUMMARY_CHARACTERS)


@dataclass(frozen=True)
class OpenAIProviderConfig:
    api_key: str
    model_id: str
    authorization_reference: str
    max_request_cost_usd: float
    input_usd_per_million_tokens: float
    output_usd_per_million_tokens: float
    endpoint: str = OPENAI_RESPONSES_ENDPOINT
    data_mode: str = DATA_MODE


@dataclass(frozen=True)
class LiveProviderStatus:
    enabled: bool
    ready: bool
    provider_id: str | None
    model_id: str | None
    data_mode: str | None
    max_request_cost_usd: float | None
    missing_fields: tuple[str, ...]
    error: str | None = None


OpenAITransport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


def _present(value: str | None) -> bool:
    if value is None or not value.strip():
        return False
    upper = value.strip().upper()
    return not any(marker in upper for marker in ("REPLACE_ME", "YOUR_", "CHOOSE_"))


def _positive_float(values: Mapping[str, str], name: str) -> float | None:
    raw = values.get(name, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if math.isfinite(value) and value > 0 else None


def inspect_live_provider_configuration(
    environ: Mapping[str, str] | None = None,
) -> LiveProviderStatus:
    """Return non-secret readiness information without making a network call."""

    values = environ if environ is not None else os.environ
    enabled = values.get("NESTLINE_ENABLE_LIVE_PROVIDER", "").strip().casefold() == "true"
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
    data_mode = values.get("NESTLINE_LIVE_PROVIDER_DATA_MODE", "").strip().casefold()
    endpoint = values.get("NESTLINE_OPENAI_RESPONSES_ENDPOINT", OPENAI_RESPONSES_ENDPOINT).strip()
    if provider != PROVIDER_ID:
        missing.append("NESTLINE_GENERATION_PROVIDER=openai")
    for name in (
        "OPENAI_API_KEY",
        "NESTLINE_GENERATION_MODEL",
        "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE",
    ):
        if not _present(values.get(name)):
            missing.append(name)
    if data_mode != DATA_MODE:
        missing.append("NESTLINE_LIVE_PROVIDER_DATA_MODE=fictional_only")
    if _positive_float(values, "NESTLINE_GENERATION_MAX_COST_USD") is None:
        missing.append("NESTLINE_GENERATION_MAX_COST_USD")
    if _positive_float(values, "NESTLINE_OPENAI_INPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_OPENAI_INPUT_USD_PER_1M")
    if _positive_float(values, "NESTLINE_OPENAI_OUTPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_OPENAI_OUTPUT_USD_PER_1M")
    error = None
    if endpoint != OPENAI_RESPONSES_ENDPOINT:
        error = "The OpenAI endpoint must use the fixed official Responses API URL."
    return LiveProviderStatus(
        enabled=True,
        ready=not missing and error is None,
        provider_id=provider or None,
        model_id=model or None,
        data_mode=data_mode or None,
        max_request_cost_usd=_positive_float(values, "NESTLINE_GENERATION_MAX_COST_USD"),
        missing_fields=tuple(missing),
        error=error,
    )


def load_openai_provider_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    transport: OpenAITransport | None = None,
) -> "OpenAIResponsesProvider":
    values = environ if environ is not None else os.environ
    status = inspect_live_provider_configuration(values)
    if not status.enabled:
        raise ProviderFailure("live provider is disabled")
    if not status.ready:
        detail = status.error or "missing or invalid fields: " + ", ".join(status.missing_fields)
        raise ProviderFailure(f"live provider configuration is not ready ({detail})")
    config = OpenAIProviderConfig(
        api_key=values["OPENAI_API_KEY"].strip(),
        model_id=values["NESTLINE_GENERATION_MODEL"].strip(),
        authorization_reference=values["NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE"].strip(),
        max_request_cost_usd=float(values["NESTLINE_GENERATION_MAX_COST_USD"]),
        input_usd_per_million_tokens=float(values["NESTLINE_OPENAI_INPUT_USD_PER_1M"]),
        output_usd_per_million_tokens=float(values["NESTLINE_OPENAI_OUTPUT_USD_PER_1M"]),
        endpoint=values.get("NESTLINE_OPENAI_RESPONSES_ENDPOINT", OPENAI_RESPONSES_ENDPOINT).strip(),
        data_mode=values["NESTLINE_LIVE_PROVIDER_DATA_MODE"].strip().casefold(),
    )
    return OpenAIResponsesProvider(config, transport=transport)


def inspect_openai_benchmark_configuration(
    environ: Mapping[str, str] | None = None,
) -> LiveProviderStatus:
    """Return non-secret OpenAI benchmark readiness without making a call."""

    values = environ if environ is not None else os.environ
    missing: list[str] = []
    model = values.get("NESTLINE_OPENAI_MODEL", "").strip()
    endpoint = values.get(
        "NESTLINE_OPENAI_RESPONSES_ENDPOINT", OPENAI_RESPONSES_ENDPOINT
    ).strip()
    for name in (
        "OPENAI_API_KEY",
        "NESTLINE_OPENAI_MODEL",
        "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE",
    ):
        if not _present(values.get(name)):
            missing.append(name)
    if _positive_float(values, "NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD") is None:
        missing.append("NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD")
    if _positive_float(values, "NESTLINE_OPENAI_INPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_OPENAI_INPUT_USD_PER_1M")
    if _positive_float(values, "NESTLINE_OPENAI_OUTPUT_USD_PER_1M") is None:
        missing.append("NESTLINE_OPENAI_OUTPUT_USD_PER_1M")
    error = None
    if endpoint != OPENAI_RESPONSES_ENDPOINT:
        error = "The OpenAI endpoint must use the fixed official Responses API URL."
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


def load_openai_benchmark_provider_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    transport: OpenAITransport | None = None,
) -> "OpenAIResponsesProvider":
    values = environ if environ is not None else os.environ
    status = inspect_openai_benchmark_configuration(values)
    if not status.ready:
        detail = status.error or "missing or invalid fields: " + ", ".join(
            status.missing_fields
        )
        raise ProviderFailure(
            f"OpenAI benchmark configuration is not ready ({detail})"
        )
    config = OpenAIProviderConfig(
        api_key=values["OPENAI_API_KEY"].strip(),
        model_id=values["NESTLINE_OPENAI_MODEL"].strip(),
        authorization_reference=values[
            "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE"
        ].strip(),
        max_request_cost_usd=float(
            values["NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD"]
        ),
        input_usd_per_million_tokens=float(
            values["NESTLINE_OPENAI_INPUT_USD_PER_1M"]
        ),
        output_usd_per_million_tokens=float(
            values["NESTLINE_OPENAI_OUTPUT_USD_PER_1M"]
        ),
        endpoint=values.get(
            "NESTLINE_OPENAI_RESPONSES_ENDPOINT", OPENAI_RESPONSES_ENDPOINT
        ).strip(),
    )
    return OpenAIResponsesProvider(config, transport=transport)


def _default_transport(
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
            f"OpenAI Responses API returned HTTP {exc.code}{detail}"
        ) from None
    except (URLError, TimeoutError, OSError):
        raise ProviderFailure("OpenAI Responses API is unavailable") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ProviderFailure("OpenAI response exceeded the bounded response size")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, JSONDecodeError):
        raise ProviderFailure("OpenAI response was not valid JSON") from None
    if not isinstance(parsed, dict):
        raise ProviderFailure("OpenAI response had an invalid top-level shape")
    return parsed


def _output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    parts: list[str] = []
    output = response.get("output")
    if not isinstance(output, list):
        return ""
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "refusal":
                raise ProviderFailure("OpenAI declined the bounded summary request")
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                parts.append(part["text"])
    return "".join(parts)


class OpenAIResponsesProvider:
    """Responses API adapter that can modify only the deterministic summary."""

    provider_id = PROVIDER_ID
    provider_label = "OpenAI"
    responses_endpoint = OPENAI_RESPONSES_ENDPOINT
    reasoning_effort: str | None = None
    fixture_only = False

    def __init__(
        self,
        config: OpenAIProviderConfig,
        *,
        transport: OpenAITransport | None = None,
    ) -> None:
        if config.endpoint != self.responses_endpoint:
            raise ValueError(
                f"only the fixed official {self.provider_label} Responses endpoint is permitted"
            )
        if config.data_mode != DATA_MODE:
            raise ValueError("live model use is restricted to fictional_only data")
        if not _present(config.api_key) or not _present(config.model_id):
            raise ValueError("an API key and explicit model ID are required")
        if not _present(config.authorization_reference):
            raise ValueError("an explicit paid-evaluation authorization reference is required")
        if min(
            config.max_request_cost_usd,
            config.input_usd_per_million_tokens,
            config.output_usd_per_million_tokens,
        ) <= 0:
            raise ValueError("positive price inputs and request-cost ceiling are required")
        self.config = config
        self.model_id = config.model_id
        self._transport = transport or _default_transport
        self._spent_usd = 0.0

    def _charged_cost(
        self,
        usage: dict[str, Any],
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Return request cost; OpenAI currently requires a token-price estimate."""

        del usage
        return (
            input_tokens * self.config.input_usd_per_million_tokens
            + output_tokens * self.config.output_usd_per_million_tokens
        ) / 1_000_000

    @property
    def spent_usd(self) -> float:
        return self._spent_usd

    def complete(
        self,
        *,
        agent: AgentName,
        instructions: list[str],
        draft: dict[str, Any],
        budget: AgentBudget,
    ) -> ProviderResponse:
        if draft.get("evaluation_only") is not True or draft.get("public_eligible") is not False:
            raise ProviderFailure("live provider accepts only non-public fictional evaluation drafts")
        base_summary = draft.get("summary")
        if not isinstance(base_summary, str) or not base_summary.strip():
            raise ProviderFailure("deterministic draft summary is required")
        if base_summary != ALLOWED_BASE_SUMMARIES.get(agent):
            raise ProviderFailure("live provider rejected a non-canonical or potentially personal summary")

        max_output_tokens = min(128, max(32, budget.max_tokens // 4))
        narrow_input = json.dumps(
            {"agent": agent.value, "base_summary": base_summary},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        # Two characters per token is deliberately conservative for this tiny,
        # English-only payload. Actual API usage remains the enforced authority.
        conservative_input_tokens = math.ceil(len(narrow_input) / 2)
        if conservative_input_tokens + max_output_tokens > budget.max_tokens:
            raise ProviderFailure("bounded summary request would exceed the worker token budget")
        projected_cost = (
            conservative_input_tokens * self.config.input_usd_per_million_tokens
            + max_output_tokens * self.config.output_usd_per_million_tokens
        ) / 1_000_000
        if self._spent_usd + projected_cost > self.config.max_request_cost_usd:
            raise ProviderFailure("live request cost ceiling would be exceeded")

        system_instructions = "\n".join([
            "Rewrite only the supplied deterministic base_summary in calm, concise, plain English.",
            "Do not add facts, health claims, advice, diagnosis, reassurance, evidence, actions, or promises.",
            "Do not remove uncertainty or imply medical safety, monitoring, professional review, or clearance.",
            *instructions,
        ])
        payload = {
            "model": self.model_id,
            "instructions": system_instructions,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": narrow_input}]}],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "nestline_stage7_summary_v1",
                    "description": "One bounded summary; all other Maya AI fields remain deterministic.",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"summary": {"type": "string"}},
                        "required": ["summary"],
                        "additionalProperties": False,
                    },
                }
            },
            "max_output_tokens": max_output_tokens,
            "store": False,
        }
        if self.reasoning_effort is not None:
            payload["reasoning"] = {"effort": self.reasoning_effort}
        started = perf_counter()
        response = self._transport(
            self.config.endpoint,
            {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            payload,
            max(0.1, budget.timeout_ms / 1000),
        )
        latency_ms = (perf_counter() - started) * 1000
        usage = response.get("usage")
        if not isinstance(usage, dict):
            raise ProviderFailure("OpenAI response omitted token usage")
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            raise ProviderFailure("OpenAI token usage was invalid")
        if input_tokens < 0 or output_tokens < 0:
            raise ProviderFailure("OpenAI token usage was invalid")
        cost = self._charged_cost(
            usage,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self._spent_usd += cost

        def paid_failure(message: str) -> ProviderFailure:
            return ProviderFailure(
                message,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost,
            )

        if latency_ms > budget.timeout_ms:
            raise paid_failure("provider response exceeded the configured timeout")
        if input_tokens + output_tokens > budget.max_tokens:
            raise paid_failure(f"{self.provider_label} response exceeded the worker token budget")
        if self._spent_usd > self.config.max_request_cost_usd:
            raise paid_failure(f"{self.provider_label} response exceeded the request cost ceiling")
        if response.get("status") not in {None, "completed"}:
            raise paid_failure(f"{self.provider_label} response did not complete")
        try:
            text = _output_text(response)
        except ProviderFailure as exc:
            raise paid_failure(str(exc)) from None
        try:
            summary_payload = _SummaryOutput.model_validate_json(text)
        except ValidationError:
            raise paid_failure(f"{self.provider_label} structured summary failed schema validation") from None

        merged = dict(draft)
        merged["summary"] = summary_payload.summary.strip()
        return ProviderResponse(
            payload=merged,
            provider=self.provider_id,
            model=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
        )
