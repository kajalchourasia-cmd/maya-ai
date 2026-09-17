-- Preserve recovered review-required evidence without promoting it to reviewed.
-- Existing published-only RLS and retrieval functions are deliberately unchanged.
begin;

alter table public.public_sources drop constraint public_sources_status_check;
alter table public.public_sources add constraint public_sources_status_check
  check (status in ('review_required', 'reviewed', 'published', 'retired'));
alter table public.guideline_chunks drop constraint guideline_chunks_status_check;
alter table public.guideline_chunks add constraint guideline_chunks_status_check
  check (status in ('review_required', 'reviewed', 'published', 'retired'));

-- Lossless operator-only import receipt. Includes original candidate metadata,
-- source governance, raw historical dry-run flags, and independently supplied reviews.
-- This is provenance, not a second retrieval store or a public-release approval.
create table private.corpus_import_receipts (
  import_fingerprint text primary key check (import_fingerprint ~ '^[a-f0-9]{64}$'),
  release_id uuid not null references public.content_releases(id) on delete restrict,
  package_manifest_sha256 text not null check (package_manifest_sha256 ~ '^[a-f0-9]{64}$'),
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  created_at timestamptz not null default timezone('utc', now())
);
alter table private.corpus_import_receipts enable row level security;
revoke all on private.corpus_import_receipts from public, anon, authenticated, service_role;
comment on table private.corpus_import_receipts is
  'Local/operator corpus-import provenance; never grants publication or clinical approval.';

commit;
