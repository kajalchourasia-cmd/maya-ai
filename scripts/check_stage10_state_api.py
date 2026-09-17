"""Exercise the Stage 10 RPC with two real local authenticated principals.

Fixture setup and cleanup use the local service key. Every product operation uses
the public key plus a user JWT. No token, email, record text, or key is printed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from urllib.parse import quote
from uuid import uuid4

from scripts.check_stage2_storage_api import (
    LocalSupabase, _expect_denied, _expect_success,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _command(kind: str, key: str, version: int, payload: dict, provenance: dict) -> dict:
    return {
        "schema_version": "10.0.0",
        "command_id": str(uuid4()),
        "idempotency_key": key,
        "expected_state_version": version,
        "submitted_at": _now(),
        "caller": "authenticated_ui",
        "provenance": provenance,
        "confirmation": {
            "confirmed": True,
            "confirmation_id": f"confirmation-{key}",
            "confirmed_at": _now(),
            "wording_version": "stage10-confirmation-v1",
            "consent_scope": "Apply this controlled fictional action",
        },
        "payload": {"kind": kind, **payload},
    }


def _snapshot(client: LocalSupabase, token: str, workspace: str) -> dict:
    status, raw = client.request(
        "POST", "/rest/v1/rpc/stage10_authenticated_snapshot",
        key=client.anon_key, token=token,
        json_body={"requested_workspace_id": workspace},
    )
    _expect_success(status, "authenticated Stage 10 snapshot")
    result = client.json(raw)
    if not result or not result.get("database_derived_state"):
        raise AssertionError("snapshot was not derived from authenticated storage")
    return result


def _commit(client: LocalSupabase, token: str, workspace: str, command: dict) -> tuple[int, dict | None]:
    status, raw = client.request(
        "POST", "/rest/v1/rpc/stage10_commit", key=client.anon_key, token=token,
        json_body={"requested_workspace_id": workspace, "requested_command": command},
    )
    return status, client.json(raw)


def main() -> int:
    client = LocalSupabase()
    marker = uuid4().hex
    password = f"Nestline-{uuid4().hex}-A1!"
    emails = [f"stage10-owner-{marker}@example.invalid", f"stage10-other-{marker}@example.invalid"]
    user_ids: list[str] = []
    workspace_ids: list[str] = []
    created_release: str | None = None
    checks = 0

    try:
        tokens: list[str] = []
        for email in emails:
            status, raw = client.request(
                "POST", "/auth/v1/admin/users", key=client.service_key,
                json_body={"email": email, "password": password, "email_confirm": True},
            )
            _expect_success(status, "temporary user creation")
            user_ids.append(client.json(raw)["id"])
            status, raw = client.request(
                "POST", "/auth/v1/token?grant_type=password", key=client.anon_key,
                json_body={"email": email, "password": password},
            )
            _expect_success(status, "temporary user sign-in")
            tokens.append(client.json(raw)["access_token"])

        for index, token in enumerate(tokens):
            status, raw = client.request(
                "POST", "/rest/v1/rpc/create_workspace", key=client.anon_key, token=token,
                json_body={"requested_mode": "fictional_demo", "requested_display_name": f"Stage 10 API fixture {index + 1}"},
            )
            _expect_success(status, "workspace creation")
            workspace_ids.append(client.json(raw))

        owner_workspace, other_workspace = workspace_ids
        release_id, source_id = str(uuid4()), f"SRC-STAGE10-{marker[:10]}"
        created_release = release_id
        status, _ = client.request(
            "POST", "/rest/v1/content_releases", key=client.service_key,
            json_body={"id": release_id, "corpus_version": f"stage10-api-{marker}", "release_fingerprint": "1" * 64, "status": "published", "published_at": _now()},
        )
        _expect_success(status, "release fixture")
        status, _ = client.request(
            "POST", "/rest/v1/public_sources", key=client.service_key,
            json_body={"source_id": source_id, "release_id": release_id, "title": "Stage 10 API fixture", "publisher": "Nestline tests", "canonical_url": "https://example.invalid/stage10-api", "jurisdiction": ["GLOBAL"], "source_version": "1", "reuse_status": "permitted", "allowed_use": ["testing"], "status": "published", "content_checksum": "2" * 64},
        )
        _expect_success(status, "source fixture")
        evidence_id = f"EVID-STAGE10-{marker[:10]}"
        status, _ = client.request(
            "POST", "/rest/v1/guideline_chunks", key=client.service_key,
            json_body={"chunk_id": f"CHUNK-STAGE10-{marker[:10]}", "release_id": release_id, "evidence_id": evidence_id, "source_id": source_id, "candidate_checksum": "3" * 64, "text": "Controlled fictional evidence.", "source_block_ids": ["BLOCK-STAGE10"], "stage": "pregnancy", "unit": "week", "range_start": 24, "range_end": 24, "jurisdiction": ["GLOBAL"], "domains": ["nutrition"], "display_slots": ["plan"], "status": "published"},
        )
        _expect_success(status, "evidence fixture")

        journey_id, document_id, candidate_id = str(uuid4()), str(uuid4()), str(uuid4())
        status, _ = client.request(
            "POST", "/rest/v1/journey_states", key=client.service_key,
            json_body={"id": journey_id, "workspace_id": owner_workspace, "stage": "pregnancy", "timing_source": "manual_week_day", "gestational_week": 24, "gestational_day": 2, "user_confirmed": True, "version": 1, "confirmed_at": _now(), "confirmed_by_user_id": user_ids[0], "effective_date": datetime.now(UTC).date().isoformat(), "calculation_date": datetime.now(UTC).date().isoformat()},
        )
        _expect_success(status, "journey fixture")
        status, _ = client.request(
            "POST", "/rest/v1/private_documents", key=client.service_key,
            json_body={"id": document_id, "workspace_id": owner_workspace, "storage_object_path": f"{owner_workspace}/stage10/DOC-001.pdf", "original_filename": "DOC-001.pdf", "media_type": "application/pdf", "byte_size": 100, "sha256": "a" * 64, "status": "needs_confirmation", "contains_real_medical_data": False, "fixture_document_key": "DOC-001", "scan_status": "fixture_verified", "scan_provider": "api-check", "scan_version": "v1", "scan_completed_at": _now(), "review_version": 1},
        )
        _expect_success(status, "fictional document fixture")
        exact_span = "allergy: sesame"
        status, _ = client.request(
            "POST", "/rest/v1/document_facts", key=client.service_key,
            json_body={"id": candidate_id, "workspace_id": owner_workspace, "document_id": document_id, "field_name": "allergy", "value": {"label": "sesame"}, "source_page": 1, "source_text": exact_span, "confidence": 1.0, "status": "proposed", "candidate_key": "p1-allergy", "fact_type": "allergy", "source_span": {"page": 1, "exact_text": exact_span, "start": 0, "end": 15}, "completeness": "complete", "disposition": "extract_verbatim", "record_only": False, "source_value_matches": True},
        )
        _expect_success(status, "document fact fixture")

        snapshot = _snapshot(client, tokens[0], owner_workspace)
        checks += 1
        status, raw = client.request(
            "POST", "/rest/v1/rpc/stage10_authenticated_snapshot", key=client.anon_key,
            token=tokens[1], json_body={"requested_workspace_id": owner_workspace},
        )
        _expect_success(status, "other-owner empty snapshot request")
        if client.json(raw) is not None:
            raise AssertionError("other user derived the owner's state")
        checks += 1

        provenance = {
            "kind": "document_candidate", "source_id": "candidate:p1-allergy",
            "source_document_id": document_id, "source_document_fact_id": candidate_id,
            "source_page": 1, "exact_span": exact_span,
            "exact_span_sha256": sha256(exact_span.encode()).hexdigest(),
        }
        fact_command = _command(
            "fact_decision", f"stage10-api-fact-{marker}", snapshot["current_state_version"],
            {"document_fact_id": candidate_id, "decision": "confirm", "material_dependency_key": "sesame"}, provenance,
        )
        status, fact_result = _commit(client, tokens[0], owner_workspace, fact_command)
        _expect_success(status, "owner fact commit")
        if fact_result["status"] != "committed" or fact_result["trace"]["raw_personal_text_logged"]:
            raise AssertionError("fact commit result or trace was invalid")
        checks += 1
        status, replay = _commit(client, tokens[0], owner_workspace, fact_command)
        _expect_success(status, "idempotent fact replay")
        if replay["status"] != "replayed" or not replay["idempotent_replay"]:
            raise AssertionError("fact replay was not idempotent")
        checks += 1

        plan_id, item_id = str(uuid4()), str(uuid4())
        snapshot = _snapshot(client, tokens[0], owner_workspace)
        plan_command = _command(
            "plan_create", f"stage10-api-plan-{marker}", snapshot["current_state_version"],
            {
                "plan_id": plan_id, "journey_state_id": journey_id, "journey_week": 24,
                "source_release_id": release_id, "user_preferences": {"window": "morning"},
                "confirmed_constraints": ["sesame allergy"], "component_agent_outputs": {"nutrition": "validated fixture"},
                "source_evidence_ids": [evidence_id], "user_edits": [], "validation_disposition": "pass",
                "validation_trace_id": str(uuid4()), "unresolved_conflict_ids": [],
                "items": [{"item_id": item_id, "domain": "nutrition", "title": "Fictional breakfast", "body": "Choose a validated sesame-free option.", "day": "monday", "time_window": "morning", "record_only": False, "evidence_ids": [evidence_id], "applied_constraint_ids": fact_result["entity_ids"][1:], "material_keys": ["oats"], "excluded_material_keys": ["sesame"], "contributor": "nutrition-agent-v1"}],
                "dependencies": [{"kind": "journey_state", "entity_id": journey_id, "material_key": "pregnancy-week-24"}, {"kind": "allergy", "entity_id": fact_result["entity_ids"][-1], "material_key": "sesame", "source_item_id": item_id}, {"kind": "evidence", "entity_id": evidence_id, "material_key": f"stage10-api-{marker}", "source_item_id": item_id}],
            },
            {"kind": "validated_plan", "source_id": "stage8-validated-fixture", "validation_policy_version": "stage8-validation-v1"},
        )
        status, result = _commit(client, tokens[0], owner_workspace, plan_command)
        _expect_success(status, "validated plan create")
        if result["status"] != "committed":
            raise AssertionError("plan did not begin as a committed draft")
        checks += 1

        for from_state, to_state in (("draft", "user_reviewed"), ("user_reviewed", "saved"), ("saved", "active")):
            snapshot = _snapshot(client, tokens[0], owner_workspace)
            command = _command(
                "plan_transition", f"stage10-api-plan-{to_state}-{marker}", snapshot["current_state_version"],
                {"plan_id": plan_id, "from_status": from_state, "to_status": to_state},
                {"kind": "user_action", "source_id": "stage10-plan-ui"},
            )
            status, _ = _commit(client, tokens[0], owner_workspace, command)
            _expect_success(status, f"plan transition {from_state} to {to_state}")
            checks += 1

        status, raw = client.request(
            "POST", "/rest/v1/rpc/stage10_durable_state", key=client.anon_key,
            token=tokens[0], json_body={"requested_workspace_id": owner_workspace},
        )
        _expect_success(status, "durable state reload after relogin-equivalent request")
        durable = client.json(raw)
        if durable.get("loaded_from") != "storage_layer" or len(durable.get("facts", [])) != 1:
            raise AssertionError("durable fact truth was not reloaded from storage")
        if [plan["status"] for plan in durable.get("plans", [])] != ["active"]:
            raise AssertionError("durable plan lifecycle was not reloaded from storage")
        checks += 1
        snapshot = _snapshot(client, tokens[0], owner_workspace)
        forged = _command(
            "follow_up_create", f"stage10-api-forged-{marker}", snapshot["current_state_version"],
            {"task_id": str(uuid4()), "title": "Forbidden", "provenance_ids": ["fixture"]},
            {"kind": "validated_follow_up", "source_id": "fixture"},
        )
        status, _ = _commit(client, tokens[1], owner_workspace, forged)
        _expect_denied(status, "cross-workspace commit")
        checks += 1
        status, _ = client.request(
            "PATCH", f"/rest/v1/plans?id=eq.{quote(plan_id)}", key=client.anon_key,
            token=tokens[0], json_body={"status": "archived"},
        )
        _expect_denied(status, "direct authenticated plan write")
        checks += 1
        status, _ = client.request(
            "POST", "/rest/v1/rpc/stage10_commit", key=client.service_key,
            json_body={"requested_workspace_id": owner_workspace, "requested_command": forged},
        )
        _expect_denied(status, "ordinary service-role commit")
        checks += 1

        snapshot = _snapshot(client, tokens[0], owner_workspace)
        reminder = _command(
            "follow_up_create", f"stage10-api-reminder-{marker}", snapshot["current_state_version"],
            {"task_id": str(uuid4()), "title": "Prepare fictional questions", "due_at": _now(), "provenance_ids": ["question-fixture"], "reminder": {"opted_in": True, "scheduled_for": _now(), "timezone": "Asia/Kolkata", "channel": "email"}},
            {"kind": "validated_follow_up", "source_id": "stage7-follow-up"},
        )
        status, reminder_result = _commit(client, tokens[0], owner_workspace, reminder)
        _expect_success(status, "truthful unavailable reminder")
        if reminder_result["external_delivery_scheduled"]:
            raise AssertionError("external notification was falsely scheduled")
        checks += 1

        snapshot = _snapshot(client, tokens[0], owner_workspace)
        review_id = str(uuid4())
        review = _command(
            "review_create", f"stage10-api-review-{marker}", snapshot["current_state_version"],
            {"case_id": review_id, "reason": "urgent", "immediate_safety_completed": True, "safety_result": "urgent", "packet": {"question": "Fictional urgent handoff", "journey_state_id": journey_id, "confirmed_fact_ids": [], "user_reported_context_ids": ["symptom-fixture"], "exact_span_ids": [], "trace_reference": str(uuid4()), "unresolved_conflict_ids": [], "requested_action": "Simulated organizational review", "unrelated_personal_data_included": False}},
            {"kind": "safety_trace", "source_id": "stage6-urgent-trace"},
        )
        status, review_result = _commit(client, tokens[0], owner_workspace, review)
        _expect_success(status, "simulated review offer")
        if review_result["trace"]["generation_call_count"] != 0:
            raise AssertionError("urgent review path used generation")
        checks += 1

    finally:
        for workspace_id in workspace_ids:
            client.request("DELETE", f"/rest/v1/workspaces?id=eq.{quote(workspace_id)}", key=client.service_key)
        if created_release:
            client.request("DELETE", f"/rest/v1/guideline_chunks?release_id=eq.{quote(created_release)}", key=client.service_key)
            client.request("DELETE", f"/rest/v1/public_sources?release_id=eq.{quote(created_release)}", key=client.service_key)
            client.request("DELETE", f"/rest/v1/content_releases?id=eq.{quote(created_release)}", key=client.service_key)
        for user_id in user_ids:
            client.request("DELETE", f"/auth/v1/admin/users/{quote(user_id)}", key=client.service_key)

    print(json.dumps({
        "valid": True, "stage": 10, "checks": checks, "principals": 2,
        "product_calls_used_authenticated_jwt": True,
        "fixture_setup_used_local_service_key": True,
        "service_role_ordinary_commit_rejected": True,
        "external_delivery_performed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

