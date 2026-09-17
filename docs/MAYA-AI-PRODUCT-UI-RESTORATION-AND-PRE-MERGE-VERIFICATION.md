# Maya AI Product UI Restoration and Pre-Merge Verification

**Date:** 13 September 2026 (IST)
**Repository:** `kajalchourasia-cmd/nestline`
**Source branch:** `fix/maya-ui-local-interaction-review`
**Exact starting SHA:** `abe80982736b7405ca62f0e0e60bc55cdf356740`
**Restoration branch:** `fix/maya-ai-product-ui-restoration`
**Final pushed SHA:** recorded in the final task response because the commit containing this report cannot truthfully contain its own SHA
**Data used:** fictional, synthetic, or generated redacted evidence only

## Verdicts

- **Controlled Product Preview engineering:** **GO**
- **Ready for Kajal’s pre-merge product/code review:** **GO**, subject to both required GitHub jobs passing on the exact pushed head
- **Public or clinical release:** **NO-GO**
- **Real medical data, authenticated React Personal Mode, or deployment:** **NO-GO**

The React experience is now a complete, locally runnable Product Preview. It is not a production maternal-health service. Clinical, safety-specification, India-localisation, content-publication, image-licence, privacy/security, live-provider, and deployment gates remain open.

## Baseline and scope

The branch was created from the exact reviewed correction commit `abe80982736b7405ca62f0e0e60bc55cdf356740`. The valid dependency, CORS, CI, landing interaction, onboarding safety-block, and zero-generation urgent fixes were preserved.

No commit was made on `main`; the local `main` ref remained `039b1a688488dcd0531cba05fe8a039979e7b3d9` throughout this work. No PR, merge, deployment, remote migration, external contact, real-data use, or paid-provider call occurred.

## Product restoration

The implementation restores and connects:

1. the complete landing view and immediate “Begin my journey” action;
2. the five-step onboarding flow;
3. pregnancy and postpartum selection;
4. name, exact week, approximate month, due date, birth date, diet, allergy, symptoms, and fictional care-record input;
5. pregnancy dashboard KPIs, trimester tracker, comparison card, and persistent safety access;
6. postpartum recovery, nourishment, feeding, wellbeing, and care-record surfaces;
7. nutrition, movement, symptoms, wellbeing, FAQ, and care-record tabs;
8. designed unavailable states for unreleased content instead of deleting product structure;
9. the full week library;
10. connected nutrition, movement, wellbeing, and balanced plan drafting;
11. Ask Maya suggestions, free text, provenance, citations, clarification, abstention, and urgent display;
12. loading, empty, validation, recoverable error, retry, blocked, gated, and unavailable states;
13. desktop and phone layouts;
14. stale in-memory session validation and recovery;
15. React as the primary user-facing Maya surface, with Streamlit retained for internal engineering and legacy verification.

All displayed health content continues through the accepted evidence and display-validation boundaries or remains visibly gated.

## Journey and comparison behavior

### Library inventory

- Library rows: **41/41**, contiguous from week 1 through week 41.
- Weeks 1–2 remain timing-only and do not claim an embryo/baby comparison.
- Referenced image assets: **29/29 present**.
- Source asset inventory retained: **25** comparison images, **5** staged baby images, and **1** shared week-22 baby image.
- Later-week rounded sequence includes small muskmelon, small cabbage, cabbage, honeydew melon, small watermelon, large muskmelon, full-size watermelon, and large watermelon.
- Rejected elongated-object labels “banana” and “carrot” are absent.

### Approval representation

The UI uses the recorded product/content decision only:

- Approval ID: `KAJAL-STAGE-1-PRODUCT-REVIEW-2026-09-11`
- Reviewer: Kajal
- Capacity: Product/content review
- Decision date: 11 September 2026
- Catalogue version: `1.0.0`
- Catalogue SHA-256: `D3554DFE325FE3DEBF8A7FFF78A391BA262200F885B305C08946448697E247E8`
- Product-reviewed week set derived from the governed CSV: **13 weeks** (`20, 21, 22, 23, 24, 25, 26, 28, 29, 31, 32, 33, 36`)

Other weeks remain explicitly product-review pending. Measurement source/review and image ownership/licence are separate fields. Measurements are never rendered and are labelled “Measurements hidden.” No clinical, licence, India-localisation, or publication approval was invented.

