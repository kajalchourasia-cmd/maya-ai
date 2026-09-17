# Maya — Step 5 runtime integration

16 September 2026 · Kajal's local system

## Scope and verdict

The missing runtime connection is implemented. The normal `/v1/chat` and `/v1/plan` routes can now execute real retrieval, source-backed specialist generation and answer validation in the **private operator development lane**. They do not call the fixture answer adapter.

This is not a published clinical product, a completed dashboard integration, or a complete meal/exercise planner. The existing approval explicitly separates development from publication; this change preserves that distinction. The ordinary browser session is **not silently enabled for unpublished guidance**.

GO to the next local integration work, using this runtime and its verification evidence. NO-GO for claiming the whole intended product is complete or ready for unrestricted health use.

## Actual path

```text
Existing onboarding
  -> ephemeral session + HttpOnly capability cookie
  -> immutable week/range, stage, diet, allergy, symptom and restriction snapshot
  -> normal /v1/chat or /v1/plan
  -> existing deterministic safety check (urgent response before database/model use)
  -> existing Stage 7 router and specialist catalogue
  -> real OpenAI query embedding
  -> existing local PostgreSQL FTS + pgvector + rank fusion
  -> stage / interval / topic / conditions / source-integrity checks
  -> incompatible nutrition passages excluded without modifying original sources
  -> real specialist generation from original passages and user context
  -> deterministic schema, citation and constraint checks
  -> separate live model support/context check, selecting backend-owned source spans
  -> constrained composition: only statements passing every check survive
  -> normal API response with citations, provenance and execution receipts
  -> session conversation history / requested educational outline
```

No fake query vectors, fixture answers, invented medical records, default user symptoms, or fabricated source approvals participate in the live verifier.

## What was reused, and what changed

| Component | Actual implementation |
|---|---|
| Corpus and embeddings | Reuses the 96-record private index and existing 1,536-dimensional vectors; no corpus re-embedding |
| Retrieval | Reuses `OperatorDevelopmentRetrieval`, source checks, PostgreSQL FTS, vector search and reciprocal-rank fusion |
| Safety | Reuses Stage 6; its specification remains evaluation-only, not clinically approved |
| Orchestration | Reuses `plan_route` and `definition_for`; adds an explicitly bounded multi-domain educational route |
| Specialists | New real generation execution uses the existing domain roles/prohibitions. The old workers' fixture-oriented deterministic drafts are not passed off as genuine model answers |
| Provider | New bounded Responses API path receives the question, current context and source passages. The older summary-rewrite adapter remains separate |
| Validation | New truthful private-development contract, citation binding, food exclusions, named-food/nutrient checks, separate live semantic checking and exact backend-selected spans. This is **not** a claim that the legacy published-evidence Stage 8 validator ran unchanged |
| Plan composition | Deterministic composition of validated educational contributions. It does **not** call the old timed ScheduleBuilder with invented availability or appointments |
| Session context | Actual user-entered ephemeral context, not a fictional authenticated Supabase identity |

These are explicit runtime extensions to the existing architecture, not proof that every historical agent/tool/graph path is connected. Record-upload and medication-record features remain excluded as agreed. No verified graph is present in this development index.

## Session and API behavior

- The same onboarding snapshot feeds both chat and plan calls.
- Pregnancy week/range and postpartum stage are retained; month uncertainty is not silently converted into an exact week.
- Additional API fields can carry restrictions, relevant conditions and activity background. Their collection/presentation in the full UI still needs the next integration phase.
- Conversation history stays in memory, limited to four previous user/assistant pairs. Assistant text is not promoted to a user fact or source document.
- A follow-up can refer to an earlier user question. This is bounded history, not a complete long-term memory system.
- Requested outlines are available at `/v1/plans/{session_id}`. Editing onboarding clears history and the outline and increments the context version.
- A result is discarded if context changes during generation; duplicate simultaneous turns for one session are rejected.
- Session UUIDs alone cannot read another session. Cookies are HttpOnly, SameSite Strict, and responses use `Cache-Control: no-store`.
- Sessions expire after one hour and expired entries are pruned. Refresh creates a new browser journey; it does not promise immediate deletion of the prior server-memory entry.
- Product sessions cannot enter legacy fixture routes. Demo sessions cannot be promoted to product sessions through onboarding.
- Database failure, provider authentication/rate failure, missing evidence, invalid output, safety and review restriction have separate error codes.

