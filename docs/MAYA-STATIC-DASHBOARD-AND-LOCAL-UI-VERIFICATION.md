# Maya: static dashboard and local UI verification

Date: 16 September 2026. Scope: Kajal's requested static content, onboarding context, and private local browser-to-backend connection. This is an implementation receipt, not a claim that the whole product is finished or clinically approved.

## Open and test

Open **http://127.0.0.1:5180/** on this computer. Use this exact address, not another old localhost instance. The local bridge intentionally accepts this loopback origin only.

Start a journey, select pregnancy or postpartum, enter the timeline, and optionally add preferences, allergies, symptoms and activity restrictions. No login or upload is required. Refresh starts a new journey. Editing your details refreshes context and clears earlier conversation/plan state so stale facts are not carried forward.

The local API and UI must be running; Docker/Supabase and the existing backend provider configuration are needed for live chat, not for deterministic catalogue selection. Secrets stay server-side. Nothing was deployed, pushed or published in this step.

## What was implemented

| Surface | Implementation and information source |
|---|---|
| Journey KPI | Uses the existing server timeline resolver. Exact week, approximate month range, or resolved due/birth date; no default week. |
| Nutrition KPI | Two nutrient highlights from five stored pregnancy-stage profiles; separate postpartum content. These are editorial highlights of sourced general guidance, not claims that requirements suddenly change every week. |
| Energy KPI | Encouraging stored self-care themes: rest, comfortable pauses, support and time for yourself. No prediction of mood, hormone levels or symptoms. |
| Movement KPI | Stored stage guidance; reported symptoms/restrictions can replace the generic focus with comfort/support. No automatic exercise clearance from a week number. |
| Baby fact | 42 stored calendar-week entries. Weeks 1–3 explain dating; later entries give a brief sourced development fact. Appears below existing growth measurements. Approximate month input does not invent an exact-week milestone. |
| Maternal fact | Applicable shared stage facts, inside Your Journey and outside the three trimester panels. Separate postpartum self-care fact. |
| FAQs | Nine pregnancy-month sets, six answers each: 54 placements using reusable records. Six separate postpartum answers. Expand inline, show source links, and offer Ask Maya follow-up. No generation needed. |
| Nutrition/movement tabs | Existing sourced reference catalogue and deterministic context rules remain. Vegan/vegetarian and recognised allergy filtering remains; reported restrictions now feed movement cards. These tabs have NOT been relabelled as live RAG generation. |
| Ask Maya | The normal UI now reaches the existing private retrieval/generation/validation runtime through a server-side same-origin bridge. Not the demo/fixture endpoint. |

Catalogue: `data/dashboard/overview_catalogue.json`. Selector: `app/services/dashboard_overview.py`. Existing month mapping and growth assets/measurement library were reused. No database migration, corpus re-indexing, review-status change or fabricated source publication was required.

### Source and interpretation boundaries

The new catalogue uses NHS week-by-week pregnancy pages, NHS dating/rest/activity/mental-health/postnatal guidance, and the existing NIH dietary-reference source records. URLs, source locators, jurisdiction, version, source-check date and an honest development review status are retained. Baby facts were paraphrased briefly from the relevant week sources. The full source list is in the two dashboard catalogues and the selector's weekly-source mapping.