### Timing verification

- Exact week 26 rendered the week-26 baby and small-cabbage editorial comparison.
- Month 6 remained an approximate week range; the UI stated that it had not guessed a single week and rendered no single-week comparison.
- A due date 140 days ahead resolved through the Stage 3 Journey Resolver to an exact week near week 20 and displayed that resolved week.
- A birth date 14 days earlier rendered postpartum timing and the postpartum dashboard.
- Postpartum showed no pregnancy comparison, `FetalVisual`, or `FruitVisual`.

## Safety preservation

Stage 6 still runs before Stage 7/8 ordinary generation.

- Stage 6 development cases: **65/65 passed**.
- Critical safety cases: **61/61 passed**.
- Urgent zero-generation cases: **35/35 passed**.
- Ambiguous/failure cases conservatively stopped: **21/21 passed**.
- Tested unsafe reassurance: **0/65**.
- Browser urgent case displayed the unique fixed “This may need urgent medical attention” route and **Ordinary generation calls: 0**.
- Browser ambiguous case stopped for clarification and did not open ordinary generation.
- Mixed and urgent paths remained blocked before ordinary worker/composition calls.

The safety specification remains draft; live/public routing therefore remains fail-closed. These results are software-contract evidence, not clinical validation.

## Connected service regression evidence

The final clean-environment checker pass completed **28/28 command groups**:

| Area | Result |
|---|---:|
| Stage 1 governed ingestion | pass |
| Stage 2 storage/contracts | pass |
| Journey development evals | **26/26** |
| Stage 3 UI and checker | pass |
| Stage 4 readiness, UI, and checker | pass |
| Stage 5 retrieval, paraphrase, and checker | pass |
| Stage 6 safety eval and checker | pass |
| Stage 7 orchestration eval and checker | pass |
| Stage 8 validation eval and checker | pass |
| Stages 5–8 rectification checker | pass |
| Stage 9 eval, UI, and checker | **42/42 cases; 29/29 critical; 9/9 stories** |
| Stage 10 eval, UI, and checker | **33/33 cases; 13/13 critical; 9/9 stories** |
| Migration manifest | **17/17** |
| Consolidated improvement checker | pass |
| Connected service journeys | **17/17** |
| Secret hygiene | **0 findings** |

Stage 5’s frozen synthetic development set remained **28/28** for expected behavior, with Recall@5 **18/18**, citation precision **18/18**, confirmed-personal-fact precision **12/12**, graph-path correctness **1/1**, and zero wrong-week, wrong-jurisdiction, unapproved-source, cross-workspace, or conflict/proposal-personalisation violations. Fixture embeddings and this small synthetic set do not establish production retrieval quality.

Stage 7 remained **76/76 cases** and **64/64 critical**. Stage 8 remained **69/69 cases** and **57/57 critical**.

## Automated verification

| Command/check | Actual result |
|---|---:|
| Fresh Python 3.12.7 venv creation | pass |
| `python -m pip install -r requirements.txt` in fresh venv | pass |
| `python -m unittest -v tests.test_demo_api tests.test_maya_ui_restoration` | **27/27 passed** |
| `python -m unittest discover -s tests -v` | **541/541 passed; 0 failed; 0 skipped** |
| `python -m scripts.validate_content` | pass; 63 profiles, 0 published, 31 sources, 55 spans, 56 fragments |
| `python -m scripts.validate_content --require-review-ready` | pass |
| `python -m scripts.run_contract_evals` | **64/64 passed** |
| `python -m scripts.check_stage0` | expected exit 1: software checks pass; publication gate remains closed |
| Clean `npm ci` under Node 24 | pass; 674 packages installed |
| `npm run lint` | pass; 0 errors |
| `npm run typecheck` | pass |
| `npm run check:interactions` | **38 controls checked** (33 native + 5 component), 0 failures |
| `npm run build` under Node 24 | pass; **3/3** static pages generated |
| `python scripts/capture_maya_restoration_evidence.py` | **19/19 browser cases passed** |
| `git diff --check` | pass |

