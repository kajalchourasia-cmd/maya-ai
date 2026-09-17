# Maya — Step 5 real retrieval and orchestration checkpoint

16 September 2026 · Kajal's local system

**Historical retrieval-only checkpoint.** The subsequent [runtime integration report](MAYA-STEP-5-RUNTIME-INTEGRATION-VERIFICATION.md) records the real normal-API/private-operator generation connection and later verification. Preserve the evidence below, but do not use this older runtime status as the current status.

**Verdict: real private retrieval is implemented and its initial engineering benchmark passes. Full Step 5 is NOT complete. The normal API, personalised generation and dashboard/chat are not connected by this change. No publication or clinical approval was granted.**

This report separates actual execution from code existence and fixture tests. It follows the authorised development scope: `Kajal-development-indexing-not-publication-20260916`.

## What now runs for real

```text
Fixed synthetic question + explicit test context
          |
          v
Real OpenAI query embedding (same model/dimensions as the corpus)
          |
          v
Local PostgreSQL: 96 source-bound records + 96 real pgvector embeddings
          |
          +--> PostgreSQL full-text ranking
          +--> pgvector cosine search
          |
          v
Stage / complete timing interval / topic / known jurisdiction / condition filters
          |
          v
Shared reciprocal-rank fusion + known-overlap suppression
          |
          v
Private operator results: original passages, URLs, locators, hashes and scores
          |
          X  NOT published / NOT passed to user-facing generation
```

The query questions are synthetic test inputs. Their embeddings, the source passages, database search and retrieval scores are real. No fixture answer or deterministic vector provider participates in this run.

### Implementation

- `app/services/development_retrieval.py`: operator-only hybrid retrieval; validated request contract, read-only transaction, five-second SQL statement timeout, source-integrity checks, filtering before ranking/limit, explicit review/metadata flags and citations.
- `scripts/maya_step5_retrieval.py`: reproducible benchmark with expectations saved before provider/search execution, bounded paid-call ledger, exact query/model/corpus-bound vector cache, actual corpus verification and permission checks.
- `app/services/retrieval.py`: reciprocal-rank scoring extracted as a shared primitive. Production eligibility rules are unchanged. The private search does not pretend its records meet the production gateway's published-evidence contract or its authenticated-user contract.
- `app/services/orchestration.py`: extracted the existing identity-free route-planning core for reuse in diagnostics. Normal worker execution still performs its existing identity/safety/evidence validation.
- `app/services/safety_gate.py` and specialist intent keywords: fixed ordinary food/nutrition/protein/calcium/exercise recognition. Urgent matching still runs first; current symptom examples remain on the safety path. No safety specification was promoted to published.
- `tests/test_development_retrieval.py`: boundary and regression tests, explicitly distinguishing synthetic unit doubles from live evidence.

No new database service, public endpoint, public RPC, database migration, frontend redesign or permission bypass was introduced.

## Executed results

| Check | Actual result |
|---|---|
| Corpus before search | All 96 stored records and vectors match the Step 4D packet/cache and receipts |
| Provider | One real HTTP 200 OpenAI embedding call; `text-embedding-3-small`, 1,536 dimensions |
| Usage | 157 tokens; estimated USD 0.00000314; reservation USD 0.01 |
| First database run | 19/19 predeclared engineering cases passed |
| Repeat database run | 19/19 passed, same ranked IDs; zero new provider calls |
| First-run search latency | Approximately 325–463 ms per case, including local Docker/psql overhead; excludes the batched query-embedding call |
| Database permissions | Nine denial checks passed: anon, authenticated and service_role cannot read the three private development tables |
| Original public corpus | Before/after snapshot unchanged; no approval, release or public embedding writes |
| Generation | Zero generation calls; no user-facing answers or plans produced |

The API key was neither printed nor put in a report. Shared provider-account balance was not independently checked. The estimate uses the existing embedding rate; it is not an account invoice or a whole-product cost estimate.

Provider request ID: `req_56c404772a5d456e924f36ef51dc57c0`.

Evidence directory:

`reports/local/step5-retrieval/f99ddd72c235119d24e424fe38215e62b3a05ec64013f390d4a7a0c11cb6589b/`

- `predeclared-cases.json`
- `query-provider-ledger.json`
- `query-vectors.json`
- `verification-20260916T135614659012Z.json` — first live run
- `verification-20260916T135852562061Z.json` — cached repeat

Corpus packet: `8ad39c36af0425cf527102a22ea798c5b16ce347bf49fc5d57430d844b5cbed0`.

The embedding request format follows the [official OpenAI embeddings reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create). The model was not changed.

### What the 19 cases actually demonstrate

Source retrieval was checked for food washing, plant protein, leafy-green iron, hydration, exercise consultation, development at weeks 24 and 36, early/late symptoms, postpartum activity with missing/present/excluded conditions, breastfeeding diet and postpartum emotional support. Additional cases checked strict jurisdiction filtering, an unrelated question, SQL-like question text, approximate timing and an unsupported possible-pregnancy nutrition request.

Week 24 and week 36 returned their corresponding development passages and rejected the other week's passages. A known postpartum movement restriction excluded the narrower conditional gentle-exercise record. A 24–28-week interval did not silently become exact week 24. SQL-like input remained encoded data. No irrelevant answer was generated for empty cases.

**19/19 is not 100% answer accuracy.** This small engineering set was authored with knowledge of the corpus. Some cases test exclusion/empty results rather than positive relevance. It does not measure clinical correctness, exhaustive allergy safety, every pregnancy week, every postpartum condition, citation entailment of generated answers, or independent evaluator performance.