Examples: [NHS week 26](https://www.nhs.uk/best-start-in-life/pregnancy/week-by-week-guide-to-pregnancy/2nd-trimester/week-26/), [NHS activity](https://www.nhs.uk/pregnancy/keeping-well/exercise/), [NHS rest](https://www.nhs.uk/pregnancy/common-symptoms/tiredness/), [NHS postnatal rest](https://www.nhs.uk/baby/support-and-services/sleep-and-tiredness-after-having-a-baby/).

This is source-checked educational content, not independent clinical review. Nutrient requirements may apply across pregnancy; the UI must not manufacture a new target each week. Month labels use the existing approximate product convention. A baby's development, an individual's mood and exercise suitability cannot be measured from this calendar.

## Failures found and corrected during verification

1. **Frontend startup failed:** Turbopack rejected this machine's linked node_modules directory. The local launcher now uses webpack, which successfully starts this checkout without reinstalling dependencies.
2. **Onboarding returned 403:** the backend cookie's `/v1` path did not match the UI proxy's `/api/maya/v1` path. The bridge now remaps only Maya's session cookie path, preserving HttpOnly, SameSite and expiry. Onboarding then passed through the real browser. Access checks were not removed.
3. **Two old growth tests contradicted the accepted design:** one expected outdated measurement imports/labels; the other demanded removed review-pending UI copy. They now check the preserved measurement library, estimate note and absence of obsolete labels. This does not alter clinical approval or the review metadata.
4. **Restriction-only wording suggested a reported symptom:** adjusted the shared limited-activity wording to refer to symptoms *or restrictions*.
5. **Desktop overview gutter:** retained readable outer spacing instead of allowing the four cards to touch the window edge at ordinary desktop widths.

## Verification receipts

- Final full Python regression with actual recovered-package paths configured: **837 passed, 315 subtests passed, zero failures/skips**. Six dependency deprecation warnings remain. Receipt: `reports/local/ui-integration/regression.xml`.
- Earlier run without those paths: 793 passed, 44 skipped. The skips were resolved by configuring the package paths, not deleting checks.
- Frontend component/asset/bridge suite: **25 passed**. Includes all growth asset mappings, timeline boundaries, exactly four overview cards, maternal-fact placement and cookie/access restrictions.
- TypeScript: `tsc --noEmit` passed.
- Browser: landing → all four onboarding steps → week-26 dashboard passed with synthetic vegan/peanut context, no symptoms and an activity restriction. No upload was required.
- Browser: nutrition focus button selects Nutrition; displayed food choices are plant-based and context exclusions remain visible. Movement reflects the entered restriction.
- Browser: week-26 baby fact sits below unchanged 35.6 cm / 856 g references; maternal fact sits below the journey timeline, outside trimester panels.
- Browser: month-six FAQs render six questions; expanding an answer reveals its text/source and a follow-up action.
- Browser: editing to week 6 changes the overview and month-two FAQ set. Clearing the restriction with native keyboard input returns the ordinary early-stage movement focus. An automation `fill('')` did not fire the expected controlled-input change; native keyboard interaction verified the user action.
- Browser: month nine stays **weeks 36–42** and selects the month-nine FAQ set.
- Browser: postpartum birth-date input resolves to recovery week 3 and shows six postpartum FAQs and distinct recovery focus cards, not fetal-development content.
- Layout: desktop and 390px mobile viewport inspected. Mobile document width matched viewport width (375 CSS px excluding scrollbar); no horizontal overflow observed. Temporary viewport override was reset.
- **Real live browser chat:** submitted a protein-food question using synthetic onboarding context. It returned generated, cited evidence with Vegan, Peanut and activity restriction listed as applied context. The source drawer showed the original Ministry of Health and Family Welfare passage and URL. Provider receipts record an embedding request, two generation requests and one semantic-validation request, all HTTP 200. No hard-coded answer was substituted. One successful case is not a general medical accuracy score or complete chat evaluation.

## What remains, explicitly

1. Complete Symptoms, Wellbeing and other still-pending category cards; do not call every dashboard tab finished.
2. Connect richer personalised category content to the evidence pipeline where the intended specification requires it. Current nutrition/movement reference cards are useful static education plus context rules, not freshly retrieved full plans.
3. Broaden live chat tests: follow-up preference changes, symptom clarification, postpartum, evidence gaps, urgent cases and latency. Earlier backend tests cover parts of these, but this browser pass covers one live question.
4. Build richer requested meal/activity plans and finish their UI/state behavior. The existing backend plan remains an educational outline, not a calculated meal menu or full exercise programme.
5. Document upload remains excluded; no document memory is claimed. Deferred UI controls should be revisited with the later upload implementation.
6. Clinical/source publication review and production privacy/session/deployment work remain separate gates. This bridge is deliberately loopback-only and is **not** the public deployment architecture.
7. The growth image library still covers weeks 1–41. Static factual coverage includes week 42, but no extra growth image or measurement was invented for that week.

## Restart on this computer

From the repository root, with ports 8000 and 5180 free:

```powershell
& 'C:\Users\Hrishikesh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B scripts/start_maya_local_ui.py --execute-private-local --node 'C:\Users\Hrishikesh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
```

The script refuses occupied ports rather than terminating unknown processes. It creates a fresh operator token only in process memory, writes no secrets, and stores process IDs/logs under `reports/local/ui-integration/`. Opening static cards makes no model/embedding/retrieval calls. Asking live questions uses the existing bounded provider budget; a technical/budget error must remain visible rather than trigger fixture text.

**Verdict:** GO for Kajal's local onboarding/static-dashboard testing and a bounded private live-chat test. NOT a full-product, public-deployment or clinical-readiness sign-off.
