begin;

create extension if not exists pgtap with schema extensions;
select plan(33);

create or replace function pg_temp.commit_code(workspace_id uuid, command jsonb)
returns text language plpgsql as $$
begin
  perform public.stage10_commit(workspace_id,command);
  return null;
exception when others then
  return sqlstate;
end;
$$;
create or replace function pg_temp.stage10_command(
  kind text, command_key text, state_version integer, body jsonb, source_kind text
) returns jsonb language sql volatile as $$
  select jsonb_build_object(
    'schema_version','10.0.0','command_id',extensions.gen_random_uuid(),
    'idempotency_key',command_key,'expected_state_version',state_version,
    'submitted_at',clock_timestamp(),'caller','authenticated_ui',
    'provenance',jsonb_build_object('kind',source_kind,'source_id','hardening-fixture') ||
      case when source_kind='validated_plan' then jsonb_build_object('validation_policy_version','stage8-validation-v1') else '{}'::jsonb end,
    'confirmation',jsonb_build_object('confirmed',true,'confirmation_id','hardening-confirm',
      'confirmed_at',clock_timestamp(),'wording_version','stage10-confirmation-v1',
      'consent_scope','Apply this fictional hardening action'),
    'payload',body || jsonb_build_object('kind',kind)
  );
$$;

select has_function('public','stage10_commit',array['uuid','jsonb'],'public State Committer wrapper exists');
select ok(has_function_privilege('authenticated','public.stage10_commit(uuid,jsonb)','EXECUTE'),
  'authenticated role can execute only the public wrapper');
select ok(not has_function_privilege('anon','public.stage10_commit(uuid,jsonb)','EXECUTE'),
  'anonymous role cannot execute the State Committer');
select ok(not has_function_privilege('public','public.stage10_commit(uuid,jsonb)','EXECUTE'),
  'PUBLIC cannot execute the State Committer');
select ok(not has_function_privilege('authenticated','private.stage10_commit_impl(uuid,jsonb)','EXECUTE'),
  'authenticated role cannot bypass the wrapper and call the private implementation');
select is((select config from unnest((select proconfig from pg_proc where oid=
  'public.stage10_commit(uuid,jsonb)'::regprocedure)) config where config like 'search_path=%'),
  'search_path=pg_catalog','public wrapper has a fixed minimal search path');
select ok(not exists(select 1 from unnest((select proconfig from pg_proc where oid=
  'private.stage10_commit_impl(uuid,jsonb)'::regprocedure)) config where config like '%pg_temp%'),
  'private implementation search path excludes temporary schemas');

insert into auth.users(id) values
  ('c0000000-0000-0000-0000-000000000001'),
  ('c0000000-0000-0000-0000-000000000002');
insert into public.workspaces(id,owner_user_id,mode,display_name) values
  ('c1000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-000000000001','fictional_demo','Hardening A'),
  ('c1000000-0000-0000-0000-000000000002','c0000000-0000-0000-0000-000000000002','fictional_demo','Hardening B');

select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
create temporary table command_a(value jsonb);
insert into command_a select pg_temp.stage10_command(
  'follow_up_create','stage10-hardening-shared-key-0001',1,
  jsonb_build_object('task_id','c8000000-0000-0000-0000-000000000001',
    'title','Fictional follow-up A','provenance_ids',jsonb_build_array('fixture-a')),
  'validated_follow_up');
create temporary table result_a(value jsonb);
insert into result_a select public.stage10_commit(
  'c1000000-0000-0000-0000-000000000001',(select value from command_a));
select is((select value->>'status' from result_a),'committed','valid owner command commits through wrapper');
select is((public.stage10_commit('c1000000-0000-0000-0000-000000000001',
  (select value from command_a))->>'status'),'replayed','same owner, key, and payload replays one result');
select is((select count(*) from public.follow_up_tasks where workspace_id=
  'c1000000-0000-0000-0000-000000000001'),1::bigint,'replay creates no duplicate task');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  jsonb_set((select value from command_a),'{payload,title}','"Changed title"')),
  '23505','same owner and key with different payload is rejected');

