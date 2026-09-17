"""Two-minute edit retaining actual clicks, typing, loading and response arrivals."""
import html
import json
import math
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/local/demo-video-20260917-v2'
CAP=OUT/'take-03'
FF=Path('C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')
FINAL=OUT/'Maya-AI-Action-Walkthrough-Jenny-v2.mp4'

def run(args):
    r=subprocess.run([str(FF),'-hide_banner','-loglevel','warning','-nostdin',*args],cwd=OUT,capture_output=True,text=True)
    if r.returncode: raise RuntimeError(r.stderr[-5000:])

def ts(t,ass=False):
    if ass:
        n=round(t*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100)
        return f'{h}:{m:02}:{s:02}.{n:02}'
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{n:03}'

def captions(scenes):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Segoe UI,30,&H003A2935,&H003A2935,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,0,0,1,1,0,2,110,110,24,1
Style: Chapter,Segoe UI,21,&H006A3D56,&H006A3D56,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,1,0,1,0,0,7,108,108,12,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    titles={'landing':'A little less searching','onboarding':'A journey that starts with Jenny','kpis':'Four priorities, one clear starting point','rhythm':"Understanding her body's changing rhythm",'growth':'Room for wonder','this-week':'Her week at a glance','nutrition':'From guidance to food choices','movement':'Making movement manageable','support':'Care for the whole person','plan':'Select. Build. See the week ahead.','chat-intro':'From a dashboard to a conversation','allergy':'01 / Meals, with her context','vegan':'02 / A follow-up, not a fresh start','heartburn':'03 / Help with a reported symptom','urgent':'04 / Recognising when to seek urgent help','secrets':'05 / Keeping credentials private','closing':'A clearer next step'}
    lines=[];srt=[];n=1
    for scene in scenes:
        start=scene['start'];end=scene['end'];text=scene['text'];words=json.loads(Path(scene['boundaries']).read_text(encoding='utf-8'))
        lines.append(f"Dialogue: 1,{ts(start,True)},{ts(end,True)},Chapter,,0,0,0,,MAYA  /  {titles[scene['id']]}")
        positions=[];cur=0;search=text.replace('’',"'").replace('‘',"'")
        for w in words:
            needle=html.unescape(w['text']).replace('’',"'").replace('‘',"'")
            m=re.search(re.escape(needle),search[cur:],re.I)
            if not m: raise ValueError('Cannot align word: '+needle)
            a=cur+m.start();b=cur+m.end();positions.append((a,b));cur=b
        first=0
        for i,w in enumerate(words):
            nxt=positions[i+1][0] if i+1<len(words) else len(text)
            phrase=text[positions[first][0]:nxt].strip()
            punct=text[positions[i][1]:nxt]
            if len(phrase)<66 and i-first<10 and not re.search(r'[.!?;]',punct) and i+1<len(words):continue
            a=start+words[first]['offset']/1e7;b=start+(w['offset']+w['duration'])/1e7+.1
            if i+1<len(words):b=min(b,start+words[i+1]['offset']/1e7-.006)
            b=min(b,end);phrase=phrase.replace('{','').replace('}','')
            lines.append(f'Dialogue: 2,{ts(a,True)},{ts(b,True)},Caption,,0,0,0,,{phrase}')
            srt += [str(n),f'{ts(a)} --> {ts(b)}',phrase,''];n+=1;first=i+1
    (OUT/'captions.ass').write_text(header+'\n'.join(lines)+'\n',encoding='utf-8')
    (OUT/'Maya-Action-Walkthrough-English.srt').write_text('\n'.join(srt),encoding='utf-8')

def intervals(s,seconds):
    a=s['start'];b=s['end'];h=s['holdStart'];m=s['marks'];key=s['id']
    if key=='plan':
        # Preserve visible selection/click plus over one second of actual processing.
        return [(a,m['sent']+1.15,3.5),(m['received']-.08,m['routine'],seconds-5.0),(m['routine'],b,1.5)]
    if key in ('allergy','vegan','heartburn','urgent','secrets'):
        wait=m['received']-m['sent']
        # Instant deterministic refusals/urgent routing are retained as a continuous exchange.
        if wait<1.4:
            # Keep the same exchange continuous, accelerating only the typing/action span.
            split=m['received']+.15
            return [(a,split,2.5),(split,min(b,split+seconds-2.5),seconds-2.5)]
        action_end=m['sent']+1.0
        action_secs=min(action_end-a,3.25)
        return [(a,action_end,action_secs),(m['received']-.08,min(b,m['answer']+seconds-action_secs),seconds-action_secs)]
    if key=='onboarding':return [(a,h,seconds)]
    if key=='kpis':return [(a,min(b,a+seconds),seconds)]
    if key=='support':return [(a,m['self'],2.0),(m['self'],m['faq'],1.6),(m['faq'],b,seconds-3.6)]
    if key=='nutrition':return [(a,m['detail'],3.3),(m['detail'],b,seconds-3.3)]
    if key=='movement':
        # Omit the preparatory scroll back from nutrition, but retain the actual tab click.
        return [(max(a,h-1.0),min(b,max(a,h-1.0)+seconds),seconds)]
    if key=='closing':return [(a,b,1.0),('endcard','endcard',seconds-1.0)]
    # Keep the real transition, then a calm hold; do not use still screenshots.
    return [(a,min(b,a+seconds),seconds)]

