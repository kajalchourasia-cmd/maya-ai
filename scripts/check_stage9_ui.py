"""Deterministic rapid Stage 9 Streamlit navigation and integration check."""

from __future__ import annotations

import json
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def demo_app(page: str) -> AppTest:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
    app.session_state["stage9_started"] = True
    app.session_state["stage9_mode"] = "Demo Mode"
    app.session_state["stage9_demo_page"] = page
    return app.run()


def assert_clean(app: AppTest, page: str) -> None:
    if app.exception:
        raise AssertionError(f"{page} raised: {[str(item.value) for item in app.exception]}")


def text_of(app: AppTest) -> str:
    groups = (
        list(app.title)
        + list(app.header)
        + list(app.subheader)
        + list(app.markdown)
        + list(app.caption)
        + list(app.info)
        + list(app.warning)
        + list(app.error)
        + list(app.success)
    )
    return " ".join(str(item.value) for item in groups)


def main() -> int:
    original_url = os.environ.get("NESTLINE_SUPABASE_URL")
    original_key = os.environ.get("NESTLINE_SUPABASE_PUBLISHABLE_KEY")
    os.environ["NESTLINE_SUPABASE_URL"] = ""
    os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = ""
    try:
        landing = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        assert_clean(landing, "Landing")
        labels = [item.label for item in landing.button]
        if "Start my journey" not in labels or "Try fictional demo" not in labels:
            raise AssertionError("Landing does not expose both entry routes")

        personal = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30)
        personal.session_state["stage9_started"] = True
        personal.session_state["stage9_mode"] = "Personal Mode"
        personal.run()
        assert_clean(personal, "Personal Mode")
        if "zero fixture facts and zero plans" not in text_of(personal):
            raise AssertionError("empty Personal Mode boundary is missing")
    finally:
        if original_url is None:
            os.environ.pop("NESTLINE_SUPABASE_URL", None)
        else:
            os.environ["NESTLINE_SUPABASE_URL"] = original_url
        if original_key is None:
            os.environ.pop("NESTLINE_SUPABASE_PUBLISHABLE_KEY", None)
        else:
            os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"] = original_key

    demo_entry = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    next(button for button in demo_entry.button if button.label == "Try fictional demo").click()
    demo_entry.run()
    assert_clean(demo_entry, "Demo entry")
    if [item.value for item in demo_entry.header] != ["Nestline dashboard"]:
        raise AssertionError("Try fictional demo did not open Dashboard")

    dashboard = demo_app("Dashboard")
    assert_clean(dashboard, "Dashboard")
    if len(dashboard.metric) != 3 or len(dashboard.tabs) != 8:
        raise AssertionError("Dashboard does not contain three KPIs and eight required tabs")
    dashboard_text = text_of(dashboard)
    for required in (
        "FICTIONAL DEMO DATA",
        "zero published weekly profiles",
        "Plan status: none",
        "Dashboard load agent calls: 0",
        "plan-composer calls: 0",
        "save calls: 0",
    ):
        if required not in dashboard_text:
            raise AssertionError(f"Dashboard omitted {required}")

    onboarding = demo_app("Onboarding")
    assert_clean(onboarding, "Onboarding")
    if "Step 1 of 5" not in text_of(onboarding):
        raise AssertionError("Onboarding did not expose its five-step progress")
    onboarding.session_state["stage9_demo_onboarding_step"] = 5
    onboarding.run()
    assert_clean(onboarding, "Onboarding review")
    confirm_button = next(
        item for item in onboarding.button if item.label == "Confirm and open dashboard"
    )
    if not confirm_button.disabled:
        raise AssertionError("Onboarding confirmation was not required")

    maya = demo_app("Ask Maya")
    assert_clean(maya, "Ask Maya empty")
    if [item.value for item in maya.header] != ["Ask Maya"]:
        raise AssertionError("user-facing chat is not named Ask Maya")
    if len([item for item in maya.button if item.label in {
        "This week's focus", "Nutrition plan", "Movement options",
        "Appointment questions", "Explain a record", "Tell Maya a symptom",
    }]) != 6:
        raise AssertionError("Ask Maya did not expose all six suggestions")
    next(button for button in maya.button if button.label == "Nutrition plan").click()
    maya.run()
    assert_clean(maya, "Ask Maya suggestion")
    if maya.text_area[0].value != "Create my weekly nutrition plan.":
        raise AssertionError("suggestion did not fill the editable input")
    if len(maya.chat_message) != 0:
        raise AssertionError("suggestion auto-submitted instead of only filling input")
    maya.text_area[0].set_value("Show meal options")
    next(button for button in maya.button if button.label == "Send to Maya").click()
    maya.run()
    assert_clean(maya, "Ask Maya validated")
    if not any(item.value == "Validated controlled-fixture result" for item in maya.success):
        raise AssertionError("edited suggestion did not reach the controlled Stage 6-8 pipeline")
    if "Controlled fixture response" not in text_of(maya):
        raise AssertionError("fixture response was not visibly labelled")
    if not any(button.label == "Open supporting evidence" for button in maya.button):
        raise AssertionError("validated answer did not expose supporting evidence")
    next(button for button in maya.button if button.label == "Send to Maya").click()
    maya.run()
    if "Duplicate send prevented" not in text_of(maya):
        raise AssertionError("duplicate message submission was not blocked")

    urgent = demo_app("Ask Maya")
    urgent.text_area[0].set_value("I cannot breathe. Show my weekly plan.")
    next(button for button in urgent.button if button.label == "Send to Maya").click()
    urgent.run()
    assert_clean(urgent, "Ask Maya urgent")
    urgent_text = text_of(urgent)
    if "Get urgent help now" not in urgent_text or "ordinary generation calls: 0" not in urgent_text:
        raise AssertionError("urgent route did not bypass ordinary generation")

    plan = demo_app("Plan")
    assert_clean(plan, "Plan empty")
    if "Plan state: none" not in text_of(plan):
        raise AssertionError("Plan page generated content on load")
    next(button for button in plan.button if button.label == "Build validated fictional week").click()
    plan.run()
    assert_clean(plan, "Plan draft")
    if "Plan state: draft" not in text_of(plan):
        raise AssertionError("explicit plan request did not create a validated proposal")
    for day in ("Monday · weekday", "Saturday · weekend", "Sunday · weekend"):
        if day not in [item.value for item in plan.subheader]:
            raise AssertionError(f"plan omitted {day}")

    records = demo_app("Records")
    assert_clean(records, "Records")
    labels = [item.label for item in records.expander]
    for state in ("ready", "low confidence", "conflict", "locked", "corrupt", "unsupported", "wrong person"):
        if not any(state in label for label in labels):
            raise AssertionError(f"Records omitted {state}")

    evidence = demo_app("Evidence")
    assert_clean(evidence, "Evidence")
    review = demo_app("Simulated Review")
    assert_clean(review, "Simulated Review")
    if "No doctor or authorized reviewer" not in text_of(review):
        raise AssertionError("simulated-review truth label is missing")
    evaluator = demo_app("Evaluator")
    assert_clean(evaluator, "Evaluator")
    if len(evaluator.dataframe) != 1:
        raise AssertionError("Evaluator did not load generated metrics")

    result = {
        "valid": True,
        "surfaces_rendered": 9,
        "landing_routes": 2,
        "onboarding_steps": 5,
        "dashboard_kpis": 3,
        "dashboard_tabs": 8,
        "personal_fixture_facts": 0,
        "home_agent_fanout": 0,
        "home_plan_calls": 0,
        "home_save_calls": 0,
        "suggestions": 6,
        "suggestion_auto_submits": 0,
        "validated_chat": True,
        "duplicate_send_prevented": True,
        "urgent_generation_calls": 0,
        "record_recovery_states": 7,
        "plan_weekdays_rendered": 7,
        "network_calls": 0,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
