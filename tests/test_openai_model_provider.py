"""Deterministic tests for the opt-in OpenAI Stage 7 provider boundary."""

from __future__ import annotations

import json
import unittest

from app.schemas.orchestration import AgentBudget, AgentName
from app.services.model_provider import ProviderFailure
from app.services.openai_model_provider import (
    OPENAI_RESPONSES_ENDPOINT,
    OpenAIProviderConfig,
    OpenAIResponsesProvider,
    inspect_live_provider_configuration,
    load_openai_provider_from_env,
)
from app.services.product_experience import run_compass


def configuration(**updates: str) -> dict[str, str]:
    values = {
        "NESTLINE_ENABLE_LIVE_PROVIDER": "true",
        "NESTLINE_LIVE_PROVIDER_DATA_MODE": "fictional_only",
        "NESTLINE_GENERATION_PROVIDER": "openai",
        "NESTLINE_GENERATION_MODEL": "test-model-explicit",
        "NESTLINE_GENERATION_MAX_COST_USD": "0.10",
        "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE": "user-approved-test-reference",
        "NESTLINE_OPENAI_INPUT_USD_PER_1M": "2.00",
        "NESTLINE_OPENAI_OUTPUT_USD_PER_1M": "12.00",
        "NESTLINE_OPENAI_RESPONSES_ENDPOINT": OPENAI_RESPONSES_ENDPOINT,
        "OPENAI_API_KEY": "sk-test-only-placeholder-000000",
    }
    values.update(updates)
    return values


def budget(*, max_tokens: int = 1200, timeout_ms: int = 8000) -> AgentBudget:
    return AgentBudget(
        max_model_calls=1,
        max_steps=6,
        max_tokens=max_tokens,
        max_retries=1,
        max_repairs=1,
        timeout_ms=timeout_ms,
    )


def draft() -> dict:
    return {
        "summary": "Here is a practical option after applying your confirmed food constraints.",
        "evaluation_only": True,
        "public_eligible": False,
        "facts_used": ["fact-1"],
        "citations": [{"evidence_id": "evidence-1"}],
        "applied_constraints": ["allergy: peanut"],
        "proposed_actions": [{"action_id": "a-1"}],
    }


def response(summary: str = "Here is a calm, concise summary.", *, input_tokens: int = 100,
             output_tokens: int = 20) -> dict:
    return {
        "status": "completed",
        "output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": json.dumps({"summary": summary})}],
        }],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


class LiveProviderConfigurationTests(unittest.TestCase):
    def test_disabled_is_explicit_and_needs_no_secret(self):
        status = inspect_live_provider_configuration({})
        self.assertFalse(status.enabled)
        self.assertFalse(status.ready)
        self.assertEqual(status.missing_fields, ())

    def test_enabled_configuration_requires_every_governance_field(self):
        status = inspect_live_provider_configuration({"NESTLINE_ENABLE_LIVE_PROVIDER": "true"})
        self.assertTrue(status.enabled)
        self.assertFalse(status.ready)
        self.assertIn("OPENAI_API_KEY", status.missing_fields)
        self.assertIn("NESTLINE_GENERATION_MODEL", status.missing_fields)
        self.assertIn("NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE", status.missing_fields)

    def test_complete_configuration_is_ready_without_exposing_key(self):
        status = inspect_live_provider_configuration(configuration())
        self.assertTrue(status.ready)
        self.assertEqual(status.provider_id, "openai")
        self.assertEqual(status.model_id, "test-model-explicit")
        self.assertNotIn("api_key", status.__dict__)
        self.assertNotIn("sk-test", repr(status))

    def test_non_official_endpoint_fails_closed(self):
        values = configuration(NESTLINE_OPENAI_RESPONSES_ENDPOINT="https://example.invalid/collect")
        status = inspect_live_provider_configuration(values)
        self.assertFalse(status.ready)
        self.assertIn("fixed official", status.error)
        with self.assertRaises(ProviderFailure):
            load_openai_provider_from_env(values)