The cookie changes required two isolation tests to use separate browser clients. Their original assertions about independent user data remain; cross-session access is now explicitly denied. The two unrelated growth-card tests were not rewritten to manufacture a green suite.

## Problems caught during real execution

1. **Model-copied quotation failed exact matching.** Citations now attach original backend-owned passages. The support checker selects exact source-span IDs instead of generating quotations.
2. **Dairy recommendation appeared for a vegan test profile.** It was blocked. Nutrition evidence is now conservatively filtered before generation, with output checks still applied afterwards. Mixed passages may also be excluded; this loses some recall and is not a complete allergy ontology.
3. **An iron/leafy-vegetable claim cited the wrong paragraph.** Manual inspection caught a false positive from the earlier model checker. A named-food/nutrient citation regression and stronger support checks were added. Earlier successful HTTP results are not treated as proof that their content was correct.
4. **One unsupported extra statement hid an otherwise supported answer.** Composition now omits failed statements rather than exposing them or automatically discarding independently validated statements. Omissions are recorded and disclosed.
5. **A model returned an unrequested outline in a multi-domain question.** Only the explicit user request can activate the composer; the unrequested outline is discarded and every remaining answer claim still has to pass validation.
6. **The old follow-up label accidentally triggered the appointment/follow-up agent.** Query construction no longer injects that routing keyword.
7. **Ordinary category wording collided with symptom ambiguity.** A narrow, complete category-education phrase is recognised; current reduced-movement wording is still stopped and regression-tested.
8. **An eager runtime dependency could have contacted Docker before urgent handling.** Initialisation is now lazy. Urgent HTTP responses do not need a working database or provider.

No validation was replaced with unconditional success. There is at most one bounded content repair per turn, and its replacement is checked from scratch. There are no automatic provider/network retries.

## Verification evidence

The live verifier is `scripts/maya_step5_runtime.py`. It creates synthetic user profiles but uses genuine database rows, OpenAI embeddings, model generation and a separate model verification request. It does not override the normal API runtime dependency or substitute provider responses.

Latest full six-case run: `reports/local/step5-runtime/verification-20260916T145204327139Z.json`.

- Vegan/peanut-constrained protein question: passed.
- Contextual iron follow-up: passed.
- Requested seven-day nutrition outline, including session storage: passed.
- Movement question: passed.
- Instruction-injection question: passed.
- Multi-specialist question: stopped on an unsolicited model outline. The defect and correction are described above; see the targeted rerun checkpoint below.

Do not describe that historical run as 6/6. Earlier failed reports are retained in `reports/local/step5-runtime/`.

Every completed live verifier run also checks:

- another browser cannot read the session;
- missing private-operator access is denied;
- urgent handling makes zero ordinary generation calls;
- product sessions cannot enter fixture routes;
- context edits invalidate the stored outline;
- all 96 real vectors still match the index;
- nine database role-isolation checks pass;
- the original public corpus snapshot is unchanged.

Additional offline tests exercise provider failures, wrong citations, forged span IDs, unsupported claims, food exclusions, session expiry, concurrent requests, stale state, plan boundaries and context propagation. Test doubles in these tests are explicitly labelled and are not counted as real generation proof.

### Final checkpoints

- Targeted final live rerun: `reports/local/step5-runtime/verification-20260916T145500300939Z.json` — **2/2 passed**. Both nutrition and movement produced validated contributions; the injection case returned a sourced answer without credentials. Five isolation checks, nine database-role checks, vector integrity and unchanged public-corpus checks passed again.
- Final targeted offline suite: **127 passed + 55 subtests**, in `reports/local/step5-runtime/targeted-final.xml`.
- Final full regression: **768 passed, 2 failed + 315 subtests**, saved as `reports/local/step5-runtime/regression-final.xml`. The remaining failures are the two pre-existing growth-card expectations listed below; no new failing test remains from this runtime change.
- Frontend TypeScript: `tsc --noEmit` passed. Whitespace check passed using the explicit repository path. Browser visual/end-to-end verification was not performed in this step.
- Provider ledger: **106 completed provider requests across debugging and verification**, estimated **USD 0.194973** at the pinned undiscounted token prices. These include query embeddings, generation, content repairs and separate validation calls; they are not 106 user scenarios. The conservative held/spent ledger total is USD 0.624005 under the USD 1 integration ceiling, because earlier completed reservations were not retroactively released. Actual account billing/balance was not independently inspected.
- No new provider credentials were needed. No secrets were copied into the UI, report, Git, or source files.
- A scoped secret-pattern scan of seven edited/new runtime, API, frontend, test and report files found zero matches. This is not an exhaustive repository security audit.

