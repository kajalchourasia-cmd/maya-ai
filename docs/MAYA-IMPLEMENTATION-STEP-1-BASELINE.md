# Maya implementation — Step 1 baseline

Date: 16 September 2026  
Status: Current source preserved; targeted baseline checks complete. This is not a live-RAG readiness verdict.

## 1. Product contract

Use `MAYA-INTENDED-PRODUCT-EXPERIENCE-AND-DATA-FLOW-SPEC.md` as the current experience specification:

- Keep Kajal's frontend, light-theme default and growth-image library.
- No-login, isolated session-based onboarding; no document uploads in this phase.
- Four overview cards: Your journey, Nutrition focus, Energy focus, Movement focus.
- Pre-authored, sourced week/stage overview and standard FAQ tables; no runtime model/vector call for those displays.
- Detailed personalised guidance, Ask Maya and requested plans use actual evidence and the existing RAG/orchestration architecture.
- No invented symptoms, approvals, personal facts or live responses disguised by fixture fallback.

## 2. Checkpoint created and verified

Working repository:

`C:\Users\Hrishikesh\Developer\maya-ai-product-preview`

Branch: `fix/maya-onboarding-flow-local`  
HEAD: `81533e32103b60c3e705955137949b25d834baa3`

Checkpoint:

`C:\Users\Hrishikesh\Developer\maya-checkpoints\before-live-integration-20260916-124610`

- 690 existing tracked and non-ignored untracked files copied, approximately 55.25 MiB.
- Each copied file's SHA-256 compared against the source successfully at copy time.
- This preserves the current source/UI changes; it is not merely the last Git commit.
- Credentials, ignored dependency directories, generated caches and Git history were not copied.
- The existing local `.env` remains in place; it is ignored and not tracked by Git.
- The source repository and its Git history remain untouched.
- The checkpoint is not a database backup or a replacement for the three corpus handoff archives.

Restore by comparing and selectively copying required files from the checkpoint. Do not overwrite later user work or reset the repository blindly. This baseline report was written after the checkpoint and is therefore not inside it.

## 3. Handoff archive integrity

All three local ZIP hashes match the operational handoff:

| Archive | Verified SHA-256 |
|---|---|
| MAYA-CORPUS-HANDOFF-20260915T193957Z.zip | `0a4d4a7f727f45d640662534f018b97c705302591d22e3f6ce82bb194d5950d0` |
| MAYA-MISSING-CORPUS-DISCOVERY-20260915T211431Z.zip | `73544bebd1ba36ce70383d2b6d7cdcb3379a81ee89126d47f5fa6dd94f3a2408` |
| MAYA-EXISTING-ASSETS-ADDENDUM-20260916T024138Z.zip | `4b2efcce16362b74622f09a96f8b07a45729aaa661520492cc84cc101ab033a8` |

Archive integrity does not establish content completeness, publication approval or working retrieval. Internal manifest verification from earlier review is separate from this turn's archive checks.

## 4. Baseline results

| Check | Result | Meaning |
|---|---|---|
| Growth/journey/theme Node tests | 19 passed, 0 failed | Existing lookup, asset, timeline and selected theme contracts passed |
| TypeScript | Passed, exit 0 | Frontend type-check completed with incremental writes disabled |
| Selected Python tests | 36 passed, 2 failed | Existing guidance, runtime/access and UI restoration test selection; not the full backend suite |
| Local migration inventory | 17 SQL files present | Files exist; they have not been applied to a local Maya database in this step |
| Docker read-only check | Accessible through desktop-linux | Existing n8n container/volume preserved; no Maya/Supabase stack present |
| Secret-file Git check | `.env` ignored and untracked | No credential values printed or copied into the checkpoint |

Selected Python files:

- `tests/test_dashboard_guidance.py`
- `tests/test_product_runtime_integration.py`
- `tests/test_maya_runtime_access.py`
- `tests/test_maya_ui_restoration.py`

