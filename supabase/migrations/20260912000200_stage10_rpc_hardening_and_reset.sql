-- Nestline Stage 10 hardening: strict JSONB RPC validation and complete workspace reset.
-- Forward-only and local until a separately authorized remote migration.

begin;

-- Stage 2 originally allowed direct user-reported fact CRUD. The final Stage 10
-- schema routes all active personal truth through the State Committer.
drop policy if exists "workspace owners create user-reported health_facts" on public.health_facts;
drop policy if exists "workspace owners update user-reported health_facts" on public.health_facts;
drop policy if exists "workspace owners delete user-reported health_facts" on public.health_facts;
drop policy if exists "workspace owners read health_facts" on public.health_facts;

create or replace function private.stage10_assert_object_keys(
  candidate jsonb,
  allowed_keys text[],
  required_keys text[],
  object_label text
)
returns void
language plpgsql
immutable
security invoker
set search_path = pg_catalog
as $$
declare missing_key text;
declare unexpected_key text;
begin
  if candidate is null or jsonb_typeof(candidate) <> 'object' then
    raise exception '% must be a JSON object', object_label using errcode='22023';
  end if;
  select key into unexpected_key
  from jsonb_object_keys(candidate) key
  where not (key = any(allowed_keys))
  order by key limit 1;
  if unexpected_key is not null then
    raise exception '% contains unsupported field', object_label using errcode='22023';
  end if;
  select key into missing_key
  from unnest(required_keys) key
  where not (candidate ? key)
  order by key limit 1;
  if missing_key is not null then
    raise exception '% is missing a required field', object_label using errcode='22023';
  end if;
end;
$$;
revoke all on function private.stage10_assert_object_keys(jsonb,text[],text[],text)
  from public, anon, authenticated;

-- Keep the already-tested implementation private. The public wrapper below is the
-- only executable boundary and validates the complete JSON shape before mutation.
alter function public.stage10_commit(uuid,jsonb) set schema private;
alter function private.stage10_commit(uuid,jsonb) rename to stage10_commit_impl;
alter function private.stage10_commit_impl(uuid,jsonb)
  set search_path = pg_catalog, public, private, extensions;

-- SQLSTATE 40001 means a retryable serialization failure to PostgREST. These are
-- deterministic application conflicts, so return an immediate HTTP 409 instead of
-- triggering transparent retries that can leave the client waiting indefinitely.
do $stage10_conflict_codes$
declare definition text;
begin
  select pg_get_functiondef('private.stage10_commit_impl(uuid,jsonb)'::regprocedure)
    into definition;
  definition := replace(definition, 'errcode=''40001''', 'errcode=''PT409''');
  execute definition;
end;
$stage10_conflict_codes$;
revoke all on function private.stage10_commit_impl(uuid,jsonb)
  from public, anon, authenticated;

