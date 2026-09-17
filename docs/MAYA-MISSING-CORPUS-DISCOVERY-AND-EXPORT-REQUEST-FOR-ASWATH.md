# Maya AI — missing corpus discovery and export request

Date: 16 September 2026  
Sender: Aswath and his Codex  
Receiver: Kajal and her Codex

## 1. In simple words: what we need you to do

We received your first handoff successfully. However, it does not contain a populated knowledge database or real retrieval embeddings. Please check whether the fuller corpus exists in another project folder, Supabase instance, hosted project, or project backup on your system. If it exists, export the relevant project knowledge safely. If it does not, tell us exactly what exists and what still needs to be built.

**This task is discovery, export, and verification — not rebuilding the product.** Do not invent missing content, generate replacement embeddings, publish draft material, change safety policies, modify the UI, deploy, or push to GitHub. Do not simply send the same empty database again and call it complete.

“Export everything” here means all relevant, transferable **Maya public knowledge assets and their dependencies**, not your entire laptop, all Supabase data, user medical records, personal credentials, or unrelated projects.

## 2. What the first handoff actually contains

Package: `MAYA-CORPUS-HANDOFF-20260915T193957Z`.

The receiving-side review verified the ZIP checksum and all 330 entries in its file-checksum manifest. This establishes transfer integrity, not completeness of the original corpus. The following findings must be cross-checked, not treated as proof that the data never existed elsewhere.

| Item | Finding in the received package | What we need you to establish |
|---|---|---|
| Selected local database | Inventory identifies `supabase_db_nestline`, database `postgres`; all 10 allowlisted knowledge tables have zero rows. The supplied SQL contains no knowledge rows. | Was this the database actually used for the completed ingestion and retrieval runs? Where are the populated tables, if elsewhere? |
| Hosted database | Inventory reports zero rows visible through a publishable-key check. It explicitly says no administrator export was performed. | Inspect the correct hosted project with authorized database access. Application-key invisibility is not proof of absence. |
| Weekly profiles | 63 draft profiles, including 46 coverage shells. `P06`, `P07`, `P26`, and `P37` have empty content slots in the supplied files. | Are there richer versions or stage-level guidance elsewhere? Distinguish empty authoring slots from missing underlying evidence. |
| Guidance and citations | 56 guidance fragments and 55 evidence spans were supplied. | Are these the complete authored collection or only an initial subset? Where are the underlying source blocks and full extraction outputs? |
| Source inventory | 31 registry records: 26 candidate and 5 excluded. | Preserve source decisions and exclusions. Identify any additional legitimate source collections used by the actual pipeline. |
| Source snapshots | 22 selected-excerpt JSON snapshots, not full-document archives. | Supply available source originals and full extraction outputs where transfer is permitted, or document why each is unavailable. |
| Real vector index | No populated production retrieval index in this export. A separate fixture contains 20 records and 32-dimensional deterministic test vectors. | Locate genuine indexed chunks, embeddings, model identity, dimensions, and release linkage. Keep fixtures clearly separate. |
| Storage | Selected local inventory reports one bucket and zero objects. | Check whether public source files were stored elsewhere. Do not include private user-upload buckets. |
| Existing local authoring files | Weekly manifest, guidance fragments, source registry, and section manifest match files already on Kajal's computer. | Identify genuinely additional data rather than presenting these unchanged files as the missing full corpus. |
| Backend code | A snapshot/patch was supplied, including a signed-in workspace-oriented dashboard path. | Identify the actual retrieval entry point and required configuration. Code transfer alone does not prove the no-login UI is connected. |

The original report's successful empty-database restore is useful structural evidence. It is **not** evidence of a populated or useful retrieval system. We have not independently rerun its restore scripts on Kajal's machine.

## 3. First: locate the actual source of truth

Please perform a read-only investigation in the relevant Maya/Nestline project locations.

