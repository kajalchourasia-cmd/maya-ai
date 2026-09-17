# Maya — verified progress, next milestone and Aswath availability checklist

Prepared for Kajal on 16 September 2026.

**Verdict: GO for the next local engineering milestone. Not a GO for a completed live-RAG product or public deployment.**

The local foundation is working. The application knowledge connection is still work to do. This distinction is essential: a working model key and vector database are necessary, but do not prove the dashboard or chatbot retrieves medical evidence correctly.

## 1. What was cross-verified

| Check | Result | What this establishes |
|---|---|---|
| Local services, checked again at 08:49 UTC | All seven Maya containers running; health checks healthy where present; Auth, REST and Studio HTTP 200 | Local infrastructure is available; published ports bind only to localhost |
| Migration replay | 17 migrations present | The local schema includes the supplied Stage 5 and Stage 10 changes |
| SQL regression suite, rerun | 325 assertions across eight files passed | Existing SQL contracts and security tests pass; not proof of populated-corpus retrieval |
| Selected Python regression suite, rerun | 64 passed, **2 failed**, 1 warning | Do not describe the entire test suite as green |
| Real-vector database round trip, rerun | Saved real OpenAI vectors, 1,536 dimensions; expected ranking; database cosine agrees with independent calculation | Real vectors can be stored and searched locally; this used non-medical test sentences, not Maya's corpus |
| Round-trip cleanup | Temporary table removed; real knowledge chunks and content releases both still zero | The verification did not create a published corpus |
| OpenAI provider evidence inspected | Successful generation and embedding calls recorded at 08:25 UTC | The replacement key worked for both operations then; no extra paid requests made in this recheck |
| Three supplied ZIP hashes | All match the handoff's full SHA-256 values | The original packages are present and unchanged |
| Extracted payload hashes, rerun | Package A: 330/330; B: 137/137; C: 45/45 | Every manifest-listed payload matched; this does not establish clinical accuracy, completeness, or permission to publish |

The two Python failures were already present in the Step 1 baseline. They concern an older growth measurement helper name (`generalWeekMeasurementReferences`, replaced in the current UI by `getGrowthMeasurements`) and an older “Product review pending” display expectation. Reconcile the assertions with the approved UI while preserving source/provenance protections. Do not merely delete them or weaken checks to obtain a green result.

This turn did not rerun every frontend/browser test, perform full user-journey testing, or test deployment. Earlier frontend checks must not be represented as fresh end-to-end verification.

Evidence is in `reports/local/supabase-kajal/`, `reports/local/provider-smoke/`, and `docs/MAYA-IMPLEMENTATION-STEP-2-LOCAL-INFRASTRUCTURE.md`. These local reports are not a public-product certification.

## 2. What is still missing

1. **Corpus loader:** a transactional, repeat-safe import into the existing Supabase schema. Preserve source, block and evidence IDs, hashes, applicability and review history. The existing file-export publisher is not this database loader.
2. **Knowledge population and embeddings:** the actual knowledge tables remain empty. Provider smoke-test vectors are not corpus embeddings.
3. **Source coverage and review:** the supplied handoff reports 72 retained governed blocks, 55 review-required candidates and missing historical source captures. It does not contain a complete, published, clinically reviewed knowledge library. Existing product/content decisions must be preserved, not mistaken for all review roles.
4. **Real retrieval trace:** prove a real question returns the right eligible source passages and citations through the existing retrieval gateway. Verify stage, jurisdiction, status and user-isolation exclusions before ranking.
5. **Runtime integration:** connect the existing backend configuration, retrieval, generation and validation to ordinary dashboard/chat endpoints. No hidden fixture fallback. The current configuration helper alone does not activate this path.
6. **Static weekly catalogue:** complete sourced, versioned Journey/Nutrition focus/Energy focus/Movement focus cards and standard FAQs. These are deterministic lookups, not per-visit LLM calls. Reuse stage-wide guidance where appropriate rather than inventing differences every week.
7. **Dashboard categories:** nutrition and movement first, then symptoms, wellbeing and do's/don'ts. Use the same current onboarding context; no invented symptoms or dietary preferences.
8. **Ask Maya and requested plans:** session context, grounded answers, citations, follow-ups, requested weekly plans, revisions and stale-plan handling still need connected end-to-end verification.
9. **Final UI and operational tests:** correct loading/errors/retries, session isolation, privacy, accessibility, frontend regression reconciliation and hosted deployment verification remain.

Document upload and user-facing login remain excluded by Kajal's current scope. Supabase Auth being available locally does not change that product decision.

## 3. The next milestone and its acceptance criteria

**Next: implement and prove the corpus loader locally, before claiming that the UI is using RAG.**

1. Use the checksum-verified packages and the current repository contracts. Inventory exact sources, candidates, review decisions and missing links; do not overwrite the UI with a historical code snapshot.
2. Implement a dry-run/preflight report and a separate explicit local import. Fail clearly on broken references, incompatible schema, conflicting IDs or invalid hashes.
3. Test the loader with controlled synthetic records: repeated import creates no duplicates; an intentional mid-import failure rolls back completely; conflicting records do not silently overwrite existing ones.
4. Preserve original draft/review-required status. Do not change historical dry runs to successful published runs. Isolate controlled development material from ordinary public retrieval.
5. Generate real embeddings only for a clearly defined eligible engineering/source set within the authorized budget and usage restrictions. Record model, dimensions, text hash and version. Do not mix fixture and real vectors or models.
6. Verify actual source-bearing retrieval through the appropriate existing database/gateway path, and separately verify that drafts remain excluded from the public lane. A controlled development retrieval is not a published health-guidance release.
7. Record counts, tests, failures, source IDs and remaining review blockers in an MD report. Then connect the dashboard and chat in the agreed sequence.

