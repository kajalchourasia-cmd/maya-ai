"""Narration for the second, action-led cut. Leaves first deliverable untouched."""
import asyncio
import json
import re
import subprocess
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/local/demo-video-20260917-v2'
FF = Path('C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')

async def main():
    scenes = json.loads((ROOT / 'scripts/demo_v2_story.json').read_text(encoding='utf-8'))
    (OUT/'audio').mkdir(parents=True, exist_ok=True)
    for scene in scenes:
        audio = OUT/'audio'/f"{scene['id']}.mp3"
        boundaries = audio.with_suffix('.json')
        if not audio.exists() or not boundaries.exists():
            words = []
            voice = edge_tts.Communicate(scene['text'], 'en-US-JennyNeural', rate='+12%', boundary='WordBoundary')
            with audio.open('wb') as handle:
                async for chunk in voice.stream():
                    if chunk['type']=='audio': handle.write(chunk['data'])
                    elif chunk['type']=='WordBoundary': words.append(chunk)
            boundaries.write_text(json.dumps(words, indent=2), encoding='utf-8')
        probe = subprocess.run([str(FF), '-hide_banner', '-i', str(audio)],capture_output=True,text=True)
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe.stderr)
        h,m,s = map(float,match.groups())
        scene.update(audio=str(audio), boundaries=str(boundaries), audio_seconds=h*3600+m*60+s)
        print(json.dumps({k:scene[k] for k in ['id','seconds','audio_seconds']}),flush=True)
    (OUT/'narration.json').write_text(json.dumps(scenes,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'allocated':sum(s['seconds'] for s in scenes),'audio':sum(s['audio_seconds'] for s in scenes),'over':sum(max(0,s['audio_seconds']+.05-s['seconds']) for s in scenes)}),flush=True)

if __name__=='__main__': asyncio.run(main())
