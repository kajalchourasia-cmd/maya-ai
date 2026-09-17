# Historical report index

Reports in this repository preserve the truth at the commit and branch named inside each file. Statements such as “not pushed,” “not merged,” “Stage 6 is next,” or lower migration/test counts are historical pre-merge snapshots; they are not current-state claims and are not rewritten after the fact.

For the current Maya UI/runtime and final submission, start with [current project status](MAYA-CURRENT-PROJECT-STATUS.md),
[the integration record](MAYA-RELEASE-INTEGRATION-20260917.md) and [final deliverables](FINAL-DELIVERABLES.md).
The older `NESTLINE-CURRENT-STATUS.md`, capability/evaluation manifests and consolidated final report describe
their own earlier integration scope. The Stage 5–10 handoff files remain useful implementation evidence,
while `NESTLINE-STAGES-5-TO-10-FINAL-INTEGRATED-VERIFICATION.md` records the integration preceding merged PR #4.
Stage 0–4 reports likewise remain stage-specific historical evidence.

When counts differ, use the canonical generated manifest for the current denominator and retain the old count as evidence from its original run. When code behaviour differs, rerun the current checker against the current commit rather than assuming an older GO still applies.
