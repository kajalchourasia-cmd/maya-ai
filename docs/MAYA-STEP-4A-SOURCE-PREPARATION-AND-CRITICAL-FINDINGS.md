# Maya — Step 4A source preparation and critical findings

16 September 2026 · Prepared for Kajal

**Verdict: Step 4A local preparation and initial coverage assessment executed. GO for targeted evidence expansion and reconciliation. Not a GO for completed live RAG or public health-guidance release.**

This is a technical/content-inventory audit, not a clinical review. Current medical accuracy and source currency were not independently verified online in this step. No source claim below is a recommendation for a patient.

## 1. What actually ran

1. Verified the pinned discovery manifest and all **137 payload checksums** before preparation, and again after it. The original package is unchanged.
2. Reused the existing validated import plan and indexing inventory. Did not create a separate knowledge database or rewrite existing source/review records.
3. Processed all **12 supplemental text derivatives**, associated with five source IDs.
4. Applied explicit, tested article-boundary recipes to three web-text derivatives. Separated navigation/preamble, footer/licence/date/link/video metadata and the licence-only PDF page from the review-text output.
5. Preserved retained text exactly, with original decoded-text character offsets, input hashes, section hashes, source URLs and source-binding limitations. Kept health cautions and support contacts in the review material rather than deleting them as boilerplate.
6. Added topic/stage discovery hints and flags for numeric content, supplement instructions, country-specific services, professional instructions and flattened tables. These are not approved clinical applicability tags.
7. Built a matrix separating existing candidates' declared applicability from supplemental text leads. No weekly coverage is inferred from a topic label alone.
8. Counted the supplied structured catalogues and their status/quantity limitations.
9. Rechecked the actual local database import with the existing read-only verifier. Exact mapped records and provenance still match; draft/role-isolation checks passed.
10. Ran focused preparation/import/content/embedding-boundary regression tests: **79 passed and 30 subtests passed**, with five PyMuPDF/SWIG deprecation warnings.

**No provider calls, charges, database mutations, new approvals, production embeddings, application UI changes, Git commits or pushes occurred.**

## 2. What is available after cleaning

| Input | Raw words | Retained review words | Review sections |
|---|---:|---:|---:|
| OWH staying healthy text | 6,462 | 5,652 | 25 |
| OWH pregnancy stages text | 2,190 | 1,382 | 14 |
| NHS activity after birth text | 1,405 | 1,199 | 9 |
| Eight retained NHM page derivatives | 959 | 959 | 8 |
| NHM licence-only page | 45 | 0 | 0 |
| **Total** | **11,061** | **9,192** | **56** |

The 1,869-word difference is material excluded from the health-review text, not deleted from the source package. Licence information remains available in the original and exclusion manifest.

These **56 preparation sections are not the 55 previously imported evidence candidates**. They are larger, traceable working sections for Step 4C; they may overlap existing selected evidence and are not final retrieval-sized chunks. Zero exact duplicate sections were found; this does not mean there is no overlapping or near-duplicate guidance.

The earlier approximately 11,060-word PowerShell count differed by one token from Python's Unicode-whitespace count of 11,061. Counts are now reproducible through the checked-in preparation script. Word counts do not measure clinical completeness.

## 3. Important catches and required responses

### F01 — More text is useful, but it is not a complete per-week library

**Evidence:** The inventory finds the same nine broad pregnancy nutrition candidates and five movement candidates overlapping each inspected pregnancy band. One general dating passage makes the journey domain appear covered across weeks even where there is no specific development passage. Forty-six draft profiles still have no linked evidence.

**Risk:** A count-based coverage report can appear green while the user receives the same generic information or unsupported week-specific claims.

**Action:** Step 4C must assess answerable questions and subtopics, not just domains. Retain legitimate stage-wide advice; add truly supported differences without inventing 42 distinct prescriptions. Journey dating, fetal development, FAQ readiness and plan support need separate checks.

### F02 — Source timing and product timing differ

