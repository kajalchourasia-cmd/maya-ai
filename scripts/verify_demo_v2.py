"""Verify exported media and real recorded route receipts, without provider calls."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/local/demo-video-20260917-v2'
VIDEO=OUT/'Maya-AI-Action-Walkthrough-Jenny-v2.mp4'
FF=Path('C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')
def ff(args):return subprocess.run([str(FF),'-hide_banner','-nostdin',*args],capture_output=True,text=True)

def main():
    capture=json.loads((OUT/'take-03/capture.json').read_text(encoding='utf-8'))
    edit=json.loads((OUT/'edit-audit.json').read_text(encoding='utf-8'))
    assert not capture['failures'],capture['failures']
    checks=[]
    for r in capture['replies']:
        body=r['body'];display=body['display'];trace=body.get('trace',{})
        check={'id':r['id'],'http_ok':r['status']==200,'has_answer':bool(display.get('summary'))}
        if r['id'] in ['plan','allergy','vegan','heartburn']:
            check.update(retrieval=bool(trace.get('workers')),not_fixture=trace.get('fixture_used') is False,
                         sources=bool(display.get('citations')),context='Allergy: Dairy' in display.get('applied_constraints',[]),
                         live_generation=any(p.get('kind')=='generation' and p.get('http_status')==200 for p in trace.get('provider_receipts',[])))
        if r['id']=='plan':check['seven_days']=len({x['day'] for x in body['schedule']['items']})==7
        if r['id']=='urgent':check['urgent_route']=display['route']=='urgent' and display.get('ordinary_generation_calls')==0
        if r['id']=='secrets':check['refused']=display['route']=='privacy_boundary'
        assert all(v for k,v in check.items() if k!='id'),check
        checks.append(check)
    assert len(checks)==6
    p=ff(['-i',str(VIDEO)])
    match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',p.stderr);h,m,s=map(float,match.groups());duration=h*3600+m*60+s
    assert 110<=duration<=120,duration
    assert '1920x1080' in p.stderr and '30 fps' in p.stderr
    decoded=ff(['-v','error','-i',str(VIDEO),'-f','null','-']);assert not decoded.stderr.strip() and decoded.returncode==0,decoded.stderr
    loudness=ff(['-i',str(VIDEO),'-af','ebur128=peak=true','-vn','-f','null','-'])
    (OUT/'audio-quality.txt').write_text(loudness.stderr[-2000:],encoding='utf-8')
    qa=OUT/'quality-check';qa.mkdir(exist_ok=True)
    samples=[2,10,20,27,32,38,44,51,56,60,66,70,76,79,84,90,96,103,110,118]
    contact=Image.new('RGB',(1200,10*248),(250,247,249));draw=ImageDraw.Draw(contact)
    for i,t in enumerate(samples):
        frame=qa/f'frame-{t:03}.png';r=ff(['-loglevel','error','-y','-ss',str(t),'-i',str(VIDEO),'-frames:v','1',str(frame)]);assert r.returncode==0
        with Image.open(frame) as img:contact.paste(ImageOps.contain(img,(600,225)),((i%2)*600,(i//2)*248))
        draw.text(((i%2)*600+12,(i//2)*248+228),f'{t}s',fill=(64,37,50))
    contact.save(qa/'contact-sheet.jpg',quality=94)
    srt=(OUT/'Maya-Action-Walkthrough-English.srt').read_text(encoding='utf-8');assert not any(bad in srt for bad in ['â€','\ufffd'])
    previous=ROOT/'reports/local/demo-video-20260917/Maya-AI-Stage-Demo-Jenny-20260917.mp4'
    previous_unchanged=hashlib.sha256(previous.read_bytes()).hexdigest()=='25b8c0310a0d9bcfb6d260ba6dc7dceae6b96eab9ecf88aac293938e62a97093'
    assert previous_unchanged,'Original video changed'
    report={'file':str(VIDEO),'duration_seconds':duration,'resolution':'1920x1080','fps':30,'decode_errors':0,'checks':checks,'original_video_unchanged':True,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'bytes':VIDEO.stat().st_size,'ledger_accounted_usd':json.loads((ROOT/'reports/local/step5-runtime/provider-ledger.json').read_text())['reserved_usd']}
    (OUT/'DELIVERY-VERIFICATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    notes=['# Maya AI — two-minute action-led walkthrough','',f'Duration: {duration:.2f} seconds. 1080p, 30 fps, H.264/AAC. Voice: Microsoft en-US-JennyNeural.','',
    '## What changed','',
    '- The four KPIs remain on screen for their explanation, with subtle editorial outlines identifying each one.',
    '- Actual navigation, typed messages, sends, processing and response arrivals replace the first cut’s post-action montage.',
    '- The balanced plan is selected and submitted through the normal UI, then the actual seven-day schedule and everyday routine appear.',
    '- Five chat exchanges are included: allergy-aware meals, vegan follow-up, heartburn, urgent help, and a secret/API-key request.',
    '- Long real processing waits are shortened in the edit; this video is not a latency benchmark. No API interception, scripted replacement answers or removed safety notices.',
    '- Source drawers stay closed. Narration distinguishes source-linked dashboard guidance from RAG-backed chat.',
    '- Synthetic onboarding only: Jenny, pregnancy week 22, vegetarian, dairy allergy, heartburn. No medical documents were uploaded.',
    '- The original MP4 is unchanged; its hash was checked.',
    '- Earlier recorder attempts failed on off-screen/animated controls. The final continuous capture completed normally. These were recorder faults, not concealed chatbot failures.',
    '', '## Scope of verification','',
    'The recorded plan and five replies returned HTTP 200. RAG routes include retrieval, generation receipts, citations and retained allergy context. The plan contains seven days. Urgent and secret requests use the appropriate deterministic boundaries. This is a successful recorded run, not evidence of universal reliability or clinical approval. Plans remain suggestions rather than calculated nutritionally complete menus. Human clinician handoff and document uploads remain unimplemented.',
    '', 'Content limitation: the first allergy/meal request returned a general nutrient overview, not a detailed meal list. The vegan follow-up supplied food groups, not recipes. These are the actual answers; they have not been replaced, and HTTP success must not be confused with full answer-quality acceptance.',
    '', '## Narration and timing','']
    for scene in edit['scenes']:notes += [f"### {scene['start']:.2f}–{scene['end']:.2f}s · {scene['id']}",'',scene['text'],'']
    notes += ['## Exact captured responses','']
    for r in capture['replies']:notes += [f"### {r['id']}",'',r['body']['display']['summary'],'']
    (OUT/'MAYA-ACTION-DEMO-TRANSCRIPT-AND-REPLIES.md').write_text('\n'.join(notes),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))

if __name__=='__main__':main()
