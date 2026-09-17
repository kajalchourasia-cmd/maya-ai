# Maya — dashboard layout and next chatbot repair

Date: 16 September 2026

## Delivered locally

At http://127.0.0.1:5180/: yellow Nutrition KPI; small stars on both fact headings; redundant trimester callout removed; compact educational hormone chart with current stage coloured and other stages grey; four This week highlights; create/rebuild action routes to Plans; full-width weekly comparison table on desktop and expanded day cards on mobile/chat.

The chart adapts the earlier local `maya-maternal-companion/app/hormone-data.ts` design. Its hand-authored, independently normalised curves are schematic, not lab measurements, comparable concentrations, mood predictions or inputs to recommendations. Source checked: [Endotext — Endocrinology of Pregnancy](https://www.ncbi.nlm.nih.gov/books/NBK278962/). Approximate month ranges stay approximate and can span two trimesters. Postpartum retains its recovery timeline instead.

Repeated hydration, existing-routine, allergy and symptom reminders appear once beneath the grid only when identical and present on every displayed day. Meal components become readable choices, with their preparation guidance retained above the grid. Other text is preserved. Missing entries say “Not scheduled”. Other category layouts and growth measurements are unchanged.

## Verification

- 35 frontend tests passed: trimester boundaries, approximate ranges, postpartum isolation, four category actions, plan routing, all days visible, reminder grouping and meal-choice preservation.
- TypeScript `tsc --noEmit` passed.
- 70 relevant backend regression tests passed, with six existing dependency deprecation warnings. These are offline tests, not new live-generation evidence.
- `git diff --check` passed; existing line-ending notices remain.
- Browser verified existing week-22 journey, selected-stage highlight, desktop Nutrition plan grid and mobile expanded day cards. Document width 375px within a 390px viewport; no horizontal overflow. Temporary viewport override reset afterwards.
- The user's current onboarding and existing plan were retained, not refreshed away.
- Create/rebuild routing was checked offline. The paid rebuild action was not executed against the user's health profile.
- No paid model calls, corpus/database changes, provider cap changes, Git push, deployment or publication were performed in this pass.

## Confirmed chatbot defect — not yet repaired

The user quoted a food-constraint validation error. No screenshot attachment was visible in this turn. A local synthetic diagnostic of `source_bound_draft`, with a Dairy allergy, returned:

| Candidate text | Result |
| --- | --- |
| Choose dairy-free options. | `constraint_validation_failed` — false positive |
| Avoid dairy. | Passes this deterministic check |
| Try milk. | `constraint_validation_failed` — expected rejection |

This confirms a keyword/negation defect. It does not establish the actual generated text or sole cause of the user's failed response. No food validator was disabled or loosened in this UI pass.

Next repair: reproduce the exact question with synthetic equivalent context; distinguish food recommendations from exclusions/free-from wording; retain ingredient and cross-contact checks; add positive and negative regression cases; inspect evidence filtering that drops mixed passages; use bounded re-generation only with validation and cost controls; verify through the normal live chat endpoint. Do not relabel static fallbacks as live RAG or remove safety checks to pass a test.

The meal catalogue remains limited to protein-component choices. It is not a full recipe library, calorie/portion calculator or nutritionally complete menu. The layout does not fix this separate content gap.

## Proposed only: optional care-document upload

1. Optional upload, consent, file validation/scanning and private extraction/OCR.
2. Extract candidate appointment date/time, clinician instructions and medicine/supplement fields only where present and legible. Keep original wording and document/page references.
3. Show the user a confirmation screen; do not guess missing doses, ambiguous dates or diagnoses. User confirmation is not clinical approval; unclear medication details need clinician/pharmacist confirmation.
4. Separate historical records from confirmed current instructions. Resolve contradictions before applying them.
5. Display “From your care record” separately from Maya's general suggestions. Do not say “doctor verified” unless actual clinician review occurred.
6. Store confirmed appointment/routine fields as structured data. Use document RAG for source-linked questions and context, not as a replacement for exact field extraction.
7. Treat document text as untrusted data, not instructions. Establish isolation, retention, deletion and consent for external processing before enabling uploads. The current no-login design would need secure ephemeral handling or an agreed account model for persistent records.
8. Skipping uploads must never block the rest of the product.

## Proposed only: human-in-the-loop care handoff

- Emergency path: immediate appropriate emergency/maternity contact instructions; never wait for a chat reply or review queue.
- Non-emergency path: user's existing care contact, or a verified provider integration if a partner is available.
- User previews and consents to sharing a concise care summary: stage, symptoms/onset, relevant constraints and specific question.
- A genuine clinician loop needs verified clinicians, secure review access, real availability, acknowledgement/status handling and an audit trail. A clinic link alone is referral support, not clinician review.
- Never show “connected”, “reviewed” or “approved” without a real corresponding acknowledgement. No doctor partnership or service coverage is assumed.

Uploads and human review were not implemented; they remain proposals for the user's decision after the chatbot repair.
