-- Explicit development permission is NOT publication/clinical approval.
-- Same PostgreSQL/pgvector instance; no public API or RPC exposes this lane.
begin;
create table private.development_corpus_batches (
  packet_checksum text primary key check(packet_checksum ~ '^[a-f0-9]{64}$'),
  payload jsonb not null check((jsonb_typeof(payload)='object'
    and payload->>'authorization'='Kajal-development-indexing-not-publication-20260916'
    and payload->>'packet_checksum'=packet_checksum
    and payload->'publication_eligible'='false'::jsonb) is true),
  created_at timestamptz not null default now()
);
create table private.development_evidence (
  packet_checksum text not null references private.development_corpus_batches on delete restrict,
  evidence_id text not null,
  payload jsonb not null check((jsonb_typeof(payload)='object'
    and payload->'publication_eligible'='false'::jsonb
    and payload->>'id'=evidence_id
    and payload->>'review_status'='review_required'
    and payload->>'source_id'<>'BHC-WEEKS') is true),
  search_vector tsvector generated always as (to_tsvector('english',payload->>'search_text')) stored,
  primary key(packet_checksum,evidence_id)
);
create table private.development_vectors (
  packet_checksum text not null,
  evidence_id text not null,
  model text not null check(model='text-embedding-3-small'),
  embedding extensions.vector(1536) not null,
  receipt jsonb not null check(jsonb_typeof(receipt)='object'),
  primary key(packet_checksum,evidence_id,model),
  foreign key(packet_checksum,evidence_id) references private.development_evidence on delete restrict
);
create index development_evidence_fts on private.development_evidence using gin(search_vector);
alter table private.development_corpus_batches enable row level security;
alter table private.development_evidence enable row level security;
alter table private.development_vectors enable row level security;
revoke all on private.development_corpus_batches,private.development_evidence,private.development_vectors
  from public,anon,authenticated,service_role;
comment on table private.development_vectors is 'Operator-only real embeddings. No public retrieval or clinical release approval.';
commit;
