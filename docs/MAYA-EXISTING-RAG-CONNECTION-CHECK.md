# Maya: existing RAG connection check

Checked on 15 September 2026 against the local `maya-ai-product-preview` working tree and the Supabase project configured in its ignored `.env`. This is not a fresh GitHub-head verification. No remote state, permissions, releases or approvals were changed. No patient records were queried.

## Bottom line

The original pipeline code exists and should be reused. A live end-to-end connection to its corpus has **not** been established. Filling `.env` made a read-only Supabase connection possible, but did not make a published corpus appear or connect the existing UI to Stage 5.

Do not replace the corpus with newly written content and call it the original RAG. Do not promote drafts or use administrator credentials in ordinary user requests to conceal the missing connection.

## Verified evidence

| Check | Result | Meaning |
|---|---|---|
| Supabase Auth settings read | HTTP 200 | Project is reachable with the configured application key. |
| Anonymous sign-in | Disabled | Current no-visible-login UX cannot simply create an anonymous authenticated Supabase session without a project configuration decision. |
| Published content releases read | HTTP 200, empty list | No published release is visible to application access. |
| Guideline chunks and public sources | HTTP 200, visible count 0 for both | No public evidence is currently available through those reads. This does not prove no private/draft records exist. |
| Repository RLS policy | Published releases/sources/chunks are readable by anon and authenticated roles | If deployed policies match this repository, published content should be visible. Need to establish whether this is the correct project, a publication gap, or deployed-policy drift. |
| Stage 5 public full-text and vector RPCs | Granted to authenticated, not anon | A publishable key alone is not a user session token. |
| Existing RetrievalGateway | Resolves authenticated workspace and exact state before public/personal retrieval | An in-memory browser session UUID is not interchangeable with a verified database workspace. |
| Current frontend dashboard | Calls `/v1/home`; that endpoint uses a local educational catalogue | This is not yet the hosted Stage 5 retrieval path. |
| Current frontend chat and plans | Call `/v1/demo/chat` and `/v1/demo/plan` | These still use the legacy fixture-backed path. |
| Local ingestion artifacts | Only the tracked source audit found in this checkout and two related local checkouts | A full ingestion/corpus export was not found in those locations. The teammate may have it elsewhere. |
| Release selection config | Corpus version and release ID blank | Must discover an actual release or receive its identifiers; never invent values. |
| Embedding configuration | No embedding model/provenance established by this check | Query embeddings must match the indexed corpus model/dimensions. Model-generation credentials do not establish this. |

## Existing architecture to reuse

- `app/services/journey.py`: resolve week/date/month and postpartum timing.
- `app/services/onboarding.py`: existing structured onboarding and Supabase boundaries.
- `app/services/retrieval.py`: PostgrestRetrievalRepository, RetrievalGateway, filters, separate caches, ranking and graph path.
- `app/services/embeddings.py`: real embedding provider interface; never select the deterministic test provider for runtime evidence.
- `app/services/retrieval_policy.py` and `app/schemas/retrieval.py`: applicability, provenance and answerability contracts.
- Existing safety, specialist/orchestration, and output-validation services: preserve and wire these boundaries, rather than routing the real UI through fixture setup scripts.
- Existing frontend: preserve its visual design and bind the structured results to its existing cards and chat.

## Information needed from the teammate

1. Confirm that the configured Supabase project is the one containing the completed ingestion work.
2. Provide the existing published `release_id` and `corpus_version`, if a release exists. If the work is local/unpublished, provide the corpus export or exact artifact directory and ingestion-run manifests instead.
3. Confirm source blocks, text chunks and embeddings were actually loaded, not only schemas/migrations and test fixtures. Supply aggregate counts, not personal records.
4. Supply embedding provider/model/dimensions used for those chunks and applicable environment-variable names. Share secrets only through secure local configuration.
5. Confirm remote migrations match the repository. If public data exists but is not visible, check the deployed RLS policies; do not disable RLS.
6. Resolve no-login session architecture: the existing gateway requires authenticated workspace state. Possible approaches need explicit design review: invisible anonymous authenticated sessions with suitable lifecycle controls, or a carefully scoped public-education retrieval lane that never reads personal database records. Do not repurpose the teammate's user account for every visitor.

`SUPABASE_ACCESS_TOKEN` is the CLI/management credential in this repository's example configuration. It is not the per-user access token expected by PostgrestRetrievalRepository. The database password is not an application-session substitute either.

## Implementation sequence after the missing connection is resolved

1. Validate the real release, source provenance and representative nutrition/movement evidence across pregnancy and postpartum. Start with read-only retrieval.
2. Connect onboarding to one accurately identified session context. Preserve entered values; do not seed symptoms, allergies, dates or a default week. No document dependency.
3. Connect the existing Stage 5 gateway through the agreed session/public boundary. Use the actual embedding configuration; explicitly report full-text-only operation if vectors are unavailable.
4. Retrieve ordinary stage-appropriate guidance even with no optional symptoms/allergies. Restrict only advice affected by a symptom/allergy or actual evidence limitation. Never relabel an infrastructure failure as a clinical clarification.
5. Feed source-backed results through the existing specialist/output boundaries into dashboard nutrition and movement schemas. Keep source citations and distinguish stage-wide references from genuinely week-specific claims.
6. Wire timeline/KPIs/growth to the same resolved journey. Preserve the current image library; do not invent missing measurements, mood or appointments.
7. Verify actual browser onboarding through dashboard at weeks 5 and 26, postpartum, month/date inputs, empty optional fields, vegan/vegetarian diets, allergies and symptom adaptations. Confirm changing context refreshes dependent outputs.
8. Connect Ask Maya and requested plans next through the same real context and retrieval stack; remove fixture endpoints from the ordinary UI path only when their replacements are verified. Symptoms, wellbeing and FAQs remain required subsequent work.

## Verification completed here

Existing retrieval, dashboard-guidance and demo-API regression tests: **91 passed, 202 subtests passed**, with one dependency deprecation warning. These are automated/local tests, not proof of a populated hosted corpus or successful live generation.

Including the new credential-safety diagnostic tests, the final focused run was **98 passed, 202 subtests passed**, with the same dependency warning.

Reusable safe diagnostic: `scripts/check_maya_runtime_access.py`. It uses only the application key for fixed read-only public-content/settings requests and logs no credential values. It does not publish content, create users, modify settings, or query patient records.

## Not done / not claimed

- No original corpus publication, ingestion rerun, embeddings regeneration or remote migrations.
- No administrator credential used in the runtime path.
- No live provider inference verified in this check.
- No new UI substituted; no completed end-to-end RAG integration claim.
- No GitHub push, merge or deployment.