create or replace function public.stage10_commit(
  requested_workspace_id uuid,
  requested_command jsonb
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = pg_catalog
as $$
declare command_kind text;
declare item jsonb;
declare dependency jsonb;
declare edit jsonb;
declare reminder jsonb;
declare packet jsonb;
declare normalized_command jsonb;
begin
  -- Authenticate before parsing untrusted JSON so error behavior cannot reveal
  -- whether another workspace or payload shape exists.
  if auth.uid() is null
     or coalesce(auth.role(), '') <> 'authenticated'
     or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'authenticated workspace owner access required' using errcode='42501';
  end if;
  if requested_command is null
     or jsonb_typeof(requested_command) <> 'object'
     or octet_length(requested_command::text) > 65536 then
    raise exception 'invalid Stage 10 command envelope' using errcode='22023';
  end if;

  perform private.stage10_assert_object_keys(
    requested_command,
    array['schema_version','command_id','idempotency_key','expected_state_version',
      'submitted_at','caller','provenance','confirmation','payload'],
    array['schema_version','command_id','idempotency_key','expected_state_version',
      'submitted_at','caller','provenance','confirmation','payload'],
    'Stage 10 command'
  );
  perform private.stage10_assert_object_keys(
    requested_command->'provenance',
    array['kind','source_id','trace_id','source_document_id','source_document_fact_id',
      'source_page','exact_span','exact_span_sha256','validation_policy_version'],
    array['kind','source_id'],
    'command provenance'
  );
  perform private.stage10_assert_object_keys(
    requested_command->'confirmation',
    array['confirmed','confirmation_id','confirmed_at','wording_version','consent_scope'],
    array['confirmed','confirmation_id','confirmed_at','wording_version','consent_scope'],
    'actor confirmation'
  );
  if requested_command->'confirmation'->'confirmed' <> 'true'::jsonb
     or length(trim(requested_command->'confirmation'->>'confirmation_id'))=0
     or length(trim(requested_command->'confirmation'->>'wording_version'))=0
     or length(trim(requested_command->'confirmation'->>'consent_scope'))=0 then
    raise exception 'actor confirmation is malformed or absent' using errcode='22023';
  end if;
  if requested_command->'provenance'->>'kind'='document_candidate' and (
       coalesce(requested_command->'provenance'->>'source_document_id','')=''
       or coalesce(requested_command->'provenance'->>'source_document_fact_id','')=''
       or coalesce(requested_command->'provenance'->>'source_page','')=''
       or coalesce(requested_command->'provenance'->>'exact_span','')=''
       or coalesce(requested_command->'provenance'->>'exact_span_sha256','') !~ '^[a-f0-9]{64}$'
     ) then
    raise exception 'document provenance is incomplete' using errcode='22023';
  end if;
  if requested_command->'provenance'->>'kind'<>'document_candidate' and (
       coalesce(requested_command->'provenance'->>'source_document_id','')<>''
       or coalesce(requested_command->'provenance'->>'source_document_fact_id','')<>''
       or coalesce(requested_command->'provenance'->>'source_page','')<>''
       or coalesce(requested_command->'provenance'->>'exact_span','')<>''
       or coalesce(requested_command->'provenance'->>'exact_span_sha256','')<>''
     ) then
    raise exception 'non-document provenance cannot carry a document span' using errcode='22023';
  end if;
  if requested_command->'provenance'->>'kind'='validated_plan'
     and coalesce(requested_command->'provenance'->>'validation_policy_version','')='' then
    raise exception 'validated plan provenance requires its validation policy' using errcode='22023';
  end if;
  if jsonb_typeof(requested_command->'payload') <> 'object' then
    raise exception 'command payload must be a JSON object' using errcode='22023';
  end if;
  command_kind := requested_command->'payload'->>'kind';

  if command_kind='fact_decision' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','document_fact_id','decision','corrected_value','supersedes_health_fact_id',
        'material_dependency_key'],
      array['kind','document_fact_id','decision'],'fact decision payload');
  elsif command_kind='plan_create' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','plan_id','journey_state_id','journey_week','source_release_id',
        'user_preferences','confirmed_constraints','component_agent_outputs',
        'source_evidence_ids','user_edits','items','dependencies','validation_disposition',
        'validation_trace_id','unresolved_conflict_ids'],
      array['kind','plan_id','journey_state_id','journey_week','source_release_id',
        'source_evidence_ids','items','dependencies','validation_disposition','validation_trace_id'],
      'plan create payload');
    if not exists(
      select 1 from public.journey_states state
      where state.workspace_id=requested_workspace_id and state.is_current and state.user_confirmed
    ) then
      raise exception 'onboarding_required: confirmed current journey state is missing'
        using errcode='40001';
    end if;
    for item in select value from jsonb_array_elements(coalesce(requested_command->'payload'->'items','[]')) value loop
      perform private.stage10_assert_object_keys(item,
        array['item_id','domain','title','body','day','time_window','duration_minutes',
          'optional','flexible','record_only','evidence_ids','applied_constraint_ids',
          'material_keys','excluded_material_keys','contributor'],
        array['item_id','domain','title','body','day','time_window','evidence_ids','contributor'],
        'plan item');
    end loop;
    for dependency in select value from jsonb_array_elements(coalesce(requested_command->'payload'->'dependencies','[]')) value loop
      perform private.stage10_assert_object_keys(dependency,
        array['kind','entity_id','material_key','source_item_id'],
        array['kind','entity_id','material_key'],'plan dependency');
    end loop;
    for edit in select value from jsonb_array_elements(coalesce(requested_command->'payload'->'user_edits','[]')) value loop
      perform private.stage10_assert_object_keys(edit,
        array['item_id','field','previous_value','new_value','validated','validation_trace_id'],
        array['item_id','field','previous_value','new_value','validated','validation_trace_id'],
        'validated plan edit');
    end loop;
  elsif command_kind='plan_transition' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','plan_id','from_status','to_status','replacement_plan_id'],
      array['kind','plan_id','from_status','to_status'],'plan transition payload');
  elsif command_kind='follow_up_create' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','task_id','title','due_at','provenance_ids','reminder'],
      array['kind','task_id','title','provenance_ids'],'follow-up create payload');
    reminder := requested_command->'payload'->'reminder';
    if reminder is not null and jsonb_typeof(reminder) <> 'null' then
      perform private.stage10_assert_object_keys(reminder,
        array['opted_in','scheduled_for','timezone','channel'],
        array['opted_in','scheduled_for','timezone','channel'],'reminder');
    end if;
  elsif command_kind='follow_up_transition' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','task_id','from_status','to_status'],
      array['kind','task_id','from_status','to_status'],'follow-up transition payload');
  elsif command_kind='review_create' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','case_id','reason','packet','immediate_safety_completed','safety_result'],
      array['kind','case_id','reason','packet','immediate_safety_completed','safety_result'],
      'review create payload');
    packet := requested_command->'payload'->'packet';
    perform private.stage10_assert_object_keys(packet,
      array['question','journey_state_id','confirmed_fact_ids','user_reported_context_ids',
        'exact_span_ids','trace_reference','unresolved_conflict_ids','requested_action',
        'unrelated_personal_data_included'],
      array['question','journey_state_id','trace_reference','requested_action'],
      'simulated review packet');
  elsif command_kind='review_transition' then
    perform private.stage10_assert_object_keys(requested_command->'payload',
      array['kind','case_id','from_state','to_state','simulated_response'],
      array['kind','case_id','from_state','to_state'],'review transition payload');
  else
    raise exception 'unsupported Stage 10 command kind' using errcode='22023';
  end if;

  normalized_command := requested_command;
  if command_kind='fact_decision' then
    if normalized_command->'payload'->'corrected_value' = 'null'::jsonb then
      normalized_command := normalized_command #- '{payload,corrected_value}';
    end if;
    if normalized_command->'payload'->'supersedes_health_fact_id' = 'null'::jsonb then
      normalized_command := normalized_command #- '{payload,supersedes_health_fact_id}';
    end if;
    if normalized_command->'payload'->'material_dependency_key' = 'null'::jsonb then
      normalized_command := normalized_command #- '{payload,material_dependency_key}';
    end if;
  end if;
  return private.stage10_commit_impl(requested_workspace_id, normalized_command);
