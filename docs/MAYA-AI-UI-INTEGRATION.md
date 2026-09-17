# Maya AI UI integration

## Current outcome

The React/Next.js application in `frontend/` is the primary Maya AI user experience. It uses the thin FastAPI adapter in `api/` to expose accepted Product Preview capabilities from Stages 3–8. Streamlit remains an internal engineering, evidence, and legacy verification surface.

This document describes the current restoration branch. The earlier integration report is retained as a historical review baseline and is superseded for product-surface status by `MAYA-AI-PRODUCT-UI-RESTORATION-AND-PRE-MERGE-VERIFICATION.md`.

## Connected behavior

| React surface | Service boundary | Current behavior |
|---|---|---|
| Begin my journey | `POST /v1/demo/session` | Opens onboarding immediately; creates an isolated in-memory fictional session. |
| Pregnancy/postpartum timing | Stage 3 Journey Resolver | Preserves exact week, approximate range, due-date, and postpartum semantics. |
| Preferences and allergies | Authenticated-shape fictional context | Keeps dietary preferences and confirmed sample allergies separate. |
| Symptoms during onboarding/chat | Stage 6 Safety Gate | Urgent and clarification routes block ordinary continuation; urgent output makes zero ordinary-generation calls. |
| Dashboard | `GET /v1/demo/home/{session}` | Returns journey KPIs, governed card states, fictional record status, and eligible editorial comparison metadata. |
| 41-week library | Governed editorial catalogue | Shows weeks 1–41; measurements remain hidden and review/licence limitations remain visible. |
| Plans | Stages 6 → 7 → 8 | Returns validated proposed schedules with applied constraints; nothing is durably saved. |
| Ask Maya | Stages 6 → 7 → 8 | Sends displayed suggestions exactly, renders provenance/citations, and preserves safety precedence. |
| Restart/retry | Demo session validation | Detects stale server memory, rebuilds selected fictional context, and retries without discarding the active UI result. |

## Preserved boundaries

- The repository has 63 authored profiles and 0 published profiles.
- No comparison is represented as clinically or measurement approved.
- The product-approved editorial sequence is shown only as a non-clinical Product Preview with measurements hidden.
- Real medical-file upload is disabled.
- React Personal Mode, durable Stage 10 commits, production provider selection, remote migrations, deployment, and public/clinical release remain unavailable.
- The fixture provider is deterministic test/demo infrastructure and cannot silently serve Personal Mode.
- Passing local tests is software-contract evidence, not clinical validation.

## Local run

Follow `frontend/README.md`. The committed `frontend/.env.example` contains only `NEXT_PUBLIC_MAYA_API_URL=http://127.0.0.1:8000`. No `.env` or secret is committed.

## Source and restoration lineage

The restoration branch `fix/maya-ai-product-ui-restoration` was created from the reviewed correction commit `abe80982736b7405ca62f0e0e60bc55cdf356740`, preserving the safety, dependency, CI, CORS, and onboarding interaction fixes. The complete verification and screenshot evidence is recorded in `docs/MAYA-AI-PRODUCT-UI-RESTORATION-AND-PRE-MERGE-VERIFICATION.md`.
