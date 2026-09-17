"""Opt-in live normal-API smoke check; synthetic input, no fixture overrides."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '.local-api-deps'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-authorized-development', action='store_true')
    parser.add_argument('--only', nargs='+', choices=['nutrition','movement','wellbeing','balanced'])
    args = parser.parse_args()
    if not args.execute_authorized_development:
        parser.error('Explicit live development execution required')
    from fastapi.testclient import TestClient
    from api.main import app
    os.environ['MAYA_RUNTIME_MODE'] = 'private_development'
    os.environ['MAYA_OPERATOR_TOKEN'] = secrets.token_urlsafe(36)
    headers = {'X-Maya-Operator': os.environ['MAYA_OPERATOR_TOKEN']}
    client = TestClient(app, client=('127.0.0.1', 51000))
    sid = client.post('/v1/session').json()['session_id']
    payload = dict(session_id=sid,name='Synthetic refinement test',journey='pregnant',timeline_mode='week',timeline_value='22',diets=['Vegetarian'],allergies=['Dairy'],symptoms=['Heartburn'])
    assert client.post('/v1/onboarding',json=payload).status_code == 200
    directory = ROOT / 'reports/local/ui-integration'
    results = []
    for focus in ('nutrition','movement','wellbeing','balanced'):
        if args.only and focus not in args.only:
            continue
        response = client.post('/v1/plan',json=dict(session_id=sid,horizon='week',focus=focus),headers=headers)
        body = response.json()
        trace = body.get('trace',{})
        items = (body.get('schedule') or {}).get('items',[])
        checks = dict(http_ok=response.status_code==200,seven_days={i['day'] for i in items}==set(map(str,range(1,8))),
            fixture_free=trace.get('fixture_used') is False,
            real_generation=any(p.get('kind')=='generation' and p.get('http_status')==200 for p in trace.get('provider_receipts',[])),
            real_retrieval=bool(trace.get('workers')),
            plan_stored=response.status_code==200 and client.get('/v1/plans/'+sid).json().get('plan') is not None)
        results.append(dict(focus=focus,checks=checks,response=body))
        print(json.dumps(dict(focus=focus,checks=checks,error=body.get('detail'))),flush=True)
    result = dict(at=datetime.now(timezone.utc).isoformat(),synthetic_profile=True,results=results,
        passed=all(all(r['checks'].values()) for r in results))
    report=directory/('live-plan-focus-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(report),'passed':result['passed']}),flush=True)
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
