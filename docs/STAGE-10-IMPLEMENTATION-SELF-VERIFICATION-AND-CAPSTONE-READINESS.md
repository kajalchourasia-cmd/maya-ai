# Stage 10 implementation, self-verification, and capstone readiness

**Evidence status:** the Stage 10 implementation and its local integration verification are complete on the corrected Stage 5–8 foundation. Public/clinical release remains blocked by human review, released-content, and live-provider gates.

## Verdict

`STAGE 10 ACCEPTED FOR CONTROLLED ENGINEERING — CAPSTONE READY FOR INDEPENDENT REVIEW`

Equivalent release-preparation boundary: `STAGE 10 ACCEPTED FOR CONTROLLED CAPSTONE VALIDATION — RELEASE PREPARATION MAY BEGIN`.

This GO applies to a local, fictional-data, controlled capstone review. It does not authorize deployment, remote migrations, public health guidance, real clinician operations, external notifications, or use of real personal/medical data.

## Repository and entry evidence

- Corrected Stage 5–8 base: `e2a8c542648f97c9bb93d73528f2414a4f41e5c8`.
- Corrected Stage 9 checkpoint: `078b21b` on the ancestry of this branch.
- Stage 10 restored implementation checkpoint: `a044ecb8fd2be9c7986c8401367956f85bcbd3e6`.
- Integration branch: `integration/capstone-demo-final`.
- The corrected base is an ancestor of the integration branch (`git merge-base --is-ancestor` exit 0).
- Verified implementation/evidence commit: `70f3f0e9f7f88196012bf7af8188966e3079161c`; the report-only follow-up SHA is reported outside its own commit.
- The original recovery stash remains preserved as `stash@{0}`.
- No PR, merge, force-push, deployment, remote migration, external message, notification, paid-provider call, or real patient-data operation occurred.

## Plain-language behavior

The app now has one guarded doorway for saved changes. Chat and workers can suggest a fact, task, review packet, or plan, but cannot save it directly. The authenticated user must review and explicitly submit a typed command. The State Committer checks the real session workspace, current version, provenance, consent, constraints, and allowed transition inside one database transaction.

A duplicate submission returns the original logical result. Two stale commands racing from the same version cannot both win. A material confirmed change marks only dependent plans stale and records the causal connection. Deleting a workspace clears the public product rows and private Stage 10 ledgers, so recreating a workspace cannot replay an old idempotency result.

## Requirement-to-implementation map

| Requirement | Implementation | Verification evidence |
|---|---|---|
| Single authorized write boundary | `app/services/state_committer.py`; `public.stage10_commit(uuid,jsonb)` | unit tests, 71 Stage 10 pgTAP assertions, 40 authenticated API/concurrency checks |
| Trusted authenticated scope | RPC derives caller from `auth.uid()` and checks owner membership | forged-scope, cross-workspace, anonymous and direct-write denials |
| Strict command/result contracts | `app/schemas/state_lifecycle.py`; strict SQL JSON-key and 64 KiB checks | 33 typed development cases; malformed/extra/oversized payload tests |
| Atomic versioned commits | private implementation uses a transaction, expected state version, ledgers and state increments | stale-write, rollback and three simultaneous race matrices |
| Idempotency | workspace-scoped key uniqueness plus command hash and committed response | replay, same-key/different-payload, response-loss and reset tests |
| Fact confirm/correct/reject | decision ledger, exact provenance, supersession and confirmation state | unit, pgTAP and authenticated API coverage |
| Plan lifecycle | `draft`, `user_reviewed`, `saved`, `active`, `stale`, `replaced`, `archived` | complete valid/invalid transition matrix |
| User-edit validation | Stage 8 validation disposition, source evidence, constraints and unresolved-conflict checks | unsafe edit and stale snapshot rejection cases |
| Selective staleness | normalized dependency rows and table-specific invalidation triggers | relevant-change positive and unrelated-change negative tests |
| Graph continuity | plan/fact/document nodes and causal edges | document → fact/restriction → plan item → stale plan → question story |
| Follow-ups/reminders | typed in-app tasks; reminder consent/date/time/timezone/channel; external delivery false | missing-consent/field and unavailable-delivery tests |
| Simulated review | minimal consented packet and nine-state transition graph | minimum-data, decline, timeout, unavailable, duplicate and urgent-independence tests |
| Personal/Demo persistence isolation | authenticated workspace state plus deterministic mode reset | UI, API, reset/deletion and two-principal checks |
| Clean and upgrade migrations | forward migrations `20260912000100` and `20260912000200` | clean replay and exact Stage 9 → Stage 10 upgrade, each with 325/325 pgTAP and 110/110 API checks |

