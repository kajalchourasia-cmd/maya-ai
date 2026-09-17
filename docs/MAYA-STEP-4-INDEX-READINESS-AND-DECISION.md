# Maya — Step 4 readiness, recheck and pending decision

Date: 16 September 2026

**Status: prior import reverified; indexing inventory and embedding-client hardening implemented. Real corpus embedding/indexing is NOT executed or complete.**

## What is real and verified

The database still contains the actual recovered 14 sources, 72 source blocks, 55 draft evidence chunks, 56 guidance fragments and 63 draft weekly profiles. All 54 original content/product decisions and the private provenance receipt still match the transferred package. The release remains draft and all 55 review tasks remain pending.

The source-bearing SQL search still returns real stored evidence and source links in the operator review lane. This is not a fake answer adapter. It is also not yet a published retrieval-gateway result or a generated chatbot response.

The earlier provider smoke test and non-medical vector round-trip remain historical evidence of working provider/database infrastructure; they do not mean these corpus passages have embeddings. No provider call was made in this step.

## What was implemented this step

1. `app/services/corpus_indexing.py`: a read-only inventory derived from the checksum-verified handoff, showing embedding permission separately from the existing approval gate, missing review roles, and draft evidence availability by stage, week/day and domain.
2. `scripts/audit_maya_index_readiness.py`: rechecks the actual local database against the handoff before writing the inventory report. It does not alter the database or call an LLM.
3. `app/services/embeddings.py`: strengthened the existing real HTTP provider client. It now validates exact response model, complete unique integer indices, finite/nonzero numeric vectors and optional expected dimensions; rejects blank inputs; prevents HTTP redirects carrying credentials; and retains only response status/request ID/model/usage metadata for later accounting. No fixture fallback was added.
4. `tests/test_embedding_boundary.py` and additional real-handoff inventory assertions: cover malformed provider output and the actual handoff's permission/review split. Provider error-case tests use explicitly mocked responses; they are not evidence of live provider calls.

The initial inventory run used the wrong location for the run's source identity. It stopped without mutations; this was corrected to use the historical artifact's source ID and covered by a real-package regression test.

## The exact blocking distinction

| Question | Verified answer |
|---|---:|
| Recovered evidence candidates | 55 |
| Candidates whose source registry permits embedding | 53 |
| Candidates whose source forbids embedding | 2 (`BHC-WEEKS`) |
| Candidates eligible under the existing production ingestion approval rule | **0** |
| New corpus vectors generated this step | **0** |
| New paid API calls this step | **0** |
| Published releases | **0** |

The existing `public_ingestion._embeddings` function selects only candidates with state `approved`. The fact that a source permits embedding does not satisfy the candidate's outstanding review roles. The operational handoff also distinguishes development work from publication and real-user guidance.

Outstanding accepted review roles across the 55 tasks:

- Clinical: 55.
- Licence: 55.
- India localisation: 55.
- Content: 28.
- Product: 28.

These are missing role decisions under the existing project contracts, not new requirements invented in this step. Existing content/product decisions were retained, not invalidated.

**46 of 63 draft profiles have no linked evidence.** A profile's empty links do not necessarily mean no broad-stage passage exists; the inventory now distinguishes these two facts. Candidate availability alone is not evidence of complete coverage or clinically appropriate advice.

## Decision requested from Kajal

Recommended development path: explicitly authorize a real operator-only development index of the 53 passages whose recorded source permissions allow embedding. Keep all original review statuses and publication gates unchanged, exclude the two restricted passages, and make the development index inaccessible to dashboard/chat users.

This would be a documented development-path extension, not silently passing pending material through the existing approved-only ingestion path. It would use real provider embeddings and real local database searches, with source IDs, hashes, model/dimension provenance, costs, rollback/idempotency checks and citation/filter tests. It would **not** create clinical approvals or establish readiness for real-user health guidance.

Alternative: retain the existing gate unchanged and wait for the necessary reviews before corpus embedding. The current production code must not be made to pretend pending candidates are approved.

No development-index exception, new index table, corpus-vector upload or publication change was applied while this decision was pending. The async question's suggested option is not an approval until Kajal answers it.

## Recheck results

- **187 Python tests passed**, plus **232 subtests passed**: existing import, actual handoff, local infrastructure, ingestion, content, retrieval, and the new embedding-boundary checks.
- **325 database assertions passed**, across all 8 existing SQL test files.
- All mapped imported values and the full provenance receipt match.
- Anonymous/authenticated application roles still cannot read the draft corpus or the private receipt.
- Five PyMuPDF/SWIG deprecation warnings; no test failures.
- This was not a full browser/onboarding/dashboard/chat verification, and no such claim is made.

Evidence:

- `reports/local/corpus-indexing/readiness-20260916T102221636460Z.json`
- `reports/local/corpus-indexing/regression.xml`
- `reports/local/supabase-kajal/test-redacted.log`

## What comes after the decision

1. Complete the authorized real indexing path with bounded provider spending and model/dimension checks. Preserve source restrictions and review states.
2. Test actual semantic and full-text retrieval, timing/domain/condition filters, source spans and no-match/error cases. Report operator-only results separately from the published gateway.
3. Resolve publication and content-coverage requirements; connect the existing gateway to the server-controlled no-login context rather than accepting browser-supplied workspace authority.
4. Connect nutrition/movement first, then other dashboard sections, Ask Maya, follow-ups and requested plans. Test different weeks, diets, allergies and stated symptoms without adding hidden facts.
5. Verify browser-to-backend-to-retrieval-to-answer traces before claiming the user-facing product is working end to end.

The engineering path is feasible. Completion, useful coverage and safe user-facing quality are not guaranteed by passing infrastructure tests, and have not yet been demonstrated.

## API documentation used

The OpenAI Docs skill was used to check the current embedding response contract, supported dimensions and pricing against official documentation:

- [Embedding API](https://developers.openai.com/api/reference/resources/embeddings/methods/create)
- [Vector embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)
- [text-embedding-3-small model/pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small)

The planned existing model remains `text-embedding-3-small`, with 1,536 dimensions. Published standard input pricing is USD 0.02 per million tokens; actual costs must be calculated from returned usage and logged within the already authorized account caps. This report makes no new paid call or account-balance claim.

No key values were read or displayed for this audit. No database records, frontend, hosted setting, original handoff package or review decision were modified. No Git commit or push was made.
