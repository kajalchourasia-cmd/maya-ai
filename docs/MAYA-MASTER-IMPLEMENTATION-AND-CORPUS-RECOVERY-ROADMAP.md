# Maya — master implementation and corpus-recovery roadmap

Prepared for Kajal · 16 September 2026

**Purpose:** Keep one implementation sequence while corpus recovery proceeds in parallel. This is a plan and evidence-based checkpoint, not a claim that the full product is complete.

**Current position: Step 4C/4D development admission/indexing remains verified for 96 records. Step 5 now connects the normal chat/plan API to real private retrieval, bounded specialist generation and source/context validation. The six-case live run passed 5/6; its unsolicited-outline failure was fixed and the targeted two-case rerun passed 2/2. This is a private-development runtime milestone, NOT publication or full-product readiness. Dashboard/browser integration, detailed planners and broader acceptance coverage remain. Three expanded sections remain held.**

Latest execution: [Step 5 runtime integration and verification](MAYA-STEP-5-RUNTIME-INTEGRATION-VERIFICATION.md). Read the exact architecture extensions, real failures caught and corrected, test receipts and limits before proceeding. Source publication, unresolved metadata and graph coverage remain incomplete. Two pre-existing growth-card UI tests remain failing. The [earlier retrieval-only checkpoint](MAYA-STEP-5-REAL-RETRIEVAL-AND-ORCHESTRATION-CHECK.md) is historical; its statements that the normal runtime is unconnected no longer describe the private operator path.

**Latest execution (supersedes browser/UI status above):** [Static dashboard and local UI verification](MAYA-STATIC-DASHBOARD-AND-LOCAL-UI-VERIFICATION.md). Four overview cards, 42 calendar-week facts, nine six-question pregnancy FAQ sets and a separate postpartum set are implemented. Maternal facts are inside Your Journey but outside trimester panels. The private local browser connection passed onboarding and one genuinely retrieved/generated chat question with a working citation drawer. Full regression: 837 passed plus 315 subtests; frontend: 25 passed. The two obsolete growth-test expectations are reconciled and pass. Complete category content, detailed planners, broader live acceptance and public readiness remain outstanding.

Current evidence: [4C/4D development execution](MAYA-STEP-4C-4D-DEVELOPMENT-INDEX-VERIFICATION.md). One real embedding request, 10,920 tokens, estimated USD 0.0002184; 254 Python tests plus 232 subtests and 325 SQL assertions passed. Existing public corpus/review state and UI are unchanged. Read this before the earlier checkpoints below.

### Earlier checkpoints (before development-scope approval)

Latest update: [4B verification and 4C evidence expansion](MAYA-STEP-4B-VERIFICATION-AND-4C-EVIDENCE-EXPANSION.md). Seven delivered files match the pinned archive; it supplies reproduction documents, not new source text. The expansion packet contains 7,991 words, with 12 explicit source ranges, 34 unresolved broad-stage intervals and ten overlapping units. No new corpus records or embeddings were loaded.

Step 4C continuation: [counts, category coverage and overlap reconciliation](MAYA-STEP-4C-COUNTS-COVERAGE-AND-RECONCILIATION.md). Mechanical whole-token overlap reconciliation is executed and tested: ten sections contain 19 existing passages; none is wholly redundant. 83 targeted tests passed. No database/provider/UI changes occurred. Stay in 4C: passage-specific applicability, conditions, source admission, genuine reviews and additive import remain before 4D or Step 5. Counts of parser blocks, selected passages and expansion sections are not interchangeable.

Earlier execution checkpoint: [Step 4D preflight](MAYA-STEP-4D-PREFLIGHT-RESULT.md), 16 September 13:08 UTC. At that point production embedding eligibility was zero and no corpus embeddings existed. The subsequent explicitly approved development path is recorded above; it did not grant production eligibility.

Latest milestone: [Step 4A execution and critical findings](MAYA-STEP-4A-SOURCE-PREPARATION-AND-CRITICAL-FINDINGS.md). This records 9,192 retained review words in 56 sections, 79 passing tests plus 30 subtests, and a fresh local import recheck. See F01–F11 there for specific content/integration catches; they are not all fixed by source preparation.

## 1. How to use this document

