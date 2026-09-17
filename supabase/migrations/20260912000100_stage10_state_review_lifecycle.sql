-- Nestline Stage 10: one authenticated state-commit boundary and durable lifecycle.
-- Forward-only and local until a separately authorized remote migration.

begin;

alter table public.workspaces
  add constraint workspaces_id_owner_unique unique (id, owner_user_id);

alter table public.plans
  add column owner_user_id uuid,
  add column journey_state_version integer,
  add column journey_week integer,
  add column reviewed_at timestamptz,
  add column saved_at timestamptz,
  add column user_preferences jsonb not null default '{}',
  add column confirmed_constraints jsonb not null default '[]',
  add column component_agent_outputs jsonb not null default '{}',
  add column source_evidence_ids text[] not null default '{}',
  add column user_edits jsonb not null default '[]',
  add column replacement_plan_id uuid,
  add column validation_trace_id uuid;

update public.plans plan
set owner_user_id = workspace.owner_user_id,
    journey_state_version = state.version,
    journey_week = state.gestational_week,
    reviewed_at = case when plan.status in ('user_reviewed','saved','active','stale','replaced','archived')
      then coalesce(plan.user_confirmed_at, plan.updated_at) else null end,
    saved_at = case when plan.status in ('saved','active','stale','replaced','archived')
      then coalesce(plan.user_confirmed_at, plan.updated_at) else null end
from public.workspaces workspace, public.journey_states state
where workspace.id = plan.workspace_id
  and state.workspace_id = plan.workspace_id and state.id = plan.journey_state_id;

alter table public.plans
  alter column owner_user_id set not null,
  alter column journey_state_version set not null,
  add constraint plans_owner_workspace_fk foreign key (workspace_id, owner_user_id)
    references public.workspaces(id, owner_user_id) on delete cascade,
  add constraint plans_replacement_fk foreign key (workspace_id, replacement_plan_id)
    references public.plans(workspace_id, id) on delete restrict,
  add constraint plans_journey_state_version_check check (journey_state_version >= 1),
  add constraint plans_journey_week_check check (journey_week is null or journey_week between 1 and 42),
  add constraint plans_persisted_json_shapes_check check (
    jsonb_typeof(user_preferences) = 'object'
    and jsonb_typeof(confirmed_constraints) = 'array'
    and jsonb_typeof(component_agent_outputs) = 'object'
    and jsonb_typeof(user_edits) = 'array'
  ),
  add constraint plans_lifecycle_timestamps_check check (
    (status <> 'user_reviewed' or reviewed_at is not null)
    and (status not in ('saved','active','replaced') or reviewed_at is not null)
    and (status not in ('saved','active','replaced') or saved_at is not null)
    and (status <> 'replaced' or replacement_plan_id is not null)
  );

create or replace function private.stage10_bind_plan_scope()
returns trigger language plpgsql security definer
set search_path = public, pg_temp
as $$
begin
  select workspace.owner_user_id into new.owner_user_id
  from public.workspaces workspace where workspace.id=new.workspace_id;
  select state.version,state.gestational_week
    into new.journey_state_version,new.journey_week
  from public.journey_states state
  where state.workspace_id=new.workspace_id and state.id=new.journey_state_id;
  if new.status in ('user_reviewed','saved','active','stale','replaced','archived') then
    new.reviewed_at:=coalesce(new.reviewed_at,new.user_confirmed_at,timezone('utc',now()));
  end if;
  if new.status in ('saved','active','stale','replaced','archived') then
    new.saved_at:=coalesce(new.saved_at,new.user_confirmed_at,timezone('utc',now()));
  end if;
  return new;
end;
$$;
revoke all on function private.stage10_bind_plan_scope() from public,anon,authenticated;
create trigger plans_stage10_bind_scope before insert or update of workspace_id,owner_user_id,journey_state_id
on public.plans for each row execute function private.stage10_bind_plan_scope();
create unique index plans_one_active_per_workspace
  on public.plans(workspace_id) where status = 'active';

create table private.stage10_plan_dependencies (
  workspace_id uuid not null,
  plan_id uuid not null,
  plan_item_id uuid,
  dependency_kind text not null check (dependency_kind in (
    'journey_state','allergy','restriction','condition','symptom','medication',
    'supplement','clinician_instruction','evidence'
  )),
  entity_id text not null check (length(trim(entity_id)) between 1 and 200),
  material_key text not null check (length(trim(material_key)) between 1 and 200),
  created_at timestamptz not null default timezone('utc', now()),
  primary key (workspace_id, plan_id, dependency_kind, entity_id, material_key),
  foreign key (workspace_id, plan_id)
    references public.plans(workspace_id, id) on delete cascade,
  foreign key (workspace_id, plan_item_id)
    references public.plan_items(workspace_id, id) on delete cascade
);
create index stage10_plan_dependencies_lookup
  on private.stage10_plan_dependencies(workspace_id, dependency_kind, material_key);

create table private.stage10_plan_lifecycle_events (
  event_id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  plan_id uuid not null,
  from_status text,
  to_status text not null,
  actor_user_id uuid not null,
  state_version_before integer not null check (state_version_before >= 1),
  command_id uuid not null,
  occurred_at timestamptz not null,
  foreign key (workspace_id, plan_id)
    references public.plans(workspace_id, id) on delete cascade
);

create table private.stage10_fact_decisions (
  decision_id uuid primary key default extensions.gen_random_uuid(),
  workspace_id uuid not null,
  document_fact_id uuid not null,
  health_fact_id uuid,
  decision text not null check (decision in ('confirm','correct','reject')),
  actor_user_id uuid not null,
  command_id uuid not null,
  provenance jsonb not null,
  occurred_at timestamptz not null,
  foreign key (workspace_id, document_fact_id)
    references public.document_facts(workspace_id, id) on delete restrict,
  foreign key (workspace_id, health_fact_id)
    references public.health_facts(workspace_id, id) on delete restrict
);

