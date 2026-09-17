"""Edit real recorded UI into a new captioned stage video, with source audit trail."""
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/local/demo-video-20260917'
CAPTURE = OUT / 'recording-take-02'
CHAT_CAPTURE = OUT / 'recording-take-03'
FFMPEG = Path(r'C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')
FINAL = OUT / 'Maya-AI-Stage-Demo-Jenny-20260917.mp4'
TITLES = ['A little less searching', 'A journey that starts with Jenny', 'Her week, in focus', 'Room for a little wonder', 'From information to everyday choices', 'A clearer view of the week ahead', 'Ask Maya · a conversation with context', 'A clearer next step']


def run(args):
    p = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'warning', '-nostdin', *args], cwd=OUT, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])


def timestamp(t, ass=False):
    if ass:
        n = round(t * 100); h, n = divmod(n, 360000); m, n = divmod(n, 6000); s, n = divmod(n, 100)
        return f'{h}:{m:02}:{s:02}.{n:02}'
    n = round(t * 1000); h, n = divmod(n, 3600000); m, n = divmod(n, 60000); s, n = divmod(n, 1000)
    return f'{h:02}:{m:02}:{s:02},{n:03}'


def subtitles(scenes):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Segoe UI,30,&H003A2935,&H003A2935,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,0,0,1,1,0,2,110,110,25,1
Style: Chapter,Segoe UI,21,&H006A3D56,&H006A3D56,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,1,0,1,0,0,7,108,108,12,1
Style: Feature,Georgia,72,&H006A3D56,&H006A3D56,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,0,0,1,0,0,7,180,800,310,1
Style: FeatureDetail,Segoe UI,31,&H00756376,&H00756376,&H00FFF9FC,&H00FFF9FC,0,0,0,0,100,100,0,0,1,0,0,7,185,800,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines = []; srt = []; counter = 1
    for i, scene in enumerate(scenes):
        start = scene['start']; end = scene['end']
        lines.append(f'Dialogue: 1,{timestamp(start,True)},{timestamp(end,True)},Chapter,,0,0,0,,MAYA  /  {i+1:02}    {TITLES[i]}')
        if scene['id']=='growth':
            lines.append(f'Dialogue: 1,{timestamp(start,True)},{timestamp(end,True)},Feature,,0,0,0,,A little wonder.\\NEvery week.')
            lines.append(f'Dialogue: 1,{timestamp(start,True)},{timestamp(end,True)},FeatureDetail,,0,0,0,,A size comparison.\\NA weekly discovery.\\NA moment to connect.')
        words = json.loads(Path(scene['boundaries']).read_text(encoding='utf-8'))
        original = scene['narration']
        searchable = original.replace('’', "'").replace('‘', "'")
        positions = []
        source_cursor = 0
        for word in words:
            needle = html.unescape(word['text']).replace('’', "'").replace('‘', "'")
            found = re.search(re.escape(needle), searchable[source_cursor:], re.I)
            if found:
                a = source_cursor + found.start(); b = source_cursor + found.end()
                positions.append((a,b)); source_cursor=b
            else:
                positions.append(None)
        batch = []
        batch_first = 0
        for wi, word in enumerate(words):
            if not batch:
                batch_first = wi
            batch.append(word)
            char_count = sum(len(x['text']) + 1 for x in batch)
            next_start = positions[wi+1][0] if wi+1<len(words) and positions[wi+1] else len(original)
            trailing = original[positions[wi][1]:next_start] if positions[wi] else ''
            sentence_end = bool(re.search(r'[.!?]',trailing))
            if char_count < 64 and len(batch) < 11 and wi < len(words)-1 and not sentence_end:
                continue
            a = start + batch[0]['offset'] / 1e7
            b = start + (batch[-1]['offset'] + batch[-1]['duration']) / 1e7 + .08
            if wi+1 < len(words):
                b = min(b, start + words[wi+1]['offset']/1e7 - .005)
            phrase = html.unescape(' '.join(x['text'] for x in batch)).replace('{','').replace('}','')
            if positions[batch_first] and positions[wi]:
                phrase = original[positions[batch_first][0]:next_start].strip().replace('{','').replace('}','')
            lines.append(f'Dialogue: 2,{timestamp(a,True)},{timestamp(min(b,end),True)},Caption,,0,0,0,,{phrase}')
            srt.extend([str(counter), f'{timestamp(a)} --> {timestamp(min(b,end))}', phrase, ''])
            counter += 1; batch = []
    (OUT/'captions.ass').write_text(header+'\n'.join(lines)+'\n', encoding='utf-8')
    (OUT/'Maya-AI-Stage-Demo-English.srt').write_text('\n'.join(srt), encoding='utf-8')


