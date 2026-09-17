#!/usr/bin/env python3
"""Verify xAI API/model access without making a generation or embedding call."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
MODELS_ENDPOINT = "https://api.x.ai/v1/models"


def _fetch_model_ids(api_key: str, timeout_seconds: float) -> set[str]:
    request = Request(
        MODELS_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read(2_000_001).decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"xAI models endpoint returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError(
            "xAI models endpoint was unavailable or returned invalid JSON"
        ) from None
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        raise RuntimeError("xAI models response had an invalid shape")
    return {
        item["id"]
        for item in data
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-api-access", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)

    key = os.environ.get("XAI_API_KEY", "").strip()
    selected_model = os.environ.get("NESTLINE_XAI_MODEL", "grok-4.6").strip()
    report = {
        "schema_version": "nestline-xai-access-check-v1",
        "generation_call_made": False,
        "embedding_call_made": False,
        "api_key_present": bool(key),
        "api_access_checked": args.verify_api_access,
        "api_access": None,
        "visible_model_count": None,
        "selected_model": selected_model or None,
        "selected_model_visible": None,
        "secrets_printed": False,
    }
    if not args.verify_api_access:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if not key:
        report["api_access"] = False
        report["error"] = "XAI_API_KEY is missing"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    try:
        model_ids = _fetch_model_ids(key, args.timeout_seconds)
    except RuntimeError as exc:
        report["api_access"] = False
        report["error"] = str(exc)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    report["api_access"] = True
    report["visible_model_count"] = len(model_ids)
    report["selected_model_visible"] = selected_model in model_ids
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if selected_model in model_ids else 1


if __name__ == "__main__":
    sys.exit(main())
