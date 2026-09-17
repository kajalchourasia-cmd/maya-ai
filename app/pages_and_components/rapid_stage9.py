"""Rapid functional Stage 9 surface over the accepted Stage 6-8 services.

This module owns presentation and session navigation only. Safety, routing,
retrieval, validation, and durable writes stay behind their existing boundaries.
"""

from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256

import streamlit as st

from app.pages_and_components import stage9 as legacy
from app.schemas.product_experience import PlanDisplayState, ProductMode
from app.services.product_experience import (
    ProductExecution,
    demo_weekly_home,
    reset_demo_state_keys,
    run_compass,
)


RAPID_PAGES = (
    "Dashboard",
    "Ask Maya",
    "Plan",
    "Records",
    "Evidence",
    "Simulated Review",
    "Evaluator",
)
DASHBOARD_TABS = (
    "Overview",
    "Nutrition",
    "Movement",
    "Well-being",
    "Symptoms & safety",
    "Guidance",
    "Records",
    "FAQs",
)
PROMPTS = (
    ("This week's focus", "What should I focus on this week?"),
    ("Nutrition plan", "Create my weekly nutrition plan."),
    ("Movement options", "What movement options respect my recorded restriction?"),
    ("Appointment questions", "Help me prepare questions for my next appointment."),
    ("Explain a record", "Explain a record I uploaded."),
    ("Tell Maya a symptom", "I want to tell Maya about a symptom."),
)


def _navigate(page: str) -> None:
    st.session_state.stage9_demo_page = page
    st.query_params["page"] = page


