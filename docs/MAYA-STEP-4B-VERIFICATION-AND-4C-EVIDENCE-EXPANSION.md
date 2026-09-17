# Maya — Step 4B verification and Step 4C evidence expansion

Prepared for Kajal · 16 September 2026

**Verdict: 4B archive and extracted-file integrity VERIFIED. GO for local evidence authoring. Step 4C draft expansion implemented and tested; 4C overall remains IN PROGRESS. Not ready for production embedding or live user guidance.**

## 1. What we received and independently verified

Package: `MAYA-FINAL-RECOVERY-AND-DEPENDENCY-CHECK-20260916T114006Z`.

ZIP SHA-256:

`fd6f8bf83997cebe4f2e17ed15518f73878b7721438ae31ba00ef48b1c14ed2c`

Executed checks:

- ZIP checksum matches the supplied checksum file and screenshot.
- ZIP CRC check passes.
- All seven archive files exactly match the seven extracted files; no extra extracted files exist.
- Six manifest-listed payload hashes and byte sizes match. The seventh file is `SHA256SUMS.json` itself, whose bytes are covered by the pinned ZIP hash. This explains “7 files” versus “6 payload hashes.”
- The separately attached report matches the report inside the verified ZIP.
- All four reported historical original hashes agree with the earlier source-linkage inventory.
- Source packages were rechecked after the authoring run and remained unchanged.

These checks verify the delivered bytes. They do **not** independently inspect Aswath's laptop, verify current account balances, establish legal rights, confirm clinical accuracy or prove live RAG.

The new material is three reproduction documents: the Stage 1 implementation guide, the ingestion failure-recovery runbook and extraction-provider ADR 0004. The package also includes status/manifests and the prior operational handoff.

**There are no new source bodies, source binaries, embeddings, database records or backend code in this delivery.** The new documents confirm that the original parser deliberately selected evidence and retained its governed blocks. The unretained 914 bodies are not a missing ZIP attachment that another export can recover.

## 2. What went well, what remains unresolved

| Area | Assessment | Consequence |
|---|---|---|
| Integrity | Verified with pinned ZIP hash, CRC, payload hashes and exact extracted-byte comparison | Safe to use the supplied documents as reference inputs |
| Reproduction | Missing operator/recovery documents now supplied | We can understand and reproduce the intended parser workflow without another backend transfer |
| Original files | Sender reports all four exact originals retained, with matching historical hashes, but withheld under the recorded scope | We do not have those original bytes here; verifying their hashes in a report is not verifying the files themselves |
| Unretained blocks | Report confirms other 914 bodies were not saved | Expansion requires new extraction/authoring, not recovery by renaming existing files |
| New work | Sender reports no additional code/content/review changes | No reason to wait for another full code ZIP for current work |
| Reviews | No new clinical/licence/localisation approvals supplied | Existing decisions remain preserved; new text must not inherit approvals |
| Deployment | No verified hosting project/domain supplied | Local progress can continue; deployment remains a later explicit task |
| Provider status | Handoff repeats an unresolved 401, but local direct execution evidence shows later successful replacement-key tests relative to the failure | Record the discrepancy; do not rotate keys or overwrite configuration solely because this report repeats old failure information |

The handoff's transfer restrictions are recorded project decisions. This verification does not independently establish that every binary is legally non-transferable. If the team wants broader transfer/use, obtain a specific rights decision rather than asking the exporter to silently disregard its recorded scope.

### API-key reconciliation

Our local `reports/local/provider-smoke/ledger-after-key-replacement-2.json` records:

- 16 September, 08:25:52 UTC: generation request succeeded with HTTP 200.
- 16 September, 08:25:55 UTC: embedding request succeeded with HTTP 200, three vectors and 1,536 dimensions.

The newer handoff report repeats a historical 401 but contains no new failed request from Kajal's machine. Therefore “currently broken” is not supported by that report alone. Conversely, an earlier successful call does not prove the key will still work at the next paid run. No provider call or credential inspection was made during 4B/4C. Recheck configured access when authorised embedding execution starts.

Do not copy the handoff's commands into the environment automatically. In particular, do not create competing key aliases, alter `.env`, test unrelated providers or change hosting accounts just because a supplied document suggests it.

## 3. Step 4C work actually implemented