def main():
    prepare_ui = '--prepare-ui' in sys.argv
    manifest = json.loads((CAPTURE/'capture.json').read_text(encoding='utf-8'))
    chat_manifest = json.loads((CHAT_CAPTURE/'capture.json').read_text(encoding='utf-8')) if not prepare_ui else {'shots':[], 'checks':[]}
    scenes = json.loads((OUT/'narration.json').read_text(encoding='utf-8'))
    if prepare_ui:
        scenes = scenes[:6]
    shots = {s['id']: {**s,'source':str(CAPTURE/'Maya-real-ui-raw.webm')} for s in manifest['shots']}
    shots.update({s['id']: {**s,'source':str(CHAT_CAPTURE/'Maya-real-ui-raw.webm')} for s in chat_manifest['shots']})
    failures = [c for c in manifest['checks'] if c['id'] != 'capture-exception' and not c['passed']]
    failures += [c for c in chat_manifest['checks'] if not c['passed']]
    if failures:
        raise RuntimeError('Capture has failed checks; inspect before editing: '+json.dumps(failures)[:800])
    groups = {
        'landing': [('landing', 1)],
        'onboarding': [('onboard-name', .18),('onboard-journey',.17),('onboard-timeline',.32),('onboard-preferences',.33)],
        'dashboard': [('dashboard', .53),('hormones',.47)],
        'growth': [('growth', 1)],
        'explore': [('this-week', .26),('nutrition',.18),('nutrition-detail',.13),('movement',.17),('symptoms',.08),('self-love',.08),('faqs',.10)],
        'plan': [('plan-builder', .20),('plan-result',.18),('plan-table',.45),('plan-routine',.17)],
        'chat': [('chat-intro',.05),('chat-week',.06),('chat-compare-week',.04),('chat-allergy',.085),('chat-vegan',.085),('chat-calcium',.05),('chat-heartburn',.075),('chat-movement',.055),('chat-self-love',.04),('chat-weekly-plan',.055),('chat-tomorrow-plan',.055),('chat-memory',.07),('chat-medication',.055),('chat-secrets',.06),('chat-environment',.045),('chat-no-document',.04),('chat-urgent',.075)],
        'closing': [('closing', .30),('endcard',.70)],
    }
    clips = OUT/'clips-polished'; clips.mkdir(exist_ok=True)
    cursor = 0; audit = []
    for si, scene in enumerate(scenes):
        duration = scene['audio_seconds'] + .23
        duration = round(duration * 30) / 30
        scene.update(start=cursor, end=cursor+duration, duration=duration)
        cursor += duration
        group = groups[scene['id']]
        weight_sum = sum(w for _,w in group)
        remaining = round(duration*30)
        part_files = []
        for pi,(key,weight) in enumerate(group):
            shot=shots.get(key)
            frames = remaining if pi==len(group)-1 else round(duration*30*weight/weight_sum)
            remaining -= frames; seconds=frames/30
            part=clips/f'{si:02}-{pi:02}-{key}.mp4'
            start=shot['start']+.15 if shot else 0
            available=shot['end']-start-.1 if shot else seconds
            take=min(seconds,available)
            # Preserve the complete viewport. The border and caption area are editorial framing,
            # not alterations to the app or its answers. No source dropdown is opened.
            vf=f'fps=30,scale=1706:960,pad=1920:1080:107:42:color=0xFFF9FC,setsar=1,tpad=stop_mode=clone:stop_duration={seconds+1},trim=duration={seconds},setpts=PTS-STARTPTS,format=yuv420p'
            if key=='growth':
                vf=f'fps=30,crop=446:680:1038:85,scale=590:900,pad=1920:1080:1130:65:color=0xFFF9FC,setsar=1,tpad=stop_mode=clone:stop_duration={seconds+1},trim=duration={seconds},setpts=PTS-STARTPTS,format=yuv420p'
            elif key.startswith('chat-') and key!='chat-intro':
                vf=f'fps=30,crop=890:700:355:78,scale=1220:960,pad=1920:1080:350:42:color=0xFFF9FC,setsar=1,tpad=stop_mode=clone:stop_duration={seconds+1},trim=duration={seconds},setpts=PTS-STARTPTS,format=yuv420p'
            input_args=['-ss',f'{start:.4f}','-t',f'{take:.4f}','-i',shot['source']] if shot else []
            if key=='endcard':
                input_args=['-loop','1','-i','endcard.png']
                vf=f'fps=30,trim=duration={seconds},setpts=PTS-STARTPTS,format=yuv420p'
            if not part.exists():
                run(['-y',*input_args,'-vf',vf,'-an','-frames:v',str(frames),'-c:v','libx264','-preset','veryfast','-crf','19',str(part)])
            part_files.append(part)
            audit.append(dict(scene=scene['id'],shot=key,source_start=start,source_take=take,edited_seconds=seconds))
        listing=clips/f'{si:02}-parts.txt'
        listing.write_text(''.join(f"file '{p.as_posix()}'\n" for p in part_files),encoding='utf-8')
        rendered=clips/f'scene-{si:02}.mp4'
        if not rendered.exists():
            run(['-y','-f','concat','-safe','0','-i',str(listing),'-i',scene['audio'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',f'apad,atrim=duration={duration},asetpts=PTS-STARTPTS','-c:a','aac','-b:a','192k','-ar','48000','-t',f'{duration:.5f}',str(rendered)])
        print(json.dumps(dict(scene=scene['id'],seconds=duration)),flush=True)
    if prepare_ui:
        print('UI chapters prepared; no final video exported.', flush=True)
        return
    if cursor > 120:
        raise RuntimeError(f'Timing exceeds limit: {cursor}')
    subtitles(scenes)
    concat=OUT/'scene-list.txt'
    concat.write_text(''.join(f"file '{(clips/f'scene-{i:02}.mp4').as_posix()}'\n" for i in range(len(scenes))),encoding='utf-8')
    run(['-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','stage-uncaptioned.mp4'])
    run(['-y','-i','stage-uncaptioned.mp4','-vf',f"ass=captions.ass,fade=t=in:st=0:d=0.25,fade=t=out:st={cursor-.45:.3f}:d=0.45",'-af',f'loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={cursor-.25:.3f}:d=0.25','-c:v','libx264','-preset','medium','-crf','19','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(FINAL)])
    (OUT/'edit-audit.json').write_text(json.dumps(dict(duration=cursor,scenes=scenes,shots=audit,source='Real localhost UI; waiting/typing time edited; no answer substitution.',voice='Microsoft en-US-JennyNeural',resolution='1920x1080',fps=30),indent=2),encoding='utf-8')
    print(json.dumps(dict(file=str(FINAL),duration=cursor)),flush=True)


if __name__=='__main__':
    main()
