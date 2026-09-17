# Maya local integration progress

## Available to test

- Updated frontend: http://127.0.0.1:5180/
- Updated API: http://127.0.0.1:8010/healthz
- Older API at port 8000 reported `controlled_demo`; do not use it to judge these changes.
- Refresh the updated frontend to start blank onboarding. No upload is required.

The running processes are local development servers, not deployed services. They must be restarted after they exit or the computer restarts.

## Changes made without the teammate's corpus

1. Normal frontend chat and plan requests now use `/v1/chat` and `/v1/plan` rather than `/v1/demo/*`.
2. Normal sessions cannot enter legacy fixture chat, plans or sample-document mutation routes.
3. Added a typed, versioned session-context boundary containing resolved journey, diet, allergies and symptoms. This is explicitly user-entered session context, **not** an invented authenticated Supabase identity.
4. Both normal request handlers accept that same context. Contract tests confirm the values reach the injected runtime boundary. No hosted runtime is bound yet.
5. Missing corpus connection returns a named setup error (`corpus_not_connected`), not a clinical safety block, generic server error or fictional answer. Retrying endlessly is not suggested for this known setup issue.
6. Urgent chat routing uses the existing safety service without needing the corpus/model. Corrected its input-channel mapping to `chat_message`.
7. Session-expiry recovery triggers only for actual missing-session responses, not every HTTP 404.
8. Frontend error handling displays structured validation errors legibly.
9. Chat display history survives dashboard navigation within the current page session. Editing onboarding clears outdated conversation content. Refresh starts fresh. This is UI history preservation, not a claim of model conversational memory.
10. Late chat responses are not appended after leaving that chat component. Sample-context labelling was removed from the normal chat's applied-constraints label.
11. An isolated Next.js build directory permits side-by-side testing. The local dependency junction required webpack rather than Turbopack for this instance.

## Browser verification performed

Using a clearly named test session, completed all four onboarding steps, selected pregnancy week 26, Vegetarian and Peanut, and left symptoms empty.

- Timeline preview showed week 26 and second trimester.
- Dashboard showed the selected timeline, nutrition focus, movement focus and growth references.
- Nutrition showed source-linked protein/iron/calcium/folate sections and vegetarian food examples.
- Movement showed activity, strength/posture and position/comfort sections.
- Ask Maya's ordinary question returned the explicit missing-library error, not fixture text.
- Returning to the dashboard and reopening chat preserved that question and error once.
- No document upload or sample record was required.

The dashboard content here is the existing local source-linked educational catalogue, **not the transferred original RAG corpus**. This browser test does not establish that hosted retrieval, allergy-aware model generation or full weekly planning works.

## Automated verification

Focused retrieval, dashboard, demo API and new runtime integration suite: **99 tests passed, 202 subtests passed**, one dependency deprecation warning. TypeScript checking passed before the isolated server generated additional type-directory entries.

New tests cover session isolation, mandatory onboarding, exact context forwarding, context revision changes, rejection of product sessions by fixture routes, explicit missing-corpus errors, urgent zero-generation response and blank-message validation. The injected runtime in contract tests is a test double; it is not the live corpus implementation.

## Still required

- Transfer or reconstruct the actual public corpus and its metadata using the existing ingestion pipeline.
- Resolve the database session/public-retrieval boundary without sharing an administrator identity among visitors.
- Bind the existing Stage 5–8 pipeline behind `get_product_runtime`; the default is deliberately an explicit unconnected runtime, not a pretend implementation.
- Verify embeddings, citation provenance and live provider generation.
- Replace temporary dashboard reference assembly with the verified original-corpus response path.
- Complete remaining symptom/wellbeing/FAQ/plan integration. These are not complete merely because the tabs exist.

No GitHub push/merge, remote permission changes, content publication or deployment was performed.