end;
$$;
revoke all on function public.stage10_commit(uuid,jsonb) from public, anon, authenticated;
grant execute on function public.stage10_commit(uuid,jsonb) to authenticated;
comment on function public.stage10_commit(uuid,jsonb) is
  'Strict owner-authenticated Stage 10 JSON boundary. Validates exact shapes, then invokes the private transactional State Committer.';

-- Stage 10 history uses restrictive references during ordinary operation. Before an
-- explicitly authorized workspace deletion, remove private child ledgers and clear
-- same-workspace historical links so the existing workspace cascade can complete.
create or replace function private.stage10_prepare_workspace_delete()
returns trigger
language plpgsql
volatile
security definer
set search_path = pg_catalog
as $$
begin
  delete from private.stage10_fact_decisions decision where decision.workspace_id=old.id;
  update public.health_facts fact set supersedes_fact_id=null where fact.workspace_id=old.id;
  update public.plans plan set replacement_plan_id=null where plan.workspace_id=old.id;
  -- Plans reference journey rows with RESTRICT during ordinary lifecycle changes.
  -- Delete plans first so the subsequent workspace cascade can delete journey truth.
  delete from public.plans plan where plan.workspace_id=old.id;
  return old;
end;
$$;
revoke all on function private.stage10_prepare_workspace_delete()
  from public, anon, authenticated;
create trigger workspaces_stage10_prepare_delete
before delete on public.workspaces
for each row execute function private.stage10_prepare_workspace_delete();

commit;
