# Maya AI: normal-user content and RAG routing plan

Status: implementation plan, not a claim that live content is already released. This document is for the existing React UI at `http://localhost:5173/`. It does not authorize a merge, push, deployment, or the publication of unreviewed medical guidance.

## What is broken today

1. Onboarding captures the journey and optional diet, allergy, and symptom context in `api/main.py`, but the React experience calls `/v1/demo/*` in `frontend/lib/maya-api.ts`. Refresh begins a new browser journey; the backend's in-memory session is not a durable private user record.
2. `/v1/demo/chat` and `/v1/demo/plan` call `run_compass()` in `app/services/product_experience.py`. That function constructs a request through `scripts/stage7_fixture_support.py`. The real `PostgrestRetrievalRepository` and `RetrievalGateway` in `app/services/retrieval.py` are not instantiated for this UI path. A passing fixture evaluation therefore does **not** prove a real user can retrieve the actual corpus.
3. Dashboard cards use `released_weekly_cards()`, which correctly needs published source, fragment, and profile status. The 63 weekly profiles are drafts; inspected P05, P06, and P26 are empty coverage shells. Thus a missing week-specific nutrition or movement card is not merely a frontend rendering problem.
4. `scripts/build_publication_readiness.py` hardcodes clinical and India-localisation review to pending, sets every profile's `publication_eligible` to false, and asserts zero published profiles/comparisons. Historical verification code also expects zero. These permanent-zero assumptions must become evidence-derived release checks. Changing a test expectation alone is not a content approval.
5. The available Supabase schema/RLS verification is not proof that the teammate's remote database contains an active, actually published, week-complete release. A server-side generation provider and usable key have not been verified in this local environment.

## The intended one-user journey

Landing page -> new, anonymous session -> onboarding with chosen pregnancy/postpartum position and optional confirmed/reported context -> dashboard for that position -> source-linked weekly tabs -> Ask Maya and plans using the same context. Document upload is **optional and out of scope for this first routing fix**. No fictional symptoms, allergies, appointment, or record may be silently inserted. A refresh should return to the blank journey, as requested, without exposing another session's context.

The UI must not manufacture an exact week from an approximate month/due-date range. The backend should preserve the timing source and range, and either render guidance valid for the whole range or ask for an exact week only when a more specific claim needs it.

## Which gates change, and which remain

| Check | Decision | Reason |
| --- | --- | --- |
| `/v1/demo/*` and fixture-request default for normal users | Replace with real `/v1/*` session/home/chat/plan service | Fixtures are evaluation tools, not the production answer source. |
| Hardcoded `published_profiles == 0`, `publication_eligible = false`, and unconditional review-pending values | Replace with checks derived from actual signed review/source records and active release | A completed review must be able to release approved content. Historical zero-state tests can remain as baseline fixtures, not live assertions. |
| Full-profile gate for every individual tab | Review granularity: release independently approved, source-linked domain fragments where the data model supports it; do not require an unrelated comparison or empty domain to block another approved domain | A baby-size comparison should not suppress separately approved nutrition guidance. If schema only supports profile-level release, extend schema/RPC deliberately and test it. |
| Entire-dashboard clarification stop for a nonurgent reported symptom | Remove | Keep the report as context; clarify only for the specific unsafe request that actually needs more detail. |
| Source reuse/licence, currency, material health-content review, India localisation where claims are local, provenance, RLS, urgent-symptom routing, allergy exclusion, unsupported-claim rejection | Keep and make them narrow and visible in traces | Removing these would create unsupported or unsafe personalized claims, not a functioning RAG product. |
| No released evidence for a requested claim | Do not fill with model memory or fixture text | Show a specific evidence gap for that claim; other released tabs should still load. |

## Implementation order

### 1. Establish the actual release truth

- Inventory coverage by stage/week/domain: pregnancy P01-P42 and postpartum PP01-PP12, each with source spans, fragment text, review decision, and allowed use. Identify empty shells and absent nutrition, movement, symptoms, well-being, FAQ, and growth fields. The existing 56 fragments do not automatically provide complete content for all 63 profiles.
- Obtain the **actual** approved content and review records from the teammate's workspace. Record reviewer role/name, item IDs, decision, date, source locator, licence/reuse and currency, localisation scope, and release version. Do not infer approval from a prior handoff or set `published` manually for an empty shell.
- Refactor the readiness builder to compute eligibility from those records. Separate independent domains and comparison eligibility. Remove permanent zero assertions from the live path; retain regression tests that a truly draft profile stays hidden and a legitimately approved fragment becomes visible.
- Create a versioned active release in Supabase and verify the public/full-text/vector/weekly-profile RPCs return the intended approved candidates for at least two materially different weeks and one postpartum position. Check P05 and P26 specifically rather than just a source count. If data/reviews are missing, this is a content-production task, not an API toggle.

