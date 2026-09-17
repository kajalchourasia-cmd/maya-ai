#!/usr/bin/env python3
"""Run one bounded fictional Stage 7 provider benchmark after authorization."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Callable

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.provider_benchmark import (
    ProviderBenchmarkObservation,
    ProviderBenchmarkReport,
)
from app.services.model_provider import StructuredProvider
from app.services.openai_model_provider import (
    inspect_openai_benchmark_configuration,
    load_openai_benchmark_provider_from_env,
)
from app.services.product_experience import ProductExecution, run_compass
from app.services.provider_benchmark import aggregate_authorized_benchmark
from app.services.xai_model_provider import (
    inspect_xai_benchmark_configuration,
    load_xai_benchmark_provider_from_env,
)


DATASET = ROOT / "evals/stage7_live_provider_development.jsonl"
DEFAULT_OUTPUTS = {
    "openai": ROOT / "docs/STAGE-7-OPENAI-LIVE-PROVIDER-BENCHMARK.json",
    "xai": ROOT / "docs/STAGE-7-XAI-LIVE-PROVIDER-BENCHMARK.json",
}
Loader = Callable[[], StructuredProvider]


def cases() -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _disposition(execution: ProductExecution, stage8_pass: bool) -> str:
    if execution.display.route == "urgent":
        return "escalate"
    if execution.display.route == "clarification":
        return "clarify"
    if stage8_pass:
        return "pass"
    if execution.display.route in {"abstained", "unsupported"}:
        return "abstain"
    return "failed"


def _constraint_boundary_violations(execution: ProductExecution) -> int:
    """Count observed unsafe boundary escapes, not fail-closed provider errors."""

    if execution.stage8 is None or not execution.stage8.validation_report.display_allowed:
        return 0
    finding_codes = {str(item.code) for item in execution.stage8.validation_report.findings}
    boundary_codes = {
        "allergy_violation",
        "restriction_violation",
        "required_constraint_dropped",
        "prescribing_or_medication_change",
        "plan_combined_constraint_failure",
    }
    return len(finding_codes & boundary_codes)


def run_benchmark(
    *,
    provider_id: str,
    authorization_reference: str,
    maximum_total_cost_usd: float,
) -> tuple[ProviderBenchmarkReport, list[dict]]:
    if provider_id == "openai":
        status = inspect_openai_benchmark_configuration()
        loader: Loader = load_openai_benchmark_provider_from_env
    elif provider_id == "xai":
        status = inspect_xai_benchmark_configuration()
        loader = load_xai_benchmark_provider_from_env
    else:
        raise ValueError("provider must be openai or xai")
    if not status.ready:
        detail = status.error or "missing or invalid settings: " + ", ".join(
            status.missing_fields
        )
        raise RuntimeError(f"{provider_id} benchmark configuration is not ready ({detail})")
    if maximum_total_cost_usd <= 0:
        raise ValueError("a positive total benchmark cost ceiling is required")

    observations: list[ProviderBenchmarkObservation] = []
    case_results: list[dict] = []
    total_cost = 0.0
    for case in cases():
        if (
            case["expected_model_calls"] > 0
            and total_cost + float(status.max_request_cost_usd)
            > maximum_total_cost_usd
        ):
            raise RuntimeError(
                "the remaining total benchmark ceiling cannot cover the next configured request ceiling"
            )
        provider = loader()
        execution = run_compass(
            case["question"],
            horizon=case["horizon"],
            provider=provider,
        )
        request_cost = sum(
            item.trace.estimated_cost_usd for item in execution.stage7.worker_results
        )
        total_cost += request_cost
        total_input = sum(
            item.trace.input_tokens for item in execution.stage7.worker_results
        )
        total_output = sum(
            item.trace.output_tokens for item in execution.stage7.worker_results
        )
        route_matches = execution.display.route == case["expected_route"]
        call_count_matches = (
            execution.display.ordinary_generation_calls
            == case["expected_model_calls"]
        )
        stage8_pass = (
            execution.stage8 is not None
            and execution.stage8.validation_report.display_allowed
            and execution.display.route == "validated"
        )
        completed = route_matches and call_count_matches
        observation = ProviderBenchmarkObservation(
            case_id=case["case_id"],
            dataset_version=case["dataset_version"],
            provider_id=status.provider_id,
            model_id=status.model_id,
            completed=completed,
            stage8_disposition=_disposition(execution, stage8_pass),
            citation_claim_support_passed=(
                stage8_pass
                or execution.display.route in {"urgent", "clarification"}
            ),
            allergy_restriction_medication_violations=(
                _constraint_boundary_violations(execution)
            ),
            retries=sum(
                item.trace.retry_count for item in execution.stage7.worker_results
            ),
            timed_out=any(
                item.trace.stop_reason == "provider_timeout"
                for item in execution.stage7.worker_results
            ),
            latency_ms=execution.stage7.trace.latency_ms,
            input_tokens=total_input,
            output_tokens=total_output,
            estimated_cost_usd=request_cost,
            manual_tone_review="pending",
        )
        observations.append(observation)
        case_results.append(
            {
                "case_id": case["case_id"],
                "criticality": case["criticality"],
                "expected_route": case["expected_route"],
                "observed_route": execution.display.route,
                "expected_model_calls": case["expected_model_calls"],
                "observed_model_calls": execution.display.ordinary_generation_calls,
                "completed": completed,
                "stage8_display_allowed": stage8_pass,
                "summary": execution.display.summary,
                "worker_summaries": [
                    {
                        "agent": item.agent.value,
                        "provider": item.trace.provider,
                        "model": item.trace.model,
                        "summary": item.summary,
                    }
                    for item in execution.stage7.worker_results
                ],
                "input_tokens": total_input,
                "output_tokens": total_output,
                "estimated_cost_usd": request_cost,
                "stop_reasons": [
                    item.trace.stop_reason for item in execution.stage7.worker_results
                ],
            }
        )

    report = aggregate_authorized_benchmark(
        observations,
        authorization_reference=authorization_reference,
    )
    return report, case_results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("openai", "xai"))
    parser.add_argument("--execute-paid-fictional-benchmark", action="store_true")
    parser.add_argument("--authorization-reference", required=True)
    parser.add_argument("--maximum-total-cost-usd", required=True, type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case-output", type=Path)
    args = parser.parse_args(argv)
    load_dotenv(ROOT / ".env", override=False)

    if not args.execute_paid_fictional_benchmark:
        raise SystemExit(
            "Refusing to call a paid provider without --execute-paid-fictional-benchmark"
        )
    expected_reference = os.environ.get(
        "NESTLINE_BENCHMARK_AUTHORIZATION_REFERENCE", ""
    ).strip()
    if (
        not expected_reference
        or args.authorization_reference != expected_reference
    ):
        raise SystemExit(
            "Authorization reference must exactly match the configured local value"
        )
    try:
        report, case_results = run_benchmark(
            provider_id=args.provider,
            authorization_reference=args.authorization_reference,
            maximum_total_cost_usd=args.maximum_total_cost_usd,
        )
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from None

    output = args.output or DEFAULT_OUTPUTS[args.provider]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + chr(10),
        encoding="utf-8",
        newline=chr(10),
    )
    if args.case_output is not None:
        args.case_output.parent.mkdir(parents=True, exist_ok=True)
        args.case_output.write_text(
            json.dumps(
                {
                    "schema_version": "nestline-live-provider-case-results-v1",
                    "provider_id": report.provider_id,
                    "model_id": report.model_id,
                    "dataset_version": report.dataset_version,
                    "cases": case_results,
                },
                indent=2,
                sort_keys=True,
            )
            + chr(10),
            encoding="utf-8",
            newline=chr(10),
        )
    print(
        json.dumps(
            {
                "output": str(output),
                "case_output": (
                    str(args.case_output) if args.case_output is not None else None
                ),
                "completed_cases": report.completed_cases,
                "total_cases": report.total_cases,
                "stage8_passed_cases": report.stage8_passed_cases,
                "estimated_cost_usd": report.estimated_cost_usd,
                "manual_tone_reviews_pending": report.manual_tone_reviews_pending,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.completed_cases == report.total_cases else 1


if __name__ == "__main__":
    sys.exit(main())
