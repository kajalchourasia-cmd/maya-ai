# Stages 0–8 and 10 Consolidated Improvement Final Report

## Decision and scope

This report records one consolidated improvement pass against `NESTLINE-CONSOLIDATED-IMPROVEMENT-PLAN-EXCLUDING-STAGE-9-AND-DEPLOYMENT.md`.

- Repository: `kajalchourasia-cmd/nestline`
- Base branch: `upstream/main`
- Exact base commit: `796c05cd29a055188e86685990078709fca0bfbc`
- Local improvement branch: `fix/consolidated-stages-0-8-and-10-improvements`
- Authorized remote target branch: `integration/capstone-demo-final`
- Verified implementation commit: `607a67a09aba7bf82d090c50dbe6ae779d650456`
- Final report commit: the commit containing this report; its SHA is intentionally recorded in the task response because a commit cannot contain its own SHA.
- Stage 9 UI, styling, screenshots and visual assets changed: **no**
- Deployment or remote migration performed: **no**
- Feature-branch push performed: **yes**, without force, to `integration/capstone-demo-final`
- Merge or PR performed: **no**
- Published profiles: **0/63**
- Test data: fictional, synthetic or redacted only

The engineering pass is suitable for the deterministic fictional demo and for a later Stage 9 integration decision. It is not a public, clinical, authenticated live-assistant or deployment release.

## What changed

The pass added one confirmed-context boundary, mode-safe state access, local corpus lifecycle controls, ingestion recovery, typed configuration validation, redacted trace envelopes, provider-neutral OpenAI/xAI transports, frozen provider and document benchmark harnesses, evaluation/capability/migration/publication manifests, expanded Stage 6 language coverage, cross-stage service journeys, CI integrity gates, reviewer packets and current-status documentation.

All public content and safety release boundaries remain fail-closed. Personal Mode cannot select fixture state or fixture generation. Agents remain unable to write durable state directly. Stage 10 remains the write boundary.

## Action ledger

