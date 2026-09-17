"""Run deterministic Step 4A preparation into ignored local review reports only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.corpus_import import build_plan, verified_payloads, sha256
from app.services.corpus_preparation import build_preparation

MANIFEST_HASH = '2ebd508df90d7bc32055de176e2e081330a645df5ba83029fffde0f5ad2396b7'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    payloads, _ = verified_payloads(args.package, MANIFEST_HASH)
    plan = build_plan(args.package, MANIFEST_HASH)
    report = build_preparation(plan, payloads)
    directory = ROOT / 'reports/local/corpus-preparation' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True, exist_ok=False)
    report['prepared_at_utc'] = datetime.now(timezone.utc).isoformat()
    (directory / 'preparation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    with (directory / 'review-sections.jsonl').open('w', encoding='utf-8') as stream:
        for section in report['sections']:
            stream.write(json.dumps(section, ensure_ascii=False) + '\n')
    # Clean files are exact retained substrings in source order, not rewritten health advice.
    for document in report['documents']:
        filename = Path(document['input_path']).name
        pieces = [s['text'] for s in report['sections'] if s['input_path'] == document['input_path']]
        if pieces:
            (directory / ('cleaned-' + filename)).write_text(''.join(pieces), encoding='utf-8')
    lines = ['# Step 4A local source-preparation inventory', '',
        'Review material only. No new ingestion candidates, publication, embeddings or database changes.', '',
        '| File | Raw words | Retained words | Sections |', '|---|---:|---:|---:|']
    for d in report['documents']:
        lines.append(f"| {Path(d['input_path']).name} | {d['raw_words']} | {d['retained_words']} | {d['retained_section_count']} |")
    lines += ['', '## Existing draft coverage versus supplemental discovery', '',
        'IDs in the JSON report are traceable. Candidate presence is not sufficient clinical coverage. Supplemental topic hints do not establish exact-week applicability.', '',
        '| Stage/range | Topic | Existing draft candidates | Weeks with no candidate | Supplemental topic sections |',
        '|---|---|---:|---|---:|']
    for c in report['coverage']:
        lines.append(f"| {c['stage']} {c['start']}-{c['end']} | {c['domain']} | {len(c['existing_evidence_ids'])} | {', '.join(map(str,c['weeks_without_existing_candidate'])) or 'none'} | {len(c['supplemental_discovery_ids'])} |")
    lines += ['', '## Limitations', ''] + ['- '+item for item in report['limitations']]
    (directory / 'inventory.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    # Verify the original package again: preparation must not alter any source payload.
    verified_payloads(args.package, MANIFEST_HASH)
    checksums = {p.name:sha256(p.read_bytes()) for p in sorted(directory.iterdir()) if p.is_file()}
    (directory / 'output-sha256.json').write_text(json.dumps(checksums, indent=2), encoding='utf-8')
    print(json.dumps({'summary':report['summary'], 'source_payloads_unchanged':True,
                      'report_directory':str(directory), 'catalogues':report['catalogues']}, indent=2))


if __name__ == '__main__':
    main()