create table public.follow_up_tasks (
  id uuid primary key,
  workspace_id uuid not null,
  owner_user_id uuid not null,
  title text not null check (length(trim(title)) between 1 and 500),
  status text not null check (status in ('proposed','confirmed','completed','cancelled')),
  due_at timestamptz,
  provenance_ids text[] not null check (cardinality(provenance_ids) > 0),
  reminder jsonb,
  reminder_state text not null check (reminder_state in (
    'not_requested','in_app_confirmed','external_delivery_unavailable'
  )),
  external_delivery_scheduled boolean not null default false check (not external_delivery_scheduled),
  confirmed_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (workspace_id, id),
  foreign key (workspace_id, owner_user_id)
    references public.workspaces(id, owner_user_id) on delete cascade,
  check (status <> 'confirmed' or confirmed_at is not null),
  check (reminder is null or (
    jsonb_typeof(reminder) = 'object'
    and (reminder->>'opted_in')::boolean
    and length(trim(reminder->>'scheduled_for')) > 0
    and length(trim(reminder->>'timezone')) > 0
    and reminder->>'channel' in ('in_app','email','sms','push')
  ))
);
create trigger follow_up_tasks_set_updated_at before update on public.follow_up_tasks
for each row execute function private.set_updated_at();

alter table public.human_review_cases
  add column owner_user_id uuid,
  add column trace_reference uuid,
  add column consent_record jsonb,
  add column requested_action text,
  add column immediate_safety_completed boolean not null default false,
  add column safety_result text,
  add column response_text text,
  add column response_label text;
update public.human_review_cases review
set owner_user_id = workspace.owner_user_id
from public.workspaces workspace where workspace.id = review.workspace_id;
alter table public.human_review_cases
  alter column owner_user_id set not null,
  add constraint human_review_owner_workspace_fk foreign key (workspace_id, owner_user_id)
    references public.workspaces(id, owner_user_id) on delete cascade,
  add constraint human_review_safety_result_check check (
    safety_result is null or safety_result in ('urgent','needs_clarification','non_urgent')
  ),
  add constraint human_review_simulated_truth_check check (
    simulated and coalesce(reviewer_label, '') not ilike '%doctor%'
    and coalesce(response_label, '') not ilike '%doctor%'
  ),
  add constraint human_review_response_check check (
    trace_reference is null or ((state = 'reviewed') =
      (response_text is not null and response_label = 'Simulated response'))
  );
create or replace function private.stage10_bind_review_owner()
returns trigger language plpgsql security definer
set search_path = public, pg_temp
as $$
begin
  select workspace.owner_user_id into new.owner_user_id
  from public.workspaces workspace where workspace.id=new.workspace_id;
  return new;
end;
$$;
revoke all on function private.stage10_bind_review_owner() from public,anon,authenticated;
create trigger human_review_stage10_bind_owner before insert or update of workspace_id,owner_user_id
on public.human_review_cases for each row execute function private.stage10_bind_review_owner();
create table private.stage10_commit_log (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  idempotency_key text not null,
  command_id uuid not null,
  command_kind text not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  result jsonb not null,
  actor_user_id uuid not null,
  committed_at timestamptz not null default timezone('utc', now()),
  primary key (workspace_id, idempotency_key),
  unique (workspace_id, command_id)
);

alter table public.follow_up_tasks enable row level security;
create policy "workspace owners read follow_up_tasks" on public.follow_up_tasks
  for select to authenticated using (private.is_workspace_owner(workspace_id));

drop policy if exists "workspace members manage health_facts" on public.health_facts;
drop policy if exists "workspace members manage plans" on public.plans;
drop policy if exists "workspace members manage plan_items" on public.plan_items;
drop policy if exists "workspace members manage human_review_cases" on public.human_review_cases;
create policy "workspace owners read health_facts stage10" on public.health_facts
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read plans stage10" on public.plans
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read plan_items stage10" on public.plan_items
  for select to authenticated using (private.is_workspace_owner(workspace_id));
create policy "workspace owners read human_review_cases stage10" on public.human_review_cases
  for select to authenticated using (private.is_workspace_owner(workspace_id));
revoke insert, update, delete on public.health_facts, public.plans, public.plan_items,
  public.human_review_cases, public.follow_up_tasks from authenticated;
grant select on public.follow_up_tasks to authenticated;

create or replace function private.stage10_invalidate_plans(
  requested_workspace_id uuid,
  requested_dependency_kind text,
  requested_entity_id text,
  requested_material_key text,
  requested_reason text
)
returns uuid[]
language plpgsql
volatile
security definer
set search_path = public, private, pg_temp
as $$
declare affected uuid[] := '{}'::uuid[];
declare fact_node_id uuid;
declare item_node_id uuid;
declare plan_node_id uuid;
declare row_value record;
begin
  select coalesce(array_agg(distinct plan.id order by plan.id), '{}'::uuid[])
  into affected
  from public.plans plan
  join private.stage10_plan_dependencies dependency
    on dependency.workspace_id = plan.workspace_id and dependency.plan_id = plan.id
  where plan.workspace_id = requested_workspace_id
    and plan.status in ('draft','user_reviewed','saved','active','stale')
    and dependency.dependency_kind = requested_dependency_kind
    and (dependency.entity_id = requested_entity_id
      or dependency.material_key = requested_material_key
      or dependency.material_key = '*');

  update public.plans plan
  set status = 'stale',
      stale_reasons = private.append_unique_text(plan.stale_reasons, requested_reason)
  where plan.workspace_id = requested_workspace_id and plan.id = any(affected);
  update public.plan_items item set state = 'stale'
  where item.workspace_id = requested_workspace_id and item.plan_id = any(affected);

  select id into fact_node_id from public.graph_nodes
  where workspace_id = requested_workspace_id
    and entity_id::text = requested_entity_id
    and node_type in ('fact','restriction','allergy','condition','symptom_event','medication_mention')
  order by created_at desc limit 1;
  if fact_node_id is not null then
    for row_value in
      select dependency.plan_id, dependency.plan_item_id
      from private.stage10_plan_dependencies dependency
      where dependency.workspace_id = requested_workspace_id
        and dependency.plan_id = any(affected)
        and dependency.dependency_kind = requested_dependency_kind
        and (dependency.entity_id = requested_entity_id
          or dependency.material_key = requested_material_key
          or dependency.material_key = '*')
    loop
      item_node_id := null;
      select id into item_node_id from public.graph_nodes
      where workspace_id = requested_workspace_id and node_type = 'plan_item'
        and entity_id = row_value.plan_item_id;
      if item_node_id is not null then
        insert into public.graph_edges(workspace_id, from_node_id, to_node_id, relation)
        values (requested_workspace_id, fact_node_id, item_node_id, 'CONSTRAINS')
        on conflict do nothing;
      end if;
      select id into plan_node_id from public.graph_nodes
      where workspace_id = requested_workspace_id and node_type = 'plan'
        and entity_id = row_value.plan_id;
      if item_node_id is not null and plan_node_id is not null then
        insert into public.graph_edges(workspace_id, from_node_id, to_node_id, relation)
        values (requested_workspace_id, item_node_id, plan_node_id, 'TRIGGERED')
        on conflict do nothing;
      end if;
    end loop;
  end if;
  return affected;