## State Committer contract

Seven command kinds are supported through the one write boundary:

1. `fact_decision`;
2. `plan_create`;
3. `plan_transition`;
4. `follow_up_create`;
5. `follow_up_transition`;
6. `review_create`;
7. `review_transition`.

Every command carries a schema version, command ID, idempotency key, expected state version, timestamp, typed payload, provenance, and explicit actor/confirmation evidence where applicable. Unknown keys, oversized JSON, invalid identifiers, malformed nested objects, unsupported transitions, missing consent, stale versions, unresolved conflicts, unsafe plan content, or unauthorized scope are rejected without a partial write.

The public wrapper is executable only by `authenticated`. Its implementation function is private, has a fixed search path, and cannot be called by ordinary clients. The caller-supplied workspace is only a target to authorize; it never establishes identity. Ordinary clients and agents have read-only table access where required and cannot mutate Stage 10-owned facts, plans, items, reviews, ledgers, or dependencies directly.

## Idempotency and concurrency

The database-connected matrix used two authenticated fictional principals and independent HTTP RPC requests. It passed **26/26** checks:

- same key in different workspaces is isolated;
- exact replay and response-loss replay return the committed result;
- same key with different payload is rejected;
- concurrent plan saves: 1 committed, 1 rejected;
- fact change versus save: 1 committed, 1 rejected;
- fact change versus activate: 1 committed, 1 rejected;
- a stale retry returns current state for review;
- workspace deletion removes all checked product state;
- the other workspace remains unchanged;
- a recreated workspace cannot replay the old workspace's idempotency result.

The first implementation used SQLSTATE `40001` for an application-level stale version. PostgREST treated it as a retryable serialization failure, causing the caller to wait until timeout. Migration `20260912000200_stage10_rpc_hardening_and_reset.sql` changes this to `PT409`, preserving the conflict response while returning immediately.

## Fact confirmation and correction

Document-derived proposals retain source document, page, exact span, extraction confidence, and confirmation status. Confirm, correct, and reject are explicit user actions. Correction creates a new version and a supersession link; it never rewrites source history. Only successfully committed confirmed facts can personalize later reads. Unconfirmed, rejected, conflicting, and superseded facts remain excluded from active personalization.

## Plan lifecycle

| From | Allowed next state |
|---|---|
| `draft` | `user_reviewed`, `archived` |
| `user_reviewed` | `saved`, `draft`, `archived` |
| `saved` | `active`, `replaced`, `archived` |
| `active` | `stale`, `replaced`, `archived` |
| `stale` | `replaced`, `archived` |
| `replaced` | `archived` |
| `archived` | none |

A persisted plan contains owner/workspace, journey week and state version, creation/review timestamps, preferences, confirmed constraints, component outputs, source evidence, user edits, status, stale reason, items, and normalized dependencies. At save/activate time, current authenticated state is reloaded. A view, rerun, retry, or generated draft is never treated as review or confirmation. Stale plans remain visible but cannot be active or silently resaved.

## Dependency-driven staleness and graph continuity

Dependencies are stored for the exact journey state, allergies, restrictions, conditions, symptom state, medication/supplement records, clinician instructions, and evidence used by the plan. Relevant committed changes stale dependent plans in the same authorized transaction. Unrelated changes leave them unchanged. Missing dependency information fails visibly. No trigger regenerates, replaces, saves, or activates a plan automatically.

The connected fictional document story preserves this path:

`document → proposed/confirmed restriction → affected plan item → stale plan → professional question`

## Deletion, reset, and retention

`docs/STAGE-10-DELETION-RETENTION-INVENTORY.json` is generated from the canonical inventory and covers 13 Stage 10 state objects. The hardening migration installs a workspace-delete preparation trigger that safely removes private audit/idempotency/dependency rows and public product rows in foreign-key order while retaining unrelated workspaces. The API matrix verifies 10 public workspace-scoped tables reach zero rows, private replay becomes impossible, and the second principal is unchanged.

