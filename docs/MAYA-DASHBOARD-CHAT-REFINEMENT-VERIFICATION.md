# Maya dashboard, plans and chat refinement

Date: 16 September 2026

## Verdict

Ready for another **local functional test** at http://127.0.0.1:5180/.
This is not a clinical-approval or public-deployment verdict. No code was pushed, no source approvals were changed, and no fixture adapter was substituted for a failed live request.

## Requested changes and outcome

| Area | Change | Verification |
|---|---|---|
| Journey and growth facts | Removed the extra timing tags; retained small expandable Source links | Browser confirmed at week 32 |
| Nutrition | Added early/middle/late stage introductions; preserved general daily references; explicit allergy exclusions, symptom adaptations, food safety and water guidance | Browser compared weeks 32 and 6 with vegan/peanut constraints; backend tests also compare week 20 and 36 |
| Movement | Added stage focus and stop/help guidance; retained activity, strength/posture/pelvic-floor and position sections | Browser at week 32; restriction tests |
| Symptoms | Actual reported entries, supported heartburn/nausea/back-discomfort/rest adaptations, symptom-note guidance and escalation | Heartburn appeared when selected and disappeared when removed; no symptoms were silently inserted |
| Self-love | Replaces the Wellbeing navigation label; source-linked support, rest and help-seeking content; contextual rest/emotional-concern sections | Browser verified content; backend domain remains `wellbeing` |
| Care records | Removed from dashboard navigation; no upload dependency | Browser and navigation regression test |
| Plans | Seven day disclosures, meal-component options, hydration and existing-supplement reminders, conditional movement and optional self-care slots | All four live plan focuses returned seven-day schedules |
| Plan continuity | Chat-created schedule appears in Plans; switching tabs keeps it; editing onboarding clears stale plans | Browser verified chat → Plans, tab changes, and edit → empty plan |
| Chat presentation | Sans-serif text, typing dots, automatic scroll to latest message; removed disabled attachment control | Browser verified font, dots and visible answers |
| Generic plan intent | “Create a plan for this week” routes to supported specialists rather than no-supported-domain response | Live browser request succeeded |
| Week overview questions | Explicit source-linked lookup for common “what is week X about?” phrasing | Week 32 and week 36 returned different facts; onboarding stayed at week 32 |

## What actually supplies the content

1. **Dashboard education:** versioned local, source-linked catalogue selected by resolved timeline and entered context. It is not claimed to be a fresh RAG generation.
2. **Week overview questions:** deterministic lookup from the same weekly fact catalogue. No model call; exploring another week does not alter onboarding.
3. **Ordinary supported chat and plan evidence:** the existing private-development hybrid retrieval, real embeddings, specialist generation, original-source binding and semantic validation.
4. **Plan presentation:** deterministic, separately attributed catalogue components wrapped around a successful live schedule. Accepted retrieved claims remain under “Guidance retrieved for your plan.” Authored components retain a distinct origin and source IDs.
5. **Failure handling:** failed provider calls do not become fake successes. If some generated domain contributions are rejected while others pass, the plan context and trace disclose any domains supplied only by the educational catalogue.

The final balanced-plan test had accepted Movement and Wellbeing contributions but no accepted generated Nutrition contribution. Its Nutrition components therefore used the cited educational catalogue. The separate Nutrition-only live test passed with accepted retrieved claims. This variability is recorded rather than hidden.

## Verification evidence

- Backend regression: **853 passed; 315 subtests passed**, with six existing dependency deprecation warnings.
- Frontend component/proxy/theme tests: **29 passed**.
- TypeScript: **passed**.
- Git whitespace check: passed; existing line-ending warnings remain.
- Actual browser: fresh onboarding, week 32, vegan diet, peanut allergy, heartburn; Symptoms/Self-love/Nutrition/Movement/Plans; generic weekly-plan chat; week 32/36 lookups; edit to week 6 and remove heartburn; old plan cleared.
- Responsive: plan controls and seven day headings inspected at 390px; no horizontal document overflow. Temporary viewport override reset.
- Opt-in live normal-API checks: Nutrition, Movement, Wellbeing and Balanced all returned HTTP 200, seven days, real generation receipts, retrieval traces, fixture-free trace and stored session plan.
- Live check uses a synthetic profile, not personal medical data. User explicitly approved transmitting the synthetic profile and retrieved source passages to OpenAI.

Local receipts:

- `reports/local/ui-integration/dashboard-refinement-tests.xml`
- `reports/local/ui-integration/live-dashboard-refinement-check.json`
- `reports/local/step5-runtime/provider-ledger.json`

Repeat the opt-in live test with `scripts/verify_dashboard_refinements.py --execute-authorized-development` using the configured Python environment. It makes real, metered model calls. Do not run without authorized provider access and budget.

## Important boundaries / remaining improvements

- Meal suggestions are **components/options**, not a dietitian-authored, portion-calculated seven-day menu. The displayed protein figure is a published pregnancy reference, not a computed personal goal or proof that these meals meet it.
- Activity duration is conditional starter guidance, not exercise clearance. Symptoms, restrictions and recovery can suppress timed activity suggestions.
- Self-care time is an optional scheduling choice, not a clinical dose. Week-based content never predicts the user's emotional state.
- No blanket papaya or other fruit prohibition was invented. Food restrictions must have source support and relevant context.
- The recovered RAG corpus remains limited. Relevant-source coverage and generated answer quality still need broader evaluation. These successful tests do not prove arbitrary medical questions, all allergies, every plan revision or all postpartum scenarios.
- Week-lookup phrasing is intentionally bounded; it is not a replacement for open-ended developmental-question retrieval.
- The separate postpartum Feeding card workflow was not completed in this change.
- Refresh starts a new journey, by the agreed product design. No login, durable health profile or medical-file upload was introduced.
- The private-development corpus has not been published or clinically approved. The changes do not waive those separate requirements.
- The provider ledger is approximately **USD 0.73 reserved/estimated against the existing USD 1 integration cap** after verification. This is a local accounting cap, not an account-balance reading. Further testing may reach it; it was not increased silently.

## Source checks for added education

- [NHS mental health](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/)
- [NHS rest and sleep](https://www.nhs.uk/pregnancy/common-symptoms/tiredness/)
- [NHS food safety](https://www.nhs.uk/pregnancy/keeping-well/foods-to-avoid/)
- [NHS heartburn](https://www.nhs.uk/pregnancy/common-symptoms/indigestion-and-heartburn/)
- [NHS exercise](https://www.nhs.uk/pregnancy/keeping-well/exercise/)
- [ACOG water guidance](https://www.acog.org/womens-health/experts-and-stories/ask-acog/how-much-water-should-i-drink-during-pregnancy)
- [ACOG starter activity discussion](https://www.acog.org/womens-health/experts-and-stories/the-latest/the-top-6-pregnancy-questions-i-hear-from-first-time-moms)
- [CDC urgent warning signs](https://www.cdc.gov/hearher/maternal-warning-signs/index.html)

Source checking is not clinical approval. Preserve provenance and eligibility separately from UI presentation.
