# Maya — intended product experience and data-flow specification

**Prepared for:** Kajal  
**Date:** 16 September 2026  
**Status:** Section-by-section product behaviour accepted by Kajal; latest refinement uses weekly overview cards, monthly FAQ sets, and weekly baby/maternal facts. This is not an implementation-completion or clinical-content approval report.

## 1. The product we are building

Maya is a maternal companion for pregnant and postpartum users. A user begins a journey, enters their timeline and optional personal context, and receives a useful dashboard immediately. They can explore supported guidance, ask follow-up questions and request plans through Ask Maya.

The intended experience is one connected product: onboarding, dashboard, FAQs, conversation and plans all use the same current user context. The existing UI and growth-image library remain the design foundation.

We are not rebuilding the architecture from scratch. Existing ingestion, retrieval, orchestration, specialist and validation components are reused where appropriate. Step 5 records a populated 96-record development index and real private chat/plan API execution. The subsequent static-dashboard checkpoint connects the local browser and verifies one live chat response with source evidence. Complete category integration, richer plans and broader acceptance testing remain; the earlier empty-store/unconnected-runtime assessment is historical, not the current private-backend state.

### Latest change record — 16 September 2026

- Preserve the existing growth measurement/image library; do not replace its values or redesign this working section as part of the new content work.
- Standard pregnancy FAQs become **nine pre-authored monthly sets, six or seven question-and-answer pairs per month**, rather than newly generated weekly sets.
- Keep the four cards below, using deterministic weekly/stage content. Energy focus describes possible common experiences and a helpful action, not a prediction of this person's mood or hormone level.
- Add one short sourced baby-development fact **below the measurements inside the Growth at a glance card**.
- Add one short sourced maternal-change/self-care fact **inside the Your Journey card, outside the individual trimester panels**. It belongs below the journey content, not inside First/Second/Third trimester. This is not a fifth KPI or a return of the removed top-level changing-body card.
- All these standard overview/fact/FAQ records are stored in versioned data and require no runtime model, embedding or vector-search calls. Detailed personalised guidance and Ask Maya still use the real RAG runtime.
- Implementation checkpoint: the static catalogue and local browser connection are now built. See [Static dashboard and local UI verification](MAYA-STATIC-DASHBOARD-AND-LOCAL-UI-VERIFICATION.md) for actual tests, source provenance and outstanding work. Source checking and development display are not clinical approval or corpus publication.
- Energy focus uses encouraging actions such as rest, calm pauses and accepting help. It must not predict that this individual will feel calm, energetic, stressed or low from a week number or supposed hormone level.

### Confirmed scope

- Preserve the current design, with light theme as the default.
- No user-facing login, account or workspace-creation step.
- No document upload in this implementation phase; no feature may depend on an uploaded document.
- Refresh starts a new journey, following Kajal's selected session behaviour. Explain this briefly before users rely on retained plans or conversation.
- Optional context improves guidance but is not required to receive general stage-applicable information.
- Dashboard guidance appears without asking the user to generate a plan.
- Plans are created only when requested.
- No silent fictional user facts or fixture answers in the ordinary product path.

### Latest dashboard-card decision

The four summary cards are:

1. **Your journey**
2. **Nutrition focus**
3. **Energy focus**
4. **Movement focus**

**Your changing body is removed as a top card.** A calorie target is not part of the revised top-card set.

**Updated direction:** Energy focus automatically provides a supported stage-based energy/self-care theme and a short practical daily suggestion. It does not require a check-in to display useful content. It describes common possibilities, not a forecast of the user's actual mood, hormones or energy. An optional report can refine the guidance but must not be invented.

**Latest delivery decision:** Top focus cards and baby/maternal facts are prepared in advance in a versioned week/stage catalogue; standard pregnancy FAQ questions/answers use separate monthly sets. Display uses deterministic lookup and local context rules, with no runtime LLM, embedding or vector-search call. Detailed personalised guidance, conversational follow-ups and requested plans use the connected evidence/RAG pipeline. Pre-authored educational content is real product content, not a fixture pretending to be generated.

## 2. User journey, step by step

### Step 1 — Landing page

Keep the existing landing page and Begin your journey action. Do not send a first-time user directly into a prefilled week-26 dashboard.

### Step 2 — Choose the journey

The user chooses pregnant or postpartum. Collect their preferred name if the existing onboarding includes it; do not require it for knowledge retrieval.

