"""Generate the canonical Stage 10 consolidated self-review findings."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/STAGE-10-SELF-REVIEW-FINDINGS.json"


def review() -> dict:
    findings = [
        {
            "id": "S10-SR-001", "severity": "high",
            "requirement": "Multi-table dependency invalidation must be safe and selective",
            "first_status": "FAIL",
            "evidence": "A shared row trigger referenced fields absent from some trigger tables during clean replay.",
            "rectification": "Split invalidation into journey, fact, symptom, medication and evidence table-specific trigger functions with bounded dependency lookup.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-002", "severity": "high",
            "requirement": "Existing plans and reviews must bind authenticated owner and current journey truth",
            "first_status": "FAIL",
            "evidence": "New required owner/journey columns made an accepted Stage 2 fixture insert invalid.",
            "rectification": "Added database-derived owner/journey binding triggers and retained strict foreign keys.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-003", "severity": "high",
            "requirement": "Refresh and relogin must reload durable truth",
            "first_status": "FAIL",
            "evidence": "The initial UI integration exposed only a version snapshot, not committed fact/plan/task/review records.",
            "rectification": "Added owner-only stage10_durable_state RPC, authenticated client method and UI reload on each authenticated render.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-004", "severity": "high",
            "requirement": "User edits must pass the accepted Stage 8 validation boundary",
            "first_status": "FAIL",
            "evidence": "Plan user_edits initially accepted untyped dictionaries.",
            "rectification": "Added strict ValidatedPlanEdit schema, trace requirement, item/field matching and transactional SQL enforcement.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-005", "severity": "high",
            "requirement": "A plan cannot omit active confirmed hard constraints",
            "first_status": "FAIL",
            "evidence": "A syntactically valid plan could omit a confirmed allergy dependency.",
            "rectification": "Both committers require dependencies for every active confirmed allergy, restriction and clinician instruction.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-006", "severity": "high",
            "requirement": "Corrections must invalidate dependencies on superseded truth",
            "first_status": "FAIL",
            "evidence": "A correction invalidated only the new material key and could leave a plan linked to superseded truth active.",
            "rectification": "Correction commits invalidate the old fact identity/material dependency and new confirmed dependency atomically.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-007", "severity": "high",
            "requirement": "Only the State Committer may mutate confirmed facts and plans",
            "first_status": "FAIL",
            "evidence": "Earlier authenticated direct CRUD policies remained on Stage 10-owned tables.",
            "rectification": "Replaced direct mutation policies with owner-read policies and the authenticated State Committer RPC.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-008", "severity": "medium",
            "requirement": "Offline UI checks must show recoverable unavailability",
            "first_status": "FAIL",
            "evidence": "Stage 4 UI smoke reproduced an uncaught network error from durable-state loading.",
            "rectification": "The client emits a typed recoverable failure and the UI renders an honest unavailable state.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-009", "severity": "medium",
            "requirement": "Migration SQL must compile on clean and upgrade histories",
            "first_status": "FAIL",
            "evidence": "Clean pgTAP exposed an ambiguous JSON dependency alias inside PL/pgSQL.",
            "rectification": "Renamed the alias and replayed both clean and exact upgrade histories.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-010", "severity": "high",
            "requirement": "All earlier pgTAP regressions remain meaningful and green under the Stage 10 write boundary",
            "first_status": "FAIL",
            "evidence": "The legacy Stage 2 file required direct CRUD that Stage 10 intentionally revokes and stopped at assertion 32/122.",
            "rectification": "Preserved all 122 assertions while making post-Stage-10 expectations verify owner reads and denial of direct writes; State Committer pgTAP remains separate.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-011", "severity": "high",
            "requirement": "The JSONB RPC must reject unknown, forged and oversized command shapes before mutation",
            "first_status": "FAIL",
            "evidence": "The original SQL implementation validated required values but did not enforce exact nested object keys or a bounded request size.",
            "rectification": "Added an authenticated strict wrapper with exact top-level and per-kind nested allowlists, a 64 KiB limit and private implementation isolation.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-012", "severity": "high",
            "requirement": "A stale API command must return a bounded conflict response",
            "first_status": "FAIL",
            "evidence": "Stale-state errors used SQLSTATE 40001, causing PostgREST to retry the deterministic rejection until the HTTP client timed out.",
            "rectification": "The forward hardening migration maps deterministic stale conflicts to PT409; simultaneous authenticated HTTP races now return one commit and one rejection.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-013", "severity": "high",
            "requirement": "Workspace reset removes all scoped durable and derived state without cross-workspace impact",
            "first_status": "FAIL",
            "evidence": "Self-referential fact/plan history and private ledgers had no explicit deletion-order contract or machine-readable inventory.",
            "rectification": "Added a pre-delete cleanup trigger, 13-object retention inventory, two-principal reset checks, orphan checks and recreated-workspace idempotency isolation.",
            "post_status": "PASS",
        },
        {
            "id": "S10-SR-014", "severity": "high",
            "requirement": "Demo reset must not retain Stage 10 fixture state or clear Personal Mode state",
            "first_status": "FAIL",
            "evidence": "The reset helper removed stage9_demo_* keys but left stage10_demo_* commit/idempotency state.",
            "rectification": "Reset now clears both demo prefixes and the regression proves personal keys remain untouched.",
            "post_status": "PASS",
        },
    ]
    return {
        "schema_version": "10.0.0",
        "review_kind": "single_consolidated_self_review",
        "reviewed_stage10_checkpoint": "a044ecb8fd2be9c7986c8401367956f85bcbd3e6",
        "integration_branch_base": "e2a8c542648f97c9bb93d73528f2414a4f41e5c8",
        "branch": "integration/capstone-demo-final",
        "findings": findings,
        "summary": {
            "findings": len(findings),
            "post_pass": len(findings),
            "post_blocked": 0,
            "post_fail": 0,
            "verdict": "GO_PENDING_COMPLETE_CONSOLIDATED_VERIFICATION",
        },
    }


def main() -> int:
    payload = review()
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "findings": len(payload["findings"]), "output": str(OUTPUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