- This is the execution tracker. The detailed product contract remains [Maya intended product experience and data-flow specification](MAYA-INTENDED-PRODUCT-EXPERIENCE-AND-DATA-FLOW-SPEC.md).
- These are **local implementation steps**, not a renumbering of the historical project Stages 0–10. Passing an old stage's fixture tests does not complete a local live-integration step.
- Keep earlier reports as historical evidence. Their old statements such as “empty database” must not override later import results.
- Update this roadmap after every milestone: status, actual changes, evidence paths, unresolved issues and exact next action. Do not mark work complete from a plan, code presence or passing mock tests alone.
- A new handoff is input to this sequence, not permission to replace the current repository, UI, database or source history.
- Changes to the accepted product behaviour or architecture must be explained to Kajal before implementation. Never silently substitute a smaller product and call it complete.

## 2. What is established and what is not

The following is based on the existing reports inspected for this roadmap. This documentation task did not rerun Docker, database tests, live provider calls or browser journeys.

| Area | Recorded state | Important limit |
|---|---|---|
| Step 1 — baseline | Current UI/source checkpoint and targeted baseline checks recorded | That checkpoint predates subsequent work; create a fresh checkpoint before further mutations |
| Step 2 — infrastructure | Local Supabase, provider generation/embedding smoke tests and real-vector database round trip recorded as working | Non-medical test vectors do not establish corpus RAG; account availability can change |
| Step 3 — import | Real recovered draft corpus imported; rollback, repeat safety, exact-field comparison and role isolation checked | Draft import is neither publication nor a live chatbot |
| Step 4 — development indexing | Authorised 96-record development admission and real embedding/indexing verified in the linked 4C/4D report | Production publication, held content and broader evidence coverage remain incomplete |
| Actual imported knowledge | 14 sources, 72 retained source blocks, 55 draft chunks, 56 guidance fragments, 63 draft weekly profiles and 54 preserved review decisions | 46 profiles have no linked evidence; broader applicable guidance may exist, but coverage must be tested |
| Permissions/reviews | 53 candidates have a recorded source-level embedding permission; 2 from BHC-WEEKS do not | Under the existing production approval rule, zero candidates currently qualify; permission and content approval are different |
| Publication | Zero published releases in the inspected readiness report | Do not silently promote drafts or represent them as approved health guidance |
| Additional text | 12 local supplemental text derivatives, approximately 11,060 whitespace-counted words before cleaning | Includes boilerplate and potentially overlapping text; not 11,060 words of reviewed guidance |
| Historical missing bodies | 986 parsed blocks were counted; 72 bodies retained; 914 other bodies were not recovered | No retained proof that all 914 bodies were saved. Do not call newly extracted text an exact historical recovery |
| Dashboard/chat | Existing UI, adapters and backend components are present | Complete browser-to-retrieval-to-answer behaviour is not yet demonstrated |

The previously quoted 11,061-word supplemental count and this approximately 11,060-word count differ with tokenisation. Neither is a coverage or quality measure.

Evidence references:

- [Step 1 baseline](MAYA-IMPLEMENTATION-STEP-1-BASELINE.md)
- [Step 2 infrastructure](MAYA-IMPLEMENTATION-STEP-2-LOCAL-INFRASTRUCTURE.md)
- [Step 3 corpus import](MAYA-IMPLEMENTATION-STEP-3-CORPUS-IMPORT.md)
- [Step 4 readiness and decision](MAYA-STEP-4-INDEX-READINESS-AND-DECISION.md)
- `reports/local/corpus-indexing/readiness-20260916T105254844629Z.json` — database/import recheck and eligibility inventory, timestamped 10:52 UTC on 16 September.

## 3. Intended product: decisions we must preserve

### Onboarding

1. User arrives on the existing landing page and chooses Begin your journey.
2. Select pregnant or postpartum; collect a preferred name only as the existing experience requires.
3. Pregnancy timing uses week, month **or** due date. Postpartum uses delivery date or elapsed time. These are alternative timing inputs, not requirements to supply all three.
4. Resolve timing on the server, preserve precision and show the interpretation. Month-only input remains approximate. Resolve real conflicts with one relevant question.
5. Optional diet preferences, allergies, symptoms, activity background and restrictions become shared context. Preserve relevant free text; distinguish unanswered from explicitly none.
6. Review/edit details, then open the dashboard without needing documents or an account.
7. Editing context refreshes affected sections and marks old plans as needing refresh.
8. Refresh begins a fresh journey as agreed. Server session expiry/cleanup must match this behaviour; browser refresh alone is not proof that server-held information has been deleted.