| ID | Status | Evidence and disposition | Incomplete reason and owner |
|---|---|---|---|
| S0-01 | completed | Machine-readable 63-profile publication ledger and matching summary; 31 sources, 55 spans and 56 fragments reconcile. | — |
| S0-02 | partially completed | PC00, P10 and PP01 review packet prepared; no draft was promoted and published count remains 0. | Clinical, India-localisation, licence and product decisions require qualified reviewers coordinated by Kajal. |
| S0-03 | partially completed | All 42 comparisons remain hidden; the packet preserves rounded-object preference and requires measurement/object/product evidence. | Measurement provenance and human product/clinical decisions remain with qualified reviewers. |
| S1-01 | partially completed | Repeat build, atomic activation, withdrawal and rollback are tested with isolated synthetic release records. | The real promotion path cannot run until S0 supplies a genuinely approved published slice; owners: Stage 0 reviewers/Kajal. |
| S1-02 | blocked | Zero published fragments depend on uncertain rights, so the release invariant is safe. | Currency, reuse, licence and attribution decisions require the source/licence reviewer. |
| S1-03 | completed | Failed fetch, hash change and parse failure preserve last-known-good state; quarantine/recovery runbook added. | — |
| S2-01 | completed | Ordered 17-migration manifest with checksums and purposes; checker passes 17/17. | — |
| S2-02 | completed | Two authenticated principals exercised storage, onboarding, documents, retrieval and State Committer boundaries; cross-workspace, forged scope and ordinary service-role behaviour remain denied. | — |
| S2-03 | completed | Local-only deployment migration runbook covers backup, dry run, ordering, verification and rollback; it explicitly requires later authorization. | — |
| S3-01 | completed | `ConfirmedContextService` is consumed by retrieval, orchestration and the mode-safe commit facade; unconfirmed/conflicting/cross-owner/stale inputs stop. | — |
| S3-02 | completed | Transition, conflict, concurrent edit, active-episode and relogin reproducibility checks pass. | — |
| S4-01 | completed | Personal configuration fails closed without scanner/privacy readiness; Demo fixtures remain isolated. | Real uploads still require scanner, privacy, retention and deletion approval. |
| S4-02 | partially completed | Frozen 8-document fictional benchmark and run plan exist; no extraction winner is claimed. | No authorized live extraction candidate benchmark was available; owners: product/security/platform. |
| S4-03 | completed | Proposal/rejection/confirmation/correction/deletion/provenance/invalidation coverage passes in unit, pgTAP and authenticated API suites. | — |
| S5-01 | blocked | Retrieval still rejects pending/unapproved content and reports no approved public content. | A genuinely published Stage 0/1 slice does not exist; owners: content/review team. |
| S5-02 | partially completed | Decision record keeps exact SQL/full-text and deterministic fixture embeddings as controlled routes and fail-closed lexical fallback; no production provider is selected. | Production embedding/reranking candidates, credentials and measured published-corpus evidence are unavailable; owner: platform/product. |
| S5-03 | completed | Versioned manifest, snapshot linkage, repeatable rebuild, atomic switch, rollback, withdrawal and isolation tests pass. | — |
| S6-01 | partially completed | Qualified-review packet records both reduced-movement phrases and preserves clarification/zero-generation behaviour. | The public rule and wording need qualified clinical and India-localisation decisions; no approval was invented. |
| S6-02 | completed | Frozen adversarial additions cover Hinglish, indirect/multiple symptoms, mixed product intent, stored-report text and override attempts. | — |
| S6-03 | completed | Equivalent safety behaviour is checked across chat, onboarding, document facts, check-ins and plan input. | — |
| S7-01 | partially completed | Explicit OpenAI/xAI transports enforce endpoint/model lock, strict structured output, timeout, token/cost ceilings, redaction, no tools/writes and fail-closed errors; Personal Mode cannot use fixtures. | An automatic transport retry was not added because the canonical specialist budget permits one model call. Changing that budget requires Kajal/architecture approval. |
| S7-02 | partially completed | Same frozen 8-case set attempted with xAI `grok-4.6` and OpenAI `gpt-5.4-mini`; neither was selected. | xAI was 6/8 complete; OpenAI inference failed 6/6 attempted provider cases with HTTP 429; 8/8 tone reviews remain pending. |
| S7-03 | completed | Deterministic plan cases preserve journey, allergies/restrictions, medication record-only language, conflicts, draft/save and staleness boundaries. | — |
| S7-04 | completed | Health contributions require accepted spans or abstain; product-only help is separated; Stage 7 and Stage 8 gates pass. | — |
| S8-01 | completed | Canonical manifest maps 12 datasets and 446 case records/identifiers to stages, evaluators, thresholds, artifacts and limitations. | — |
| S8-02 | partially completed | Live-provider development report preserves every failure and exact provider/model/cost result. Sealed final holdout answers were not opened. | OpenAI inference was unavailable, xAI had 2 failures, and all human tone review is pending; owners: provider/platform and human reviewers. |
| S8-03 | blocked | Separate human-review packets exist for clinical safety, nutrition/movement, India localisation, citation fidelity, tone/usability and privacy. | Named qualified reviewers, decisions and dates are external human work. |
| S8-04 | partially completed | 17/17 synthetic service journeys cover confirmed context, safety, agents, validation, commits, staleness, concurrency, outage and cross-user denial. | The approved-public-evidence hop is blocked by zero published profiles. |
| S10-01 | completed | One mode-safe facade allows allowlisted in-memory Demo commits and authenticated, database-derived Personal commits only. | — |
| S10-02 | completed | Clean and supported upgrades run the same pgTAP, two-user API, idempotency, concurrency, deletion, relogin and audit coverage. | — |
| S10-03 | completed | Draft, change intent, review, explicit save, persisted/stale plan and simulated/external review states are documented consistently. | — |
| X-01 | completed | README, progress, current status and historical-report index identify merged PR #4, the deterministic path, zero publication and pending deployment. | — |
| X-02 | completed | Typed mode/component configuration reports omit values; Demo needs no paid credentials and incomplete Personal Mode fails closed. | — |
| X-03 | completed | Machine and human capability matrices classify 21/21 capabilities with evidence and blockers. | — |
| X-04 | completed | Redaction handles credentials, identifiers and medical fields; trace export is opt-in; secret scan reports zero findings. | — |