end;
$$;
revoke all on function private.stage10_invalidate_plans(uuid,text,text,text,text)
  from public, anon, authenticated;

create or replace function private.stage10_current_version(requested_workspace_id uuid)
returns integer language sql stable security definer
set search_path = public, pg_temp
as $$
  select coalesce((select version from public.personal_retrieval_versions
    where workspace_id = requested_workspace_id), 1);
$$;
revoke all on function private.stage10_current_version(uuid) from public, anon, authenticated;

create or replace function public.stage10_authenticated_snapshot(requested_workspace_id uuid)
returns jsonb
language sql stable security invoker
set search_path = public, private, pg_temp
as $$
  select jsonb_build_object(
    'schema_version','10.0.0',
    'workspace_id',workspace.id,
    'owner_user_id',workspace.owner_user_id,
    'care_episode_id',workspace.id,
    'current_state_version',coalesce(version.version,1),
    'current_journey_state_id',(select id from public.journey_states
      where workspace_id=workspace.id and is_current order by version desc limit 1),
    'authenticated_at',timezone('utc', now()),
    'identity_source','authenticated_session',
    'database_derived_state',true,
    'service_role_used',false
  )
  from public.workspaces workspace
  left join public.personal_retrieval_versions version on version.workspace_id=workspace.id
  where workspace.id=requested_workspace_id
    and workspace.owner_user_id=auth.uid()
    and private.is_workspace_owner(workspace.id);
$$;
revoke all on function public.stage10_authenticated_snapshot(uuid) from public, anon, authenticated;
grant execute on function public.stage10_authenticated_snapshot(uuid) to authenticated;
create or replace function public.stage10_durable_state(requested_workspace_id uuid)
returns jsonb
language sql stable security invoker
set search_path = public, private, pg_temp
as $$
  select jsonb_build_object(
    'schema_version','10.0.0',
    'workspace_id',workspace.id,
    'owner_user_id',workspace.owner_user_id,
    'state_version',coalesce(version.version,1),
    'facts',coalesce((select jsonb_agg(jsonb_build_object(
      'id',fact.id,'fact_type',fact.fact_type,'value',fact.value,
      'confirmation_status',fact.confirmation_status,'source_kind',fact.source_kind,
      'record_only',fact.record_only,'source_document_fact_id',fact.source_document_fact_id
    ) order by fact.created_at) from public.health_facts fact
      where fact.workspace_id=workspace.id and fact.confirmation_status='confirmed'
        and fact.valid_to is null),'[]'::jsonb),
    'plans',coalesce((select jsonb_agg(jsonb_build_object(
      'plan_id',plan.id,'version',plan.version,'journey_week',plan.journey_week,
      'journey_state_version',plan.journey_state_version,'status',plan.status,
      'stale_reasons',plan.stale_reasons,'reviewed_at',plan.reviewed_at,
      'saved_at',plan.saved_at,'replacement_plan_id',plan.replacement_plan_id
    ) order by plan.version) from public.plans plan
      where plan.workspace_id=workspace.id),'[]'::jsonb),
    'follow_up_tasks',coalesce((select jsonb_agg(jsonb_build_object(
      'task_id',task.id,'title',task.title,'status',task.status,'due_at',task.due_at,
      'reminder_state',task.reminder_state,'external_delivery_scheduled',task.external_delivery_scheduled
    ) order by task.created_at) from public.follow_up_tasks task
      where task.workspace_id=workspace.id),'[]'::jsonb),
    'simulated_review_cases',coalesce((select jsonb_agg(jsonb_build_object(
      'case_id',review.id,'state',review.state,'reason',review.reason,
      'simulated',review.simulated,'reviewer_label',review.reviewer_label,
      'response_label',review.response_label,'immediate_safety_completed',review.immediate_safety_completed
    ) order by review.created_at) from public.human_review_cases review
      where review.workspace_id=workspace.id),'[]'::jsonb),
    'loaded_from','storage_layer'
  )
  from public.workspaces workspace
  left join public.personal_retrieval_versions version on version.workspace_id=workspace.id
  where workspace.id=requested_workspace_id and workspace.owner_user_id=auth.uid()
    and private.is_workspace_owner(workspace.id);
$$;
revoke all on function public.stage10_durable_state(uuid) from public, anon, authenticated;
grant execute on function public.stage10_durable_state(uuid) to authenticated;
comment on function public.stage10_durable_state(uuid) is
  'Owner-only RLS-protected durable truth used after refresh/relogin; never trusts UI session state.';
create or replace function public.stage10_commit(
  requested_workspace_id uuid,
  requested_command jsonb
)
returns jsonb
language plpgsql
volatile
security definer
set search_path = public, private, extensions, pg_temp
as $$
declare
  current_version integer;
  new_version integer;
  payload jsonb;
  provenance jsonb;
  confirmation jsonb;
  command_kind text;
  expected_version integer;
  command_uuid uuid;
  requested_key text;
  payload_hash text;
  prior private.stage10_commit_log;
  candidate public.document_facts;
  old_fact public.health_facts;
  new_fact_id uuid;
  mapped_fact_type text;
  chosen_value jsonb;
  decision text;
  fact_node_id uuid;
  document_node_id uuid;
  plan_row public.plans;
  created_plan_id uuid;
  item jsonb;
  dependency jsonb;
  item_uuid uuid;
  version_number integer;
  item_position integer := 0;
  affected_plan_ids uuid[] := '{}'::uuid[];
  entity_ids uuid[] := '{}'::uuid[];
  result jsonb;
  reminder jsonb;
  reminder_state text;
  review_row public.human_review_cases;
  now_value timestamptz;
  expected_provenance text;
  changed_id uuid;