reset role;
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000002',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
create temporary table command_b(value jsonb);
insert into command_b select pg_temp.stage10_command(
  'follow_up_create','stage10-hardening-shared-key-0001',1,
  jsonb_build_object('task_id','c8000000-0000-0000-0000-000000000002',
    'title','Fictional follow-up B','provenance_ids',jsonb_build_array('fixture-b')),
  'validated_follow_up');
select is((public.stage10_commit('c1000000-0000-0000-0000-000000000002',
  (select value from command_b))->>'status'),'committed','same key is independent in another owner workspace');
select is((select count(*) from public.follow_up_tasks where workspace_id=
  'c1000000-0000-0000-0000-000000000002'),1::bigint,'other owner receives only their own task');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-wrong-workspace-0001',2,
    jsonb_build_object('task_id',extensions.gen_random_uuid(),'title','Forbidden',
      'provenance_ids',jsonb_build_array('x')),'validated_follow_up')),
  '42501','wrong-workspace owner is denied without content disclosure');

reset role;
set local role anon;
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  '{}'::jsonb),'42501','anonymous caller is denied');
reset role;
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  (select value from command_a) || jsonb_build_object('workspace_id','c1000000-0000-0000-0000-000000000002')),
  '22023','JSON workspace or owner fields cannot alter authenticated scope');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  jsonb_set((select value from command_a),'{payload,table}','"plans"')),
  '22023','unknown payload field is rejected before retrieval or mutation');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  jsonb_set((select value from command_a),'{provenance,sql}','"select 1"')),
  '22023','JSON cannot select a SQL fragment or object');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-unknown-reminder-1',2,
    jsonb_build_object('task_id',extensions.gen_random_uuid(),'title','Reminder fixture',
      'provenance_ids',jsonb_build_array('x'),'reminder',jsonb_build_object(
        'opted_in',true,'scheduled_for',clock_timestamp(),'timezone','Asia/Kolkata',
        'channel','in_app','provider','fake')),'validated_follow_up')),
  '22023','unknown nested reminder field is rejected');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-oversized-title-1',2,
    jsonb_build_object('task_id',extensions.gen_random_uuid(),'title',repeat('x',70000),
      'provenance_ids',jsonb_build_array('x')),'validated_follow_up')),
  '22023','oversized JSON command is rejected');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001','[]'::jsonb),
  '22023','malformed non-object command is rejected');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('arbitrary_sql','stage10-unsupported-kind-1',2,
    jsonb_build_object('table','plans'),'user_action')),
  '22023','non-allowlisted command kind is rejected');
select is(pg_temp.commit_code('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-stale-failed-key-1',999,
    jsonb_build_object('task_id',extensions.gen_random_uuid(),'title','Stale fixture',
      'provenance_ids',jsonb_build_array('x')),'validated_follow_up')),
  'PT409','stale expected version fails inside the transactional boundary');
