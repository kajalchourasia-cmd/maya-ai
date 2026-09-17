# Final Capstone + Maya UI Integration Verification

> **Historical integration baseline.** This report records the earlier conservative correction at its reviewed commit. Current React product-surface status and superseding restoration evidence are in [MAYA-AI-PRODUCT-UI-RESTORATION-AND-PRE-MERGE-VERIFICATION.md](MAYA-AI-PRODUCT-UI-RESTORATION-AND-PRE-MERGE-VERIFICATION.md). The original findings and results below are preserved as historical evidence.

**Date:** 13 September 2026 (IST)
**Repository:** `kajalchourasia-cmd/nestline`
**Local branch:** `integration/final-capstone-maya-ui`
**Remote used:** `upstream` → `https://github.com/kajalchourasia-cmd/nestline.git`
**Final correction commit:** pending by design; the commit containing this report cannot truthfully contain its own SHA. The final task response records the exact local SHA.
**External actions:** no push, pull request, merge to `main`, deployment, remote migration, external contact, or paid-provider call occurred.

## Verdict

**LOCAL NO-GO FOR FINAL CAPSTONE ACCEPTANCE — INTERACTIVE UI VERIFICATION REMAINS REQUIRED.**

The Git integration, backend controls, database histories, automated UI checks, React build, Streamlit startup, controlled API behavior, and deterministic stories pass. The branch is **safe to push for Kajal's review** after user approval because no unresolved safety, permission, privacy, evidence, or State Committer regression was found. It is not yet eligible for an unqualified final GO because this run could not complete the required interactive desktop, phone, focus, keyboard, and task-completion walkthrough: the browser-control runtime exited before attaching to the local page. No screenshot or visual result is fabricated.

Public/clinical release is separately **NO-GO**: 0/63 profiles are published, the safety specification remains draft, qualified reviews and provider selection remain open, real uploads remain disabled, and no deployment/privacy/security authorization exists.

## Exact source state and ancestry

| Item | Exact evidence |
|---|---|
| Verified capstone remote head | `40ee1ae56d96697aad5f450994cc9340e95e6a10` |
| Maya UI remote head | `7a5531635242c997bacf33b2cabe2acbf67fa751` |
| Common ancestor | `40ee1ae56d96697aad5f450994cc9340e95e6a10` |
| Commits unique to capstone | 0 |
| Commits unique to Maya side | `ab29e63` (merge of capstone into `main`) and `7a55316` (React/FastAPI integration) |
| Maya contains capstone | Yes; the common ancestor is the exact capstone head. |
| Local integration merge | `01b4f889f7d7652ecc0a87b85632369381f16a71` |
| Merge method | Normal `git merge --no-ff`; no squash, rebase, cherry-pick, reset, or force update. |
| Merge conflicts | 0 |

The original `github-nestline` worktree contained unrelated uncommitted provider/UI work. It was preserved untouched. This integration was performed in the separate worktree `C:\Users\ASWATH HARISH\Downloads\nestline-main\final-capstone-maya-ui`.

## Source-branch baseline

### `integration/capstone-demo-final`

- Clean checkout at `40ee1ae...`.
- Previously generated accepted capstone evidence remained present.
- Python baseline: 514/514 passed.
- GitHub `Data contracts` run on the exact SHA: success ([run 34713116912](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34713116912)).
- No source file was changed on this branch.

### `integration/maya-ai-ui-demo`

