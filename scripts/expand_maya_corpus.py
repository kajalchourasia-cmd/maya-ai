"""Verify Step 4B and build an immutable, review-only Step 4C authoring packet."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.services.corpus_import import build_plan, verified_payloads, sha256
from app.services.corpus_preparation import build_preparation
from app.services.corpus_expansion import build_expansion, reconcile_expansion
from scripts.prepare_maya_corpus import MANIFEST_HASH
from scripts.verify_maya_recovery import verify_recovery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--recovery-zip',type=Path,required=True)
    parser.add_argument('--recovery-root',type=Path,required=True)
    args = parser.parse_args()
    recovery = verify_recovery(args.recovery_zip,args.recovery_root)
    payloads,_ = verified_payloads(args.package,MANIFEST_HASH)
    plan = build_plan(args.package,MANIFEST_HASH)
    prepared = build_preparation(plan,payloads)
    expansion = build_expansion(plan,prepared,payloads)
    # Determinism is necessary for reproducible, version-bound review.
    if expansion != build_expansion(plan,prepared,payloads):
        raise ValueError('Non-deterministic expansion')
    reconciliation = reconcile_expansion(plan, expansion, payloads)
    directory = ROOT/'reports/local/corpus-expansion'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    directory.mkdir(parents=True,exist_ok=False)
    for name,value in [('recovery-verification',recovery),('expansion',expansion),
                       ('reconciliation',reconciliation)]:
        (directory/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
    (directory/'units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in expansion['units']),encoding='utf-8')
    lines = ['# Step 4C draft evidence expansion', '', expansion['scope'], '',
        'Broad-stage intervals are deliberately unresolved, not guessed. Explicit source ranges are not automatically the product trimester convention.', '',
        '| ID | Source / topic | Source timing | Existing overlap |', '|---|---|---|---|']
    for u in expansion['units']:
        interval = u['source_explicit_applicability']
        timing = f"{interval['start']}-{interval['end']} source weeks" if interval else 'Interval unresolved'
        lines.append(f"| {u['unit_id']} | {u['source_id']} / {u['heading']} | {timing} | {', '.join(u['overlapping_existing_evidence_ids']) or 'none by exact normalised substring'} |")
    lines += ['', '## Held for further authoring', '']
    lines += [f"- {h['source_id']} / {h['heading']}: {'; '.join(h['reasons'])}" for h in expansion['held']]
    (directory/'review-index.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    verified_payloads(args.package,MANIFEST_HASH)
    verify_recovery(args.recovery_zip,args.recovery_root)
    hashes = {p.name:sha256(p.read_bytes()) for p in directory.iterdir() if p.is_file()}
    (directory/'output-sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({'recovery':recovery,'expansion':expansion['summary'],
                      'reconciliation':reconciliation['counts'],
                      'packet_checksum':expansion['packet_checksum'],'report_directory':str(directory)},indent=2))


if __name__ == '__main__':
    main()