No default week 26, hidden symptoms, fictional prescriptions or carried-over facts. No document uploads, login or workspace-creation flow in this scope. No feature may require those excluded inputs.

### Four overview cards and journey visuals

| Section | What users see | Source and method |
|---|---|---|
| Your journey | Confirmed week/trimester, approximate month or postpartum timing | Deterministic timeline calculation, not an LLM |
| Nutrition focus | Two supported nutrient highlights and a short explanation | Versioned pre-authored stage/week catalogue with evidence references and context rules |
| Energy focus | Supportive self-care theme, a possible stage-related experience and a practical action | Same sourced catalogue; not a prediction of personal mood, hormones or energy |
| Movement focus | Supported activity/recovery theme with relevant adaptations | Same catalogue plus restriction rules; never infer “heavy exercise” from week alone |
| Journey visual | The agreed trimester/progress design, plus appropriate postpartum treatment | Same resolved timeline; no independent UI date calculation |
| Growth at a glance | Existing mapped baby/comparison images and sourced typical measurements | Fixed week library with units/conventions; no model-generated values or claims about this baby's actual measurements |
| Baby-development fact | One compact fact below measurements in the Growth card | Sourced weekly/range lookup; preserve existing measurement/image data |
| Maternal fact | One compact common-change/self-care fact inside Your Journey | Sourced weekly/range lookup; not a new KPI or inferred personal symptom |

Overview cards and standard FAQs make **no runtime LLM, embedding or vector-search call**. Several weeks can legitimately share a stage-level entry. Actual values still need source verification; approving the card design did not approve uncreated medical content.

Growth images remain balanced medium size, with the agreed short professional info note. No fetal comparison is presented as a postpartum infant measurement. Missing assets or measurements are identified, not silently replaced with another week.

### Detailed dashboard sections

| Section | Required information | Constraints and exclusions |
|---|---|---|
| Nutrition | Focus summary; protein, iron, calcium and other supported nutrients; why they matter; applicable general intake references; practical food choices; symptom adaptations; food safety; sources | Match diet and allergies. Do not assume deficiencies or supplement use, change prescriptions, or claim a supplement removes the need for food guidance |
| Movement | Overview; supported aerobic, strength, mobility/posture, pelvic-floor and recovery categories; practical options; modifications; stop/help guidance; sources | Use actual restrictions, symptoms and activity background. Week alone cannot determine exercise suitability |
| Symptoms | Actual reported symptoms, separately labelled stage education, supported comfort information, cautions and appropriate escalation | No invented symptoms or diagnosis; urgent concerns must not be normalised as ordinary stage changes |
| Wellbeing | Supportive self-care, rest/social support, optional check-ins and responses to expressed concerns | No guessed mood, mental-health diagnosis or forced positivity |
| FAQs | Nine pregnancy-month sets, six or seven stored Q&As per month, expandable immediately with sources and Ask a follow-up; separate postpartum sets | Stable within each month; shared explicit timeline mapping; local constraint variants only, no runtime generation. Typical development is not a personal assessment |
| Do's and don'ts | Concise food, movement and everyday-care guidance, explanations/alternatives and links to detail | Same evidence and relevant constraints as the main tabs; no myths or contradictory restrictions |
| Plans | Only plans explicitly requested by the user, organised by day/week with revision and refresh state | Not an automatic onboarding output. No invented supplements, appointments, numerical adequacy or medical clearance |

The dashboard shows useful guidance before anyone asks for a plan. A user who supplies only a timeline still receives supported general information. Personal context adapts relevant content; not every fact affects every category.

### Ask Maya

- Use the same current onboarding context, relevant conversation history and corpus as the dashboard.
- Answer the actual question through live retrieval and the existing appropriate specialist/orchestration components; no scripted fixture fallback.
- Support follow-ups, explanations and explicit nutrition/movement/combined plan requests where evidence supports them.
- Validate source support, allergies, restrictions, numbers and output shape; citation presence alone is insufficient.
- Show sources accessibly and explain relevant adaptations naturally.
- Preserve constraints during “make that vegan” or “change Tuesday” revisions.
- Route urgent concerns appropriately. Ask targeted clarifications only when necessary for the requested advice, without blanking unrelated information.
- Never claim to have read documents that were not uploaded, or ask users for passwords/API keys.
- Persist requested plans within the current isolated session and show them in Plans. Explain that a fresh session will not retain them.

