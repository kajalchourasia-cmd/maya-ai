# Maya AI — urgent RAG completeness and missing-deliverables investigation

**Priority: HIGH — critical dependency for the working product**  
**From:** Kajal  
**To:** Aswath and his Codex  
**Date:** 16 September 2026

## 1. In simple words: what we need answered

We expected to transfer the knowledge library and existing RAG implementation so that Maya's dashboard and chatbot could use them on Kajal's computer. The latest handoff contains useful recovered material, but not a populated retrieval database, real embeddings, or evidence of a working live knowledge pipeline.

Please explain **why each expected item is missing, whether it ever existed, and exactly what is needed next**. A great deal of the product depends on this. Do not respond only with “not found,” “pending approval,” “gated,” or a passing test count without explaining the underlying cause and practical resolution.

This is an evidence request, not an accusation of withholding data. We need to distinguish an incomplete export from work that was implemented in code but never executed against real data.

### Important clarification about the earlier request

`MAYA-MISSING-CORPUS-DISCOVERY-AND-EXPORT-REQUEST-FOR-ASWATH.md` explicitly requested existing source material, chunks, genuine embeddings, releases, retrieval dependencies and relevant code. It also explicitly prohibited generating replacement embeddings, publishing drafts, rebuilding the product or changing the UI during discovery.

Therefore:

- If genuine embeddings existed in scope, they should have been located and exported or their exclusion explained.
- If they did not exist, generating them merely to make the export appear complete would have been incorrect.
- That request was a corpus-discovery handoff, not an unrestricted ZIP of the entire laptop or every application dependency.
- We now need a clear account of the **complete application's existing assets and missing runtime work**, not another package whose completeness is inferred from successful checksums.

## 2. Scope and safeguards

First investigate and produce the response below. You may package additional existing, transferable project assets that the investigation locates. Preserve original files and existing exports.

Do not generate new embeddings, incur provider charges, change database rows or schemas, publish content, fabricate approvals, modify the application, overwrite Kajal's frontend, push to GitHub, or deploy as part of this request. For work requiring those actions, describe the exact proposed action and required approval separately.

Use known Maya/Nestline project locations and authorized services. Ask before expanding into unrelated folders or accounts. Never export API keys, passwords, raw `.env` files, authentication records, unrelated databases, or personal medical records. Provide configuration **names**, not secret values.

## 3. Starting evidence — cross-check, do not simply repeat

Reference the latest `ASWATH-CORPUS-DISCOVERY-RESPONSE.md` and package `MAYA-MISSING-CORPUS-DISCOVERY-20260915T211431Z`.

| Item | Current evidence | What remains unanswered |
|---|---|---|
| Database | Sender reports zero rows in all 10 allowlisted knowledge tables in both checked local and hosted databases. | Were these the actual intended runtime databases? Why were they never populated, or where was the populated system used? |
| Ingestion | 14 recovered runs, all `dry_run=true`, with `review_required` outcomes. | Why did execution stop at dry runs? Was a real ingestion command ever attempted? |
| Parsed material | 986 blocks counted; 72 governed block bodies preserved. | Which unretained content is actually needed, rather than assuming every parsed block is useful evidence? |
| Evidence and review | 55 candidates and 55 pending tasks in historical run files; 54 accepted content/product decisions in separate authoring records. | How are these different records reconciled? Which decisions remain applicable? |
| Embeddings | Zero real vectors in the inspected runs, databases and file stores. | Was the provider path configured, invoked, blocked, failed, or never implemented? |
| Publication | Zero published releases; authoring profiles/fragments remain draft. | What exact requirements prevented publication, and which are content requirements versus engineering limitations? |
| Source originals | Exact-hash originals located for 4 of 14 runs; 10 not located. Twelve supplemental text derivatives exported; 15 PDF/HTML/image files excluded. | Give individual reasons and workable permitted alternatives, not one blanket exclusion statement. |
| Retrieval tests | Stage 5 fixtures contain deterministic test vectors. | Is there any historical successful query against a real index? If not, state that clearly. |
| Application code | Latest package contains reference code, not a standalone full application. | Which checkout and additional files are needed to run the actual product? |

Receiving-side checks verified the ZIP hash, 137 listed payload checksums, and the package verifier's counts. They also checked candidate-to-block references and existing review checksum matches. This verifies the received material, **not** a live database connection or clinical completeness. The sender's reported 500 passing tests were not independently rerun during that receiving-side review.

## 4. The central question: what was actually completed?

For ingestion, parsing/chunking, persistence, embeddings, retrieval, generation, agent routing, dashboard endpoints and chat endpoints, supply this matrix:

| Component | Code exists? | Fixture-tested? | Executed with real public corpus? | Output saved where? | Connected to normal UI? | Evidence and remaining work |
|---|---|---|---|---|---|---|

Support each answer with a file/function, commit, redacted execution record, artifact or database observation. Use `UNKNOWN` when evidence is unavailable.

Answer explicitly:

1. Was end-to-end live RAG ever successfully executed? On which checkout, configuration and data version?
2. If yes, where are its persisted outputs and execution evidence now?
3. If no, which earlier “complete,” “GO,” or self-verification conclusions meant code/fixture readiness rather than an operational populated system? Cite their actual wording and limitations.
4. Was work intentionally deferred, stopped by a gate, blocked by access/cost, interrupted by failure, or simply never invoked? Separate proven facts from inference.
5. Which existing implementation can we reuse immediately? Do not propose rebuilding working architecture without evidence that it is necessary.

Do not create a new successful trace and present it as historical proof.

## 5. Investigate the exact stopping points

### A. Why were all recovered ingestion runs dry runs?

Identify the entry point, command/configuration and relevant defaults. Establish whether a non-dry-run execution was attempted. If it failed, provide its actual error and redacted logs; if no receipt exists, say so.

Inspect the transition from extraction to candidate selection, review, embedding and persistence. Explain what prevents `write_staging_run` and related persistence paths from accepting these recovered dry-run artifacts. Do not simply flip their flags to make them importable.

### B. Chunks and the 914 unretained blocks

The inspected `_governed_blocks` logic retains blocks selected by evidence candidates, not an unbounded page dump. Therefore “914 bodies not found” is **not proof of 914 lost clinical facts**.

Explain whether full parse retention was intended, whether another parse cache exists, and whether the 72 retained blocks cover the selected evidence. Identify useful content gaps by requirement and source. Do not insist on restoring all 986 blocks merely to satisfy a count.

Reconcile the eight historical run variants against the current audit: list changed IDs, text/hashes, applicability and review consequences. Do not invalidate unchanged approvals unnecessarily.

### C. Real embeddings and retrieval

Check the actual embedding implementation and configuration, not only exported arrays. Distinguish “provider not selected” from “provider configured but never invoked” and “invocation failed.”

If real vectors exist elsewhere in known project scope, export them with chunk IDs, text hashes, provider/model, dimensions, preprocessing version, index settings and release linkage. Otherwise explain the precise missing execution steps and dependencies. Never infer a model from vector dimensions or substitute deterministic fixtures.

If a historical real retrieval trace exists, show a non-private query, source/chunk IDs, retrieved passages, filtering/ranking path and citations. Explain whether response generation also ran. Retrieval-only success is not proof of a complete chat response.

### D. Database, migrations and storage

The report lists 17 local migrations and 14 hosted migrations, with the hosted schema stopping at Stage 4. Identify the missing migrations, whether that hosted project was intended for current runtime use, and the impact on retrieval and application functions.

Explain whether the real intended corpus store is PostgreSQL, an immutable file release, another vector store, or a combination. Locate the code that writes and reads that store. Do not assume a local publication script automatically populates Supabase.

If a populated database is newly located, specify the smallest safe export and restore procedure for project knowledge and required schema, with storage files exported separately. Do not send an empty SQL file as the missing corpus. If no populated store exists, say that export cannot solve creation of missing data.

### E. Reviews and gates

Preserve the existing 54 accepted content/product decisions covering 27 candidates, subject to matching content hashes. Do not ask Kajal to repeat those decisions without a specific changed-content reason. Do not treat them as clinical, licence or India-localisation approval.

For each blocking gate, state:

- The exact rule and operation it blocks.
- Whether it is a justified release requirement, an engineering prerequisite, or an overly broad runtime restriction.
- What existing evidence satisfies it and what is genuinely missing.
- Whether isolated development/retrieval testing can proceed without misrepresenting publication readiness.
- Who can resolve it and the smallest legitimate next action.

Do not remove safeguards or invent approvals just to obtain a GO verdict. Equally, do not apply a publication blocker to unrelated engineering work without explaining why.

## 6. Explain every excluded or unavailable asset individually

Use one row per item or genuinely equivalent group:

| Item/IDs | Status | Specific reason | Supporting evidence | Impact | Permitted alternative/next action | Owner or access needed |
|---|---|---|---|---|---|---|

Allowed statuses: `EXPORTED`, `EXISTS BUT EXCLUDED`, `EXISTS ELSEWHERE`, `NOT FOUND IN CHECKED SCOPE`, `NEVER GENERATED — CONFIRMED`, `ACCESS BLOCKED`, `APPROVAL BLOCKED`, `EXPORT FAILED`, `NOT REQUIRED`.

