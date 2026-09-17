# Maya — what the corpus numbers mean and where Step 4C stands

Prepared for Kajal · 16 September 2026

## Plain-language explanation

An evidence unit is a selected piece of source text with a source identifier, a location, a topic and information about when it applies. It is not a complete document, an answer, a model or an embedding. A draft means we have prepared the text and its traceability, but have not completed admission/review for use in the product.

Think of parser blocks as pieces a document-reading tool detected, selected passages as short quotations chosen from those pieces, and expansion sections as longer sections we are now preparing. Comparing their counts directly is misleading. We should have made that distinction clear earlier.

| Number | What it counts | What it does not mean |
|---|---|---|
| 986 | Parser blocks reported across the 14 historical ingestion runs | Not 986 saved, useful, approved chunks; not necessarily 986 distinct facts |
| 72 | Block bodies preserved in the handoff and initial import | Not 72 full documents |
| 914 | Difference between reported parser blocks and retained bodies | Not 914 embeddings waiting in another ZIP. The sender reports these bodies were never persisted |
| 55 | Existing selected evidence candidates | Not 55 published answers |
| 53 | Of those 55, candidates with recorded source-level embedding permission | Not 53 already generated embeddings; content review is separate |
| 2 | Existing BHC-WEEKS candidates without embedding permission | Not all growth-card assets or all week-related knowledge |
| 46 | New, larger authoring sections prepared locally from supplemental text derivatives | Not a replacement for the 53; not yet database additions |

The 53 permitted existing passages contain **1,124 whitespace-separated words**, averaging approximately **21 words each**. The 46 expansion sections contain **7,991 words**, averaging approximately **174 words each**. Length varies considerably. These counts use source text, not model tokens.

The expansion comes from four sources: NHM-MOTHERHOOD, NHS-PP-ACTIVE, OWH-HEALTH and OWH-STAGES. Twelve derivative files were supplied overall; cleaning retained 56 sections across five sources before further authoring holds and exclusions.

**Do not add 53 and 46 and call the result 99 unique knowledge chunks.** Their granularity differs and some text overlaps. Do not equate word count with safe, complete product coverage.

## What was executed in this continuation

The existing expansion service now performs a reproducible overlap and count reconciliation:

- Rechecks packet hashes, source bytes, source governance checksum and original import identity.
- Matches complete normalized token sequences, not word fragments.
- Identifies whether a new section contains an old passage, is contained by it, or has identical text.
- Records old passage IDs, existing timing and conditions as references only. They are not automatically inherited.
- Counts overlapping text without deleting source clauses or double-counting overlapping matches within a section.
- Separates category/topic presence, source-explicit timing and actual eligibility.

Results on the real handoff:

- 10 expansion sections contain 19 distinct existing selected passages.
- None of the 46 sections is wholly covered by those matched existing passages.
- Those ten sections are retained as broader context pending admission; old records remain canonical for their current version.
- The other 36 sections have no same-source complete-token containment match. That does not prove they contain wholly new facts: semantic duplication still needs review.
- 12 sections have source-explicit timing; 34 have broad-stage hints without an established exact interval.
- No new database records, embeddings, approvals or published releases were created by this continuation.

**83 targeted tests passed, no skips**, with five existing PyMuPDF/SWIG deprecation warnings. These are authoring/import/embedding-boundary regression tests, not clinical validation or a live chatbot test. The first sandbox invocation could not load pytest correctly; the same tests then ran successfully with access to the installed local dependencies.

The original expansion checksum remains unchanged: `ea2aadb8cf2707fa0887030e5e4ebbb90b3c2e7263bd663ca273439a1196a2be`.

Execution evidence:

- `reports/local/corpus-expansion/20260916T124003503057Z/reconciliation.json`
- `reports/local/corpus-expansion/20260916T124003503057Z/output-sha256.json`
- `reports/local/corpus-expansion/step4c-reconciliation-tests.xml`

## Category inventory — not a completeness score

These numbers describe only the 46-section expansion. A section can have several topic labels, so totals across categories exceed 46. Existing corpus passages and separate fixed growth/FAQ catalogues are not counted here.