1. Identify the project checkout and exact commit used for the latest successful ingestion and real retrieval test. Include relevant uncommitted backend changes separately; exclude secrets.
2. Inspect project configuration locally to identify referenced database hosts, project identifiers, data directories, index stores, and release identifiers. Report non-secret identifiers only; do not print connection strings or key values.
3. List relevant running and stopped Supabase containers and associated project volumes. Do not delete, reset, prune, or modify them. If inspecting a stopped database requires starting it or restoring a backup, explain the specific target and obtain approval first.
4. Check other known Maya/Nestline clones and their configured local projects. Do not assume the newest folder or currently running container is the one used for ingestion.
5. Check any relevant hosted Supabase project using Aswath's authorized access. Distinguish database-admin counts from application-visible counts and explain any difference without weakening row-level security.
6. Look for project-owned raw downloads, parsed documents, ingestion outputs, JSONL datasets, vector files, release manifests, ingestion logs, and backups in the known project paths. Ask before expanding the search outside those locations.
7. Locate evidence of a real successful retrieval: query, selected release, returned chunk IDs, source citations, and index configuration. Remove private inputs and secrets from exported logs.

Return a location table with: non-secret location/project identifier, access method, knowledge row counts, release/status counts, source-file count, real embedding count, and conclusion. Label each location `FOUND`, `EMPTY`, `ACCESS BLOCKED`, or `NOT CHECKED`.

If the only existing data is the first handoff, say so clearly. An honest `NOT FOUND IN CHECKED LOCATIONS` is better than assuming a complete corpus exists.

## 4. What to export when you find it

| Asset | Required contents |
|---|---|
| Source catalogue | Source IDs, URLs/titles, applicable geography, pregnancy/postpartum and stage applicability, retrieval dates, licensing/transfer restrictions, review and exclusion status. |
| Original source files | Available PDFs/HTML/text and other public knowledge originals where redistribution is permitted. Preserve IDs, filenames, hashes and mappings. A selected excerpt must not be labelled a complete source document. |
| Parsed evidence | Full available extraction outputs, source blocks/chunks, page or section anchors, evidence spans, citations and source linkage. |
| Guidance and weekly material | Existing fragments, profiles, overlays, stage/topic mappings, measurement-source mappings, catalogues, FAQs and plan templates if present. Preserve their real draft/published states. |
| Actual embeddings | Stored vectors with their existing chunk IDs, model/provider, dimensions, text/preprocessing version, similarity/index settings and release membership. Mark unknown configuration as unknown; never infer the model from dimensions alone. |
| Release and review metadata | Existing releases, ingestion runs, decision records and provenance needed to understand eligibility. Exclude or redact personal details while preserving necessary relationships. |
| Schema and runtime dependencies | Exact migrations, required extensions/versions, retrieval functions, relevant indexes/RLS definitions, dependency versions, configuration variable names and a secret-free example file. |
| Code needed to use the data | Existing ingestion/retrieval entry points, commands and relevant uncommitted backend changes. Do not replace Kajal's frontend or growth-image library. |
| External files/storage | Downloaded public knowledge objects plus an object-to-source manifest; database rows alone are not the files. |

For each item, state `EXPORTED`, `ALREADY IN FIRST HANDOFF`, `NOT FOUND`, `ACCESS BLOCKED`, or `EXCLUDED WITH REASON`.

Start with the previous database allowlist, then inspect whether legitimate additional public-knowledge dependencies exist:

```text
public.content_releases
public.public_sources
public.source_artifacts
public.source_blocks
public.ingestion_runs
public.evidence_review_tasks
public.evidence_review_decisions
public.weekly_profiles
public.guidance_fragments
public.guideline_chunks
```

The schema name `public` does not mean its rows are non-private. Check actual columns, ownership and relationships before exporting. Do not export auth users, sessions, prescriptions, private uploads, chats, personal profiles, workspace data or secrets. Workspace-linked graph tables remain excluded unless a separately verified public-only subset can be safely extracted with its dependencies. Document any excluded dependency that prevents a complete restore.

## 5. Supabase export: recommended approach

**Yes, Supabase PostgreSQL data can be exported. The important questions are whether the data exists, whether the selected project is correct, and whether Aswath has authorized access.**

### A. Correct local Supabase database is available

1. Confirm the exact container/project, PostgreSQL version, installed vector extension and permitted tables.
2. Record source counts, status counts, chunk-to-source linkage and real embedding dimensions before export. Verify candidate tables do not contain private records.
3. Use PostgreSQL logical export tooling with an explicit table allowlist. Have Codex generate the exact command for the verified local container and schema; do not paste a guessed container command.
4. Prefer an allowlisted data export alongside the project's exact migrations. Include required functions/extensions and an explicit restore order; selected-table dumps do not automatically include every dependency.
5. Use the export tool's output-file option or a verified binary-safe transfer path, especially for custom-format archives on Windows. Preserve vector values, UUIDs, JSON and Unicode without spreadsheet conversions.
6. Keep drafts as drafts. Exporting a permitted draft is not the same as releasing it to users. Do not change source data or disable RLS to make an export appear populated.