Absence from the checked locations does not prove something never existed. “Rejected” must identify who/what rejected it, the applicable rule, and a practical resolution.

For the 15 excluded source files, identify the relevant source-level terms or registry restriction and distinguish a verified restriction from uncertainty. Do not assume every PDF or webpage is forbidden to transfer. Conversely, do not override a genuine restriction. Offer permitted excerpts, acquisition URLs and precise manual retrieval instructions where appropriate. A newly downloaded changed document is a new version; do not reuse old hashes or approvals automatically.

## 7. What does the complete-product handoff actually require?

Inventory the previous full handoff and the latest discovery package together before asking us to resend duplicate assets. Provide an assembly map, or a consolidated existing-assets ZIP where lawful and practical, containing:

1. The canonical backend source at an identified commit, with relevant uncommitted changes supplied separately and explained.
2. Required modules, migrations, dependency/lock files, startup commands and a secret-free configuration template.
3. Existing source catalogue, eligible source text, chunks, citations, reviews, releases and real vectors **only if they exist**, with their actual statuses preserved.
4. Database/schema and storage restore instructions appropriate to what was actually found.
5. A component inventory naming what is absent, external, optional or separately configured.
6. A minimal reproducibility check that distinguishes import/startup success, database access, real retrieval and generated answers.

The discovery snapshot does not include several imported modules, including `app/schemas/content.py`, `app/services/embeddings.py`, `app/services/public_parsers.py` and `app/services/content_validation.py`. Establish where their matching versions are supplied; a reference snapshot is not automatically runnable.

Explain whether the excluded local live-provider benchmark changes are actually unrelated to connecting real answers. Export relevant existing work separately if needed, without secrets or unrelated edits.

**Kajal already has the intended frontend and growth-image library. Preserve them.** Identify backend/API contracts and integration dependencies rather than replacing her UI with an older frontend. Do not package `node_modules`, virtual environments, whole Docker volumes, private uploads or credentials as a shortcut to portability.

## 8. Tie the missing data to actual product requirements

For each area, identify existing evidence IDs/implementation, the genuine gap and whether it is a corpus, metadata, runtime-wiring or presentation issue:

| Area | Required capability |
|---|---|
| Shared context | Pregnancy/postpartum timeline, diet, allergies, symptoms and restrictions flow consistently from onboarding; no silent sample facts. |
| Nutrition | Supported stage guidance, nutrient information and food options; dietary/allergy filtering and relevant symptom adaptations. |
| Movement | Supported stage guidance, activity categories, restrictions, adaptations and relevant stop/escalation advice. |
| Symptoms and wellbeing | Actual reported concerns, supported explanations/support and appropriate escalation, without inventing a user's emotional state. |
| FAQs and do's/don'ts | Useful grounded answers; no requirement for a separate FAQ corpus if existing evidence adequately supports them. |
| Chat and plans | Real retrieval, session context, relevant constraints, follow-ups, citations and requested plan creation/revision. |
| Growth and timeline | Existing week/measurement/image mappings and calculations; identify their separate data source rather than assuming everything needs RAG. |

Broad pregnancy applicability must not be presented as unique weekly advice. A fragment appearing in three trimester buckets does not establish three distinct guidance sets. Do not create unsupported week-by-week differences to conceal coverage gaps.

## 9. Required response and deliverables

Create **`ASWATH-RAG-COMPLETENESS-ROOT-CAUSE-AND-DELIVERABLES-RESPONSE.md`** with:

1. A short plain-language answer: why the full expected RAG package was not supplied.
2. The component-status and missing-item matrices above, backed by evidence.
3. A reconciliation of earlier completion claims with real execution and persisted outputs.
4. Any additional existing assets found, with a manifest, SHA-256 checksums and verification instructions. If none were found, say so; do not manufacture a fuller ZIP.
5. The shortest dependency-ordered recovery plan: what can be reused, what needs execution, what needs genuinely new work, and what needs human input.
6. A clear split between actions Aswath must perform and actions Kajal can perform locally, including precise non-secret access requirements. State whether Aswath's laptop is still needed and for which task.
7. Separate verdicts for **sufficient to start local implementation**, **sufficient for real grounded retrieval**, and **ready for user-facing use**. Explain unmet conditions rather than giving one ambiguous GO.

If producing an additional archive, name it `MAYA-EXISTING-ASSETS-ADDENDUM-<timestamp>.zip` and state which previous package(s), if any, it depends on. Preserve this request alongside the response.

**Completion means every important omission has an evidenced explanation and an actionable next step. It does not mean making the numbers look complete or repeating that tests passed. We need an honest, usable path from the work already built to the working product.**
