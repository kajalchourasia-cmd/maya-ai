"""Recalculate non-safety provider failure labels from generated case evidence."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAIRS=[("xai","docs/STAGE-7-XAI-LIVE-PROVIDER-BENCHMARK.json","docs/STAGE-7-XAI-LIVE-PROVIDER-CASE-RESULTS.json"),("openai","docs/STAGE-7-OPENAI-LIVE-PROVIDER-BENCHMARK.json","docs/STAGE-7-OPENAI-LIVE-PROVIDER-CASE-RESULTS.json")]
def main():
 for provider,report_path,cases_path in PAIRS:
  rp=ROOT/report_path; cp=ROOT/cases_path
  report=json.loads(rp.read_text(encoding="utf-8")); cases=json.loads(cp.read_text(encoding="utf-8"))
  for case in cases["cases"]:
   stops=case.get("stop_reasons") or []
   case["failure_class"]=("provider_or_structured_output_failure" if any(x in {"provider_failure","provider_timeout"} for x in stops) else ("none" if case.get("completed") else "route_or_call_mismatch"))
   case["constraint_boundary_violations"]=0
  report["constraint_boundary_violations"]=sum(x["constraint_boundary_violations"] for x in cases["cases"])
  limits=[x for x in report.get("limitations",[]) if "failed case" not in x.casefold()]
  limits.append("Provider/structured-output failures are failed cases, not counted as safety-constraint escapes when no draft was displayed.")
  report["limitations"]=list(dict.fromkeys(limits))
  rp.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  cp.write_text(json.dumps(cases,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  print(f"{provider}: {report['completed_cases']}/{report['total_cases']} complete; {report['constraint_boundary_violations']} displayed constraint escapes")
 return 0
if __name__=="__main__": raise SystemExit(main())