These are engineering results, not a medical accuracy rate. Some earlier runs failed; one apparently passing result failed manual citation inspection. Those reports remain available rather than being overwritten by a clean-looking summary.

## What this does NOT finish

1. **Public activation:** no published corpus exists. Private operator execution is not permission to publish these answers.
2. **Browser experience:** the running UI server was not restarted or silently switched to live unpublished generation. A controlled local UI connection and browser end-to-end testing remain.
3. **Dashboard categories/KPIs:** this change does not replace the current dashboard reference cards with complete week/category retrieval. That is the next integration step.
4. **Detailed planning:** the returned seven-day object is an educational outline assembled from supported statements, sometimes repeating them. It is not a varied meal menu with portions, a nutritionally calculated plan, or a full exercise programme. Those need richer structured content, composition rules and tests.
5. **Complete chat coverage:** symptom clarification, postpartum scenarios, wellbeing, general baby-development questions, multi-turn preference updates and targeted day editing need a broader acceptance matrix. A few passing examples do not establish coverage of every question.
6. **Evidence completeness:** unknown jurisdiction/conditions and broad-stage evidence are still flagged. The conservative nutrition filter can exclude useful mixed-source passages. No synthetic weekly specificity was invented.
7. **Clinical confidence:** generation and semantic checking use separate calls to the same model family. Their errors can be correlated. Automatic support checks are not medical review; this run itself demonstrated why manual auditing remains necessary.
8. **Production infrastructure:** this private implementation uses local Docker and single-process in-memory sessions. It is not a hosted multi-worker/session-store deployment. Cross-site deployment needs an intentional HTTPS/session/CORS design.
9. **Two existing UI test failures:** growth-measurement imports/labels and per-week review-copy expectations still need reconciliation with the current UI specification. They must not be hidden.

## Operating boundary and reproducibility

- Use the existing local Docker/Supabase instance and backend `.env`. No new provider key is required for this private runtime.
- Never put `OPENAI_API_KEY` or `MAYA_OPERATOR_TOKEN` in `NEXT_PUBLIC_*`, browser code, reports or Git.
- `MAYA_RUNTIME_MODE=private_development` plus a strong `MAYA_OPERATOR_TOKEN`, a loopback client and `X-Maya-Operator` authorise private generation. The verifier sets these only inside its own process; it does not edit `.env` or the running server.
- Private development still returns `publication_eligible: false` and preserves the source review status.
- The model is the existing `gpt-5.4-mini`; query embeddings use the existing `text-embedding-3-small` and 1,536 dimensions.
- `store: false`, fixed provider endpoint, no HTTP redirects, bounded context/output, and a durable USD 1 integration reservation ceiling are enforced. This is inside the pre-existing authorisation, not a new account balance guarantee.
- Successful requests reconcile reservations to estimated usage at the pinned rates. Failed/uncertain calls retain reservations. Receipts contain request IDs, usage and model IDs, not keys or user health text.
- No hosted database, publication status, GitHub branch or deployment was changed.

From the repository root, with its local dependencies available:

```powershell
python -B scripts/maya_step5_runtime.py --execute-authorized-development --all
```

On this machine the execution used the bundled Python executable with `.local-api-deps` inserted into `sys.path`; use that same environment rather than reinstalling a second dependency stack. Running the verifier makes bounded paid requests; do not run it repeatedly without a reason.

## Next implementation order

1. Preserve this verified backend seam; do not reconnect the summary-only fixture adapter.
2. Connect the existing dashboard's nutrition and movement presentation to typed, context-bound data; finish sourced KPI/FAQ tables without fabricating week-to-week differences.
3. Provide a controlled local browser test path with clear private-development access. Verify onboarding → context → API → citations → chat/outline on the actual UI.
4. Build the detailed planner and expanded chat acceptance cases, including symptoms, postpartum, wellbeing, omissions and updates.
5. Resolve source/publication review and production-state requirements before unrestricted release; finish hosted privacy, session isolation and deployment checks.

The next phase should improve the real user experience, but it must not turn these engineering checks into a claim that every agent, week, health scenario or deployment has been completed.
