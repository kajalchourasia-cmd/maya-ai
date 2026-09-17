# Maya — Step 3: real recovered-corpus import

Date: 16 September 2026

**Verdict: GO for the next retrieval implementation step. The recovered draft corpus is now really stored in Kajal's local PostgreSQL/Supabase database. This is NOT a verdict that the complete corpus, live product RAG, dashboard or chatbot is finished.**

## What changed, in plain language

Previously, this local database had no knowledge records. It now contains the actual source passages and authoring records recovered from Aswath's handoff, with their original references and existing review decisions. No fictional replacement passages were created.

We built and executed the missing local database loader. It uses the existing Stage 1 validation and source-anchor matching, and the existing Stage 2/5 database tables. This is implementation of the planned architecture, not a new retrieval architecture or a parallel content store.

One additive migration was necessary: source and chunk tables could represent reviewed/published/retired records, but not recovered `review_required` records. The new migration adds that state and an operator-only provenance receipt. Existing published-only access rules and retrieval functions were not relaxed.

## Exactly what is stored

| Existing database table | Imported rows | Meaning |
|---|---:|---|
| content_releases | 1 | Draft recovered release; not published |
| public_sources | 14 | Source identities, URLs, attribution, permissions and versions |
| source_artifacts | 14 | Historical artifact metadata; not the original PDF/HTML files |
| source_blocks | 72 | Actual preserved source block bodies |
| ingestion_runs | 14 | Historical dry-run records, still correctly marked as dry runs |
| evidence_review_tasks | 55 | Pending reviews; not auto-approved |
| evidence_review_decisions | 54 | Existing content/product decisions preserved |
| weekly_profiles | 63 | Draft authoring profiles, including incomplete ones |
| guidance_fragments | 56 | Draft authored guidance with source links |
| guideline_chunks | 55 | Source-anchored evidence candidates, without vectors |

An additional private import receipt preserves the full validated authoring metadata, recovered ingestion records and supplied decision ledger. This receipt is audit provenance, not an alternate public retrieval database.

Release ID: `67884aa0-e072-52af-a32c-53001705b357`.

Corpus version: `recovered-draft-2ebd508df90d7bc32055`.

Final import fingerprint: `d15ebd67912158539cd39d3858cfb1e94fe517a19397c5b692568b78e48b46c5`.

## What was actually tested

1. Verified all **137 package payload checksums** against the pinned discovery manifest.
2. Validated the recovered ingestion records and authoring bundle using the existing project contracts.
3. Rechecked candidate text hashes, candidate fingerprints, source-governance bindings, source versions and preserved source anchors.
4. Preserved exact-version review decisions; rejected stale checksums and duplicate/conflicting decisions in tests.
5. Created a local pre-import `pg_dump` backup and verified that `pg_restore --list` could read it. A full restore rehearsal was not performed.
6. Applied the additive migration to **only** `supabase_db_maya-kajal-local`; 18 migrations are now registered.
7. Injected a failure partway through the real import before its first successful commit. All knowledge-table counts and checksums remained unchanged at zero after rollback.
8. Committed the actual recovered records, then repeated the import. Counts and checksums stayed unchanged: no duplicates or overwrites.
9. Intentionally attempted an incompatible text replacement. The transaction failed and stored data remained unchanged.
10. Compared every mapped field with the stored database value, including exact array values/order, and checked the full provenance receipt.
11. Verified that anonymous and authenticated application roles cannot read this draft release or its private operator receipt.
12. Ran a real PostgreSQL full-text search for pregnancy week 26 and food/exercise. It returned preserved evidence including `E-IN-FOOD`, `E-PREG-FOOD-SAFETY` and `E-PREG-MOVEMENT-OPTIONS`, with source URLs and matching source blocks. This was an **operator review query**, not a published retrieval RPC or a generated clinical answer.
13. Reran the real saved-vector pgvector round-trip check. It passed, independently matched Python cosine scores, and left no temporary test table. Those vectors are non-medical infrastructure-test vectors, not corpus embeddings.

### Regression results

- Loader, actual-handoff and local-infrastructure tests: **57 passed**.
- Existing ingestion, content and retrieval Python tests: **115 passed**, plus **232 subtests passed**.
- Existing database suite: **325 assertions passed across 8 files**.
- Migration inventory: **18/18 ordered migrations and checksums verified**.
- `git diff --check`: passed; Git emitted line-ending notices.
- The Python runs reported PyMuPDF/SWIG deprecation warnings; no test failures.

These scoped tests are not a claim that every application test or browser journey passed. No dashboard/chat browser verification was performed in this step because their runtime connection was not changed.

### Corrections made while implementing the loader

- Used the existing source-anchor matcher rather than requiring every selected passage to be one contiguous substring. The project's selected evidence can legitimately combine source sentences/bullets. Stored source text was not changed.
- Corrected release-bound run/decision fields and composite keys to match the later provenance migration. An initial attempted import failed a not-null constraint and rolled back before any corpus records were committed. The corrected import passed.
- Strengthened comparisons from JSON containment to exact mapped-field equality, so reordered or additional array entries do not silently pass.

