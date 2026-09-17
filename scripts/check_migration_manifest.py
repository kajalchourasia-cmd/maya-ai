"""Fail when the checked-in migration manifest differs from the migration directory."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/supabase/migration_manifest.json"
MIGRATIONS = ROOT / "supabase/migrations"


def main() -> int:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = sorted(path.name for path in MIGRATIONS.glob("*.sql"))
    rows = value["migrations"]
    recorded = [row["migration"] for row in rows]
    failures = []
    if recorded != files:
        failures.append("ordered migration list differs")
    if value["migration_count"] != len(files):
        failures.append("migration_count differs")
    for index, row in enumerate(rows, start=1):
        path = MIGRATIONS / row["migration"]
        if row["order"] != index:
            failures.append(f"order mismatch: {row['migration']}")
        if not row["purpose"].strip() or not row["expected_post_migration_schema_version"].strip():
            failures.append(f"metadata missing: {row['migration']}")
        if path.is_file() and sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            failures.append(f"checksum mismatch: {row['migration']}")
    if failures:
        print("migration manifest failed: " + "; ".join(failures))
        return 1
    print(f"migration manifest passed: {len(rows)}/{len(files)} ordered and checksum verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