Do not infer pregnancy confirmation, medical history or personal circumstances from a name or selection.

### Step 3 — Establish timing

- Pregnancy: offer week, month or estimated due date as alternative entry methods.
- Postpartum: offer delivery date or time since delivery.
- Resolve timing consistently on the backend and show the interpretation for confirmation.
- Month-only input stays approximate; do not invent an exact day.
- If inputs conflict, ask a focused timeline question rather than applying a generic safety stop.
- Record the input method and precision as well as the resolved range.

This drives journey progress, growth where applicable, stage filtering, FAQ selection and the context used for answers and plans.

### Step 4 — Optional context

Collect selected options and free text where useful:

| Input | Where it influences the product |
|---|---|
| Diet preference | Nutrition options, food-related answers and meal plans |
| Allergies | Relevant ingredient exclusions, alternatives and food-related plans |
| Reported symptoms | Symptoms tab and supported adaptations to nutrition, movement or wellbeing |
| Activity restrictions or clinician instructions | Relevant recommendations and plans; conflicts must be surfaced |
| Activity background, when provided | Movement guidance and specific plan suitability |

Distinguish “none reported” from “not answered.” Do not add low energy, sleep problems, nausea or other facts the user never supplied.

No energy check-in is required for this card. If the user volunteers how they feel during onboarding or chat, preserve that as an actual report and use it where relevant; it is not a replacement for symptom assessment.

### Step 5 — Review and open dashboard

Show the interpreted journey and optional context, with Edit actions. Completing onboarding opens the dashboard even without symptoms, preferences or documents.

### Step 6 — Update details later

Provide Edit my details. Changes increment the context version, refresh affected cards and answers, and flag existing plans for refresh. An old in-flight response must not overwrite content generated for the new context.

No-login does not mean no isolation: the server must establish a session boundary, enforce it and clean up expired state. Personalised data must not leak across sessions or appear after a fresh start.

## 3. Shared context: one source of user information

Maintain one server-resolved context containing journey, timing precision, preferences, allergies, symptoms, restrictions and optional current check-ins. Preserve the original user wording alongside normalised values where necessary.

Use relevant context, not every field indiscriminately. A peanut allergy affects food suggestions; it does not change the trimester or imply an emotional state. A symptom may affect several categories only where the evidence supports that connection.

Each personalised response should be traceable to a context version and relevant evidence version. The UI can show a short “Based on your preferences” explanation without exposing internal identifiers.

## 4. Four top summary cards

These are compact overviews, not four invented numerical health scores. Use one prominent value or focus, one short explanation and one clear action per card.

| Card | Main display | Information source | Action |
|---|---|---|---|
| Your journey | Confirmed week/day and trimester, approximate month, or postpartum timing | Deterministic timeline resolver using onboarding | View journey or edit timing |
| Nutrition focus | Two supported nutrient highlights | Pre-authored week/stage catalogue with evidence references and deterministic context rules | Open the corresponding Nutrition sections |
| Energy focus | A supported stage-based self-care theme, one sentence about possible energy changes, and a practical daily suggestion | Pre-authored week/stage catalogue, adjusted only by supported rules for actual reported context | Explore energy, rest and wellbeing guidance |
| Movement focus | Short supported activity theme, such as a category of movement or recovery | Pre-authored week/stage catalogue with relevant restriction/context checks | Open the corresponding Movement section |

### Pre-authored weekly overview catalogue

Create explicit entries for the supported pregnancy weeks and separate entries/ranges for postpartum. Several weeks may reference the same supported stage-level content rather than duplicating text or manufacturing weekly differences. Approximate month input must use appropriate range-level content, not arbitrary exact-week development claims.

| Field/group | Stored content |
|---|---|
| Identity and applicability | Stable entry ID, pregnancy/postpartum, week or range, timing precision, applicable audience/jurisdiction |
| Nutrition | Two supported nutrient labels, short explanation, evidence references and detail-section links |
| Energy | Theme, possible stage-related experience, one practical action and supporting references |
| Movement | Theme, concise explanation, relevant cautions, supported alternative variants and detail-section links |
| Baby fact | Short title/body, supported timing range, source anchor and fallback policy; typical development, not an assessment of this user's baby |
| Maternal fact | Short title/body, supported timing range and source anchor; common changes or practical self-care, not an invented personal symptom |
| FAQs | Reference to the selected monthly set; each pregnancy month has six or seven stored question-and-answer records |
| Provenance | Source URLs/anchors, source/evidence version, review status and content update date |
| Context rules | Applicable exclusions, safe pre-authored alternatives and conditions requiring a focused follow-up |

