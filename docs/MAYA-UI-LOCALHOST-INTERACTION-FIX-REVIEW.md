# Maya UI localhost interaction fix — review handoff

## Scope

This correction is limited to the local Next.js development origin and the landing-page transition into onboarding. It is based on the integrated capstone at commit `fd066a52376cd189111e8cc651719c9861a4fe23`.

Review branch: `fix/maya-ui-local-interaction-review`

## Reproduced behavior

The landing page returned HTTP 200, but the running Next.js server logged that it blocked development resources requested from `127.0.0.1`. The `Begin my journey` handler also waited for a demo API session before changing the view. A browser/API interruption could therefore leave the server-rendered landing page visible with no obvious transition.

## Corrections

- `frontend/next.config.ts`: permits the documented local development hosts `127.0.0.1` and `localhost` through Next.js `allowedDevOrigins`.
- `frontend/app/page.tsx`: opens the onboarding view synchronously when `Begin my journey` is selected. Session creation remains required and occurs through the existing trusted demo API before onboarding submission completes.

No safety, retrieval, agent, validation, State Committer, migration, content-release, deployment, or production-mode behavior was changed.

## Verification

- Next.js live server restarted with the corrected configuration and no repeated blocked-origin warning.
- Browser-origin CORS preflight for `POST /v1/demo/session`: `200`.
- Browser-origin demo session creation: passed.
- Installed headless Chrome interaction:
  - `Begin my journey` visible: passed.
  - click dispatched: passed.
  - onboarding heading rendered: passed.
  - onboarding name field rendered: passed.
- Fictional onboarding-to-home API flow:
  - session identity preserved: passed;
  - week 26 resolved: passed;
  - unexpected safety block: false;
  - home mode: `demo`;
  - fictional test name returned correctly.
- `npm run lint`: passed with 0 errors.
- `npm exec tsc -- --noEmit`: passed with 0 errors.
- `git diff --check`: passed.

## Review boundary

This proves the reported landing-button transition and its immediate API boundary. It does not replace the broader desktop, phone, keyboard, accessibility, or clinical/product review still recorded in `docs/FINAL-CAPSTONE-MAYA-UI-INTEGRATION-VERIFICATION.md`. Public/clinical release remains NO-GO.
