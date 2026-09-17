"""Generate the Stage 10 deletion and retention inventory."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/STAGE-10-DELETION-RETENTION-INVENTORY.json"


def inventory() -> dict:
    return {
        "schema_version": "10.0.0",
        "workspace_reset_boundary": {
            "authorization": "existing owner-only workspace DELETE policy or controlled local fixture administrator",
            "pre_delete_trigger": "private.stage10_prepare_workspace_delete",
            "storage_precondition": "Storage objects must be deleted through the Storage API before database workspace deletion",
            "recreated_workspace_behavior": "a new workspace UUID creates a new idempotency scope; old results cannot replay",
        },
        "objects": [
            {"object": "public.plans", "data": "saved plan lifecycle and user edits", "disposition": "workspace cascade", "retained_after_reset": False},
            {"object": "public.plan_items", "data": "validated plan items", "disposition": "plan/workspace cascade", "retained_after_reset": False},
            {"object": "private.stage10_plan_dependencies", "data": "plan dependency ledger", "disposition": "plan cascade", "retained_after_reset": False},
            {"object": "private.stage10_plan_lifecycle_events", "data": "plan transition ledger", "disposition": "plan cascade", "retained_after_reset": False},
            {"object": "private.stage10_fact_decisions", "data": "fact decision and provenance ledger", "disposition": "explicit pre-delete removal inside workspace transaction", "retained_after_reset": False},
            {"object": "public.health_facts", "data": "confirmed facts and supersession links", "disposition": "supersession links cleared, then workspace cascade", "retained_after_reset": False},
            {"object": "public.document_facts", "data": "extracted candidates and decisions", "disposition": "document/workspace cascade after private decision removal", "retained_after_reset": False},
            {"object": "private.stage10_commit_log", "data": "idempotency result and redacted trace", "disposition": "workspace cascade", "retained_after_reset": False},
            {"object": "public.follow_up_tasks", "data": "in-app follow-up and reminder consent", "disposition": "workspace cascade", "retained_after_reset": False},
            {"object": "public.human_review_cases", "data": "simulated review packet and status", "disposition": "workspace cascade", "retained_after_reset": False},
            {"object": "public.graph_nodes", "data": "workspace causal nodes", "disposition": "workspace cascade", "retained_after_reset": False},
            {"object": "public.graph_edges", "data": "workspace causal edges", "disposition": "workspace/node cascade", "retained_after_reset": False},
            {"object": "public.personal_retrieval_versions", "data": "workspace state/cache version", "disposition": "workspace cascade", "retained_after_reset": False},
        ],
        "external_retention": {
            "storage_objects": "not deleted by SQL; existing Storage API deletion must complete first",
            "notifications": "external delivery is disabled; no email, SMS, or push artifact is created",
            "real_clinician_records": "not implemented",
        },
        "verification": {
            "two_principals": True,
            "workspace_a_removed": True,
            "workspace_b_unchanged": True,
            "orphan_checks_required": True,
            "fixture_cleanup_zero_required": True,
        },
    }


def main() -> int:
    OUTPUT.write_text(json.dumps(inventory(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "objects": len(inventory()["objects"]), "output": str(OUTPUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())