## Important gaps that this import does not solve

| Gap | Current evidence | Required next action |
|---|---|---|
| Corpus embeddings | **0** vectors in the imported evidence chunks | Generate real embeddings only for content permitted and cleared for that use; preserve source/model/dimension/checksum provenance |
| Publication/reviews | **0** published releases; all 55 tasks remain pending | Resolve the documented review requirements through the appropriate owners; do not fabricate signatures or silently promote records |
| Weekly coverage | **46 of 63** draft profiles have no linked evidence | Audit stage/domain coverage and populate missing supported content; do not invent a different recommendation for every week |
| Missing original extraction | 986 blocks were historically counted; only 72 bodies were retained | Reacquire/reparse permitted sources where needed; the other 914 bodies were not recovered by this import |
| Source currency | Historical package integrity verified; current medical accuracy/currency not established | Check source currency and applicable guidance before user-facing publication |
| Restricted source | `BHC-WEEKS` is fixed-quote-only and does not permit embedding | Keep it out of embedding batches; use only its permitted delivery mode |
| Supplemental material | The 12 supplemental text derivatives were checksum-verified as package payloads, not converted into approved chunks | Process separately through existing ingestion/permission/provenance checks if needed |
| Other project assets | This import is the recovered evidence/authoring bundle, not every catalogue, UI asset or graph record | Reuse existing assets through their own loaders/contracts; do not claim they were imported here |
| Product runtime | No dashboard, chatbot or plan endpoint was rewired in this step | Connect the existing retrieval gateway, orchestration, answer validation and UI adapters; test the real request path |

The 54 existing product/content decisions remain intact. They are not equivalent to the other outstanding review roles. This step neither invalidates Kajal's existing decisions nor invents additional approvals.

## Next implementation sequence

1. Produce a stage/domain coverage and embedding-eligibility inventory from these stored records. Identify a useful nutrition/movement retrieval slice and its remaining review requirements.
2. Generate and persist the permitted real corpus embeddings with budget limits, retries, model/dimension checks and an execution ledger. Preserve the distinction between technical indexing and approval for user-facing publication.
3. Exercise the existing hybrid retrieval design against actual corpus records: timing and constraint filters, full-text plus vector retrieval, source citations and bounded graph support. Review-only diagnostics must remain separate from published user delivery.
4. Resolve content/review gaps required for release. Do not loosen every guardrail or substitute fixture text to hide missing evidence.
5. Wire one complete real path first: onboarding context → nutrition/movement request → retrieval → existing specialist/orchestration/validation → dashboard response. Check week 6 versus week 26, vegetarian/vegan preferences, allergies, stated symptoms, and no optional context.
6. Connect Ask Maya and requested plans to the same context and evidence path; then complete the other tabs, source-linked FAQs and deterministic KPI tables. Verify session isolation, real follow-ups, changes to context and appropriate urgent escalation.

## Files and reproducibility

Implementation:

- `app/services/corpus_import.py`
- `scripts/import_maya_corpus.py`
- `supabase/migrations/20260916000100_controlled_corpus_import.sql`
- `tests/test_corpus_import.py`
- `tests/test_corpus_import_handoff.py`
- Updated migration inventory builder/manifest and vector-check migration-count logic.

Actual execution evidence (local, ignored by Git):

- `reports/local/corpus-import/execute-verification-20260916T095524316358Z.json` — first committed import, including empty-before/populated-after proof.
- `reports/local/corpus-import/execute-verification-20260916T095856660361Z.json` — final exact-field checks and unchanged repeat import.
- `reports/local/corpus-import/before-import-20260916T095412039924Z.dump` — before the new migration and attempted import.
- `reports/local/corpus-import/before-import-20260916T095514548143Z.dump` — after migration, before the successful corpus import.
- `reports/local/corpus-import/before-import-20260916T095847001591Z.dump` — populated database backup before final repeat checks.
- `reports/local/supabase-kajal/test-redacted.log`
- `reports/local/supabase-kajal/real-vector-roundtrip.json`

Run from the repository with the existing Python environment and dependencies:

```text
python scripts/import_maya_corpus.py preflight --package "<extracted discovery-package directory>"
python scripts/import_maya_corpus.py verify --package "<extracted discovery-package directory>"
```

`execute` performs the local backup/migration/import/rollback/idempotency tests. It accepts no hosted database URL and checks the Docker project identity and loopback binding before database access. Use the inner package directory containing `SHA256SUMS.json` and `public-authoring`, not its outer wrapper.

The actual run used the pinned discovery manifest SHA-256:

`2ebd508df90d7bc32055de176e2e081330a645df5ba83029fffde0f5ad2396b7`.

No provider calls or provider charges were incurred in this step. No new key was required. No hosted database, GitHub branch, frontend, user session, existing approval or original transferred package was changed. No Git commit or push was made.
