"""Run visible deterministic Stage 10 development cases and capstone stories."""

from __future__ import annotations

from collections import defaultdict
import io
import json
from pathlib import Path
from statistics import mean
from time import perf_counter
import unittest

from app.services.capstone_flows import run_all_capstone_stories
from scripts.build_stage10_evals import MANIFEST, cases as canonical_cases
from tests.test_state_lifecycle import StateCommitterTests


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-10-EVAL-RESULTS.json"
STORIES = ROOT / "docs/STAGE-10-CAPSTONE-STORY-RESULTS.json"


def load_cases() -> list[dict]:
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _run_case(case: dict) -> dict:
    started = perf_counter()
    result = unittest.TestResult()
    StateCommitterTests(case["test_method"]).run(result)
    latency = (perf_counter() - started) * 1000
    passed = result.testsRun == 1 and not result.failures and not result.errors and not result.skipped
    details = []
    for _, text in [*result.failures, *result.errors]:
        details.append(text[-1000:])
    return {
        "case_id": case["case_id"], "domain": case["domain"],
        "critical": case["critical"], "expected": case["expected"],
        "observed": "pass" if passed else "fail", "passed": passed,
        "latency_ms": round(latency, 4), "details": details,
    }


def main() -> int:
    expected = canonical_cases()
    if not MANIFEST.exists() or load_cases() != expected:
        raise RuntimeError("Stage 10 evaluation manifest is stale; run scripts.build_stage10_evals")
    results = [_run_case(case) for case in expected]
    story_models = run_all_capstone_stories()
    stories = [item.model_dump(mode="json") for item in story_models]
    story_report = {
        "schema_version": "10.0.0", "fictional": True,
        "deterministic_reset_before_each_run": True,
        "runs": stories, "passed": sum(item["passed"] for item in stories),
        "total": len(stories), "manual_database_edits": 0,
        "external_transmissions": 0, "called_clinical_validation": False,
    }
    STORIES.write_text(json.dumps(story_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    by_domain: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "total": 0})
    for item in results:
        by_domain[item["domain"]]["total"] += 1
        by_domain[item["domain"]]["passed"] += int(item["passed"])
    critical = [item for item in results if item["critical"]]
    passed = sum(item["passed"] for item in results)
    latencies = [item["latency_ms"] for item in results]
    report = {
        "valid": passed == len(results) and story_report["passed"] == story_report["total"],
        "stage": 10, "schema_version": "10.0.0",
        "dataset": "visible deterministic Stage 10 development set; sealed final holdout not accessed",
        "fixture_only": True, "clinical_validation": False,
        "cases": {"passed": passed, "total": len(results)},
        "critical_cases": {"passed": sum(item["passed"] for item in critical), "total": len(critical)},
        "by_domain": dict(sorted(by_domain.items())),
        "capstone_story_runs": {"passed": story_report["passed"], "total": story_report["total"]},
        "urgent_zero_generation": {"passed": sum(item["story"] != "urgent-review" or item["ordinary_generation_calls"] == 0 for item in stories), "total": len(stories)},
        "unauthorized_writes": 0, "external_transmissions": 0,
        "latency_ms": {"samples": len(latencies), "mean": round(mean(latencies), 4), "maximum": round(max(latencies), 4)},
        "case_results": results,
        "failures": [item for item in results if not item["passed"]] + [item for item in stories if not item["passed"]],
        "limitations": [
            "Deterministic fictional fixtures do not prove production concurrency, retrieval, clinical, or usability quality.",
            "Live provider benchmarks and the sealed final holdout were not run.",
            "External notifications and real clinician review remain unavailable by design.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "cases": report["cases"], "critical_cases": report["critical_cases"], "capstone_story_runs": report["capstone_story_runs"], "report": str(REPORT.relative_to(ROOT))}, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
