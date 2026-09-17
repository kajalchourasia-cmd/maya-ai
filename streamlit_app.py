"""Nestline Streamlit entry point for the rapid integrated experience."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from app.pages_and_components.onboarding import render_onboarding
from app.pages_and_components.rapid_stage9 import render_landing, render_rapid_demo
from app.schemas.foundation import SafetySpec
from app.schemas.product_experience import ProductMode
from app.services.product_experience import (
    load_runtime_config,
    personal_empty_home,
    reset_demo_state_keys,
)


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

st.set_page_config(
    page_title="Nestline · Ask Maya",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

requested_mode = st.query_params.get("mode", "").casefold()
if requested_mode in {"personal", "demo"}:
    st.session_state.stage9_started = True
    st.session_state.stage9_mode = (
        ProductMode.DEMO.value
        if requested_mode == "demo"
        else ProductMode.PERSONAL.value
    )

if not st.session_state.get("stage9_started", False):
    render_landing()
    st.stop()

mode = st.session_state.get("stage9_mode", ProductMode.PERSONAL.value)
previous_mode = st.session_state.get("stage9_previous_mode")
if previous_mode == ProductMode.DEMO.value and mode == ProductMode.PERSONAL.value:
    reset_demo_state_keys(st.session_state)
st.session_state.stage9_previous_mode = mode
st.query_params["mode"] = "demo" if mode == ProductMode.DEMO.value else "personal"

if mode == ProductMode.DEMO.value:
    render_rapid_demo()
else:
    st.title("Nestline Compass")
    st.warning("Development privacy boundary: use fictional information only.")
    st.subheader("Start my journey")
    st.info(
        "Personal Mode starts empty. Demo fixtures are never copied into this "
        "mode or another workspace."
    )
    config = load_runtime_config()
    if not config.personal_mode_available:
        home = personal_empty_home()
        st.info(home.hero_body)
        st.error(
            "Personal Mode configuration is incomplete. Missing: "
            + ", ".join(config.missing_fields)
            + ". Copy .env.example to .env, fill only the public Supabase URL "
            "and publishable key, then restart Streamlit."
        )
        st.caption("Your Personal workspace contains zero fixture facts and zero plans.")
        if st.button("Return to landing", key="rapid_personal_return"):
            st.session_state.stage9_started = False
            st.rerun()
    else:
        safety_spec = SafetySpec.model_validate_json(
            (ROOT / "data/safety/rule_spec.yaml").read_text(encoding="utf-8")
        )
        render_onboarding(
            os.environ["NESTLINE_SUPABASE_URL"].strip(),
            os.environ["NESTLINE_SUPABASE_PUBLISHABLE_KEY"].strip(),
            safety_spec,
        )
