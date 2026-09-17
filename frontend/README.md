# Maya AI React product

The React/Next.js application in this directory is the primary Maya AI user experience. It exposes the approved local Product Preview over the accepted journey, safety, orchestration, retrieval, and validation services. Streamlit remains an internal engineering, evidence, and legacy verification surface.

## Available in the Product Preview

- five-step pregnancy and postpartum onboarding;
- exact pregnancy week, due-date resolution, approximate month ranges, and postpartum timing;
- a complete 41-week editorial comparison library;
- pregnancy and postpartum dashboards;
- nutrition, movement, symptoms, wellbeing, FAQ, and care-record tabs;
- validated proposed day/week plans;
- Ask Maya with evidence provenance and applied constraints;
- Stage 6 clarification and fixed urgent routes before ordinary generation;
- stale in-memory session recovery and visible API retry;
- responsive desktop and 390px phone layouts.

Medical measurements remain hidden. Gated content stays visible with honest awaiting-review states. Real health-data upload, authenticated Personal Mode, durable React saving, clinical approval, live-provider selection, and deployment are unavailable. Use sample information only.

## Requirements

- Python 3.12
- Node.js 22.13 or later; CI uses Node 24
- npm

## Local run

From a clean repository checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Terminal 1, repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`.

## Reset and recovery

Use **Maya home** to return to the landing page and **Explore a sample week** to reset deterministic fictional context. Browser session IDs are temporary. If the API restarts, the UI validates the stored ID, recreates the fictional session from browser-session context, and retries the requested action once. If the API is unavailable, the relevant surface shows an error and retry action.

To reset manually, clear local storage and session storage for `127.0.0.1:5173`, or open a private browser window.

If the API does not respond, verify `http://127.0.0.1:8000/healthz` and `NEXT_PUBLIC_MAYA_API_URL` in `.env.local`. The committed `.env.example` contains a local placeholder only. No `.env` file or credential belongs in Git.
