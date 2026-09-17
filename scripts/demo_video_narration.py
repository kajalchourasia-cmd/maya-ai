"""Create a NEW Jenny narration from the approved script; never edit older videos."""
import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/local/demo-video-20260917'
FFMPEG = Path(r'C:/Users/Hrishikesh/Developer/genai/Capstone Project/demo-video/node_modules/ffmpeg-static/ffmpeg.exe')
NAMES = ['landing', 'onboarding', 'dashboard', 'growth', 'explore', 'plan', 'chat', 'closing']


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'audio-jenny16').mkdir(exist_ok=True)
    lines = (ROOT / 'docs/MAYA-TWO-MINUTE-DEMO-TRANSCRIPT-FOR-APPROVAL.md').read_text(encoding='utf-8').splitlines()
    rows = [line for line in lines if re.match(r'^\| \d:\d\d', line)]
    scenes = []
    for name, row in zip(NAMES, rows, strict=True):
        text = row.split('|')[-2].strip().strip('“”')
        audio = OUT / 'audio-jenny16' / f'{name}.mp3'
        boundaries = OUT / 'audio-jenny16' / f'{name}.boundaries.json'
        if not audio.exists() or not boundaries.exists():
            chunks = []
            voice = edge_tts.Communicate(text, 'en-US-JennyNeural', rate='+16%', pitch='+0Hz', boundary='WordBoundary')
            with audio.open('wb') as handle:
                async for chunk in voice.stream():
                    if chunk['type'] == 'audio':
                        handle.write(chunk['data'])
                    elif chunk['type'] in ('WordBoundary', 'SentenceBoundary'):
                        chunks.append({k: v for k, v in chunk.items() if k != 'data'})
            boundaries.write_text(json.dumps(chunks, indent=2), encoding='utf-8')
        probe = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(audio)], capture_output=True, text=True)
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', probe.stderr)
        if not match:
            raise RuntimeError(f'Cannot measure {audio.name}')
        h, m, s = map(float, match.groups())
        duration = h * 3600 + m * 60 + s
        scenes.append(dict(id=name, narration=text, audio=str(audio), audio_seconds=duration, boundaries=str(boundaries)))
        print(json.dumps(dict(scene=name, seconds=duration)), flush=True)
    (OUT / 'narration.json').write_text(json.dumps(scenes, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(dict(total_audio_seconds=sum(x['audio_seconds'] for x in scenes), voice='en-US-JennyNeural')), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
