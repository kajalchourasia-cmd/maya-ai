import json

import pytest

from scripts.check_maya_paid_access import request_body, summarize
from scripts.maya_local_database import safe_output
from app.services.local_backend_configuration import canonical_provider_settings, local_profile


def test_local_config_maps_legacy_names_without_hosted_secrets():
    values = canonical_provider_settings({"MAYA_GENERATION_PROVIDER": "openai", "MAYA_GENERATION_MODEL": "gpt-5.4-mini",
                                          "OPENAI_API_KEY": "test-key", "SUPABASE_DB_PASSWORD": "never-copy",
                                          "SUPABASE_ACCESS_TOKEN": "never-copy", "NESTLINE_SUPABASE_URL": "https://hosted.invalid"})
    assert values["NESTLINE_GENERATION_MODEL"] == "gpt-5.4-mini"
    assert values["NESTLINE_EMBEDDING_API_KEY"] == "test-key"
    assert "SUPABASE_DB_PASSWORD" not in values
    assert "NESTLINE_SUPABASE_URL" not in values
    assert not any(key.startswith("MAYA_") for key in values)


def test_local_config_conflict_is_explicit():
    with pytest.raises(ValueError, match="Conflicting"):
        canonical_provider_settings({"MAYA_GENERATION_PROVIDER": "openai", "NESTLINE_GENERATION_PROVIDER": "xai"})


def test_setup_never_enables_generation_or_includes_admin_credentials():
    profile = local_profile("test-public-key")
    assert profile["NESTLINE_ENABLE_LIVE_PROVIDER"] == "false"
    assert profile["NESTLINE_SUPABASE_URL"] == "http://127.0.0.1:54321"
    assert profile["NESTLINE_EMBEDDING_URL"] == "https://api.openai.com/v1/embeddings"
    assert not any("SERVICE_ROLE" in key or "PASSWORD" in key for key in profile)


def test_smoke_requests_are_fixed_small_and_not_user_health_data():
    for kind in ("openai", "xai"):
        body = request_body(kind)
        assert body["store"] is False
        assert body["max_output_tokens"] == 256
        assert "tools" not in body
        assert "MAYA_READY" in body["input"][0]["content"]
    assert request_body("embedding")["dimensions"] == 1536


def test_generation_needs_complete_marker_and_usage():
    payload = {"usage": {"input_tokens": 25, "output_tokens": 5}, "status": "completed",
               "output": [{"type": "message", "content": [{"type": "output_text", "text": "MAYA_READY"}]}]}
    result = summarize("openai", payload)
    assert result["success"]
    assert result["accounted_cost_usd"] == pytest.approx(0.00004125)
    payload["status"] = "incomplete"
    assert not summarize("openai", payload)["success"]
    payload["usage"] = {}
    with pytest.raises(ValueError):
        summarize("openai", payload)


def embeddings_payload():
    return {"model": "text-embedding-3-small", "usage": {"prompt_tokens": 30},
            "data": [{"index": i, "embedding": [0.1] * 1536} for i in range(3)]}


def test_real_embedding_shape_contract():
    assert summarize("embedding", embeddings_payload())["success"]


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), True, "0.1"])
def test_invalid_embedding_numbers_rejected(invalid):
    payload = embeddings_payload()
    payload["data"][1]["embedding"][0] = invalid
    with pytest.raises(ValueError):
        summarize("embedding", payload)


def test_embedding_duplicate_index_and_wrong_dimension_rejected():
    payload = embeddings_payload()
    payload["data"][1]["index"] = 0
    with pytest.raises(ValueError):
        summarize("embedding", payload)
    payload = embeddings_payload()
    payload["data"][0]["embedding"] = [0.1] * 32
    with pytest.raises(ValueError):
        summarize("embedding", payload)


def test_cli_secrets_are_not_in_printed_logs():
    text = "Ready\nservice_role: sensitive\npostgresql://postgres:secret@localhost/db\nsb_secret_abcdef\neyJabc.def.ghi"
    result = safe_output(text)
    for secret in ("sensitive", "postgres:secret", "abcdef", "eyJabc"):
        assert secret not in result
    assert "Ready" in result
