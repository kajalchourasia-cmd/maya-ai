# Maya AI: complete the no-document onboarding and weekly experience

Status: live implementation tracker, based on the current local UI-integration checkout. This is not a claim that the product is already production-ready. Do not push or merge until Kajal reviews the implementation and test evidence.

Implementation update (local, unpushed): the four-step no-document onboarding now reaches the dashboard with week 26, Vegetarian, Peanut, and Back ache selected. A balanced weekly plan without a document returns HTTP 200 and a visible schedule; if a symptom is selected, movement is omitted instead of giving exercise clearance. The nutrition worker filters tagged fixture food candidates marked incompatible with a selected vegetarian preference or reported allergen and shows both applied constraints in a relevant food answer. The dashboard now records the week and selected constraints in its cards and loads source-linked cards **only** from published weekly profiles. The care-record step is absent from onboarding and the care-record tab is deferred/nonblocking. The backend suite and React TypeScript check passed; the same four-input journey and plan were checked in the actual browser. This is still **fixture-backed**, not released week-specific medical guidance or production private-data processing.

Further local correction (unpushed): the React app was automatically restoring a persisted test session, which explained why refresh could jump straight to week 26. Browser storage and startup restore were removed; a refresh now stays on Landing until explicit onboarding. In the browser, week 6 with no optional inputs reached a week-6 dashboard. A mobile CSS rule hid all dashboard tabs; tabs are visible again and the FAQ tab now expands with direct, profile-aware product answers instead of routing every question to safety chat. A dedicated Plans tab can build a plan and focused card actions move there; clicking the nutrition card was checked in the browser. The no-constraint fixture plan no longer fails on missing schedule metadata; the API and browser now produce a **controlled-fixture** schedule rather than a server error. Week 6 and 26 show source-linked **general** NHS length references with their measurement basis. The wider length/weight table remains unverified and is not displayed. All 547 backend tests, the React TypeScript check and an optimized webpack production build pass after these corrections. None of these changes establishes live week-specific clinical content or authenticated real-health-data handling.

Current verdict: **GO for local UI/contract testing only; NO-GO for public real-health-data use or a claim of complete week-by-week advice.** The exact blocker is not the week selector. `P06`/`P26` and other weekly profile shells are drafts and the repository reports 0 published profiles. The plan/chat route uses synthetic evidence whose fixture applicability is aligned to the entered journey for testing; that is not genuine week-6 or week-26 sourced advice. The comparison planning series has values but no clinical measurement/source review; only separately source-linked general week 6/26 lengths are now displayed. A clinical/content reviewer, licence/localisation review, approved weekly fragments and ingredient metadata, and the teammate's authenticated live-provider/storage integration are required before removing the controlled-fixture boundary.

## The decision

Defer medical-record upload, extraction, and appointment-from-document features. Remove the record step from the normal onboarding path for now. A mother should complete onboarding with a journey position and any food preferences, allergies, and reported symptoms she chooses to provide, then reach a useful dashboard without a document. Do not substitute a fictional prescription or appointment for a missing record. Do not claim that a document was processed.

Keep urgent maternal warning handling. Do **not** make a broad, unclassified symptom a mandatory onboarding clarification dead-end. Recording a symptom is different from diagnosing it or prescribing an exercise/treatment response. If a symptom may alter the safety of a plan, the response must respect that uncertainty; an urgent warning must still interrupt ordinary guidance.

## What exists today, and what is broken

| Area | Current behavior in this checkout | Required result |
| --- | --- | --- |
| Onboarding inputs | Week/month/due date, diets, allergies and symptoms are sent to `api/main.py`; context is built without a record too. | Preserve these inputs; make the record step absent or clearly optional and nonblocking. |
| Offered symptoms | Fixed locally: a nonurgent reported symptom no longer blocks Home; the Stage 6 classification remains visible in API metadata and urgent input still blocks. | Keep symptom handling meaningful in each tab and answer without inventing a diagnosis or exercise clearance. |
| Weekly plan button | Fixed locally: the partial full-plan route now validates, and the full plan omits Follow-up when no relevant record or appointment exists. No-record week-26 plans return HTTP 200. | Replace fixture content with source-released, week-specific contributions and retain regression coverage. |
| Dashboard tabs | Fixed locally in part: cards now reflect the resolved week and recorded inputs; `app/services/dashboard_content.py` selects and attributes published weekly fragments only. No actual week 6/26 health cards can display because those profiles are empty unpublished shells. | Populate, clinically review, license and publish the week-specific source content, then verify all domain cards and condition filters. |
| Nutrition constraints | Fixed for the current tagged fixture candidates: Peanut and Vegetarian are both applied before and after the worker boundary and appear in relevant outputs. Free-text/unknown ingredients and the draft real food catalogue are not yet guaranteed. | Enforce compatibility against verified ingredient/allergen metadata for the actual released catalogue, including free-text aliases and unknown-ingredient fail-closed behavior. |
| Ask Maya | React currently calls the deterministic Demo Mode adapter; a passing fixture answer does not establish live grounded generation. | Connect to a selected, authorized retrieval/generation route; cite released evidence and avoid unsupported personal medical claims. |
| Persistence | The React adapter keeps sessions in memory. | If this is to be a real product, add authenticated durable profile/context storage with privacy controls; do not accept real health information into the demo session store as a production substitute. |

