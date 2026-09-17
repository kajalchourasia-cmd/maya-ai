"""Offline checks for the public final submission, not product/clinical validation."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = json.loads((ROOT / 'docs/FINAL-ARTIFACTS.json').read_text(encoding='utf-8'))


def test_final_artifact_bytes_and_hashes():
    for entry in CATALOGUE['files']:
        path = ROOT / entry['path']
        assert path.is_file()
        assert path.stat().st_size == entry['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    for relative in CATALOGUE['companion_documents']:
        assert (ROOT / relative).is_file()


def test_final_deck_has_seven_slides_and_correct_demo_link():
    deck = next(e for e in CATALOGUE['files'] if e['kind'] == 'final_presentation')
    video = next(e for e in CATALOGUE['external_links'] if e['kind'] == 'google_drive_final_demo')
    with zipfile.ZipFile(ROOT / deck['path']) as archive:
        assert archive.testzip() is None
        slides = [name for name in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', name)]
        assert len(slides) == 7
        links = []
        for name in archive.namelist():
            if name.endswith('.rels'):
                for rel in ET.fromstring(archive.read(name)):
                    if rel.get('TargetMode') == 'External':
                        links.append(rel.get('Target'))
        assert video['url'] in links
        assert not any(link.startswith(('file:', 'C:', 'c:')) for link in links)


def test_subtitles_fit_the_recording_and_cover_ending():
    subtitles = (ROOT / 'docs/demo/Maya-Action-Walkthrough-English.srt').read_text(encoding='utf-8-sig')
    times = re.findall(r'(\d\d):(\d\d):(\d\d),(\d\d\d)', subtitles)
    seconds = [int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000 for h,m,s,ms in times]
    assert seconds and min(seconds) >= 0 and max(seconds) <= 119.77
    assert max(seconds) > 116
    assert 'Maya' in subtitles


def test_current_docs_use_selected_final_video():
    for relative in ('README.md', 'docs/README.md', 'docs/FINAL-DELIVERABLES.md', 'docs/demo/README.md'):
        text = (ROOT / relative).read_text(encoding='utf-8')
        assert '1ZPV1fXbu57OIT5IvDuibPqoZ0_IiEKDy' in text
        assert '1_c9PBi_t13wArErK4ggj-w4Wmq0mH7jF' not in text
        assert 'Maya_3_Slide_Final_Deck' not in text
