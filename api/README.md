# Maya AI demo API

This thin FastAPI adapter connects the React interface to the accepted Stage 3 journey and Stage 6–8 safety, orchestration, planning, and validation services. It exposes controlled fictional Demo Mode only.

Urgent and unresolved onboarding symptoms are returned with `safety_blocked = true`, so the React client stays on the fixed safety/clarification route. Urgent chat results report zero ordinary-generation calls. Sessions are isolated in memory and disappear when the API restarts.

The adapter does not expose Personal Mode, accept real medical documents, or implement the Stage 10 durable State Committer/save/review lifecycle. Those accepted Stage 10 capabilities remain on the Streamlit/storage surface.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The frontend uses `NEXT_PUBLIC_MAYA_API_URL`, whose local placeholder defaults to `http://127.0.0.1:8000`. No secret is required for the controlled demo.