class OpenAIResponsesProviderTests(unittest.TestCase):
    def provider(self, transport, **updates) -> OpenAIResponsesProvider:
        values = configuration(**{key: str(value) for key, value in updates.items()})
        return load_openai_provider_from_env(values, transport=transport)

    def test_model_can_change_only_summary_and_request_is_minimized(self):
        observed = {}

        def transport(endpoint, headers, payload, timeout):
            observed.update(endpoint=endpoint, headers=headers, payload=payload, timeout=timeout)
            return response("A calmer bounded summary.")

        provider = self.provider(transport)
        original = draft()
        result = provider.complete(
            agent=AgentName.NUTRITION,
            instructions=["Keep uncertainty visible."],
            draft=original,
            budget=budget(),
        )
        self.assertEqual(result.payload["summary"], "A calmer bounded summary.")
        for key in ("facts_used", "citations", "applied_constraints", "proposed_actions"):
            self.assertEqual(result.payload[key], original[key])
        self.assertEqual(observed["endpoint"], OPENAI_RESPONSES_ENDPOINT)
        self.assertFalse(observed["payload"]["store"])
        self.assertTrue(observed["payload"]["text"]["format"]["strict"])
        sent = observed["payload"]["input"][0]["content"][0]["text"]
        self.assertNotIn("evidence-1", sent)
        self.assertNotIn("peanut", sent)
        self.assertNotIn("fact-1", sent)
        self.assertNotIn("sk-test", json.dumps(observed["payload"]))
        self.assertAlmostEqual(result.estimated_cost_usd, 0.00044)

    def test_non_canonical_summary_is_rejected_before_transport(self):
        calls = []

        def transport(*args):
            calls.append(args)
            return response()

        provider = self.provider(transport)
        candidate = {**draft(), "summary": "A user-controlled or personal value"}
        with self.assertRaisesRegex(ProviderFailure, "non-canonical"):
            provider.complete(
                agent=AgentName.NUTRITION, instructions=[], draft=candidate, budget=budget(),
            )
        self.assertEqual(calls, [])

    def test_personal_or_public_draft_is_rejected_before_transport(self):
        calls = []

        def transport(*args):
            calls.append(args)
            return response()

        provider = self.provider(transport)
        for changes in (
            {"evaluation_only": False},
            {"public_eligible": True},
        ):
            candidate = {**draft(), **changes}
            with self.assertRaisesRegex(ProviderFailure, "fictional"):
                provider.complete(
                    agent=AgentName.NUTRITION,
                    instructions=[],
                    draft=candidate,
                    budget=budget(),
                )
        self.assertEqual(calls, [])

    def test_malformed_structured_output_and_refusal_fail_closed(self):
        malformed = self.provider(lambda *args: {
            "status": "completed",
            "output_text": json.dumps({"summary": "okay", "extra": "not permitted"}),
            "usage": {"input_tokens": 10, "output_tokens": 10},
        })
        with self.assertRaisesRegex(ProviderFailure, "schema"):
            malformed.complete(
                agent=AgentName.NUTRITION, instructions=[], draft=draft(), budget=budget(),
            )
        refused = self.provider(lambda *args: {
            "status": "completed",
            "output": [{"type": "message", "content": [{"type": "refusal"}]}],
            "usage": {"input_tokens": 10, "output_tokens": 0},
        })
        with self.assertRaisesRegex(ProviderFailure, "declined"):
            refused.complete(
                agent=AgentName.NUTRITION, instructions=[], draft=draft(), budget=budget(),
            )

    def test_token_and_cost_ceilings_fail_closed(self):
        over_tokens = self.provider(lambda *args: response(input_tokens=1100, output_tokens=200))
        with self.assertRaisesRegex(ProviderFailure, "token budget"):
            over_tokens.complete(
                agent=AgentName.NUTRITION, instructions=[], draft=draft(), budget=budget(),
            )
        preflight = self.provider(
            lambda *args: response(),
            NESTLINE_GENERATION_MAX_COST_USD="0.000001",
        )
        with self.assertRaisesRegex(ProviderFailure, "cost ceiling"):
            preflight.complete(
                agent=AgentName.NUTRITION, instructions=[], draft=draft(), budget=budget(),
            )

    def test_urgent_request_never_calls_live_transport(self):
        calls = []

        def transport(*args):
            calls.append(args)
            return response()

        execution = run_compass(
            "I cannot breathe. Show my weekly plan.",
            horizon="week",
            provider=self.provider(transport),
        )
        self.assertEqual(execution.display.route, "urgent")
        self.assertEqual(execution.display.ordinary_generation_calls, 0)
        self.assertEqual(calls, [])

    def test_injected_live_provider_still_passes_stage8_before_display(self):
        calls = []

        def transport(*args):
            calls.append(args)
            return response("Here is a practical option using the validated fictional inputs.")

        execution = run_compass("Show meal options", provider=self.provider(transport))
        self.assertEqual(execution.display.route, "validated")
        self.assertTrue(execution.stage8.validation_report.display_allowed)
        self.assertEqual(execution.stage7.worker_results[0].trace.provider, "openai")
        self.assertIn("live-model", execution.display.title)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
