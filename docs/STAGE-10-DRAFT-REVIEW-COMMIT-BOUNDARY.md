# Draft, review and durable-commit boundary

| State/action | Meaning | Durable? | What may happen next |
|---|---|---:|---|
| generated draft | Agent/composer output that passed applicable display validation | No | User may inspect, edit or discard. |
| change intent | A user requests a change | No | Revalidate the proposed result. |
| `draft` plan | Validated proposal | Yes only through State Committer | Requires explicit review transition. |
| `user_reviewed` plan | Authenticated user explicitly reviewed the exact version | Yes | May receive an explicit save command. |
| explicit save command | Typed command with idempotency key, expected state version, provenance and confirmation | Command | State Committer reloads current truth and commits atomically or rejects. |
| `saved` / `active` plan | Persisted accepted version | Yes | Active use only while dependencies remain current. |
| `stale` plan | A material dependency changed or could not be safely resolved | Yes | Visible with causal reason; cannot silently reactivate or save again. |
| `replaced` / `archived` | Historical version retained | Yes | Linked history remains auditable. |
| simulated review | Consented, minimal, explicitly simulated state machine | Yes through State Committer | No real clinician contact or guarantee. |
| external submission | Transmission to a real reviewer/service | Unavailable | Requires a separately authorized integration and approvals. |

A view, rerun, retry, chat answer or agent output is never confirmation. Extracted facts remain proposed until an authenticated confirm/correct/reject command succeeds. Personal mode uses `SupabaseStateCommitterClient`; Demo mode uses only isolated allowlisted fictional in-memory workspaces. Agents and models have no direct database or service-role authority. Duplicate keys are idempotent; stale expected versions fail without overwriting newer truth.