## Verification results

The canonical machine-readable record is `docs/STAGES-0-TO-8-AND-10-CONSOLIDATED-VERIFICATION-RESULTS.json`.

| Verification | Actual result |
|---|---|
| Complete Python unit discovery | 514/514 passed; 0 failed; 0 skipped |
| Content authoring validation | valid; 63 profiles, 31 sources, 55 spans, 56 fragments |
| Review-ready content validation | valid; 0 profiles published |
| Phase contract evaluations | 64/64 passed |
| Stage 1 governed ingestion | 14 source runs, 55 candidates/anchors, 72 governed blocks, 54 decisions, 0 errors |
| Journey evaluations | 26/26 passed |
| Stage 4 controlled documents | 8 documents; 33 candidates; 6 explicit abstentions; all checks passed |
| Stage 5 development retrieval | 28/28 passed; Recall@5 18/18; citation precision 18/18; 0 forbidden decoys |
| Stage 5 paraphrases and rectification | 12/12 plus 212/212 passed |
| Stage 6 safety | 65/65; critical 61/61; urgent zero-generation 35/35; ambiguous stopped 21/21; unsafe reassurance 0/65 |
| Stage 7 orchestration | 76/76; critical 64/64; 8 specialists; urgent zero-agent-generation 5/5 |
| Stage 8 validation | 69/69; critical 57/57; urgent composition calls 0; maximum retry 1; maximum repair 1 |
| Stage 10 lifecycle | 33/33; critical 13/13; capstone stories 9/9; direct table writes 0; external actions 0 |
| Consolidated service journeys | 17/17 passed |
| Generated manifests | 17/17 migrations; 12 datasets; 21 capabilities; 20 required artifacts |
| Stage 9 exclusion proof | 30/30 excluded file hashes verified; base-to-implementation diff is empty for all excluded paths |
| Secret hygiene | 450 repository files scanned; 0 credential findings; `.env` ignored |
| Syntax and whitespace | `compileall` passed; `git diff --check` passed |

### Local database matrix

| Schema history | Upgrade/replay | pgTAP | Authenticated API | Lint |
|---|---:|---:|---:|---:|
| Accepted Stage 9 → current | pass | 8/8 files, 325/325 assertions | 6/6 checkers, 110/110 checks | 0 errors |
| Accepted Stage 4 → current | pass | covered by the supported current matrices | covered by the supported current matrices | covered |
| Accepted Stage 3 → current | pass | 8/8 files, 325/325 assertions | 6/6 checkers, 110/110 checks | 0 errors |
| Clean migration replay | pass | 8/8 files, 325/325 assertions | 6/6 checkers, 110/110 checks | 0 errors |

The API matrices used two authenticated principals. Product calls used authenticated JWTs. Ordinary service-role commits were rejected. The three simultaneous-write scenarios each committed exactly one request and rejected exactly one stale competitor. Workspace reset checked 10 public tables and cleanup completed.

### GitHub branch/check evidence

The authorized initial push advanced `integration/capstone-demo-final` from `dd65daf1dccd079b9e43e8e72c0c1ad50479027c` to `13ab7a41008c198fa9677586c0a73e31f17a396a` without force. GitHub workflow run [34711771806](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34711771806) reported:

- `supabase-integration`: **passed** on the exact initial pushed commit ([job 103601702437](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34711771806/job/103601702437));
- `validate`: all preceding validation steps passed, then the consolidated checker failed because its raw-byte Stage 9 preservation hashes were line-ending-dependent ([job 103601702362](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34711771806/job/103601702362));
- the correction uses the versioned cross-platform hashing contract described in the Stage 9 preservation section and adds a dedicated regression test;
- the exact corrected remote head and its final GitHub check links are intentionally recorded in the task response after the normal follow-up push, because the report commit cannot contain its own SHA.