reset role;
select is((select count(*) from private.stage10_commit_log where workspace_id=
  'c1000000-0000-0000-0000-000000000001' and idempotency_key='stage10-stale-failed-key-1'),
  0::bigint,'failed command cannot replay as a committed result');
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select is((public.stage10_authenticated_snapshot(
  'c1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
  1,'failed validation and stale commands do not advance state version');

reset role;
insert into public.content_releases(id,corpus_version,release_fingerprint,status,published_at)
values('c2000000-0000-0000-0000-000000000001','stage10-hardening',repeat('c',64),'published',clock_timestamp());
insert into public.public_sources(source_id,release_id,title,publisher,canonical_url,jurisdiction,
  source_version,reuse_status,allowed_use,status,content_checksum)
values('SRC-STAGE10-HARDENING','c2000000-0000-0000-0000-000000000001','Hardening fixture',
  'Nestline tests','https://example.invalid/stage10-hardening',array['GLOBAL'],'1','permitted',
  array['testing'],'published',repeat('e',64));
insert into public.guideline_chunks(chunk_id,release_id,evidence_id,source_id,candidate_checksum,
  text,source_block_ids,stage,unit,range_start,range_end,jurisdiction,domains,display_slots,status)
values('CHUNK-STAGE10-HARDENING','c2000000-0000-0000-0000-000000000001','EVID-HARDENING',
  'SRC-STAGE10-HARDENING',repeat('f',64),'Controlled deletion fixture evidence.',
  array['BLOCK-HARDENING'],'pregnancy','week',24,24,array['GLOBAL'],array['nutrition'],
  array['plan'],'published');
insert into public.journey_states(id,workspace_id,stage,timing_source,gestational_week,
  gestational_day,user_confirmed,version,confirmed_at,confirmed_by_user_id,effective_date,calculation_date)
values('c3000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'pregnancy','manual_week_day',24,1,true,1,clock_timestamp(),
  'c0000000-0000-0000-0000-000000000001',current_date,current_date);
insert into public.private_documents(id,workspace_id,storage_object_path,original_filename,media_type,
  byte_size,sha256,status,contains_real_medical_data,fixture_document_key,scan_status,scan_provider,
  scan_version,scan_completed_at,review_version)
values('c4000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'c1000000-0000-0000-0000-000000000001/stage10/fixture.pdf','fixture.pdf','application/pdf',
  20,repeat('d',64),'needs_confirmation',false,'DOC-001','fixture_verified','pgtap','v1',clock_timestamp(),1);
insert into public.document_facts(id,workspace_id,document_id,field_name,value,source_page,source_text,
  confidence,status,candidate_key,fact_type,source_span,completeness,disposition,record_only,source_value_matches)
values('c5000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'c4000000-0000-0000-0000-000000000001','allergy','{"label":"sesame"}',1,'allergy: sesame',
  1,'proposed','hardening-allergy','allergy','{"page":1,"exact_text":"allergy: sesame","start":0,"end":15}',
  'complete','extract_verbatim',false,true);
insert into public.health_facts(id,workspace_id,fact_type,value,source_kind,confirmation_status,
  source_document_id,source_document_fact_id,record_only)
values('c5100000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'allergy','{"label":"sesame"}','document_extracted','confirmed',
  'c4000000-0000-0000-0000-000000000001','c5000000-0000-0000-0000-000000000001',false);
insert into private.stage10_fact_decisions(workspace_id,document_fact_id,health_fact_id,decision,
  actor_user_id,command_id,provenance,occurred_at)
values('c1000000-0000-0000-0000-000000000001','c5000000-0000-0000-0000-000000000001',
  'c5100000-0000-0000-0000-000000000001','confirm','c0000000-0000-0000-0000-000000000001',
  extensions.gen_random_uuid(),'{"kind":"document_candidate"}',clock_timestamp());
insert into public.plans(id,workspace_id,version,journey_state_id,source_release_id,status)
values('c6000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',1,
  'c3000000-0000-0000-0000-000000000001','c2000000-0000-0000-0000-000000000001','draft');
insert into public.plan_items(id,workspace_id,plan_id,evidence_ids,category,title,body,state,position)
values('c6100000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'c6000000-0000-0000-0000-000000000001',array['EVID-HARDENING'],'nutrition',
  'Fixture item','Controlled fixture','proposed',0);
insert into private.stage10_plan_dependencies(workspace_id,plan_id,plan_item_id,dependency_kind,
  entity_id,material_key)
values('c1000000-0000-0000-0000-000000000001','c6000000-0000-0000-0000-000000000001',
  'c6100000-0000-0000-0000-000000000001','allergy',
  'c5100000-0000-0000-0000-000000000001','sesame');
insert into private.stage10_plan_lifecycle_events(workspace_id,plan_id,from_status,to_status,
  actor_user_id,state_version_before,command_id,occurred_at)
values('c1000000-0000-0000-0000-000000000001','c6000000-0000-0000-0000-000000000001',
  null,'draft','c0000000-0000-0000-0000-000000000001',2,extensions.gen_random_uuid(),clock_timestamp());
insert into public.human_review_cases(id,workspace_id,state,reason,simulated,reviewer_label,
  owner_user_id,immediate_safety_completed)
values('c9000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'offered','Fictional review fixture',true,'Simulated review','c0000000-0000-0000-0000-000000000001',true);
insert into public.graph_nodes(id,workspace_id,node_type,entity_id,label) values
  ('ca000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001','fact',
    'c5100000-0000-0000-0000-000000000001','Fixture fact'),
  ('ca000000-0000-0000-0000-000000000002','c1000000-0000-0000-0000-000000000001','plan',
    'c6000000-0000-0000-0000-000000000001','Fixture plan');
insert into public.graph_edges(id,workspace_id,from_node_id,to_node_id,relation)
values('cb000000-0000-0000-0000-000000000001','c1000000-0000-0000-0000-000000000001',
  'ca000000-0000-0000-0000-000000000001','ca000000-0000-0000-0000-000000000002','TRIGGERED');

select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select lives_ok($command$delete from public.workspaces where id=
  'c1000000-0000-0000-0000-000000000001'$command$,
  'owner workspace reset completes through its explicit RLS delete boundary');
reset role;
select ok(
  not exists(select 1 from public.workspaces where id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.plans where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.plan_items where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.health_facts where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.document_facts where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.follow_up_tasks where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.human_review_cases where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.graph_nodes where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from public.graph_edges where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from private.stage10_plan_dependencies where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from private.stage10_plan_lifecycle_events where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from private.stage10_fact_decisions where workspace_id='c1000000-0000-0000-0000-000000000001')
  and not exists(select 1 from private.stage10_commit_log where workspace_id='c1000000-0000-0000-0000-000000000001'),
  'workspace A reset removes every inventoried database artifact');
select ok(exists(select 1 from public.workspaces where id='c1000000-0000-0000-0000-000000000002')
  and exists(select 1 from public.follow_up_tasks where workspace_id='c1000000-0000-0000-0000-000000000002'),
  'workspace B remains unchanged after workspace A reset');
select ok(
  not exists(select 1 from private.stage10_plan_dependencies dependency left join public.plans plan
    on plan.workspace_id=dependency.workspace_id and plan.id=dependency.plan_id where plan.id is null)
  and not exists(select 1 from public.graph_edges edge left join public.graph_nodes source
    on source.workspace_id=edge.workspace_id and source.id=edge.from_node_id where source.id is null),
  'reset leaves no orphan dependency or graph rows');

insert into public.workspaces(id,owner_user_id,mode,display_name)
values('c1000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-000000000001',
  'fictional_demo','Recreated hardening A');
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select is((public.stage10_commit('c1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-hardening-shared-key-0001',1,
    jsonb_build_object('task_id','c8000000-0000-0000-0000-000000000003',
      'title','Recreated workspace action','provenance_ids',jsonb_build_array('new-workspace')),
    'validated_follow_up'))->>'status'),'committed',
  'old idempotency result cannot replay into a recreated workspace');
reset role;
select is((select count(*) from private.stage10_commit_log where workspace_id=
  'c1000000-0000-0000-0000-000000000001'),1::bigint,
  'recreated workspace begins with a fresh idempotency ledger');
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
delete from public.workspaces where id='c1000000-0000-0000-0000-000000000001';
reset role;
select set_config('request.jwt.claim.sub','c0000000-0000-0000-0000-000000000002',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
delete from public.workspaces where id='c1000000-0000-0000-0000-000000000002';
reset role;
delete from public.guideline_chunks where release_id='c2000000-0000-0000-0000-000000000001';
delete from public.public_sources where release_id='c2000000-0000-0000-0000-000000000001';
delete from public.content_releases where id='c2000000-0000-0000-0000-000000000001';
delete from auth.users where id in ('c0000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-000000000002');
select is((select count(*) from public.workspaces where id::text like 'c1%'),0::bigint,
  'fixture cleanup leaves zero temporary workspaces');
select is((select count(*) from auth.users where id::text like 'c0%'),0::bigint,
  'fixture cleanup leaves zero temporary principals');

select * from finish();
rollback;
