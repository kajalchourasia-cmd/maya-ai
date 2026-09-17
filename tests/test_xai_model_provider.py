"""Deterministic tests for the opt-in xAI Stage 7 provider boundary."""

from __future__ import annotations

import json
import unittest

from app.schemas.orchestration import AgentBudget, AgentName
from app.services.model_provider import ProviderFailure
from app.services.openai_model_provider import ALLOWED_BASE_SUMMARIES
from app.services.product_experience import run_compass
from app.services.xai_model_provider import (
    MODEL_ID,
    XAI_RESPONSES_ENDPOINT,
    inspect_xai_benchmark_configuration,
    load_xai_benchmark_provider_from_env,
)


def configuration(**updates: str) -> dict[str, str]:
    values = {
        "NESTLINE_XAI_MODEL": MODEL_ID,
        "NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD": "0.02",
        "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE": "user-approved-test-reference",
        "NESTLINE_XAI_INPUT_USD_PER_1M": "2.00",
        "NESTLINE_XAI_OUTPUT_USD_PER_1M": "6.00",
        "NESTLINE_XAI_RESPONSES_ENDPOINT": XAI_RESPONSES_ENDPOINT,
        "XAI_API_KEY": "xai-test-only-placeholder-000000",
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
        "summary": ALLOWED_BASE_SUMMARIES[AgentName.NUTRITION],
        "evaluation_only": True,
        "public_eligible": False,
        "facts_used": ["fact-1"],
        "citations": [{"evidence_id": "evidence-1"}],
        "applied_constraints": ["allergy: peanut"],
        "proposed_actions": [{"action_id": "a-1"}],
    }


def response(
    summary: str = "Here is a calm, concise summary.",
    *,
    input_tokens: int = 100,
    output_tokens: int = 20,
    cost_ticks: int = 1_585_000,
) -> dict:
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps({"summary": summary}),
                    }
                ],
            }
        ],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_in_usd_ticks": cost_ticks,
        },
    }


class XAIConfigurationTests(unittest.TestCase):
    def test_complete_configuration_is_ready_without_exposing_key(self):
        status = inspect_xai_benchmark_configuration(configuration())
        self.assertTrue(status.ready)
        self.assertEqual(status.provider_id, "xai")
        self.assertEqual(status.model_id, MODEL_ID)
        self.assertNotIn("api_key", status.__dict__)
        self.assertNotIn("xai-test", repr(status))

    def test_exact_model_and_endpoint_are_required(self):
        wrong_model = inspect_xai_benchmark_configuration(
            configuration(NESTLINE_XAI_MODEL="made-up-model")
        )
        self.assertFalse(wrong_model.ready)
        self.assertIn(f"NESTLINE_XAI_MODEL={MODEL_ID}", wrong_model.missing_fields)

        values = configuration(
            NESTLINE_XAI_RESPONSES_ENDPOINT="https://example.invalid/collect"
        )
        status = inspect_xai_benchmark_configuration(values)
        self.assertFalse(status.ready)
        self.assertIn("fixed official", status.error)
        with self.assertRaises(ProviderFailure):
            load_xai_benchmark_provider_from_env(values)


class XAIResponsesProviderTests(unittest.TestCase):
    def provider(self, transport, **updates):
        values = configuration(**{key: str(value) for key, value in updates.items()})
        return load_xai_benchmark_provider_from_env(values, transport=transport)

    def test_model_changes_only_summary_and_uses_bounded_xai_request(self):
        observed = {}

        def transport(endpoint, headers, payload, timeout):
            observed.update(
                endpoint=endpoint,
                headers=headers,
                payload=payload,
                timeout=timeout,
            )
            return response("A calmer bounded Grok summary.")

        provider = self.provider(transport)
        original = draft()
        result = provider.complete(
            agent=AgentName.NUTRITION,
            instructions=["Keep uncertainty visible."],
            draft=original,
            budget=budget(),
        )
        self.assertEqual(result.payload["summary"], "A calmer bounded Grok summary.")
        for key in (
            "facts_used",
            "citations",
            "applied_constraints",
            "proposed_actions",
        ):
            self.assertEqual(result.payload[key], original[key])
        self.assertEqual(observed["endpoint"], XAI_RESPONSES_ENDPOINT)
        self.assertEqual(observed["payload"]["reasoning"], {"effort": "low"})
        self.assertFalse(observed["payload"]["store"])
        self.assertTrue(observed["payload"]["text"]["format"]["strict"])
        self.assertNotIn("tools", observed["payload"])
        sent = observed["payload"]["input"][0]["content"][0]["text"]
        self.assertNotIn("evidence-1", sent)
        self.assertNotIn("peanut", sent)
        self.assertNotIn("fact-1", sent)
        self.assertNotIn("xai-test", json.dumps(observed["payload"]))
        self.assertAlmostEqual(result.estimated_cost_usd, 0.0001585)

    def test_billed_cost_is_required_and_enforced(self):
        missing = self.provider(
            lambda *args: {
                "status": "completed",
                "output_text": json.dumps({"summary": "Bounded summary."}),
                "usage": {"input_tokens": 10, "output_tokens": 10},
            }
        )
        with self.assertRaisesRegex(ProviderFailure, "billed-cost"):
            missing.complete(
                agent=AgentName.NUTRITION,
                instructions=[],
                draft=draft(),
                budget=budget(),
            )

        over = self.provider(
            lambda *args: response(cost_ticks=300_000_000),
            NESTLINE_BENCHMARK_MAX_REQUEST_COST_USD="0.02",
        )
        with self.assertRaisesRegex(ProviderFailure, "cost ceiling"):
            over.complete(
                agent=AgentName.NUTRITION,
                instructions=[],
                draft=draft(),
                budget=budget(),
            )

    def test_urgent_request_never_calls_xai(self):
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


if __name__ == "__main__":
    unittest.main()