### Exact command families

```powershell
..\github-nestline\.venv\Scripts\python.exe -m unittest discover -s tests -v
..\github-nestline\.venv\Scripts\python.exe -m scripts.validate_content
..\github-nestline\.venv\Scripts\python.exe -m scripts.validate_content --require-review-ready
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_contract_evals
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_journey_evals
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage1 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage2 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage3 --skip-remote --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage3_ui
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage4_readiness --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage4 --skip-remote --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage4_ui
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage5_retrieval_evals
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage5_rectification_matrix
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage5_paraphrase_evals
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage5 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage6_safety_evals --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage6 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage7_evals --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage7 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage8_evals --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage8 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stages5_8_rectification --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.run_stage10_evals
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage10_ui
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_stage10 --write-report
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_configuration --mode demo
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_migration_manifest
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_consolidated_improvements
..\github-nestline\.venv\Scripts\python.exe -m scripts.check_secret_hygiene
..\github-nestline\.venv\Scripts\python.exe -m compileall -q app scripts tests
git diff --check
```

The database runs used the repository Supabase CLI with `supabase start`, versioned `db reset --local --version ...`, local fixture SQL through the Docker Postgres container, `migration up --local`, each `supabase/tests/*.test.sql`, the six authenticated API checkers, `db lint --local`, and `stop --no-backup`. No command targeted the remote project.

## Provider evidence

| Provider/model | Frozen cases | Validated display | Citation/support | Tokens | Cost | Outcome |
|---|---:|---:|---:|---:|---:|---|
| xAI `grok-4.6` | 6/8 completed | 4/8 | 6/8 | 6,405 input; 2,366 output | $0.020862 | Two failures; 0 displayed constraint escapes; 8/8 human tone reviews pending |
| OpenAI `gpt-5.4-mini` | 2/8 route cases completed | 0/8 | 2/8 safety-route support | 0 | $0 | Both completed cases were zero-call safety routes; all 6 intended provider calls failed closed with HTTP 429 at benchmark time |

The xAI and OpenAI model-list endpoints were reachable with local ignored credentials, but that is access evidence only. OpenAI inference was not usable in the benchmark. Neither provider was selected. Fireworks was not tested because no Fireworks access was available. These visible fictional development cases are not a sealed-holdout, clinical, tone or production-quality benchmark.

## Self-review and focused correction

The implementation and post-push verification process found six genuine issues:

1. The system Python had an older Pydantic build and lacked PyMuPDF, producing environment failures unrelated to repository behaviour. All authoritative checks were rerun with the existing project virtual environment.
2. A provider import was malformed during the first edit. It was corrected before the final 514/514 run.
3. The initial report rebuild counted provider/structured-output failures with no displayed draft as constraint escapes. The generator was corrected; failed cases remain failed, while displayed constraint-boundary violations are now accurately 0.
4. One service-journey expectation treated a diagnosis request as ordinary unsupported product intent, while the accepted safety contract conservatively clarified it. The diagnosis case was preserved as a safety regression and a separate canonical unsupported product request was added. The final service matrix is 17/17.
5. The final staged diff check found trailing whitespace and extra end-of-file blank lines. Those were normalized and the staged check passed.
6. The first GitHub `validate` run exposed a cross-platform preservation-check defect: the Stage 9 immutability manifest hashed raw text bytes, while Git converted CRLF to LF for `.streamlit/config.toml` and `assets/stage9/week-24-journey.svg` on Linux. The checker now uses a versioned cross-platform scheme: tracked text files are normalized to LF solely for hashing, binary files remain byte-exact, ignored cache files are excluded, and a CRLF/LF regression test proves equivalence. No Stage 9 UI file was changed.

No expected safety route, security threshold or test assertion was weakened to obtain a passing result.

