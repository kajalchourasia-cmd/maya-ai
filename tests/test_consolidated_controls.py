"""Cross-stage controls added by the consolidated non-UI improvement pass."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from app.schemas.retrieval import (
    AuthenticatedRetrievalScope,
    ExactPersonalContext,
    JourneyStateSnapshot,
)
from app.services.configuration import ApplicationMode, validate_configuration
from app.services.confirmed_context import ConfirmedContextService
from app.services.corpus_lifecycle import IndexedEvidence, VersionedCorpusIndexStore
from app.services.ingestion_recovery import SourceRecoveryStore
from app.services.redaction import (
    audit_trace_metadata,
    provider_trace_metadata,
    redact_for_trace,
    redact_text,
)
from app.services.state_committer import InMemoryStateCommitter
from app.services.state_service import ModeSafeStateService
from scripts.build_stage9_immutability_manifest import stable_sha256
from scripts.stage10_fixture_support import (
    OWNER_A,
    WORKSPACE_A,
    WORKSPACE_B,
    fact_command,
    fixture_committer,
    scope,
)

NOW = datetime(2026, 9, 12, 9, 0, tzinfo=timezone.utc)


class ConfigurationAndRedactionTests(unittest.TestCase):
    def test_demo_needs_no_paid_credentials(self):
        report = validate_configuration({}, mode=ApplicationMode.DEMO)
        self.assertTrue(report.valid)
        self.assertTrue(report.fixture_provider_permitted)
        self.assertEqual(report.generation.status, "disabled")

    def test_personal_mode_fails_closed_without_live_provider(self):
        report = validate_configuration(
            {
                "NESTLINE_SUPABASE_URL": "https://fixture.invalid",
                "NESTLINE_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture",
            },
            mode=ApplicationMode.PERSONAL,
        )
        self.assertFalse(report.valid)
        self.assertIn("provider", " ".join(report.errors).casefold())

    def test_personal_mode_accepts_explicit_non_fixture_provider(self):
        report = validate_configuration(
            {
                "NESTLINE_SUPABASE_URL": "https://fixture.invalid",
                "NESTLINE_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture",
                "NESTLINE_ENABLE_LIVE_PROVIDER": "true",
                "NESTLINE_GENERATION_PROVIDER": "configured-http",
                "NESTLINE_GENERATION_MODEL": "fictional-model-id",
                "NESTLINE_LIVE_PROVIDER_AUTHORIZATION_REFERENCE": "approval-fixture",
                "NESTLINE_GENERATION_MAX_COST_USD": "0.10",
            },
            mode=ApplicationMode.PERSONAL,
        )
        self.assertTrue(report.valid)
        self.assertFalse(report.fixture_provider_permitted)
        self.assertEqual(report.generation.status, "ready")

    def test_real_uploads_fail_closed_without_scanner(self):
        report = validate_configuration(
            {"NESTLINE_ENABLE_REAL_UPLOADS": "true"},
            mode=ApplicationMode.DEMO,
        )
        self.assertFalse(report.valid)
        self.assertEqual(report.scanner.status, "blocked")

    def test_provider_and_audit_trace_envelopes_are_redacted(self):
        request = {
            "input": [{"text": "fictional chest pain"}],
            "authorization": "Bearer FICTIONAL.JWT.TOKEN",
            "workspace_id": "workspace-fixture-a",
        }
        provider = provider_trace_metadata(
            provider="xai", model="grok-fixture",
            request=request,
            error="failed for fake.person@example.com with sk-FICTIONAL123456789",
        )
        audit = audit_trace_metadata({
            "owner_user_id": "owner-fixture-a",
            "medication": "fictional tablet",
            "action": "rejected",
        })
        rendered = repr((provider, audit))
        for forbidden in (
            "fictional chest pain", "FICTIONAL.JWT.TOKEN", "workspace-fixture-a",
            "fake.person@example.com", "sk-FICTIONAL", "owner-fixture-a",
            "fictional tablet",
        ):
            self.assertNotIn(forbidden, rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertEqual(provider["provider"], "xai")
        self.assertEqual(audit["action"], "rejected")

    def test_redaction_removes_credentials_identifiers_and_medical_text(self):
        raw = {
            "workspace_id": "workspace-fixture-a",
            "owner_user_id": "owner-fixture-a",
            "api_key": "sk-FICTIONAL123456789",
            "authorization": "Bearer FICTIONAL.JWT.TOKEN",
            "symptoms": ["fictional chest pain"],
            "medication": "fictional tablet",
            "error": "contact fake.person@example.com xai-FICTIONAL123456",
        }
        redacted = redact_for_trace(raw)
        rendered = repr(redacted)
        for forbidden in (
            "workspace-fixture-a",
            "owner-fixture-a",
            "sk-FICTIONAL",
            "xai-FICTIONAL",
            "fictional chest pain",
            "fictional tablet",
            "fake.person@example.com",
        ):
            self.assertNotIn(forbidden, rendered)
        self.assertIn("redacted:", rendered)
        self.assertEqual(
            redact_text("Bearer abcdefghijklmnopqrstuv"),
            "[REDACTED_CREDENTIAL]",
        )


class ConfirmedContextTests(unittest.TestCase):
    def _scope(self):
        owner = UUID("11111111-1111-4111-8111-111111111111")
        workspace = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        return AuthenticatedRetrievalScope(
            workspace_id=workspace,
            care_episode_id=workspace,
            owner_user_id=owner,
            session_subject=owner,
            state_version=7,
            authenticated_at=NOW,
        )

    def _journey(self, *, confirmed=True, conflict=False, week=24):
        return JourneyStateSnapshot(
            state_id=UUID("33333333-3333-4333-8333-333333333333"),
            stage="pregnancy",
            timing_source="confirmed_due_date",
            gestational_week=week,
            user_confirmed=confirmed,
            has_dating_conflict=conflict,
            version=7,
        )

    def test_confirmed_journey_personalizes_and_is_reproducible(self):
        exact = ExactPersonalContext(journey_state=self._journey())
        first = ConfirmedContextService.from_retrieval(self._scope(), exact)
        relogin = ConfirmedContextService.from_retrieval(self._scope(), exact)
        self.assertEqual(first, relogin)
        self.assertTrue(first.personalization_permitted)
        self.assertEqual(first.journey.exact, 24)
        self.assertEqual(first.state_version, 7)

    def test_unconfirmed_or_conflicting_journey_cannot_personalize(self):
        for journey, expected in (
            (self._journey(confirmed=False), "unconfirmed"),
            (self._journey(conflict=True), "conflicting"),
        ):
            with self.subTest(expected=expected):
                result = ConfirmedContextService.from_retrieval(
                    self._scope(), ExactPersonalContext(journey_state=journey)
                )
                self.assertFalse(result.personalization_permitted)
                self.assertEqual(result.confirmation_status, expected)
                self.assertIsNone(result.journey)


class CorpusLifecycleTests(unittest.TestCase):
    @staticmethod
    def _entry(evidence_id: str, source_id: str) -> IndexedEvidence:
        return IndexedEvidence(
            evidence_id=evidence_id,
            source_id=source_id,
            source_snapshot_sha256=sha256(f"snapshot:{source_id}".encode()).hexdigest(),
            release_status="published",
            source_status="published",
            candidate_status="published",
            span_sha256=sha256(f"span:{evidence_id}".encode()).hexdigest(),
            payload={"fictional": True},
        )

    def test_repeat_build_switch_withdraw_and_rollback_are_version_safe(self):
        with TemporaryDirectory() as directory:
            store = VersionedCorpusIndexStore(Path(directory))
            entries = [self._entry("E-1", "S-1"), self._entry("E-2", "S-2")]
            first, status = store.build(
                index_version="index-v1",
                corpus_version="corpus-v1",
                release_version="release-v1",
                entries=entries,
            )
            same, repeated = store.build(
                index_version="index-v1",
                corpus_version="corpus-v1",
                release_version="release-v1",
                entries=list(reversed(entries)),
            )
            self.assertEqual(status, "created")
            self.assertEqual(repeated, "unchanged")
            self.assertEqual(first.content_digest, same.content_digest)
            store.activate("index-v1")
            withdrawn = store.rebuild_without_source(
                source_id="S-1",
                new_index_version="index-v2",
                new_corpus_version="corpus-v2",
                new_release_version="release-v2",
            )
            self.assertEqual([item.source_id for item in withdrawn.entries], ["S-2"])
            self.assertEqual(store.active_manifest().index_version, "index-v2")
            self.assertEqual(store.rollback().active_index_version, "index-v1")
            self.assertEqual(store.active_manifest().content_digest, first.content_digest)

    def test_failed_fetch_hash_or_parse_preserves_last_known_good(self):
        with TemporaryDirectory() as directory:
            store = SourceRecoveryStore(Path(directory))
            good = b'{"fictional": true}'
            good_hash = sha256(good).hexdigest()
            promoted = store.refresh(
                source_id="S-1",
                fetch=lambda: good,
                parse=lambda raw: raw.decode("utf-8"),
                expected_sha256=good_hash,
            )
            self.assertEqual(promoted.status, "promoted")
            failures = [
                store.refresh(
                    source_id="S-1",
                    fetch=lambda: (_ for _ in ()).throw(ConnectionError("offline")),
                    parse=lambda raw: raw,
                ),
                store.refresh(
                    source_id="S-1",
                    fetch=lambda: b"changed",
                    parse=lambda raw: raw,
                    expected_sha256=good_hash,
                ),
                store.refresh(
                    source_id="S-1",
                    fetch=lambda: good,
                    parse=lambda raw: (_ for _ in ()).throw(ValueError("bad parse")),
                ),
            ]
            self.assertEqual(
                [item.quarantine_reason for item in failures],
                ["fetch_failed", "hash_changed", "parse_failed"],
            )
            self.assertTrue(all(item.active_sha256 == good_hash for item in failures))
            self.assertEqual(store.active_sha256("S-1"), good_hash)


class ModeSafeStateServiceTests(unittest.TestCase):
    def test_demo_is_allowlisted_and_stale_write_remains_typed(self):
        committer = fixture_committer()
        service = ModeSafeStateService.demo(
            committer=committer,
            scope_resolver=lambda requested: scope(workspace=requested, version=1),
            fixture_workspace_ids=frozenset({WORKSPACE_A}),
        )
        with self.assertRaises(PermissionError):
            service.load_snapshot(WORKSPACE_B)
        stale = service.commit(WORKSPACE_A, fact_command(version=99))
        self.assertEqual(stale.status.value, "stale")
        self.assertEqual(stale.new_state_version, 1)

    def test_personal_mode_rejects_fixture_committer(self):
        with self.assertRaises(ValueError):
            ModeSafeStateService(
                mode="personal",
                scope_resolver=lambda requested: scope(workspace=requested),
                personal_client=fixture_committer(),
            )

    def test_personal_snapshot_must_be_database_derived_and_owner_scoped(self):
        class FakeClient:
            def __init__(self, value):
                self.value = value

            def load_snapshot(self, workspace_id):
                return self.value

            def commit(self, workspace_id, command):
                return {"status": "fixture"}

        client = FakeClient(
            {
                "workspace_id": str(WORKSPACE_A),
                "owner_user_id": str(OWNER_A),
                "database_derived_state": False,
            }
        )
        service = ModeSafeStateService(
            mode="personal",
            scope_resolver=lambda requested: scope(workspace=requested),
            personal_client=client,
        )
        with self.assertRaises(RuntimeError):
            service.load_snapshot(WORKSPACE_A)


class Stage9ImmutabilityManifestTests(unittest.TestCase):
    def test_stage9_hash_is_line_ending_stable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_bytes(b"[theme]\r\nbase = 'light'\r\n")
            windows_digest, windows_mode = stable_sha256(path)
            path.write_bytes(b"[theme]\nbase = 'light'\n")
            linux_digest, linux_mode = stable_sha256(path)
            self.assertEqual(windows_digest, linux_digest)
            self.assertEqual(windows_mode, "normalized_lf_sha256")
            self.assertEqual(linux_mode, "normalized_lf_sha256")


if __name__ == "__main__":
    unittest.main()
