"""Check the consolidated Stages 0–8 and 10 improvement controls."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.configuration import ApplicationMode, validate_configuration
from scripts.build_stage9_immutability_manifest import stable_sha256

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "docs/STAGE-0-PUBLICATION-READINESS-LEDGER.json",
    "docs/STAGE-0-PUBLICATION-READINESS-SUMMARY.md",
    "docs/STAGE-0-DEMONSTRATION-SLICE-REVIEW-PACKET.md",
    "docs/STAGE-0-COMPARISON-REVIEW-PACKET.md",
    "docs/STAGE-1-INGESTION-FAILURE-RECOVERY-RUNBOOK.md",
    "data/supabase/migration_manifest.json",
    "docs/STAGE-2-DEPLOYMENT-MIGRATION-RUNBOOK.md",
    "docs/STAGE-4-DOCUMENT-PROVIDER-BENCHMARK-PLAN.md",
    "evals/stage4_document_provider_benchmark.jsonl",
    "docs/STAGE-5-EMBEDDING-RERANKING-DECISION.md",
    "docs/STAGE-6-REDUCED-MOVEMENT-QUALIFIED-REVIEW-PACKET.md",
    "docs/STAGE-7-LIVE-PROVIDER-BENCHMARK-AND-SELECTION-GATE.md",
    "docs/STAGE-8-HUMAN-REVIEW-PACKETS.md",
    "docs/STAGE-10-DRAFT-REVIEW-COMMIT-BOUNDARY.md",
    "docs/NESTLINE-EVALUATION-MANIFEST.json",
    "docs/NESTLINE-CAPABILITY-MATRIX.json",
    "docs/STAGES-0-8-10-SERVICE-JOURNEY-RESULTS.json",
    "docs/NESTLINE-CURRENT-STATUS.md",
    "docs/HISTORICAL-REPORT-INDEX.md",
    "data/stage9_ui_immutability_manifest.json",
]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append("missing " + name)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        return 1

    ledger = load("docs/STAGE-0-PUBLICATION-READINESS-LEDGER.json")["counts"]
    expected = {
        "profiles": 63,
        "sources": 31,
        "source_spans": 55,
        "guidance_fragments": 56,
        "published_profiles": 0,
        "comparisons": 42,
        "display_eligible_comparisons": 0,
    }
    for key, value in expected.items():
        if ledger.get(key) != value:
            errors.append(f"publication ledger {key}={ledger.get(key)} expected {value}")

    safety = load("docs/STAGE-6-SAFETY-EVAL-RESULTS.json")
    if not safety.get("valid") or safety.get("cases") != {"passed": 65, "total": 65}:
        errors.append("Stage 6 report is not 65/65")
    journeys = load("docs/STAGES-0-8-10-SERVICE-JOURNEY-RESULTS.json")
    if journeys.get("cases") != {"passed": 17, "total": 17}:
        errors.append("service journeys are not 17/17")
    if journeys.get("approved_published_slice_available") is not False:
        errors.append("service journeys invented a published slice")
    evaluations = load("docs/NESTLINE-EVALUATION-MANIFEST.json")
    if evaluations.get("sealed_holdout_accessed") is not False or evaluations["totals"]["datasets"] != 12:
        errors.append("evaluation manifest is incomplete")
    capabilities = load("docs/NESTLINE-CAPABILITY-MATRIX.json")
    if len(capabilities.get("capabilities", [])) != 21:
        errors.append("capability matrix is incomplete")
    for provider in ("XAI", "OPENAI"):
        report = load(f"docs/STAGE-7-{provider}-LIVE-PROVIDER-BENCHMARK.json")
        if report.get("constraint_boundary_violations") != 0:
            errors.append(f"{provider} report conflates failure with displayed constraint escape")
        if report.get("manual_tone_reviews_pending") != 8:
            errors.append(f"{provider} human tone denominator is not pending 8/8")

    demo = validate_configuration({}, mode=ApplicationMode.DEMO)
    if not demo.valid or not demo.fixture_provider_permitted:
        errors.append("Demo configuration no longer works credential-free")
    personal = validate_configuration(
        {
            "NESTLINE_SUPABASE_URL": "https://fixture.invalid",
            "NESTLINE_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture",
        },
        mode=ApplicationMode.PERSONAL,
    )
    if personal.valid:
        errors.append("incomplete Personal Mode did not fail closed")

    frozen = load("data/stage9_ui_immutability_manifest.json")
    if frozen.get("schema_version") != "stage9-ui-immutability-v2":
        errors.append("Stage 9 immutability manifest is not cross-platform version 2")
    for row in frozen["files"]:
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append("Stage 9 excluded file missing: " + row["path"])
            continue
        digest, hash_mode = stable_sha256(path)
        if digest != row["sha256"] or hash_mode != row.get("hash_mode"):
            errors.append("Stage 9 excluded file changed: " + row["path"])

    result = {
        "valid": not errors,
        "checks": {
            "required_artifacts": len(REQUIRED),
            "publication_inventory": len(expected),
            "safety_cases": 65,
            "service_journeys": 17,
            "evaluation_datasets": 12,
            "capabilities": 21,
            "provider_reports": 2,
            "stage9_immutable_files": len(frozen["files"]),
            "configuration_modes": 2,
        },
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