This is a product workspace-reset contract for controlled engineering. It is not a legal retention policy or proof of compliance; privacy/legal owners still need to set production retention periods and backup-erasure procedures.

## Follow-up, reminders, and simulated review

Follow-up tasks are in-app records with owner/workspace, provenance, status, and due information when known. A reminder requires opt-in plus date/time, timezone, and channel. External delivery remains explicitly unavailable and no notification is scheduled or sent.

Simulated review packets contain only the relevant question, journey state, minimum confirmed/user-reported context, exact evidence spans, trace, conflict, requested action, and consent record. Valid states are `not_required`, `offered`, `consented`, `queued`, `reviewed/responded`, `resumed`, `declined`, `unavailable`, and `timed_out`. Every surface says simulated. Urgent fixed guidance completes first and is independent of consent, queue state, or reviewer availability.

## Stage 9 UI integration

The Stage 9 UI routes fact decisions, plan review/save, follow-up, and simulated-review actions through the State Committer adapter. Pending, committed, rejected, stale conflict, retry-safe, offline, and unavailable states are explicit. Stable idempotency keys protect Streamlit reruns and repeated clicks. Refresh/relogin loads durable state through the storage interface; session state holds only temporary interaction state. Demo reset clears both Stage 9 and Stage 10 keys so fictional state does not leak into Personal Mode.

## Generated development evidence

- Stage 10 typed cases: **33/33**, including **13/13 critical**.
- Connected Stage 10 stories: **9/9** (three stories × three deterministic resets).
- Stage 10 focused pgTAP: **71/71** (`38 + 33`).
- Stage 10 authenticated state API: **14/14**.
- Concurrency/deletion API: **26/26**.
- Full Python suite: **480/480**.
- Clean database history: **325/325 pgTAP** and **110/110 authenticated API checks**.
- Exact Stage 9 → Stage 10 upgrade: **325/325 pgTAP** and **110/110 authenticated API checks**.
- Database lint: **0 findings** for `public` and `private`.
- Urgent ordinary-generation calls: **0**.
- External transmissions: **0**.

Machine-readable evidence:

- `data/schemas/state_lifecycle.schema.json`;
- `docs/STAGE-10-COVERAGE-MANIFEST.json`;
- `docs/STAGE-10-EVAL-RESULTS.json`;
- `docs/STAGE-10-CAPSTONE-STORY-RESULTS.json`;
- `docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json`;
- `docs/STAGE-10-DELETION-RETENTION-INVENTORY.json`;
- `docs/STAGE-10-SELF-REVIEW-FINDINGS.json`;
- `docs/STAGE-10-CHECK-RESULTS.json`.

