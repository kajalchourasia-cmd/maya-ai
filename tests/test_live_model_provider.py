"""Tests for explicit runtime provider selection and fail-closed dispatch."""

from __future__ import annotations

import unittest

from app.services.live_model_provider import (
    inspect_selected_provider_configuration,
    load_selected_provider_from_env,
)
from app.services.model_provider import ProviderFailure


def common(**updates: str) -> dict[str, str]:
    values = {
        "NESTLINE_ENABLE_LIVE_PROVIDER": "true",
        "NESTLINE_LIVE_PROVIDER_DATA_MODE": "fictional_only",
        "NESTLINE_GENERATION_MAX_COST_USD": "0.02",
        "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE": "approved-test-reference",
        "NESTLINE_OPENAI_INPUT_USD_PER_1M": "0.75",
        "NESTLINE_OPENAI_OUTPUT_USD_PER_1M": "4.50",
        "NESTLINE_OPENAI_RESPONSES_ENDPOINT": "https://api.openai.com/v1/responses",
        "NESTLINE_XAI_INPUT_USD_PER_1M": "2.00",
        "NESTLINE_XAI_OUTPUT_USD_PER_1M": "6.00",
        "NESTLINE_XAI_RESPONSES_ENDPOINT": "https://api.x.ai/v1/responses",
        "OPENAI_API_KEY": "sk-test-not-real",
        "XAI_API_KEY": "xai-test-not-real",
    }
    values.update(updates)
    return values


class LiveModelProviderDispatchTests(unittest.TestCase):
    def test_disabled_runtime_selects_nothing(self):
        status = inspect_selected_provider_configuration({})
        self.assertFalse(status.enabled)
        self.assertFalse(status.ready)
        with self.assertRaisesRegex(ProviderFailure, "disabled"):
            load_selected_provider_from_env({})

    def test_unknown_provider_fails_closed_without_fallback(self):
        values = common(
            NESTLINE_GENERATION_PROVIDER="invented",
            NESTLINE_GENERATION_MODEL="invented-model",
        )
        status = inspect_selected_provider_configuration(values)
        self.assertFalse(status.ready)
        self.assertIn("unsupported", status.error)
        with self.assertRaisesRegex(ProviderFailure, "unsupported"):
            load_selected_provider_from_env(values)

    def test_openai_selection_is_explicit(self):
        values = common(
            NESTLINE_GENERATION_PROVIDER="openai",
            NESTLINE_GENERATION_MODEL="gpt-5.4-mini",
        )
        status = inspect_selected_provider_configuration(values)
        self.assertTrue(status.ready)
        provider = load_selected_provider_from_env(values)
        self.assertEqual(provider.provider_id, "openai")
        self.assertEqual(provider.model_id, "gpt-5.4-mini")

    def test_xai_selection_is_explicit_and_model_locked(self):
        values = common(
            NESTLINE_GENERATION_PROVIDER="xai",
            NESTLINE_GENERATION_MODEL="grok-4.6",
        )
        status = inspect_selected_provider_configuration(values)
        self.assertTrue(status.ready)
        provider = load_selected_provider_from_env(values)
        self.assertEqual(provider.provider_id, "xai")
        self.assertEqual(provider.model_id, "grok-4.6")

        wrong = common(
            NESTLINE_GENERATION_PROVIDER="xai",
            NESTLINE_GENERATION_MODEL="made-up",
        )
        self.assertFalse(inspect_selected_provider_configuration(wrong).ready)


if __name__ == "__main__":
    unittest.main()