### 2. Replace the fixture path, not the React design

- Add a normal API service that instantiates `PostgrestRetrievalRepository` with Supabase URL, publishable key, a **user-scoped access token**, corpus version, and active release ID; wrap it in `RetrievalGateway`. No service-role key goes to the browser. The existing Stage 5 RPCs include `stage5_public_full_text`, `stage5_public_vector`, `stage5_weekly_profile`, and authenticated/personal-context RPCs.
- The user requested no visible login. If user-scoped Supabase access is required, use invisible anonymous Auth only after reviewing RLS and anonymous-account cleanup. Supabase anonymous users use the `authenticated` database role; a public anon key by itself is not a private user identity. For the initial local flow, keep input in the current session until this access model is safely configured.
- Create `/v1/session`, `/v1/onboarding`, `/v1/home`, `/v1/chat`, and `/v1/plan` (or an equivalently named normal route). Change only the React API adapter to call these; retain the designed landing/onboarding/dashboard components. Fixture endpoints remain separately available for tests, never as a fallback in the normal route.
- Fail startup or the affected request clearly if release/database/provider configuration is absent. Do not silently substitute `FixtureRetrievalRepository`, `make_stage7_request`, or controlled canned provider text.

### 3. Use one trusted context envelope everywhere

The same server-validated envelope must reach dashboard selection, chat retrieval, specialist agents, and plan validation: journey state, exact week or honest range, timing source, jurisdiction, confirmed diet, confirmed allergies, user-reported symptoms (not diagnoses), constraints/limitations, active release ID, and session subject. User text is data, not an instruction to override safety or source rules. Unknown fields stay `not_provided`; they are never replaced with sample facts.

- Dashboard: retrieve released weekly/domain fragments and growth/comparison items for the position. Render short week-specific guidance and source links. Apply deterministic exclusion/annotation for confirmed allergies and diet preferences **before** displaying food examples; do not trust the model as the only filter. Movement suggestions with a symptom that changes safety require narrower safety handling, not generic high-intensity advice.
- Ask Maya: run urgent/symptom routing first; retrieve approved public evidence with position/domain filters; combine the confirmed context and evidence packet; dispatch only the relevant bounded agent(s); validate factual claims against evidence and constraints before display. A general question should not trigger a global clarification wall.
- Plans: compose a seven-day schedule from eligible agent suggestions, then independently verify each entry against week/range, diet/allergy, reported restrictions, clinician-provided context if present later, and evidence provenance. Reject only unsafe/unsupported plan entries and explain the exact limitation; avoid a server error or an empty fixture schedule.
- FAQ: use released question-answer items or source-linked retrieved answers, expanding in the existing UI. A clickable unanswered placeholder is not an FAQ.

### 4. Test one complete real-data slice before expanding

Run one vertical integration round using a genuinely reviewed and released slice. Minimum cases: no optional context at P05; Vegetarian plus Peanut at P26; Vegan if the UI offers it; an ordinary backache report without a dashboard-wide stop; an urgent reduced-movement message that routes to prompt clinical care rather than routine exercise advice; an approximate month range; and a postpartum position. Verify tab text, evidence IDs/locators, allergy filtering, chat, weekly plan, and no 500s. Negative tests: no cross-session/user data under RLS, no fixture evidence/provider in normal trace, no unsupported weekly measurements or medical claims, no invented symptoms, and refresh returns to blank onboarding.

Only after this slice passes, expand coverage week/domain by week/domain. Track visible coverage and the exact reason for every missing tab; do not use a global `public_release_available: false` when some independent domains are genuinely released.

## Information needed before live wiring can finish

The teammate should provide, through local configuration or a secure handoff rather than chat: the Supabase project URL and publishable key; whether anonymous Auth is enabled and its RLS policy review; active release UUID/corpus version and remotely verified approved candidate counts by week/domain; reviewer decision records and source registry; and a chosen server-side generation/embedding provider with working credentials. No passwords, service-role keys, or health records should be pasted into GitHub or this document.

If those release facts are not available, we can implement/test the **routing contract** locally, but cannot honestly claim the dashboard already gives complete, approved, source-grounded guidance for every week. The way forward is to finish content and release a reviewed slice, not to weaken the evidence gate or disguise a fixture as live RAG.