## Exact verification commands

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -q
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
git diff --check
```

## One self-review and consolidated rectification

The generated self-review contains **14/14 PASS** findings. The consolidated correction:

1. preserved the single authenticated State Committer instead of restoring direct client CRUD;
2. aligned the legacy Stage 2 final-schema tests with that stricter contract while preserving all 122 assertions;
3. added strict JSON shape/size checks and fixed search paths;
4. made the private implementation non-callable by ordinary clients;
5. replaced retrying `40001` application conflicts with immediate typed `PT409` responses;
6. added real simultaneous authenticated race checks and response-loss replay;
7. completed workspace deletion across public and private Stage 10 state;
8. prevented idempotency replay after reset/recreation;
9. fixed plan provenance in API fixtures and upgrade fixtures;
10. corrected upgrade fixture fingerprint collision without changing product behavior;
11. made Demo reset remove both Stage 9 and Stage 10 temporary state;
12. kept legacy Stage 3/4 smoke assertions and navigated them through the new shell;
13. restored the expected Personal Mode product title and privacy boundary;
14. added canonical retention and self-review generators and CI coverage.

## Issue register

| ID | Severity | Observed evidence | Disposition | Controlled capstone blocker | Public/release blocker |
|---|---|---|---|---|---|
| S10-LEGACY-CRUD | High | Old Stage 2 assertions expected direct writes after Stage 10 | Corrected tests to assert owner read plus direct-write denial; 122/122 pass | No | No |
| S10-RPC-RETRY | High | stale `40001` caused PostgREST retry/timeout | changed application conflict to `PT409`; concurrent matrix passes | No | No |
| S10-RPC-SHAPE | High | wrapper accepted broader JSON than the typed contract | exact-key, nested-key and size validation added | No | No |
| S10-DELETE | High | private ledgers/self-references could outlive workspace deletion | ordered cleanup trigger plus 26-check API matrix | No | Requires production retention review |
| S10-DEMO-RESET | Medium | Stage 10 session keys were not cleared by Stage 9 reset | reset namespace corrected and tested | No | No |
| S10-UPGRADE-FIXTURE | Low | fixture fingerprint collided with an older deterministic row | unique fictional fingerprint used; both histories pass | No | No |
| S10-LIVE-PROVIDER | Medium | no authorized paid/live provider benchmark | deterministic providers remain clearly labelled | No | Yes for provider claims |
| S10-CONTENT-REVIEW | High | zero public weekly releases; safety/content/licence reviews remain open | production/public paths remain fail-closed | No | Yes |
| S10-REAL-OPERATIONS | High | no clinician service, external reminder, deployment, legal/privacy approval | surfaces state unavailable/simulated | No | Yes |
| S10-HOLDOUT-USABILITY | Medium | sealed holdout and independent external-user study were not run | preserved for authorized final evaluation | No | Yes for final quality claims |

No required local engineering check was silently skipped. GitHub `validate` and `supabase-integration` passed on implementation/evidence SHA `70f3f0e9f7f88196012bf7af8188966e3079161c` in [workflow run 34697772681](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34697772681).

## Migration and configuration impact

- Forward-only local migrations:
  - `supabase/migrations/20260912000100_stage10_state_review_lifecycle.sql`;
  - `supabase/migrations/20260912000200_stage10_rpc_hardening_and_reset.sql`.
- No remote migration was applied.
- No new secret, provider, paid credential, external service, or environment key is required.
- `.env.example` contains placeholders only.
- Docker and local Supabase are required for database integration verification.

## Stage 10 changed-file inventory

- `.github/workflows/data-contracts.yml`
- `app/pages_and_components/onboarding.py`
- `app/pages_and_components/stage9.py`
- `app/schemas/state_lifecycle.py`
- `app/services/capstone_flows.py`
- `app/services/product_experience.py`
- `app/services/state_committer.py`
- `data/schemas/state_lifecycle.schema.json`
- `docs/STAGE-10-CAPSTONE-STORY-RESULTS.json`
- `docs/STAGE-10-CHECK-RESULTS.json`
- `docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json`
- `docs/STAGE-10-COVERAGE-MANIFEST.json`
- `docs/STAGE-10-DELETION-RETENTION-INVENTORY.json`
- `docs/STAGE-10-EVAL-RESULTS.json`
- `docs/STAGE-10-IMPLEMENTATION-SELF-VERIFICATION-AND-CAPSTONE-READINESS.md`
- `docs/STAGE-10-SELF-REVIEW-FINDINGS.json`
- `evals/stage10_state_lifecycle.jsonl`
- `scripts/build_stage10_evals.py`
- `scripts/check_stage10.py`
- `scripts/check_stage10_concurrency_and_deletion_api.py`
- `scripts/check_stage10_state_api.py`
- `scripts/check_stage10_ui.py`
- `scripts/export_stage10_retention_inventory.py`
- `scripts/export_stage10_self_review.py`
- `scripts/export_state_lifecycle_schema.py`
- `scripts/run_stage10_evals.py`
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

## Privacy, scope, and external-action confirmation

- All committed fixtures use fictional UUIDs, fictional names, and `example.invalid` identities.
- No raw personal text is stored in Stage 10 audit traces.
- No model or agent receives direct database write authority or service-role credentials.
- Safety and public content remain draft/unreleased and live routing stays fail-closed.
- No external review packet, reminder, notification, or message was transmitted.
- No remote migration, deployment, PR, merge, main-branch change, or paid-provider request occurred.
- The sealed final holdout was not opened.

## Remaining gates and owners

- **Kajal/product:** independent review of this integration branch and authorization to push/review.
- **Clinical and India-localisation reviewers:** qualify safety wording, routine symptom policy, and health content.
- **Licence reviewer:** approve public reuse and embedding rights.
- **Privacy/legal:** approve retention, deletion, consent, and real operational data handling.
- **Engineering/release:** GitHub checks passed on the implementation/evidence SHA; independently review the branch, then separately authorize any PR, merge, deployment, or remote migration.
