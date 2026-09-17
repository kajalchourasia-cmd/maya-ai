begin;

create extension if not exists pgtap with schema extensions;
select plan(38);

insert into auth.users(id) values
  ('b0000000-0000-0000-0000-000000000001'),
  ('b0000000-0000-0000-0000-000000000002');
insert into public.workspaces(id, owner_user_id, mode, display_name) values
  ('b1000000-0000-0000-0000-000000000001','b0000000-0000-0000-0000-000000000001','fictional_demo','Stage 10 owner fixture'),
  ('b1000000-0000-0000-0000-000000000002','b0000000-0000-0000-0000-000000000002','fictional_demo','Stage 10 other fixture');
insert into public.content_releases(id,corpus_version,release_fingerprint,status,published_at)
values('b2000000-0000-0000-0000-000000000001','stage10-test-v1',repeat('1',64),'published',clock_timestamp());
insert into public.public_sources(
  source_id,release_id,title,publisher,canonical_url,jurisdiction,source_version,
  reuse_status,allowed_use,status,content_checksum
) values('SRC-STAGE10','b2000000-0000-0000-0000-000000000001','Stage 10 fixture',
  'Nestline tests','https://example.invalid/stage10',array['GLOBAL'],'1','permitted',
  array['testing'],'published',repeat('2',64));
insert into public.guideline_chunks(
  chunk_id,release_id,evidence_id,source_id,candidate_checksum,text,source_block_ids,
  stage,unit,range_start,range_end,jurisdiction,domains,display_slots,status
) values('CHUNK-STAGE10','b2000000-0000-0000-0000-000000000001','EVID-STAGE10-001',
  'SRC-STAGE10',repeat('3',64),'Controlled fictional evidence.',array['BLOCK-STAGE10'],
  'pregnancy','week',24,24,array['GLOBAL'],array['nutrition'],array['plan'],'published');
insert into public.journey_states(
  id,workspace_id,stage,timing_source,gestational_week,gestational_day,user_confirmed,
  version,confirmed_at,confirmed_by_user_id,effective_date,calculation_date
) values('b3000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000001',
  'pregnancy','manual_week_day',24,2,true,1,clock_timestamp(),
  'b0000000-0000-0000-0000-000000000001',current_date,current_date);
insert into public.private_documents(
  id,workspace_id,storage_object_path,original_filename,media_type,byte_size,sha256,
  status,contains_real_medical_data,fixture_document_key,scan_status,scan_provider,
  scan_version,scan_completed_at,review_version
) values('b4000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000001',
  'b1000000-0000-0000-0000-000000000001/stage10/DOC-001.pdf','DOC-001.pdf',
  'application/pdf',100,repeat('a',64),'needs_confirmation',false,'DOC-001',
  'fixture_verified','pgtap','v1',clock_timestamp(),1);
insert into public.document_facts(
  id,workspace_id,document_id,field_name,value,source_page,source_text,confidence,status,
  candidate_key,fact_type,source_span,completeness,disposition,record_only,source_value_matches
) values('b5000000-0000-0000-0000-000000000001','b1000000-0000-0000-0000-000000000001',
  'b4000000-0000-0000-0000-000000000001','allergy','{"label":"sesame"}',1,
  'allergy: sesame',1.0,'proposed','p1-allergy','allergy',
  '{"page":1,"exact_text":"allergy: sesame","start":0,"end":15}',
  'complete','extract_verbatim',false,true);

create or replace function pg_temp.sqlstate_of(command text)
returns text language plpgsql as $$
begin execute command; return null;
exception when others then return sqlstate; end;
$$;

create or replace function pg_temp.stage10_command(
  kind text, command_key text, state_version integer, body jsonb, source_kind text
) returns jsonb language sql volatile as $$
  select jsonb_build_object(
    'schema_version','10.0.0','command_id',extensions.gen_random_uuid(),
    'idempotency_key',command_key,'expected_state_version',state_version,
    'submitted_at',clock_timestamp(),'caller','authenticated_ui',
    'provenance',jsonb_build_object('kind',source_kind,'source_id','pgtap-stage10') ||
      case when source_kind='validated_plan' then jsonb_build_object('validation_policy_version','stage8-validation-v1') else '{}'::jsonb end,
    'confirmation',jsonb_build_object('confirmed',true,'confirmation_id','pgtap-confirm',
      'confirmed_at',clock_timestamp(),'wording_version','stage10-confirmation-v1',
      'consent_scope','Apply this fictional action'),
    'payload',body || jsonb_build_object('kind',kind)
  );
