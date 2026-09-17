"""Run versioned non-UI cross-stage journeys using only fictional/redacted data."""
from __future__ import annotations
import json
from pathlib import Path
from uuid import UUID
from app.schemas.integration import OnboardingState, ProviderAvailability, RuntimeGateInput, RuntimeOperation
from app.schemas.orchestration import ContextOrigin, RuntimeMode
from app.services.capstone_flows import run_all_capstone_stories
from app.services.integration_gate import assess_runtime
from app.services.product_experience import run_compass
from scripts.stage10_fixture_support import fact_command, fixture_committer, scope
from scripts.stage7_fixture_support import make_context
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/STAGES-0-8-10-SERVICE-JOURNEY-RESULTS.json"
BASE="796c05cd29a055188e86685990078709fca0bfbc"
def compass_case(case_id,text,expected,horizon="none"):
 value=run_compass(text,horizon=horizon)
 evidence=[] if value.stage8 is None else list(value.stage8.validation_report.trace.evidence_ids)
 passed=value.display.route==expected and (value.display.ordinary_generation_calls==0 if expected in {"urgent","clarification"} else True)
 return {"case_id":case_id,"passed":passed,"expected_route":expected,"observed_route":value.display.route,"ordinary_generation_calls":value.display.ordinary_generation_calls,"evidence_ids":evidence,"provider_models":[f"{w.trace.provider}/{w.trace.model}" for w in value.stage7.worker_results],"validation_display_allowed":value.display.validation_display_allowed,"state_version":(value.stage7.proposed_schedule.state_version if value.stage7.proposed_schedule is not None else 3),"trace_id":value.display.trace_id}
def main():
 cases=[
  compass_case("supported-fixture-nutrition","Show me fictional nutrition options","validated"),
  compass_case("urgent-zero-generation","I have heavy bleeding; make a meal plan too","urgent"),
  compass_case("ambiguous-symptom","I feel dizzy","clarification"),
  compass_case("diagnosis-conservative-stop","Predict a diagnosis for me","clarification"),
  compass_case("unsupported-non-health","Open the billing settings","unsupported"),
 ]
 context=make_context()
 personal_unavailable=assess_runtime(RuntimeGateInput(mode=RuntimeMode.PERSONAL,operation=RuntimeOperation.ORCHESTRATION,query="Create a plan",session_subject=context.session_subject,context=context.model_copy(update={"context_origin":ContextOrigin.AUTHENTICATED_STORE}),context_origin=ContextOrigin.AUTHENTICATED_STORE,onboarding_state=OnboardingState.CONFIRMED,explicit_user_action=True,provider_availability=ProviderAvailability.UNAVAILABLE,requires_personalization=True))
 cases.append({"case_id":"personal-provider-unavailable","passed":not personal_unavailable.proceed and personal_unavailable.stop_code.value=="provider_unavailable","expected_route":"provider_unavailable","observed_route":personal_unavailable.stop_code.value,"ordinary_generation_calls":0,"evidence_ids":[],"provider_models":[],"validation_display_allowed":False,"state_version":context.state_version,"trace_id":None})
 other=UUID("79999999-9999-4999-8999-999999999999")
 cross=assess_runtime(RuntimeGateInput(mode=RuntimeMode.PERSONAL,operation=RuntimeOperation.RETRIEVAL,query="Show records",session_subject=other,context=context.model_copy(update={"context_origin":ContextOrigin.AUTHENTICATED_STORE}),context_origin=ContextOrigin.AUTHENTICATED_STORE,onboarding_state=OnboardingState.CONFIRMED,explicit_user_action=True,provider_availability=ProviderAvailability.CONFIGURED,requires_personalization=True))
 cases.append({"case_id":"cross-user-denial","passed":not cross.proceed and cross.stop_code.value=="mode_scope_mismatch","expected_route":"mode_scope_mismatch","observed_route":cross.stop_code.value,"ordinary_generation_calls":0,"evidence_ids":[],"provider_models":[],"validation_display_allowed":False,"state_version":context.state_version,"trace_id":None})
 committer=fixture_committer(); first=committer.commit(scope(),fact_command()); stale=committer.commit(scope(),fact_command(key="stale-second-0001"))
 cases.append({"case_id":"concurrent-stale-write","passed":first.status.value=="committed" and stale.status.value=="stale","expected_route":"stale","observed_route":stale.status.value,"ordinary_generation_calls":0,"evidence_ids":[],"provider_models":[],"validation_display_allowed":False,"state_version":stale.new_state_version,"trace_id":str(stale.trace.trace_id)})
 stories=[x.model_dump(mode="json") for x in run_all_capstone_stories()]
 total=len(cases)+len(stories); passed=sum(x["passed"] for x in cases)+sum(x["passed"] for x in stories)
 payload={"schema_version":"stages-0-8-10-service-journeys-v1","base_commit":BASE,"fixture_only":True,"sealed_holdout_accessed":False,"approved_published_slice_available":False,"provider_selection":None,"cases":{"passed":passed,"total":total},"service_cases":cases,"capstone_stories":stories,"blocked_dependencies":["No profile is genuinely published, so the approved-public retrieval hop cannot run.","No live provider is selected; deterministic provider remains Demo/test-only.","Safety specification and routine symptom policy remain draft/unapproved."],"limitations":["These journeys validate service contracts using fictional fixtures; they are not clinical validation or production Personal Mode evidence."]}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"passed":passed,"total":total},sort_keys=True))
 return 0 if passed==total else 1
if __name__=="__main__": raise SystemExit(main())