Built a repeatable, source-bound authoring packet from the verified 4A material:

| Output | Count |
|---|---:|
| Structured draft expansion units | 46 |
| Words in these units | 7,991 |
| Source IDs represented | 4 |
| Units with explicit source timing ranges | 12 |
| Broad-stage units with no invented exact interval | 34 |
| Units containing/overlapping old selected evidence by normalised substring check | 10 |
| Complete preparation sections held out | 10 |
| Additional trailing-heading holds | 2 |
| New production candidates approved/imported | 0 |
| New corpus vectors or paid provider calls | 0 |

Each unit contains:

- Stable ID and content/metadata checksum.
- Exact text, derivative hash, character offsets and a reproducible text normalization.
- Source ID, direct canonical source URL, historical artifact hash and a **separate derivative version**. A derivative is not mislabelled as the historical original artifact.
- Topic and intended display-slot mappings using existing domain/slot types.
- Native source jurisdiction and proposed India target, kept distinct.
- Relevant personal-fact dependencies for future integration.
- Explicit timing only where stated in the source; broad-stage applicability is left visible for authoring rather than silently assigning all weeks.
- The existing five review roles/check categories and concrete unresolved issues, without invented reviewer decisions.
- Overlap references to existing evidence and source-level condition-key leads. These leads are not automatically applied as passage-specific conditions.

The domains include nutrition, movement, symptoms, wellbeing, journey/development, preparation and follow-up. A unit can belong to several domains; the domain totals are not unique new-chunk counts.

This packet does **not** add 46 wholly new independent facts to the existing 55 candidates. Ten overlap older evidence, and some material is general rather than tailored to a particular week. Deduplication and answerability review must precede admission.

## 4. Why this is a review-authoring packet, not a production ingestion run

The existing `EvidenceCandidate`/`IngestionRun` contracts require complete applicability and verified original parsed-block references. The recovered text proves its derivative offsets, but not every original PDF/HTML anchor or exact applicability interval.

Forcing these records through those contracts would require fabricating missing metadata or weakening original-source validation. Neither was done.

Instead, an **offline authoring-only `ExpansionUnit` contract** reuses the existing domain, display-slot, applicability and review-role types while explicitly representing unresolved provenance/applicability. This is a small preparation-boundary extension, not a replacement RAG architecture, database or public API. Production ingestion rejects these records as the wrong schema, and their publication/embedding/approval flags cannot be switched on.

There is no new database table, migration, runtime adapter, provider or public route. Original imported records, the 54 existing decisions and current UI were not modified. The existing Stage 1 production gates remain unchanged.

### Holds and a structural correction

- Professional supervisory instructions, care schedules, a flattened nutrient table and treatment material need audience/structure-specific authoring before candidate admission.
- Introductions or standalone headings are not counted as evidence units.
- Two later-trimester headings were trailing the preceding development paragraph in the earlier preparation grouping. The new authoring step separates these headings; it does not rewrite the source or attach the next trimester to the previous milestone.
- Sections above the existing 3,000-normalised-character threshold would be held for context-preserving splitting rather than silently truncated. No current emitted unit exceeds that threshold.

The report retains the held material references. It has not been deleted from the original or cleaned source files.

## 5. Tests and verification

**Final result: 102 tests passed, plus 30 subtests passed.** Five PyMuPDF/SWIG deprecation warnings remain.

Tests cover:

- Actual 4B archive/extraction integrity and archive/path failure cases.
- Actual recovered-text anchoring and deterministic authoring output.
- Schema validation, exact text hashes and metadata fingerprints.
- Rejection of edited text, changed offsets, changed domains, changed search text and mutated source bytes.
- Explicit refusal to treat authoring units as production `EvidenceCandidate` records.
- Inability to change authoring flags into approval/publication/embedding eligibility.
- Preserving source-literal trimester ranges rather than adopting conflicting UI labels.
- Keeping broad-stage applicability unresolved rather than inventing exact-week support.
- Holding professional/table/treatment material and separating trailing headings.
- A genuinely oversized synthetic section to test non-truncating hold behaviour.
- Related existing preparation, import, real-handoff, embedding-boundary and content regressions.

During the first test run, two new tests were incorrectly constructed: one “changed” offset to its existing value, and one assumed the real handoff contained an oversized section. They were corrected to perform a real offset mutation and a dedicated synthetic oversized-input test; production checks were not weakened. The final suite passes.