## Implementation order

### 1. Make onboarding useful without documents

1. Remove the example-record screen from the main journey or replace it with a single `Skip records for now` transition. No fictional supplement, fictional appointment, or record KPI should appear for a user who skips it. Preserve week/month/due-date/postpartum resolution and the timeline ring.
2. Persist each entered item with its correct type and provenance: Vegetarian and other diet choices as preferences; Peanut and other reported allergens as avoidance constraints; symptoms as **user-reported**, not clinically confirmed facts. Normalize case/synonyms and reject contradictory diet entries rather than silently ignoring them. Do not assume an allergy is diagnosed merely because the user selected it; still avoid it in food suggestions.
3. Separate `can_open_dashboard` from `can_give_symptom_specific_guidance`. A generic, nonurgent symptom may be saved and the dashboard opened without a clarification form. For an urgent warning, show the existing urgent next-step message and stop ordinary plan/chat generation. For uncertain symptoms, provide week-appropriate general information only and no unsupported diagnosis, medication change, or exercise clearance.
4. Confirm that a no-record user at week 6 or 26 reaches Home, all tabs, Ask Maya, and the plan screen. The user must be able to edit journey and constraints later; changing week or allergy should invalidate cached cards/plans.

### 2. Fix the weekly-plan failure before adding more plan content

1. Reproduce the HTTP 500 with no record, week 26, Vegetarian and Peanut. Add an API regression test for this exact case and the symptom-selected case.
2. Fix the Stage 7 **partial execution** contract explicitly. A stopped full-plan contributor prefix is not an ordinary one-specialist route; represent it as a valid partial full-plan outcome while retaining worker order, evidence-plan order, call budget, stop reason, and trace. Do not weaken the rule for ordinary, non-plan requests or pretend Plan Composer ran.
3. Return a typed status to React: `completed`, `partially_available`, `needs_review`, or `safety_stopped`, with a plain-language reason. Disable save unless a validated proposed schedule exists. Display an honest retry/unavailable state instead of a raw server error.
4. Verify day and week horizons and nutrition, movement, wellbeing, and balanced focuses. A week plan should use the exact week or an explicitly marked month range, user availability, allergies/restrictions, diet, reported symptoms, and recorded appointments **only when actually supplied**. No invented prescription/supplement/dose or appointment date.

### 3. Make diet and allergy constraints deterministic

1. Define structured food tags and a diet compatibility matrix for the nutrition candidate catalogue. Vegetarian must exclude meat/fish/poultry candidates; egg/dairy semantics must follow the exact selected preference, not guess. Allergy exclusion must cover ingredient aliases and cross-reference tags. If ingredient data are insufficient, omit the candidate rather than asserting it is safe.
2. Apply the same filter before displaying a nutrition card, before emitting Nutrition Agent contributions, when composing a weekly plan, and when Ask Maya answers a food question. The model should never be the sole enforcement layer.
3. The answer should visibly say, when relevant, `I considered your vegetarian preference and reported peanut allergy` and show any limited evidence/uncertainty. It should not repeat that sentence on unrelated questions.
4. Regression tests: week 6 and 26; Vegetarian alone, Peanut alone, both together, no constraints, conflicting preferences, and unknown ingredients. Assert that no prohibited food candidate appears in cards, plans, or relevant chat output.

### 4. Replace generic tabs with released week-aware content

1. Use the existing governed source registry, extracted evidence, authored profiles and fragment audit—not new unsourced AI prose. Map each content fragment to supported pregnancy weeks or postpartum interval, domain, jurisdiction/conditions, required safety caveats, source/evidence IDs, and release status. An approximate month must remain a week range; do not pretend it is exact week 26.
2. Start with explicit week 6 and week 26 end-to-end acceptance slices, then cover every supported week and postpartum interval before claiming complete week-by-week guidance. Week specificity must be substantive, not just a changed heading or a copied generic paragraph. The Do's/Don'ts, nutrition, movement, wellbeing/self-love, symptom education, preparation/FAQ, and baby-size editorial card each need their own eligibility and evidence checks.
   The current `P06` and `P26` records are empty `coverage_shell` drafts. Selecting those weeks alone cannot produce a trustworthy nutrition or movement answer from the authored corpus. Author and review those slices first; then expand coverage without treating a template sentence as week-specific content.
3. Add a governed content-selection service/API. For eligible reviewed fragments, return exact week, domain, wording, citations, conditions, exclusions, limitations, and review provenance. Filter and rank for the current context. If no fragment is released for a domain/week, give an honest unavailable state; do not secretly show an `awaiting_specialist_review` draft as health guidance.
4. Request qualified clinical, licence, India-localisation, and product publication review for actual health content. The repository currently says 63 authored profiles but **0 published**, and 42 comparison review records but **0 display-eligible clinical comparisons**. Kajal's recorded product/content approval of an editorial size sequence is not a clinical measurement or artwork licence approval. Resolve those gates rather than deleting their labels.
5. Every personalized claim or contraindication should have source spans and the necessary context condition. Do not infer that a general pregnancy activity is safe for a person reporting back pain, dizziness, bleeding, reduced movement, or clinician restrictions. Medication and supplements remain record-only unless a clinician directs them.

