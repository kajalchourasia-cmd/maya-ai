"""Verify previously generated real embeddings against local pgvector, then roll back.

No model calls, no corpus changes and no clinical content. Uses a temporary table
inside one transaction and independently compares the SQL similarity with Python.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VECTOR_FILE = ROOT / "reports/local/provider-smoke/synthetic-vectors.json"
DB = "supabase_db_maya-kajal-local"


def validate_vectors(payload: dict) -> list[list[float]]:
    if payload.get("model") != "text-embedding-3-small" or payload.get("dimensions") != 1536:
        raise ValueError("Unexpected real embedding model/dimensions")
    vectors = payload.get("vectors", [])
    if len(vectors) != 3 or any(not isinstance(v, list) or len(v) != 1536 or
                              any(type(n) not in (float, int) or not math.isfinite(n) for n in v) or
                              sum(n*n for n in v) == 0 for v in vectors):
        raise ValueError("Invalid saved vectors")
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x*y for x, y in zip(a, b)) / math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))


def main() -> None:
    original = VECTOR_FILE.read_bytes()
    vectors = validate_vectors(json.loads(original))
    ledger = json.loads((VECTOR_FILE.parent / "ledger-after-key-replacement-2.json").read_text(encoding="utf-8"))
    if not any(c.get("kind") == "embedding" and c.get("success") and c.get("http_status") == 200 for c in ledger["calls"]):
        raise ValueError("Successful real embedding call evidence missing")
    inspected = subprocess.run(["docker", "inspect", DB], capture_output=True, check=True, text=True)
    container = json.loads(inspected.stdout)[0]
    if container["Config"]["Labels"].get("com.supabase.cli.project") != "maya-kajal-local":
        raise ValueError("Not the isolated Maya database")
    ports = container["NetworkSettings"]["Ports"].get("5432/tcp") or []
    if not container["State"]["Running"] or not ports or any(p["HostIp"] != "127.0.0.1" for p in ports):
        raise ValueError("Require the running loopback-bound database")
    # Numeric vectors only are interpolated; labels are fixed non-medical text.
    first, second, query = (json.dumps(v, separators=(",", ":")) for v in vectors)
    sql = f"""
begin;
set local statement_timeout='10s';
set local search_path=public,extensions;
create temporary table maya_step2_vector_probe (id text primary key, embedding vector(1536));
insert into maya_step2_vector_probe values ('garden_rose','{first}'::vector), ('garage_bicycle','{second}'::vector);
select jsonb_build_object('stored_count',(select count(*) from maya_step2_vector_probe),
    'dimensions',(select min(vector_dims(embedding)) from maya_step2_vector_probe),
    'ranked',(select jsonb_agg(r) from (select id, 1-(embedding <=> '{query}'::vector) as similarity
        from maya_step2_vector_probe order by embedding <=> '{query}'::vector) r));
rollback;
select jsonb_build_object('temporary_table_removed',to_regclass('pg_temp.maya_step2_vector_probe') is null,
    'guideline_chunks',(select count(*) from public.guideline_chunks),
    'content_releases',(select count(*) from public.content_releases),
    'migration_count',(select count(*) from supabase_migrations.schema_migrations));
"""
    result = subprocess.run(["docker", "exec", "-i", DB, "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
                             "-U", "postgres", "-d", "postgres"], input=sql, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Local SQL round trip failed; transaction connection closed without commit")
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    if len(rows) != 2:
        raise ValueError("Unexpected SQL verification output")
    retrieved, cleanup = rows
    expected = {"garden_rose": cosine(vectors[0], vectors[2]), "garage_bicycle": cosine(vectors[1], vectors[2])}
    correct = retrieved["stored_count"] == 2 and retrieved["dimensions"] == 1536 and len(retrieved["ranked"]) == 2
    correct = correct and retrieved["ranked"][0]["id"] == "garden_rose"
    correct = correct and all(abs(item["similarity"] - expected[item["id"]]) < 0.00001 for item in retrieved["ranked"])
    expected_migrations = len(list((ROOT / 'supabase/migrations').glob('*.sql')))
    correct = correct and cleanup["temporary_table_removed"] and cleanup["migration_count"] == expected_migrations
    report = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "pass": correct,
              "model": "text-embedding-3-small", "vector_file_sha256": hashlib.sha256(original).hexdigest(),
              "provider_calls_this_test": 0, "provider_cost_this_test_usd": 0,
              "retrieval": retrieved, "independent_cosine": expected, "cleanup": cleanup,
              "scope": "Real saved embeddings and temporary pgvector table; not corpus/RPC/product RAG verification"}
    path = ROOT / "reports/local/supabase-kajal/real-vector-roundtrip.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not correct:
        raise ValueError("One or more vector round-trip assertions failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Vector round trip failed: {type(exc).__name__}; no raw credentials or vectors printed")
        raise SystemExit(1)
