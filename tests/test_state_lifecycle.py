from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import unittest
from unittest.mock import patch
from urllib.error import URLError
from uuid import UUID

from pydantic import ValidationError

from app.schemas.state_lifecycle import (
    CommitStatus, FactDecision, FactDecisionPayload, FollowUpCreatePayload, PlanCreatePayload,
    RejectionCode, ReviewCreatePayload, StateCommitCommand,
)
from app.services.state_committer import SupabaseStateCommitterClient
from scripts.stage10_fixture_support import (
    CANDIDATE_ALLERGY, CANDIDATE_CONFLICT, CANDIDATE_UNRELATED, DOCUMENT_A,
    JOURNEY_A, OWNER_B, WORKSPACE_A, confirmation, document_provenance, fact_command, fixture_committer,
    follow_up_command, plan_create_command, plan_transition_command,
    review_create_command, review_transition_command, scope,
)


class StateCommitterTests(unittest.TestCase):
    def test_supabase_snapshot_network_failure_is_recoverable(self):
        client = SupabaseStateCommitterClient("https://unavailable.example.invalid", "publishable", "user-token")
        with patch("app.services.state_committer.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "temporarily unavailable"):
                client.load_snapshot(WORKSPACE_A)

    def test_chat_or_agent_cannot_form_direct_write(self):
        command = fact_command()
        raw = command.model_dump(mode="json")
        raw["caller"] = "nutrition_agent"
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_workspace_and_owner_are_not_command_fields(self):
        raw = fact_command().model_dump(mode="json")
        raw["workspace_id"] = str(WORKSPACE_A)
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_cross_workspace_owner_is_rejected_without_write(self):
        service = fixture_committer()
        result = service.commit(scope(owner=OWNER_B), fact_command())
        self.assertEqual(result.status, CommitStatus.REJECTED)
        self.assertEqual(result.rejection_code, RejectionCode.UNAUTHORIZED)
        self.assertEqual(service.load_snapshot(scope()).state_version, 1)

    def test_confirm_fact_requires_exact_source_provenance(self):
        service = fixture_committer()
        command = fact_command()
        command.provenance.exact_span = "altered span"
        result = service.commit(scope(), command)
        self.assertEqual(result.rejection_code, RejectionCode.UNSUPPORTED_PROVENANCE)
        self.assertEqual(service.load_snapshot(scope()).facts, [])

    def test_confirmed_fact_personalizes_only_after_commit(self):
        service = fixture_committer()
        self.assertEqual(service.load_snapshot(scope()).facts, [])
        result = service.commit(scope(), fact_command())
        self.assertEqual(result.status, CommitStatus.COMMITTED)
        snapshot = service.load_snapshot(scope(version=2))
        self.assertEqual(len(snapshot.facts), 1)
        self.assertEqual(snapshot.facts[0]["status"], "confirmed")

    def test_correction_preserves_candidate_and_corrected_value(self):
        service = fixture_committer()
        result = service.commit(
            scope(), fact_command(decision="correct", key="fact-correct-0001"),
        )
        self.assertEqual(result.status, CommitStatus.COMMITTED)
        self.assertEqual(service.load_snapshot(scope(version=2)).facts[0]["value"]["label"], "sesame seeds")

    def test_rejection_never_personalizes(self):
        service = fixture_committer()
        result = service.commit(
            scope(), fact_command(decision="reject", key="fact-reject-00001"),
        )
        self.assertEqual(result.status, CommitStatus.COMMITTED)
        self.assertEqual(service.load_snapshot(scope(version=2)).facts, [])

    def test_unresolved_conflict_cannot_be_confirmed(self):
        service = fixture_committer()
        result = service.commit(
            scope(), fact_command(CANDIDATE_CONFLICT, key="conflict-confirm-01"),
        )
        self.assertEqual(result.rejection_code, RejectionCode.UNRESOLVED_CONFLICT)

    def test_atomic_rollback_on_invalid_plan_transition(self):
        service = fixture_committer()
        created = service.commit(scope(), plan_create_command())
        plan_id = created.entity_ids[0]
        invalid = plan_transition_command(
            plan_id, 2, "draft", "saved", key="plan-invalid-save-1",
        )
        result = service.commit(scope(version=2), invalid)
        self.assertEqual(result.rejection_code, RejectionCode.INVALID_TRANSITION)
        snapshot = service.load_snapshot(scope(version=2))
        self.assertEqual(snapshot.plans[0]["status"], "draft")
        self.assertEqual(snapshot.state_version, 2)

    def test_full_plan_review_save_activate_lifecycle(self):
        service = fixture_committer()
        created = service.commit(scope(), plan_create_command())
        plan_id = created.entity_ids[0]
        reviewed = service.commit(scope(version=2), plan_transition_command(
            plan_id, 2, "draft", "user_reviewed", key="plan-reviewed-0001",
        ))
        saved = service.commit(scope(version=3), plan_transition_command(
            plan_id, 3, "user_reviewed", "saved", key="plan-saved-0000001",
        ))
        active = service.commit(scope(version=4), plan_transition_command(
            plan_id, 4, "saved", "active", key="plan-active-000001",
        ))
        self.assertEqual([reviewed.status, saved.status, active.status], [CommitStatus.COMMITTED] * 3)
        plan = service.load_snapshot(scope(version=5)).plans[0]
        self.assertEqual(plan["status"], "active")
        self.assertIsNotNone(plan["reviewed_at"])
        self.assertIsNotNone(plan["saved_at"])

    def test_stale_plan_cannot_be_saved(self):
        service = fixture_committer()
        plan_id = service.commit(scope(), plan_create_command()).entity_ids[0]
        stale = service.commit(scope(version=2), fact_command(version=2, key="fact-stale-plan-01"))
        self.assertEqual(stale.affected_plan_ids, [plan_id])
        attempt = service.commit(scope(version=3), plan_transition_command(
            plan_id, 3, "stale", "saved", key="stale-plan-save-01",
        ))
        self.assertEqual(attempt.rejection_code, RejectionCode.INVALID_TRANSITION)

    def test_relevant_fact_stales_only_matching_plan(self):
        service = fixture_committer()
        matching = service.commit(scope(), plan_create_command()).entity_ids[0]
        other = service.commit(scope(version=2), plan_create_command(
            version=2, key="plan-create-other1", material_key="peanut",
        )).entity_ids[0]
        result = service.commit(scope(version=3), fact_command(version=3, key="fact-selective-0001"))
        self.assertEqual(result.affected_plan_ids, [matching])
        plans = {item["id"]: item for item in service.load_snapshot(scope(version=4)).plans}
        self.assertEqual(plans[str(matching)]["status"], "stale")
        self.assertEqual(plans[str(other)]["status"], "draft")

    def test_unrelated_fact_does_not_stale_plan(self):
        service = fixture_committer()
        plan_id = service.commit(scope(), plan_create_command()).entity_ids[0]
        result = service.commit(scope(version=2), fact_command(
            CANDIDATE_UNRELATED, version=2, key="fact-unrelated-0001",
        ))
        self.assertEqual(result.affected_plan_ids, [])
        self.assertEqual(service.load_snapshot(scope(version=3)).plans[0]["status"], "draft")

    def test_stale_concurrent_write_returns_current_version(self):
        service = fixture_committer()
        service.commit(scope(), fact_command())
        stale = service.commit(scope(), plan_create_command(key="stale-concurrent-1"))
        self.assertEqual(stale.status, CommitStatus.STALE)
        self.assertEqual(stale.rejection_code, RejectionCode.STALE_STATE_VERSION)
        self.assertEqual(stale.current_state["state_version"], 2)

    def test_idempotent_retry_does_not_duplicate_fact(self):
        service = fixture_committer()
        command = fact_command()
        first = service.commit(scope(), command)
        second = service.commit(scope(version=2), command)
        self.assertEqual(first.status, CommitStatus.COMMITTED)
        self.assertEqual(second.status, CommitStatus.REPLAYED)
        snapshot = service.load_snapshot(scope(version=2))
        self.assertEqual(len(snapshot.facts), 1)
        self.assertEqual(snapshot.state_version, 2)

    def test_idempotency_key_cannot_represent_different_payload(self):
        service = fixture_committer()
        service.commit(scope(), fact_command())
        changed = fact_command(CANDIDATE_UNRELATED, version=2, key="fact-confirm-0001")
        result = service.commit(scope(version=2), changed)
        self.assertEqual(result.rejection_code, RejectionCode.IDEMPOTENCY_CONFLICT)

    def test_external_reminder_is_truthfully_unavailable(self):
        service = fixture_committer()
        result = service.commit(scope(), follow_up_command(1, channel="email"))
        self.assertFalse(result.external_delivery_scheduled)
        task = service.load_snapshot(scope(version=2)).follow_up_tasks[0]
        self.assertEqual(task["reminder_state"], "external_delivery_unavailable")
        self.assertFalse(task["external_delivery_scheduled"])

    def test_in_app_follow_up_has_exact_consent_metadata(self):
        service = fixture_committer()
        service.commit(scope(), follow_up_command(1))
        task = service.load_snapshot(scope(version=2)).follow_up_tasks[0]
        self.assertEqual(task["reminder"]["timezone"], "Asia/Kolkata")
        self.assertEqual(task["reminder"]["channel"], "in_app")

    def test_reminder_without_exact_fields_fails_schema(self):
        raw = follow_up_command(1).model_dump(mode="json")
        del raw["payload"]["reminder"]["timezone"]
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_simulated_review_packet_is_minimized_and_truthful(self):
        service = fixture_committer()
        result = service.commit(scope(), review_create_command(1))
        case = service.load_snapshot(scope(version=2)).simulated_review_cases[0]
        self.assertEqual(case["label"], "Simulated review")
        self.assertFalse(case["packet"]["unrelated_personal_data_included"])
        self.assertEqual(result.trace.generation_call_count, 0)

    def test_urgent_review_occurs_after_zero_generation_safety(self):
        service = fixture_committer()
        service.commit(scope(), review_create_command(1, urgent=True))
        case = service.load_snapshot(scope(version=2)).simulated_review_cases[0]
        self.assertTrue(case["immediate_safety_completed"])
        self.assertEqual(case["urgent_generation_call_count"], 0)

    def test_review_requires_consent_before_queue(self):
        service = fixture_committer()
        created = service.commit(scope(), review_create_command(1))
        case_id = created.entity_ids[0]
        invalid = service.commit(scope(version=2), review_transition_command(
            case_id, 2, "offered", "queued", key="review-bypass-consent",
        ))
        self.assertEqual(invalid.rejection_code, RejectionCode.INVALID_TRANSITION)

    def test_review_valid_state_machine_and_simulated_response(self):
        service = fixture_committer()
        case_id = service.commit(scope(), review_create_command(1)).entity_ids[0]
        service.commit(scope(version=2), review_transition_command(
            case_id, 2, "offered", "consented", key="review-consented-1",
        ))
        service.commit(scope(version=3), review_transition_command(
            case_id, 3, "consented", "queued", key="review-queued-00001",
        ))
        reviewed = service.commit(scope(version=4), review_transition_command(
            case_id, 4, "queued", "reviewed", key="review-reviewed-001",
            response="Simulated response: prepare these questions.",
        ))
        case = service.load_snapshot(scope(version=5)).simulated_review_cases[0]
        self.assertEqual(reviewed.status, CommitStatus.COMMITTED)
        self.assertEqual(case["response_label"], "Simulated response")

    def test_review_cannot_include_unrelated_personal_data_flag(self):
        raw = review_create_command(1).model_dump(mode="json")
        raw["payload"]["packet"]["unrelated_personal_data_included"] = True
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_plan_item_medication_language_requires_record_only(self):
        raw = plan_create_command().model_dump(mode="json")
        raw["payload"]["items"][0]["body"] = "Change medication timing."
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_user_edited_allergen_item_is_rejected_before_save(self):
        service = fixture_committer()
        service.commit(scope(), fact_command())
        command = plan_create_command(version=2, key="plan-allergen-bad1")
        command.payload.items[0].material_keys = ["sesame"]
        command.payload.items[0].excluded_material_keys = []
        result = service.commit(scope(version=2), command)
        self.assertEqual(result.rejection_code, RejectionCode.VALIDATION_FAILED)
        self.assertEqual(service.load_snapshot(scope(version=2)).plans, [])

    def test_user_edited_allergen_exclusion_remains_save_eligible(self):
        service = fixture_committer()
        service.commit(scope(), fact_command())
        command = plan_create_command(version=2, key="plan-allergen-safe1")
        command.payload.items[0].material_keys = ["oats"]
        command.payload.items[0].excluded_material_keys = ["sesame"]
        result = service.commit(scope(version=2), command)
        self.assertEqual(result.status, CommitStatus.COMMITTED)
    def test_generated_plan_cannot_claim_failed_validation(self):
        raw = plan_create_command().model_dump(mode="json")
        raw["payload"]["validation_disposition"] = "fail"
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_rejected_write_has_redacted_audit(self):
        service = fixture_committer()
        result = service.commit(scope(version=99), fact_command(version=99))
        self.assertFalse(result.trace.raw_personal_text_logged)
        self.assertFalse(result.trace.service_role_used)
        self.assertFalse(result.trace.direct_agent_write)
        self.assertEqual(result.trace.generation_call_count, 0)


    def test_active_confirmed_constraint_dependency_cannot_be_omitted(self):
        service = fixture_committer()
        service.commit(scope(), fact_command())
        command = plan_create_command(version=2, key="plan-missing-dependency-1")
        command.payload.dependencies = [
            item for item in command.payload.dependencies if item.kind.value != "allergy"
        ]
        result = service.commit(scope(version=2), command)
        self.assertEqual(result.rejection_code, RejectionCode.MISSING_DEPENDENCY)
        self.assertEqual(service.load_snapshot(scope(version=2)).plans, [])

    def test_user_edit_must_match_persisted_validated_item(self):
        raw = plan_create_command(edited=True).model_dump(mode="json")
        raw["payload"]["items"][0]["time_window"] = "morning"
        with self.assertRaises(ValidationError):
            StateCommitCommand.model_validate(raw)

    def test_correction_supersession_invalidates_old_material_dependency(self):
        service = fixture_committer()
        first = service.commit(scope(), fact_command())
        prior_fact_id = first.entity_ids[-1]
        plan = service.commit(
            scope(version=2), plan_create_command(version=2, key="plan-before-correction-1"),
        )
        candidate_id = UUID("50000000-0000-0000-0000-000000000004")
        span = "allergy correction: tahini"
        service.seed_document_candidate(
            WORKSPACE_A, candidate_id, fact_type="allergy", value={"label": "sesame"},
            document_id=DOCUMENT_A, page=3, exact_span=span, material_key="tahini",
        )
        command = StateCommitCommand(
            idempotency_key="fact-correction-supersede-1", expected_state_version=3,
            submitted_at=fact_command().submitted_at,
            provenance=document_provenance(candidate_id, 3, span),
            confirmation=confirmation("correct-and-supersede"),
            payload=FactDecisionPayload(
                document_fact_id=candidate_id, decision=FactDecision.CORRECT,
                corrected_value={"label": "tahini"}, supersedes_health_fact_id=prior_fact_id,
                material_dependency_key="tahini",
            ),
        )
        result = service.commit(scope(version=3), command)
        self.assertEqual(result.status, CommitStatus.COMMITTED)
        self.assertEqual(result.affected_plan_ids, plan.entity_ids)
        facts = service.load_snapshot(scope(version=4)).facts
        self.assertEqual({item["status"] for item in facts}, {"confirmed", "superseded"})

if __name__ == "__main__":
    unittest.main()