The host’s system `npm.cmd` initially launched lifecycle scripts with Node 18.15 and Next.js correctly rejected it. Prepending the bundled Node 24 binary produced the passing build above. The repository already declares `node >=22.13.0`, and GitHub uses Node 24. The clean npm install emitted one Windows EPERM cleanup warning for an irrelevant FreeBSD WASM optional directory but exited successfully; lint, TypeScript, interaction, runtime, and production build checks then passed.

The optional browser harness is reproducible through `requirements-ui-verification.txt`; `MAYA_NODE` and `MAYA_CHROME` can override standard executable discovery.

## Interactive browser walkthroughs

Automated Chrome drove the real Next.js page and FastAPI service. **19/19 passed**:

1. pregnancy exact-week comparison;
2. full pregnancy navigation;
3. 41/41 library controls;
4. rounded later-week sequence;
5. allergy propagation to plan;
6. API-connected proposed plan;
7. suggested-question fidelity;
8. validated routine chat with provenance;
9. ambiguous-symptom clarification stop;
10. unique fixed urgent message with zero generation;
11. approximate month without exact-week guessing;
12. due-date resolution;
13. postpartum recovery/nourishment/feeding/wellbeing;
14. postpartum pregnancy-comparison suppression;
15. actual backend restart and automatic fictional-context recovery;
16. API outage, visible error, backend restart, and successful Retry;
17. desktop principal views;
18. exact 390×844 viewport with no horizontal page overflow;
19. keyboard focus and activation.

Keyboard focus traversed named controls in order: Maya home, Ask Maya, Begin my journey. Each showed a **3px** focus outline, and Enter on Begin my journey opened the first onboarding field without mouse input.

## Screenshots and machine-readable evidence

- [Landing — desktop](maya-ui-restoration-evidence/01-landing-desktop.png)
- [Onboarding — desktop](maya-ui-restoration-evidence/12-onboarding-desktop.png)
- [Pregnancy dashboard — week 26](maya-ui-restoration-evidence/02-pregnancy-dashboard-week-26.png)
- [Complete week library](maya-ui-restoration-evidence/03-week-library-desktop.png)
- [Validated weekly plan](maya-ui-restoration-evidence/04-validated-plan-desktop.png)
- [Ask Maya validated answer](maya-ui-restoration-evidence/05-ask-maya-validated-answer.png)
- [Fixed urgent safety bypass](maya-ui-restoration-evidence/06-urgent-safety-bypass.png)
- [Approximate month-range dashboard](maya-ui-restoration-evidence/07-month-range-dashboard.png)
- [Postpartum dashboard](maya-ui-restoration-evidence/08-postpartum-dashboard-desktop.png)
- [API recovery success](maya-ui-restoration-evidence/09-api-recovery-success.png)
- [Landing — exact 390px viewport](maya-ui-restoration-evidence/10-landing-mobile.png)
- [Pregnancy dashboard — exact 390px viewport](maya-ui-restoration-evidence/11-pregnancy-dashboard-mobile.png)
- [Interactive results](maya-ui-restoration-evidence/interactive-walkthrough-results.json)
- [Engineering check results](maya-ui-restoration-evidence/engineering-check-results.json)
- [Canonical content/publication results](maya-ui-restoration-evidence/canonical-check-results.json)

## Self-review and consolidated correction

The thorough self-review found and corrected:

| Finding | Correction | Final evidence |
|---|---|---|
| The sample landing context used broad “Nuts,” which had no exact accepted schedule evidence and correctly abstained. | Changed only the fictional sample to the accepted exact “Peanut” constraint. | Connected plan and visible constraint pass. |
| Inline stale-session recovery cleared `homeData`, unmounted the plan component, and discarded a successful retry response. | Split session-identity invalidation from full UI reset so inline recovery keeps the active screen mounted. | Actual backend restart and API failure/retry pass. |
| The first urgent screenshot trigger matched a prior clarification trace. | Required unique fixed urgent wording, urgent title, and zero-generation text; scrolled the urgent card into view. | Dedicated urgent screenshot and browser assertion pass. |
| Ordinary Chrome window sizing produced a 548px inner viewport while evidence described 390px. | Used CDP device metrics and required exact width 390 with no horizontal overflow. | Landing and dashboard both report width/scrollWidth 390/390. |
| Keyboard evidence recorded generic focus steps but did not prove visible focus or activation. | Required `:focus-visible`, nonzero outline, and Enter-key onboarding navigation. | Three named buttons each show 3px outline; activation succeeds. |
| TypeScript ran during build but had no named gate. | Added `npm run typecheck` using `tsc --noEmit`. | Explicit TypeScript check passes. |
| The browser script contained a host-specific Node path. | Added PATH/environment executable discovery and a separate pinned verification requirements file. | Portable script compiles and reruns 19/19 with override. |
| The prior integration report described the conservative pre-restoration UI as current. | Marked it historical and updated current React/Streamlit documentation without rewriting its evidence. | README and integration documentation reviewed. |