Author and verify content against actual evidence before release. A hormonal mechanism alone does not justify a week-by-week mood prediction, nutrient priority or exercise prescription. Do not use the model's memory as the authority for table values.

Two users at the same week can receive the same general overview and FAQ set. User-reported constraints still take precedence: a generic movement theme must not override a restriction, and a food suggestion must not ignore an allergy. Apply deterministic exclusions or an appropriate pre-authored alternative; do not silently launch an LLM request to fill the card.

Keep catalogue evidence identifiers compatible with the knowledge pipeline so detailed guidance and chat can explain the same information consistently. Missing entries are content gaps to resolve, not permission to fall back to invented data. Versioned static content can remain available during a generation-provider outage when the application itself is available.

### Nutrition focus details

- “Iron + calcium” is an example of display format, not a predetermined recommendation for any week.
- Select two highlights only when there is sufficient support; do not fill a missing slot with a guess.
- Selection may remain the same across several weeks when the evidence supports a broader stage.
- Explain why these are highlighted in the expanded tab.
- Do not imply they are the only important nutrients or that the user has a deficiency.
- Preferences and allergies primarily adapt food options; they must not automatically change nutrient requirements.
- The card and the detailed tab must use the same selected evidence and context, not independent contradictory model responses.

### Energy focus details

- Display content immediately using the confirmed journey and relevant stage evidence. No compulsory self-report and no empty card awaiting a check-in.
- Use supportive themes such as “Gentle pacing,” “Make room for rest” or “Steady routines” only where the chosen guidance supports them. These are action themes, not measurements of how the user feels.
- Avoid standalone “You are energetic,” “You are calm,” “Low energy this week” or “Your hormones will make you feel…” claims unless clearly representing an actual user report, and never invent a hormonal explanation for that report.
- State common possibilities with wording such as “You may notice…” or “Tiredness can be common at this stage.” Do not promise a feeling on an exact week/day or invent a menstrual-cycle-like pregnancy mood calendar.
- Under the theme, show one short supported daily action concerning rest, hydration, regular eating or another relevant self-care topic. Select the action from usable corpus evidence, not arbitrary daily variation.
- Respect actual allergies, preferences, restrictions and relevant clinician instructions in food or hydration suggestions. Do not attach a fluid target or calorie target without an appropriate basis.
- Do not present water or snacks as a treatment for hormonal mood changes, persistent low mood or unexplained fatigue.
- The user’s actual report overrides a generic expectation: never insist they should feel energetic because of the stage. A high-energy report does not override movement restrictions.
- Severe, persistent or concerning symptoms must follow the relevant symptom-support/escalation path, not be dismissed as normal hormones.
- The energy card supports day-to-day care; the Movement focus card concerns activity categories. Keep these distinct and consistent.
- Suggested structure: **theme → common stage possibility → one practical action → expandable source**. A theme may legitimately remain the same across several weeks.