## Stage 9 preservation

No change exists under:

- `streamlit_app.py`
- `.streamlit/`
- `app/pages_and_components/`
- `assets/`
- `docs/stage9-ui-evidence/`

`data/stage9_ui_immutability_manifest.json` records 30 cross-platform hashes, and the consolidated checker verifies all 30. Tracked text files are normalized to LF solely for hashing; binary files remain byte-exact. The only product-experience change is service-layer provider injection in `app/services/product_experience.py`; it does not modify Stage 9 UI, style, screenshots or visual assets.

## Complete changed-file inventory

### Cross-stage, configuration and current truth

```text
.env.example
.github/workflows/data-contracts.yml
README.md
docs/HISTORICAL-REPORT-INDEX.md
docs/NESTLINE-CAPABILITY-MATRIX.json
docs/NESTLINE-CAPABILITY-MATRIX.md
docs/NESTLINE-CURRENT-STATUS.md
docs/NESTLINE-EVALUATION-MANIFEST.json
docs/NESTLINE-EVALUATION-MANIFEST.md
docs/PROJECT-PROGRESS.md
docs/STAGES-0-TO-8-AND-10-CONSOLIDATED-IMPROVEMENT-FINAL-REPORT.md
data/stage9_ui_immutability_manifest.json
app/services/configuration.py
app/services/redaction.py
scripts/build_capability_matrix.py
scripts/build_evaluation_manifest.py
scripts/build_stage9_immutability_manifest.py
scripts/check_configuration.py
scripts/check_consolidated_improvements.py
scripts/check_secret_hygiene.py
tests/test_consolidated_controls.py
```

### Stages 0–2

```text
data/schemas/storage.schema.json
data/supabase/migration_manifest.json
docs/STAGE-0-CHECK-RESULTS.json
docs/STAGE-0-COMPARISON-REVIEW-PACKET.md
docs/STAGE-0-DEMONSTRATION-SLICE-REVIEW-PACKET.md
docs/STAGE-0-PUBLICATION-READINESS-LEDGER.json
docs/STAGE-0-PUBLICATION-READINESS-SUMMARY.md
docs/STAGE-1-CHECK-RESULTS.json
docs/STAGE-1-INGESTION-FAILURE-RECOVERY-RUNBOOK.md
docs/STAGE-2-DEPLOYMENT-MIGRATION-RUNBOOK.md
app/services/ingestion_recovery.py
scripts/build_migration_manifest.py
scripts/build_publication_readiness.py
scripts/check_migration_manifest.py
```

### Stages 3–5

```text
app/services/confirmed_context.py
app/services/corpus_lifecycle.py
app/services/retrieval_policy.py
docs/STAGE-4-DOCUMENT-PROVIDER-BENCHMARK-PLAN.md
docs/STAGE-5-CHECK-RESULTS.json
docs/STAGE-5-EMBEDDING-RERANKING-DECISION.md
docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json
docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json
docs/STAGE-5-RETRIEVAL-METRICS.json
evals/stage4_document_provider_benchmark.jsonl
scripts/build_stage4_provider_benchmark.py
```

### Stages 6–8 and provider transport