## 4. Architecture and information flow

We retain the existing architecture. The work is to populate, connect and verify it, with any required extension explicitly documented.

```text
SOURCE TRACK
Existing recovered text + permitted originals/new captures
  -> clean and parse using existing ingestion components
  -> anchored passages + applicability + permissions + review/version records
  -> idempotent database import
  -> eligible real embeddings + existing full-text/semantic retrieval
  -> verified, versioned evidence store

USER TRACK
Landing -> onboarding -> server-resolved, isolated, versioned user context
  |
  +-> timeline calculation + fixed growth library -> journey/growth
  |
  +-> sourced weekly/stage catalogue + rules -> four cards + baby/maternal facts
  |
  +-> shared month mapping / postpartum stage -> stored standard FAQ sets
  |
  +-> category request / Ask Maya question + relevant history
        -> urgent/scope handling
        -> eligible evidence retrieval using timeline and relevant context
        -> existing specialist/orchestration and structured generation
        -> evidence, citation and constraint validation
        -> existing dashboard / chat / explicitly requested plan
```

Source authoring supplies references to both the deterministic catalogue and live evidence path. The catalogue is genuine pre-authored content, not a fake live answer.

Reuse the existing PostgreSQL full-text, pgvector, ranking/fusion and bounded graph facilities where applicable. Verify required graph tables/relationships and call paths separately; do not claim graph retrieval works merely because the code exists. Do not introduce a second vector database, new agent framework or undocumented provider path for convenience.

Personalisation has two parts: retrieve applicable evidence **and** enforce user constraints on proposed output. An allergy is not merely an extra search keyword. Broader pregnancy/trimester evidence must remain available when exact-week evidence is unnecessary.

## 5. One ordered implementation sequence

### Steps 1–3 — retain completed foundation

**Status: recorded complete within scope; not to be rebuilt.**

Preserve the existing UI/source baseline, local infrastructure and transactional corpus loader. Before new mutations, check service identity, current import integrity and a fresh checkpoint of uncommitted work. Do not reset Docker volumes, start old duplicate containers sharing volumes, replay destructive setup or replace the repository with a teammate snapshot.

### Step 4A — clean available text and measure actual coverage

**Status: EXECUTED for the current 12-file handoff.** See the Step 4A report for coverage limits, source-binding limitations and reproducible outputs. Re-run reconciliation when new 4B material arrives; do not treat this as complete clinical coverage.

1. Inventory the 12 supplemental derivatives and existing retained blocks against manifests; preserve originals unchanged.
2. Identify source/page/heading anchors, capture/version identity, extraction quality and recorded allowed uses.
3. Remove boilerplate, navigation and duplication in derived working outputs; retain traceability to the unmodified originals.
4. Produce a coverage matrix: pregnancy stages and supported weeks/ranges, postpartum ranges, nutrition, movement, symptoms, wellbeing, development, FAQs and plan-supporting content.
5. Classify each cell: supported with evidence IDs; broad-stage support; partial; missing; permission/review unresolved. Never count empty profiles as content.
6. Separate fact/reference tables from passages suitable for retrieval. Review numeric units and applicable populations explicitly.

**Completion evidence:** source manifest, cleaning/exclusion log, representative passage checks, coverage matrix and prioritised acquisition list. Do not promise complete coverage based on word or chunk counts.

### Step 4B — receive/reacquire missing sources, in parallel

**Status: handoff received and verified.** The final recovery ZIP supplies three reproduction documents but no new source text/binaries. The four originals remain withheld under recorded restrictions; the other 914 bodies were never persisted according to the sender's investigation. Source acquisition/scope decisions remain open where needed, but another identical export is not required.

