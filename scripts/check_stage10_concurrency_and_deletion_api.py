"""Database-connected Stage 10 concurrency, idempotency, and reset matrix.

All product mutations use authenticated user JWTs. The local service key is used
only to create and remove isolated fictional fixtures and to inspect cleanup.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from scripts.check_stage2_storage_api import LocalSupabase, _expect_denied, _expect_success
from scripts.check_stage10_state_api import _command, _commit, _now, _snapshot

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json"



def _create_user(client: LocalSupabase, email: str, password: str) -> tuple[str, str]:
    status, raw = client.request("POST", "/auth/v1/admin/users", key=client.service_key,
        json_body={"email": email, "password": password, "email_confirm": True})
    _expect_success(status, "temporary user creation")
    user_id = client.json(raw)["id"]
    status, raw = client.request("POST", "/auth/v1/token?grant_type=password", key=client.anon_key,
        json_body={"email": email, "password": password})
    _expect_success(status, "temporary user sign-in")
    return user_id, client.json(raw)["access_token"]


def _insert(client: LocalSupabase, table: str, value: dict) -> None:
    status, _ = client.request("POST", f"/rest/v1/{table}", key=client.service_key, json_body=value)
    _expect_success(status, f"{table} fixture")


def _create_workspace(client: LocalSupabase, token: str, label: str) -> str:
    status, raw = client.request("POST", "/rest/v1/rpc/create_workspace", key=client.anon_key,
        token=token, json_body={"requested_mode": "fictional_demo", "requested_display_name": label})
    _expect_success(status, "workspace creation")
    return client.json(raw)


def _plan_payload(plan_id: str, item_id: str, journey_id: str, release_id: str,
                  evidence_id: str, fact_id: str, material: str, marker: str) -> dict:
    return {
        "plan_id": plan_id,
        "journey_state_id": journey_id,
        "journey_week": 24,
        "source_release_id": release_id,
        "user_preferences": {"window": "morning"},
        "confirmed_constraints": [f"{material} allergy"],
        "component_agent_outputs": {"nutrition": "validated fictional fixture"},
        "source_evidence_ids": [evidence_id],
        "user_edits": [],
        "validation_disposition": "pass",
        "validation_trace_id": str(uuid4()),
        "unresolved_conflict_ids": [],
        "items": [{
            "item_id": item_id, "domain": "nutrition", "title": "Fictional breakfast",
            "body": f"Choose a validated {material}-free option.", "day": "monday",
            "time_window": "morning", "record_only": False, "evidence_ids": [evidence_id],
            "applied_constraint_ids": [fact_id], "material_keys": ["oats"],
            "excluded_material_keys": [material], "contributor": "nutrition-agent-v1",
        }],
        "dependencies": [
            {"kind": "journey_state", "entity_id": journey_id, "material_key": "pregnancy-week-24"},
            {"kind": "allergy", "entity_id": fact_id, "material_key": material, "source_item_id": item_id},
            {"kind": "evidence", "entity_id": evidence_id, "material_key": f"stage10-concurrency-{marker}", "source_item_id": item_id},
        ],
    }


def _plan_command(client: LocalSupabase, token: str, workspace: str, payload: dict, key: str) -> dict:
    return _command("plan_create", key, _snapshot(client, token, workspace)["current_state_version"],
        payload, {"kind": "validated_plan", "source_id": "stage8-concurrency-fixture",
                  "validation_policy_version": "stage8-validation-v1"})


def _transition(client: LocalSupabase, token: str, workspace: str, plan_id: str,
                from_state: str, to_state: str, key: str) -> tuple[int, dict | None]:
    command = _command("plan_transition", key,
        _snapshot(client, token, workspace)["current_state_version"],
        {"plan_id": plan_id, "from_status": from_state, "to_status": to_state},
        {"kind": "user_action", "source_id": "stage10-concurrency-ui"})
    return _commit(client, token, workspace, command)


def _concurrent(client: LocalSupabase, token: str, workspace: str,
                commands: list[dict]) -> list[tuple[int, dict | None]]:
    """Send independent authenticated HTTP requests at the same state version."""
    def send(command: dict) -> tuple[int, dict | None]:
        return _commit(client, token, workspace, command)

    with ThreadPoolExecutor(max_workers=len(commands)) as executor:
        futures = [executor.submit(send, command) for command in commands]
        return [future.result(timeout=30) for future in futures]


def _service_count(client: LocalSupabase, table: str, workspace: str) -> int:
    scope_column = "id" if table == "workspaces" else "workspace_id"
    status, raw = client.request("GET",
        f"/rest/v1/{table}?{scope_column}=eq.{quote(workspace)}&select=id",
        key=client.service_key)
    _expect_success(status, f"inspect {table}")
    return len(client.json(raw))


def main() -> int:
    client = LocalSupabase()
    marker = uuid4().hex
    password = f"Nestline-{uuid4().hex}-A1!"
    emails = [f"stage10-race-a-{marker}@example.invalid", f"stage10-race-b-{marker}@example.invalid"]
    users: list[str] = []
    workspaces: list[str] = []
    release_id: str | None = None
    checks = 0
    concurrency = {"plan_save": {}, "fact_vs_save": {}, "fact_vs_activate": {}}
    recreated_workspace: str | None = None
    try:
        principals = [_create_user(client, email, password) for email in emails]
        users = [item[0] for item in principals]
        tokens = [item[1] for item in principals]
        workspaces = [
            _create_workspace(client, tokens[0], f"Concurrency A {marker[:6]}"),
            _create_workspace(client, tokens[1], f"Concurrency B {marker[:6]}"),
        ]
        workspace_a, workspace_b = workspaces

        # Same idempotency key remains independent across authenticated workspaces.
        shared_key = f"stage10-shared-{marker}"
        shared_results = []
        for index, (token, workspace) in enumerate(zip(tokens, workspaces, strict=True)):
            command = _command("follow_up_create", shared_key, 1,
                {"task_id": str(uuid4()), "title": f"Fictional scoped task {index}",
                 "provenance_ids": [f"scope-{index}"]},
                {"kind": "validated_follow_up", "source_id": "stage10-scope-fixture"})
            status, result = _commit(client, token, workspace, command)
            _expect_success(status, "scoped idempotency commit")
            if result["status"] != "committed":
                raise AssertionError("same key crossed workspace scope")
            shared_results.append((command, result))
        checks += 2
        status, replay = _commit(client, tokens[0], workspace_a, shared_results[0][0])
        _expect_success(status, "response-loss replay")
        if replay["status"] != "replayed":
            raise AssertionError("response-loss retry did not replay")
        checks += 1
        conflicting = json.loads(json.dumps(shared_results[0][0]))
        conflicting["payload"]["title"] = "Different payload"
        status, _ = _commit(client, tokens[0], workspace_a, conflicting)
        _expect_denied(status, "same key different payload")
        checks += 1

        release_id = str(uuid4())
        source_id = f"SRC-S10-RACE-{marker[:10]}"
        evidence_id = f"EVID-S10-RACE-{marker[:10]}"
        _insert(client, "content_releases", {"id": release_id,
            "corpus_version": f"stage10-race-{marker}", "release_fingerprint": sha256(marker.encode()).hexdigest(),
            "status": "published", "published_at": _now()})
        _insert(client, "public_sources", {"source_id": source_id, "release_id": release_id,
            "title": "Stage 10 concurrency fixture", "publisher": "Nestline tests",
            "canonical_url": "https://example.invalid/stage10-concurrency", "jurisdiction": ["GLOBAL"],
            "source_version": "1", "reuse_status": "permitted", "allowed_use": ["testing"],
            "status": "published", "content_checksum": "2" * 64})
        _insert(client, "guideline_chunks", {"chunk_id": f"CHUNK-S10-RACE-{marker[:10]}",
            "release_id": release_id, "evidence_id": evidence_id, "source_id": source_id,
            "candidate_checksum": "3" * 64, "text": "Controlled fictional evidence.",
            "source_block_ids": ["BLOCK-S10-RACE"], "stage": "pregnancy", "unit": "week",
            "range_start": 24, "range_end": 24, "jurisdiction": ["GLOBAL"],
            "domains": ["nutrition"], "display_slots": ["plan"], "status": "published"})
        journey_id, document_id = str(uuid4()), str(uuid4())
        _insert(client, "journey_states", {"id": journey_id, "workspace_id": workspace_a,
            "stage": "pregnancy", "timing_source": "manual_week_day", "gestational_week": 24,
            "gestational_day": 2, "user_confirmed": True, "version": 1,
            "confirmed_at": _now(), "confirmed_by_user_id": users[0],
            "effective_date": datetime.now(UTC).date().isoformat(),
            "calculation_date": datetime.now(UTC).date().isoformat()})
        _insert(client, "private_documents", {"id": document_id, "workspace_id": workspace_a,
            "storage_object_path": f"{workspace_a}/stage10/DOC-001.pdf", "original_filename": "DOC-001.pdf",
            "media_type": "application/pdf", "byte_size": 100, "sha256": "a" * 64,
            "status": "needs_confirmation", "contains_real_medical_data": False,
            "fixture_document_key": "DOC-001", "scan_status": "fixture_verified",
            "scan_provider": "api-concurrency", "scan_version": "v1", "scan_completed_at": _now(),
            "review_version": 1})

        def add_candidate(text: str, label: str) -> str:
            candidate_id = str(uuid4())
            _insert(client, "document_facts", {"id": candidate_id, "workspace_id": workspace_a,
                "document_id": document_id, "field_name": "allergy", "value": {"label": label},
                "source_page": 1, "source_text": text, "confidence": 1.0, "status": "proposed",
                "candidate_key": f"candidate-{uuid4().hex}", "fact_type": "allergy",
                "source_span": {"page": 1, "exact_text": text, "start": 0, "end": len(text)},
                "completeness": "complete", "disposition": "extract_verbatim", "record_only": False,
                "source_value_matches": True})
            return candidate_id

        def fact_provenance(candidate_id: str, text: str) -> dict:
            from hashlib import sha256
            return {"kind": "document_candidate", "source_id": f"candidate:{candidate_id}",
                "source_document_id": document_id, "source_document_fact_id": candidate_id,
                "source_page": 1, "exact_span": text,
                "exact_span_sha256": sha256(text.encode()).hexdigest()}

        first_text = "allergy: sesame"
        first_candidate = add_candidate(first_text, "sesame")
        first_command = _command("fact_decision", f"stage10-first-fact-{marker}",
            _snapshot(client, tokens[0], workspace_a)["current_state_version"],
            {"document_fact_id": first_candidate, "decision": "confirm", "material_dependency_key": "sesame"},
            fact_provenance(first_candidate, first_text))
        status, first_result = _commit(client, tokens[0], workspace_a, first_command)
        _expect_success(status, "initial confirmed allergy")
        fact_id = first_result["entity_ids"][-1]
        checks += 1

        # Two simultaneous saves at the same expected version: exactly one commits.
        plan1, item1 = str(uuid4()), str(uuid4())
        status, _ = _commit(client, tokens[0], workspace_a,
            _plan_command(client, tokens[0], workspace_a,
                _plan_payload(plan1, item1, journey_id, release_id, evidence_id, fact_id, "sesame", marker),
                f"stage10-race-plan1-{marker}"))
        _expect_success(status, "race plan create")
        _expect_success(_transition(client, tokens[0], workspace_a, plan1, "draft", "user_reviewed",
            f"stage10-race-plan1-review-{marker}")[0], "race plan review")
        version = _snapshot(client, tokens[0], workspace_a)["current_state_version"]
        save_commands = [_command("plan_transition", f"stage10-save-race-{index}-{marker}", version,
            {"plan_id": plan1, "from_status": "user_reviewed", "to_status": "saved"},
            {"kind": "user_action", "source_id": "stage10-race-ui"}) for index in range(2)]
        save_results = _concurrent(client, tokens[0], workspace_a, save_commands)
        committed_save = [index for index, (status, _) in enumerate(save_results) if 200 <= status < 300]
        if len(committed_save) != 1:
            raise AssertionError(f"expected one concurrent save, got {len(committed_save)}")
        concurrency["plan_save"] = {"attempts": 2, "committed": 1, "rejected": 1}
        checks += 2
        winner = committed_save[0]
        status, replay = _commit(client, tokens[0], workspace_a, save_commands[winner])
        _expect_success(status, "lost-response plan save replay")
        if replay["status"] != "replayed" or _service_count(client, "plans", workspace_a) != 1:
            raise AssertionError("plan response-loss retry duplicated state")
        checks += 1

        # Fact correction racing with plan save cannot bypass a changed constraint.
        plan2, item2 = str(uuid4()), str(uuid4())
        status, _ = _commit(client, tokens[0], workspace_a,
            _plan_command(client, tokens[0], workspace_a,
                _plan_payload(plan2, item2, journey_id, release_id, evidence_id, fact_id, "sesame", marker),
                f"stage10-race-plan2-{marker}"))
        _expect_success(status, "fact/save race plan create")
        _expect_success(_transition(client, tokens[0], workspace_a, plan2, "draft", "user_reviewed",
            f"stage10-race-plan2-review-{marker}")[0], "fact/save race plan review")
        second_text = "allergy update: sesame"
        second_candidate = add_candidate(second_text, "sesame")
        version = _snapshot(client, tokens[0], workspace_a)["current_state_version"]
        save2 = _command("plan_transition", f"stage10-fact-save-race-save-{marker}", version,
            {"plan_id": plan2, "from_status": "user_reviewed", "to_status": "saved"},
            {"kind": "user_action", "source_id": "stage10-race-ui"})
        correct2 = _command("fact_decision", f"stage10-fact-save-race-fact-{marker}", version,
            {"document_fact_id": second_candidate, "decision": "correct",
             "corrected_value": {"label": "tahini"}, "supersedes_health_fact_id": fact_id,
             "material_dependency_key": "tahini"}, fact_provenance(second_candidate, second_text))
        race2 = _concurrent(client, tokens[0], workspace_a, [save2, correct2])
        committed2 = [index for index, (status, _) in enumerate(race2) if 200 <= status < 300]
        if len(committed2) != 1:
            raise AssertionError("fact/save race did not serialize to one commit")
        durable = client.json(client.request("POST", "/rest/v1/rpc/stage10_durable_state",
            key=client.anon_key, token=tokens[0], json_body={"requested_workspace_id": workspace_a})[1])
        plan2_state = next(plan["status"] for plan in durable["plans"] if plan["plan_id"] == plan2)
        if committed2[0] == 1 and plan2_state != "stale":
            raise AssertionError("committed fact correction did not stale the raced plan")
        if committed2[0] == 0 and plan2_state != "saved":
            raise AssertionError("saved plan race produced an unexpected lifecycle state")
        concurrency["fact_vs_save"] = {"attempts": 2, "committed": 1, "rejected": 1,
            "winner": "fact" if committed2[0] == 1 else "save"}
        checks += 2
        if committed2[0] == 0:
            # The failed correction can be submitted only as a fresh, current-version command.
            correct2 = _command("fact_decision", f"stage10-fact-save-race-fact-retry-{marker}",
                _snapshot(client, tokens[0], workspace_a)["current_state_version"],
                {"document_fact_id": second_candidate, "decision": "correct",
                 "corrected_value": {"label": "tahini"}, "supersedes_health_fact_id": fact_id,
                 "material_dependency_key": "tahini"}, fact_provenance(second_candidate, second_text))
            status, result2 = _commit(client, tokens[0], workspace_a, correct2)
            _expect_success(status, "fresh correction after serialized save")
        else:
            result2 = race2[1][1]
        current_fact = result2["entity_ids"][-1]

        # Relevant correction racing with activation: no changed-constraint plan becomes active.
        plan3, item3 = str(uuid4()), str(uuid4())
        status, _ = _commit(client, tokens[0], workspace_a,
            _plan_command(client, tokens[0], workspace_a,
                _plan_payload(plan3, item3, journey_id, release_id, evidence_id, current_fact, "tahini", marker),
                f"stage10-race-plan3-{marker}"))
        _expect_success(status, "fact/activate race plan create")
        for before, after in (("draft", "user_reviewed"), ("user_reviewed", "saved")):
            _expect_success(_transition(client, tokens[0], workspace_a, plan3, before, after,
                f"stage10-race-plan3-{after}-{marker}")[0], f"plan3 transition {after}")
        third_text = "allergy update: tahini"
        third_candidate = add_candidate(third_text, "tahini")
        version = _snapshot(client, tokens[0], workspace_a)["current_state_version"]
        activate3 = _command("plan_transition", f"stage10-fact-activate-race-activate-{marker}", version,
            {"plan_id": plan3, "from_status": "saved", "to_status": "active"},
            {"kind": "user_action", "source_id": "stage10-race-ui"})
        correct3 = _command("fact_decision", f"stage10-fact-activate-race-fact-{marker}", version,
            {"document_fact_id": third_candidate, "decision": "correct",
             "corrected_value": {"label": "peanut"}, "supersedes_health_fact_id": current_fact,
             "material_dependency_key": "peanut"}, fact_provenance(third_candidate, third_text))
        race3 = _concurrent(client, tokens[0], workspace_a, [activate3, correct3])
        committed3 = [index for index, (status, _) in enumerate(race3) if 200 <= status < 300]
        if len(committed3) != 1:
            raise AssertionError("fact/activation race did not serialize to one commit")
        durable = client.json(client.request("POST", "/rest/v1/rpc/stage10_durable_state",
            key=client.anon_key, token=tokens[0], json_body={"requested_workspace_id": workspace_a})[1])
        plan3_state = next(plan["status"] for plan in durable["plans"] if plan["plan_id"] == plan3)
        if committed3[0] == 1 and plan3_state != "stale":
            raise AssertionError("changed-constraint plan became active")
        if committed3[0] == 0 and plan3_state != "active":
            raise AssertionError("activation winner did not preserve unchanged constraint state")
        concurrency["fact_vs_activate"] = {"attempts": 2, "committed": 1, "rejected": 1,
            "winner": "fact" if committed3[0] == 1 else "activate"}
        checks += 2

        # A stale/failed operation cannot later replay as a committed result.
        stale = _command("follow_up_create", f"stage10-stale-key-{marker}", 1,
            {"task_id": str(uuid4()), "title": "Stale action", "provenance_ids": ["stale"]},
            {"kind": "validated_follow_up", "source_id": "stage10-stale-fixture"})
        status1, _ = _commit(client, tokens[0], workspace_a, stale)
        status2, _ = _commit(client, tokens[0], workspace_a, stale)
        if 200 <= status1 < 300 or 200 <= status2 < 300:
            raise AssertionError("stale failed operation replayed as committed")
        checks += 2

        # Delete/reset A, prove B survives, then recreate A and reuse the old key without replay.
        b_before = _service_count(client, "follow_up_tasks", workspace_b)
        status, _ = client.request("DELETE", f"/rest/v1/workspaces?id=eq.{quote(workspace_a)}",
            key=client.anon_key, token=tokens[0])
        _expect_success(status, "owner workspace reset")
        for table in ("workspaces", "health_facts", "plans", "plan_items", "follow_up_tasks",
                      "human_review_cases", "graph_nodes", "graph_edges", "private_documents", "document_facts"):
            if _service_count(client, table, workspace_a) != 0:
                raise AssertionError(f"workspace reset left {table} artifacts")
        if _service_count(client, "follow_up_tasks", workspace_b) != b_before:
            raise AssertionError("workspace A reset changed workspace B")
        checks += 11
        workspaces.remove(workspace_a)
        recreated_workspace = _create_workspace(client, tokens[0], f"Recreated A {marker[:6]}")
        workspaces.append(recreated_workspace)
        new_command = _command("follow_up_create", shared_key, 1,
            {"task_id": str(uuid4()), "title": "Fresh recreated workspace action",
             "provenance_ids": ["fresh-workspace"]},
            {"kind": "validated_follow_up", "source_id": "stage10-reset-fixture"})
        status, result = _commit(client, tokens[0], recreated_workspace, new_command)
        _expect_success(status, "recreated workspace action")
        if result["status"] != "committed":
            raise AssertionError("old idempotency result replayed into recreated workspace")
        checks += 1

    finally:
        for workspace in list(workspaces):
            client.request("DELETE", f"/rest/v1/workspaces?id=eq.{quote(workspace)}", key=client.service_key)
        if release_id:
            client.request("DELETE", f"/rest/v1/guideline_chunks?release_id=eq.{quote(release_id)}", key=client.service_key)
            client.request("DELETE", f"/rest/v1/public_sources?release_id=eq.{quote(release_id)}", key=client.service_key)
            client.request("DELETE", f"/rest/v1/content_releases?id=eq.{quote(release_id)}", key=client.service_key)
        for user_id in users:
            client.request("DELETE", f"/auth/v1/admin/users/{quote(user_id)}", key=client.service_key)

    result = {
        "valid": True, "stage": 10, "checks": checks, "principals": 2,
        "concurrency": concurrency, "same_key_cross_workspace_isolated": True,
        "response_loss_replay": True, "workspace_reset_public_tables_checked": 10,
        "old_idempotency_replay_after_reset": False, "fixture_cleanup_requested": True,
        "product_calls_used_authenticated_jwt": True,
        "concurrency_transport": "simultaneous_authenticated_http_rpc_requests",
        "http_api_matrix_verified_separately": True, "external_actions": 0,
    }
    REPORT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
