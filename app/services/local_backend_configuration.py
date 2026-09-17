"""Explicit local setup configuration; importing this does not enable live calls.

The application is not switched to this profile automatically. Runtime wiring is
a separate integration step, after retrieval has been verified.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

GENERATION_ALIASES = {
    "NESTLINE_GENERATION_PROVIDER": "MAYA_GENERATION_PROVIDER",
    "NESTLINE_GENERATION_MODEL": "MAYA_GENERATION_MODEL",
}


def canonical_provider_settings(values: Mapping[str, str | None]) -> dict[str, str]:
    result = {}
    for canonical, legacy in GENERATION_ALIASES.items():
        first, second = (values.get(canonical) or "").strip(), (values.get(legacy) or "").strip()
        if first and second and first != second:
            raise ValueError(f"Conflicting {canonical} and {legacy}; choose one configuration")
        if first or second:
            result[canonical] = first or second
    provider = result.get("NESTLINE_GENERATION_PROVIDER")
    model = result.get("NESTLINE_GENERATION_MODEL")
    if provider not in ("openai", "xai") or not model:
        raise ValueError("Select the generation provider and exact model; no fixture fallback")
    # Carry only provider credentials. Never inherit hosted DB/operator secrets.
    for name in ("OPENAI_API_KEY", "XAI_API_KEY"):
        if values.get(name):
            result[name] = str(values[name]).strip()
    result["NESTLINE_EMBEDDING_API_KEY"] = result.get("OPENAI_API_KEY", "")
    return result


def local_profile(public_key: str) -> dict[str, str]:
    if not public_key or "\n" in public_key or "\r" in public_key:
        raise ValueError("Local publishable key is missing or invalid")
    return {
        "NESTLINE_SUPABASE_URL": "http://127.0.0.1:54321",
        "NESTLINE_SUPABASE_PUBLISHABLE_KEY": public_key,
        "NESTLINE_ENABLE_LIVE_PROVIDER": "false",
        "NESTLINE_LIVE_PROVIDER_DATA_MODE": "fictional_only",
        "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE": "Aswath-Maya-handoff-20260916",
        "NESTLINE_GENERATION_MAX_COST_USD": "0.01",
        "NESTLINE_OPENAI_MODEL": "gpt-5.4-mini",
        "NESTLINE_XAI_MODEL": "grok-4.6",
        "NESTLINE_OPENAI_INPUT_USD_PER_1M": "0.75",
        "NESTLINE_OPENAI_OUTPUT_USD_PER_1M": "4.50",
        "NESTLINE_XAI_INPUT_USD_PER_1M": "2.00",
        "NESTLINE_XAI_OUTPUT_USD_PER_1M": "6.00",
        "NESTLINE_EMBEDDING_PROVIDER": "openai_compatible",
        "NESTLINE_EMBEDDING_MODEL": "text-embedding-3-small",
        "NESTLINE_EMBEDDING_URL": "https://api.openai.com/v1/embeddings",
    }


def load_local_backend_values(root: Path) -> dict[str, str]:
    from dotenv import dotenv_values
    selected = canonical_provider_settings(dotenv_values(root / ".env", interpolate=False))
    profile = dotenv_values(root / ".env.maya-local", interpolate=False)
    expected = local_profile(profile.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY") or "")
    if dict(profile) != expected:
        raise ValueError("Local setup profile differs from its verified settings; review before loading")
    return {**selected, **expected}