def main():
    raw=json.loads((CAP/'capture.json').read_text(encoding='utf-8'))
    assert not raw['failures'],raw['failures']
    assert len(raw['replies'])==6, 'Need one plan and five replies'
    manifest={s['id']:s for s in raw['scenes']}
    scenes=json.loads((OUT/'narration.json').read_text(encoding='utf-8'))
    requested={s['id']:s for s in json.loads((ROOT/'scripts/demo_v2_story.json').read_text(encoding='utf-8'))}
    for scene in scenes: scene['seconds']=requested[scene['id']]['seconds']
    cursor=0
    for s in scenes:
        words=json.loads(Path(s['boundaries']).read_text(encoding='utf-8'))
        spoken_end=(words[-1]['offset']+words[-1]['duration'])/1e7
        duration=math.ceil(max(s['seconds'],spoken_end+.16)*30)/30
        s.update(start=cursor,end=cursor+duration,duration=duration);cursor+=duration
    if cursor>120:raise RuntimeError(f'Too long: {cursor}')
    clips=OUT/'action-clips-final';clips.mkdir(exist_ok=True);audit=[]
    for i,s in enumerate(scenes):
        source=manifest[s['id']];parts=[];frames_left=round(s['duration']*30)
        cuts=intervals(source,s['duration'])
        for j,(a,b,duration) in enumerate(cuts):
            frames=frames_left if j==len(cuts)-1 else round(duration*30);frames_left-=frames;duration=frames/30
            dest=clips/f'{i:02}-{j:02}-{s["id"]}.mp4';parts.append(dest)
            if a=='endcard':
                inputs=['-loop','1','-i',str(ROOT/'reports/local/demo-video-20260917/endcard.png')]
                vf=f'fps=30,trim=duration={duration},setpts=PTS-STARTPTS,format=yuv420p'
                speed=1
            else:
                available=b-a
                # Trim quiet tail, preserve all action. Only longer action spans are sped modestly.
                preserve_action=s['id'] in ('onboarding','plan','support','nutrition') or (j==0 and s['id'] in ('allergy','vegan','heartburn','urgent','secrets'))
                take=available if preserve_action else min(available,duration)
                speed=max(1,take/duration)
                inputs=['-ss',f'{a:.5f}','-t',f'{take:.5f}','-i',str(CAP/'Maya-action-recording.webm')]
                framing='scale=1706:960,pad=1920:1080:107:42:color=0xFFF9FC'
                if s['id'] in ('allergy','vegan','heartburn','urgent','secrets'):
                    framing='crop=980:890:310:0,scale=1058:960,pad=1920:1080:431:42:color=0xFFF9FC'
                vf=f'setpts=(PTS-STARTPTS)/{speed:.8f},fps=30,{framing},setsar=1,tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},format=yuv420p'
                if s['id']=='kpis':
                    # Editorial outline identifies each real KPI as its name is spoken.
                    for x,t0,t1 in [(214,.65,2.35),(592,2.35,4.4),(970,4.4,6.6),(1348,6.6,8.6)]:
                        vf+=f",drawbox=x={x}:y=142:w=358:h=302:color=0xb26887@0.60:t=2:enable='between(t,{t0},{t1})'"
            if not dest.exists() or s['id']=='movement':run(['-y',*inputs,'-vf',vf,'-frames:v',str(frames),'-an','-c:v','libx264','-preset','veryfast','-crf','18',str(dest)])
            audit.append({'scene':s['id'],'source_start':a,'source_end':b,'edited_seconds':duration,'playback_speed':speed})
        listing=clips/f'{i:02}.txt';listing.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts),encoding='utf-8')
        scene_file=clips/f'scene-{i:02}.mp4'
        if not scene_file.exists() or s['id']=='movement':run(['-y','-f','concat','-safe','0','-i',str(listing),'-i',s['audio'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',f'apad,atrim=duration={s["duration"]},asetpts=PTS-STARTPTS','-c:a','aac','-b:a','192k','-ar','48000','-t',str(s['duration']),str(scene_file)])
        print(json.dumps({'scene':s['id'],'start':s['start'],'duration':s['duration']}),flush=True)
    captions(scenes)
    listing=OUT/'scene-list.txt';listing.write_text(''.join(f"file '{(clips/f'scene-{i:02}.mp4').as_posix()}'\n" for i in range(len(scenes))),encoding='utf-8')
    run(['-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','uncaptioned-v2.mp4'])
    run(['-y','-i','uncaptioned-v2.mp4','-vf',f'ass=captions.ass,fade=t=in:st=0:d=0.2,fade=t=out:st={cursor-.35}:d=0.35','-af',f'loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={cursor-.25}:d=0.25','-c:v','libx264','-preset','medium','-crf','19','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(FINAL)])
    (OUT/'edit-audit.json').write_text(json.dumps({'duration':cursor,'scenes':scenes,'cuts':audit,'note':'Real UI action recording. Only long processing waits shortened. No answer replacements. Recording-only pointer overlay.'},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'file':str(FINAL),'duration':cursor}),flush=True)

if __name__=='__main__':main()
