# Maya AI: fresh repository baseline

**18 September 2026 (India)**

New development home: [kajalchourasia-cmd/maya-ai](https://github.com/kajalchourasia-cmd/maya-ai).
Original collaboration: [kajalchourasia-cmd/nestline](https://github.com/kajalchourasia-cmd/nestline).

## What this baseline preserves

- The merged application baseline from original PRs #6 and #7, previously recorded as
  `b31fcff7d6c29bc1baa08fd3693e953a0bfaeaf4` in the original repository.
- Its source code, UI assets, backend, retrieval/orchestration,
  migrations, dependency locks, tests, documentation and final presentation artifacts.
- The original capstone deck/video and their historical Group 62 attribution.
- Existing source restrictions, review states and runtime boundaries.

## Fresh Git history, unchanged application

At Kajal's request, this repository begins with one parentless snapshot commit under her GitHub
identity. The earlier migration imported the old history; that 70-commit history was backed up
before replacement. It is not part of the new main branch's ancestry. The snapshot's date records
the import, not when all the original application code was written.

The source snapshot was `bc9a2f3addaf018dd122958124041761307c19ab`; only the README and transition/naming
notes changed for this fresh import. Application code, tests, assets and existing source notices
are unchanged. Original commit references in historical reports resolve through the original repository
or the owner's private Git bundle, not necessarily through the new repository.

The original repository is not deleted, rewritten or force-pushed. Historical PRs and discussions
stay there. Superseded and checkpoint branches must not be bulk-pushed or merged into the fresh history.

## Existing computer: no corpus migration or re-embedding

The existing `maya-ai-product-preview` working folder remains the application folder. Its private
configuration, source packages, cached embeddings, provider ledgers and local Supabase database remain
on this computer. No database reset, new embedding call, provider call or credential change is part
of moving the Git remote. The local runtime is not stored in GitHub.

The independent repository becomes the default `origin`. The old repository is retained as the
`legacy-nestline` remote for historical reference. These linked worktrees share Git remote configuration;
changing that configuration does not copy or alter their private data.

The running folder's earlier uncommitted work and the replaced history are preserved in separate
local-only checkpoints. Future changes should start from the fresh `maya-ai` main using feature
branches and PRs, not the historical collaboration branches.

## New computer: code plus private runtime

A clone brings the public project, not the populated database or keys. Use the owner's versioned,
encrypted complete-project ZIP and its separately stored key. Restore cached embeddings with their
matching evidence and model/dimensions instead of regenerating unchanged knowledge.

The refreshed September 17 archive contains the merged baseline used here. This transition adds
documentation only; it does not change the schema, evidence or vector compatibility of that snapshot.
Its newer `private-runtime/RECOVERY-CATALOGUE.json` must be used explicitly instead of the older
default catalogue in the repository. Follow the archive's README-FIRST.md and
[new-computer guide](MAYA-BACKUP-AND-NEW-COMPUTER-GUIDE.md).

The existing database preserves 194 evidence records and 194 vectors across two versions, with 98
records/vectors in the active version. Software dependencies and services still need installation;
provider credentials/billing must remain valid and authorized. Repository ownership does not transfer
a teammate's provider account or extend authorization to use it.

## Future development

1. Start each feature from the reviewed `maya-ai` main baseline.
2. Define the intended behavior and acceptance tests, then work on a dedicated branch.
3. Test the current onboarding, dashboard, retrieval, chat and plans for regressions.
4. Review the PR and its checks before merging. Do not reset the populated local database to satisfy CI.
5. Refresh the private recovery snapshot after relevant code, schema, corpus or ledger changes.

Human/doctor review and secure document intake remain proposed features, not functionality added by
this migration. The [current implementation guide](MAYA-CURRENT-PROJECT-STATUS.md) remains the feature-status reference.
