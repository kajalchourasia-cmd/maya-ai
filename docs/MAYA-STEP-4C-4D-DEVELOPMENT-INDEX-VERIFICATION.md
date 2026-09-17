# Maya — real development corpus admission and embeddings

16 September 2026 · for Kajal

**Outcome: the approved development-only admission/indexing path is implemented and verified for 96 records. Real OpenAI embeddings are stored in local PostgreSQL/pgvector. This is not a published corpus, clinical approval, connected dashboard/chat, or a Step 5 retrieval-quality result.**

## 1. What changed after your approval

Kajal explicitly authorised separating development indexing from user-facing publication, using permitted source material and retaining all unfinished review statuses. Reference: `Kajal-development-indexing-not-publication-20260916`.

Implemented one bounded extension in the existing database: private development batches, evidence and vectors. Reused the source verification, expansion, hashing, database tooling and real embedding client. No replacement vector database, new model framework or canned-answer runtime was introduced.

This lane does not weaken the approved-only production ingestion contract. It makes indexing permission separate from clinical/publication approval. No human review decisions were invented and no production candidate was promoted.

| Work | Result |
|---|---|
| 4C development admission for selected eligible material | Verified, 96 source-bound records imported |
| Full original 4C production/content-review scope | Still incomplete; source holds and semantic/release work remain |
| 4D development embeddings | Verified, 96 real vectors, 1,536 dimensions each |
| Step 5 retrieval quality and runtime | Not executed in this turn |
| User-facing publication/dashboard/chat | Unchanged; not declared ready |

## 2. Exact corpus scope

- 53 existing selected passages admitted under the verified handoff's storage/embedding permissions.
- 43 of the 46 expanded text sections admitted for private development: 35 OWH sections and 8 NHS sections.
- 3 broader NHM-MOTHERHOOD sections held: extracted pages 9, 12 and 16. Existing narrower permitted passages from that source remain included. The broader selections' permission/third-party-origin assessment was not independently completed; unsuccessful attempts to fetch the full current policy are not treated as fresh verification.
- 2 BHC-WEEKS passages remain excluded from embedding under their recorded restriction.
- Previously held preparation material, such as flattened tables and treatment schedules, was not silently added to this batch.

96 is a record count, not a count of independent new facts. Overlap IDs are preserved. Existing selections retain their exact candidate provenance. Expanded records retain derivative hashes, offsets, canonical links and the original authoring record; they do not falsely claim verified original PDF/HTML bytes.

Source text is embedded after deterministic normalization only, not replaced with model-generated summaries. Historical search text included title/locator prefixes; the new development inputs deliberately use passage text alone. Those historical fields remain in provenance and were not edited in the public corpus.

### Source-use basis