This was not a live chatbot test, medical validation, new provider smoke test, database expansion import or deployment test. Local database preservation was verified in 4A; this authoring code makes no database connection.

## 6. What remains inside Step 4C

Step 4C is **in progress**, not automatically complete because a packet now exists.

1. Resolve 34 broad-stage applicability intervals from source meaning and the intended product range, explicitly distinguishing an editorial proposal from a source-literal week range.
2. Reconcile the ten overlapping units with existing evidence and any different context/cautions. Keep canonical evidence and aliases where appropriate rather than double-counting.
3. Turn condition-key leads into justified passage-specific conditions; retain relevant clauses and exclusions. Do not assume breastfeeding, uncomplicated delivery, exercise clearance or dietary needs.
4. Reconcile the source-native and UI trimester conventions, without editing the source to conceal differences.
5. Decide the permitted source scope for new selected text and establish the required source anchors. Obtain eligible originals where needed, or deliberately specify and review a derived-text ingestion path; do not claim the original was checked when it was not.
6. Adapt/reconstruct held content only where needed and supported. Numeric tables, care schedules and supplement claims require particular care and current-source verification.
7. Record applicable genuine content/licence/clinical/localisation decisions, preserving old decisions for unchanged subjects only.
8. Convert admitted material to the existing ingestion/loader contract and verify additive import, conflicts, rollback and repeat safety before claiming the database corpus expanded.

Then Step 4D can generate eligible real embeddings, followed by retrieval/runtime and the existing dashboard/chat milestones. The earlier proposed operator-only development-index exception remains a separate unresolved decision; this packet does not grant it or constitute an embedding job.

## 7. Do we need anything else from Aswath now?

**No additional backend ZIP or API key is required to continue the current local authoring work.** This delivery does not contain a hidden populated RAG system we still need to transfer.

Remaining external dependencies are specific:

- Source-specific permission/anchor decisions if broader material or complete originals are needed.
- Appropriate review owners; another technical export cannot supply absent clinical approval.
- Account continuity/current shared budget before paid runs and later hosting access when a deployment target is chosen.

Optional correction to send him:

> We verified the 4B ZIP and all extracted files. Our local replacement-key ledger records successful generation and embedding requests on 16 September at 08:25 UTC, so please record your repeated 401 as historical/unverified current status, not a newly confirmed failure. No new key or full backend ZIP is needed for local authoring. We are continuing from the recovered text; please let us know only if new source-permission decisions or genuinely new assets become available.

Do not spend more time repeatedly searching for the same 914 unsaved bodies. If fuller content is required, use a new, source-versioned extraction workflow.

## 8. Files and reproducibility

Implementation:

- `scripts/verify_maya_recovery.py`
- `app/schemas/corpus_expansion.py`
- `app/services/corpus_expansion.py`
- `scripts/expand_maya_corpus.py`
- `tests/test_corpus_expansion.py`

Run in the existing dependency environment:

```text
python scripts/expand_maya_corpus.py --package "<inner discovery package>" --recovery-zip "<4B ZIP>" --recovery-root "<inner 4B extracted directory>"
```

Verified outputs:

- `reports/local/corpus-expansion/20260916T121741221622Z/recovery-verification.json`
- `reports/local/corpus-expansion/20260916T121741221622Z/expansion.json`
- `reports/local/corpus-expansion/20260916T121741221622Z/units.jsonl`
- `reports/local/corpus-expansion/20260916T121741221622Z/review-index.md`
- `reports/local/corpus-expansion/20260916T121741221622Z/output-sha256.json`
- `reports/local/corpus-expansion/step4bc-tests.xml`

Packet checksum: `ea2aadb8cf2707fa0887030e5e4ebbb90b3c2e7263bd663ca273439a1196a2be`. The final packet includes direct canonical URLs in every unit; the earlier 12:10 output is preserved but superseded.

Generated full-text outputs remain local and ignored by Git. Do not publicly redistribute them merely because they passed an engineering checksum check.

**Bottom line:** 4B clarified the remaining assets and removed uncertainty about what another export can supply. 4C now has a concrete, tested evidence-authoring packet. The source-review, applicability and integration work is still real work to finish—not something hidden behind an “all done” verdict.
