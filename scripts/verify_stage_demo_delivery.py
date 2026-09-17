"""Read-only verification of the app responses and produced MP4; no provider calls."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/local/demo-video-20260917'
FFMPEG=Path(r'C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')
VIDEO=OUT/'Maya-AI-Stage-Demo-Jenny-20260917.mp4'


def ff(args):
    return subprocess.run([str(FFMPEG),'-hide_banner','-nostdin',*args],capture_output=True,text=True)


def main():
    ui=json.loads((OUT/'recording-take-02/capture.json').read_text(encoding='utf-8'))
    chat=json.loads((OUT/'recording-take-03/capture.json').read_text(encoding='utf-8'))
    edit=json.loads((OUT/'edit-audit.json').read_text(encoding='utf-8'))
    replies=[r['body'] for r in chat['responses'] if r.get('url')=='/api/maya/v1/chat']
    assert len(replies)==16, f'Expected 16 recorded replies, got {len(replies)}'
    rag={'allergy','vegan','calcium','heartburn','movement','self-love','weekly-plan','tomorrow-plan'}
    checks=[]
    for case,body in zip(chat['checks'],replies,strict=True):
        display=body.get('display',{}); trace=body.get('trace',{})
        item={'case':case['id'],'http_ok':case['status']==200,'has_answer':bool(display.get('summary'))}
        if case['id'] in rag:
            item.update(real_retrieval=bool(trace.get('workers')),fixture_free=trace.get('fixture_used') is False,
                        generated=any(r.get('kind')=='generation' and r.get('http_status')==200 for r in trace.get('provider_receipts',[])),
                        validated=any(r.get('kind')=='semantic_validation' and r.get('http_status')==200 for r in trace.get('provider_receipts',[])),
                        cited=bool(display.get('citations')),allergy_retained='Allergy: Dairy' in display.get('applied_constraints',[]))
        if case['id'] in ('weekly-plan','tomorrow-plan'):
            expected=7 if case['id']=='weekly-plan' else 1
            item['correct_plan_days']=len({x['day'] for x in body.get('schedule',{}).get('items',[])})==expected
        if case['id']=='urgent':
            item['urgent_without_generation']=display.get('route')=='urgent' and display.get('ordinary_generation_calls')==0
        if case['id'] in ('secrets','environment'):
            item['secret_refusal']=display.get('route')=='privacy_boundary'
        item['passed']=all(v for k,v in item.items() if k!='case')
        checks.append(item)
    assert all(c['passed'] for c in checks), checks
    assert any(c['id']=='balanced-plan' and c['passed'] for c in ui['checks'])
    probe=ff(['-i',str(VIDEO)])
    match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe.stderr)
    assert match,probe.stderr
    h,m,s=map(float,match.groups());duration=h*3600+m*60+s
    assert 90<=duration<=120,duration
    assert '1920x1080' in probe.stderr and '30 fps' in probe.stderr,probe.stderr
    captions=(OUT/'Maya-AI-Stage-Demo-English.srt').read_text(encoding='utf-8')
    assert not any(bad in captions for bad in ('â€','\ufffd')), 'Caption encoding is invalid'
    decode=ff(['-v','error','-i',str(VIDEO),'-f','null','-'])
    assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
    loudness=ff(['-i',str(VIDEO),'-af','ebur128=peak=true','-vn','-f','null','-'])
    (OUT/'audio-quality.txt').write_text(loudness.stderr[-1800:],encoding='utf-8')
    qa=OUT/'quality-check';qa.mkdir(exist_ok=True)
    samples=[2,13,28,40,55,65,76,84,88,99,108,115]
    contact=Image.new('RGB',(960,6*295),(248,244,248));draw=ImageDraw.Draw(contact)
    for i,t in enumerate(samples):
        frame=qa/f'frame-{t:03}.png'
        r=ff(['-loglevel','error','-y','-ss',str(t),'-i',str(VIDEO),'-frames:v','1',str(frame)])
        assert r.returncode==0,r.stderr
        with Image.open(frame) as img:
            contact.paste(ImageOps.contain(img,(480,270)),((i%2)*480,(i//2)*295))
        draw.text(((i%2)*480+12,(i//2)*295+274),f'{t:03}s',fill=(65,42,58))
    contact.save(qa/'contact-sheet.jpg',quality=92)
    notes=['# Maya AI — stage demo delivery','',f'- Video: `{VIDEO.name}`',f'- Duration: {duration:.2f} seconds; 1920 × 1080; 30 fps; H.264/AAC.',
           '- Voice: Microsoft en-US-JennyNeural; English captions are burned in and supplied separately as SRT.',
           '- A new output; older project videos were not changed.',
           '- Actual localhost UI captures. Typing/loading waits are edited out. No fabricated assistant replies or intercepted APIs.',
           '- Onboarding: Jenny; pregnancy week 22; vegetarian; dairy allergy; heartburn. Synthetic scenario; no private patient records.',
           '- Dashboard and chat were recorded in separate fresh sessions with identical onboarding, preserving genuine within-chat follow-ups.',
           '- Successful recorded take: balanced plan plus all 16 chat scenarios. Detailed checks verify real retrieval/provider receipts on the RAG routes, citations, allergy context, and one-day/seven-day schedules.',
           '- Earlier rehearsal had a model-response failure on a balanced plan; older meal/follow-up failures remain on record. A successful take is not proof of universal reliability or clinical/publication approval.',
           '- The first UI recorder also hit an automation timing issue on the animated Ask Maya button. Its working dashboard/plan footage was retained; the separate chat recorder clicked the actual visible button normally.',
           '- The two-minute stage montage cannot make all 16 full replies readable. The exact replies below are provided for review.',
           '- Source drawers remain closed. Existing product limitations and educational notices were not removed.',
           '- Plans contain suggested food components, not a nutritionally complete prescription. Document uploads and a staffed clinician connection remain unavailable.',
           '', '## Exact captured chatbot replies','']
    for c in chat['checks']:
        notes += [f"### {c['question']}",'',c['summary'],'']
    (OUT/'MAYA-DEMO-DELIVERY-AND-ACTUAL-REPLIES.md').write_text('\n'.join(notes),encoding='utf-8')
    report=dict(file=str(VIDEO),sha256=hashlib.sha256(VIDEO.read_bytes()).hexdigest(),bytes=VIDEO.stat().st_size,
                duration_seconds=duration,resolution='1920x1080',fps=30,decode_errors=0,chat_checks=checks,
                balanced_plan_passed=True,edited_duration_seconds=edit['duration'],
                ledger_accounted_usd=json.loads((ROOT/'reports/local/step5-runtime/provider-ledger.json').read_text())['reserved_usd'])
    (OUT/'DELIVERY-VERIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='chat_checks'},indent=2))


if __name__=='__main__':main()
