"""One-time, budget-reserved provider smoke tests. Not a RAG benchmark.

Only fixed non-medical test text leaves the machine. No tools, retries, personal
context or hosted database calls. Credentials are read from .env, never printed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "reports/local/provider-smoke"
MODELS = {"openai": "gpt-5.4-mini", "xai": "grok-4.6", "embedding": "text-embedding-3-small"}
ENDPOINTS = {"openai": "https://api.openai.com/v1/responses", "xai": "https://api.x.ai/v1/responses",
             "embedding": "https://api.openai.com/v1/embeddings"}
PRICES = {"openai": (0.75, 4.50), "xai": (2.00, 6.00), "embedding": (0.02, 0)}
FIXTURES = ["The fictional garden contains a red rose.", "The fictional garage contains a blue bicycle.",
            "A flower growing in a garden."]
RESERVATION_USD = 0.01


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_body(kind: str) -> dict:
    if kind == "embedding":
        return {"model": MODELS[kind], "input": FIXTURES, "encoding_format": "float", "dimensions": 1536}
    return {"model": MODELS[kind], "store": False, "max_output_tokens": 256,
            "reasoning": {"effort": "low" if kind == "xai" else "none"},
            "input": [{"role": "user", "content": "Connection check using fictional data. Reply with exactly MAYA_READY and nothing else."}]}


def summarize(kind: str, payload: dict) -> dict:
    usage = payload.get("usage") or {}
    input_tokens = usage.get("prompt_tokens") if kind == "embedding" else usage.get("input_tokens")
    output_tokens = 0 if kind == "embedding" else usage.get("output_tokens")
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("missing_or_invalid_usage")
    rate_in, rate_out = PRICES[kind]
    cost = (input_tokens * rate_in + output_tokens * rate_out) / 1_000_000
    summary = {"input_tokens": input_tokens, "output_tokens": output_tokens,
               "estimated_cost_usd": cost, "price_checked_date": "2026-09-16"}
    # xAI exposes exact cost in 1e-10 USD ticks; retain it when supplied.
    ticks = usage.get("cost_in_usd_ticks")
    if type(ticks) is int and ticks >= 0:
        summary["provider_reported_cost_usd"] = ticks / 10_000_000_000
        cost = max(cost, summary["provider_reported_cost_usd"])
    summary["accounted_cost_usd"] = cost
    if kind == "embedding":
        rows = sorted(payload.get("data", []), key=lambda row: row.get("index", -1))
        if [row.get("index") for row in rows] != list(range(len(FIXTURES))):
            raise ValueError("embedding_indices_invalid")
        vectors = [row.get("embedding") for row in rows]
        if any(not isinstance(v, list) or len(v) != 1536 or
               any(type(n) not in (float, int) or not math.isfinite(n) for n in v) or
               not any(n != 0 for n in v) for v in vectors):
            raise ValueError("embedding_vectors_invalid")
        summary.update({"vector_count": len(vectors), "dimensions": 1536, "vectors_finite_nonzero": True,
                        "success": payload.get("model") == MODELS[kind]})
    else:
        text = "".join(c.get("text", "") for item in payload.get("output", []) if item.get("type") == "message"
                       for c in item.get("content", []) if c.get("type") == "output_text")
        summary.update({"completed": payload.get("status") == "completed", "expected_marker_returned": text.strip() == "MAYA_READY"})
        summary["success"] = summary["completed"] and summary["expected_marker_returned"]
    if cost > RESERVATION_USD:
        summary["success"] = False
        summary["error"] = "reservation_exceeded_stop_all_paid_work"
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-authorized-smoke", action="store_true")
    parser.add_argument("--retry-replaced-openai-key", action="store_true",
                        help="One explicit retry after the operator replaces a key rejected with HTTP 401")
    parser.add_argument("--replacement-attempt", type=int, choices=(2,),
                        help="Second explicitly authorised key replacement; preserves both earlier ledgers")
    parser.add_argument("--openai-only", action="store_true", help="Check OpenAI generation and embeddings only")
    args = parser.parse_args()
    if not args.execute_authorized_smoke:
        print(json.dumps({"calls_made": 0, "maximum_reserved_usd": 0.03,
                          "models": MODELS, "purpose": "provider access only; not live RAG"}, indent=2))
        return 0
    from dotenv import dotenv_values
    values = dotenv_values(ROOT / ".env", interpolate=False)
    if not (values.get("OPENAI_API_KEY") or "").strip():
        print("Missing OpenAI key; no requests sent.")
        return 1
    LOCAL.mkdir(parents=True, exist_ok=True)
    ledger_path = LOCAL / "ledger.json"
    previous_ledger = None
    if args.retry_replaced_openai_key or args.replacement_attempt:
        if args.retry_replaced_openai_key and args.replacement_attempt:
            parser.error("Select one replacement attempt")
        if args.replacement_attempt:
            ledger_path = LOCAL / "ledger-after-key-replacement.json"
        previous_ledger = ledger_path.name
        previous = json.loads(ledger_path.read_text(encoding="utf-8"))
        calls = previous.get("calls", [])
        if len(calls) != 1 or calls[0].get("kind") != "openai" or calls[0].get("http_status") != 401:
            print("Retry requires the recorded OpenAI 401 and explicit replacement-key instruction.")
            return 1
        ledger_path = LOCAL / ("ledger-after-key-replacement-2.json" if args.replacement_attempt else "ledger-after-key-replacement.json")
    # An exclusive file is the run lock AND durable reservation. Never retry an
    # uncertain request automatically; manually reconcile provider usage first.
    ledger = {"authorization": "MAYA-FINAL-OPERATIONAL-HANDOFF-FOR-KAJAL.md",
              "project_caps_usd": {"openai": 30, "xai": 5},
              "reported_prior_spend_usd": {"openai": 0, "xai": 0.06},
              "prior_spend_is_account_report_not_live_balance": True,
              "reserved_this_run_usd": {"openai": 0.02, "xai": 0 if args.openai_only else 0.01},
              "not_an_account_wide_budget_enforcer": True, "calls": []}
    if previous_ledger:
        ledger["previous_attempt_ledger"] = previous_ledger
        ledger["previous_attempt_reservation_usd"] = 0.01
    try:
        with ledger_path.open("x", encoding="utf-8") as file:
            json.dump(ledger, file, indent=2)
    except FileExistsError:
        print("Smoke ledger already exists; no requests repeated. Review the previous results first.")
        return 1
    opener = build_opener(NoRedirect())
    for kind in (("openai", "embedding") if args.openai_only else ("openai", "xai", "embedding")):
        key = (values.get("XAI_API_KEY" if kind == "xai" else "OPENAI_API_KEY") or "").strip()
        if not key:
            record = {"kind": kind, "model": MODELS[kind], "status": "skipped_missing_key", "success": False, "request_sent": False}
            ledger["calls"].append(record)
            ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
            print(json.dumps(record), flush=True)
            continue
        record = {"kind": kind, "model": MODELS[kind], "endpoint": ENDPOINTS[kind],
                  "started_utc": datetime.now(timezone.utc).isoformat(), "status": "reserved", "success": False}
        ledger["calls"].append(record)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        request = Request(ENDPOINTS[kind], data=json.dumps(request_body(kind)).encode(), method="POST",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        started = time.perf_counter()
        payload = None
        try:
            with opener.open(request, timeout=45) as response:
                record["http_status"] = response.status
                record["request_id"] = response.headers.get("x-request-id")
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("response_too_large")
            payload = json.loads(raw)
            record.update(summarize(kind, payload))
            record["status"] = "passed" if record["success"] else "failed"
        except HTTPError as exc:
            record.update({"status": "http_error", "http_status": exc.code,
                           "request_id": exc.headers.get("x-request-id")})
            # Never print the provider's raw error message or the request headers.
            try:
                error = json.loads(exc.read(16000)).get("error", {})
                if isinstance(error, dict) and error.get("code") in {"insufficient_quota", "rate_limit_exceeded", "invalid_api_key", "model_not_found"}:
                    record["error_code"] = error["code"]
            except (ValueError, OSError):
                pass
        except (URLError, TimeoutError, OSError):
            record["status"] = "transport_error_cost_unknown"
        except (ValueError, TypeError, KeyError):
            record["status"] = "invalid_response_cost_reserved"
        record["latency_seconds"] = round(time.perf_counter() - started, 3)
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
        if kind == "embedding" and record["success"]:
            vectors = [row["embedding"] for row in sorted(payload["data"], key=lambda row: row["index"])]
            (LOCAL / "synthetic-vectors.json").write_text(json.dumps({"model": MODELS[kind], "dimensions": 1536,
                                                                       "texts": FIXTURES, "vectors": vectors}), encoding="utf-8")
        print(json.dumps(record, indent=2), flush=True)
        if not record["success"]:
            print("Stopped after failure. No retries or further paid requests were made.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