Reference for content preparation: [NHS — Tiredness and sleep problems in pregnancy](https://www.nhs.uk/pregnancy/common-symptoms/tiredness/) describes fatigue and hormonal changes particularly in early pregnancy. [NHS — Mental health in pregnancy](https://www.nhs.uk/pregnancy/mental-health-in-pregnancy-and-after-the-birth/mental-health/) provides support information. These are reference leads, not a claim that they have already been ingested, licensed for every use or approved for the product's release.

### Movement focus details

- Prefer an understandable activity theme over labels such as “heavy exercise week.”
- Intensity and suitability cannot be inferred from pregnancy week alone.
- Select an evidence-supported theme with relevant adaptations; explain limitations in the tab.
- Preserve restrictions and symptom-related precautions when the user asks for a plan.
- If a specific recommendation needs clarification, keep unaffected general information available.

## 5. Journey visual and growth at a glance

### Journey visual

Preserve the selected trimester/progress design. Progress follows the confirmed timeline, with an appropriate postpartum alternative. Approximate timing must not be displayed as exact. Progress is a calendar view, not a health or fetal-development score.

Inside this card, add a compact **About this stage** maternal fact beneath or alongside the existing progress content without crowding it. Use the selected week's sourced entry, or an applicable broader-stage entry for approximate timing. Discuss a common maternal change or useful self-care observation with conditional wording. Never assert that the user has a symptom, a measured hormone level or a particular mood. The fact does not become a user-reported field in retrieval or chat.

### Growth at a glance

For applicable pregnancy weeks:

- Show “This week, your baby is about the size of …” using the existing approved product-library mapping, preserving its actual source/review status.
- Use the corresponding baby illustration and comparison asset at balanced medium sizes.
- Use the fixed sourced measurement library for typical length and weight, with clear units and measurement convention.
- Never generate measurements or comparison values with an LLM.
- Do not imply the image pair is an exact clinical scale unless a valid scale mapping actually exists.
- Keep the short info note explaining that these are estimates, not the user's baby's measurements.
- Do not silently substitute a different week's image when an asset is missing.
- Beneath the measurements, inside this same card, add a compact **This week's development** fact from the static catalogue. Describe one supported typical milestone, such as an aspect of development where its timing is actually supported; do not invent its week from memory.
- Keep the existing short estimate info note and source access. Do not restore a separate “About these estimates” block, “playful comparison” wording or internal “Product review pending” labels.

The fact catalogue needs an explicit entry or supported shared-range reference for every pregnancy week accepted by onboarding. Verify that actual range before authoring; do not assume all interfaces accept the same weeks. For the earliest gestational weeks, use sourced dating/preconception context where appropriate rather than inventing fetal organ development. For later weeks, distinguish typical development from guarantees about this baby. Approximate month-only timing uses month/range wording rather than a randomly chosen exact-week milestone. Do not recalculate or replace growth measurements while adding these facts.

Do not display fetal growth comparisons as postpartum infant measurements. Postpartum content needs its own applicable evidence and must not assume measured infant growth.

## 6. Nutrition tab

The tab must be useful immediately after onboarding, before any plan is requested.

| Section | Intended output |
|---|---|
| Your nutrition focus | A short stage-applicable summary aligned with the two top-card highlights |
| Nutrient sections | Protein, iron, calcium and other relevant topics where the corpus supports useful information |
| Why it matters | A concise supported explanation, without overstating week-specificity |
| Intake references | Sourced general references where applicable, clearly separated from personal prescriptions |
| Food options | Practical options matching stated preferences, with relevant allergy exclusions and alternatives |
| Symptom adaptations | Supported adjustments for symptoms actually reported, without diagnosing causes |
| Food safety | Relevant preparation, handling and avoidance guidance |
| Sources and follow-up | Expandable source details plus Ask Maya actions |

Supplement information must not assume use or recommend starting, stopping or changing prescribed treatment. Do not imply that taking a supplement removes the need for food guidance.

Do not label meals allergy-safe based on a prompt alone. Ingredient validation must respect exclusions; preparation and cross-contact limitations must be represented appropriately.

No automatic seven-day schedule appears merely because the user opens Nutrition. A plan action or chat request starts that process explicitly.

## 7. Movement tab

Show:

1. A stage-applicable movement overview, consistent with the top card.
2. Supported categories such as aerobic activity, strength, mobility/posture, pelvic-floor work and rest/recovery.
3. Practical options, with supported intensity/duration information where appropriate.
4. Relevant adaptations for restrictions, activity background, symptoms and any actual energy report; never treat the energy-card theme as a user-reported symptom.
5. What to modify or avoid.
6. When to stop and obtain appropriate help.
7. Ask Maya to explain an activity or create a plan.

Do not equate early pregnancy with permission for heavy exercise, or later pregnancy with a blanket ban on exercise. A reported backache does not establish a diagnosis or justify every suggested stretch.

Missing optional information should limit only the recommendations that genuinely require it, not blank the whole tab.

## 8. Symptoms and wellbeing

UI refinement (16 September 2026): the wellbeing tab is labelled **Self-love**; backend domain IDs remain `wellbeing`. Symptoms and Self-love render source-linked educational sections directly, with reported symptom adaptations. Care records is removed from navigation while uploads are deferred. The maternal and baby fact cards retain a discreet expandable Source link; their extra timing tags are not displayed.

### Symptoms

Separate “Symptoms you reported” from “Topics relevant to this stage.” The latter are educational topics, not claims about the user's body.

Provide supported general explanations, comfort information, relevant precautions and appropriate escalation. Include Add/update symptom. Urgent advice is prominent; ordinary information should not be trapped in generic confirmation loops.

### Wellbeing

Provide supportive self-care ideas, rest and social-support information, optional check-ins and relevant support for expressed concerns. Tone should be warm, respectful and free of guilt or forced positivity.

Do not infer anxiety, depression, calmness, sleep problems or low energy from the week. Energy and mood are different concepts. Do not turn the energy card into a mental-health screening result.

## 9. Monthly, pre-authored FAQs

FAQs must reflect the journey, not remain a fixed list of product-help questions.

- Prepare nine pregnancy-month sets (months 1–9), each with **six or seven complete question-and-answer pairs**: 54–63 set entries in total. Reusing an answer across applicable months is permitted; this is not a requirement for 63 unique medical claims.
- Keep a month's base set and order stable for users in that month; no daily or per-user randomisation and no model-generated answers on expansion.
- Select the month through one explicit, versioned mapping shared with the timeline resolver. Month labels are an approximate product grouping, not a claim that every calendar month equals four weeks. Exact-week/due-date users use this shared mapping; month-only users retain their selected month and approximate precision.
- Verify mapping coverage and boundaries for every supported pregnancy week, including the latest supported weeks. Do not invent a tenth pregnancy-month set, silently clamp invalid input or select an arbitrary exact week.
- Prioritise genuinely relevant stage topics. A shared question may span months where its answer remains applicable; development answers must not assign every milestone to an entire month if that would be misleading.
- Show useful sourced answers directly on expansion, with Ask a follow-up available.
- Use relevant preferences or symptoms when adapting the answer; do not invent concerns.
- Keep ordinary product help separate from maternal-health FAQs.

Content contract: monthly set ID, month label, ordered list of six or seven FAQ IDs, mapping version; each FAQ stores question, topic, journey, applicable range, prewritten short answer, optional expanded answer, evidence IDs/source anchors, source/review version and applicable constraints. The answer itself must be stored, not just a prompt or retrieval intent.

FAQ expansion is a deterministic lookup with no LLM or live vector retrieval. Users in the same pregnancy month share the same base set. Prefer broadly useful answers without specific incompatible food/activity suggestions; where personal constraints matter, use sourced pre-authored variants or omit only the conflicting suggestion, not the entire FAQ set. Personal follow-up questions go to Ask Maya with the selected FAQ, current context and real RAG path. Do not describe a general FAQ answer as an assessment of the individual. Postpartum uses a separate applicable stage catalogue; never reuse pregnancy-month fetal-development answers for postpartum users.

Suggested editorial question families, to be assigned only to weeks/ranges supported by the source material:

- What is typically developing for babies around this week?
- Which body parts or abilities are developing at this stage?
- How is typical baby size described at this stage?
- What nutrition topics are useful to focus on now?
- What energy or rest changes might someone notice at this stage?
- What should I consider when choosing movement this week?
- Which changes can be common, and when should I contact my care team?
- What questions could I prepare for my next care visit?

Avoid answering “How is my baby doing?” with reassurance about that specific baby. Reframe the general FAQ as “What is typically developing this week?” and explain that individual wellbeing cannot be established from the week alone. Postpartum FAQs need their own relevant topics, not fetal-development wording.

Acceptance requires comparing early, middle and late pregnancy plus postpartum: question selection must reflect actual evidence applicability, not merely replace a week number in the heading.

## 10. Do's and don'ts

Weekly-plan presentation update: requested plans appear as Monday–Sunday disclosures in both chat and Plans. They persist only in the active session and are cleared on onboarding edits/refresh. Live retrieval, specialist generation and claim validation remain the basis for retrieved guidance. A separately attributed deterministic presentation layer adds filtered meal components, fluid guidance, conditional starter activity and optional self-care slots. This layer is not described as generated RAG evidence, a nutritionally complete menu, personal exercise clearance or a supplement prescription. Missing accepted domain contributions must remain visible in plan context; no failed provider request is replaced by a fabricated successful response. Pure “what is week X about?” requests use the same source-linked weekly fact catalogue as the dashboard, without a model call or a change to onboarding.

Create concise, useful summaries grouped by food, movement and everyday care, with relevant symptom-related precautions.

- Use the same evidence and constraints as the main tabs.
- Explain important restrictions briefly and offer alternatives where supported.
- Include sources or links to the expanded category information.
- Do not add popular myths or unsupported blanket restrictions.
- Do not display a diet preference as a medical prohibition.
- Do not contradict the nutrition, movement or chatbot output.

This is not merely a display of “your choices” and “your constraints”; it must contain actual supported guidance.

## 11. Ask Maya and requested plans

### Conversation expectations

Ask Maya is visible and easy to open. Suggested questions may be stage-aware, but answers must come through the real runtime rather than a scripted response table.

For each request:

1. Resolve the isolated session and current context version.
2. Use the question and relevant conversation history.
3. Handle genuinely urgent concerns before ordinary generation.
4. Retrieve applicable evidence with the appropriate eligibility filters.
5. Reuse the relevant existing specialist/orchestration components.
6. Generate a structured, understandable answer from evidence and relevant context.
7. Validate citations, constraints, numbers and output structure.
8. Display the answer, accessible sources and appropriate follow-up actions.

The answer should address the question directly, with a short summary first and details beneath. Explain relevant adaptations naturally rather than reciting every onboarding field in every message.

Follow-ups such as “make those options vegan,” “explain that” and “change Tuesday” must retain the relevant prior context and constraints. Conversation history being visible in the UI does not prove it reaches the reasoning pipeline; test both.

Do not claim access to uploaded prescriptions or reports, request API keys/passwords from the user, invent citations, or silently substitute fixture answers when live retrieval fails.

### Plans

Create plans only after a request. Support nutrition, movement and supported wellbeing contributions through the existing plan-composition architecture.

- Organise daily/weekly output clearly, including named days where appropriate.
- Use the requested duration, actual constraints and supported evidence.
- Ask only for missing details that materially affect the plan.
- Do not invent availability, prescribed supplements or appointment dates.
- Place the resulting plan in Plans and support revision.
- Mark it stale when relevant user context changes.
- Do not claim exact nutritional adequacy unless actual calculation and verification exist.

No record-dependent specialist may pretend to use documents in this upload-free version. Other useful agent capabilities remain connected where their inputs are available.

## 12. Where the information comes from

| Product output | Authoritative input | Role of RAG/generation |
|---|---|---|
| Journey card, trimester and progress | Confirmed timeline and deterministic resolver | No model-based date calculation |
| Growth images and measurements | Existing versioned, sourced week library | No invented generated measurements |
| Baby-development fact within Growth | Sourced weekly/range fact catalogue, selected using confirmed timing precision | Deterministic lookup; no runtime LLM/vector retrieval |
| Maternal fact within Your Journey | Sourced weekly/range maternal fact catalogue plus relevant local constraints | Deterministic lookup; no personal mood/symptom/hormone inference |
| Nutrition highlights | Pre-authored sourced week/stage catalogue plus local context rules | No runtime LLM/vector retrieval; references connect to detailed guidance |
| Energy focus | Pre-authored sourced week/stage catalogue plus relevant local context rules | No runtime LLM/vector retrieval; never predict personal mood or energy |
| Movement theme | Pre-authored sourced week/stage catalogue plus restriction/context rules | No runtime LLM/vector retrieval; never override an actual restriction |
| Nutrition/movement tabs | Evidence library plus relevant current context | Structured grounded presentation and validation |
| Symptoms/wellbeing | Actual reports plus stage-applicable evidence | Supported explanation/support; no diagnosis or guessed feelings |
| Standard FAQs | Nine pregnancy-month sets of six or seven sourced Q&As; separate postpartum stage sets | Deterministic lookup; personal follow-ups use Ask Maya/RAG |
| Do's/don'ts | Same category evidence and constraints | Consistent concise summaries |
| Chat and plans | Question, session context, relevant history and retrieved evidence | Live generation, orchestration and validation |

Source documents, chunks, applicability metadata, embeddings and review/version records form the knowledge layer. An API key does not supply that library. Retrieval finds relevant evidence; it does not by itself enforce allergies or guarantee that generated claims are correct.

## 13. Technical connection and output expectations

The intended connections are:

**Overview cards and facts: onboarding → versioned user context → weekly/stage catalogue lookup → deterministic applicability/constraint checks → existing UI. Standard FAQs use the same context → shared month mapping (or postpartum stage) → stored Q&A set. Neither path makes runtime LLM or vector-retrieval calls.**

**Detailed personalised guidance and Ask Maya: onboarding → versioned user context → category/question request → relevant checks → evidence retrieval → structured guidance or generation → validation → existing UI.**

Before that works, the knowledge path must exist:

**Permitted source material → ingestion/chunking → real embeddings → idempotent database load → versioned retrieval store.**

Reuse the existing components. Complete the missing loader/runtime wiring and reconcile the local provider configuration instead of creating an unrelated parallel architecture.

Retrieve general applicable guidance alongside stage-specific material; strict exact-week matching must not discard valid broader evidence. Review status, jurisdiction and source restrictions must remain explicit. Development/test lanes must not silently become approved-public content.

Constraints such as excluded ingredients require structured checks in addition to prompting. Citation presence alone is insufficient: the supporting passage must actually support the claim.

| Condition | Expected UI behaviour |
|---|---|
| Sufficient evidence and valid request | Useful supported content |
| No optional context | General stage-applicable content |
| One necessary ambiguity | Focused clarification, with unaffected content retained |
| Limited evidence | Supported information plus a concise, specific limitation |
| Urgent concern | Appropriate prominent escalation |
| Provider/database failure | Technical explanation and retry, not a medical warning |
| One failed category | Other independent dashboard sections remain usable |
| Changed context | Refresh affected results and reject stale responses |

Show loading states, bounded retries and accessible errors. Cache by evidence version and relevant context; never leak one session's answers into another. Keep secrets server-side and avoid logging personal health text unnecessarily.

## 14. Acceptance checks before calling the experience complete

- [ ] First-time users complete onboarding without a document or account.
- [ ] No hidden sample timeline, symptoms or preferences appear.
- [ ] Missing optional information does not empty the dashboard.
- [ ] Independent sessions do not share personal information.
- [ ] Timeline changes update the journey, growth and relevant content.
- [ ] Nutrition highlights are supported and consistent with the tab.
- [ ] Energy focus displays supported stage guidance without requiring a check-in or predicting a personal mood/energy state.
- [ ] Energy-card themes never become invented symptoms in chat or movement plans; actual user reports take precedence.
- [ ] Movement themes respect relevant constraints rather than guessing intensity from week alone.
- [ ] Nutrition and movement contain practical guidance before any plan request.
- [ ] Allergies/preferences are respected in relevant dashboard content, chat and plan revisions.
- [ ] Symptoms are not invented; stage education is clearly distinguished from personal reports.
- [ ] Wellbeing support does not invent mood or diagnosis.
- [ ] Each pregnancy month 1–9 has six or seven stored, sourced FAQ answers; the base set stays stable within the month and expands without generation.
- [ ] Week/due-date-to-month boundaries are explicit, consistent and tested; month-only timing remains approximate and postpartum uses its own content.
- [ ] Every supported pregnancy week has a sourced baby fact and maternal fact, or a deliberately shared applicable range; no invented week-specific differences.
- [ ] Baby facts render below the existing measurements; maternal facts render inside Your Journey, not in an extra KPI.
- [ ] Existing growth measurements/assets are unchanged by the fact-catalogue work; display and selected-week mapping are regression-tested.
- [ ] All supported timeline ranges have verified overview/FAQ coverage or an explicit gap; repeated stage-level content is not falsely labelled unique to one week.
- [ ] Opening top cards, baby/maternal facts or standard FAQs makes zero LLM, embedding or vector-search calls, including during a generation-provider outage.
- [ ] Same-week general content is consistent across users, while relevant allergies/restrictions are respected by local rules.
- [ ] Development FAQs explain typical development without claiming this individual baby is healthy or meeting a milestone.
- [ ] Do's/don'ts agree with the main tabs.
- [ ] Chat uses actual retrieved evidence and valid, supporting citations.
- [ ] Follow-ups carry forward relevant context without cross-session leakage.
- [ ] Plans appear only on request and are marked for refresh after relevant changes.
- [ ] Provider failures are not hidden behind fixtures or generic safety wording.
- [ ] Review/publication status remains truthful; passing engineering tests is not clinical approval.
- [ ] Real browser flows, real retrieval traces and relevant negative tests support the completion claim.

## 15. Agreed direction and remaining content work

Kajal accepted the section-by-section product behaviour and requested the pre-authored catalogue approach. The current direction is:

1. Four cards: Your journey, Nutrition focus, Energy focus, Movement focus.
2. Energy focus supplies a sourced self-care theme, not a compulsory check-in or personal hormonal forecast.
3. Nutrition/energy/movement overview cards and standard FAQs use versioned tables with no runtime LLM or vector retrieval.
4. FAQs use six or seven prewritten Q&As per pregnancy month, with engaging sourced development topics and a separate postpartum catalogue.
5. Detailed personalised guidance, Ask Maya and requested plans remain connected to the existing RAG architecture.
6. Add sourced weekly baby facts within Growth and maternal facts within Your Journey, preserving the existing growth library and layout.

The actual week-table values and FAQ answers still need preparation, source verification and the applicable content review. Acceptance of this product design is not approval of medical statements that have not yet been authored. Any required scope change or unsupported content gap must be made visible, not silently replaced with invented information.

### Content implementation contract — next work, not already delivered

Use versioned records under the existing `data/dashboard/` content area rather than burying health text in UI components. Keep weekly overview records, baby facts, maternal facts, monthly FAQ sets and their timeline mapping logically separate with stable IDs. Reuse existing schema/loader infrastructure where compatible instead of building a competing catalogue service. Every factual record needs its original source URL/anchor, supported timing, verification date, version and honest review status. Add machine checks for schema, duplicate IDs, complete supported-range coverage, month-boundary mapping and six/seven FAQ counts; these checks do not replace checking each claim against its source.

Inspect current source/corpus coverage first. Research missing facts from authoritative sources before authoring; retain reuse restrictions and do not fabricate clinical approval. No fact or nutrient focus is selected merely to make each week look different. Report unresolved factual gaps explicitly; do not fill them using model memory or silently expose draft material. Catalogue content that is unavailable must not block unrelated working sections.

### What the old per-week review-label test means

`test_review_state_is_visible_per_week` is a source-text assertion requiring the literal labels “Product direction accepted” and “Product review pending” in the dashboard. It is not a user workflow, clinical review process or agreed dashboard requirement. Those internal labels are not wanted in the user-facing card. Keep actual source/review metadata internally and the concise estimate/source information in the UI.

In the next implementation, replace that obsolete expectation with behavioural checks for the accepted display: correct selected-week data, retained estimate/source access, and absence of the removed internal labels. Similarly, reconcile the measurement test with the existing `getGrowthMeasurements` library rather than restoring an old import solely to pass it. Test changes require evidence of the intended behaviour; do not simply delete coverage. This documentation update does not change either test or claim they now pass.

### Delivery checkpoint and immediate sequence

1. **Contract update (this change):** record the monthly FAQ decision, weekly fact placements and unchanged four-card design; reconcile roadmap status.
2. **Private browser integration:** reuse the verified normal chat/plan API and existing UI; establish server-side private access without exposing operator/provider secrets, start services and test the actual onboarding-to-chat journey. This is controlled local testing under the existing development approval, not publication.
3. **Dashboard content:** author and verify static catalogues; add the two compact fact areas and monthly FAQ expansion; connect detailed Nutrition and Movement to real evidence/current context without replacing the growth library.
4. **Remaining experience:** complete Symptoms, Wellbeing and do's/don'ts; connect requested plans to Plans, richer composition and revisions; test relevant context changes across every section.
5. **Acceptance:** report browser, backend, source-quality and publication readiness separately. The Step 5 private backend milestone is verified within its reported scope; the whole product and every chat scenario are not yet complete.

**Success means one usable, coherent experience: onboarding supplies the context; the knowledge pipeline supplies the evidence; the dashboard makes it understandable; Ask Maya helps the user explore and request plans.**

### Latest presentation agreement — 16 September 2026

Nutrition KPI uses a soft yellow surface. Your Journey replaces the redundant trimester note with a compact, explicitly educational hormone-pattern chart adapted from the earlier local design; only the current stage is coloured. It must not infer personal levels or mood. Approximate ranges remain ranges. Maternal and baby facts retain tiny star icons and subtle source links.

This week displays Nutrition, Movement, Symptoms and Self-love highlights from the existing context-aware dashboard response, plus a create/rebuild action that opens Plans and requests a balanced plan. Plans uses a full-width desktop day-by-category table and expanded mobile cards, not per-day disclosures. Identical all-day reminders can be grouped once without losing instructions. These presentation choices supersede the earlier day-disclosure layout.

Chatbot repair follows this UI pass. Uploads and real clinician handoff remain proposals, not implemented features. See `MAYA-DASHBOARD-LAYOUT-AND-NEXT-CHAT-PASS.md` for the confirmed food-check false positive, verification and proposed next stages.