The pre-fix fictional failure screenshot and body text remain in `maya-ui-restoration-evidence/` as honest self-review evidence. They contain no real user or medical data.

## Changed-file inventory

### Product and integration code

- `.github/workflows/data-contracts.yml`
- `api/main.py`
- `frontend/.gitignore`
- `frontend/app/baby-growth-library.ts`
- `frontend/app/globals.css`
- `frontend/app/page.tsx`
- `frontend/app/maya/chat.tsx`
- `frontend/app/maya/dashboard.tsx`
- `frontend/app/maya/onboarding.tsx`
- `frontend/app/maya/visuals.tsx`
- `frontend/lib/maya-api.ts`
- `frontend/package.json`
- `frontend/scripts/check-product-interactions.mjs`
- `requirements-ui-verification.txt`
- `scripts/capture_maya_restoration_evidence.py`

### Tests

- `tests/test_demo_api.py`
- `tests/test_maya_ui_restoration.py`

### Current documentation

- `README.md`
- `frontend/README.md`
- `docs/MAYA-AI-UI-INTEGRATION.md`
- `docs/FINAL-CAPSTONE-MAYA-UI-INTEGRATION-VERIFICATION.md` (historical-status notice only)
- `docs/MAYA-AI-PRODUCT-UI-RESTORATION-AND-PRE-MERGE-VERIFICATION.md`

### Canonically regenerated evidence

- `docs/STAGE-0-CHECK-RESULTS.json`
- `docs/STAGE-5-PARAPHRASE-EVAL-RESULTS.json`
- `docs/STAGE-5-RECTIFICATION-EVIDENCE-PACKETS.json`
- `docs/STAGE-5-RETRIEVAL-METRICS.json`
- `docs/STAGE-9-EVAL-RESULTS.json`
- `docs/STAGE-10-CAPSTONE-STORY-RESULTS.json`
- `docs/STAGE-10-EVAL-RESULTS.json`
- `docs/STAGES-0-8-10-SERVICE-JOURNEY-RESULTS.json`
- every file under `docs/maya-ui-restoration-evidence/`

## Remaining limitations and owners

| Limitation | Current safe behavior | Owner/gate |
|---|---|---|
| 0/63 profiles publicly released | Cards remain visible but gated; runtime does not present draft health content as published guidance. | Qualified content/clinical/localisation/licence review and publisher |
| Safety specification draft | Product-preview evaluation only; live/public route fails closed. | Qualified safety and clinical review |
| Measurements and dimensions unverified | Measurements hidden everywhere. | Clinical/measurement review |
| Image ownership/licence incomplete | Product Preview labels the limitation. | Licence/ownership review |
| React authentication and durable personal state absent | Sample-only Product Preview; no real data accepted. | Privacy/security engineering and Stage 10 React API integration |
| Real document upload absent | Disabled control; fictional sample record only. | Private storage, scanner, extraction, confirmation, RLS, deletion, privacy approval |
| Live provider not selected | Deterministic fixture only; no Personal Mode fallback. | Frozen live-provider benchmark and team selection |
| No deployment or operational review | Local-only run instructions. | Team-authorized security/privacy/legal/release preparation |
| Automated walkthrough is not user research | Evidence is labelled engineering verification only. | Independent product/usability review if required |

## Git and external-action truth

This report was prepared before the required feature-branch push. The exact pushed SHA and GitHub job URLs are therefore reported in the final task response after the branch exists and both jobs are inspected. The branch will be pushed only to `upstream/fix/maya-ai-product-ui-restoration`, without force.

Nothing was merged to `main`. No PR was created. Nothing was deployed, published, transmitted externally, or applied to a remote database. No real medical/personal data, secret, token, `.env`, or service-role key was added.