- Clean checkout at `7a55316...` in a detached baseline worktree.
- Python compilation/imports passed.
- After temporarily supplying the missing test dependency in the local verifier environment, Python tests passed 521/521; focused API tests passed 7/7.
- React lint completed with 0 errors and 2 image warnings; production build passed.
- Streamlit startup returned HTTP 200 with a 7,459-byte bootstrap page.
- Secret hygiene: 563 files scanned, 0 credential findings, `.env` ignored.
- Remote GitHub `supabase-integration` passed, but `validate` failed on the Python unit-test step ([run 34716924350](https://github.com/kajalchourasia-cmd/nestline/actions/runs/34716924350)). The branch added FastAPI `TestClient` tests without declaring its required `httpx` dependency. A clean install reproduced `RuntimeError: starlette.testclient requires httpx`.

The baseline also contained four functional/product defects: onboarding safety results were ignored by the React navigation; unreleased weekly fetal/editorial content was displayed; the landing page did not clearly identify fictional-only use; and its `Ask Maya` entry opened chat before a trusted session existed.

## Integration corrections

| Finding | Root cause | Correction | Evidence |
|---|---|---|---|
| Maya CI validation failure | `httpx` was undeclared. | Added pinned `httpx==0.28.1`. | Focused API 11/11; full Python 525/525. |
| Frontend setup instructions referenced a missing file | `.env.example` was ignored by `frontend/.gitignore`. | Added a placeholder-only file and explicit allow rule. | Secret scan 565/565 files, 0 findings; `.env` remains ignored. |
| Frontend could regress without CI detection | Validate job did not install, lint, or build `frontend`. | Added Node 24, `npm ci`, lint, and production build to `validate`. | Local lint 0 errors; production build generated 3/3 static routes. Final remote CI awaits an authorized push. |
| Urgent/ambiguous onboarding proceeded to dashboard | API returned safety results but no blocking contract; client ignored them. | Added typed trace/generation fields, server `safety_blocked`, and client-side fixed safety/clarification stop. | New urgent and ambiguous regression tests; Stage 6 65/65; urgent 35/35 with zero generation. |
| Unapproved health/fetal claims appeared in React | Static concept content bypassed the governed release state. | Removed/hid hard-coded growth, size, weight, development, and health-guidance cards; added explicit fail-closed content status. | Governed inventory remains 0/63 published and 0/42 comparison-eligible; rendered landing assertions 5/5. |
| Landing did not clearly state Demo-only boundary | Controlled-demo label appeared only after onboarding. | Added first-screen fictional/no-real-data/product-boundary wording and corrected metadata. | Rendered HTML assertions 5/5. |
| `Ask Maya` could open before a session existed | Landing navigation set the chat view directly. | Entry now creates the deterministic fictional preview context, then opens chat. | Source audit and successful API preview/chat flow; browser click walkthrough remains pending. |
| API scope description overstated Stage 10 | React adapter does not expose durable state commits. | Documented React as Stage 3 and 6–8 only; retained Stage 10 on Streamlit/storage surface. | Stage 10 tests and Streamlit checker remain green. |
| Apparent Stage 3 migration failure during local verification | Local Supabase reset initialization continued after the command yielded, and the fixture was loaded before all target migrations settled. | No historical migration was changed. The verifier waited for the exact ledger target before loading the fixture. | Immutable migration fingerprint passes; Stage 3 upgrade, 325/325 pgTAP, and 110 authenticated checks pass. |

## Architecture and requirement mapping

- **Journey:** React onboarding calls the Stage 3 resolver and preserves exact/range semantics.
- **Safety:** Stage 6 executes before routine generation in onboarding and chat; urgent chat and onboarding remain zero-generation.
- **Orchestration/planning:** React plan/chat use the existing Stage 7 orchestrator and Plan Composer through `run_compass`; no worker gained write authority.
- **Validation/evidence:** Stage 8 display permission and controlled evidence remain in the accepted service boundary; unreleased public content is not shown as guidance.
- **Durable state:** The accepted Stage 10 State Committer, lifecycle, invalidation, idempotency, concurrency, and simulated-review flows remain exposed through Streamlit/storage. React remains proposal-only and does not claim durable saving.
- **UI architecture:** The canonical documents still identify `streamlit_app.py` as the complete capstone entry point. React is a complementary Demo-only surface. This split is documented rather than silently redefining Stage 10.
- **Data/privacy:** tests and live checks used fictional temporary records only. No provider keys or private medical data were used.

## Final verification results

### Application and unit verification

| Check | Result |
|---|---:|
| Complete Python discovery | **525/525 passed**, 0 failed, 0 skipped |
| Focused React adapter API tests | **11/11 passed** |
| Python compilation (`app`, `api`, `scripts`, `tests`) | passed |
| React ESLint | passed, 0 errors, 0 warnings |
| React production build | passed; TypeScript passed; static routes **3/3** |
| React live HTTP integration | **6/6 assertions passed**; 2 sessions isolated; urgent generation calls 0 |
| React server-rendered boundary/claim checks | **5/5 passed**, HTTP 200 |
| React root smoke | **3/3 passed**, HTTP 200 |
| Streamlit startup smoke | **3/3 passed**, HTTP 200, 7,459 bytes |
| Streamlit repository UI checkers | Stage 3, 4, 9, and 10 UI checkers passed |
| `git diff --check` | passed, exit 0 |

### Controlled stage/evaluation evidence

- Content review-ready validation: 63/63 profiles structurally valid; **0/63 published**; 31 sources; 55 exact spans; 56 fragments.
- Stage 0 publication gate: expected fail-closed result, exit 1, because no profile is approved for public release. This is a release blocker, not a software regression.
- Controlled Stage 1–10 checker/evaluation commands: **29/29 non-configuration modules passed**. Demo configuration passed separately 1/1; Personal Mode without live settings failed closed as expected.
- Demo configuration: **1/1 passed**; deterministic provider permitted only in Demo Mode.
- Personal configuration without live settings: **1/1 correctly failed closed**, with fixture provider prohibited.
- Stage 5 frozen development truth: 28/28 expected behavior; Recall@5 18/18; evidence precision 18/18; confirmed-fact precision 12/12; graph correctness 1/1; 0 wrong-week, wrong-jurisdiction, unapproved-source, cross-workspace, or proposal/conflict-personalization violations.
- Stage 5 paraphrases: 12/12 expected behavior; Recall@5 9/9; precision 9/9; 0 forbidden evidence IDs.
- Stage 6: 65/65 total; 61/61 critical; urgent zero-generation 35/35; conservative ambiguous/failure stops 21/21; zero unsafe reassurance 65/65. Specification remains draft.
- Stage 7: 64/64 critical synthetic cases.
- Stage 8: 57/57 critical synthetic cases.
- Stage 9: 42/42 cases; 29/29 critical; home agent fan-out 0; Stage 10 writes 0; provider live runs 0.
- Stage 10: 33/33 cases; 13/13 critical; unauthorized writes 0; external transmissions 0.
- Secret hygiene: 565 files scanned, 0 credential findings; `.env` ignored.

### Database, permissions, RLS, lifecycle, and migrations

| Path/check | Result |
|---|---:|
| Exact Stage 9 → Stage 10 upgrade | passed; fixture validated and removed |
| Exact Stage 4 → Stage 5–10 upgrade | passed; fixture validated and removed |
| Exact Stage 3 → Stage 4–10 upgrade | passed after waiting for local reset ledger target; fixture validated and removed |
| Clean replay | **17/17 migrations applied** |
| pgTAP on exact Stage 9 upgrade | **325/325 passed** across 8 files |
| pgTAP on exact Stage 3 upgrade | **325/325 passed** across 8 files |
| pgTAP on final clean replay | **325/325 passed** across 8 files |
| Authenticated API checkers | **6/6 scripts passed**, **110 reported checks** per full matrix, two principals where applicable |
| Stage 10 concurrency/deletion | 26 checks; one commit/one rejection in each simultaneous race; response-loss replay true; cross-workspace idempotency isolated; 10 public tables checked on reset |
| Application-schema lint | 0 findings |
| Remote migrations | 0 applied |

The 325 pgTAP assertions include RLS, two-user isolation, retrieval/vector/graph separation, lifecycle, state commit, idempotency, and RPC hardening. Product calls in authenticated scripts used user JWTs; the ordinary service-role State Committer call was rejected.

## Connected demo stories

Canonical deterministic evidence was regenerated from scripts:

| Story | Runs | Result |
|---|---:|---:|
| Journey + fictional allergy/restriction + plan edit/validation/save/version | 3 | **3/3 passed** |
| Fictional document + fact confirmation/correction + dependency + stale plan/question | 3 | **3/3 passed** |
| Urgent fixed route + zero generation + minimum simulated-review packet | 3 | **3/3 passed** |
| Stage 9 boundary walkthroughs | 9 total story runs | **9/9 passed**; durable Stage 10 actions explicitly unavailable there |
| Stage 10 connected capstone flows | 9 total story runs | **9/9 passed**; deterministic reset, 0 manual DB edits, 0 external transmissions |

These are synthetic software-contract results. They do not establish clinical safety, user research, production retrieval quality, or release approval.

## Streamlit and React UI review

Automated Streamlit state/navigation checks, startup, rerun/idempotency tests, and the unchanged Stage 9 artifact-integrity manifest passed. React lint/build/HTTP and backend-connected flows passed. The first-screen Demo-only boundary, safe content-release state, onboarding safety stop, and session isolation were corrected.

The requested interactive inspection could not be completed. Browser attachment failed with a Windows sandbox ACL error before the page could be controlled. Exact unverified interactive denominator:

- desktop and phone visual passes: **0/2 completed; 2 skipped**;
- named Streamlit surface walkthroughs: **0/13 completed in this run; 13 skipped**;
- explicit keyboard/focus walkthrough: **0/1 completed; 1 skipped**;
- new screenshots: **0 captured**.

Existing generated Stage 9 evidence and automated checks remain valid, but they are not represented as a substitute for this missing independent interaction pass. This is the reason for the local final-acceptance NO-GO.

## Provider and configuration truth

- No OpenAI, xAI, Fireworks, LangSmith, or other paid-provider request was made.
- Demo Mode requires no provider credential and passed configuration validation.
- The isolated worktree intentionally contained no copied `.env`; Personal Mode failed closed without public Supabase/live-provider configuration and prohibited fixture fallback.
- Existing provider-neutral code and historical benchmark evidence were not changed.
- `frontend/.env.example` contains only `NEXT_PUBLIC_MAYA_API_URL=http://127.0.0.1:8000` and comments.

## Self-review and consolidated correction

The first review found failures in dependency completeness, frontend CI coverage, onboarding safety presentation, governed-content display, initial privacy/comprehension wording, pre-session chat navigation, and Stage 10 scope wording. One consolidated correction pass addressed those items. The final rerun passed the affected Python/API/React/content/stage/database checks. The temporary review matrix is outside the repository at `C:\Users\ASWATH HARISH\Downloads\nestline-main\integration-verification-logs\FINAL-INTEGRATION-SELF-REVIEW.md`.

## Honest issue register

| Severity | Issue/evidence | User/safety impact | Disposition | Blocks |
|---|---|---|---|---|
| High | Onboarding urgent/ambiguous results were ignored by React. | Could continue ordinary product flow after a safety stop. | **Fixed and regression-tested.** | No |
| High | Unreleased fetal/editorial health claims were hard-coded in React. | Could present unapproved content as guidance. | **Fixed; content hidden and gate shown.** | No |
| Medium | `httpx` missing; Maya remote validate failed. | Clean CI/test install failed. | **Fixed locally; final CI awaits push.** | Final remote acceptance |
| Medium | First-screen fictional/privacy boundary was unclear. | A user could mistake the prototype for a personal health service. | **Fixed.** | No |
| Medium | Landing `Ask Maya` lacked a session. | First task failed and required developer explanation. | **Fixed in code; interactive click confirmation pending.** | Interactive acceptance |
| Medium | React does not expose Stage 10 durable state flows. | React alone is not the complete capstone surface. | Documented; Streamlit remains the accepted complete Stage 3–10 surface. | React-only capstone claim |
| Medium | Interactive desktop/phone/keyboard review unavailable. | Layout, focus, and end-user comprehension are not independently proven in this run. | Open; Kajal/reviewer must execute the documented walkthrough. | **Final capstone GO** |
| Medium | Final integration commit has no GitHub checks because push is prohibited. | Remote reproducibility is not yet confirmed. | Open until authorized push. | Final remote acceptance |
| High/public | 0/63 profiles published; safety spec draft; real uploads/providers/review/deployment gated. | Cannot support public clinical reliance. | Fail closed and documented. | **Public/clinical release** |

## Complete changed-file inventory

### Exact Maya merge (`40ee1ae...` → merge commit `01b4f88...`)

- `M	README.md`
- `A	api/README.md`
- `A	api/__init__.py`
- `A	api/main.py`
- `M	app/services/product_experience.py`
- `A	docs/MAYA-AI-UI-INTEGRATION.md`
- `M	docs/NESTLINE-CURRENT-STATUS.md`
- `M	docs/NESTLINE-EXECUTION-PLAN.md`
- `M	docs/Nestline updated architecture.md`
- `M	docs/PROJECT-PROGRESS.md`
- `A	frontend/.gitignore`
- `A	frontend/.npmrc`
- `A	frontend/AGENTS.md`
- `A	frontend/CLAUDE.md`
- `A	frontend/README.md`
- `A	frontend/app/baby-growth-library.ts`
- `A	frontend/app/chatgpt-auth.ts`
- `A	frontend/app/globals.css`
- `A	frontend/app/layout.tsx`
- `A	frontend/app/page.tsx`
- `A	frontend/build/sites-vite-plugin.LICENSE`
- `A	frontend/build/sites-vite-plugin.ts`
- `A	frontend/cloudflare-env.d.ts`
- `A	frontend/components.json`
- `A	frontend/components/ui/accordion.tsx`
- `A	frontend/components/ui/alert-dialog.tsx`
- `A	frontend/components/ui/alert.tsx`
- `A	frontend/components/ui/aspect-ratio.tsx`
- `A	frontend/components/ui/attachment.tsx`
- `A	frontend/components/ui/avatar.tsx`
- `A	frontend/components/ui/badge.tsx`
- `A	frontend/components/ui/breadcrumb.tsx`
- `A	frontend/components/ui/bubble.tsx`
- `A	frontend/components/ui/button-group.tsx`
- `A	frontend/components/ui/button.tsx`
- `A	frontend/components/ui/calendar.tsx`
- `A	frontend/components/ui/card.tsx`
- `A	frontend/components/ui/carousel.tsx`
- `A	frontend/components/ui/chart.tsx`
- `A	frontend/components/ui/checkbox.tsx`
- `A	frontend/components/ui/collapsible.tsx`
- `A	frontend/components/ui/combobox.tsx`
- `A	frontend/components/ui/command.tsx`
- `A	frontend/components/ui/context-menu.tsx`
- `A	frontend/components/ui/dialog.tsx`
- `A	frontend/components/ui/direction.tsx`
- `A	frontend/components/ui/drawer.tsx`
- `A	frontend/components/ui/dropdown-menu.tsx`
- `A	frontend/components/ui/empty.tsx`
- `A	frontend/components/ui/field.tsx`
- `A	frontend/components/ui/form.tsx`
- `A	frontend/components/ui/hover-card.tsx`
- `A	frontend/components/ui/input-group.tsx`
- `A	frontend/components/ui/input-otp.tsx`
- `A	frontend/components/ui/input.tsx`
- `A	frontend/components/ui/item.tsx`
- `A	frontend/components/ui/kbd.tsx`
- `A	frontend/components/ui/label.tsx`
- `A	frontend/components/ui/marker.tsx`
- `A	frontend/components/ui/menubar.tsx`
- `A	frontend/components/ui/message-scroller.tsx`
- `A	frontend/components/ui/message.tsx`
- `A	frontend/components/ui/native-select.tsx`
- `A	frontend/components/ui/navigation-menu.tsx`
- `A	frontend/components/ui/pagination.tsx`
- `A	frontend/components/ui/popover.tsx`
- `A	frontend/components/ui/progress.tsx`
- `A	frontend/components/ui/radio-group.tsx`
- `A	frontend/components/ui/resizable.tsx`
- `A	frontend/components/ui/scroll-area.tsx`
- `A	frontend/components/ui/select.tsx`
- `A	frontend/components/ui/separator.tsx`
- `A	frontend/components/ui/sheet.tsx`
- `A	frontend/components/ui/sidebar.tsx`
- `A	frontend/components/ui/skeleton.tsx`
- `A	frontend/components/ui/slider.tsx`
- `A	frontend/components/ui/sonner.tsx`
- `A	frontend/components/ui/spinner.tsx`
- `A	frontend/components/ui/switch.tsx`
- `A	frontend/components/ui/table.tsx`
- `A	frontend/components/ui/tabs.tsx`
- `A	frontend/components/ui/textarea.tsx`
- `A	frontend/components/ui/toggle-group.tsx`
- `A	frontend/components/ui/toggle.tsx`
- `A	frontend/components/ui/tooltip.tsx`
- `A	frontend/db/index.ts`
- `A	frontend/db/schema.ts`
- `A	frontend/drizzle.config.ts`
- `A	frontend/drizzle/meta/_journal.json`
- `A	frontend/eslint.config.mjs`
- `A	frontend/examples/d1/app/api/notes/route.ts`
- `A	frontend/examples/d1/db/schema.ts`
- `A	frontend/hooks/use-mobile.ts`
- `A	frontend/lib/maya-api.ts`
- `A	frontend/lib/utils.ts`
- `A	frontend/next.config.ts`
- `A	frontend/package-lock.json`
- `A	frontend/package.json`
- `A	frontend/pnpm-workspace.yaml`
- `A	frontend/postcss.config.mjs`
- `A	frontend/public/babies/week-05.png`
- `A	frontend/public/babies/week-08.png`
- `A	frontend/public/babies/week-12.png`
- `A	frontend/public/babies/week-16.png`
- `A	frontend/public/babies/week-26-reference.png`
- `A	frontend/public/baby-week-22.png`
- `A	frontend/public/comparisons/avocado.png`
- `A	frontend/public/comparisons/bell-pepper.png`
- `A	frontend/public/comparisons/blueberry.png`
- `A	frontend/public/comparisons/cabbage.png`
- `A	frontend/public/comparisons/cauliflower.png`
- `A	frontend/public/comparisons/cherry.png`
- `A	frontend/public/comparisons/grapefruit.png`
- `A	frontend/public/comparisons/guava.png`
- `A	frontend/public/comparisons/honeydew-melon.png`
- `A	frontend/public/comparisons/lemon.png`
- `A	frontend/public/comparisons/lentil.png`
- `A	frontend/public/comparisons/lime.png`
- `A	frontend/public/comparisons/mango.png`
- `A	frontend/public/comparisons/muskmelon.png`
- `A	frontend/public/comparisons/orange.png`
- `A	frontend/public/comparisons/papaya-reference-v2.png`
- `A	frontend/public/comparisons/papaya.png`
- `A	frontend/public/comparisons/pomegranate.png`
- `A	frontend/public/comparisons/poppy-seed.png`
- `A	frontend/public/comparisons/pumpkin-seed.png`
- `A	frontend/public/comparisons/pumpkin.png`
- `A	frontend/public/comparisons/rajma-bean.png`
- `A	frontend/public/comparisons/sesame-seed.png`
- `A	frontend/public/comparisons/strawberry.png`
- `A	frontend/public/comparisons/watermelon.png`
- `A	frontend/public/favicon.svg`
- `A	frontend/public/file.svg`
- `A	frontend/public/globe.svg`
- `A	frontend/public/week-26-growth-v2.png`
- `A	frontend/public/week-26-growth.png`
- `A	frontend/public/window.svg`
- `A	frontend/scripts/build-verified.sh`
- `A	frontend/scripts/execution-profile.mjs`
- `A	frontend/scripts/install-ci.mjs`
- `A	frontend/scripts/install-ci.sh`
- `A	frontend/scripts/install-pnpm.sh`
- `A	frontend/scripts/pnpm-install.mjs`
- `A	frontend/scripts/run-framework.mjs`
- `A	frontend/scripts/sites-env.mjs`
- `A	frontend/scripts/sites-env.sh`
- `A	frontend/tsconfig.json`
- `A	frontend/vendor/shadcn-tailwind-4.13.0.LICENSE.md`
- `A	frontend/vendor/shadcn-tailwind-4.13.0.css`
- `A	frontend/vite.config.ts`
- `A	render.yaml`
- `M	requirements.txt`
- `M	scripts/stage7_fixture_support.py`
- `A	tests/test_demo_api.py`

### Local correction/report files

- `.github/workflows/data-contracts.yml`
- `api/main.py`
- `api/README.md`
- `docs/FINAL-CAPSTONE-MAYA-UI-INTEGRATION-VERIFICATION.md`
- `docs/MAYA-AI-UI-INTEGRATION.md`
- `docs/STAGE-0-CHECK-RESULTS.json`
- `docs/STAGE-10-CAPSTONE-STORY-RESULTS.json`
- `docs/STAGE-10-EVAL-RESULTS.json`
- `docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json`
- `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-9-EVAL-RESULTS.json`
- `frontend/.env.example`
- `frontend/.gitignore`
- `frontend/app/globals.css`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/lib/maya-api.ts`
- `frontend/README.md`
- `README.md`
- `requirements.txt`
- `tests/test_demo_api.py`

The frontend component library and visual assets above came from Kajal's UI commit. The integration did not regenerate or falsely release those assets; user-visible code no longer renders the unapproved fetal comparison/measurement assets as health guidance.

## Exact command inventory

Key commands executed (PowerShell equivalents used where shell redirection differed):

```text
git fetch upstream
git worktree add -b integration/final-capstone-maya-ui <worktree> upstream/integration/capstone-demo-final
git merge --no-ff upstream/integration/maya-ai-ui-demo
python -m compileall -q app api scripts tests
python -m unittest discover -s tests -v
python -m scripts.validate_content
python -m scripts.validate_content --require-review-ready
python -m scripts.run_contract_evals
python -m scripts.run_journey_evals
python -m scripts.run_stage5_retrieval_evals
python -m scripts.run_stage5_paraphrase_evals
python -m scripts.run_stage6_safety_evals
python -m scripts.run_stage7_evals
python -m scripts.run_stage8_evals
python -m scripts.run_stage9_evals
python -m scripts.run_stage10_evals
python -m scripts.check_stage1 ... python -m scripts.check_stage10
python -m scripts.check_stages5_8_rectification
python -m scripts.check_migration_manifest
python -m scripts.check_consolidated_improvements
python -m scripts.check_secret_hygiene
python -m scripts.check_configuration --mode demo
python -m scripts.check_configuration --mode personal
npm ci
npm run lint
npm run build
pnpm exec supabase start
pnpm exec supabase db reset --local --version 20260911001300
pnpm exec supabase db reset --local --version 20260911001200
pnpm exec supabase db reset --local --version 20260911001000
pnpm exec supabase db reset --local
pnpm exec supabase migration up --local
pnpm exec supabase db lint --local --schema app
docker exec -i supabase_db_nestline psql ... < fixture/test SQL
python -m scripts.check_stage2_storage_api
python -m scripts.check_stage3_onboarding_api
python -m scripts.check_stage4_document_api
python -m scripts.check_stage5_retrieval_api
python -m scripts.check_stage10_state_api
python -m scripts.check_stage10_concurrency_and_deletion_api
python -m streamlit run streamlit_app.py --server.headless true --server.port 8511
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

## Remaining owners and gates

- **Kajal/product and qualified specialists:** content, clinical, India-localisation, licence/currency, safety-specification, and emergency-wording review.
- **Privacy/security owner:** real upload scanner, retention/deletion, production threat review, and Personal Mode authorization.
- **Engineering/reviewer:** complete desktop/phone/keyboard walkthrough and inspect the exact pushed CI commit.
- **Provider owner:** select a live provider only after an authorized frozen benchmark and human tone review.
- **Release owner:** deployment, remote migrations, production secrets, domain/hosting, and public release remain separately prohibited.

## Final state declaration

Only fictional/synthetic/redacted data was used. No secret or `.env` value was read into committed output. `.env` remains ignored. No historical migration was modified. No source branch was changed. No PR was created. Nothing was pushed, merged to `main`, deployed, published, transmitted externally, or applied to a remote database.
