# Maya UI optional-record access — review handoff

> Historical review of commit `53775c8`. The current product has record-free onboarding and separate normal API endpoints. The legacy API metadata/test changes are retained; the old frontend is superseded. See the [integration review board](MAYA-RELEASE-INTEGRATION-20260917.md).

## Decision implemented

A care record is optional in the controlled fictional demo. A user must still supply a basic pregnancy or postpartum timeline because the accepted journey and safety contracts require stage context, but the final onboarding step now provides a clear `Continue without records` action.

The wording deliberately does not say that an answer “might not be correct.” When relevant personal context is unavailable, Maya states that no record is connected, asks for the missing information or stops, and does not guess.

## User-visible behavior

- The final onboarding screen states that care records are optional.
- `Continue without records` enters the portal without enabling the fictional sample record.
- The dashboard shows `No care record connected` and explains the personalisation limit.
- Pregnancy and postpartum dashboards include general product FAQs that contain no medical guidance.
- The chat header states that no care record is connected.
- Missing-context and abstention details are visible under `Needs confirmation`.
- A record-dependent question such as `What allergies are in my record?` abstains with `missing_record` and makes zero ordinary-generation calls.
- The fictional sample-record route remains available and separate.

## Safety and scope boundaries

- The deterministic Safety Gate still runs before ordinary chat generation.
- The journey timeline remains required; care records, allergies, diet preferences and sample documents remain optional.
- Missing, conflicting or unconfirmed information does not become personal context.
- No real upload, diagnosis, medication change, clinical claim, deployment or durable production write was added.
- The FAQ section explains product behavior only. Public health-content release remains blocked because no weekly profile is published.

## Changed files

- `frontend/app/page.tsx` — explicit skip action, optional-record explanation, limited-context dashboard notice, product FAQs and visible chat uncertainty.
- `frontend/app/globals.css` — responsive styles for the new states.
- `frontend/lib/maya-api.ts` — typed record-context fields.
- `api/main.py` — explicit `connected` / `not_connected` record context and honest notices in home/chat responses.
- `tests/test_demo_api.py` — record-free onboarding and record-dependent abstention regression.

## Verification results

- Focused connected-demo API suite: **12/12 passed**.
- Full Python unit suite: **526/526 passed**.
- Frontend ESLint: **passed, 0 errors**.
- TypeScript `--noEmit`: **passed, 0 errors**.
- Next.js production build: **passed; 3/3 static routes generated**.
- Real headless-browser walkthrough: **13/13 assertions passed**:
  - landing button opened onboarding;
  - week 26 was entered;
  - optional-record copy and skip action were visible;
  - skip action completed onboarding;
  - no-record dashboard notice and FAQs rendered;
  - no API error appeared;
  - general-question chat opened;
  - limited-context notice rendered;
  - record-dependent question submitted;
  - missing-record response and visible uncertainty rendered.
- `git diff --check`: **passed**.
- Secret hygiene: **567/567 files scanned; 0 credential findings; `.env` remains ignored**.

## Review boundary

This change is ready for engineering review of the record-free controlled-demo path. It does not claim clinical validation, public release readiness, production Personal Mode readiness, or completion of the broader manual phone/keyboard/accessibility review.