begin
  if auth.uid() is null
     or coalesce(auth.role(), '') <> 'authenticated'
     or not private.is_workspace_owner(requested_workspace_id) then
    raise exception 'authenticated workspace owner access required' using errcode='42501';
  end if;
  if jsonb_typeof(requested_command) <> 'object'
     or requested_command->>'schema_version' <> '10.0.0'
     or requested_command->>'caller' <> 'authenticated_ui'
     or coalesce((requested_command->'confirmation'->>'confirmed')::boolean,false) is not true then
    raise exception 'invalid or unconfirmed Stage 10 command' using errcode='22023';
  end if;

  command_kind := requested_command->'payload'->>'kind';
  if command_kind not in ('fact_decision','plan_create','plan_transition','follow_up_create',
      'follow_up_transition','review_create','review_transition') then
    raise exception 'unsupported Stage 10 command kind' using errcode='22023';
  end if;
  expected_provenance := case command_kind
    when 'fact_decision' then 'document_candidate'
    when 'plan_create' then 'validated_plan'
    when 'plan_transition' then 'user_action'
    when 'follow_up_create' then 'validated_follow_up'
    when 'follow_up_transition' then 'user_action'
    when 'review_create' then 'safety_trace'
    when 'review_transition' then 'user_action' end;
  if requested_command->'provenance'->>'kind' <> expected_provenance then
    raise exception 'command provenance does not match the operation' using errcode='22023';
  end if;

  command_uuid := (requested_command->>'command_id')::uuid;
  requested_key := trim(requested_command->>'idempotency_key');
  expected_version := (requested_command->>'expected_state_version')::integer;
  now_value := (requested_command->>'submitted_at')::timestamptz;
  if length(requested_key) not between 16 and 128 or expected_version < 1
     or now_value > clock_timestamp() + interval '5 minutes' then
    raise exception 'invalid idempotency, version, or timestamp' using errcode='22023';
  end if;
  payload_hash := encode(digest((requested_command - 'command_id')::text, 'sha256'), 'hex');

  select * into prior from private.stage10_commit_log log
  where log.workspace_id=requested_workspace_id and log.idempotency_key=requested_key;
  if prior.idempotency_key is not null then
    if prior.payload_sha256 <> payload_hash then
      raise exception 'idempotency key belongs to different payload' using errcode='23505';
    end if;
    return prior.result || jsonb_build_object('status','replayed','idempotent_replay',true);
  end if;

  perform 1 from public.workspaces workspace where workspace.id=requested_workspace_id
    and workspace.owner_user_id=auth.uid() for update;
  select version into current_version from public.personal_retrieval_versions versions
    where versions.workspace_id=requested_workspace_id for update;
  current_version := coalesce(current_version,1);
  if current_version <> expected_version then
    raise exception 'stale state version: expected %, current %', expected_version,current_version
      using errcode='40001', detail=jsonb_build_object('current_state_version',current_version)::text;
  end if;

  payload := requested_command->'payload';
  provenance := requested_command->'provenance';
  confirmation := requested_command->'confirmation';

  if command_kind='fact_decision' then
    select * into candidate from public.document_facts fact
    where fact.workspace_id=requested_workspace_id
      and fact.id=(payload->>'document_fact_id')::uuid for update;
    if candidate.id is null then raise exception 'document fact not found' using errcode='22023'; end if;
    if exists(select 1 from public.private_documents document
      where document.workspace_id=requested_workspace_id and document.id=candidate.document_id
        and (document.contains_real_medical_data or document.scan_status<>'fixture_verified')) then
      raise exception 'fact is outside the controlled fictional confirmation boundary' using errcode='55000';
    end if;
    if provenance->>'source_document_id' <> candidate.document_id::text
       or provenance->>'source_document_fact_id' <> candidate.id::text
       or (provenance->>'source_page')::integer is distinct from candidate.source_page
       or provenance->>'exact_span' is distinct from candidate.source_text
       or provenance->>'exact_span_sha256' <> encode(digest(candidate.source_text,'sha256'),'hex') then
      raise exception 'document provenance mismatch' using errcode='22023';
    end if;
    decision := payload->>'decision';
    if candidate.status='conflict' and decision<>'reject' then
      raise exception 'unresolved conflict cannot be confirmed' using errcode='22023';
    end if;
    if candidate.status not in ('proposed','conflict') or decision not in ('confirm','correct','reject') then
      raise exception 'invalid fact decision transition' using errcode='22023';
    end if;
    if decision='reject' then
      update public.document_facts set status='rejected', decided_at=now_value,
        decided_by_user_id=auth.uid() where id=candidate.id;
      update public.medication_mentions set status='rejected', decided_at=now_value,
        decided_by_user_id=auth.uid() where workspace_id=requested_workspace_id
        and document_id=candidate.document_id and candidate_key=candidate.candidate_key;
      entity_ids:=array[candidate.id];
    else
      if (decision='correct') <> (payload ? 'corrected_value') then
        raise exception 'correction value shape is invalid' using errcode='22023';
      end if;
      chosen_value := case when decision='correct' then payload->'corrected_value' else candidate.value end;
      if payload ? 'supersedes_health_fact_id' then
        select * into old_fact from public.health_facts fact
        where fact.workspace_id=requested_workspace_id
          and fact.id=(payload->>'supersedes_health_fact_id')::uuid
          and fact.confirmation_status='confirmed' and fact.valid_to is null for update;
        if old_fact.id is null then raise exception 'superseded fact is not current' using errcode='22023'; end if;
      end if;
      mapped_fact_type := case candidate.fact_type
        when 'allergy' then 'allergy' when 'condition' then 'medical_history'
        when 'medication' then 'medication'
        when 'medication_instruction' then 'clinician_instruction'
        when 'restriction' then 'clinician_instruction'
        when 'clinician' then 'clinician_instruction' else 'other' end;
      insert into public.health_facts(
        workspace_id,fact_type,value,source_kind,confirmation_status,
        source_document_id,source_document_fact_id,supersedes_fact_id,record_only,provenance
      ) values (
        requested_workspace_id,mapped_fact_type,
        jsonb_build_object('field',candidate.field_name,'value',chosen_value,
          'source_text',candidate.source_text,'record_only',candidate.record_only),
        'document_extracted','confirmed',candidate.document_id,candidate.id,old_fact.id,
        candidate.record_only,provenance || jsonb_build_object('confirmed_at',now_value)
      ) returning id into new_fact_id;
      if old_fact.id is not null then
        update public.health_facts set confirmation_status='superseded',valid_to=now_value
        where workspace_id=requested_workspace_id and id=old_fact.id;
      end if;
      update public.document_facts set status='confirmed',
        edited_value=case when decision='correct' then chosen_value else null end,
        confirmed_at=now_value,decided_at=now_value,decided_by_user_id=auth.uid(),
        committed_health_fact_id=new_fact_id where id=candidate.id;
      update public.medication_mentions set status='confirmed',decided_at=now_value,
        decided_by_user_id=auth.uid() where workspace_id=requested_workspace_id
        and document_id=candidate.document_id and candidate_key=candidate.candidate_key;
      insert into public.graph_nodes(workspace_id,node_type,entity_id,label,source_document_id)
      values (requested_workspace_id,
        case when mapped_fact_type='allergy' then 'allergy'
             when mapped_fact_type='medical_history' then 'condition'
             when candidate.fact_type='restriction' then 'restriction' else 'fact' end,
        new_fact_id,left(candidate.field_name||': '||coalesce(chosen_value#>>'{}','confirmed'),300),candidate.document_id)
      returning id into fact_node_id;
      select id into document_node_id from public.graph_nodes node
        where node.workspace_id=requested_workspace_id and node.node_type='document'
          and node.entity_id=candidate.document_id;
      if document_node_id is null then
        insert into public.graph_nodes(workspace_id,node_type,entity_id,label,source_document_id)
        select requested_workspace_id,'document',document.id,document.original_filename,document.id
        from public.private_documents document where document.id=candidate.document_id
        returning id into document_node_id;
      end if;
      insert into public.graph_edges(workspace_id,from_node_id,to_node_id,relation)
      values(requested_workspace_id,fact_node_id,document_node_id,'EXTRACTED_FROM') on conflict do nothing;
      affected_plan_ids := private.stage10_invalidate_plans(
        requested_workspace_id,
        case mapped_fact_type when 'allergy' then 'allergy'
          when 'medical_history' then 'condition' when 'medication' then 'medication'
          when 'clinician_instruction' then 'clinician_instruction' else 'condition' end,
        new_fact_id::text,coalesce(payload->>'material_dependency_key',chosen_value->>'label','*'),
        'confirmed_fact_changed:'||new_fact_id::text);
      entity_ids:=array[candidate.id,new_fact_id];
    end if;
    insert into private.stage10_fact_decisions(
      workspace_id,document_fact_id,health_fact_id,decision,actor_user_id,command_id,provenance,occurred_at
    ) values(requested_workspace_id,candidate.id,new_fact_id,decision,auth.uid(),command_uuid,provenance,now_value);


  elsif command_kind='plan_create' then
    if payload->>'validation_disposition'<>'pass'
       or jsonb_array_length(coalesce(payload->'unresolved_conflict_ids','[]'))>0
       or jsonb_typeof(payload->'items')<>'array'
       or jsonb_typeof(payload->'dependencies')<>'array'
       or jsonb_array_length(payload->'items') not between 1 and 100
       or jsonb_array_length(payload->'dependencies') not between 1 and 200 then
      raise exception 'unvalidated, conflicted, or malformed plan draft' using errcode='22023';
    end if;
    if exists(
      select 1 from public.health_facts fact
      where fact.workspace_id=requested_workspace_id
        and fact.confirmation_status='confirmed' and fact.valid_to is null
        and fact.fact_type in ('allergy','dietary_restriction','clinician_instruction')
        and not exists(
          select 1 from jsonb_array_elements(payload->'dependencies') as dep_element
          where dep_element->>'kind'=case fact.fact_type
            when 'allergy' then 'allergy'
            when 'dietary_restriction' then 'restriction'
            else 'clinician_instruction' end
            and lower(dep_element->>'material_key')=
              lower(coalesce(fact.value->>'label',fact.value->'value'->>'label',''))
        )
    ) then
      raise exception 'plan omitted an active confirmed constraint dependency' using errcode='22023';
    end if;
    if jsonb_typeof(coalesce(payload->'user_edits','[]'))<>'array' or exists(
      select 1 from jsonb_array_elements(coalesce(payload->'user_edits','[]')) edit
      where coalesce((edit->>'validated')::boolean,false)=false
        or edit->>'field' not in ('title','body','day','time_window','duration_minutes')
        or coalesce(edit->>'validation_trace_id','') !~ '^[0-9a-f-]{36}$'
        or not exists(
          select 1 from jsonb_array_elements(payload->'items') value
          where value->>'item_id'=edit->>'item_id'
            and value->>(edit->>'field')=edit->>'new_value'
        )
    ) then
      raise exception 'plan user edits are not validated against the persisted item' using errcode='22023';
    end if;
    if not exists(select 1 from public.journey_states state
      where state.workspace_id=requested_workspace_id
        and state.id=(payload->>'journey_state_id')::uuid and state.is_current and state.user_confirmed) then
      raise exception 'plan journey state is not current and confirmed' using errcode='40001';
    end if;
    if exists(select 1 from jsonb_array_elements(payload->'items') value
      where jsonb_array_length(coalesce(value->'evidence_ids','[]'))=0
        or (lower(coalesce(value->>'title','')||' '||coalesce(value->>'body',''))
          ~ '(medicine|medication|supplement)' and coalesce((value->>'record_only')::boolean,false)=false)
        or exists(
          select 1 from public.health_facts fact
          where fact.workspace_id=requested_workspace_id
            and fact.fact_type in ('allergy','dietary_restriction','clinician_instruction')
            and fact.confirmation_status='confirmed' and fact.valid_to is null
            and lower(coalesce(fact.value->>'label',fact.value->'value'->>'label','')) in
              (select lower(material) from jsonb_array_elements_text(coalesce(value->'material_keys','[]')) as materials(material))
            and lower(coalesce(fact.value->>'label',fact.value->'value'->>'label','')) not in
              (select lower(material) from jsonb_array_elements_text(coalesce(value->'excluded_material_keys','[]')) as materials(material))
        )) then
      raise exception 'plan item failed evidence or medication-boundary validation' using errcode='22023';
    end if;
    created_plan_id:=(payload->>'plan_id')::uuid;
    select coalesce(max(plan.version),0)+1 into version_number from public.plans plan
      where plan.workspace_id=requested_workspace_id;
    insert into public.plans(
      id,workspace_id,owner_user_id,version,journey_state_id,journey_state_version,
      journey_week,source_release_id,status,user_preferences,confirmed_constraints,
      component_agent_outputs,source_evidence_ids,user_edits,validation_trace_id
    ) select created_plan_id,requested_workspace_id,auth.uid(),version_number,state.id,state.version,
      (payload->>'journey_week')::integer,(payload->>'source_release_id')::uuid,'draft',
      payload->'user_preferences',payload->'confirmed_constraints',payload->'component_agent_outputs',
      array(select jsonb_array_elements_text(payload->'source_evidence_ids')),
      payload->'user_edits',(payload->>'validation_trace_id')::uuid
      from public.journey_states state where state.workspace_id=requested_workspace_id
        and state.id=(payload->>'journey_state_id')::uuid;
    insert into public.graph_nodes(workspace_id,node_type,entity_id,label)
      values(requested_workspace_id,'plan',created_plan_id,'Validated draft plan version '||version_number);
    item_position := 0;
    for item in select value from jsonb_array_elements(payload->'items') value loop
      item_uuid:=(item->>'item_id')::uuid;
      insert into public.plan_items(
        id,workspace_id,plan_id,evidence_ids,confirmed_fact_ids,category,title,body,state,position
      ) values(item_uuid,requested_workspace_id,created_plan_id,
        array(select jsonb_array_elements_text(item->'evidence_ids')),
        array(select value::uuid from jsonb_array_elements_text(coalesce(item->'applied_constraint_ids','[]')) value
          where value ~ '^[0-9a-f-]{36}$'),
        item->>'domain',item->>'title',item->>'body','proposed',item_position);
      item_position := item_position + 1;
      insert into public.graph_nodes(workspace_id,node_type,entity_id,label)
        values(requested_workspace_id,'plan_item',item_uuid,left(item->>'title',300));
    end loop;
    for dependency in select value from jsonb_array_elements(payload->'dependencies') value loop
      insert into private.stage10_plan_dependencies(
        workspace_id,plan_id,plan_item_id,dependency_kind,entity_id,material_key
      ) values(requested_workspace_id,created_plan_id,nullif(dependency->>'source_item_id','')::uuid,
        dependency->>'kind',dependency->>'entity_id',dependency->>'material_key');
    end loop;
    insert into private.stage10_plan_lifecycle_events(
      workspace_id,plan_id,from_status,to_status,actor_user_id,state_version_before,command_id,occurred_at
    ) values(requested_workspace_id,created_plan_id,null,'draft',auth.uid(),current_version,command_uuid,now_value);
    entity_ids:=array[created_plan_id];

  elsif command_kind='plan_transition' then
    select * into plan_row from public.plans plan where plan.workspace_id=requested_workspace_id
      and plan.id=(payload->>'plan_id')::uuid for update;
    if plan_row.id is null or plan_row.status<>payload->>'from_status' then
      raise exception 'plan not found or stale lifecycle state' using errcode='40001';
    end if;
    if not ((plan_row.status='draft' and payload->>'to_status' in ('user_reviewed','archived'))
      or (plan_row.status='user_reviewed' and payload->>'to_status' in ('saved','archived'))
      or (plan_row.status='saved' and payload->>'to_status' in ('active','replaced','archived'))
      or (plan_row.status='active' and payload->>'to_status' in ('replaced','archived'))
      or (plan_row.status='stale' and payload->>'to_status' in ('replaced','archived'))
      or (plan_row.status='replaced' and payload->>'to_status'='archived')) then
      raise exception 'invalid plan lifecycle transition' using errcode='22023';
    end if;
    if payload->>'to_status' in ('saved','active') and (
      plan_row.stale_reasons<>'{}' or not exists(select 1 from public.journey_states state
        where state.workspace_id=requested_workspace_id and state.id=plan_row.journey_state_id and state.is_current)) then
      raise exception 'stale plan cannot be saved or activated' using errcode='40001';
    end if;
    if payload->>'to_status'='saved' and plan_row.reviewed_at is null then
      raise exception 'explicit user review is required before save' using errcode='22023';
    end if;
    if payload->>'to_status'='replaced' and not exists(select 1 from public.plans plan
      where plan.workspace_id=requested_workspace_id and plan.id=(payload->>'replacement_plan_id')::uuid
        and plan.status in ('saved','active')) then
      raise exception 'replacement plan must already be saved' using errcode='22023';
    end if;
    update public.plans set status=payload->>'to_status',
      reviewed_at=case when payload->>'to_status'='user_reviewed' then now_value else reviewed_at end,
      saved_at=case when payload->>'to_status'='saved' then now_value else saved_at end,
      user_confirmed_at=case when payload->>'to_status' in ('saved','active') then now_value else user_confirmed_at end,
      replacement_plan_id=case when payload->>'to_status'='replaced'
        then (payload->>'replacement_plan_id')::uuid else replacement_plan_id end
      where workspace_id=requested_workspace_id and id=plan_row.id;
    insert into private.stage10_plan_lifecycle_events(
      workspace_id,plan_id,from_status,to_status,actor_user_id,state_version_before,command_id,occurred_at
    ) values(requested_workspace_id,plan_row.id,plan_row.status,payload->>'to_status',
      auth.uid(),current_version,command_uuid,now_value);
    entity_ids:=array[plan_row.id];

  elsif command_kind='follow_up_create' then
    reminder:=payload->'reminder';
    if jsonb_array_length(coalesce(payload->'provenance_ids','[]'))=0 then
      raise exception 'follow-up requires provenance' using errcode='22023';
    end if;
    if reminder is not null and (coalesce((reminder->>'opted_in')::boolean,false)=false
      or coalesce(reminder->>'scheduled_for','')='' or coalesce(reminder->>'timezone','')=''
      or reminder->>'channel' not in ('in_app','email','sms','push')) then
      raise exception 'reminder requires explicit schedule, timezone, and channel consent' using errcode='22023';
    end if;
    reminder_state:=case when reminder is null then 'not_requested'
      when reminder->>'channel'='in_app' then 'in_app_confirmed'
      else 'external_delivery_unavailable' end;
    insert into public.follow_up_tasks(
      id,workspace_id,owner_user_id,title,status,due_at,provenance_ids,reminder,
      reminder_state,external_delivery_scheduled,confirmed_at
    ) values((payload->>'task_id')::uuid,requested_workspace_id,auth.uid(),payload->>'title',
      'confirmed',nullif(payload->>'due_at','')::timestamptz,
      array(select jsonb_array_elements_text(payload->'provenance_ids')),
      reminder,reminder_state,false,now_value);
    entity_ids:=array[(payload->>'task_id')::uuid];

  elsif command_kind='follow_up_transition' then
    update public.follow_up_tasks task set status=payload->>'to_status'
    where task.workspace_id=requested_workspace_id and task.id=(payload->>'task_id')::uuid
      and task.status=payload->>'from_status'
      and ((task.status='proposed' and payload->>'to_status' in ('confirmed','cancelled'))
        or (task.status='confirmed' and payload->>'to_status' in ('completed','cancelled')))
    returning id into changed_id;
    if changed_id is null then raise exception 'invalid follow-up transition' using errcode='22023'; end if;
    entity_ids:=array[changed_id];

  elsif command_kind='review_create' then
    if jsonb_typeof(payload->'packet')<>'object'
       or coalesce((payload->'packet'->>'unrelated_personal_data_included')::boolean,false)
       or jsonb_array_length(coalesce(payload->'packet'->'confirmed_fact_ids','[]'))>12
       or jsonb_array_length(coalesce(payload->'packet'->'user_reported_context_ids','[]'))>12
       or jsonb_array_length(coalesce(payload->'packet'->'exact_span_ids','[]'))>12
       or (payload->>'reason'='urgent' and coalesce((payload->>'immediate_safety_completed')::boolean,false)=false) then
      raise exception 'review packet is not minimal or safety-first' using errcode='22023';
    end if;
    insert into public.human_review_cases(
      id,workspace_id,owner_user_id,state,reason,packet,simulated,trace_reference,
      requested_action,immediate_safety_completed,safety_result,reviewer_label
    ) values((payload->>'case_id')::uuid,requested_workspace_id,auth.uid(),'offered',
      payload->>'reason',payload->'packet',true,(payload->'packet'->>'trace_reference')::uuid,
      payload->'packet'->>'requested_action',(payload->>'immediate_safety_completed')::boolean,
      payload->>'safety_result','Simulated review');
    entity_ids:=array[(payload->>'case_id')::uuid];

  elsif command_kind='review_transition' then
    select * into review_row from public.human_review_cases review
      where review.workspace_id=requested_workspace_id and review.id=(payload->>'case_id')::uuid for update;
    if review_row.id is null or review_row.state<>payload->>'from_state'
      or not ((review_row.state='offered' and payload->>'to_state' in ('consented','declined','unavailable','timed_out'))
        or (review_row.state='consented' and payload->>'to_state' in ('queued','declined','unavailable'))
        or (review_row.state='queued' and payload->>'to_state' in ('reviewed','unavailable','timed_out'))
        or (review_row.state='reviewed' and payload->>'to_state'='resumed')) then
      raise exception 'invalid simulated review transition' using errcode='22023';
    end if;
    if payload->>'to_state'='reviewed' and coalesce(payload->>'simulated_response','')='' then
      raise exception 'reviewed simulation requires a response' using errcode='22023';
    end if;
    update public.human_review_cases set state=payload->>'to_state',
      consented_at=case when payload->>'to_state'='consented' then now_value else consented_at end,
      consent_record=case when payload->>'to_state'='consented' then confirmation else consent_record end,
      reviewed_at=case when payload->>'to_state'='reviewed' then now_value else reviewed_at end,
      response_text=case when payload->>'to_state'='reviewed' then payload->>'simulated_response' else response_text end,
      response_label=case when payload->>'to_state'='reviewed' then 'Simulated response' else response_label end
      where workspace_id=requested_workspace_id and id=review_row.id;
    entity_ids:=array[review_row.id];
  end if;

  select coalesce(version,1) into new_version from public.personal_retrieval_versions versions
    where versions.workspace_id=requested_workspace_id;
  result:=jsonb_build_object(
    'schema_version','10.0.0','command_id',command_uuid,'status','committed',
    'command_kind',command_kind,'old_state_version',current_version,
    'new_state_version',new_version,'entity_ids',to_jsonb(entity_ids),
    'affected_plan_ids',to_jsonb(affected_plan_ids),
    'external_delivery_scheduled',false,'idempotent_replay',false,
    'trace',jsonb_build_object(
      'committer_version','stage10-state-committer-v1','workspace_id',requested_workspace_id,
      'actor_user_id',auth.uid(),'command_kind',command_kind,
      'idempotency_key_hash',encode(digest(requested_key,'sha256'),'hex'),
      'old_state_version',current_version,'new_state_version',new_version,
      'generation_call_count',0,'direct_agent_write',false,'service_role_used',false,
      'raw_personal_text_logged',false,'committed_at',now_value
    )
  );
  insert into private.stage10_commit_log(
    workspace_id,idempotency_key,command_id,command_kind,payload_sha256,result,actor_user_id,committed_at
  ) values(requested_workspace_id,requested_key,command_uuid,command_kind,payload_hash,result,auth.uid(),now_value);
  return result;
end;
$$;

revoke all on function public.stage10_commit(uuid,jsonb) from public, anon, authenticated;
grant execute on function public.stage10_commit(uuid,jsonb) to authenticated;
comment on function public.stage10_commit(uuid,jsonb) is
  'Single owner-authenticated, versioned, idempotent Stage 10 write boundary. Direct table writes remain unavailable to ordinary clients.';


create or replace function private.stage10_invalidate_journey_change()
returns trigger language plpgsql volatile security definer
set search_path = public, private, pg_temp
as $$
begin
  if new.is_current then
    update public.plans plan set status='stale',
      stale_reasons=private.append_unique_text(plan.stale_reasons,
        'journey_state_changed:'||new.id::text)
    where plan.workspace_id=new.workspace_id and plan.journey_state_id<>new.id
      and plan.status in ('draft','user_reviewed','saved','active');
    update public.plan_items item set state='stale'
    where item.workspace_id=new.workspace_id and exists(
      select 1 from public.plans plan where plan.workspace_id=item.workspace_id
        and plan.id=item.plan_id and plan.status='stale'
        and 'journey_state_changed:'||new.id::text=any(plan.stale_reasons));
  end if;
  return new;
end;
$$;

create or replace function private.stage10_invalidate_fact_change()
returns trigger language plpgsql volatile security definer
set search_path = public, private, pg_temp
as $$
declare dependency_kind text;
declare material_key text;
declare affected uuid[];
begin
  if new.confirmation_status='confirmed' and new.valid_to is null then
    dependency_kind:=case new.fact_type when 'allergy' then 'allergy'
      when 'dietary_restriction' then 'restriction'
      when 'medical_history' then 'condition'
      when 'medication' then 'medication'
      when 'clinician_instruction' then 'clinician_instruction' else 'condition' end;
    material_key:=coalesce(new.value->>'label',new.value->'value'->>'label','*');
    affected:=private.stage10_invalidate_plans(new.workspace_id,dependency_kind,
      new.id::text,material_key,'confirmed_fact_changed:'||new.id::text);
  elsif tg_op='UPDATE' and old.confirmation_status='confirmed'
    and new.confirmation_status='superseded' then
    dependency_kind:=case old.fact_type when 'allergy' then 'allergy'
      when 'dietary_restriction' then 'restriction'
      when 'medical_history' then 'condition'
      when 'medication' then 'medication'
      when 'clinician_instruction' then 'clinician_instruction' else 'condition' end;
    affected:=private.stage10_invalidate_plans(old.workspace_id,dependency_kind,
      old.id::text,'*','confirmed_fact_superseded:'||old.id::text);
  end if;
  return new;
end;
$$;

create or replace function private.stage10_invalidate_symptom_change()
returns trigger language plpgsql volatile security definer
set search_path = public, private, pg_temp
as $$
declare affected uuid[];
begin
  if new.user_confirmed then
    affected:=private.stage10_invalidate_plans(new.workspace_id,'symptom',new.id::text,
      '*','symptom_state_changed:'||new.id::text);
  end if;
  return new;
end;
$$;

create or replace function private.stage10_invalidate_medication_change()
returns trigger language plpgsql volatile security definer
set search_path = public, private, pg_temp
as $$
declare affected uuid[];
begin
  if new.status='confirmed' then
    affected:=private.stage10_invalidate_plans(new.workspace_id,'medication',new.id::text,
      '*','medication_record_changed:'||new.id::text);
  end if;
  return new;
end;
$$;

create or replace function private.stage10_invalidate_evidence_change()
returns trigger language plpgsql volatile security definer
set search_path = public, private, pg_temp
as $$
begin
  if new.status in ('retired','reviewed') and old.status is distinct from new.status then
    update public.plans plan set status='stale',
      stale_reasons=private.append_unique_text(plan.stale_reasons,
        'evidence_changed:'||new.evidence_id)
    where plan.status in ('draft','user_reviewed','saved','active') and exists(
      select 1 from private.stage10_plan_dependencies dependency
      where dependency.workspace_id=plan.workspace_id and dependency.plan_id=plan.id
        and dependency.dependency_kind='evidence' and dependency.entity_id=new.evidence_id);
    update public.plan_items item set state='stale'
    where exists(select 1 from public.plans plan where plan.id=item.plan_id
      and plan.workspace_id=item.workspace_id and plan.status='stale'
      and 'evidence_changed:'||new.evidence_id=any(plan.stale_reasons));
  end if;
  return new;
end;
$$;

revoke all on function private.stage10_invalidate_journey_change() from public,anon,authenticated;
revoke all on function private.stage10_invalidate_fact_change() from public,anon,authenticated;
revoke all on function private.stage10_invalidate_symptom_change() from public,anon,authenticated;
revoke all on function private.stage10_invalidate_medication_change() from public,anon,authenticated;
revoke all on function private.stage10_invalidate_evidence_change() from public,anon,authenticated;

create trigger journey_states_stage10_invalidation after insert or update of is_current
on public.journey_states for each row execute function private.stage10_invalidate_journey_change();
create trigger health_facts_stage10_invalidation after insert or update of confirmation_status,valid_to
on public.health_facts for each row execute function private.stage10_invalidate_fact_change();
create trigger symptom_events_stage10_invalidation after insert or update of user_confirmed
on public.symptom_events for each row execute function private.stage10_invalidate_symptom_change();
create trigger medication_mentions_stage10_invalidation after insert or update of status
on public.medication_mentions for each row execute function private.stage10_invalidate_medication_change();
create trigger guideline_chunks_stage10_invalidation after update of status
on public.guideline_chunks for each row execute function private.stage10_invalidate_evidence_change();
commit;
