**Evidence:** The OWH stages derivative labels trimesters 1–12, 13–28 and 29–40. The existing `dashboard_guidance.py` overview uses `<14` and `<28`, producing boundaries at weeks 14 and 28.

**Risk:** The dashboard, retrieved explanation and FAQ could assign different trimester labels to the same week.

**Action:** Record one product timeline convention with its source and boundary tests. Preserve source-native wording/metadata, reconcile display mappings explicitly, and do not silently reinterpret source ranges. Test at least weeks 12, 13, 14, 27, 28 and 29. This step identified the mismatch; it did not choose or implement a clinical convention.

### F03 — Derivative integrity is not original-document verification

**Evidence:** All transferred payload hashes pass. However, cleaned sections are anchored to the transferred `.txt` derivatives. The original PDF/HTML bytes are not in this package, and OWH historical versus later captures were already reported to differ.

**Risk:** Claiming a derivative offset is an original HTML/PDF citation, or applying old decisions to new text.

**Action:** Step 4B/4C must reconcile original source versions when available. Output explicitly records that derivative-to-original reproduction has not been verified. Never invent PDF page confirmation beyond the filename's page hint. New passage versions need their own applicable decisions.

### F04 — Professional instructions and country-specific content need adaptation

**Evidence:** `nhm-cho-11.txt` is titled as a supervisory role for community health officers. Other pages contain care schedules and supplement instructions. OWH and NHS bodies include US/UK contact details and services. The registry marks NHM-CHO commercial permission restricted and the other four supplemental source IDs' commercial permission unverified.

**Risk:** Turning instructions for professionals into patient prescriptions, or presenting foreign services/entitlements as local ones.

**Action:** Separate professional guidance, educational material, numeric references and treatment/schedule content. Review audience and localisation per passage. These are recorded restrictions, not an independent legal ruling; source-level “may embed” alone does not clear every expanded passage for publication.

### F05 — Numeric tables and prescriptions cannot be ingested blindly

**Evidence:** The derivatives include flattened nutrient tables, age-qualified references, supplement quantities and exercise instructions. A text export can lose table structure, and a short chunk can separate a number from its qualifying population or caution.

**Risk:** Wrong units, reference population, treatment interpretation or truncated caveats even when retrieval is technically successful.

**Action:** In 4C, preserve headings, population, units, dose-versus-food distinctions and attached cautions. Verify high-impact numbers and current applicability against authoritative sources before delivery. Do not copy an old schedule or merge conflicting values automatically. Current text has been preserved for review, not certified correct.

### F06 — The normal chatbot runtime remains unconnected

**Evidence:** `app/services/product_runtime.py:get_product_runtime()` returns `UnconnectedProductRuntime`; normal chat/plan requests use this dependency in `api/main.py`.

**Risk:** Even a fully populated embedding database would not make the current chatbot live by itself.

**Action:** Step 5 must bind the actual retrieval/orchestration/generation path. Prove it with the normal endpoint, not a test dependency override. Step 8 must then prove conversation and requested-plan behaviour. This is a known remaining implementation task, not something fixed in 4A.

### F07 — The current context contract lacks some intended inputs

**Evidence:** `OnboardingRequest`, session fields and `ProductContext` carry diet, allergies and symptoms, but the inspected contract has no explicit activity-background or clinician/activity-restriction fields.

**Risk:** Even if the UI adds these later, the backend could discard them or fail to carry them into advice and plan revisions. Free-text symptoms are not a reliable substitute for every restriction.

**Action:** Steps 5–6 must extend and test the shared context deliberately, preserving original user wording and normalised values. Add only relevant optional inputs; do not turn this into mandatory medical-history onboarding. For specific postpartum activities, delivery/recovery details may require a targeted question rather than assumed clearance.

### F08 — The existing detailed dashboard path is not live RAG

**Evidence:** The dashboard API calls `build_dashboard_guidance()`. Its trace identifies `local_reference_catalogue`, with no model call; the current nutrition headings are coarse phase rules, not the agreed two-nutrient overview catalogue.

**Risk:** A populated screen can be mistaken for completion of the planned evidence retrieval and personalisation path.

