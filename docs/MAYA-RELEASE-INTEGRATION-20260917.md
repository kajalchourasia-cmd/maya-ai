# Maya AI integration review board — 17 September 2026

## Scope

User-authorised integration branch: `integration/maya-release-20260917t143720z`.
Target: `kajalchourasia-cmd/nestline:main`. No merge into main or deployment is authorised in this task; the owner reviews and merges the pull request.

The original running app and other dirty worktrees remain separate. Before integration, tracked files, nonignored untracked files, staged/unstaged patches and all local Git refs were backed up with SHA-256 verification. Credentials and ignored private data remain in their original locations rather than being copied to the public repository.

## Branch and worktree decisions

| Input | Decision |
|---|---|
| Latest main `ab29e630e8093037ae89e1e3ee3abdcea68ecfb4` | Included in the integration ancestry. Recheck remote before pushing. |
| `fix/maya-ai-product-ui-restoration`, HEAD `81533e3` | Base for the integration branch; preserves the existing restored design. |
| Dirty local `fix/maya-onboarding-flow-local` | Current application, corpus/retrieval/runtime work, migrations, static content, UI, chat, plans, tests and implementation documents copied into the integration worktree. |
| `integration/maya-ai-ui-demo` | Already an ancestor of the restoration branch; no separate duplicate merge needed. |
| `fix/maya-ui-local-interaction-review`, unique commit `53775c8` | Reconcile optional-record API metadata/tests. Keep the newer record-free onboarding UI, not the superseded single-file page. Preserve the historical review document. |
| Stage 0/1, Stage 5–8 closure and final capstone branches | Their remote heads are already ancestors of latest main. |
| Dirty `docs/maya-ai-public-readme` | Incorporate documentation branding; rewrite outdated README claims for the current application. Keep hashed historical verifier/source records and persisted identifiers unchanged. |
| Old local main's untracked `ui/` | Backed up, not copied into the product: an older standalone frontend with local plan data, superseded by `frontend/`. |
| Final presentation | Include seven-slide PPTX and portable presenter script; link the demo video and case study from the README. |

Do not force-push other branches or delete them. Keeping an old branch does not mean its superseded UI should replace the current product.

## Review checklist

- [x] Existing local work preserved before integration.
- [x] Public-facing Maya AI / Ask Maya naming and submission links reviewed.
- [x] Current UI retained; no second frontend or fixture answer adapter introduced.
- [x] Development and publication permissions remain distinct.
- [x] Shared onboarding context, record-free access and separate fixture/product lanes remain covered by tests.
- [x] Updated orchestration/validation JSON schemas generated from their Python definitions.
- [x] CI expanded to include pytest-style regressions, frontend regression tests and TypeScript checking.
- [x] React lifecycle issues found by lint corrected; timeline results keyed to their inputs.
- [x] Button-checker false positive fixed with TSX parsing, with regression tests.
- [x] Credentials, private source exports, admission packets, provider ledger, database contents, node_modules and local video outputs excluded.
- [ ] GitHub checks on the pushed integration commit: review in the pull request.
- [ ] Owner review and merge into main.

## Local verification

- Final merged Python regression run: **832 passed + 315 subtests passed; 60 skipped**. Skips include optional private-artifact/infrastructure-dependent checks; they are not counted as verified.
- Frontend regression run: **47 passed; 0 failed, 0 skipped**.
- Frontend ESLint, TypeScript and interaction checks: passed.
- Production build: passed using Next.js 16.3.4 / webpack. GitHub also checks its normal clean-install build.
- All 29 offline Python commands in the CI validation job passed, including content, Stage 1–10, consolidated-improvement, migration-manifest and secret-hygiene checks.
- No new paid model calls or live corpus re-embedding performed for this integration. Earlier live-test reports retain their original scope.
- Supabase clean-install/upgrade tests run in GitHub's disposable runner. The user's populated local Docker database was not reset.

The optional-record branch was merged with its 13-line legacy API metadata addition, record-free access regression and historical review document. Three frontend conflicts were resolved using the already-committed current UI: its onboarding has no upload requirement and its normal API calls must not be reverted to fixture endpoints. The final merged suite includes the additional regression above.

## What GitHub does not transfer

A repository push transfers committed code and permitted assets. It does **not** transfer the locally populated Supabase database, model keys, private source exports, development admission packet or cost ledger. A new computer still needs the documented authorised restore/configuration procedure. No unrestricted medical deployment, live clinician handoff or record upload is claimed by this PR.

Earlier implementation reports are historical evidence, not a replacement for the current PR checks. Failed checks must be resolved or clearly left outstanding before merging.

## Recovery follow-up (17 September 2026)

A separate encrypted runtime backup now includes a current database dump, roles, supplied corpus,
cached real vectors, configurations and ledgers. The isolated database restore and content/search/access
checks passed; the working database was not altered. The public repository receives only the
safe recovery guide, version catalogue, read-only integrity checker and tests. No private payload,
credential, recovery key or database dump is committed. See the backup/new-computer guide.

Off-device backup verification and a full second-computer application rehearsal are still outstanding.
These remain explicit handoff checks, not implied by a green code-test suite or successful pg_restore.

Recovery follow-up verification: **848 Python tests and 315 subtests passed; 61 tests skipped**.
This includes 16 new recovery-checker tests; its symlink test was skipped on this Windows host because
unprivileged link creation is unavailable. The remaining skip scope is unchanged. The actual encrypted
archive SHA-256/size and all 1,177 payload-file hashes passed the new read-only checker. The existing
credential scan found zero findings across 705 text files. Frontend code was not changed in this follow-up;
new GitHub checks must still be reviewed on the pushed commit. No paid provider calls were performed.
