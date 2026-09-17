# Maya AI Stages 5–10 final integrated verification

## Executive verdicts

- `STAGES 5–8 CORRECTION PRESERVED: GO`
- `RAPID STAGE 9 FUNCTIONAL UI: GO`
- `ASK MAYA CONTROLLED FLOW: GO`
- `STAGE 10 STATE LIFECYCLE: GO`
- `INTEGRATED FICTIONAL-DATA CAPSTONE DEMO: GO`
- `LIVE PROVIDER EXPERIENCE: NO-GO`
- `PUBLIC/CLINICAL RELEASE: NO-GO`

The five GO verdicts cover controlled local engineering and fictional-data capstone review only. They do not authorize public use, clinical claims, deployment, remote database changes, real reviewer operations, or real personal/medical data.

## Exact repository lineage

| Checkpoint | Branch/role | Commit |
|---|---|---|
| Accepted corrected foundation | `fix/stages-5-8-integration-closure` | `e2a8c542648f97c9bb93d73528f2414a4f41e5c8` |
| Corrected Stage 9 full UI | integration ancestry | `c830ab3` |
| Rapid Stage 9 functional layer | integration ancestry | `516315e` |
| Stage 9 checkpoint report | integration ancestry | `078b21b` |
| Restored Stage 10 checkpoint | `integration/capstone-demo-final` | `a044ecb8fd2be9c7986c8401367956f85bcbd3e6` |
| Verified implementation/evidence commit | `integration/capstone-demo-final` | `70f3f0e9f7f88196012bf7af8188966e3079161c` |
| Report metadata follow-up | `integration/capstone-demo-final` | exact non-self-referential remote head is reported outside this commit |

`git merge-base --is-ancestor e2a8c542648f97c9bb93d73528f2414a4f41e5c8 HEAD` returned 0. The old Stage 10 work was first preserved, its original stash remains retained, and the restoration was applied on the integration ancestry rather than on `main`.

## Scope delivered

This integrated branch:

1. preserves and revalidates the accepted Stage 5 retrieval, Stage 6 deterministic safety, Stage 7 bounded orchestration, and Stage 8 validation/answer composition;
2. provides the complete local Stage 9 Streamlit shell plus the requested rapid landing, onboarding, dashboard, Ask Maya, plan, records, evidence, safety, and evaluator flows;
3. restores Stage 10 through one authenticated State Committer;
4. implements fact decisions, complete plan lifecycle, selective dependency invalidation, in-app follow-up, reminder consent, truthful simulated review, idempotency, concurrency, deletion/reset, and durable mode/workspace isolation;
5. runs the three connected fictional capstone stories three times each;
6. keeps public health routing, external delivery, real review, deployment, and live-provider claims disabled.

## Stage 5–8 preservation evidence

The canonical consolidated checker passes with no errors:

| Stage | Evidence | Result |
|---|---|---|
| Stage 5 | frozen paraphrase set | 12/12 PASS |
| Stage 5 | retrieval development truth | 28/28 expected behavior, support state, and journey relation |
| Stage 5 | Recall@5 | 18/18 |
| Stage 5 | citation/evidence precision | 18/18 |
| Stage 5 | confirmed-personal-fact precision | 12/12 |
| Stage 5 | graph-path correctness | 1/1 |
| Stage 5 | forbidden decoys/leakage | 0 wrong-week, wrong-jurisdiction, unapproved, or cross-workspace results |
| Stage 5 | rectification matrix | 212 deterministic cases represented by the checker |
| Stage 6 | safety development cases | 55/55; critical 51/51 |
| Stage 6 | urgent zero-generation cases | 27/27 |
| Stage 6 | zero tested unsafe reassurance | 55/55 |
| Stage 7 | orchestration development cases | 76/76; critical 64/64 |
| Stage 7 | urgent zero-agent-generation | 5/5 |
| Stage 7 | one-domain minimal routing | 6/6 |
| Stage 7 | communication/no-direct-write contract | 66/66 each |
| Stage 8 | validation development cases | 69/69; critical 57/57 |
| Stage 8 | validator catalogue | 7/7 controls with positive and negative coverage |
| Stage 8 | persistent writes | 0 across 67 applicable cases |

