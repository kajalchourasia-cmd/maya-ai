"""Export only the synthetic rehearsal reports to a readable local document.

No provider calls, secrets, personal sessions or changes to recorded answers.
Later reports replace a matching question (for example a corrected retest).
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORTS=['chat-demo-20260916T194431Z.json','chat-demo-20260916T194652Z.json']

def main():
    cases={}
    for name in REPORTS:
        report=json.loads((ROOT/'reports/local/ui-integration'/name).read_text(encoding='utf-8'))
        if not report['synthetic_profile']['name'].startswith('Synthetic'):
            raise ValueError('Only explicitly synthetic reports may be exported')
        for result in report['results']:
            cases[result['name']]=(name,result)
    lines=['# Maya: actual recorded demo replies', '', '17 September 2026. Synthetic profile: week 22, vegetarian, dairy allergy, heartburn.', '',
        'These are exact stored replies, not proposed dialogue or guaranteed future wording. The movement reply below uses the corrected retest. Full traces remain in the referenced local JSON reports.', '',
        'Quality note: meal answers currently suggest food groups, not full recipes. Plans combine validated live guidance with separately source-linked authored meal components; they do not calculate consumed nutrients or prove nutritional completeness.', '']
    for index,(name,result) in enumerate(cases.values(),1):
        response=result['response']; display=response.get('display',{}); trace=response.get('trace',{})
        lines += [f'## {index}. {result["question"]}', '',f'Report: `{name}`. HTTP {result["status"]}. Mechanical checks: '+('passed' if all(result['checks'].values()) else 'FAILED')+'.', '', '### Actual reply', '',display.get('summary','No answer'), '']
        if display.get('applied_constraints'):
            lines += ['Applied context: '+'; '.join(display['applied_constraints']), '']
        citations=display.get('citations',[])
        if citations:
            lines += ['Sources returned:']+['- '+c['source_title']+(' — '+c['url'] if c.get('url') else '') for c in citations]+['']
        items=(response.get('schedule') or {}).get('items',[])
        if items:
            lines += ['### Actual saved schedule','', '| Day | Section | Text |', '| --- | --- | --- |']
            for item in items:
                values=[str(item['day']),item.get('slot') or item['domain'],item['item']]
                lines.append('| '+' | '.join(v.replace('|','\\|').replace('\n','<br>') for v in values)+' |')
            lines += ['']
        lines += ['Route: `'+str(trace.get('selection') or display.get('route'))+'`; fixture used: `'+str(trace.get('fixture_used',False)).lower()+'`.','']
    output=ROOT/'docs/MAYA-DEMO-ACTUAL-REPLIES-20260917.md'
    output.write_text('\n'.join(lines),encoding='utf-8')
    print(output)

if __name__=='__main__':main()
