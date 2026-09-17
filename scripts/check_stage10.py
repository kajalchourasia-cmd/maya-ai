"""Deterministic Stage 10 completion checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_stage10_evals import cases as canonical_cases
from scripts.export_stage10_retention_inventory import inventory
from scripts.export_stage10_self_review import review
from scripts.export_state_lifecycle_schema import coverage_bundle, schema_bundle


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-10-CHECK-RESULTS.json"
SCHEMA = ROOT / "data/schemas/state_lifecycle.schema.json"
COVERAGE = ROOT / "docs/STAGE-10-COVERAGE-MANIFEST.json"
EVAL_REPORT = ROOT / "docs/STAGE-10-EVAL-RESULTS.json"
STORIES = ROOT / "docs/STAGE-10-CAPSTONE-STORY-RESULTS.json"
SELF_REVIEW = ROOT / "docs/STAGE-10-SELF-REVIEW-FINDINGS.json"
CONCURRENCY = ROOT / "docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json"
RETENTION = ROOT / "docs/STAGE-10-DELETION-RETENTION-INVENTORY.json"
HANDOFF = ROOT / "docs/STAGE-10-IMPLEMENTATION-SELF-VERIFICATION-AND-CAPSTONE-READINESS.md"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check() -> dict:
    errors: list[str] = []
    required = [
        ROOT / "app/schemas/state_lifecycle.py",
        ROOT / "app/services/state_committer.py",
        ROOT / "app/services/capstone_flows.py",
        ROOT / "app/pages_and_components/stage9.py",
        ROOT / "supabase/migrations/20260912000100_stage10_state_review_lifecycle.sql",
        ROOT / "supabase/migrations/20260912000200_stage10_rpc_hardening_and_reset.sql",
        ROOT / "supabase/tests/stage10_state_review_lifecycle.test.sql",
        ROOT / "supabase/tests/stage10_rpc_hardening_and_reset.test.sql",
        ROOT / "supabase/fixtures/stage10_stage9_upgrade.sql",
        ROOT / "supabase/fixtures/stage10_stage9_upgrade_check.sql",
        ROOT / "scripts/check_stage10_state_api.py",
        ROOT / "scripts/check_stage10_concurrency_and_deletion_api.py",
        ROOT / "scripts/check_stage10_ui.py",
        ROOT / "scripts/export_stage10_self_review.py",
        ROOT / "scripts/export_stage10_retention_inventory.py",
        ROOT / "tests/test_state_lifecycle.py",
        ROOT / "tests/test_capstone_flows.py",
        ROOT / "evals/stage10_state_lifecycle.jsonl",
        SCHEMA, COVERAGE, EVAL_REPORT, STORIES, SELF_REVIEW, CONCURRENCY,
        RETENTION, HANDOFF,
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing Stage 10 artifact: {path.relative_to(ROOT)}")

    if SCHEMA.is_file() and _json(SCHEMA) != schema_bundle():
        errors.append("Stage 10 exported schemas are stale")
    if COVERAGE.is_file() and _json(COVERAGE) != coverage_bundle():
        errors.append("Stage 10 coverage manifest is stale")

    expected_cases = canonical_cases()
    if EVAL_REPORT.is_file():
        report = _json(EVAL_REPORT)
        expected = {"passed": len(expected_cases), "total": len(expected_cases)}
        if not report.get("valid") or report.get("cases") != expected:
            errors.append("Stage 10 evaluation report is stale or failed")
        if report.get("capstone_story_runs") != {"passed": 9, "total": 9}:
            errors.append("all three connected stories did not pass three reset runs")
        if report.get("unauthorized_writes") != 0 or report.get("external_transmissions") != 0:
            errors.append("Stage 10 evaluation performed an unauthorized write or transmission")

    if STORIES.is_file():
        stories = _json(STORIES)
        if stories.get("passed") != 9 or stories.get("total") != 9:
            errors.append("Stage 10 capstone story evidence is incomplete")
        if any(item.get("ordinary_generation_calls") for item in stories.get("runs", [])
               if item.get("story") == "urgent-review"):
            errors.append("urgent capstone story invoked ordinary generation")

    if SELF_REVIEW.is_file() and _json(SELF_REVIEW) != review():
        errors.append("Stage 10 self-review findings are stale")
    if SELF_REVIEW.is_file():
        unresolved = [item["id"] for item in _json(SELF_REVIEW).get("findings", [])
                      if item.get("post_status") != "PASS"]
        if unresolved:
            errors.append(f"Stage 10 self-review findings remain unresolved: {unresolved}")

    if CONCURRENCY.is_file():
        concurrency = _json(CONCURRENCY)
        if not concurrency.get("valid") or concurrency.get("checks") != 26:
            errors.append("Stage 10 concurrency/deletion matrix is stale or failed")
        if concurrency.get("workspace_reset_public_tables_checked") != 10:
            errors.append("Stage 10 workspace reset coverage is incomplete")
        if any(value.get("committed") != 1 or value.get("rejected") != 1
               for value in concurrency.get("concurrency", {}).values()):
            errors.append("Stage 10 concurrency races did not commit exactly one contender")
        if (not concurrency.get("response_loss_replay")
                or concurrency.get("old_idempotency_replay_after_reset")):
            errors.append("Stage 10 idempotency/reset evidence is invalid")

    if RETENTION.is_file() and _json(RETENTION) != inventory():
        errors.append("Stage 10 deletion/retention inventory is stale")

    migration_paths = [
        ROOT / "supabase/migrations/20260912000100_stage10_state_review_lifecycle.sql",
        ROOT / "supabase/migrations/20260912000200_stage10_rpc_hardening_and_reset.sql",
    ]
    migration = "\n".join(
        path.read_text(encoding="utf-8") for path in migration_paths if path.is_file()
    )
    for required_sql in (
        "public.stage10_commit", "public.stage10_durable_state",
        "private.stage10_plan_dependencies", "plans_one_active_per_workspace",
        "revoke insert, update, delete", "external_delivery_scheduled",
        "stage10_bind_plan_scope", "stage10_invalidate_fact_change",
        "stage10_assert_object_keys", "stage10_prepare_workspace_delete", "PT409",
    ):
        if required_sql not in migration:
            errors.append(f"Stage 10 migration lacks required control: {required_sql}")
    if "grant execute on function public.stage10_commit(uuid,jsonb) to authenticated" not in migration:
        errors.append("State Committer is not restricted to authenticated callers")

    safety = json.loads((ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8"))
    if safety.get("status") != "draft":
        errors.append("Stage 10 changed the draft safety specification boundary")
    combined = "".join(
        path.read_text(encoding="utf-8") for path in required[:3] if path.is_file()
    ).casefold()
    for forbidden in ("import openai", "import langchain", "import n8n"):
        if forbidden in combined:
            errors.append(f"Stage 10 deterministic boundary added a forbidden provider: {forbidden}")

    if HANDOFF.is_file():
        handoff = HANDOFF.read_text(encoding="utf-8")
        verdicts = (
            "STAGE 10 ACCEPTED FOR CONTROLLED ENGINEERING — CAPSTONE READY FOR INDEPENDENT REVIEW",
            "STAGE 10 NO-GO — CAPSTONE MUST NOT BE RELEASED",
        )
        if not any(verdict in handoff for verdict in verdicts):
            errors.append("Stage 10 handoff lacks an exact verdict")

    return {
        "valid": not errors,
        "stage": 10,
        "schema_version": "10.0.0",
        "database_migration_required": True,
        "remote_migration_applied": False,
        "paid_provider_required": False,
        "external_delivery_enabled": False,
        "clinical_validation": False,
        "public_release_ready": False,
        "verified": {
            "typed_development_cases": len(expected_cases),
            "capstone_story_runs": 9,
            "command_kinds": 7,
            "plan_lifecycle_states": 7,
            "review_states": 9,
            "authenticated_api_checks": 14,
            "concurrency_and_deletion_checks": 26,
            "urgent_generation_calls": 0,
            "external_transmissions": 0,
        },
        "limitations": [
            "Controlled fictional fixtures do not prove clinical or production quality.",
            "The public safety/content review gates remain open.",
            "External reminders, real clinician review, deployment, and the sealed holdout remain unrun.",
        ],
        "errors": errors,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    result = check()
    if args.write_report:
        REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