**Action:** Keep deterministic content where agreed: overview cards, growth, standard FAQs. Connect detailed personalised guidance to the verified evidence path in Step 6. Align card and tab evidence and context. Do not remove useful existing material blindly or describe all pre-authored content as fake.

### F09 — Existing plan catalogues are small and qualitative

**Evidence:** The supplied package has 12 food items, six movement components, six wellbeing exercises, ten follow-up milestones and 42 fetal-comparison rows, all draft. All 12 food items explicitly use `qualitative_only_no_grams_or_calorie_claim`.

**Risk:** Claiming generated meal plans meet protein/calorie requirements without an ingredient/portion calculation system; treating 42 comparison rows as proof of complete medical week content.

**Action:** Reuse these catalogues as starting material, not as proof of nutritional adequacy. Build requested qualitative plans within available evidence, or separately implement/verify nutritional calculations before making numerical adequacy claims. Test allergy and recipe-ingredient handling beyond prompt instructions.

### F10 — Postpartum and symptom coverage are thinner than broad labels suggest

**Evidence:** Only one existing postpartum nutrition candidate spans weeks 1–12. Existing pregnancy symptom candidates inspected mainly cover warning/stop conditions, not a full comfort-guidance library. Supplemental material adds useful topics but not complete symptom-specific adaptations. The weekly candidate matrix has no postpartum follow-up candidates for weeks 7–12; day-based overlays are inventoried separately.

**Risk:** Treating pregnancy content as postpartum content, confusing breastfeeding with all postpartum users, or treating an escalation passage as an answer to every ordinary symptom question.

**Action:** Review pregnancy/postpartum separately; keep breastfeeding and recovery conditions attached. Assess common symptom questions and needed adaptations explicitly. Do not invent symptoms, stage-specific exercises or reassurance to fill gaps.

### F11 — Real indexing/publication decisions remain outstanding

**Evidence:** Fresh local recheck still finds 53 source-permitted candidates, two embedding-forbidden candidates, zero production-eligible candidates and pending role decisions. The earlier development-only indexing proposal has not been explicitly resolved.

**Risk:** Either unnecessary delay in independent preparation work, or silently bypassing publication rules to make output appear.

**Action:** Continue 4C source work without waiting. Before embedding pending material, resolve the documented operator-only development scope explicitly. Development indexing does not grant permission to expose that material in the user product. Track real review owners and decisions separately from engineering tests.

## 4. Initial section-by-section coverage assessment

“Available” below means located for preparation/review, not approved for user-facing guidance. Supplemental sections retain source-native context and have no automatic exact-week assignment.

| Product area | Useful existing/recovered material | Work still needed |
|---|---|---|
| Journey/trimester | Existing resolver and dating evidence | Reconcile trimester conventions, approximate month handling and source-to-display mappings |
| Growth/development | Existing UI library, 42 draft comparison rows, OWH milestone text | Verify measurements/conventions separately; source text has selected milestones, not every week's development |
| Nutrition | Food groups, nutrient discussion/table, food safety and practical choices | Numeric-reference verification, clinically appropriate applicability, preferences/allergy alternatives, symptom adaptations and postpartum distinctions |
| Movement | General activity, cautions, pelvic-floor discussion and postpartum return-to-activity material | Context/restriction contract, category coverage, conditional suitability, source currency and appropriate intensity/duration information |
| Symptoms | Warning/stop passages and trimester symptom descriptions | Non-urgent comfort guidance and source-backed adaptations; keep symptoms reported by the user separate from education |
| Wellbeing / energy | Stage-related experiences, rest, support and postpartum mental-health material | Review sensitive wording; no personal mood prediction; prepare consistent catalogue themes and escalation boundaries |
| FAQs | Source sections offer material for selected stage/development questions | Author actual sourced question-and-answer records and validate all intended stage ranges; not done by these excerpts |
| Do's and don'ts | Food safety, movement cautions and everyday-care topics | Consistent summaries with specific evidence and relevant constraints, not duplicated blanket warnings |
| Plans | Draft qualitative catalogues and broad supporting guidance | Coverage/diversity, ingredient restrictions, requested-only composition, revisions, context-version staleness and truthful limits |
| Ask Maya | Existing orchestration/retrieval components | Runtime binding, history, source-support validation, uncertainty handling, plan actions and end-to-end tests |