$$;

select has_function('public','stage10_commit',array['uuid','jsonb'],
  'single Stage 10 committer exists');
select has_function('public','stage10_durable_state',array['uuid'],
  'owner-only durable state reload exists');
select has_table('public','follow_up_tasks','durable in-app follow-up table exists');
select has_table('private','stage10_plan_dependencies','private plan dependency map exists');
select has_table('private','stage10_commit_log','private idempotency ledger exists');

select set_config('request.jwt.claim.sub','b0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;

select ok((public.stage10_authenticated_snapshot(
  'b1000000-0000-0000-0000-000000000001')->>'database_derived_state')::boolean,
  'scope is derived from authenticated storage state');
select is(public.stage10_authenticated_snapshot(
  'b1000000-0000-0000-0000-000000000002'),null::jsonb,
  'owner cannot derive another workspace scope');
select is(pg_temp.sqlstate_of($command$
  update public.plans set status='archived' where workspace_id='b1000000-0000-0000-0000-000000000001'
$command$),'42501','authenticated client cannot write plans directly');
select is(pg_temp.sqlstate_of($command$
  update public.document_facts set status='confirmed' where id='b5000000-0000-0000-0000-000000000001'
$command$),'42501','authenticated client cannot bypass fact confirmation');
select is(pg_temp.sqlstate_of($command$
  update public.health_facts set confirmation_status='superseded'
  where workspace_id='b1000000-0000-0000-0000-000000000001'
$command$),'42501','authenticated client cannot bypass the State Committer for confirmed facts');

create temporary table fact_command(value jsonb);
insert into fact_command
select pg_temp.stage10_command('fact_decision','stage10-fact-confirm-0001',
  (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
  jsonb_build_object('document_fact_id','b5000000-0000-0000-0000-000000000001',
    'decision','confirm','material_dependency_key','sesame'),'document_candidate')
  || jsonb_build_object('provenance',jsonb_build_object(
    'kind','document_candidate','source_id','candidate:p1-allergy',
    'source_document_id','b4000000-0000-0000-0000-000000000001',
    'source_document_fact_id','b5000000-0000-0000-0000-000000000001',
    'source_page',1,'exact_span','allergy: sesame',
    'exact_span_sha256',encode(extensions.digest('allergy: sesame','sha256'),'hex')));
create temporary table fact_result(value jsonb);
insert into fact_result select public.stage10_commit(
  'b1000000-0000-0000-0000-000000000001',(select value from fact_command));
select is((select value->>'status' from fact_result),'committed','fact confirmation commits once');
select is((select count(*) from public.health_facts where workspace_id=
  'b1000000-0000-0000-0000-000000000001' and confirmation_status='confirmed'),1::bigint,
  'confirmed fact becomes active only after the committer');
select is((select status from public.document_facts where id=
  'b5000000-0000-0000-0000-000000000001'),'confirmed','source candidate history is retained');
select ok(not (select (value->'trace'->>'raw_personal_text_logged')::boolean from fact_result),
  'commit trace contains no raw personal text');
select is((public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  (select value from fact_command))->>'status'),'replayed','same command replays idempotently');
select is((select count(*) from public.health_facts where workspace_id=
  'b1000000-0000-0000-0000-000000000001'),1::bigint,'idempotent replay creates no duplicate fact');

create or replace function pg_temp.commit_code(workspace_id uuid, command jsonb)
returns text language plpgsql as $$
begin perform public.stage10_commit(workspace_id,command); return null;
exception when others then return sqlstate; end;
$$;

create temporary table plan_command(value jsonb);
insert into plan_command
select pg_temp.stage10_command('plan_create','stage10-plan-create-0001',
  (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
  jsonb_build_object(
    'plan_id','b6000000-0000-0000-0000-000000000001',
    'journey_state_id','b3000000-0000-0000-0000-000000000001','journey_week',24,
    'source_release_id','b2000000-0000-0000-0000-000000000001',
    'user_preferences',jsonb_build_object('window','morning'),
    'confirmed_constraints',jsonb_build_array('sesame allergy'),
    'component_agent_outputs',jsonb_build_object('nutrition','validated fixture'),
    'source_evidence_ids',jsonb_build_array('EVID-STAGE10-001'),
    'user_edits','[]'::jsonb,'validation_disposition','pass',
    'validation_trace_id','b7000000-0000-0000-0000-000000000001',
    'unresolved_conflict_ids','[]'::jsonb,
    'items',jsonb_build_array(jsonb_build_object(
      'item_id','b6100000-0000-0000-0000-000000000001','domain','nutrition',
      'title','Fictional breakfast','body','Choose a validated sesame-free option.',
      'day','monday','time_window','morning','record_only',false,
      'evidence_ids',jsonb_build_array('EVID-STAGE10-001'),
      'applied_constraint_ids',jsonb_build_array((select id::text from public.health_facts
        where workspace_id='b1000000-0000-0000-0000-000000000001' and fact_type='allergy')),
      'material_keys',jsonb_build_array('oats'),'excluded_material_keys',jsonb_build_array('sesame'),
      'contributor','nutrition-agent-v1')),
    'dependencies',jsonb_build_array(
      jsonb_build_object('kind','journey_state','entity_id','b3000000-0000-0000-0000-000000000001',
        'material_key','pregnancy-week-24'),
      jsonb_build_object('kind','allergy','entity_id',(select id::text from public.health_facts
        where workspace_id='b1000000-0000-0000-0000-000000000001' and fact_type='allergy'),
        'material_key','sesame','source_item_id','b6100000-0000-0000-0000-000000000001'),
      jsonb_build_object('kind','evidence','entity_id','EVID-STAGE10-001',
        'material_key','stage10-test-v1','source_item_id','b6100000-0000-0000-0000-000000000001')
    )
  ),'validated_plan');
create temporary table plan_result(value jsonb);
insert into plan_result select public.stage10_commit(
  'b1000000-0000-0000-0000-000000000001',(select value from plan_command));
select is((select value->>'status' from plan_result),'committed','validated plan begins as a draft');
select is((select status from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'draft','plan creation never silently saves or activates');
select ok((select owner_user_id='b0000000-0000-0000-0000-000000000001'
  and journey_state_version=1 and cardinality(source_evidence_ids)=1
  from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'saved-plan fields bind owner, journey version, and evidence');
reset role;
select is((select count(*) from private.stage10_plan_dependencies where plan_id=
  'b6000000-0000-0000-0000-000000000001'),3::bigint,'exact plan dependencies are normalized');
set local role authenticated;

select public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('plan_transition','stage10-plan-reviewed-01',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('plan_id','b6000000-0000-0000-0000-000000000001',
      'from_status','draft','to_status','user_reviewed'),'user_action'));
select is((select status from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'user_reviewed','explicit review is a separate lifecycle transition');
select ok((select reviewed_at is not null from public.plans where id=
  'b6000000-0000-0000-0000-000000000001'),'review timestamp is durable');

select public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('plan_transition','stage10-plan-saved-00001',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('plan_id','b6000000-0000-0000-0000-000000000001',
      'from_status','user_reviewed','to_status','saved'),'user_action'));
select public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('plan_transition','stage10-plan-active-0001',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('plan_id','b6000000-0000-0000-0000-000000000001',
      'from_status','saved','to_status','active'),'user_action'));
select is((select status from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'active','reviewed and saved plan can be explicitly activated');
select ok((select reviewed_at is not null and saved_at is not null and user_confirmed_at is not null
  from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'review/save confirmation timestamps are preserved');
reset role;
insert into public.document_facts(
  id,workspace_id,document_id,field_name,value,source_page,source_text,confidence,status,
  candidate_key,fact_type,source_span,completeness,disposition,record_only,source_value_matches
) values('b5000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000001',
  'b4000000-0000-0000-0000-000000000001','allergy','{"label":"sesame"}',2,
  'allergy update: sesame',1.0,'proposed','p2-allergy','allergy',
  '{"page":2,"exact_text":"allergy update: sesame","start":0,"end":22}',
  'complete','extract_verbatim',false,true);
select set_config('request.jwt.claim.sub','b0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('fact_decision','stage10-fact-change-0002',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('document_fact_id','b5000000-0000-0000-0000-000000000002',
      'decision','confirm','material_dependency_key','sesame'),'document_candidate')
  || jsonb_build_object('provenance',jsonb_build_object(
    'kind','document_candidate','source_id','candidate:p2-allergy',
    'source_document_id','b4000000-0000-0000-0000-000000000001',
    'source_document_fact_id','b5000000-0000-0000-0000-000000000002',
    'source_page',2,'exact_span','allergy update: sesame',
    'exact_span_sha256',encode(extensions.digest('allergy update: sesame','sha256'),'hex'))));
select is((select status from public.plans where id='b6000000-0000-0000-0000-000000000001'),
  'stale','relevant confirmed allergy change stales the affected plan immediately');
select is((select state from public.plan_items where id='b6100000-0000-0000-0000-000000000001'),
  'stale','relevant confirmed allergy change stales the affected item');
select ok((select count(*)>0 from public.graph_edges edge
  join public.graph_nodes source on source.id=edge.from_node_id
  join public.graph_nodes target on target.id=edge.to_node_id
  where edge.workspace_id='b1000000-0000-0000-0000-000000000001'
    and edge.relation='CONSTRAINS' and source.node_type='allergy' and target.node_type='plan_item'),
  'causal graph links the changed allergy to the affected plan item');

reset role;
insert into public.plans(
  id,workspace_id,owner_user_id,version,journey_state_id,journey_state_version,journey_week,
  source_release_id,status,reviewed_at,saved_at,user_confirmed_at
) values('b6000000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000001',
  'b0000000-0000-0000-0000-000000000001',2,'b3000000-0000-0000-0000-000000000001',1,24,
  'b2000000-0000-0000-0000-000000000001','active',clock_timestamp(),clock_timestamp(),clock_timestamp());
insert into public.plan_items(
  id,workspace_id,plan_id,evidence_ids,category,title,body,state,position
) values('b6100000-0000-0000-0000-000000000002','b1000000-0000-0000-0000-000000000001',
  'b6000000-0000-0000-0000-000000000002',array['EVID-STAGE10-001'],'nutrition',
  'Unrelated plan','Controlled fixture body','confirmed',0);
insert into private.stage10_plan_dependencies(
  workspace_id,plan_id,plan_item_id,dependency_kind,entity_id,material_key
) values('b1000000-0000-0000-0000-000000000001','b6000000-0000-0000-0000-000000000002',
  'b6100000-0000-0000-0000-000000000002','condition','condition-thyroid','thyroid');
insert into public.document_facts(
  id,workspace_id,document_id,field_name,value,source_page,source_text,confidence,status,
  candidate_key,fact_type,source_span,completeness,disposition,record_only,source_value_matches
) values('b5000000-0000-0000-0000-000000000003','b1000000-0000-0000-0000-000000000001',
  'b4000000-0000-0000-0000-000000000001','condition','{"label":"unrelated history"}',3,
  'history: unrelated',1.0,'proposed','p3-history','condition',
  '{"page":3,"exact_text":"history: unrelated","start":0,"end":18}',
  'complete','extract_verbatim',false,true);
select set_config('request.jwt.claim.sub','b0000000-0000-0000-0000-000000000001',true);
select set_config('request.jwt.claim.role','authenticated',true);
set local role authenticated;
select public.stage10_commit('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('fact_decision','stage10-unrelated-fact-1',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('document_fact_id','b5000000-0000-0000-0000-000000000003',
      'decision','confirm','material_dependency_key','unrelated-history'),'document_candidate')
  || jsonb_build_object('provenance',jsonb_build_object(
    'kind','document_candidate','source_id','candidate:p3-history',
    'source_document_id','b4000000-0000-0000-0000-000000000001',
    'source_document_fact_id','b5000000-0000-0000-0000-000000000003',
    'source_page',3,'exact_span','history: unrelated',
    'exact_span_sha256',encode(extensions.digest('history: unrelated','sha256'),'hex'))));
