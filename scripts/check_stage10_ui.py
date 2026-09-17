"""Deterministic Stage 10 Streamlit action smoke check."""

from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _app(page: str) -> AppTest:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20)
    app.session_state["stage9_started"] = True
    app.session_state["stage9_mode"] = "Demo Mode"
    app.session_state["stage9_demo_page"] = page
    app.run()
    if app.exception:
        raise AssertionError(f"{page} failed: {app.exception}")
    return app


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def main() -> int:
    checks = 0

    plan = _app("Plan")
    _button(plan, "Build validated fictional week").click().run()
    _button(plan, "Explicitly review and save fictional plan").click().run()
    if not any("committed state version 5" in item.value for item in plan.success):
        raise AssertionError("plan commit result/version was not displayed")
    if not _button(plan, "Save plan by direct storage write (unavailable)").disabled:
        raise AssertionError("direct plan-table write was enabled")
    checks += 2

    records = _app("Records")
    _button(records, "Confirm fictional fact and show affected plan").click().run()
    if not any("Committed fictional fact at state version 4" in item.value for item in records.success):
        raise AssertionError("fact commit result/version was not displayed")
    if not any("dependent plan is stale" in item.value for item in records.warning):
        raise AssertionError("selective stale-plan result was not visible")
    checks += 2

    review = _app("Simulated review")
    _button(review, "Consent and queue fictional simulated review").click().run()
    if not any("Simulated review state: queued" in item.value for item in review.success):
        raise AssertionError("simulated review committed state was not displayed")
    if not any("ordinary generation calls: 0" in item.value for item in review.caption):
        raise AssertionError("urgent zero-generation proof was not visible")
    if not _button(review, "Submit review externally (unavailable)").disabled:
        raise AssertionError("external review submission was enabled")
    checks += 3

    print(json.dumps({
        "valid": True, "stage": 10, "checks": checks,
        "state_committer_actions": 3, "direct_table_writes": 0,
        "external_actions": 0, "urgent_generation_calls": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