Frontend tests:

- `frontend/tests/growth-card.test.cjs`
- `frontend/tests/journey-progress.test.cjs`
- `frontend/tests/purple-theme.test.cjs`

### Two recorded Python test failures

1. `test_only_source_linked_general_measurements_enter_dashboard` expects the older `generalWeekMeasurementReferences` path and older display text. The current UI imports `getGrowthMeasurements`; its newer Node tests passed. The test must be reconciled with the approved design while retaining substantive provenance/measurement assertions.
2. `test_review_state_is_visible_per_week` expects visible `Product direction accepted` and `Product review pending` labels. These conflict with Kajal's previous presentation changes and the newer growth-card test. Keep review metadata accurate without automatically restoring those labels to the main card.

No tests were weakened, deleted or rewritten in this baseline step. No claim of full medical/source accuracy follows from the structural tests.

## 5. Environment observations

- Bundled Python: 3.12.14.
- Existing checkout-local `.local-api-deps` provides pytest 9.1.1, pydantic 2.13.5 and FastAPI 0.116.1.
- The selected tests passed/failed as recorded after allowing access to those dependencies outside the sandbox. Initial sandbox import failure was an access problem, not proof that all dependencies were absent.
- No project `.venv\Scripts\python.exe` was found at the checked path.
- Root package pins Supabase CLI 2.117.0, but `node_modules\.bin\supabase.cmd` was not present at the checked path.
- Existing Supabase configuration uses project ID `nestline` and local ports 54321/54322/54323. Before starting a new stack, establish an isolated project identity and verify port availability; do not touch unrelated containers.
- Existing frontend configuration includes development port 5173; the intended local UI has also been used on 5180. Select and document one actual running frontend/backend pair instead of assuming the package default matches the current session.

## 6. What is still unconnected

- `get_product_runtime()` returns `UnconnectedProductRuntime`; ordinary product chat and plans are not connected to the intended corpus.
- Dashboard educational guidance uses a local reference catalogue, not the populated Stage 5 retrieval store.
- The new week/stage KPI and FAQ content tables have been specified but are not yet authored/integrated.
- No local Maya knowledge database, real indexed corpus or complete live query has been established by this baseline.
- Two provider setting families exist locally; configuration must be reconciled before enabling paid calls.

## 7. Next implementation milestones

1. **Local infrastructure and configuration:** isolated Supabase stack; existing migrations; explicit backend/frontend ports; one provider configuration mapping; safe cost accounting.
2. **Knowledge ingestion and retrieval:** source applicability/review audit; transactional loader; real embeddings under the recorded permissions/budgets; actual query traces with evidence IDs and citations. Development and public-release eligibility remain distinct.
3. **Deterministic weekly overview:** prepare and verify nutrition/energy/movement overview and FAQ tables; connect timeline and local context rules without provider calls.
4. **Dashboard content:** nutrition and movement, followed by symptoms, wellbeing and do's/don'ts; shared context and evidence across sections.
5. **Ask Maya and plans:** connect the existing orchestration/validation path, session history, citations and requested plan revisions.
6. **Integrated verification:** fresh sessions, changed timelines/constraints, provider errors, relevant safety cases, source coverage and actual browser flows. Reconcile the two stale tests against substantive behaviour.
7. **Deployment preparation:** only after local verification; do not treat local success as proof that hosting and public-release conditions are complete.

Provider budgets recorded in the operational handoff: OpenAI USD 30 maximum and xAI USD 5 maximum, separately tracked. No provider call or paid usage occurred during Step 1. Existing account/project usage must be considered before allocating the remaining budgets.

## 8. Scope of this step

Completed: source checkpoint, archive checks, targeted tests and environment inventory.

Not performed: application edits, database creation/migration/reset, provider calls, content publication, Git commit/push, hosted changes or deployment. The two test failures and remaining runtime gaps are recorded, not hidden.
