# Maya AI — Kajal's presentation script

Prepared 17 September 2026. Matched to the first two slides of `Maya-Group-62-Final-Presentation-v27.pptx` and the current local implementation. This document changes neither the deck nor the demo video.

## Running order

| Segment | Speaker / screen | Approximate time |
| --- | --- | --- |
| Introduction | Kajal, slide 1 | 20 seconds |
| Problem and demo introduction | Kajal, slide 2 | 30 seconds |
| Product walkthrough | Recorded Jenny video | 2 minutes |
| Live product bridge | Kajal, prepared dashboard | 25–30 seconds |
| Architecture | Aswath, architecture slides | Teammate's allocation |
| Observability and evaluation | Kajal, slide 13 | 30 seconds |
| Current limitations and next steps | Kajal, slide 18 | Approximately 1 minute |
| Closing | Kajal, slide 19 | 10 seconds |

Times are rehearsal estimates, not a measured recording. Allow approximately three minutes for Kajal's spoken sections, in addition to the two-minute video and Aswath's architecture explanation.

## 1. Slide 1 — introduction

**Screen:** Maya title slide. Do not read every card aloud.

“Good morning, everyone. We’re Group 62, and this is Maya, our maternal-health companion for expecting and new mothers.

Between appointments, everyday questions keep coming. Maya brings a mother’s stage and preferences together with source-linked guidance, helping her find a clearer next step alongside professional care.”

## 2. Slide 2 — the problem

**Screen:** Maternal information arrives fragmented.

“Imagine trying to answer a simple question: ‘What should I eat today?’ You have advice from family, information online, and your own symptoms or allergies to consider.

The work of connecting all of that falls on the mother. Generic answers can miss her circumstances, and an urgent concern needs a different response altogether.

Our design question was: how can we create continuity without inventing medical certainty?”

## 3. Introduce the video

**Action:** Switch to the saved MP4 and play it from the beginning. Let the video's voiceover take over.

“Let’s follow Jenny through Maya, from sharing her context to planning her week and asking the questions that come up along the way.”

**Video:** `C:/Users/Hrishikesh/Developer/maya-ai-product-preview/reports/local/demo-video-20260917-v2/Maya-AI-Action-Walkthrough-Jenny-v2.mp4`

## 4. After the video — a short live product bridge

**Screen:** The already-onboarded dashboard at http://127.0.0.1:5180/ . Keep the same synthetic Jenny profile as the video. Do not refresh.

**Start on This Week:**

“You’ve seen Jenny’s journey. Let me show you the thread connecting it here in the running application.”

**Click Nutrition and point to the preferences/allergy context:**

“Her week, food preferences and reported allergy carry through the experience. The dashboard combines source-linked reference content with those details.”

**Click Plans, with a previously generated plan ready:**

“The plan builder and Ask Maya add retrieval and generation to that foundation. The aim is that she can move from understanding her week to deciding what to do next.”

### Handoff to Aswath

“How does that context reach the right part of the system, and how do we check what comes back? Aswath will take you through the architecture.”

**Action:** Return to the PPT architecture section, starting at slide 6. Aswath explains the current implemented path and clearly identifies components that remain part of the wider design.

## 5. After architecture — observability and evaluation

**Screen:** Slide 13, Evaluation architecture. Avoid presenting the historical counts on slide 16 as current live-answer accuracy.

“That architecture also gives us a way to inspect what happened. Our local traces record routing, retrieved evidence, model calls, validation results, response time and estimated cost.

We test whether context carries through, whether sources support the response, and whether urgent or credential requests take the right route.

For this recording, we verified a seven-day plan and five chat exchanges. We also review usefulness: a successful request can still produce an answer that is too general.”

## 6. Limitations, immediate priorities and future scope

**Screen:** Slide 18, Future roadmap. Approximately one minute. Document upload is an additional spoken roadmap item; the existing slide does not explicitly list it.

“Our immediate improvement is answer depth. Some meal questions still receive broad guidance, so we need richer evidence coverage and more varied evaluations before wider use.

We have three next priorities.

First, human review: a consent-based handoff to a qualified clinician or care coordinator, with the relevant context attached. Urgent situations must still direct users to immediate care.

