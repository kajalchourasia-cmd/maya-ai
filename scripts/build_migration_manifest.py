"""Generate the canonical local migration manifest; never applies migrations."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase/migrations"
OUTPUT = ROOT / "data/supabase/migration_manifest.json"

PURPOSES = {
    "20260910000100_stage2_storage.sql": ("Stage 2 foundational storage, RLS, graph and public evidence schema", "stage2-storage-v1"),
    "20260910000200_protect_workspace_owner.sql": ("Protect authenticated workspace ownership", "stage2-owner-protection-v1"),
    "20260911000100_bind_public_release_provenance.sql": ("Bind public release provenance", "stage2-release-provenance-v1"),
    "20260911000200_workspace_lifecycle.sql": ("Workspace lifecycle and deletion", "stage2-workspace-lifecycle-v1"),
    "20260911000300_workspace_owner_visibility.sql": ("Owner visibility hardening", "stage2-owner-visibility-v1"),
    "20260911000400_owner_only_episode_boundary.sql": ("Owner-only care episode boundary", "stage2-owner-episode-v1"),
    "20260911000500_journey_state_invariants.sql": ("Journey-state invariants", "stage3-journey-invariants-v1"),
    "20260911000600_personal_dependency_invalidation.sql": ("Personal dependency invalidation", "stage3-dependency-invalidation-v1"),
    "20260911000700_versioned_demo_workspaces.sql": ("Versioned fictional demo workspaces", "stage3-demo-workspaces-v1"),
    "20260911000800_enforce_storage_first_documents.sql": ("Storage-first document boundary", "stage4-storage-first-v1"),
    "20260911000900_stage3_onboarding_commit.sql": ("Authenticated onboarding commit", "stage3-onboarding-commit-v1"),
    "20260911001000_stage3_exit_hardening.sql": ("Stage 3 exit hardening", "stage3-exit-v1"),
    "20260911001100_stage4_document_confirmation.sql": ("Document confirmation and supersession", "stage4-document-confirmation-v1"),
    "20260911001200_stage4_api_role_hardening.sql": ("Document API role hardening", "stage4-api-hardening-v1"),
    "20260911001300_stage5_hybrid_retrieval.sql": ("Hybrid retrieval, graph and authenticated retrieval RPCs", "stage5-retrieval-v1"),
    "20260912000100_stage10_state_review_lifecycle.sql": ("Authorized state, plan, follow-up and simulated-review lifecycle", "stage10-lifecycle-v1"),
    "20260912000200_stage10_rpc_hardening_and_reset.sql": ("Stage 10 RPC shape hardening and reset support", "stage10-rpc-hardened-v1"),
    "20260916000100_controlled_corpus_import.sql": ("Preserve review-required recovered corpus and operator import receipts", "controlled-corpus-import-v1"),
    "20260916000200_operator_development_index.sql": ("Private operator development indexing; publication unchanged", "operator-development-index-v1"),
}


def main() -> int:
    names = sorted(path.name for path in MIGRATIONS.glob("*.sql"))
    if set(names) != set(PURPOSES):
        missing = sorted(set(names) - set(PURPOSES))
        obsolete = sorted(set(PURPOSES) - set(names))
        raise SystemExit(f"migration mapping mismatch: missing={missing} obsolete={obsolete}")
    rows = []
    for order, name in enumerate(names, start=1):
        raw = (MIGRATIONS / name).read_bytes()
        purpose, schema_version = PURPOSES[name]
        rows.append({
            "order": order,
            "migration": name,
            "purpose": purpose,
            "expected_post_migration_schema_version": schema_version,
            "sha256": sha256(raw).hexdigest(),
        })
    output = {
        "schema_version": "nestline-migration-manifest-v1",
        "remote_application_authorized": False,
        "migration_count": len(rows),
        "migrations": rows,
        "supported_paths": {
            "clean_install": names,
            "stage4_to_current": names[names.index("20260911001300_stage5_hybrid_retrieval.sql"):],
            "stage9_to_current": names[names.index("20260912000100_stage10_state_review_lifecycle.sql"):],
        },
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"migration manifest: {len(rows)}/{len(names)} mapped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