Missing clinical/licensing/localisation decisions require the appropriate review owners. They are not solved by another API key, and this coding work must not fabricate them. Ordinary technical failures should be shown as technical failures, not generic medical “needs confirmation” messages.

## 4. Do we need more keys?

| Access | Needed now? | What Kajal should secure |
|---|---|---|
| OpenAI generation and embeddings | Already verified with the replacement key | Continued authorized access to its actual project, working billing/credit, project identification and an owner who can resolve quota or revoke/replace the key. A key alone does not grant billing administration |
| Local Supabase/Docker | Already available | No hosted Supabase account, hosted service-role secret or teammate laptop needed for the next local milestone |
| xAI | No, optional comparison/fallback only | Request access only if the team still wants to evaluate it. Current OpenAI-first work is not blocked by its absence |
| LangSmith | No, optional external tracing | Only needed if enabling that service; use redacted traces and the correct project access |
| Document extraction/storage scanning | No | Upload is outside this phase; do not gather unrelated secrets now |
| GitHub | Not needed to execute local code; needed for later team delivery | Confirm Kajal has repository collaboration rights through her own account; retain exact repo/branch/commit references |
| Hosted Supabase | Needed only if chosen for deployment | Invite Kajal to the intended project with the appropriate role. Record project identity and prepare server-side connection/admin access securely. Do not migrate hosted data during local setup |
| Render/Vercel or another host | Needed later for deployment | Team/project invitation and GitHub integration rights for the selected frontend/backend hosts; domain/DNS access only if using a custom domain |

**Do not send account passwords, 2FA codes, API keys or a filled `.env` through this chat, an MD file or GitHub.** Use an agreed secure secret manager/transfer channel. Keep provider and administrative database secrets on the backend, never in frontend `VITE_*` variables.

The handoff records OpenAI USD 30 maximum and xAI USD 5 maximum, separately, until revoked by Aswath. Confirm whether the replacement key belongs to that same authorized project and whether other work shares those budgets. The local smoke ledger does not measure all spending in someone else's account, and an account alert is not an application-enforced hard spending cap.

## 5. Ask Aswath for this before he becomes unavailable

Copy-paste:

> Our local Supabase setup and OpenAI generation/embedding smoke tests now work. We have verified all three handoff ZIPs and their manifest-listed files; please do not resend everything or regenerate the corpus.
>
> Before you become unavailable, please confirm:
> 1. Which project/account owns our latest working OpenAI key; continued permission to use it; remaining project budget; and how Kajal can manage or obtain help with quota, billing or key replacement. Please invite her own account where appropriate rather than share your password.
> 2. Whether any source/backend changes or review decisions were created after the final handoff. If yes, transfer only those deltas with their paths, commit references and checksums.
> 3. Where the original source files excluded from the packages are located, with complete hashes and the reason for exclusion. Transfer only material permitted for this use; otherwise provide canonical acquisition links and the applicable restrictions. Do not claim missing historical captures exist.
> 4. Who owns the outstanding licence, clinical and India-localisation decisions, and whether any new decisions have been recorded. Preserve Kajal's existing valid content/product approvals.
> 5. Confirm Kajal's GitHub collaboration access. If your hosted Supabase/Render/Vercel projects will be used for deployment, provide project invitations and non-secret project identifiers now, with required secrets through our secure channel only. Do not reset, migrate or deploy anything as part of this request.
>
> If any item is unavailable, say exactly which one, why, and whether we can obtain an equivalent independently. We do not need remote control of your laptop for the next local implementation step.

## 6. What to back up on Kajal's computer

- The three original ZIPs, full SHA-256 files/manifests, final operational handoff, source inventories and review decisions. Keep an additional trusted copy outside this laptop if available.
- The **current** source tree, including uncommitted UI/backend changes, new scripts, assets, dependency lockfiles, product specification and verification reports. The existing Step 1 checkpoint predates Step 2 work; it is not a current complete source backup.
- Credentials separately in an encrypted secret store, not inside the ordinary source archive. Retain a secret-free configuration template and setup instructions with the code.
- Once the corpus is populated, an independent database export plus a restore check. Preserve any permitted raw-source files/storage assets separately; database rows do not automatically include their binaries.
- The local setup/start instructions and container configuration records. The stopped `-before-loopback` containers share original volumes: **they are not independent database backups and must not be started alongside their replacements.** Do not prune Docker volumes.

This checklist does not claim these new backup copies or account invitations have already been created.

## Bottom line

We can continue on Kajal's computer without Aswath's laptop and without another key for the current local implementation. Secure account continuity, source/review ownership and later deployment access now. The next deliverable is a verified populated knowledge path, not another visual redesign or a claim that the full product is already complete.