select is((select status from public.plans where id='b6000000-0000-0000-0000-000000000002'),
  'active','unrelated confirmed fact change does not stale an unaffected plan');
select is((select count(*) from public.plans where workspace_id='b1000000-0000-0000-0000-000000000001'),
  2::bigint,'invalidation never silently regenerates or activates another plan');
select set_config('request.jwt.claim.sub','b0000000-0000-0000-0000-000000000002',true);
select is(pg_temp.commit_code('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-cross-workspace',1,
    jsonb_build_object('task_id','b8000000-0000-0000-0000-000000000001','title','Forbidden',
      'provenance_ids',jsonb_build_array('x')),'validated_follow_up')),
  '42501','another owner cannot write this workspace');

select set_config('request.jwt.claim.sub','b0000000-0000-0000-0000-000000000001',true);
create temporary table follow_result(value jsonb);
insert into follow_result select public.stage10_commit(
  'b1000000-0000-0000-0000-000000000001',pg_temp.stage10_command(
    'follow_up_create','stage10-followup-email-1',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('task_id','b8000000-0000-0000-0000-000000000001',
      'title','Prepare fictional questions','due_at',clock_timestamp()+interval '1 day',
      'provenance_ids',jsonb_build_array('question-fixture'),
      'reminder',jsonb_build_object('opted_in',true,'scheduled_for',clock_timestamp()+interval '1 day',
        'timezone','Asia/Kolkata','channel','email')),'validated_follow_up'));