### 5. Connect Ask Maya and the plan composer to the same context and evidence

1. Use one normalized context snapshot for Home, cards, specialist agents, Plan Composer, and Ask Maya. Confirmed allergy avoidance is hard; diet preference is an enforceable compatibility constraint; symptom is reported and safety-relevant; clinician instructions, when eventually available, override ordinary plans.
2. Run retrieval only against released, license-permitted evidence. Select and configure a real generation/extraction provider separately; the current fixture provider is test-only. Do not label fixture sentences as a live model response. Preserve Stage 6 urgent handling, Stage 7 specialist boundaries, orchestration budgets, evidence/claim checks, and Stage 8 evaluations.
3. Plan Composer should coordinate the agents without duplicating incompatible meals or movement suggestions. Show a seven-day layout, optional/rest items, constraints applied, citations, and reasons when an item could not be safely offered. Support regenerate and user edit, then save only after validation and user confirmation.
4. Evaluate with fixed context fixtures and adversarial prompts: peanut + vegetarian food question; unknown allergy ingredient; week 6 versus week 26; ordinary reported symptom; urgent symptom; password/API-key request; nonexistent document/appointment; prompt injection; unavailable evidence; approximate month. Report actual pass/fail and examples, not just aggregate green tests.

### 6. Make a clear production boundary

The local API in `api/main.py` exposes `/v1/demo/*`, synthetic context and an in-memory session store. That architecture cannot be relabeled as an end-to-end private health product by removing a banner. Before accepting real health data or deploying for public use, add authenticated user ownership, private durable storage, consent and deletion/export paths, secret management, abuse controls, logging without sensitive content, configured live retrieval/generation, clinical publication review, and a deployment/privacy assessment. Real document upload remains a separate later project: authenticated file handling, malware scanning, secure extraction, explicit fact confirmation, appointment extraction and state lifecycle. It is not needed to prove the no-document flow.

## Ownership of the remaining work

Codex in this local workspace can implement and test the React/API orchestration, constraint handling, governed source selection and UI integration. The teammate who controls the Supabase environment and provider credentials should configure the authenticated release repository, live retrieval/generation provider and deployment secrets; no credential should be sent in chat or committed. A qualified clinical reviewer must sign off the specific week/domain health claims and safety conditions, and a product/licence reviewer must clear wording, localisation and reuse. Those decisions cannot be replaced by passing fixture tests or by changing `status: draft` to `published`. Document upload can remain out of this release.

## One-round verification and handoff

Run the existing Stage 6–8 and API suites plus browser tests on the **same integration branch** (including prior local UI changes). Exercise the actual React page, not just internal Python fixtures. Capture request/response status, screenshot or short recording, displayed week, constraint values, card evidence IDs, and the plan trace for each case below:

| Test journey | Must be true |
| --- | --- |
| Week 6, no document, no optional constraints | Dashboard and chat accessible; week 6 content only if released; no invented record/appointment. |
| Week 26, Vegetarian + Peanut, no document | Dashboard accessible; diet/allergy visible; relevant nutrition cards, chat and plan have no incompatible foods; plan endpoint never returns 500. |
| Week 26 with `Back ache` selected | Symptom is retained; no generic onboarding dead-end; no unsupported exercise clearance; urgent checker still active. |
| Urgent symptom phrase | Urgent route and professional next steps shown; ordinary personalized plan/chat stopped. |
| Month 6 instead of exact week | Week range displayed; no exact-week claim, comparison, or plan falsely attributed to week 26. |
| Change allergy or week after a plan | Old plan/cards invalidated and recomputed under the new context. |
| Ask for a made-up appointment or supplement | Maya does not invent one when no record was supplied. |

Deliver: changed-file list, exact branch and commit, test commands/results, failed cases with root cause, screenshots, source/review status per displayed claim, explicit `GO/NO-GO` for internal testing and separately for **public real-health-data release**. Do not push, merge, or deploy without Kajal's approval.

## Grounding references

Project evidence: `api/main.py`; `frontend/app/maya/onboarding.tsx`; `frontend/app/maya/dashboard.tsx`; `app/schemas/orchestration.py`; `app/services/orchestration.py`; `app/services/agents.py`; `app/services/product_experience.py`; `README.md`; the governed source and authored-profile records in `data/`.

External safety/content sources for the review team, not permission to publish unreviewed personal advice: [CDC urgent maternal warning signs](https://www.cdc.gov/hearher/maternal-warning-signs/index.html), [ACOG exercise during pregnancy](https://www.acog.org/womens-health/faqs/exercise-during-pregnancy), [NHS week-by-week pregnancy guide](https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/), and [WHO antenatal care guidance](https://www.who.int/publications/i/item/9789241549912).