- Prioritise the four reported exact originals: `nhm-cho.pdf`, `nhm-motherhood.pdf`, `nhs-active.html`, `pib-pmsma.pdf`, subject to permitted transfer/use.
- Receive any existing broader parsed/OCR outputs, missing extraction instructions, new source/code/review deltas and account-continuity information.
- Verify every delivered checksum and source identity; distinguish exact originals from changed captures.
- Where historical bodies were not retained, use permitted re-extraction/reacquisition. New source versions and new passages do not inherit old approvals automatically.
- Existing ingestion uses selected evidence/pages. Simply rerunning the unchanged command is not proof that all missing text becomes useful chunks. Expand selection/authoring deliberately and test the resulting coverage.
- If material remains unavailable, record the impact and source alternatives. Do not wait indefinitely or infer that inaccessible material is essential to every feature.

**Completion evidence:** supplied/missing/restricted register and source-version reconciliation. Merge useful additions into 4A/4C; never overwrite validated current records or restart the whole project.

### Step 4C — expand the evidence set and resolve use/review boundaries

**Status: development admission VERIFIED for the selected eligible subset; full production scope remains IN PROGRESS.** A 46-unit authoring packet exists. The authorised private development lane now contains 43 expanded sections plus 53 existing passages. Three broader selections remain held; no production candidate/publication review was fabricated. See the current execution report for unresolved applicability, conditions and release work.

1. Use existing ingestion/authoring contracts to create meaningful, source-anchored passages with stable identifiers, hashes, topic, pregnancy/postpartum applicability, week/range and jurisdiction metadata.
2. Version new/changed material, deduplicate and retain the 54 valid exact-version decisions already imported.
3. Reuse the loader; test repeat imports, conflict rejection, rollback and provenance for additions.
4. Identify who can resolve each outstanding review. Distinguish source permissions, editorial/product review, clinical review and localisation; do not pretend one substitutes for another.
5. Keep BHC-WEEKS out of embedding batches under its current recorded restrictions. A restricted source can only use its allowed delivery mode.

**Decision resolved:** Kajal explicitly approved development indexing separate from publication on 16 September. Reference `Kajal-development-indexing-not-publication-20260916`. The private development extension is implemented; it does not authorise clinical approval or publication. Do not ask for the same development approval again.

**Completion evidence:** versioned candidate inventory, source/review eligibility matrix, import verification and recorded decision for any development-only extension. Product release requires the applicable outstanding decisions, not a blanket bypass.

### Step 4D — create real corpus embeddings

**Status: VERIFIED for the authorised 96-record development batch.** Real text-embedding-3-small vectors (1,536 dimensions) are stored privately, with source/model/usage receipts, rollback, conflict, repeat-safety and role-isolation checks. This does not establish production publication or semantic retrieval quality.

- Use the existing hardened provider client and verified configuration; confirm model/dimensions before loading.
- Batch eligible text with checkpointing, bounded retries, budget accounting and idempotent resume. Do not re-embed identical text unnecessarily.
- Store model, dimensions, text hash, source/chunk/version and execution provenance. Do not mix fixture vectors or incompatible models/dimensions.
- Distinguish transient failures from authentication, quota and permission failures. Stop on the latter and report the actual reason.
- Preserve source/review status and protect any development-only index from ordinary user endpoints.

**Completion evidence:** actual provider request metadata/usage, eligible-text-to-vector counts, dimension/content-hash checks, database verification and unchanged results after resuming/repeating work. A mocked test or old non-medical vector probe is insufficient.

### Step 5 — verify retrieval and connect the shared runtime

**Status: VERIFIED WITHIN PRIVATE BACKEND SCOPE. Real hybrid retrieval, normal chat/plan API routing, bounded live specialist generation, validation and isolated session context are connected and exercised. Browser activation, complete category integration, richer planning and broad chat acceptance remain later integration work, not proven by this milestone. See the runtime report for 5/6 full live cases followed by the corrected 2/2 targeted rerun and the two existing UI-test failures.**

1. Exercise the existing full-text/semantic retrieval gateway on real passages, including ranking/fusion and bounded graph behaviour where supported.
2. Test stage/range, topic, jurisdiction, source status and release filters; retain useful broader-stage evidence.
3. Prove queries return supported passages, source anchors and traceable scores/identifiers. Separate operator development results from publishable retrieval.
4. Connect runtime configuration, generation, specialist routing and validation behind the existing API. Inspect the normal path for unconnected/fixture adapters; no hidden fallback is allowed.
5. Establish one server-owned session/context contract shared by every endpoint. Never trust a browser-supplied identity to access another session.
6. Give callers distinct outcomes: evidence gap, review restriction, provider failure, invalid context, necessary clarification and urgent concern.

