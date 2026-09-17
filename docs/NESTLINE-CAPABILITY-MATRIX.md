# Maya AI capability matrix

This matrix uses one primary status per capability. Fixture or local verification is software evidence, not clinical or release approval.

| Capability | Status | Evidence | Boundary |
|---|---|---|---|
| Content publication | **requires human approval** | `docs/STAGE-0-PUBLICATION-READINESS-SUMMARY.md` | 0/63 profiles published; clinical, localisation and licence gates remain. |
| Governed ingestion | **verified with fixtures** | `docs/STAGE-1-IMPLEMENTATION.md` | Promotion remains unavailable until a genuinely approved slice exists. |
| Retrieval and causal graph | **verified locally with Supabase** | `docs/STAGE-5-SELF-VERIFICATION-AND-STAGE-6-READINESS.md` | Production embedding/reranking is unselected. |
| Deterministic Safety Gate | **requires human approval** | `docs/STAGE-6-SAFETY-EVAL-RESULTS.json` | Engineering routes pass; draft rule spec and reduced-movement gap block live use. |
| Record Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | No direct durable writes. |
| Medication Record Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | Record-only; no prescribing. |
| Symptom Navigation Agent | **requires human approval** | `docs/STAGE-7-EVAL-RESULTS.json` | Urgent/clarification fail closed; routine symptom policy remains unavailable. |
| Nutrition Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | Public clinical content remains unapproved. |
| Movement Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | No inferred clearance. |
| Well-being Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | Crisis wording still depends on draft safety policy. |
| Follow-up Agent | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | In-app proposals only. |
| Plan Composer / Schedule Builder | **verified with fixtures** | `docs/STAGE-7-EVAL-RESULTS.json` | Drafts only until explicit Stage 10 commit. |
| Stage 8 validation/composition | **verified with fixtures** | `docs/STAGE-8-EVAL-RESULTS.json` | No live semantic quality claim. |
| Configured-provider transport | **implemented** | `app/services/live_model_provider.py` | Provider-neutral, bounded and fail-closed. |
| Live provider selection | **requires human approval** | `docs/STAGE-7-LIVE-PROVIDER-BENCHMARK-AND-SELECTION-GATE.md` | xAI incomplete and tone review pending; OpenAI requests blocked by billing response. |
| Fictional document extraction | **verified with fixtures** | `docs/STAGE-4-IMPLEMENTATION.md` | Exact-hash demo fixtures only. |
| Production document extraction/uploads | **not implemented** | `docs/STAGE-4-DOCUMENT-PROVIDER-BENCHMARK-PLAN.md` | Scanner, privacy, retention, deletion and provider gates remain. |
| Authenticated Personal Mode state | **verified locally with Supabase** | `docs/STAGE-10-IMPLEMENTATION-SELF-VERIFICATION-AND-CAPSTONE-READINESS.md` | Local two-principal verification only; no deployment claim. |
| State Committer | **verified locally with Supabase** | `docs/STAGE-10-CHECK-RESULTS.json` | Only authorized write boundary. |
| Redacted tracing | **implemented** | `app/services/redaction.py` | Opt-in and configuration-controlled; live export not required. |
| Deployment | **deployment pending** | `docs/STAGE-2-DEPLOYMENT-MIGRATION-RUNBOOK.md` | No remote migration, hosting, or release in this pass. |
