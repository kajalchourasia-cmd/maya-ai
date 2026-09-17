"""Connected fictional Stage 10 capstone flows.

These flows exercise the real typed State Committer boundary with deterministic
fixtures. They make no provider call, external transmission, or database edit and
are safe for local development and the visibly fictional Streamlit Demo Mode.
"""

from __future__ import annotations

from app.schemas.state_lifecycle import (
    CapstoneStoryResult, CommitStatus, PlanLifecycle, ReviewState,
)
from scripts.stage10_fixture_support import (
    fact_command,
    fixture_committer,
    follow_up_command,
    plan_create_command,
    plan_transition_command,
    review_create_command,
    review_transition_command,
    scope,
)


def run_capstone_story(story: str, run: int = 1) -> CapstoneStoryResult:
    """Run one isolated fictional story from a deterministic empty reset."""
    if story == "plan-save":
        return _plan_save(run)
    if story == "record-continuity":
        return _record_continuity(run)
    if story == "urgent-review":
        return _urgent_review(run)
    raise ValueError(f"unsupported Stage 10 capstone story: {story}")


def _plan_save(run: int) -> CapstoneStoryResult:
    service = fixture_committer()
    confirmed = service.commit(scope(), fact_command(key=f"story1-fact-{run:02d}-0001"))
    created = service.commit(
        scope(version=2), plan_create_command(version=2, key=f"story1-plan-{run:02d}-0001", edited=True),
    )
    plan_id = created.entity_ids[0]
    reviewed = service.commit(scope(version=3), plan_transition_command(
        plan_id, 3, "draft", "user_reviewed", key=f"story1-review-{run:02d}-01",
    ))
    saved = service.commit(scope(version=4), plan_transition_command(
        plan_id, 4, "user_reviewed", "saved", key=f"story1-save-{run:02d}-0001",
    ))
    snapshot = service.load_snapshot(scope(version=5))
    plan = snapshot.plans[0]
    passed = all(
        result.status == CommitStatus.COMMITTED
        for result in (confirmed, created, reviewed, saved)
    ) and plan["status"] == "saved" and plan["reviewed_at"] and plan["saved_at"]
    return CapstoneStoryResult(
        story="plan-save", run=run, passed=bool(passed), state_version=snapshot.state_version,
        committed_entity_ids=[*confirmed.entity_ids, *created.entity_ids],
        plan_status=PlanLifecycle.SAVED, fact_status="confirmed",
        causal_chain=["confirmed allergy", "validated plan item", "explicit user review", "saved plan"],
        limitation="Controlled fictional fixture; this is software-contract evidence, not clinical validation.",
    )


def _record_continuity(run: int) -> CapstoneStoryResult:
    service = fixture_committer()
    created = service.commit(
        scope(), plan_create_command(key=f"story2-plan-{run:02d}-0001"),
    )
    plan_id = created.entity_ids[0]
    confirmed = service.commit(
        scope(version=2), fact_command(version=2, key=f"story2-fact-{run:02d}-0001"),
    )
    follow_up = service.commit(
        scope(version=3), follow_up_command(3, key=f"story2-followup-{run:02d}"),
    )
    snapshot = service.load_snapshot(scope(version=4))
    plans = {item["id"]: item for item in snapshot.plans}
    passed = (
        confirmed.status == CommitStatus.COMMITTED
        and confirmed.affected_plan_ids == [plan_id]
        and plans[str(plan_id)]["status"] == "stale"
        and follow_up.status == CommitStatus.COMMITTED
        and len(snapshot.follow_up_tasks) == 1
    )
    return CapstoneStoryResult(
        story="record-continuity", run=run, passed=passed,
        state_version=snapshot.state_version,
        committed_entity_ids=[*created.entity_ids, *confirmed.entity_ids, *follow_up.entity_ids],
        plan_status=PlanLifecycle.STALE, fact_status="confirmed",
        causal_chain=[
            "fictional document span", "confirmed sesame allergy", "affected nutrition plan item",
            "stale plan", "confirmed in-app appointment question",
        ],
        limitation="The source upload is a pre-registered fictional fixture; production upload remains outside this stage.",
    )


def _urgent_review(run: int) -> CapstoneStoryResult:
    service = fixture_committer()
    offered = service.commit(
        scope(), review_create_command(1, urgent=True, key=f"story3-offer-{run:02d}-0001"),
    )
    case_id = offered.entity_ids[0]
    consented = service.commit(scope(version=2), review_transition_command(
        case_id, 2, "offered", "consented", key=f"story3-consent-{run:02d}-1",
    ))
    queued = service.commit(scope(version=3), review_transition_command(
        case_id, 3, "consented", "queued", key=f"story3-queue-{run:02d}-01",
    ))
    snapshot = service.load_snapshot(scope(version=4))
    review = snapshot.simulated_review_cases[0]
    passed = (
        offered.trace.generation_call_count == 0
        and offered.status == consented.status == queued.status == CommitStatus.COMMITTED
        and review["state"] == "queued"
        and review["label"] == "Simulated review"
        and review["immediate_safety_completed"]
    )
    return CapstoneStoryResult(
        story="urgent-review", run=run, passed=passed,
        state_version=snapshot.state_version,
        committed_entity_ids=[case_id], review_state=ReviewState.QUEUED,
        causal_chain=["curated red flag", "fixed immediate safety route", "explicit packet consent", "simulated queue"],
        limitation="No clinician is connected and no packet leaves the local fictional fixture.",
    )


def run_all_capstone_stories() -> list[CapstoneStoryResult]:
    return [run_capstone_story(story, run) for story in (
        "plan-save", "record-continuity", "urgent-review",
    ) for run in range(1, 4)]




