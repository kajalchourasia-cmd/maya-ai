"""Recheck local imported records and write a secret-free, no-provider-call indexing inventory."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.corpus_import import build_plan
from app.services.corpus_indexing import indexing_inventory
from scripts.import_maya_corpus import MANIFEST_HASH, require_local_database, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan(args.package, MANIFEST_HASH)
    require_local_database()
    verified = verify(plan)
    inventory = indexing_inventory(plan)
    report = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  prior_import_verification=verified['checks'], inventory=inventory,
                  provider_calls=0, database_mutations=0, production_index_ready=inventory['counts']['production_embedding_eligible']>0)
    directory = ROOT / 'reports/local/corpus-indexing'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ('readiness-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'prior_import_checks_passed':all(verified['checks'].values()),
        'counts':inventory['counts'], 'outstanding_roles':inventory['review_roles_outstanding'],
        'forbidden_sources':inventory['blocked_source_ids'],
        'profiles_without_linked_evidence':len(inventory['profiles_without_linked_evidence']),
        'report':str(path)}, indent=2))


if __name__ == '__main__':
    main()
