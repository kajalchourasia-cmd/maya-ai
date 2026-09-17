# Maya — Step 2: local infrastructure and provider verification

Later update: the historical zero-corpus state below was superseded by [Step 3: real recovered-corpus import](MAYA-IMPLEMENTATION-STEP-3-CORPUS-IMPORT.md) on 16 September. The local database now has one draft release and 55 evidence chunks; product RAG is still not verified. The Step 2 results below remain the record of that earlier check.

Date: 16 September 2026  
Verdict: **STEP 2 COMPLETE — local infrastructure, OpenAI generation/embedding access, localhost bindings and the real-vector database round trip are verified. Corpus loading and application RAG remain unimplemented/unverified.**

This report records executed checks, not a claim that RAG, the dashboard or Ask Maya is complete.

## Latest infrastructure update — 08:46 UTC

The earlier local network blocker is resolved. Three exposed containers were recreated with explicit `127.0.0.1` bindings while retaining their original volume mounts and byte-verified runtime configuration files. The original containers were renamed with `-before-loopback`, disconnected from the service network and left stopped as backups. No original container or volume was deleted. No system-wide Docker/firewall setting was changed.

- Database: `127.0.0.1:54322`; API: `127.0.0.1:54321`; Studio: `127.0.0.1:54323`.
- Actual running-container bindings were checked, not merely inferred from printed URLs.
- Auth and REST returned HTTP 200. Studio returned a local 307 redirect followed by HTTP 200 on the same local origin.
- All seven active Maya service containers are running. Services with Docker health checks report healthy; REST was checked over HTTP.
- The full existing SQL suite passed again: **325 assertions across 8 files**. Schema lint reported no errors.
- Setup and repair regression tests: **28 passed**.
- Saved real OpenAI embeddings were inserted into a temporary PostgreSQL `vector(1536)` table. The flower query ranked `garden_rose` first (cosine similarity approximately 0.55364) and `garage_bicycle` second (approximately 0.19122).
- Database scores matched an independent Python cosine calculation within 0.00001. The transaction rolled back, the temporary table was absent afterward, and the 17 migrations remained applied.
- **No new provider calls or costs** were incurred in this infrastructure/round-trip step.
- Actual `guideline_chunks` and `content_releases` remain zero. This is not yet corpus retrieval, a Stage 5 RPC query with real corpus records, or a chatbot result.

The first round-trip harness run encountered multiline JSON parsing; its SQL output was made consistently single-line JSONB and the rerun passed. The initial Studio health check did not follow redirects; it now follows at most three redirects restricted to Studio's exact local origin and checks the final HTTP 200. Neither correction changed a database assertion or source content.

New evidence:

- `reports/local/supabase-kajal/loopback-repair.json`
- `reports/local/supabase-kajal/local-services-verification.json`
- `reports/local/supabase-kajal/real-vector-roundtrip.json`
- Updated `test-redacted.log` and `lint-redacted.log` in the same directory.

### Start/stop this preserved local setup

From the repository directory, use the existing Python runtime to run:

```text
python scripts/maya_local_database.py resume
python scripts/maya_local_database.py status
python scripts/check_maya_local_services.py
python scripts/maya_local_database.py test
python scripts/check_maya_vector_roundtrip.py
python scripts/maya_local_database.py stop
```

`start` also resumes the repaired containers when the repair record exists. The helper never starts the `-before-loopback` backups. Do not start those backups while their replacements run: the database backup container references the same volume and is **not** an independent data snapshot.