## 5. Prioritised acquisition and authoring backlog

This is the next implementation queue, not a request to rebuild everything.

1. **P0: source/citation and numeric context.** Reconcile 4B originals where supplied; preserve exact derivatives where not. Review flattened nutrient tables, supplement/care schedules and condition-specific language before forming new candidates.
2. **P0: nutrition and movement answer coverage.** Start with practical food options, relevant nutrient references, food safety, activity categories and restrictions for early/middle/late pregnancy and postpartum. Identify gaps by representative questions, not arbitrary target chunk counts.
3. **P0: shared timeline/context contract.** Resolve F02/F07 in the planned runtime/context work before connecting competing calculations to UI and chat. Do not change the original source text to conceal a disagreement.
4. **P1: ordinary symptom adaptations and wellbeing.** Collect or reacquire eligible authoritative material for actual supported questions where the available warning-only passages cannot answer them. Do not repurpose a provider's general knowledge as corpus evidence.
5. **P1: sourced card and FAQ authoring.** Use stage-level reuse where supported and explicit sparse development milestones. Mark unsupported exact-week claims as gaps.
6. **P1: plan catalogue coverage.** Expand useful permitted qualitative components if needed; numerical meal-plan adequacy is a separate capability, not inferred from the existing food examples.
7. **P2: broader coverage after the above.** Fill remaining supported stage/category gaps without delaying verification of the first complete real path.

We can begin 4C with the local material now. Aswath's 4B response may improve original-source verification and coverage, but is not a reason to discard this preparation or wait on all work.

## 6. Reproducible implementation and reports

Added:

- `app/services/corpus_preparation.py` — explicit handoff-specific cleaning boundaries, character accounting, provenance, review flags and coverage/catalogue inventory.
- `scripts/prepare_maya_corpus.py` — verifies the package, writes ignored local review outputs, checks the package again and writes output checksums.
- `tests/test_corpus_preparation.py` — boundary failure, unknown input, text preservation, exclusion accounting, risk flags and actual-package determinism tests.

Run with the existing Python dependency environment:

```text
python scripts/prepare_maya_corpus.py --package "<inner discovery package directory>"
```

Outputs under `reports/local/corpus-preparation/<timestamp>/`:

- `preparation.json`: full inventory, source restrictions, exact text offsets/hashes, topic hints and coverage with IDs.
- `review-sections.jsonl`: 56 traceable preparation sections, explicitly not approved ingestion candidates.
- `cleaned-*.txt`: exact retained source substrings in original order; not model paraphrases.
- `inventory.md`: human-readable file and coverage counts.
- `output-sha256.json`: checksums for generated output files.

The generated full-text material stays in ignored local reports. This is not authority to redistribute full derivatives publicly or commit them to Git.

Verification evidence:

- `reports/local/corpus-preparation/20260916T114917649429Z/` — final preparation output for this step, including full source-offset records and output checksums. The earlier 11:44 run is preserved but superseded by this final report format.
- `reports/local/corpus-preparation/step4a-tests.xml`
- `reports/local/corpus-indexing/readiness-20260916T114543727956Z.json` — fresh import and isolation verification.

A fresh browser/user-journey test, full application regression suite, current clinical-source verification, source approval and real corpus embedding were **not** performed in Step 4A. Static runtime findings are based on code inspection, not a claim that the running browser was retested.

## 7. Exact next step

**Step 4C: convert the useful review sections into a prioritised, properly anchored and versioned evidence expansion, with explicit applicability and review requirements. Merge 4B assets when available.**

The roadmap still continues through real indexing, retrieval/runtime integration, dashboard sections, Ask Maya, requested plans and end-to-end verification. These findings are now recorded against those milestones rather than left as surprises for final testing.