The two approved trace-metadata corrections remain preserved: current reduced-movement wording conservatively clarifies with zero ordinary generation and remains an open qualified-policy gap; historical nausea records preserve `S-CLARIFY` trace attribution without turning history into a current symptom. The current-symptom nausea contrast still clarifies with zero ordinary generation.

## Rapid Stage 9 functional UI

### Product surface

The local Streamlit entry remains `streamlit_app.py`. The app provides:

- landing and explicit Personal/Demo mode choice;
- five-step review-first onboarding;
- journey dashboard with three KPIs and eight user-facing tabs;
- persistent Ask Maya entry and suggested prompts;
- validated response blocks, provenance labels, applied constraints, citations, abstention, clarification, and urgent fixed-message surfaces;
- day/week plan inspection and Stage 10-backed review/save states;
- records, extracted-field review, provenance, conflicts, and evidence drawer;
- truthful simulated review states;
- separate evaluator view backed by generated artifacts.

Personal Mode begins empty. Demo Mode is visibly fictional and deterministic. The reset clears Stage 9 and Stage 10 temporary UI namespaces. The product states that it is an educational/organizational prototype and warns against entering real personal or medical information in the demo.

### UI evidence

- Stage 9 development cases: **42/42**; critical **29/29**.
- Stage 9 repeated stories: **9/9**.
- Pages/surfaces: **9**.
- Shared loading/empty/success/error/safety/stale/unavailable state coverage: **8** states.
- Dashboard agent fan-out on load: **0**.
- Urgent ordinary-generation calls: **0**.
- Stage 9 direct persistence writes before State Committer integration: **0**.
- Responsive screenshots counted by the checker: **19**, with additional rapid evidence images and redacted JSON walkthrough records.
- Keyboard walkthroughs: **1 internal deterministic walkthrough**, accurately labelled and not claimed as user research or WCAG certification.

Representative evidence is under `docs/stage9-ui-evidence/`, including desktop home/chat/records/plan/evidence/review/evaluator states, phone home/records/plan/urgent states, and rapid landing/onboarding/dashboard/Ask Maya captures.

## Ask Maya controlled flow

Ask Maya routes inputs through the accepted boundaries:

1. Stage 6 Safety Gate first;
2. Stage 7 bounded route/worker selection;
3. Stage 5 authenticated retrieval as required;
4. Stage 8 claim/evidence/citation/constraint validation;
5. deterministic display composition;
6. Stage 10 State Committer only after an explicit user write action.

Urgent and unresolved safety routes bypass ordinary generation. Invalid, unsupported, uncertain, stale, or conflicting answers clarify or abstain. Medication remains record-only. The UI never treats a chat answer as a saved personal fact or plan.

`ASK MAYA CONTROLLED FLOW: GO` means the deterministic and fictional-provider paths are connected and locally testable. A live provider-quality verdict remains NO-GO because no paid/live benchmark was authorized or run.

## Stage 10 state lifecycle and security

### Single write boundary

All product mutations enter `public.stage10_commit(uuid,jsonb)` using an authenticated JWT. Identity and workspace ownership come from database/session truth. Strict schemas, exact JSON keys, payload size, provenance, confirmation, state version, lifecycle, hard constraints, and idempotency are checked before mutation. The private implementation is not executable by ordinary users. Agents and models have no direct write authority or service-role credential.

### Facts and plans

Fact proposals can be explicitly confirmed, corrected, or rejected. Source provenance and extraction history remain intact; corrections create supersession rather than erasure. Only committed confirmed facts can personalize.

Plans implement all seven states: `draft`, `user_reviewed`, `saved`, `active`, `stale`, `replaced`, and `archived`. Save/activation reloads the current authenticated state. A Streamlit rerun or repeated click is not confirmation. User edits pass the same Stage 8 safety/evidence/constraint controls.

### Selective invalidation

Plans store exact journey, allergy, restriction, condition, symptom, medication/supplement, clinician-instruction, and evidence dependencies used. A relevant committed change stales only affected plans and stores a causal trail. An unrelated change does not stale a plan. Missing dependency data fails visibly. Nothing automatically regenerates, replaces, saves, or activates a plan.

### Concurrency, idempotency, and deletion

The two-principal authenticated matrix passed **26/26** checks:

- three simultaneous races each produced exactly one committed and one rejected command;
- exact and response-loss replay returned the same logical result;
- same key/different payload was rejected;
- the same key was isolated across workspaces;
- stale versions returned immediate `PT409` conflict rather than a retry timeout;
- workspace reset deleted all 10 checked public product table scopes plus private lifecycle/idempotency state;
- another workspace remained unchanged;
- a recreated workspace could not replay the deleted workspace's key.