def _go(page: str, label: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        _navigate(page)
        st.rerun()


def _set_prompt(prompt: str) -> None:
    st.session_state.stage9_demo_query = prompt


def _open_maya_with(prompt: str) -> None:
    _set_prompt(prompt)
    _navigate("Ask Maya")


def render_landing() -> None:
    """Render the explicit Personal/Demo entry surface."""
    legacy._css()
    st.title("Nestline")
    st.subheader("A week-aware companion for pregnancy and early postpartum journeys.")
    st.write(
        "Nestline organises reviewed guidance, confirmed personal information, "
        "plans, records, and questions in one place."
    )
    st.info(
        "Nestline is an educational capstone and does not replace professional "
        "care. Demo Mode uses fictional data."
    )
    personal, demo = st.columns(2)
    with personal:
        if st.button(
            "Start my journey",
            type="primary",
            key="rapid_start_personal",
            use_container_width=True,
        ):
            st.session_state.stage9_started = True
            st.session_state.stage9_mode = ProductMode.PERSONAL.value
            st.query_params["mode"] = "personal"
            st.rerun()
    with demo:
        if st.button("Try fictional demo", key="rapid_start_demo", use_container_width=True):
            reset_demo_state_keys(st.session_state)
            st.session_state.stage9_started = True
            st.session_state.stage9_mode = ProductMode.DEMO.value
            st.session_state.stage9_demo_onboarding_confirmed = True
            st.session_state.stage9_demo_page = "Dashboard"
            st.query_params["mode"] = "demo"
            st.query_params["page"] = "Dashboard"
            st.rerun()


def _demo_timing_step() -> None:
    st.subheader("Timing")
    stage = st.session_state.get("stage9_demo_stage_choice", "I am pregnant")
    if stage == "I am pregnant":
        method = st.selectbox(
            "Timing method",
            [
                "Estimated due date — recommended",
                "Current gestational week and day",
                "Approximate pregnancy month",
            ],
            index=1,
            key="stage9_demo_timing_method",
        )
        if method.startswith("Estimated"):
            st.date_input(
                "Fictional estimated due date",
                value=date.today() + timedelta(days=112),
                key="stage9_demo_due_date",
            )
            st.info("The deterministic Journey Resolver calculates timing; a model is not used.")
        elif method.startswith("Current"):
            left, right = st.columns(2)
            left.number_input("Gestational week", 1, 42, 24, key="stage9_demo_week")
            right.number_input("Additional day", 0, 6, 0, key="stage9_demo_day")
            st.info("Preview: week 24, day 0 · second trimester · exact fictional timing")
        else:
            st.number_input("Approximate pregnancy month", 1, 9, 6, key="stage9_demo_month")
            st.info("Preview: approximate range only. Nestline does not invent an exact week.")
    elif stage == "I am postpartum":
        st.selectbox(
            "Timing method",
            ["Delivery date — recommended", "Current postpartum week and day"],
            key="stage9_demo_postpartum_method",
        )
        st.info("Preview: postpartum timing remains separate from pregnancy timing.")
    else:
        st.info("Preview: possible pregnancy · verification stage · no pregnancy week asserted.")


def _demo_context_step() -> None:
    st.subheader("Optional personal context")
    st.caption("Add anything Nestline should consider. You can skip this and update it later.")
    st.text_input("Dietary preference", value="Vegetarian (fictional)", key="stage9_demo_diet")
    st.text_area("Allergies", value="Peanut (fictional)", key="stage9_demo_allergies")
    st.text_area("Medical history or conditions", value="", key="stage9_demo_history")
    st.text_area("Dietary restrictions", value="", key="stage9_demo_diet_restrictions")
    st.text_area(
        "Movement restrictions",
        value="Avoid high-impact movement (fictional)",
        key="stage9_demo_movement",
    )
    symptom = st.text_area("Current symptom", value="", key="stage9_demo_symptom")
    st.checkbox("I have a next doctor's appointment", value=True, key="stage9_demo_has_appointment")
    st.date_input(
        "Appointment date",
        value=date.today() + timedelta(days=3),
        key="stage9_demo_appointment_date",
    )
    st.time_input("Appointment time", key="stage9_demo_appointment_time")
    st.text_input(
        "Appointment type",
        value="Routine follow-up (fictional)",
        key="stage9_demo_appointment_type",
    )
    st.text_input("Location", value="Fictional clinic", key="stage9_demo_appointment_location")
    if symptom.strip():
        safety = run_compass(symptom.strip())
        st.session_state.stage9_demo_onboarding_safety = safety
        if safety.display.route == "urgent":
            st.error(safety.display.summary)
            st.caption("Immediate fixed safety route · ordinary generation calls: 0")
        elif safety.display.route == "clarification":
            st.warning(safety.display.summary)


def _demo_review_step() -> None:
    st.subheader("Review and confirmation")
    stage = st.session_state.get("stage9_demo_stage_choice", "I am pregnant")
    st.write(f"**Name/workspace:** {st.session_state.get('stage9_demo_display_name', 'Maya · fictional')}")
    st.write(f"**Journey:** {stage}")
    if stage == "I am pregnant":
        st.write("**Resolved state:** pregnancy week 24, day 0 · second trimester · fictional fixture")
    elif stage == "I am postpartum":
        st.write("**Resolved state:** postpartum timing · fictional preview")
    else:
        st.write("**Resolved state:** possible pregnancy · no confirmed pregnancy statement")
    st.write(f"**Allergies:** {st.session_state.get('stage9_demo_allergies', 'None entered') or 'None entered'}")
    st.write(f"**Dietary preference:** {st.session_state.get('stage9_demo_diet', 'None entered') or 'None entered'}")
    st.write(f"**Movement restriction:** {st.session_state.get('stage9_demo_movement', 'None entered') or 'None entered'}")
    st.write("**Appointment:** fictional appointment shown only when entered")
    safety = st.session_state.get("stage9_demo_onboarding_safety")
    if safety is not None:
        st.write(f"**Symptom safety status:** {safety.display.route}")
    st.warning("Weekly content and clinical/localisation approval remain unavailable.")
    confirmed = st.checkbox(
        "I confirm this fictional timing and context for this isolated demo session.",
        key="stage9_demo_onboarding_confirmation",
    )
    if st.button(
        "Confirm and open dashboard",
        type="primary",
        disabled=not confirmed,
        key="stage9_demo_confirm_open",
    ):
        st.session_state.stage9_demo_onboarding_confirmed = True
        _navigate("Dashboard")
        st.rerun()
    if st.button("Back and edit", key="stage9_demo_review_back"):
        st.session_state.stage9_demo_onboarding_step = 4
        st.rerun()
    _go("Records", "Add a record or document (optional)", "stage9_demo_optional_record")


def _demo_onboarding() -> None:
    """Five visible, session-only steps for reviewing the fictional profile."""
    st.header("Onboarding")
    st.warning("FICTIONAL DEMO DATA · Viewing a step does not save anything.")
    step = min(max(int(st.session_state.get("stage9_demo_onboarding_step", 1)), 1), 5)
    st.progress(step / 5, text=f"Step {step} of 5")
    st.caption(f"Step {step} of 5")

    if step == 1:
        st.subheader("Basic identity")
        st.text_input(
            "Display name",
            value=st.session_state.get("stage9_demo_display_name", "Maya · fictional"),
            key="stage9_demo_display_name",
        )
        st.checkbox("Personal Mode confirmation", value=False, disabled=True)
        st.caption("This route is the isolated fictional demo. Personal Mode starts empty.")
    elif step == 2:
        st.subheader("Where are you right now?")
        st.radio(
            "Journey stage",
            ["I may be pregnant", "I am pregnant", "I am postpartum"],
            index=1,
            key="stage9_demo_stage_choice",
        )
        st.caption("Possible pregnancy is never presented as confirmed pregnancy.")
    elif step == 3:
        _demo_timing_step()
    elif step == 4:
        _demo_context_step()
    else:
        _demo_review_step()
        return

    left, right = st.columns(2)
    with left:
        if step > 1 and st.button("Back", key=f"stage9_demo_back_{step}", use_container_width=True):
            st.session_state.stage9_demo_onboarding_step = step - 1
            st.rerun()
    with right:
        safety = st.session_state.get("stage9_demo_onboarding_safety")
        blocked = step == 4 and safety is not None and safety.display.route == "urgent"
        if st.button(
            "Continue",
            type="primary",
            disabled=blocked,
            key=f"stage9_demo_next_{step}",
            use_container_width=True,
        ):
            st.session_state.stage9_demo_onboarding_step = step + 1
            st.rerun()


def _section(home, heading: str):
    return next((item for item in home.sections if item.heading == heading), None)


def _render_section(home, heading: str) -> None:
    section = _section(home, heading)
    if section is None:
        st.info("This section is unavailable.")
        return
    for item in section.items:
        st.write(f"- {item}")
    if section.state.value != "success":
        st.warning(f"Status: {section.state.value.replace('_', ' ')}")


def _prompt_button(label: str, prompt: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        _open_maya_with(prompt)
        st.rerun()


def _plan_button(label: str, variant: str, key: str) -> None:
    if st.button(label, key=key, use_container_width=True):
        st.session_state.stage9_demo_plan_variant = variant
        _navigate("Plan")
        st.rerun()


def _dashboard() -> None:
    execution = st.session_state.get("stage9_demo_plan_execution")
    committed = st.session_state.get("stage10_demo_plan_commit")
    plan_state = PlanDisplayState.SAVED if committed else (
        PlanDisplayState.DRAFT if execution else PlanDisplayState.NONE
    )
    home = demo_weekly_home(plan_state=plan_state)

    heading, action = st.columns([4, 1])
    with heading:
        st.header("Nestline dashboard")
        st.caption("Maya · fictional workspace · Pregnancy week 24 · state version 3")
    with action:
        _go("Ask Maya", "Ask Maya", "rapid_dashboard_maya")
    st.warning("FICTIONAL DEMO DATA · Controlled fixtures are pending content and clinical review.")

    first, second, third = st.columns(3)
    first.metric("Current journey", "Week 24, day 0")
    second.metric("Phase", "Second trimester")
    third.metric("Next milestone", "Wed · 10:00 appointment")
    st.caption("Journey progress · deterministic fictional fixture")
    st.progress(24 / 42, text="Second trimester highlighted · exact week fixture")

    tabs = st.tabs(DASHBOARD_TABS)
    with tabs[0]:
        with st.container(border=True):
            st.subheader("Your baby this week")
            st.info(
                "Weekly development and baby-size comparison unavailable: "
                "the repository has zero published weekly profiles."
            )
            st.caption("Fictional demo layout only — pending content review. No measurement is claimed.")
        st.subheader("Your confirmed information")
        for item in home.confirmed_context:
            st.write(f"- {item} · confirmed fictional fixture")
        st.write("**Next appointment:** Wednesday, 10:00–11:00 · fictional")
        if plan_state == PlanDisplayState.NONE:
            st.info("Plan status: none. Opening this dashboard generated no plan.")
        elif committed:
            st.success(f"Plan status: saved · committed version {committed.get('state_version', 'recorded')}")
        else:
            st.success("Plan status: validated proposal · not saved")
        st.subheader("Needs confirmation")
        for item in home.unresolved_items:
            st.warning(item)
    with tabs[1]:
        st.write("**Confirmed context:** peanut allergy; vegetarian preference in this fictional demo.")
        _render_section(home, "Nutrition focus")
        _prompt_button("Ask Maya about nutrition", "What should I focus on for nutrition this week?", "rapid_nutrition_ask")
        _plan_button("Create nutrition plan", "Nutrition only", "rapid_nutrition_plan")
    with tabs[2]:
        st.write("**Confirmed restriction:** avoid high-impact movement (fictional record).")
        _render_section(home, "Movement focus")
        st.warning("Nestline does not infer exercise clearance.")
        _prompt_button("Ask Maya about movement", "What movement options respect my recorded restriction?", "rapid_movement_ask")
        _plan_button("Create movement plan", "Movement only", "rapid_movement_plan")
    with tabs[3]:
        _render_section(home, "Well-being focus")
        st.info("Optional support only; this screen does not diagnose a condition.")
        _prompt_button("Ask Maya about well-being", "Show my wellbeing support plan", "rapid_wellbeing_ask")
    with tabs[4]:
        _render_section(home, "Reported symptoms")
        _prompt_button("Tell Maya about a symptom", "I want to tell Maya about a symptom.", "rapid_symptom_ask")
        st.warning("Routine symptom guidance remains unavailable pending qualified safety-policy review.")
    with tabs[5]:
        for label in ("Consider", "Avoid", "Ask first"):
            st.subheader(label)
            _render_section(home, label)
        st.subheader("Traditional practices / nuskhas")
        st.info("Insufficient evidence or uncertain. Ask an appropriate professional before use.")
    with tabs[6]:
        st.write("**User-reported:** fictional preferences and appointment context.")
        st.write("**Confirmed:** peanut allergy and movement restriction in the controlled fixture.")
        st.write("**Needs confirmation:** extracted candidates and conflicts remain separate.")
        st.write("**History:** superseded or rejected facts never personalize.")
        _go("Records", "Open records and provenance", "rapid_records_open")
    with tabs[7]:
        faqs = {
            "How does Nestline calculate my week?": "A deterministic Journey Resolver uses confirmed timing; a model does not calculate it.",
            "What is reported versus confirmed information?": "Reported information stays labelled. Only explicitly confirmed facts may personalize.",
            "Does Nestline replace my doctor?": "No. It is an educational and organizational capstone.",
            "Why is weekly information unavailable?": "No weekly profile has completed the required publication reviews.",
            "What is Fictional Demo Mode?": "An isolated, resettable set of synthetic data for testing.",
            "How are plans created and saved?": "A plan requires an explicit request, validation, review, and an authorized State Committer save.",
        }
        for question, answer in faqs.items():
            with st.expander(question):
                st.write(answer)

    st.caption(
        f"Dashboard load agent calls: {home.agent_fanout_count} · "
        "plan-composer calls: 0 · save calls: 0"
    )
    legacy._emergency_access()


def _render_result(execution: ProductExecution, index: int) -> None:
    legacy._render_chat_result(execution, prefix=f"rapid_chat_{index}")
    st.caption("Controlled fixture response · no live provider ran.")
    if execution.stage7.proposed_schedule is not None and execution.display.route == "validated":
        if st.button("Open Plan", key=f"rapid_open_plan_{index}"):
            st.session_state.stage9_demo_plan_execution = execution
            _navigate("Plan")
            st.rerun()


def _ask_maya() -> None:
    st.header("Ask Maya")
    st.caption("Every message runs through safety, routing, evidence, and validation before display.")
    st.warning("FICTIONAL DEMO DATA · Controlled fixture response; no live provider ran.")
    legacy._emergency_access()

    st.write("**Suggested questions**")
    columns = st.columns(2)
    for index, (label, prompt) in enumerate(PROMPTS):
        with columns[index % 2]:
            st.button(
                label,
                key=f"rapid_prompt_{index}",
                on_click=_set_prompt,
                args=(prompt,),
                use_container_width=True,
            )
    with st.form("rapid_maya_form", clear_on_submit=False):
        query = st.text_area(
            "Message Maya",
            placeholder="Choose a suggestion, then edit it. Use fictional information only.",
            key="stage9_demo_query",
            help="A suggestion fills this box; it never submits automatically.",
        )
        submitted = st.form_submit_button("Send to Maya", type="primary")
    if submitted:
        normalized = " ".join(query.split())
        if not normalized:
            st.session_state.stage9_demo_input_error = "Enter a fictional question before sending."
        else:
            fingerprint = sha256(normalized.encode("utf-8")).hexdigest()
            if st.session_state.get("stage9_demo_processing"):
                st.session_state.stage9_demo_input_error = "The current request is still processing."
            elif fingerprint == st.session_state.get("stage9_demo_last_submission"):
                st.session_state.stage9_demo_input_error = "Duplicate send prevented. Edit the message before sending again."
            else:
                st.session_state.stage9_demo_processing = True
                horizon = "week" if "week" in normalized.casefold() and "plan" in normalized.casefold() else "none"
                with st.spinner("Checking safety, evidence, and constraints…"):
                    result = run_compass(normalized, horizon=horizon)
                st.session_state.setdefault("stage9_demo_chat_history", []).extend([
                    {"role": "user", "text": normalized},
                    {"role": "assistant", "execution": result},
                ])
                st.session_state.stage9_demo_last_submission = fingerprint
                st.session_state.stage9_demo_processing = False
                st.session_state.pop("stage9_demo_input_error", None)

    if error := st.session_state.get("stage9_demo_input_error"):
        st.error(error)
    history = st.session_state.get("stage9_demo_chat_history", [])
    if not history:
        st.info("No messages yet. Suggestions only fill the editable input.")
    for index, message in enumerate(history):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["text"])
            else:
                _render_result(message["execution"], index)


def render_rapid_demo() -> None:
    """Render rapid Demo navigation and every functional product surface."""
    legacy._css()
    legacy._boundary_banner()
    legacy._demo_banner()

    aliases = {
        "Weekly Home": "Dashboard",
        "Compass": "Ask Maya",
        "Simulated review": "Simulated Review",
        "Evaluator view": "Evaluator",
    }
    requested_step = st.query_params.get("onboarding_step", "")
    if requested_step in {"1", "2", "3", "4", "5"}:
        st.session_state.stage9_demo_onboarding_step = int(requested_step)
    requested = st.query_params.get("page", "")
    current = requested or st.session_state.get("stage9_demo_page", "Dashboard")
    page = aliases.get(current, current)
    if page not in RAPID_PAGES and page != "Onboarding":
        page = "Dashboard"

    st.sidebar.markdown("### Nestline")
    st.sidebar.warning("FICTIONAL DEMO DATA")
    st.sidebar.caption("Journey: pregnancy week 24 · state v3")
    if st.sidebar.button("Ask Maya", type="primary", key="rapid_sidebar_maya", use_container_width=True):
        _navigate("Ask Maya")
        st.rerun()
    st.sidebar.caption("Navigate")
    for destination in RAPID_PAGES:
        if st.sidebar.button(
            destination,
            type="primary" if destination == page else "secondary",
            key=f"rapid_nav_{destination}",
            use_container_width=True,
        ):
            _navigate(destination)
            st.rerun()
    if st.sidebar.button("Review demo onboarding", key="rapid_nav_onboarding", use_container_width=True):
        st.session_state.stage9_demo_onboarding_step = 1
        _navigate("Onboarding")
        st.rerun()
    if st.sidebar.button("Reset fictional Demo Mode", key="rapid_reset_demo", use_container_width=True):
        reset_demo_state_keys(st.session_state)
        st.session_state.stage9_started = True
        st.session_state.stage9_mode = ProductMode.DEMO.value
        st.session_state.stage9_demo_onboarding_confirmed = True
        st.session_state.stage9_demo_page = "Dashboard"
        st.rerun()
    if st.sidebar.button("Return to landing", key="rapid_return_landing", use_container_width=True):
        reset_demo_state_keys(st.session_state)
        st.session_state.stage9_started = False
        st.rerun()
    st.sidebar.caption("Urgent safety access is available on every product page.")

    st.session_state.stage9_demo_page = page
    st.query_params["page"] = page
    if page == "Dashboard":
        _dashboard()
    elif page == "Ask Maya":
        _ask_maya()
    elif page == "Onboarding":
        _demo_onboarding()
    elif page == "Plan":
        legacy._plan()
    elif page == "Records":
        legacy._records()
    elif page == "Evidence":
        legacy._evidence()
    elif page == "Simulated Review":
        legacy._review()
    else:
        legacy._evaluator()
    if page not in {"Dashboard", "Ask Maya"}:
        legacy._emergency_access()
