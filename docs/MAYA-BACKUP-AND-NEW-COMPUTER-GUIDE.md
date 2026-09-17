# Maya: preserve the project and move to another computer

## The rule

Keep the public code reproducible and the private runtime recoverable. A GitHub clone alone
is not a populated database. An ignored file is not a backed-up file. A backup on the same
physical computer does not protect against loss of that computer.

This document contains no credentials, private corpus bodies, vectors or database records.

## What lives where

| Material | Primary home | Recovery copy |
|---|---|---|
| Code, UI assets, static dashboard catalogue, migrations, dependency locks, tests, documentation | This GitHub repository | Private package includes source snapshot and Git bundle |
| Source catalogue, checksums and safe engineering/review reports | GitHub after content/privacy review | Matching version in the private package |
| Supplied corpus, selected source text, chunks, applicability metadata and actual embeddings | Operator's private project data and local database | Versioned encrypted recovery package |
| Current database, roles and permissions | Running PostgreSQL/Supabase instance | Logical dump plus role export; verify by isolated restore |
| Provider and embedding spending ledgers, local receipts and runtime configuration | Private runtime directory | Preserve in the same recovery version; do not reset ledgers |
| Provider credentials and recovery key | Secure private configuration / separate key storage | Separate secure backup; never public Git |
| Installed libraries and running processes | Each computer's environment | Reinstall from pinned files; restart services, not old PIDs |

Corpus text and embeddings are not inherently secret. A reviewed, permitted, sanitized dataset
can be published separately. The existing mixed recovery package has NOT been approved for public
redistribution and contains credentials. Do not upload it to the public repository, even though encrypted.
Do not infer publication permission from a passing checksum, a development-index approval or a private repo.

## Current recovery point: 17 September 2026

Use `data/recovery/private-runtime-20260917.json` to identify the matching private package.
Its filename, encrypted SHA-256, size and source-code commit are pinned there.

- Current PostgreSQL dump and role export are included, not just old pre-import dumps.
- 194 evidence rows and 194 vectors represent TWO versions: 96 earlier and 98 active.
- The active vector cache uses text-embedding-3-small, 1536 dimensions.
- 1,177 payload files were verified. The package includes source handoffs, configurations,
  cached real vectors, ledgers, recordings under local reports, Git history and a code snapshot.
- An isolated, network-disabled database restore passed. Restored evidence/vector/batch
  fingerprints matched the original; vector search and private table access restrictions passed.
- Storage contained zero objects at this snapshot. A later snapshot with Storage objects
  needs a separate file export as well as the database dump.
- The working database and existing app checkout were not modified by the recovery exercise.
- A complete app setup on another computer has NOT yet passed. This is not clinical approval,
  a public deployment or proof that future/unimplemented features exist.

The private package's `START-HERE.md` identifies the recovery key location. The key is NOT in
the archive and must be preserved separately. Losing both access to the original data and the key
would make this encrypted backup unusable.

## Finish protecting this recovery point

1. Keep the working project and Docker data intact.
2. Copy ONLY the prepared `TRANSFER-TO-NEW-PC` folder to a private external drive or private
   cloud folder under an account the owner controls. Do not use public/link-wide sharing.
3. Keep the separate recovery key in a password manager or another independent secure location.
   Do not put it next to the archive in the same shared folder. Check account recovery access.
4. Verify the COPIED/downloaded archive, not merely the source copy, with the command below.
   Then verify authentication using the supplied opening tool and key.
5. For stronger protection, retain both an off-device/cloud copy and an independent offline copy.
   Keep dated versions: syncing a deletion is not the same as retaining a backup.
6. Record which private destination holds the package and when it was verified. Keep that private.
   Nothing in this repository claims that an off-device copy has already been made.

```powershell
python -m scripts.check_maya_recovery --archive "PATH-TO-COPIED-BACKUP.maya"
```

This is a read-only SHA-256/size check with no network, no paid provider call and no output of contents.
The supplied Node opening tool additionally authenticates/decrypts with the separately kept key.
After decryption and extraction into a NEW PRIVATE folder:

```powershell
python -m scripts.check_maya_recovery --payload "PATH-TO-EXTRACTED-PAYLOAD"
```

The payload checker verifies every file against MANIFEST.json, rejects unsafe paths/symlinks,
and rejects missing/extra/tampered files. Authenticate the encrypted archive FIRST: a standalone
manifest does not authenticate itself. The checker does not restore, publish, approve or execute data.

## New-computer checklist

1. Clone the integration branch until it is merged; otherwise use the reviewed merged release.
   The catalogue pins the code snapshot included in this recovery point. Later code changes
   require a compatibility/migration check rather than an assumption that an old backup still fits.
2. Obtain the exact private package and its key separately. Verify, authenticate, decrypt and
   check the manifest. Keep the original backup unchanged.
3. Install Python 3.12, Node.js >=22.13 (CI uses 24), Git and Docker Desktop. Install Python
   dependencies from requirements-dev.txt, root tooling with pnpm 11.19.0 / frozen lockfile,
   and frontend dependencies with npm ci. Internet access is required for dependencies/images;
   this is not an offline installer.
4. Follow the package's RECOVERY-GUIDE.md to create a fresh dedicated local database and
   restore its dump, roles and permissions. Do not reset or overwrite any existing populated database.
   Match the recorded PostgreSQL image and examine locale/configuration compatibility.
   The verified isolated procedure used the original supabase_admin bootstrap identity;
   restoring role grants through a different bootstrap role can fail on PostgreSQL 17.
5. Restore the private runtime files into their corresponding new checkout paths. Configure
   backend credentials privately. Retain the active admission packet, caches and budget ledgers.
   Validate before using caches; do not re-embed unchanged data merely because the laptop changed.
6. Recreate the required Supabase services and loopback-only networking with the existing project
   tooling. The database dump is not a substitute for service configuration. Do not reuse old PIDs
   or blindly copy machine-specific absolute paths. Do not change integrity checks to fit a broken restore.
7. Start the existing local UI/API launcher as documented in README. Check dashboard, onboarding,
   a sourced retrieval, chat follow-ups, allergy constraints and a plan using a synthetic profile.
   Live answers still need valid credentials, provider availability and authorized budget.
8. Confirm session isolation and private table access. Run repository checks and document skips/failures.
9. Only retire the old computer after the new computer passes these checks and the off-device
   archive/key are verified. Restoring the database is proven; this final whole-app check is still pending.

## Keep backups current

After a corpus import, new embeddings, schema change, significant code release or important ledger update,
take a NEW dated snapshot. Preserve the previous known-good one. Record the code commit, active packet,
source hashes, embedding model/dimensions, migration state, object count, ledger state and restore result.
Pause app writes for a coordinated snapshot of database plus file-based runtime state.
Never silently regenerate missing material or overwrite earlier recovery history.

Update the safe catalogue only after verifying the corresponding private archive. A catalogue does not
upload a backup and an uploaded archive does not prove it can be restored. Periodically rehearse recovery.
No recurring backup automation is configured by this documentation.