Carry-forward findings F06–F08, reconciled: the normal API now has a real private operator runtime; activity/restriction fields exist at the API boundary, but full UI collection still needs integration; detailed dashboard categories still need their live evidence connection. Do not describe the private backend as unconnected, or infer that the browser is activated merely because the backend tests pass.

**Completion evidence:** real API-to-retrieval traces, positive/negative query set, constrained-output checks, isolation tests and clear configuration showing which path executes. Do not claim completion from a standalone SQL query.

### Step 6 — complete onboarding, overview, nutrition and movement

**Status: planned integration; reuse the current UI.**

- Finish context resolution, optional inputs, review/edit, fresh-session behaviour and stale-response protection.
- Start with the controlled local browser connection to the existing real runtime. Keep provider/operator credentials server-side and preserve the development/publication boundary; test the actual UI, not only an in-process API client.
- Author/verify the four-card catalogue and applicable growth/timeline mapping. No personal mood forecasts, arbitrary nutrient rotation or invented measurements.
- Preserve the current growth measurement library. Add sourced weekly/range baby facts below its measurements and maternal facts inside Your Journey; these and the four cards use deterministic data with no runtime model/vector calls.
- Reconcile the obsolete growth-card source-text tests with behavioural coverage for the current library, source/estimate info and absence of unwanted internal review labels. Do not restore rejected wording or delete tests simply to obtain a green run.
- Connect Nutrition and Movement to real applicable evidence and current constraints; display practical detail before a plan request.
- Keep categories independently loadable with summary-first cards, expandable detail/sources, loading, retry and specific error states.
- Make card actions open matching detail sections; keep the overview and detailed advice consistent.

Carry-forward finding F02: source and dashboard trimester boundaries differ. Resolve the product convention and verify boundary mappings before presenting combined results. Do not alter source text to hide the difference.

**Completion evidence:** actual browser journeys for early/middle/late pregnancy and postpartum; no optional context; vegetarian/vegan preference; peanut allergy; reported backache/restriction; context edits. Confirm absent symptoms are never invented. User-readable content must come from the eligible release, not a quietly exposed draft lane.

### Step 7 — complete symptoms, wellbeing, FAQs and do's/don'ts

**Status: planned; content preparation can overlap earlier work.**

- Fill each section to the product contract in section 3.
- Separate reported symptoms from general educational topics.
- Build nine pregnancy-month FAQ sets, each with **six or seven stored questions and answers**, including sourced typical-development topics. Use one explicit tested month mapping for week/due-date inputs, preserve month-only precision, and provide separate postpartum-specific content.
- Apply relevant deterministic FAQ variants/exclusions without a generation call; personal follow-ups enter Ask Maya.
- Validate cross-section consistency and source support; retain unrelated useful sections if one category fails.

**Completion evidence:** expandable answers, meaningful stage-appropriate question selection, no inference of personal symptoms/mood, contextual do's/don'ts, source links and zero model/vector calls for standard FAQ expansion.

### Step 8 — connect Ask Maya and requested plans fully

**Status: planned; not deferred out of the product.**

- Connect the existing chat UI to the verified runtime and server session history.
- Route supported questions to the existing relevant specialists and plan-composition logic. Record which components actually execute; do not claim unused agents participate.
- Preserve scope for record-dependent capabilities: no medication-record/report specialist may invent uploaded inputs in this upload-free phase.
- Test normal questions, multi-turn follow-ups, dietary changes, genuine urgent concerns and questions with inadequate evidence.
- Create explicit requested plans, display them in Plans, revise named days, preserve constraints and mark stale plans after edits.
- Treat retrieved documents and user text as data, not instructions that override system boundaries; test prompt injection and secret requests.

**Completion evidence:** unscripted live traces for answers and revisions, checked citations/claims, retained relevant history, allergy/restriction enforcement, request-only plan creation, no cross-session leakage and no fixture fallback.

### Step 9 — integrated evaluation and presentation checks

**Status: planned; tests are also added continuously in Steps 4–8.**

