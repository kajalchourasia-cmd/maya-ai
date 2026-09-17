# Stage 1 ingestion failure-recovery runbook

The active corpus must never be replaced by a failed or unverified candidate.

1. Fetch into a temporary candidate area. A network failure creates a quarantined record and leaves the active snapshot unchanged.
2. Verify the expected SHA-256 before parsing. A mismatch is quarantined with the candidate hash and last-known-good hash; it is never promoted automatically.
3. Parse and validate required spans. A parser exception or incomplete extraction is quarantined and cannot replace the active snapshot.
4. Promote atomically only after fetch, hash and parse checks pass. The same source/hash is idempotent and reports `unchanged`.
5. Build a new immutable index version linked to exact source snapshot hashes. Never mix versions in the active pointer.
6. Switch the active pointer atomically after full validation. Keep the last valid pointer for rollback.
7. Withdrawal creates a replacement index without the source, switches atomically and invalidates dependent caches. Verify that no orphan fragment remains retrievable.
8. For recovery, correct the upstream source decision or parser, create a new candidate and repeat the whole validation. Never edit the active snapshot in place.

Executable evidence: `tests/test_consolidated_controls.py` covers fetch error, changed hash, parse failure, last-known-good preservation, idempotent promotion, immutable rebuild, withdrawal and rollback.