select is((select reminder_state from public.follow_up_tasks where id=
  'b8000000-0000-0000-0000-000000000001'),'external_delivery_unavailable',
  'external reminder remains truthfully unavailable');
select ok(not (select external_delivery_scheduled from public.follow_up_tasks where id=
  'b8000000-0000-0000-0000-000000000001'),'no notification is falsely scheduled');

select public.stage10_commit(
  'b1000000-0000-0000-0000-000000000001',pg_temp.stage10_command(
    'review_create','stage10-review-create-01',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('case_id','b9000000-0000-0000-0000-000000000001',
      'reason','urgent','immediate_safety_completed',true,'safety_result','urgent',
      'packet',jsonb_build_object('question','Fictional urgent handoff',
        'journey_state_id','b3000000-0000-0000-0000-000000000001',
        'confirmed_fact_ids','[]'::jsonb,'user_reported_context_ids',jsonb_build_array('symptom-fixture'),
        'exact_span_ids','[]'::jsonb,'trace_reference','b9100000-0000-0000-0000-000000000001',
        'unresolved_conflict_ids','[]'::jsonb,'requested_action','Simulated organizational review',
        'unrelated_personal_data_included',false)),'safety_trace'));
select ok((select simulated and reviewer_label='Simulated review' and immediate_safety_completed
  from public.human_review_cases where id='b9000000-0000-0000-0000-000000000001'),
  'urgent review packet is simulated and follows immediate safety');
