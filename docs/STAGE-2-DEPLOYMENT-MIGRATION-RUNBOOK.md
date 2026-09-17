# Stage 2 deployment migration runbook

**Status:** preparation only; no remote migration or deployment is authorized by this document.

## Before authorization

- Identify the target project and exact current migration/version state without exposing credentials.
- Confirm an owner-approved backup/restore point and retention location.
- Review `data/supabase/migration_manifest.json`; verify all file SHA-256 values with `python -m scripts.check_migration_manifest`.
- Run the clean and every supported upgrade path locally, pgTAP, authenticated two-principal API checks and database lint.
- Review planned downtime, rollback owner, application compatibility and post-migration smoke scope.

## Authorized execution outline

1. Freeze writes or establish the approved maintenance boundary.
2. Create and verify a backup.
3. Apply migrations in manifest order with stop-on-error.
4. Verify expected schema/version, constraints, indexes, grants and RLS.
5. Run authenticated owner/cross-owner read/write/delete/stale-version checks.
6. Smoke the application with non-sensitive test data.
7. Reopen traffic only after recorded approval.

## Rollback

Forward migrations remain immutable. If verification fails, stop traffic, preserve logs in redacted form, restore the verified backup or apply a separately reviewed forward correction, and rerun all checks. Never mark a partially verified database healthy.

## Required post-checks

Migration parity; all pgTAP tests; two-principal API isolation; anonymous grants; lint; application startup; deletion; relogin; State Committer idempotency/concurrency. Record exact target, operator, commands, timestamps, results and approval. This pass did not execute any remote step.