### Follow-up and simulated review

In-app tasks require typed provenance. Reminder intent requires opt-in, exact time, timezone, and channel. External delivery remains unavailable and is never shown as sent. Simulated review uses a minimized consented packet and explicit state machine. Urgent fixed guidance happens immediately and never waits for that workflow.

## Database verification

Two independent histories were verified.

### Exact accepted Stage 9 → Stage 10 upgrade

1. reset to migration `20260911001300` without seed;
2. load the Stage 9 upgrade fixture;
3. apply `20260912000100` and `20260912000200`;
4. run the upgrade contract;
5. run every pgTAP file, every authenticated API checker, and database lint.

Result: **325/325 pgTAP**, **110/110 authenticated API**, **0 lint findings**.

### Clean installation

Result: **325/325 pgTAP**, **110/110 authenticated API**, **0 lint findings**.

pgTAP denominators per history:

- Stage 2 security/lifecycle: 122;
- Stage 3 exit criteria: 12;
- Stage 3 onboarding: 26;
- Stage 4 API role: 11;
- Stage 4 documents: 35;
- Stage 5 hybrid retrieval: 48;
- Stage 10 lifecycle: 38;
- Stage 10 hardening/reset: 33;
- total: **325**.

Authenticated API denominators per history:

- Stage 2 storage: 13;
- Stage 3 onboarding: 17;
- Stage 4 documents: 15;
- Stage 5 retrieval: 25;
- Stage 10 state lifecycle: 14;
- Stage 10 concurrency/deletion: 26;
- total: **110**.

## Connected fictional capstone stories

All three stories passed three deterministic reset runs: **9/9**.

1. **New user to saved plan:** resolve fictional P10, confirm fictional allergy/restriction, generate a sourced plan, edit, validate, explicitly review/save, and display committed version.
2. **Document to stale plan:** ingest fictional document evidence, confirm/correct facts, preserve graph dependency, create appointment question, and show only the affected plan as stale.
3. **Urgent safety to simulated review:** curated red flag returns fixed urgent handling with zero ordinary generation, then separately records consent for a minimum simulated packet with truthful state/trace.

No story required manual database editing. Passing fictional development stories is software-contract evidence, not clinical validation.

## Consolidated verification results

| Verification | Result |
|---|---|
| Full Python suite | 480/480 PASS |
| Content authoring validation | 63 profiles, 31 sources, 55 evidence spans, 56 fragments, 0 errors |
| Content review-ready validation | PASS as governed draft/review-ready data |
| Content contracts | 64/64 PASS |
| Journey evaluations | 26/26 PASS |
| Stage 1 checker | PASS |
| Stage 2 checker | PASS |
| Stage 3 checker + UI smoke | PASS |
| Stage 4 readiness/checker/UI smoke | PASS |
| Stage 5 checker + retrieval/paraphrase | PASS |
| Stage 6 checker/evaluation | PASS, 55/55 |
| Stage 7 checker/evaluation | PASS, 76/76 |
| Stage 8 checker/evaluation | PASS, 69/69 |
| Consolidated Stage 5–8 checker | PASS |
| Stage 9 checker/UI/evaluation | PASS, 42/42 + 9/9 stories |
| Stage 10 checker/UI/evaluation | PASS, 33/33 + 9/9 stories |
| Clean pgTAP | 325/325 PASS |
| Upgrade pgTAP | 325/325 PASS |
| Clean authenticated API | 110/110 PASS |
| Upgrade authenticated API | 110/110 PASS |
| Database lint | 0 findings |
| Compileall | PASS |
| `git diff --check` | PASS |
| Secret-pattern scan over tracked files | 0 credential-shaped matches |

The Stage 0 **publication** checker remains intentionally non-green because the repository still has zero publicly released weekly profiles and outstanding clinical, India-localisation, licence, and product approvals. This is the evidence for `PUBLIC/CLINICAL RELEASE: NO-GO`; draft material was not promoted merely to obtain a passing release signal.

## First review findings and consolidated corrections