Second, secure document upload: extracting details such as recorded medicines and appointment dates for the user to confirm, while keeping a doctor’s instructions distinct from AI suggestions.

Third, an opt-in WhatsApp companion, bringing the same guidance and safety controls into a familiar channel.

These are our next implementation priorities, alongside clinical review and testing with mothers.”

## 7. Final note

**Screen:** Slide 19, Thank you.

“Our aim is to help mothers spend less time piecing information together and more time feeling prepared and supported. That is the direction we’re building Maya toward. Thank you. We welcome your questions.”

## Presenter preparation — do not read aloud

### Local link and session preparation

- Open http://127.0.0.1:5180/ on Kajal's computer. The frontend and backend health endpoint both responded with HTTP 200 during this check. This does not constitute a new full chat/model test.
- This is a local address, not a public deployment link. It will not open Maya on someone else's computer.
- Keep Docker, the backend and frontend processes running. Do not close their terminals or put the laptop to sleep before presenting.
- Before the meeting, complete onboarding normally with the synthetic profile: Jenny, pregnancy week 22, vegetarian preference, dairy allergy and heartburn. Leave clinician instructions blank.
- Generate one balanced weekly plan in advance through the real UI, inspect it, then leave the dashboard open on This Week. Do not reload the page: refresh starts a new session.
- Keep the MP4 open separately. After it ends, switch to the prepared browser tab, rather than starting onboarding again.
- The live bridge needs only This Week, Nutrition and the already-generated Plans view. It need not repeat the full video or introduce another provider wait.
- If a new request fails during the meeting, acknowledge it and use the recorded run as the demonstrated result. Do not substitute a prepared answer and describe it as a live response.

### Claims to keep accurate

- The older deck describes the wider architecture. Record ingestion, authenticated workspaces, durable state, a staffed clinician connection and hosted observability must not all be described as connected in the current no-login, session-based UI.
- The current runtime has real retrieval and provider execution in the local development lane. That is distinct from clinical approval or publication of a reviewed public-health service.
- Dashboard weekly facts, FAQs and nutrient references use source-linked authored content. Do not say every dashboard card makes an LLM call.
- The hormone chart is illustrative. It does not measure Jenny's hormones or predict her mood. Growth values are approximate references, not her individual scan measurements.
- Plans contain suggested components. They are not calculated nutritionally complete menus or prescribed exercise programmes.
- Current verified observability includes local traces and provider receipts. Do not claim a live LangSmith dashboard was demonstrated without checking that connection separately.
- Five successful recorded exchanges demonstrate those requests, not every possible question or a clinical accuracy percentage. The allergy response remained a general nutrient overview; the vegan response provided food groups rather than recipes.
- The medication/document features and clinician handoff are next priorities, not completed integrations. Do not say that a doctor has received a case or that an uploaded prescription shaped the demonstrated plan.
- Treat the test counts in the older slide 16 as historical engineering evidence. Do not repurpose them as current live RAG, medical correctness or production-readiness percentages.
- No deployment, clinical review, document intake or clinician connection was added by writing this script.

### Optional answer if asked what still needs work

“We have connected and tested the local retrieval-to-response path. The next work is deeper answer coverage, broader evaluation and clinical review, followed by secure records and a real human handoff. We distinguish those next steps from what you have seen running today.”

## References used to prepare this script

- Deck: `C:/Users/Hrishikesh/Developer/genai/Capstone Project/presentation-output/Maya-Group-62-Final-Presentation-v27.pptx`, slides 1–2, 6–13 and 16–19.
- Current recording receipts: `reports/local/demo-video-20260917-v2/take-03/capture.json`.
- Video and route verification: `reports/local/demo-video-20260917-v2/DELIVERY-VERIFICATION.json`.
- Actual replies and limitations: `reports/local/demo-video-20260917-v2/MAYA-ACTION-DEMO-TRANSCRIPT-AND-REPLIES.md`.
- Latest available local regression report inspected: `reports/local/ui-integration/compact-journey-plan-regression.xml`. Its aggregate counts include subtests and skipped cases, so no simplified pass-rate claim is used in the spoken script.
- Runtime implementation: `app/services/grounded_runtime.py`, including source selection, provider receipts, constraint validation and elapsed-time trace fields.
