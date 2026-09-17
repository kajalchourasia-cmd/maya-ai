"""Read-only runtime checks. Never print credentials or patient records."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def inspect_runtime() -> dict:
    settings = dotenv_values(ROOT / ".env")
    url = (settings.get("NESTLINE_SUPABASE_URL") or "").rstrip("/")
    key = settings.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY") or ""
    parsed = urlsplit(url)
    result = {"read_only": True, "secret_values_logged": False, "checks": {}}
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".supabase.co") or parsed.username or parsed.password:
        result["checks"]["configuration"] = "Expected a hosted HTTPS Supabase project URL; not contacted."
        return result
    headers = {"apikey": key, "Accept": "application/json"}
    # Only the application's publishable key is used, never management tokens,
    # database passwords or an administrator/service-role key.
    if key.startswith("sb_secret_"):
        result["checks"]["configuration"] = "Secret key supplied in publishable field; not used."
        return result
    if key.startswith("eyJ"):
        import base64
        try:
            payload = key.split(".")[1]
            role = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role")
        except (ValueError, IndexError):
            role = None
        if role != "anon":
            result["checks"]["configuration"] = "Expected an anon/publishable application key; not used."
            return result
        headers["Authorization"] = "Bearer " + key
    targets = {
        "auth_settings": "/auth/v1/settings",
        "published_releases": "/rest/v1/content_releases?select=id,corpus_version,status&status=eq.published&limit=10",
        "visible_guideline_count": "/rest/v1/guideline_chunks?select=chunk_id&limit=1",
        "visible_source_count": "/rest/v1/public_sources?select=source_id&limit=1",
    }
    for name, path in targets.items():
        try:
            request = Request(url + path, headers=headers | {"Prefer": "count=exact"})
            with urlopen(request, timeout=12) as response:
                raw = response.read(200_001)
                if len(raw) > 200_000:
                    result["checks"][name] = {"status": "response_too_large"}
                    continue
                value = json.loads(raw)
                check = {"http_status": response.status}
                if name == "auth_settings":
                    check["anonymous_sign_ins_enabled"] = value.get("external", {}).get("anonymous_users")
                elif name == "published_releases":
                    check["visible_releases"] = value
                else:
                    check["content_range"] = response.headers.get("Content-Range")
                result["checks"][name] = check
        except HTTPError as exc:
            # Codes are sufficient. Error bodies can include internal details.
            result["checks"][name] = {"http_status": exc.code}
        except (URLError, TimeoutError, ValueError):
            result["checks"][name] = {"status": "connection_or_response_error"}
    result["note"] = "Empty or denied reads with a public key do not prove the database is empty. No user records were queried."
    return result


if __name__ == "__main__":
    print(json.dumps(inspect_runtime(), indent=2))