The [OWH reuse policy](https://womenshealth.gov/about-us/work-us/collaborate-us) permits reuse of original federal health text and distinguishes excluded photographs and linked non-federal publications. The selected expansion is original text only, with source attribution; no photographs or linked publications are imported.

The [NHS terms](https://www.nhs.uk/our-policies/terms-and-conditions/) allow reuse of covered content under stated licensing, attribution and update conditions. The [exceptions page](https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/) was inspected. Stored records carry the original article link, attribution and licence link, and the supplied capture date. Source currency and clinical suitability are not inferred from copyright permission. No publisher endorsement is claimed. A separate National Archives licence-page fetch was blocked; this report relies on the NHS terms and existing handoff documentation, not a falsely claimed successful fetch.

These are development source-use assessments, not signed clinical/licence role approvals or a blanket assessment for future commercial deployment.

## 3. Applicability and conditions: explicit remaining limits

Source-literal ranges remain unchanged. Broad-stage sections have no fabricated exact-week interval. Existing passage conditions are retained; expanded sections keep their full conditional clauses and explicitly mark structured condition interpretation unresolved. An empty structured condition array is **not** a claim that the passage is suitable for everyone.

This is sufficient to preserve and index text for operator investigation, not to automatically recommend every indexed statement. Step 5 must test conditional applicability, same-source overlap handling and relevance. User delivery also requires completing appropriate content validation, currency/localisation work and release decisions. The original 4C production goal is therefore not labelled complete.

## 4. Real execution evidence

Development packet: `8ad39c36af0425cf527102a22ea798c5b16ce347bf49fc5d57430d844b5cbed0`.

Local import completed at 13:30 UTC; real embedding operation completed at 13:31 UTC; independent database recheck completed at 13:33 UTC.

- Provider: OpenAI, endpoint `https://api.openai.com/v1/embeddings`.
- Model: `text-embedding-3-small`; dimensions explicitly requested as 1,536.
- One actual provider request; HTTP 200; 96 returned vectors.
- Provider-reported input/total tokens: 10,920.
- Estimated cost: **USD 0.0002184**, using the [published model input rate](https://developers.openai.com/api/docs/models/text-embedding-3-small).
- Maximum reservation for this request: USD 0.01. Shared account-wide remaining funds were not independently verified; this local reservation does not enforce account-wide spending.
- Every stored vector matches its source-record identity, model and provider receipt. Maximum numeric difference after PostgreSQL float32 storage: approximately `4.69e-9`.
- Same-vector cosine distance is zero. This checks storage/operator integrity, **not semantic retrieval quality**.

The [official embedding contract](https://developers.openai.com/api/reference/resources/embeddings/methods/create) was checked using the OpenAI Docs skill. Request count, per-input byte-based conservative token bounds, response indices, dimensions, finite/nonzero values and returned usage are checked. Failed or uncertain requests leave a durable reservation and are not automatically retried. A validated local cache supports resuming without another paid call.

## 5. Verification performed

- Source-bound import matched all stored values, not only counts.
- Injected import and vector-write failures rolled back.
- Repeated imports and vector writes did not create duplicates or change values.
- Deliberate record/vector receipt conflicts were rejected and rolled back; exact values were rechecked afterwards.
- Anonymous, authenticated and service-role application roles were denied access to all three private tables: nine role/table checks.
- Existing public corpus, release state and review decisions remained unchanged by before/after comparison and the existing import verifier.
- Source handoff hashes were checked again after execution.
- **254 Python tests and 232 subtests passed**, including ingestion, content, retrieval-contract, source and embedding regressions.
- **325 database assertions passed across eight SQL test files.**
- Five existing PyMuPDF/SWIG deprecation warnings remain.
- A full pre-mutation database backup was saved and its archive listing verified. A full restore rehearsal was not performed.

The first new unit-test run caught an incorrect normalization assumption. It was fixed before import/provider execution, with the original provenance retained. Synthetic vectors used by failure/cache unit tests are labelled test-only and were never inserted into the real development index. Live execution used the real HTTP embedding client.

## 6. Code and reproducibility

- `app/services/development_corpus.py`: development admission, permission exclusions, immutable record checks, bounded inputs, vector/source binding and transactional SQL.
- `scripts/maya_development_index.py`: prepare/import/embed/verify commands; local-only database identity, backup, durable provider receipt/cache, rollback/conflict/repeat/isolation checks.
- `supabase/migrations/20260916000200_operator_development_index.sql`: private tables, RLS, revoked application privileges. Applied to the isolated local database only.
- `scripts/build_migration_manifest.py` and `data/supabase/migration_manifest.json`: all 19 migrations mapped.
- `tests/test_development_corpus.py`: admission, restrictions, tampering, vector validation, cache and uncertain-request behaviour.

Reports reside under `reports/local/development-index/8ad39c36af0425cf527102a22ea798c5b16ce347bf49fc5d57430d844b5cbed0/`:

- `admission-packet.json`
- `import-verification.json`
- `embedding-ledger.json`
- `real-vectors.json`
- `embed-verification.json`
- `verify-verification.json`

Regression evidence: `reports/local/development-index/regression.xml` and `database-regression.log`.

Use the existing local Python dependency environment, then:

```text
python scripts/maya_development_index.py verify --execute-authorized-development --package "<verified inner discovery folder>"
```

Do not delete a provider ledger to retry an uncertain request. Investigate usage and cache state first. Full-text/vector reports remain ignored by Git. No key, filled environment file or health record was added to source control.

## 7. Exact next step

**GO for Step 5 operator-only retrieval testing on the admitted 96-record development batch. NO claim of public-release readiness.**

Next prove real query embedding, semantic/full-text retrieval, source fidelity, timing and conditional handling, overlap suppression, no-match/provider-failure behaviour and relevant answerability. Then connect the intended product runtime only with an explicitly appropriate evidence-release path. Do not route ordinary dashboard/chat users into these private tables to make the UI look complete.

No UI change, hosted change, Git commit/push or deployment occurred in this work. No further credential was requested or required for the successful indexing run.
