"""Readiness diagnostics may not leak secrets or write remote state."""
import base64
import json
from urllib.error import HTTPError

import pytest

from scripts import check_maya_runtime_access as audit


def settings(key="sb_publishable_test", url="https://test.supabase.co"):
    return {"NESTLINE_SUPABASE_URL": url,
            "NESTLINE_SUPABASE_PUBLISHABLE_KEY": key,
            "SUPABASE_ACCESS_TOKEN": "management-secret-do-not-use",
            "SUPABASE_DB_PASSWORD": "database-secret-do-not-use"}


class Response:
    status = 200
    headers = {"Content-Range": "*/0"}

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, limit):
        return json.dumps(self.value).encode()


def test_audit_uses_only_public_key_and_get_requests(monkeypatch):
    monkeypatch.setattr(audit, "dotenv_values", lambda path: settings())
    requests = []

    def respond(request, **kwargs):
        requests.append(request)
        assert request.get_method() == "GET"
        assert request.data is None
        assert "management-secret" not in str(request.headers)
        assert "database-secret" not in str(request.headers)
        return Response({"external": {"anonymous_users": False}}
                        if request.full_url.endswith("settings") else [])

    monkeypatch.setattr(audit, "urlopen", respond)
    result = audit.inspect_runtime()
    assert len(requests) == 4
    assert result["checks"]["auth_settings"]["anonymous_sign_ins_enabled"] is False
    assert "sb_publishable_test" not in json.dumps(result)
    assert "do not prove" in result["note"]


@pytest.mark.parametrize("url,key", [
    ("http://test.supabase.co", "sb_publishable_test"),
    ("https://other.example", "sb_publishable_test"),
    ("https://test.supabase.co", "sb_secret_private"),
    ("https://test.supabase.co", "eyJ.bad.signature"),
    ("https://test.supabase.co", "eyJ." + base64.urlsafe_b64encode(
        json.dumps({"role": "service_role"}).encode()).decode().rstrip("=") + ".sig"),
])
def test_unsafe_configuration_never_contacted(monkeypatch, url, key):
    monkeypatch.setattr(audit, "dotenv_values", lambda path: settings(key, url))
    monkeypatch.setattr(audit, "urlopen", lambda *a, **k: pytest.fail("must not contact"))
    assert "configuration" in audit.inspect_runtime()["checks"]


def test_http_error_does_not_print_response_body(monkeypatch):
    monkeypatch.setattr(audit, "dotenv_values", lambda path: settings())

    def denied(request, **kwargs):
        raise HTTPError(request.full_url, 403, "secret error details", {}, None)

    monkeypatch.setattr(audit, "urlopen", denied)
    result = audit.inspect_runtime()
    assert all(check == {"http_status": 403} for check in result["checks"].values())
    assert "secret error" not in json.dumps(result)