## Important catches — still open

1. **Retrieving information is not the same as recommending it.** The vegan protein case retained the vegan/peanut context, but its source candidates included animal/dairy passages. That context was not yet applied to a generated answer because there is no generation in this path. Existing structured-food filters can be reused, but real retrieved prose must also pass constraint-aware synthesis and output validation. Do not label this test as “vegan/allergy-safe answers verified.”
2. **Expanded source conditions are not fully structured.** A broader postpartum exercise section can still be retrieved when a narrower exercise record is excluded. It carries `conditions_unresolved_not_unconditional`, and every hit has `eligible_for_generation=false`. Sending these passages directly into advice would bypass the unresolved conditions; do not do that.
3. **Broad-stage evidence is not exact-week evidence.** Pregnancy-wide hydration content remains available across weeks. It is marked broad-stage rather than presented as a unique weekly prescription. Some approximate-interval requests produce no relevant result in this limited corpus.
4. **Unknown jurisdiction is not localisation approval.** Unknown expanded metadata remains flagged; strict-known-jurisdiction mode excludes it. Existing draft India tags remain provisional, not clinically approved localisation.
5. **Ranking is preliminary.** Several top-five lists contain broadly related but unnecessary passages. The semantic noise threshold of 0.30 is an engineering starting point, not a calibrated support/confidence threshold. More independent queries, precision checks and claim-level support validation remain.
6. **Graph retrieval has not been demonstrated here.** No verified development graph is present. The result reports that explicitly; it does not invent graph paths or causal explanations. Existing bounded production graph code remains to be exercised with real authorised graph data.
7. **The normal runtime still returns `UnconnectedProductRuntime`.** There is no real normal-API-to-retrieval-to-generation trace yet. Existing dashboard reference content was not replaced with RAG content in this step.
8. **No-login session integration remains a real contract task.** The current production orchestration contracts expect authenticated stored context. Private development testing does not fabricate that identity for ephemeral user sessions. Server-owned session context, activity/restriction fields, expiry/isolation and context-version propagation still need wiring and tests.
9. **Production review work remains.** All 96 development records remain unpublished; the safety specification is draft. Three broader source sections remain held and two embedding-prohibited passages remain excluded. Nothing in this step converts development permission into permission to publish unreviewed guidance.

## Orchestration: built, reused, but not fully connected

The repository already contains deterministic safety routing, specialist selection, eight bounded workers, a plan composer, budgets, timeouts and validation. This step reuses and tests its routing core; it does not replace it with a new agent framework.

Real routing diagnostics, without generation, show:

- Ordinary food and protein questions now reach the nutrition route instead of unnecessary safety clarification.
- An explicit nutrition-and-exercise weekly plan selects nutrition, movement and plan composer.
- An urgent bleeding example selects no ordinary worker.
- A current symptom still removes movement from a combined plan, regardless of that symptom's relevance. This remains too coarse for the intended experience and requires a context-specific decision, not removal of all safety checks.
- A non-plan food-and-exercise question still triggers multi-intent clarification. The intended UX needs bounded handling of supported multi-topic requests.

These diagnostics use the existing draft safety specification's explicit evaluation mode. They are not clinical approval and do not prove specialist generation is connected. No default fixture provider was invoked.

## Regression status

The targeted retrieval/orchestration/safety/cross-stage run passed 201 tests and 262 subtests before the additional cache test. The final complete suite produced **737 passed, 2 failed, 315 subtests passed**, with six dependency deprecation warnings. The two failures are frontend text-contract mismatches, documented below; the full project is not all-green. A separate comparison of both real retrieval reports confirmed identical hit order in all 19 cases and zero new provider calls on the repeat.

The failing tests inspect existing frontend files, not this turn's retrieval code:

- `MayaProductUiRestorationTests.test_only_source_linked_general_measurements_enter_dashboard`: expects the older `generalWeekMeasurementReferences`/measurement copy; the current dashboard uses `getGrowthMeasurements`.
- `MayaProductUiRestorationTests.test_review_state_is_visible_per_week`: expects older “Product direction accepted” / “Product review pending” copy that is absent from the current dashboard.

Those expectations must be reconciled against the accepted growth-card specification and source references, not simply deleted to obtain a green result. This step did not change the UI or weaken those tests.

## Exact next work — stay within Step 5

1. Finish a truthful runtime/evidence contract for the no-login, ephemeral session path. Retain the separate private-development and published lanes; never label real private sources as fixtures or published evidence to satisfy a schema.
2. Connect the normal API to the existing safety, retrieval, specialist and validation chain under the correct lane. Distinguish setup failure, evidence gap, review restriction and actual safety clarification. Add real API-to-retrieval traces, not only operator SQL traces.
3. Exercise real structured generation in an explicitly bounded development path; validate source support and diet/allergy/restriction constraints, and prove there is no fixture fallback. This report does not assert authorisation to publish those outputs.
4. Resolve the coarse movement/multi-intent routing behaviour with positive and negative regression cases. Preserve urgent precedence and never invent missing personal facts.
5. Establish source applicability/conditions and publication readiness separately. Do not ask Kajal to impersonate a clinician or mark five review roles approved.
6. Re-run the normal API path, failure handling, session isolation and constrained-answer tests. Only then mark full Step 5 complete and move to Step 6 dashboard integration.

**No additional Aswath laptop access or new key was needed for the retrieval work verified here.** A working retrieval engine is now demonstrated locally. That is meaningful progress, but not a complete working dashboard/chatbot, and it must not be reported as one.

No Git commit/push, hosted change, deployment, UI change, or user-facing publication occurred in this step.
