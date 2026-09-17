"""Export the canonical Stage 10 state/lifecycle schemas and coverage inventory."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.state_lifecycle import (
    AuthenticatedCommitScope, CapstoneStoryResult, CommitAuditTrace, CommitProvenance,
    DurableSnapshot, FactDecisionPayload, FollowUpCreatePayload,
    FollowUpTransitionPayload, PlanCreatePayload, PlanTransitionPayload,
    ReviewCreatePayload, ReviewPacket, ReviewTransitionPayload, StateCommitCommand,
    ValidatedPlanEdit,
    StateCommitResult,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/schemas/state_lifecycle.schema.json"
COVERAGE = ROOT / "docs/STAGE-10-COVERAGE-MANIFEST.json"


def schema_bundle() -> dict:
    contracts = [
        AuthenticatedCommitScope, CommitProvenance, FactDecisionPayload,
        PlanCreatePayload, PlanTransitionPayload, FollowUpCreatePayload,
        FollowUpTransitionPayload, ReviewPacket, ReviewCreatePayload,
        ReviewTransitionPayload, ValidatedPlanEdit, StateCommitCommand, CommitAuditTrace,
        StateCommitResult, DurableSnapshot, CapstoneStoryResult,
    ]
    return {
        "schema_version": "10.0.0",
        "contracts": {model.__name__: model.model_json_schema() for model in contracts},
    }


def coverage_bundle() -> dict:
    return {
        "schema_version": "10.0.0",
        "single_write_boundary": "public.stage10_commit(uuid,jsonb)",
        "authenticated_snapshot": "public.stage10_authenticated_snapshot(uuid)",
        "command_kinds": [
            "fact_decision", "plan_create", "plan_transition", "follow_up_create",
            "follow_up_transition", "review_create", "review_transition",
        ],
        "plan_lifecycle": [
            "draft", "user_reviewed", "saved", "active", "stale", "replaced", "archived",
        ],
        "dependency_kinds": [
            "journey_state", "allergy", "restriction", "condition", "symptom",
            "medication", "supplement", "clinician_instruction", "evidence",
        ],
        "review_states": [
            "not_required", "offered", "consented", "queued", "reviewed", "resumed",
            "declined", "unavailable", "timed_out",
        ],
        "external_delivery": "unavailable",
        "ordinary_service_role": "forbidden",
        "agent_direct_writes": "forbidden",
        "migrations": [
            "20260912000100_stage10_state_review_lifecycle.sql",
            "20260912000200_stage10_rpc_hardening_and_reset.sql",
        ],
        "remote_migration_applied": False,
        "fictional_only_evaluation": True,
    }


def main() -> int:
    SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA.write_text(json.dumps(schema_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COVERAGE.write_text(json.dumps(coverage_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "contracts": len(schema_bundle()["contracts"]), "coverage": str(COVERAGE.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