Run the matrix in section 8 across the real browser/API/database/provider path. Include cold starts, retries, changed context, concurrent sessions, partial outages and content gaps. Record what passed, failed and was not tested.

Preserve the light-default design; verify responsive layouts, readable text/units, keyboard access, source expansion and visible Ask Maya. Do not redesign unrelated screens.

**Completion evidence:** linked test results plus real end-to-end traces, a concise gap register and a separate verdict for engineering readiness and user-facing content readiness. No promise of “perfect” follows from a green fixture suite.

### Step 10 — package and deploy after local acceptance

**Status: later, not part of this documentation task.**

- Choose the actual frontend/backend/database hosts and obtain appropriate access. Local Docker working is not hosted deployment.
- Configure backend-only secrets, database migrations, eligible content/vector transfer, frontend API URL, HTTPS, allowed origins, timeouts and health checks.
- Verify backups and a real restore rehearsal, release rollback, rate/cost controls, session expiry and privacy-conscious monitoring.
- Verify the hosted product from a separate browser/device independently of either laptop.
- Retain source attribution, truthful data-handling information and an operating/runbook handoff.

No Git push, hosted migration, public release or deployment is authorised merely by creating this roadmap. Confirm the target and scope when those actions are requested.

## 6. Parallel work without losing the sequence

| Workstream | Can begin now? | Where it rejoins the plan |
|---|---|---|
| Local source inventory/cleaning/coverage | Yes | 4A -> 4C |
| Aswath recovery, deltas and account continuity | Yes, independently | 4B -> 4C; later deployment access -> 10 |
| Test design and context/API contract review | Yes, without pretending live integration is complete | 5–9 |
| Catalogue/FAQ schema and coverage mapping | Yes; actual answers must be sourced and reviewed | 6–7 |
| Real corpus embedding | Only after eligibility/authorisation is resolved | 4D |
| Public health-guidance delivery | Only for appropriately cleared, supported content | 6–10 |

Here “parallel” means these tasks need not wait on each other; it does not authorise extra autonomous agents or a competing implementation. Keep one source inventory, one context contract and one content-version authority.

## 7. Dependencies and decisions register

| ID | Dependency/decision | Owner/action | What it blocks |
|---|---|---|---|
| D1 | Draft development-index exception versus existing approved-only path | Kajal explicitly decides the development scope; preserve publication restrictions | Embedding review-required passages, not source cleaning |
| D2 | Missing originals / broader extractions | Aswath supplies existing permitted assets or explicit unavailable status; local reacquisition where permitted | Only coverage dependent on those assets |
| D3 | Content, permissions, clinical and localisation review gaps | Appropriate owners provide real version-bound decisions | Relevant public content release; not all unrelated engineering |
| D4 | Continued provider account access and remaining shared budget | Confirm Aswath's authorised project, spend and support route | Paid calls if credentials/quota fail; no new key is inherently required |
| D5 | Intended audience and supported timing coverage | Use current product/source configuration; surface conflicts or unsupported ranges for Kajal | Claims beyond verified applicability |
| D6 | Deployment target/access | Kajal chooses hosts; invitations where teammate-owned accounts are used | Hosted release only |

Recorded provider caps remain $30 OpenAI and $5 xAI separately until revoked. They are not a claim of current remaining credit. Keep a local usage ledger and reconcile shared-account spending; never expose credentials in chat, reports, Git or frontend variables.

## 8. Required acceptance matrix

Each case needs expected behaviour, actual result, evidence reference and pass/fail/not-tested status. Predetermine expectations from the product contract and sources; do not rewrite them merely to fit observed behaviour.