```text
app/services/agents.py
app/services/live_model_provider.py
app/services/model_provider.py
app/services/openai_model_provider.py
app/services/orchestration.py
app/services/product_experience.py
app/services/provider_benchmark.py
app/services/xai_model_provider.py
docs/STAGE-6-CHECK-RESULTS.json
docs/STAGE-6-REDUCED-MOVEMENT-QUALIFIED-REVIEW-PACKET.md
docs/STAGE-6-SAFETY-EVAL-RESULTS.json
docs/STAGE-7-EVAL-RESULTS.json
docs/STAGE-7-LIVE-PROVIDER-BENCHMARK-AND-SELECTION-GATE.md
docs/STAGE-7-OPENAI-LIVE-PROVIDER-BENCHMARK.json
docs/STAGE-7-OPENAI-LIVE-PROVIDER-CASE-RESULTS.json
docs/STAGE-7-XAI-LIVE-PROVIDER-BENCHMARK.json
docs/STAGE-7-XAI-LIVE-PROVIDER-CASE-RESULTS.json
docs/STAGE-8-EVAL-RESULTS.json
docs/STAGE-8-HUMAN-REVIEW-PACKETS.md
docs/STAGES-5-TO-8-RECTIFICATION-CHECK-RESULTS.json
evals/stage6_safety_development.jsonl
evals/stage7_live_provider_development.jsonl
scripts/build_stage6_safety_evals.py
scripts/check_openai_provider_access.py
scripts/check_xai_provider_access.py
scripts/rebuild_live_provider_reports.py
scripts/run_live_provider_benchmark.py
scripts/run_openai_provider_benchmark.py
tests/test_live_model_provider.py
tests/test_openai_model_provider.py
tests/test_xai_model_provider.py
```

### Stage 10 and connected services

```text
app/services/state_service.py
docs/STAGE-10-CAPSTONE-STORY-RESULTS.json
docs/STAGE-10-CONCURRENCY-AND-DELETION-RESULTS.json
docs/STAGE-10-DRAFT-REVIEW-COMMIT-BOUNDARY.md
docs/STAGE-10-EVAL-RESULTS.json
docs/STAGES-0-8-10-SERVICE-JOURNEY-RESULTS.json
docs/STAGES-0-TO-8-AND-10-CONSOLIDATED-VERIFICATION-RESULTS.json
evals/stage10_state_lifecycle.jsonl
scripts/run_consolidated_service_journeys.py
```

## Honest blockers and required owners

| Blocker | Owner | Safe current behaviour |
|---|---|---|
| No content profile has complete clinical, localisation, licence and product approval | Qualified reviewers/Kajal | 0/63 published; public health retrieval abstains |
| Baby-size measurements/object dimensions remain unverified | Clinical/product reviewers | 42/42 comparisons hidden |
| Reduced-movement policy wording remains draft | Qualified clinical and India-localisation reviewers | Generic clarification or draft urgent route; zero ordinary generation |
| Real upload scanner/privacy/retention/deletion approval absent | Security/privacy/product | Personal real upload disabled |
| Production embedding/extraction providers not selected | Platform/product | Exact/full-text and controlled fixtures only |
| OpenAI inference unavailable and xAI incomplete | Platform/provider owner | Provider failure abstains; no fixture fallback in Personal Mode |
| Human clinical/tone/citation/privacy samples not reviewed | Named qualified reviewers | Automated results are not called human approval |
| One-call specialist budget conflicts with an automatic transport retry | Kajal/architecture owner | No hidden retry; failure stops after the permitted call |
| Deployment/remote migration not authorized | Kajal/operator | No deployment or remote migration occurred |

## Verdicts

| Scope | Verdict | Reason |
|---|---|---|
| Deterministic fictional demo | **GO** | All deterministic, service, database and security checks passed using fictional/synthetic data. |
| Readiness for later Stage 9 UI integration | **GO** | Independent P1 engineering is complete or safely blocked on named external authority; Stage 9 excluded paths are unchanged. |
| Authenticated Personal Mode | **NO-GO as a complete live assistant** | State/RLS paths are locally verified, but live provider selection, approved public evidence, real-upload security and external review remain incomplete. |
| Live-provider pilot | **NO-GO** | xAI completed 6/8, OpenAI completed no intended generation calls, tone review is pending and no provider is selected. |
| Public/clinical release | **NO-GO** | Zero profiles are published; safety, clinical, licence, localisation, privacy/security and deployment gates remain open. |

## External-action boundary

The user authorized a normal, non-force push to `integration/capstone-demo-final`, including the in-scope follow-up correction required by its GitHub checks. No PR, merge, deployment or remote migration was performed.

Separate explicit decisions remain required for merge, provider selection, content or safety-specification publication, enabling real uploads, applying remote migrations and deployment. This report does not imply approval for any of them.