select is(pg_temp.commit_code('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('review_transition','stage10-review-no-consent',
    (public.stage10_authenticated_snapshot('b1000000-0000-0000-0000-000000000001')->>'current_state_version')::integer,
    jsonb_build_object('case_id','b9000000-0000-0000-0000-000000000001',
      'from_state','offered','to_state','queued'),'user_action')),'22023',
  'review cannot queue before consent');

reset role;
select set_config('request.jwt.claim.role','service_role',true);
set local role service_role;
select is(pg_temp.commit_code('b1000000-0000-0000-0000-000000000001',
  pg_temp.stage10_command('follow_up_create','stage10-service-role-1',1,
    jsonb_build_object('task_id','b8000000-0000-0000-0000-000000000002','title','Forbidden',
      'provenance_ids',jsonb_build_array('x')),'validated_follow_up')),'42501',
  'ordinary Stage 10 RPC rejects service-role invocation');

reset role;
select is((select count(*) from private.stage10_plan_lifecycle_events where plan_id=
  'b6000000-0000-0000-0000-000000000001'),4::bigint,
  'plan lifecycle preserves draft, review, save, and active history');
select ok((select count(*) from private.stage10_commit_log where workspace_id=
  'b1000000-0000-0000-0000-000000000001') >= 7,
  'successful writes have an idempotency audit record');
select is((select count(*) from public.notifications where workspace_id=
  'b1000000-0000-0000-0000-000000000001'),0::bigint,
  'Stage 10 does not enable external notification automation');

select * from finish();
rollback;




