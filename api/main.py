"""Ephemeral product API, isolated legacy fixtures and private grounded runtime.

Private development evidence is not a published clinical release. Real record
uploads and durable authenticated care records remain outside this surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import os
import secrets
from time import monotonic
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.schemas.foundation import SafetySpec
from app.schemas.onboarding import (
    ApproximateMonthTiming,
    DeliveryDateTiming,
    EstimatedDueDateTiming,
    ManualWeekDayTiming,
)
from app.schemas.orchestration import (
    AuthenticatedContextSnapshot,
    ContextItem,
    ContextKind,
    FactState,
)
from app.schemas.retrieval import JourneyPosition
from app.services.journey import JourneyResolutionError, JourneyResolver, SystemClock
from app.services.dashboard_content import released_weekly_cards
from app.services.dashboard_guidance import build_dashboard_guidance, journey_overview
from app.services.product_experience import run_compass
from app.services.product_runtime import ProductContext, ProductRuntimeUnavailable, get_product_runtime
from app.services.safety_gate import SafetyGate, build_safety_input
from scripts.validate_content import load_bundle


APP_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = APP_ROOT / "data" / "safety" / "rule_spec.yaml"
SAFETY_SPEC = SafetySpec.model_validate_json(SPEC_PATH.read_text(encoding="utf-8"))
SAFETY_GATE = SafetyGate(SAFETY_SPEC, mode="evaluation_only")
CONTENT_BUNDLE = load_bundle(APP_ROOT / "data")

COMPARISON_APPROVAL = {
    "approval_id": "KAJAL-STAGE-1-PRODUCT-REVIEW-2026-09-11",
    "approval_reviewer": "Kajal",
    "approval_capacity": "Product/content review",
    "approval_date": "2026-09-11",
    "catalogue_version": "1.0.0",
    "catalogue_sha256": "D3554DFE325FE3DEBF8A7FFF78A391BA262200F885B305C08946448697E247E8",
}


def _governed_card(card_id: str, domain: str, title: str, journey_scope: str, suggested_action: str) -> dict:
    return {
        "card_id": card_id,
        "domain": domain,
        "title": title,
        "summary": "Reviewed guidance for this section is awaiting specialist and release review.",
        "journey_scope": journey_scope,
        "evidence_ids": [],
        "review_state": "awaiting_specialist_review",
        "display_allowed": False,
        "limitations": [
            "No public weekly profile is released.",
            "The product structure is available; health claims remain hidden.",
        ],
        "source_links": [],
        "suggested_action": suggested_action,
    }


def _governed_cards(session: "DemoSession") -> list[dict]:
    scope = session.journey_label
    if session.journey.stage == "postpartum":
        cards = [
            _governed_card("pp-recovery", "recovery", "Recovery", scope, "Ask Maya about recovery"),
            _governed_card("pp-nourishment", "nutrition", "Nourishment", scope, "Build a nutrition plan"),
            _governed_card("pp-feeding", "feeding", "Feeding", scope, "Ask Maya a feeding question"),
            _governed_card("pp-wellbeing", "wellbeing", "Wellbeing", scope, "Build a wellbeing plan"),
            _governed_card("pp-documents", "documents", "Care records", scope, "Review sample record status"),
        ]
    else:
        cards = [
        _governed_card("preg-health", "health", "This week", scope, "Ask Maya a week-aware question"),
        _governed_card("preg-nutrition", "nutrition", "Nutrition", scope, "Build a nutrition plan"),
        _governed_card("preg-movement", "movement", "Movement", scope, "Build a movement plan"),
        _governed_card("preg-symptoms", "symptoms", "Symptoms", scope, "Describe a symptom to Maya"),
        _governed_card("preg-wellbeing", "wellbeing", "Wellbeing", scope, "Build a wellbeing plan"),
        _governed_card("preg-preparation", "preparation", "Preparation", scope, "Prepare questions for a visit"),
        _governed_card("preg-documents", "documents", "Care records", scope, "Review sample record status"),
        ]
    released = released_weekly_cards(CONTENT_BUNDLE, session.journey)
    released_domains = {card["domain"] for card in released}
    cards = [card for card in cards if card["domain"] not in released_domains]
    for card in cards:
        if card["domain"] == "nutrition" and (session.diets or session.allergies):
            inputs = []
            if session.diets:
                inputs.append("food preferences: " + ", ".join(session.diets))
            if session.allergies:
                inputs.append("ingredients to avoid: " + ", ".join(session.allergies))
            card["summary"] = (
                f"For {scope}, Maya recorded your {'; '.join(inputs)}. "
                "No reviewed weekly nutrition guidance has been released for this position."
            )
        elif card["domain"] == "movement" and session.symptoms:
            card["summary"] = (
                f"For {scope}, you reported {', '.join(session.symptoms)}. "
                "Maya will not treat this as exercise clearance; reviewed movement guidance is unavailable."
            )
        elif card["domain"] == "symptoms" and session.symptoms:
            card["summary"] = (
                f"You reported {', '.join(session.symptoms)} at {scope}. "
                "Maya has recorded this, not diagnosed it."
            )
        elif card["domain"] != "documents":
            card["summary"] = f"No released {card['domain']} guidance is available for {scope}."
    return [*released, *cards]


def _comparison_preview(session: "DemoSession") -> dict:
    journey = session.journey
    base = {
        **COMPARISON_APPROVAL,
        "review_state": "editorial_product_preview_only",
        "measurement_review_state": "pending",
        "image_ownership_or_licence": "pending",
        "exact_week": None,
        "range_start": journey.range_start,
        "range_end": journey.range_end,
        "eligible_context": False,
        "display_mode": "out_of_range",
        "limitations": [
            "Editorial comparison only; not a clinical growth assessment.",
            "Measurements, specialist review, localisation, and image licensing remain pending.",
        ],
    }
    if journey.stage == "postpartum":
        return {**base, "display_mode": "postpartum_hidden"}
    if journey.exact is None:
        return {**base, "display_mode": "range_confirmation"}
    if 1 <= journey.exact <= 41:
        return {**base, "eligible_context": True, "display_mode": "exact_week_editorial_preview", "exact_week": journey.exact}
    return base


class TimelineRequest(BaseModel):
    journey: Literal["pregnant", "postpartum"]
    timeline_mode: Literal["week", "month", "due", "birth_date"]
    timeline_value: str


ContextText = Annotated[str, Field(min_length=1, max_length=300)]


class OnboardingRequest(TimelineRequest):
    session_id: UUID | None = None
    name: str = Field(default="", max_length=80)
    diets: list[ContextText] = Field(default_factory=list, max_length=12)
    allergies: list[ContextText] = Field(default_factory=list, max_length=20)
    symptoms: list[ContextText] = Field(default_factory=list, max_length=12)
    restrictions: list[ContextText] = Field(default_factory=list, max_length=20)
    active_conditions: list[ContextText] = Field(default_factory=list, max_length=20)
    activity_background: str = Field(default="", max_length=500)
    use_fictional_sample_record: bool = False


class ChatRequest(BaseModel):
    session_id: UUID
    text: str = Field(min_length=1, max_length=2_000)


class PlanRequest(BaseModel):
    session_id: UUID
    horizon: Literal["day", "week"] = "week"
    focus: Literal["balanced", "nutrition", "movement", "wellbeing"] = "balanced"


class DemoSessionResponse(BaseModel):
    session_id: UUID
    mode: Literal["demo"] = "demo"
    fictional: Literal[True] = True


@dataclass
class DemoSession:
    session_id: UUID
    workspace_id: UUID
    owner_id: UUID
    name: str = ""
    state_version: int = 1
    journey: JourneyPosition = field(
        default_factory=lambda: JourneyPosition(stage="pregnancy", unit="week", exact=24)
    )
    journey_label: str = "Pregnancy week 24"
    timeline_source: str = "manual_week_day"
    diets: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    use_fictional_sample_record: bool = False
    product_session: bool = False
    context: AuthenticatedContextSnapshot | None = None
    access_token: str = field(default_factory=lambda: secrets.token_urlsafe(32), repr=False)
    expires_at: float = field(default_factory=lambda: monotonic() + 3600)
    restrictions: list[str] = field(default_factory=list)
    active_conditions: list[str] = field(default_factory=list)
    activity_background: str = ""
    history: list[tuple[str, str]] = field(default_factory=list)
    latest_plan: dict | None = None
    busy: bool = False


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, DemoSession] = {}
        self._lock = RLock()

    def create(self) -> DemoSession:
        with self._lock:
            self._sessions = {k:v for k,v in self._sessions.items() if v.expires_at > monotonic()}
            if len(self._sessions) >= 500:
                raise HTTPException(429, "Too many active sessions. Please try again later.")
            session_id, workspace_id, owner_id = uuid4(), uuid4(), uuid4()
            session = DemoSession(session_id, workspace_id, owner_id)
            self._sessions[session_id] = session
            return session

    def get(self, session_id: UUID) -> DemoSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.expires_at <= monotonic():
                self._sessions.pop(session_id, None)
                raise KeyError(session_id)
            return session


STORE = SessionStore()
app = FastAPI(
    title="Maya AI API",
    version="1.0.0",
    description="Session-based dashboard education, with separate legacy evaluation routes.",
)

allowed_origins = [
    value.strip()
    for value in os.environ.get(
        "MAYA_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5180,http://127.0.0.1:5180,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Maya-Operator"],
)


@app.middleware("http")
async def protect_ephemeral_sessions(request: Request, call_next):
    """No login, but a session ID alone must not grant access to health context."""
    if request.method != "OPTIONS" and request.url.path.startswith('/v1/'):
        origin = request.headers.get('origin')
        if origin and origin not in allowed_origins:
            return JSONResponse(status_code=403, content={'code':'origin_not_allowed','detail':'Origin not allowed.'})
        sid = None
        try:
            sid = UUID(request.url.path.rsplit('/',1)[-1])
        except ValueError:
            if request.method == 'POST':
                try:
                    data = await request.json()
                    if isinstance(data,dict) and data.get('session_id'):
                        sid = UUID(str(data['session_id']))
                except (ValueError, TypeError):
                    pass
        if sid:
            try:
                session = STORE.get(sid)
            except KeyError:
                session = None
            if session and session.product_session:
                token = request.cookies.get('maya_session', '')
                if not secrets.compare_digest(token, session.access_token):
                    return JSONResponse(status_code=403, content={'code':'session_access_denied','detail':'Start your own journey to access this session.'})
                if request.url.path.startswith('/v1/demo/'):
                    return JSONResponse(status_code=409, content={'code':'wrong_runtime_lane','detail':'Product sessions cannot use demo routes.'})
    response = await call_next(request)
    if request.url.path.startswith('/v1/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def _session_cookie(response: Response, session: DemoSession):
    response.set_cookie('maya_session', session.access_token, httponly=True,
        secure=os.environ.get('MAYA_SECURE_COOKIES') == 'true', samesite='strict',
        max_age=3600, path='/v1')


def _session(session_id: UUID) -> DemoSession:
    try:
        return STORE.get(session_id)
    except KeyError as exc:
        raise HTTPException(404, "Session not found. Please restart onboarding.") from exc


@app.exception_handler(ProductRuntimeUnavailable)
async def runtime_unavailable_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "detail": str(exc)})


def _product_context(session_id: UUID) -> ProductContext:
    session = _session(session_id)
    if not session.product_session:
        raise HTTPException(409, "Start a new journey before using the product endpoints.")
    if session.context is None:
        raise HTTPException(409, "Complete onboarding before using this feature.")
    return ProductContext(session.session_id, session.state_version,
        session.journey.model_copy(deep=True), session.journey_label,
        tuple(session.diets), tuple(session.allergies), tuple(session.symptoms),
        restrictions=tuple(session.restrictions),active_conditions=tuple(session.active_conditions),
        activity_background=session.activity_background,history=tuple(session.history))


@app.get("/v1/context/{session_id}")
def product_context(session_id: UUID) -> dict:
    context = _product_context(session_id)
    return {"session_id": context.session_id, "state_version": context.state_version,
        "journey": context.journey.model_dump(mode="json"),
        "journey_label": context.journey_label, "diets": context.diets,
        "allergies": context.allergies, "symptoms": context.symptoms,
        "origin": context.origin, "restrictions": context.restrictions,
        "active_conditions": context.active_conditions, "activity_background": context.activity_background}


def _run_product_turn(context, runtime, *, text=None, horizon=None, focus=None):
    with STORE._lock:
        session = _session(context.session_id)
        if session.busy:
            raise HTTPException(409, 'An answer is already being prepared for this session.')
        if session.state_version != context.state_version:
            raise HTTPException(409, 'Your details changed. Please retry using your updated context.')
        session.busy = True
    try:
        result = runtime.chat(context=context,text=text) if text is not None else runtime.plan(context=context,horizon=horizon,focus=focus)
        with STORE._lock:
            latest = _session(context.session_id)
            if latest.state_version != context.state_version:
                raise HTTPException(409, 'Your details changed while the answer was prepared. Please retry.')
            if result.get('display',{}).get('validation_display_allowed'):
                latest.history.extend([('user',text or f'Create a {horizon} {focus} plan'),
                    ('assistant',result['display'].get('summary','')[:4000])])
                latest.history = latest.history[-8:]
                if result.get('schedule'):
                    latest.latest_plan = result
        return result
    finally:
        with STORE._lock:
            session.busy = False


@app.post("/v1/chat")
def product_chat(payload: ChatRequest, runtime=Depends(get_product_runtime)) -> dict:
    context = _product_context(payload.session_id)
    if not payload.text.strip():
        raise HTTPException(422, "Enter a question for Maya.")
    gate = SAFETY_GATE.evaluate(build_safety_input(channel="chat_message", text=payload.text))
    if gate.route == "urgent":
        return {"mode": "session", "fictional": False, "display": {
            "route": "urgent", "title": "Get urgent help now",
            "summary": gate.fixed_message.text.replace("Compass", "Maya"), "provenance_sections": {},
            "citations": [], "uncertainties": [], "applied_constraints": [],
            "proposed_actions": [], "validation_display_allowed": True,
            "ordinary_generation_calls": 0, "trace_id": str(gate.trace.trace_id)}}
    return _run_product_turn(context,runtime,text=payload.text.strip())


@app.post("/v1/plan")
def product_plan(payload: PlanRequest, runtime=Depends(get_product_runtime)) -> dict:
    context = _product_context(payload.session_id)
    if any(check["route"] == "urgent" for check in _symptom_checks(list(context.symptoms))):
        raise HTTPException(409, "Please act on the urgent symptom advice before requesting an activity plan.")
    return _run_product_turn(context,runtime,horizon=payload.horizon,focus=payload.focus)


def _resolve_timeline(payload: TimelineRequest):
    today = SystemClock().today()
    resolver = JourneyResolver()
    if payload.journey == "postpartum":
        if payload.timeline_mode != "birth_date":
            raise JourneyResolutionError("postpartum onboarding requires a birth date")
        timing = DeliveryDateTiming(delivery_date=date.fromisoformat(payload.timeline_value))
    elif payload.timeline_mode == "week":
        timing = ManualWeekDayTiming(
            effective_date=today, gestational_week=int(payload.timeline_value), gestational_day=0,
        )
    elif payload.timeline_mode == "month":
        timing = ApproximateMonthTiming(
            effective_date=today, pregnancy_month=int(payload.timeline_value),
        )
    elif payload.timeline_mode == "due":
        timing = EstimatedDueDateTiming(
            effective_date=today,
            estimated_due_date=date.fromisoformat(payload.timeline_value),
        )
    else:
        raise JourneyResolutionError("pregnancy onboarding requires week, month, or due date")
    return resolver.resolve(timing)


def _journey_position(resolution) -> JourneyPosition:
    if resolution.stage == "pregnancy":
        if resolution.gestational_week is not None:
            return JourneyPosition(
                stage="pregnancy", unit="week", exact=resolution.gestational_week,
            )
        return JourneyPosition(
            stage="pregnancy", unit="week",
            range_start=resolution.approximate_week_min,
            range_end=resolution.approximate_week_max,
        )
    return JourneyPosition(
        stage="postpartum", unit="week", exact=resolution.postpartum_week,
    )


def context_item(item_id, kind, value, *, source_id=None, span=None, record_only=False,
                 state=FactState.CONFIRMED) -> ContextItem:
    return ContextItem(
        item_id=item_id, kind=kind, value=value, state=state,
        source_id=source_id, source_page=1 if source_id else None,
        exact_span=span, recorded_at=datetime.now(timezone.utc), record_only=record_only,
    )


def _context_for(session: DemoSession) -> AuthenticatedContextSnapshot:
    rows: list[ContextItem] = []
    for index, value in enumerate(session.diets):
        rows.append(context_item(f"diet-{index}", ContextKind.PREFERENCE, value))
    for index, value in enumerate(session.allergies):
        rows.append(context_item(f"allergy-{index}", ContextKind.ALLERGY, value))
    for index, value in enumerate(session.symptoms):
        rows.append(context_item(f"symptom-{index}", ContextKind.SYMPTOM, value, state=FactState.USER_REPORTED))
    if session.use_fictional_sample_record:
        rows.extend([
            context_item(
                "sample-supplement", ContextKind.SUPPLEMENT,
                {"name": "Fictional recorded supplement", "frequency": "daily", "timing": "08:00"},
                source_id="DEMO-DOC-001", span="Fictional sample: one recorded supplement daily",
                record_only=True,
            ),
            context_item(
                "sample-appointment", ContextKind.APPOINTMENT,
                {"day": "wednesday", "start": "10:00", "end": "11:00", "label": "Fictional check-up"},
            ),
        ])
    for day in (() if session.product_session else ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")):
        rows.append(context_item(
            f"availability-{day}", ContextKind.PREFERENCE,
            {"day": day, "start": "08:00", "end": "12:00"},
        ))
    return AuthenticatedContextSnapshot(
        workspace_id=session.workspace_id,
        care_episode_id=session.workspace_id,
        owner_user_id=session.owner_id,
        session_subject=session.owner_id,
        state_version=session.state_version,
        captured_at=datetime.now(timezone.utc),
        journey=session.journey,
        items=rows,
    )


def _symptom_checks(symptoms: list[str]) -> list[dict]:
    values = []
    for symptom in symptoms:
        gate_input = build_safety_input(channel="onboarding_symptom", text=symptom)
        result = SAFETY_GATE.evaluate(gate_input)
        values.append({
            "symptom": symptom,
            "route": result.route,
            "message": result.fixed_message.text if result.fixed_message else (
                result.clarification.question if result.clarification else "No urgent rule matched."
            ),
            "matched_rule_ids": [match.rule_id for match in result.matched_rules],
            "ordinary_generation_allowed": result.ordinary_generation_allowed,
            "trace_id": str(result.trace.trace_id),
            "stop_reason": result.trace.stop_reason,
        })
    return values


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok", "product": "Maya AI", "mode": "dashboard_education"}


@app.post("/v1/session")
def create_product_session(response: Response) -> dict:
    session = STORE.create()
    session.product_session = True
    _session_cookie(response,session)
    return {"session_id": session.session_id, "mode": "session", "fictional": False}


@app.get("/v1/session/{session_id}")
def validate_product_session(session_id: UUID) -> dict:
    session = _session(session_id)
    if not session.product_session:
        raise HTTPException(409, "Start a new product journey.")
    return {"session_id": session.session_id, "valid": True, "onboarding_complete": session.context is not None}


@app.post("/v1/timeline")
def preview_timeline(payload: TimelineRequest) -> dict:
    try:
        resolution = _resolve_timeline(payload)
        journey = _journey_position(resolution)
    except (ValueError, JourneyResolutionError) as exc:
        raise HTTPException(422, str(exc)) from exc
    label = f"Pregnancy week {journey.exact}" if journey.stage == "pregnancy" and journey.exact is not None else resolution.display_label
    return journey_overview(journey, label)


@app.post("/v1/onboarding")
def product_onboard(payload: OnboardingRequest, response: Response) -> dict:
    session = _session(payload.session_id) if payload.session_id else STORE.create()
    if payload.session_id and not session.product_session:
        raise HTTPException(409, "Demo sessions cannot become product sessions.")
    session.product_session = True
    _session_cookie(response,session)
    with STORE._lock:
        result = onboard(payload.model_copy(update={"session_id": session.session_id, "use_fictional_sample_record": False}))
        session.history.clear()
        session.latest_plan = None
    return {**result, "mode": "session", "fictional": False}


@app.get("/v1/home/{session_id}")
def product_home(session_id: UUID) -> dict:
    session = _session(session_id)
    if not session.product_session:
        raise HTTPException(409, "Start a new product journey.")
    if session.context is None:
        raise HTTPException(409, "Complete onboarding to open your dashboard.")
    if any(check["route"] == "urgent" for check in _symptom_checks(session.symptoms)):
        raise HTTPException(409, "Please act on the urgent symptom advice shown during onboarding.")
    response = home(session_id)
    guidance = build_dashboard_guidance(session.journey, session.journey_label,
        diets=session.diets, allergies=session.allergies, symptoms=session.symptoms, restrictions=session.restrictions)
    return {**response, "mode": "session", "fictional": False,
            "dashboard_guidance": guidance, "records": [],
            "kpis": {"care_records": 0, "upcoming_appointment": None, "plan_state": "created" if session.latest_plan else "not_created"}}


@app.get("/v1/plans/{session_id}")
def product_plans(session_id: UUID) -> dict:
    context = _product_context(session_id)
    return {"state_version":context.state_version,"plan":_session(session_id).latest_plan}


@app.post("/v1/demo/session", response_model=DemoSessionResponse)
def create_demo_session() -> DemoSessionResponse:
    session = STORE.create()
    return DemoSessionResponse(session_id=session.session_id)


@app.get("/v1/demo/session/{session_id}")
def validate_demo_session(session_id: UUID) -> dict:
    session = _session(session_id)
    return {
        "session_id": session.session_id,
        "valid": True,
        "onboarding_complete": session.context is not None,
        "mode": "demo",
        "fictional": True,
    }


@app.post("/v1/demo/onboarding")
def onboard(payload: OnboardingRequest) -> dict:
    session = _session(payload.session_id) if payload.session_id else STORE.create()
    if session.product_session and payload.use_fictional_sample_record:
        raise HTTPException(409, "Sample records cannot be added to a product session.")
    try:
        resolution = _resolve_timeline(payload)
    except (ValueError, JourneyResolutionError) as exc:
        raise HTTPException(422, str(exc)) from exc
    session.name = " ".join(payload.name.split())
    session.journey = _journey_position(resolution)
    # A week-only choice does not contain a meaningful day value; keep the
    # resolver's precise timing internally without displaying invented "day 0".
    session.journey_label = (
        f"Pregnancy week {session.journey.exact}"
        if session.journey.stage == "pregnancy" and session.journey.exact is not None
        else resolution.display_label
    )
    session.timeline_source = resolution.timing_source
    session.diets = sorted(set(payload.diets))
    session.allergies = sorted(set(payload.allergies))
    session.symptoms = sorted(set(payload.symptoms))
    session.restrictions = sorted(set(payload.restrictions))
    session.active_conditions = sorted(set(payload.active_conditions))
    session.activity_background = payload.activity_background.strip()
    session.state_version += 1
    session.use_fictional_sample_record = payload.use_fictional_sample_record
    session.context = _context_for(session)
    symptom_checks = _symptom_checks(session.symptoms)
    # A reported, nonurgent symptom can be retained without making the entire
    # dashboard a clarification dead-end. The Stage 6 gate still runs when a
    # user asks for symptom-specific guidance or a plan.
    safety_blocked = any(check["route"] == "urgent" for check in symptom_checks)
    return {
        "session_id": session.session_id,
        "name": session.name,
        "journey": session.journey.model_dump(mode="json"),
        "journey_label": session.journey_label,
        "timeline_source": session.timeline_source,
        "limitations": resolution.limitations,
        "symptom_checks": symptom_checks,
        "safety_blocked": safety_blocked,
        "symptom_guidance_limited": any(
            check["route"] == "needs_clarification" for check in symptom_checks
        ),
        "mode": "demo",
        "fictional": True,
    }


@app.get("/v1/demo/home/{session_id}")
def home(session_id: UUID) -> dict:
    session = _session(session_id)
    return {
        "name": session.name,
        "journey": session.journey.model_dump(mode="json"),
        "journey_label": session.journey_label,
        "confirmed_context": {
            "diets": session.diets,
            "allergies": session.allergies,
            "symptoms": session.symptoms,
            "diets_status": "confirmed" if session.diets else "not_provided",
            "allergies_status": "confirmed" if session.allergies else "not_provided",
            "symptoms_status": "reported" if session.symptoms else "not_provided",
        },
        "kpis": {
            "care_records": 1 if session.use_fictional_sample_record else 0,
            "upcoming_appointment": "Wednesday · 10:00" if session.use_fictional_sample_record else None,
            "plan_state": "not_created",
        },
        "content_cards": _governed_cards(session),
        "comparison_preview": _comparison_preview(session),
        "records": [{
            "document_id": "DEMO-DOC-001",
            "label": "Fictional sample care record",
            "status": "fictional_sample",
            "summary": "One fictional appointment and one record-only supplement are available.",
            "provenance": "Bundled synthetic Product Preview fixture",
        }] if session.use_fictional_sample_record else [{
            "document_id": "not-provided",
            "label": "No care record added",
            "status": "not_provided",
            "summary": "You can continue without a record and use general Product Preview features.",
            "provenance": "No document information was provided",
        }],
        "mode": "demo",
        "fictional": True,
        "record_context": "connected" if session.use_fictional_sample_record else "not_connected",
        "context_notice": (
            "A fictional sample care record is connected."
            if session.use_fictional_sample_record else
            "No care record is connected. Personalised answers remain limited; "
            "missing context must be requested or cause the flow to stop rather than guess."
        ),
        "public_release_available": False,
    }


@app.post("/v1/demo/chat")
def chat(payload: ChatRequest) -> dict:
    session = _session(payload.session_id)
    if session.product_session:
        raise HTTPException(409, "Product sessions cannot use demo answers. Use /v1/chat.")
    if session.context is None:
        raise HTTPException(409, "Complete onboarding before using Ask Maya.")
    execution = run_compass(payload.text, context=session.context)
    return {
        "display": execution.display.model_dump(mode="json"),
        "mode": "demo",
        "fictional": True,
        "record_context": "connected" if session.use_fictional_sample_record else "not_connected",
        "context_notice": (
            "A fictional sample care record is connected."
            if session.use_fictional_sample_record else
            "No care record is connected. This response cannot assume missing personal information."
        ),
    }


@app.post("/v1/demo/plan")
def plan(payload: PlanRequest) -> dict:
    session = _session(payload.session_id)
    if session.product_session:
        raise HTTPException(409, "Product sessions cannot use demo plans. Use /v1/plan.")
    if session.context is None:
        raise HTTPException(409, "Complete onboarding before creating a plan.")
    prompt = {
        "balanced": "Create a balanced weekly plan for nutrition, movement, wellbeing and follow-up.",
        "nutrition": "Create a weekly nutrition plan that respects all confirmed constraints.",
        "movement": "Create a weekly movement plan that respects all confirmed restrictions.",
        "wellbeing": "Create a weekly wellbeing plan with optional gentle activities.",
    }[payload.focus]
    execution = run_compass(prompt, horizon=payload.horizon, context=session.context)
    schedule = execution.stage7.proposed_schedule
    return {
        "display": execution.display.model_dump(mode="json"),
        "schedule": schedule.model_dump(mode="json") if schedule else None,
        "mode": "demo",
        "fictional": True,
        "save_available": bool(schedule and schedule.save_eligible),
    }


@app.post("/v1/demo/document-sample/{session_id}")
def enable_sample_document(session_id: UUID) -> dict:
    session = _session(session_id)
    if session.product_session:
        raise HTTPException(409, "Sample records cannot be added to a product session.")
    session.use_fictional_sample_record = True
    session.context = _context_for(session)
    return {
        "accepted": True,
        "document_id": "DEMO-DOC-001",
        "label": "Fictional sample record",
        "warning": "Real medical file upload is not enabled in Demo Mode.",
    }