| Test group | Required cases |
|---|---|
| Timeline | Pregnancy weeks 6, 12, 26 and 36; supported boundaries; invalid/out-of-range input; approximate month; due date; postpartum delivery date; conflicting input |
| Context | No optional answers; explicit none; vegetarian; vegan; peanut allergy; free-text preference; reported symptom/restriction; edit after response starts |
| Content | Broad guidance still retrieved; meaningful early/middle/late/postpartum applicability; no invented weekly changes; empty-profile and missing-evidence cases |
| Overview/FAQ | Correct deterministic mapping, no model/vector calls, source references, stored expandable answers, no personal mood or fetal-health claims |
| Nutrition/movement | Relevant adaptations across dashboard/chat/plans, supported numbers/units, no excluded ingredients or ignored restrictions, no automatic plan |
| Retrieval | Real stored vectors/passages; source anchors; eligibility and jurisdiction filtering; ranking; restricted/draft exclusions; graph path separately verified where used |
| Chat/plans | Follow-up context, corrections, multi-turn revision, requested plan storage, day-specific edits, stale plan marking, citations that support claims |
| Safety | Urgent concern routes correctly; benign requests receive useful information; ambiguity affects only relevant advice; prompt injection cannot override boundaries |
| Reliability | Database/provider outage, quota/rate failure, timeout, partial category failure, retry, zero hidden fixture substitution |
| Privacy | Two independent sessions, refresh/new session, expired state cleanup, context-keyed caches, no keys/health text in unnecessary logs or frontend bundles |
| UI | Existing design preserved, light default, mobile/keyboard usability, readable measurements, clear loading/errors, working source/FAQ expansion |
| Deployment | Separate hosted checks, migrations, eligible corpus/vector counts, secrets, HTTPS/origins, health checks, backup/restore and rollback |

An evaluator using the interface is still a user. Do not expose uncleared content or describe simulated answers as live retrieval just because the session is an evaluation.

## 9. How to handle gates without blocking the whole product

- Keep genuine urgent-care handling, privacy, source permissions and applicable publication checks.
- Fix configuration/routing failures instead of disguising them as medical uncertainty.
- Missing optional symptoms or diet details must not block general guidance.
- Missing one precise answer must not blank every category; show the supported portion and the specific limitation.
- Use focused clarification only when a recommendation genuinely depends on the missing detail.
- If a current check is redundant or incorrectly implemented, document its purpose and test a correction. Do not delete all checks simply to obtain output.
- Never publish pending records, invent clinical approval or substitute fixture text to make a screenshot appear complete.

## 10. Milestone update template and resume instructions

After each milestone, append an entry here or link its report:

```text
Milestone ID and date:
Status: not started / in progress / verified within scope / blocked
Actual files or data changed:
Tests actually executed and result paths:
Live calls versus mocked tests:
Evidence/release/context versions:
Provider usage and cumulative budget:
Remaining defects and external decisions:
Exact next milestone/action:
```

When resuming after a restart or context loss:

1. Read this roadmap, the intended-product specification and the latest linked milestone report.
2. Inspect the current working tree; preserve all uncommitted work.
3. Recheck required service availability and stored import/version state before relying on historical reports.
4. Resume the next incomplete substep. Do not repeat paid jobs/imports blindly; use stored checkpoints and hashes.
5. If new evidence changes status, update the register explicitly without rewriting historical results.

## 11. Current handoff and exact next action

**Current milestone:** authorised development admission/indexing completed for 96 records, followed by real private hybrid retrieval and the Step 5 runtime/session/specialist-generation/validation integration. The subsequent Step 6 checkpoint connects the local browser, four static overview cards, monthly FAQs and baby/maternal facts, with one live generated/cited answer verified through the UI. Continue the remaining category integration and fuller chat/plan acceptance tasks; do not mark the entire product complete. Preserve the original public corpus and all review decisions. Three expanded-source holds and production applicability/conditions/release work remain explicit; private execution does not grant publication. The development-index exception has been approved and executed, not left pending.

**Step 4B dependency:** verified as a documentation-only handoff; there is no pending full-code or embedding transfer to wait for. Reconcile genuinely new source/permission material if later supplied.

**Do not lose these later commitments:** eligible real embeddings -> verified retrieval/runtime -> context-connected overview and nutrition/movement -> symptoms/wellbeing/FAQs/do's and don'ts -> Ask Maya and requested plans -> complete end-to-end tests -> deployment.

**Step 4A execution record:** cleaned derivatives and audit reports were generated under ignored local reports; original payloads were preserved. No new content approval, production-corpus import, provider call, database mutation, UI change or deployment occurred. The linked report—not the existence of this plan—is the execution evidence.

Success is a coherent, evidence-backed product: onboarding provides the context, the corpus provides traceable knowledge, the dashboard provides useful guidance, and Ask Maya provides grounded conversation and requested plans. Completion must be demonstrated through the actual user path.