| Topic | Pregnancy sections | Postpartum sections | Important remaining work |
|---|---:|---:|---|
| Nutrition | 12 | 4 | Validate quantities and populations; distinguish general guidance from stage-specific claims; retain breastfeeding and other qualifiers; connect diet/allergy adaptations |
| Movement | 6 | 3 | Separate general education, conditional activity advice, recovery differences and stop/help instructions; do not treat every exercise as suitable for every user |
| Symptoms | 7 | 1 | Verify which ordinary comfort questions can actually be answered; separate reported symptoms, general stage education and urgent warning material |
| Wellbeing | 4 | 2 | Verify practical support coverage; do not predict a user's mood or hormone state from their week |
| Journey/development | 9 | 0 | Source milestones cover selected points, not every week; do not generate missing growth measurements from these sections |
| Preparation | 4 | 1 | Check local relevance and exclusions before presentation |
| Follow-up | 0 | 1 | Limited expansion coverage; not an appointment or clinician follow-up service |

Nutrition and movement sections in this expansion have **no source-explicit week intervals in the current authoring packet**. Some contain timing or conditional statements within their text; these still need passage-level interpretation. This is not a finding that nutrition or movement never changes by stage. It means the current metadata cannot yet support automatic stage-specific delivery reliably.

FAQ answers and complete daily/weekly plans are separate product outputs. They have not been created merely by assigning topic labels to these sections. They need their own evidence-linked authoring/generation and tests.

## Where the project is actually lacking

1. **Historical retention:** the original dry runs did not preserve most reported block bodies. Rebuilding from permitted originals/new captures is possible, but would be new extraction, not recovery of saved historical bodies. We do not need to chase the number 914 as a target.
2. **Evidence admission:** new derivative text has reproducible local offsets, but not all original-document anchors. We need a justified derived-text admission route or the necessary original-source verification, not invented PDF/page anchors.
3. **Source selection and reviews:** existing permissions refer to selected material. Expansion does not automatically inherit those decisions. The relevant permission scope must be checked; this is not a blanket claim that the law prohibits using the broader sources. Genuine content/clinical/localisation decisions must not be fabricated.
4. **Applicability and conditions:** broad pregnancy/postpartum advice must not become arbitrary weekly claims. A condition found elsewhere on the same web page must not become a requirement for every section from that source. Mixed conditional sections need scoped authoring while preserving context.
5. **Answerability:** source-topic counts do not establish support for nutrient numbers, vegan/allergy alternatives, symptom-adapted movement or every FAQ. Test representative questions and acquire additional permitted evidence only where gaps remain.
6. **Runtime:** recorded state still has no usable published corpus release or real corpus embeddings. Actual retrieval, onboarding-context wiring, generation and user-facing tests remain later milestones. Successful source preparation is not successful RAG.

## Exact next actions, without skipping milestones

We remain inside **4C**. Mechanical overlap reconciliation is now implemented; semantic reconciliation, applicability and admission are not finished.

1. Author passage-specific applicability and conditional branches, starting with nutrition and movement. Broad-stage material should be represented truthfully, not forced into a falsely precise week range.
2. Resolve source admission for expanded selections and derivative provenance. Preserve existing decisions only for their exact reviewed subjects.
3. Verify key quantities, cautions and audience/localisation; record unresolved review decisions with an owner rather than treating a technical test as clinical approval.
4. Convert eligible additions to the production ingestion/loader contract and test additive import, conflicts, rollback and repeat safety.
5. Then execute **4D** real embeddings for eligible records and verify stored vectors and source identity.
6. Then execute **Step 5** actual retrieval/runtime verification, followed by dashboard and chatbot integration.

No new key or another identical ZIP is required for the engineering portion of 4C. Source permission or qualified-review decisions may require external input; a new export cannot manufacture those decisions. If we encounter such a specific blocker, it must be reported with the affected source/text and the exact decision needed.

**Verdict:** we have more recoverable source content than the initial 53 short passages, and useful software foundations. We do not yet have a complete, admitted, indexed corpus or proven user-facing RAG. Continue 4C; do not mark it complete or jump to Step 5.