PostgreSQL documents the supported export formats, table selection and dependency limitations in [pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html). Use a compatible installed client and capture actual command results, not a hand-written success summary.

### B. The populated database is on hosted Supabase

1. Aswath opens the correct Supabase project and uses its **Connect** panel to obtain database connection details locally.
2. Use a direct database connection where supported; if the local network requires IPv4, check the documented session-pooler alternative. Do not guess hosts, ports or project IDs.
3. Authenticate locally with authorized credentials. Prefer a local protected password mechanism or interactive prompt; never paste passwords into this MD, chat, generated logs or the ZIP.
4. Perform the same scoped inventory and logical export as above. The frontend publishable key is not a substitute for database export access.
5. If connection or permission fails, report the exact sanitized error and the minimum manual action needed. Do not reset passwords or change project settings without approval.

Connection guidance: [Supabase — connect to your database](https://supabase.com/docs/guides/database/connecting-to-postgres).

### C. Source files are in Supabase Storage

Export permitted public knowledge objects separately, preserving their source mappings and checksums. Do not assume a database backup includes their contents: [Supabase's backup documentation](https://supabase.com/docs/guides/platform/backups) explicitly distinguishes database data from Storage objects.

## 6. If a normal database export is not possible

| Situation | What to do | What to tell Kajal |
|---|---|---|
| Wrong project or missing permission | Ask Aswath to select the correct project or provide authorized local database access. Continue gathering non-secret files meanwhile. | Exact project/access action needed; do not call it missing data yet. |
| Database unavailable but complete source/chunk/vector files exist | Export those files with their schema, IDs, types and existing loader commands. Verify a reconstruction path in isolation if authorized. | Which parts can be restored exactly and which cannot. |
| Only an authorized API can read the records | Export all permitted pages with stable IDs, explicit row-count reconciliation and typed serialization. Report RLS visibility limits. | This is only complete if access and pagination coverage are proven. |
| Only manual table CSV export is available | Treat it as a partial fallback. Include schema/type information and verify multiline text, JSON, vectors and row counts. | CSV alone does not reproduce policies, functions, storage or a working retrieval service. |
| Originals exist but chunks/embeddings do not | Transfer originals and existing ingestion configuration. | Re-ingestion/indexing will be a separate implementation task; do not perform paid embedding generation now. |
| Only drafts, shells and test fixtures exist | Return them with accurate labels and a content-gap inventory. | There is no additional real retrieval corpus to copy from the checked locations. |
| A source cannot legally be redistributed | Include its URL, identifier, restriction and existing acquisition instructions, not an unauthorized copy. | Kajal may need to obtain it separately; do not quietly substitute another source. |

Do not send a complete Docker volume or unrestricted Supabase backup as a workaround. Those can contain private data and credentials unrelated to the knowledge transfer.

## 7. Check whether the data supports our intended screens

Inventory existing evidence for these areas; **do not write new recommendations to fill gaps in this task**.

| Product area | Evidence/assets we expect you to locate |
|---|---|
| Timeline and growth | Journey rules and existing week/measurement/source mappings. Preserve Kajal's current UI library; identify discrepancies rather than overwrite it. |
| Nutrition | Applicable pregnancy/postpartum and trimester guidance, nutrients, food options, dietary preferences, allergies, symptom adaptations, food safety and cautions. |
| Movement | Stage applicability, aerobic/strength/mobility/pelvic-floor guidance where available, restrictions, symptom adaptations and stop/escalation advice. |
| Symptoms | Evidence for reported symptoms, comfort measures, uncertainty and urgency routing. |
| Wellbeing | Supportive content, check-ins and help-seeking information; no assumed emotional state based only on week. |
| FAQs and do's/don'ts | Existing questions/answers or evidence from which the system can generate them, with applicability and citations. |
| Chat and requested plans | Real retrieval configuration, specialist/plan contracts, supporting evidence and constraints; not scripted fixture replies. |

Provide a category-by-stage coverage table: early/mid/late pregnancy and postpartum, source IDs, evidence count, status, missing coverage and location. Common guidance can legitimately apply across several weeks. We do not need 42 artificially different recommendations, but empty week shells must not be mistaken for full coverage.

## 8. Verify the handoff before sending it

1. Create a new uniquely named output folder; retain the first package unchanged. State whether the new ZIP is self-contained or an addendum requiring the first ZIP.
2. Include a machine-readable inventory of files, table counts, status counts, chunk/vector counts, model metadata and exclusions. Compare export counts to source counts from a consistent snapshot where feasible; explain changes if the source was being written concurrently.
3. Include a SHA-256 manifest for payload files, then create the final ZIP and a separate ZIP checksum. Do not change the ZIP after calculating its checksum.
4. Check that no `.env` secrets, credentials, private records or sensitive logs are included. `.env.example` should contain placeholders only.
5. Inspect generated SQL/scripts before running them. Restore only into a separately approved, newly created disposable target with explicit target validation, not the source or Kajal's working database. Do not run cleanup against an unresolved path/container.
6. If you perform the rehearsal, report actual commands, sanitized output, restored counts, vector dimensions and reference checks. If you cannot rehearse, mark it `NOT RUN`; do not construct passing results.
7. If a genuine retrieval index exists, verify representative searches return relevant source-linked passages for nutrition, movement and postpartum. Distinguish retrieval-only testing from model-generated answers. Do not consume paid provider usage without approval.
8. Supply receiver instructions using verified paths and versions. Preserve existing records and embeddings; any unavoidable format conversion must be documented and validated.

## 9. Final response required from Aswath's Codex

Create `ASWATH-CORPUS-DISCOVERY-RESPONSE.md` with:

- **Verdict:** complete transferable corpus found / partial corpus found / access blocked / no additional corpus found in inspected locations.
- Exactly where the actual data was found and why the first export was empty or incomplete, if the cause can be established.
- A checklist of what was checked and what was not checked.
- An exported-assets table and a precise missing-assets table, including any excluded or unavailable dependencies.
- Whether real embeddings already exist; their verified model, dimensions and release mapping, or explicitly unknown fields.
- Coverage findings for each product category and stage.
- What can work after import versus what still requires ingestion, configuration or runtime integration.
- Any authentication/workspace assumptions that differ from Kajal's fresh-session, no-visible-login product flow. Do not bypass privacy protections to resolve them during export.
- Exact package path, checksum, restore instructions and real verification results.
- A short list of manual actions Aswath must perform, if any.

**A successful file transfer or restore is not a GO verdict for live product readiness.** We still need to connect and test the actual dashboard/chat runtime on Kajal's computer.

## 10. Manual steps for Aswath and Kajal

### Aswath — only if Codex requests help

1. Open the project folder that actually ran ingestion, not merely a similarly named clone.
2. If the source is local, open Docker Desktop and identify the relevant existing Supabase project. Let Codex inspect before starting or changing anything.
3. If the source is hosted, sign in to Supabase yourself, select the correct project, and make its connection details available locally. Do not send your account login, password, service key or database credentials in chat or the handoff ZIP.
4. Approve the specifically scoped knowledge export and, if needed, a separate disposable restore test. No production reset is necessary.
5. Send Kajal the final ZIP, checksum and discovery response through a private file-transfer channel. If nothing additional exists, send the honest response instead of another misleading “complete corpus” ZIP.

### Kajal — after receiving the response

1. Send Aswath this one MD file now; no database expertise is required on your side for discovery.
2. Save the returned files in a new subfolder under `C:\Users\Hrishikesh\Developer\Maya-Handoff-Inbox`. The Windows account path is still `Hrishikesh`; the receiving person is Kajal.
3. Share the paths with your local Codex. Do not run sender scripts, overwrite `.env`, replace the UI or restore over an existing database yourself.
4. We will verify the archive, compare the data, and identify an isolated restore target before importing anything.
5. Model/API credentials, if needed later, must be configured separately on the backend. Copying the corpus does not transfer account access or guarantee that a generation provider is working.

This request ends at a verified handoff and a clear list of remaining dependencies. UI implementation, content creation, live chat wiring, GitHub handoff and deployment are separate tasks.
