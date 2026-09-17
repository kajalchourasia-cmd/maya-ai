# Maya: plan repair, compact dashboard and real chatbot retest

17 September 2026. Local implementation only; no merge, deployment, clinical publication, upload or clinician-handoff feature.

## What the new test found

The user's existing Plans screen contained a saved balanced plan, but that did not prove repeated generation was reliable. A fresh normal-API test reproduced two failures: Self-love returned an incomplete model outline; Balanced week failed structural claim validation. Nutrition and Movement passed. Failed run retained in `reports/local/ui-integration/live-plan-focus-20260916T193922Z.json`.

The old pipeline required the model to enumerate every day before the existing deterministic composer could assemble a plan. That made otherwise usable guidance fail because of a missing day. Structural claim failures also bypassed the bounded repair route. Neither failure justifies disabling evidence or allergy checks.

## Fix

- Backend now constructs the requested one-day or seven-day outline from claims; model-supplied day indices are not trusted. Claims still undergo source binding, diet/allergy/scope checking and independent semantic validation, and rejected claims are removed before final composition.
- Long/malformed claims receive the existing single bounded content-repair attempt. Independently valid claims may be retained, but malformed or unsupported claims are never truncated into a seemingly valid answer.
- Manual reading of the chat retest caught an exercise-duration reference phrased as personal advice. Added a suitability-context check and retested; numerical activity guidance must be clearly general or conditional, rather than imply clearance.
- User explicitly approved raising the total local integration reservation cap from USD 1 to USD 2. The existing spending ledger was retained, not reset. No credential was printed or sent in prompts.

## Results

| Check | Result |
| --- | --- |
| Four-focus live API retest | Nutrition, Movement, Self-love and Balanced week all returned seven days, real retrieval/generation traces, no fixture fallback, and saved plans. |
| Actual browser: This week → Create my weekly plan | Opened Plans, showed loading, then displayed a complete balanced Monday–Sunday schedule. |
| Actual browser: select Nutrition → Rebuild plan | Returned a new Nutrition Monday–Sunday schedule with dairy allergy and heartburn context retained. |
| Chat rehearsal | All 16 mechanical checks passed. Actual text was also read; movement was corrected and passed a separate live retest. |
| Backend regression | 847 passed; 44 skipped; 315 subtests passed; six warnings. |
| Frontend | 37 tests passed; TypeScript passed. |
| Source index | Existing 98-record development packet unchanged in this pass. |

Reports:

- `reports/local/ui-integration/live-plan-focus-20260916T194323Z.json`
- `reports/local/ui-integration/chat-demo-20260916T194431Z.json`
- `reports/local/ui-integration/chat-demo-20260916T194652Z.json` (corrected movement)
- `reports/local/ui-integration/compact-journey-plan-regression.xml`

[Actual replies and saved schedule text](MAYA-DEMO-ACTUAL-REPLIES-20260917.md) are exported from those synthetic test reports, not written as fictional answers. Live wording can vary. The exporter does not make provider calls.

## Dashboard changes

1. Journey header: exploring week and matching trimester at top right, compact Hormones legend opposite the title, no repeated Your journey week text.
2. Chart: subtle lavender active-trimester band; removed the extra hovering circle and separate trimester row. Numeric onboarding-week marker sits on the slider scale and is clickable to return. Exploring does not edit the dashboard profile.
3. Hormone guide: compact collapsed disclosure, with five existing explanations in a three-column grid when opened. No new hormone levels or mood predictions were invented. Existing caveat remains below A Little About You.
4. Nutrition: Shaped around you; Your everyday nourishment; Supplements & food safety. Cards align within their groups; an unmatched last card spans the row. Tests ensure no existing section is dropped or duplicated, including future unknown sections.
5. Plans: clearer focus controls, compact result badge, context strip, source/method disclosures and a daily nutrient-reference panel above the comparison table.
6. One-day schedules no longer label a tomorrow request as Monday–Sunday or arbitrarily Monday.

Desktop chart, grouped Nutrition and plan layouts were inspected in the browser. First/second/third-trimester boundaries and approximate month ranges have component regression coverage. This is not an exhaustive mobile visual audit.

## Important distinction: nutrient references versus intake totals

The new panel reuses sourced dashboard references. It explicitly says menu totals are not calculated. The current schedule stores alternative food components, not selected recipes, portions, nutrient composition or a diary of consumption. Therefore it cannot honestly display grams consumed or claim the menu meets a personalized target.

A real daily-total column needs: chosen portions/recipes, a reliable food-composition dataset, allergen-aware substitutions, sum calculations with units and tests, and an explicit separation between planned and consumed intake. That is additional work, not silently simulated here.

## Demo readiness and limits

The tested flow is ready for a rehearsal in the current local environment. It is not a guarantee for every paraphrase or clinical/public-use approval. In particular, live meal-option answers currently name food groups more than concrete recipes, and schedule meal choices remain source-linked authored components around validated live guidance. They are not a complete dietitian-designed menu.

Use the existing synthetic week-22 scenario: baby development → allergy meals → vegan follow-up → heartburn → weekly plan → memory → secret refusal → urgent routing. Movement and self-care are additional verified examples. Catalogue answers and deterministic safety boundaries should not be described as LLM generation.

After the final two browser plan builds, approximately USD 1.067 was reserved/accounted for under the USD 2 cap, leaving approximately USD 0.933 headroom. This is local application accounting, not a reconciled invoice; uncertain calls retain reservations.

Local URL: http://127.0.0.1:5180/ . The services were restarted with the final backend fix. Refresh begins a new temporary journey; the open browser contains a clearly named synthetic test profile.