| Finding | Correction | Evidence |
|---|---|---|
| Legacy Stage 2 tests expected direct table mutation after Stage 10 | kept direct writes denied and changed final-schema assertions to verify read plus denial; retained 122 assertions | Stage 2 pgTAP 122/122 in clean and upgrade |
| Public RPC wrapper accepted broader JSON | exact-key, nested-key, type and 64 KiB checks | hardening pgTAP 33/33 |
| Private implementation boundary was callable too broadly | revoked execution and fixed search paths | anonymous/authenticated negative API/pgTAP tests |
| Application stale conflict used retryable `40001` | changed to `PT409` | three races complete without timeout |
| Concurrency evidence was sequential | added true simultaneous authenticated HTTP requests | 26/26 API matrix |
| Workspace deletion could leave ledgers/self-references | ordered reset/delete trigger and retention inventory | 10 public scopes zero; no replay after recreation |
| Stage 10 UI state could remain after Demo reset | reset both Stage 9 and Stage 10 namespaces | focused reset regression |
| Upgrade fixture fingerprint collided with older fixture | replaced with a unique fictional digest | exact upgrade 325/325 |
| New UI shell broke old smoke navigation | navigated legacy scripts through the shell and restored expected title/privacy warning | Stage 3/4/9/10 UI checks pass |
| Stage 9 screenshot gate initially lacked sufficient evidence | retained the stricter threshold and added real fictional/redacted captures | checker counts 19 responsive screenshots |

## Honest issue and limitation register

| ID | Severity | Evidence and effect | Disposition | Blocks controlled local demo | Blocks public/clinical release |
|---|---|---|---|---|---|
| INT-PUBLIC-CONTENT | High | zero published weekly profiles and incomplete content approvals | public/live material stays hidden/fail-closed | No | Yes |
| INT-SAFETY-REVIEW | High | safety spec remains draft; reduced-movement routine policy gap remains open | evaluation-only deterministic boundary; qualified review required | No | Yes |
| INT-LIVE-PROVIDER | Medium | no authorized live semantic/provider benchmark | fake/deterministic provider truth shown | No | Yes for provider claims |
| INT-REAL-REVIEW | High | no real clinician operation or service | all review states visibly simulated | No | Yes |
| INT-EXTERNAL-DELIVERY | Medium | email/SMS/push/n8n not implemented | UI states unavailable; no fake scheduling/sending | No | Yes for notification claims |
| INT-PRIVACY-LEGAL | High | no final privacy/legal/retention approval | local fictional data only | No | Yes |
| INT-SEALED-HOLDOUT | Medium | sealed holdout intentionally unopened | prevents overfitting; final generalization unmeasured | No | Yes for final quality claim |
| INT-USABILITY | Medium | internal keyboard/walkthrough evidence only | no claim of formal user research or WCAG conformance | No | Yes for usability/conformance claims |
| INT-CI | Low | GitHub ran both required jobs on implementation SHA `70f3f0e9f7f88196012bf7af8188966e3079161c` | `validate` and `supabase-integration` passed; report-only follow-up is rechecked separately | No | No |
| INT-STASH | Low | original Stage 10 recovery stash remains | retained intentionally for recoverability until review | No | No |

## Migration, configuration, provider, and external-action impact

- Two forward-only Stage 10 migrations are present; neither was applied remotely.
- CI now runs every pgTAP test and all six authenticated API checkers on the exact Stage 9 upgrade, the older supported upgrade, and clean install paths.
- No new secret or paid provider is required for deterministic tests.
- `.env.example` contains placeholder names only.
- Local database verification requires Docker and Supabase CLI.
- No provider credits, external messages, reminders, review packets, deployments, domains, hosting projects, remote migrations, PRs, merges, or `main` updates occurred.
- No real personal or medical data is present in committed fixtures or screenshots.