If `python` is not available on PATH here, the verified interpreter is `C:\Users\Hrishikesh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

Do not use a root-directory bare `supabase start`, `db reset` or `stop --no-backup` as a substitute: the original repository configuration still names `nestline`, while this isolated setup uses the copied working directory under `reports/local/supabase-kajal`. A future recreation/upgrade must repeat the explicit binding check; this repair does not change upstream CLI defaults.

The specific deeper reason the network-wide default was not honoured has not been established. The confirmed cause of the exposure was the absence of an explicit host IP in the original containers' published port bindings; the repaired containers use explicit localhost addresses.

**Next milestone:** implement the idempotent, transactional corpus loader using the existing ingestion/review artifacts and retrieval schema, then verify an actual source-bearing retrieval trace. Preserve all source IDs, reviews and draft/public boundaries; do not invent publication approvals.

Historical updates below are retained for traceability; their resolved blockers are not current blockers.

## Latest update — replacement key verified at 08:25 UTC

After Kajal explicitly supplied another replacement key, a new bounded OpenAI-only test succeeded on 16 September 2026:

| Check | Actual result |
|---|---|
| `gpt-5.4-mini` Responses API | HTTP 200; completed; returned the expected test marker; 22 input / 7 output tokens |
| `text-embedding-3-small` embeddings | HTTP 200; 3 finite, nonzero vectors, each 1,536 dimensions; 23 input tokens |
| Estimated combined token cost | USD **0.00004846**, based on the recorded token prices; not an account-wide billing audit |
| Setup regression tests | 12 passed |

Evidence: `reports/local/provider-smoke/ledger-after-key-replacement-2.json`. The two earlier 401 ledgers remain intact. Synthetic vectors are retained in ignored `reports/local/provider-smoke/synthetic-vectors.json` for the subsequent local database round-trip check. No private health data was sent.

**The OpenAI credential blocker below is historical and now resolved.** xAI was intentionally not tested in this OpenAI-only request. The Docker stack remains stopped, its data preserved. No corpus import, actual evidence retrieval, clinical answer, dashboard change or runtime activation was performed by this key verification.

The earlier findings below describe the initial Step 2 run. The local binding and vector round trip were subsequently completed as recorded above; another OpenAI key replacement is not needed.

## What was completed

| Item | Observed result |
|---|---|
| Supabase CLI | Installed the repository-pinned version 2.117.0 with the existing frozen lockfile |
| Isolated project | Created `maya-kajal-local` under `reports/local/supabase-kajal`; did not link any hosted project |
| Source preservation | Copied and hash-checked 32 SQL files, including all 17 migrations; original migrations/configuration unchanged |
| Migration replay | All 17 applied successfully to the new local PostgreSQL database |
| Extensions | Confirmed `vector` 0.8.2, `pgcrypto` 1.3 and `uuid-ossp` 1.1 |
| SQL verification | **325 assertions passed across 8 existing pgTAP files** |
| Database lint | No schema errors reported in extensions/private/public |
| New setup tests | **12 passed**: fixed smoke inputs, usage validation, vector shape validation, log redaction and local configuration mapping |
| Provider mapping | Added an explicit local loader mapping existing `MAYA_GENERATION_*` to backend `NESTLINE_GENERATION_*`; contradictory values cause a descriptive error |
| Local connection profile | Created ignored `.env.maya-local`; provider credentials remain in the original `.env`; hosted database password/access token are not inherited |
| Existing application | UI, migrations and application runtime behaviour were not changed; no Git commit/push or hosted database change |

The configuration helper is deliberately **not yet wired into the running product API**. It prepares one configuration path for the subsequent runtime integration. It must not be mistaken for completed dashboard/chat wiring.

## Initial provider tests — historical failures before the successful update above

The handoff authorises OpenAI project spending up to USD 30 and xAI up to USD 5 separately. This step reserved at most USD 0.03 for the first smoke sequence, then a separate USD 0.03 for the explicitly requested replacement-key sequence. Only the following requests were sent; both sequences stopped at their first error.

| Attempt | Operation | Result |
|---|---|---|
| First local key | OpenAI Responses, `gpt-5.4-mini` | HTTP **401**, `invalid_api_key` |
| After Kajal reported replacing the key | Same minimal OpenAI operation | HTTP **401**, `invalid_api_key` again |
| xAI generation | Not executed | First sequence stopped; after the edit, `XAI_API_KEY` was also absent |
| OpenAI embeddings | Not executed | Sequence stopped on authentication failure |
| Real-vector database round trip | Not executed | No real embedding was obtained |

Only a fixed, non-medical connection-check sentence was submitted. No user health details or source corpus text were sent. No provider response text, key value or raw authentication error body was printed.

The replacement key has the expected `sk-` prefix and no whitespace, obvious placeholder or `Bearer ` prefix. These format checks **do not establish validity**. OpenAI rejected it. This is different from the handoff's historical HTTP 429 quota error; we cannot infer the precise reason for the current invalid key.

No successful generation usage/cost was returned. Do not equate that with an independently verified account balance or billing total. The local ledgers retain reservations and errors; they do not monitor spending by other applications or Aswath's machine.

### Earlier requested action — OpenAI key replacement now completed successfully

1. Verify or create an active OpenAI API key in the intended project and copy its complete value securely.
2. Replace `OPENAI_API_KEY` in the repository's `.env`, not in a frontend file. Do not paste it into chat or commit it.
3. Confirm the update so a new bounded verification attempt can be explicitly authorised and recorded. Current one-time smoke ledgers intentionally prevent unattended retries.
4. xAI is optional for the first OpenAI-based implementation. Restore its key only if the team wants the separate comparison test. Missing xAI must not prevent testing a valid OpenAI key.

## Local Docker binding issue: stopped, data retained

We followed Supabase's documented custom-network setup using:

`com.docker.network.bridge.host_binding_ipv4=127.0.0.1`

The network option and container network membership were confirmed. Nevertheless, Docker reported the database/API/Studio published ports on `0.0.0.0` and `[::]`, not exclusively on loopback. The cause has **not** been established. Do not assert that these services are safely localhost-only merely because the CLI prints localhost URLs.

After schema verification, all **seven Maya containers were stopped**. Their containers and database/storage volumes were retained; no records or volumes were deleted. The unrelated n8n project was left untouched.

The setup script now verifies published bindings after startup and stops only this Maya stack if they are broader than loopback. Resolve the binding issue before leaving the services running or loading sensitive data. Do not disable this check or alter system-wide Docker/firewall settings without reviewing the scope.

The first SQL-test attempt also failed because the CLI looked for its default network despite startup using a custom one. Passing the same network explicitly to subsequent CLI commands fixed that: the complete rerun passed all 325 assertions. This was a test-runner configuration issue, not a failed SQL assertion.

## Where the evidence lives

All paths below are relative to this repository:

- `reports/local/supabase-kajal/source-manifest.json`: copied SQL hashes.
- `reports/local/supabase-kajal/start-redacted.log`: startup/migration log.
- `reports/local/supabase-kajal/test-redacted.log`: successful 325-assertion run.
- `reports/local/supabase-kajal/lint-redacted.log`: schema lint.
- `reports/local/provider-smoke/ledger.json`: first authentication failure.
- `reports/local/provider-smoke/ledger-after-key-replacement.json`: explicitly requested replacement-key failure.
- `.env.maya-local`: local-only setup profile; do not publish or print its contents.

Scripts added:

- `scripts/maya_local_database.py`: prepare/start/status/test/lint/profile/stop, scoped to this local project.
- `scripts/check_maya_paid_access.py`: fixed-input, one-time provider smoke sequence with durable reservations and no automatic retries.
- `app/services/local_backend_configuration.py`: explicit local settings mapping; not an alternate RAG implementation.
- `tests/test_maya_step2_setup.py`: setup/configuration/smoke-contract tests.

## What these results do not prove

- Knowledge chunks and content releases were still **zero** before shutdown. We have not imported, embedded or published the corpus.
- SQL tests use synthetic fixtures in transactions. Their success proves those database behaviours, not live model quality or clinical correctness.
- No real retrieval trace or provider-generated answer was obtained.
- No weekly KPI/FAQ tables were authored or switched on in this step.
- Existing source review statuses and Kajal's recorded decisions remain unchanged.
- The two older UI-restoration assertion failures recorded in Step 1 were not changed or retested away.

## Next sequence — resume, do not rebuild

1. **Completed:** resolved localhost binding and restarted the preserved local stack.
2. **Completed in the latest update:** verified the corrected OpenAI key with generation and a small embedding batch; retained usage and dimension results.
3. **Completed:** verified a real-vector write/query/rollback in this isolated database using non-medical synthetic text.
4. Implement the missing transactional corpus loader using existing source IDs, hashes, review records, release metadata and retrieval contracts. Preserve draft/public separation; no invented approvals.
5. Connect and test actual retrieval before connecting detailed dashboard guidance and Ask Maya.
6. In parallel with the knowledge work, build the agreed source-backed static weekly overview/FAQ tables; these cards do not require a live model call.

**Go:** continue local engineering with the preserved UI and existing architecture.  
**Not yet a go:** live grounded guidance, public release, or a claim that the application is fully integrated.

## Documentation consulted for this step

- [Supabase local development and loopback network guidance](https://supabase.com/docs/guides/local-development).
- [GPT-5.4 mini pricing and reasoning settings](https://developers.openai.com/api/docs/models/gpt-5.4-mini): USD 0.75 input / 4.50 output per million tokens at verification time.
- [OpenAI embedding model](https://developers.openai.com/api/docs/models/text-embedding-3-small): USD 0.02 per million input tokens at verification time.
- [xAI models and pricing](https://docs.x.ai/developers/models): Grok 4.6 USD 2 input / 6 output per million tokens at verification time.

Prices are a dated test-accounting reference, not a guarantee of future charges.