## Exact commands used

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -q
.venv\Scripts\python.exe -m scripts.validate_content
.venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
.venv\Scripts\python.exe -m scripts.run_contract_evals
.venv\Scripts\python.exe -m scripts.run_journey_evals
.venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals
.venv\Scripts\python.exe -m scripts.run_stage5_paraphrase_evals
.venv\Scripts\python.exe -m scripts.run_stage6_safety_evals
.venv\Scripts\python.exe -m scripts.run_stage7_evals
.venv\Scripts\python.exe -m scripts.run_stage8_evals
.venv\Scripts\python.exe -m scripts.run_stage9_evals
.venv\Scripts\python.exe -m scripts.run_stage10_evals
.venv\Scripts\python.exe -m scripts.check_stage1
.venv\Scripts\python.exe -m scripts.check_stage2
.venv\Scripts\python.exe -m scripts.check_stage3_ui
.venv\Scripts\python.exe -m scripts.check_stage3
.venv\Scripts\python.exe -m scripts.check_stage4_readiness
.venv\Scripts\python.exe -m scripts.check_stage4_ui
.venv\Scripts\python.exe -m scripts.check_stage4
.venv\Scripts\python.exe -m scripts.check_stage5
.venv\Scripts\python.exe -m scripts.check_stage6
.venv\Scripts\python.exe -m scripts.check_stage7
.venv\Scripts\python.exe -m scripts.check_stage8
.venv\Scripts\python.exe -m scripts.check_stages5_8_rectification
.venv\Scripts\python.exe -m scripts.check_stage9_ui
.venv\Scripts\python.exe -m scripts.check_stage9
.venv\Scripts\python.exe -m scripts.check_stage10_ui
.venv\Scripts\python.exe -m scripts.check_stage10 --write-report
pnpm exec supabase db reset --local --version 20260911001300 --no-seed
pnpm exec supabase migration up --local
pnpm exec supabase test db --local <each supabase/tests/*.test.sql>
.venv\Scripts\python.exe -m scripts.check_stage2_storage_api
.venv\Scripts\python.exe -m scripts.check_stage3_onboarding_api
.venv\Scripts\python.exe -m scripts.check_stage4_document_api
.venv\Scripts\python.exe -m scripts.check_stage5_retrieval_api
.venv\Scripts\python.exe -m scripts.check_stage10_state_api
.venv\Scripts\python.exe -m scripts.check_stage10_concurrency_and_deletion_api
pnpm exec supabase db lint --local --schema public --schema private
.venv\Scripts\python.exe -m compileall -q app scripts tests
git diff --check
```

## Machine-readable and visual evidence

- `docs/STAGES-5-TO-8-RECTIFICATION-CHECK-RESULTS.json`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-6-SAFETY-EVAL-RESULTS.json`
- `docs/STAGE-7-EVAL-RESULTS.json`
- `docs/STAGE-8-EVAL-RESULTS.json`
- `docs/STAGE-9-EVAL-RESULTS.json`
- `docs/STAGE-9-CHECK-RESULTS.json`
- `docs/STAGE-10-EVAL-RESULTS.json`
- `docs/STAGE-10-CHECK-RESULTS.json`
- `docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json`
- `docs/STAGE-10-DELETION-RETENTION-INVENTORY.json`
- `docs/STAGE-10-SELF-REVIEW-FINDINGS.json`
- `docs/stage9-ui-evidence/`

## GitHub and review status

The implementation/evidence commit `70f3f0e9f7f88196012bf7af8188966e3079161c` is pushed to Kajal's `integration/capstone-demo-final` branch. GitHub `validate` and `supabase-integration` both passed on that exact SHA: [workflow run](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34697772681), [validate job](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34697772681/job/103564108697), and [Supabase integration job](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34697772681/job/103564108664). No PR, merge, or deployment was performed.

## Complete changed-file inventory from the accepted Stage 5–8 base

- `.env.example`
- `.github/workflows/data-contracts.yml`
- `app/pages_and_components/onboarding.py`
- `app/pages_and_components/rapid_stage9.py`
- `app/pages_and_components/stage9.py`
- `app/schemas/product_experience.py`
- `app/schemas/state_lifecycle.py`
- `app/services/capstone_flows.py`
- `app/services/product_experience.py`
- `app/services/state_committer.py`
- `assets/stage9/week-24-journey.svg`
- `data/schemas/product_experience.schema.json`
- `data/schemas/state_lifecycle.schema.json`
- `docs/NESTLINE-STAGES-5-TO-10-FINAL-INTEGRATED-VERIFICATION.md`
- `docs/STAGE-0-CHECK-RESULTS.json`
- `docs/STAGE-10-CAPSTONE-STORY-RESULTS.json`
- `docs/STAGE-10-CHECK-RESULTS.json`
- `docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json`
- `docs/STAGE-10-COVERAGE-MANIFEST.json`
- `docs/STAGE-10-DELETION-RETENTION-INVENTORY.json`
- `docs/STAGE-10-EVAL-RESULTS.json`
- `docs/STAGE-10-IMPLEMENTATION-SELF-VERIFICATION-AND-CAPSTONE-READINESS.md`
- `docs/STAGE-10-SELF-REVIEW-FINDINGS.json`
- `docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json`
- `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-9-CHECK-RESULTS.json`
- `docs/STAGE-9-COVERAGE-MANIFEST.json`
- `docs/STAGE-9-DEMO-WALKTHROUGH-RESULTS.json`
- `docs/STAGE-9-EVAL-RESULTS.json`
- `docs/STAGE-9-IMPLEMENTATION-SELF-VERIFICATION-AND-STAGE-10-READINESS.md`
- `docs/STAGE-9-LOCAL-RUNBOOK.md`
- `docs/STAGE-9-RAPID-FUNCTIONAL-UI-CHECKPOINT.md`
- `docs/STAGE-9-SELF-REVIEW-FINDINGS.json`
- `docs/stage9-ui-evidence/desktop-compass-validated.png`
- `docs/stage9-ui-evidence/desktop-evaluator.png`
- `docs/stage9-ui-evidence/desktop-evidence.png`
- `docs/stage9-ui-evidence/desktop-home.png`
- `docs/stage9-ui-evidence/desktop-plan.png`
- `docs/stage9-ui-evidence/desktop-records.png`
- `docs/stage9-ui-evidence/desktop-simulated-review.png`
- `docs/stage9-ui-evidence/keyboard-walkthrough.json`
- `docs/stage9-ui-evidence/phone-home.png`
- `docs/stage9-ui-evidence/phone-plan.png`
- `docs/stage9-ui-evidence/phone-records.png`
- `docs/stage9-ui-evidence/phone-urgent.png`
- `docs/stage9-ui-evidence/rapid-ask-maya.png`
- `docs/stage9-ui-evidence/rapid-dashboard.png`
- `docs/stage9-ui-evidence/rapid-evidence.png`
- `docs/stage9-ui-evidence/rapid-landing.png`
- `docs/stage9-ui-evidence/rapid-onboarding-review.png`
- `docs/stage9-ui-evidence/rapid-plan.png`
- `docs/stage9-ui-evidence/rapid-records.png`
- `docs/stage9-ui-evidence/rapid-urgent.png`
- `docs/stage9-ui-evidence/rapid-visual-inspection.json`
- `docs/stage9-ui-evidence/visual-inspection.json`
- `evals/README.md`
- `evals/stage10_state_lifecycle.jsonl`
- `evals/stage9_product_experience.jsonl`
- `scripts/build_stage10_evals.py`
- `scripts/capture_rapid_stage9_evidence.py`
- `scripts/check_stage10_concurrency_and_deletion_api.py`
- `scripts/check_stage10_state_api.py`
- `scripts/check_stage10_ui.py`
- `scripts/check_stage10.py`
- `scripts/check_stage3_ui.py`
- `scripts/check_stage4_ui.py`
- `scripts/check_stage9_ui.py`
- `scripts/check_stage9.py`
- `scripts/export_product_experience_schema.py`
- `scripts/export_stage10_retention_inventory.py`
- `scripts/export_stage10_self_review.py`
- `scripts/export_state_lifecycle_schema.py`
- `scripts/run_stage10_evals.py`
- `scripts/run_stage9_evals.py`
- `scripts/stage10_fixture_support.py`
- `streamlit_app.py`
- `supabase/fixtures/stage10_stage9_upgrade_check.sql`
- `supabase/fixtures/stage10_stage9_upgrade.sql`
- `supabase/migrations/20260912000100_stage10_state_review_lifecycle.sql`
- `supabase/migrations/20260912000200_stage10_rpc_hardening_and_reset.sql`
- `supabase/tests/stage10_rpc_hardening_and_reset.test.sql`
- `supabase/tests/stage10_state_review_lifecycle.test.sql`
- `supabase/tests/stage2_security_and_lifecycle.test.sql`
- `tests/test_capstone_flows.py`
- `tests/test_product_experience.py`
- `tests/test_state_lifecycle.py`

## Required next decisions

1. Ask Kajal to independently review `integration/capstone-demo-final` and its generated evidence.
2. Create or merge a PR only after that review and a separate explicit decision.
3. Keep deployment, remote migrations, public content, real review, and external notifications blocked until their separate owners approve them.
