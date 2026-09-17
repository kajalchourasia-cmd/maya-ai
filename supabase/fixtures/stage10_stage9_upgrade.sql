-- Exact accepted Stage 9 schema fixture, loaded before the Stage 10 migration.
insert into auth.users(id) values ('ca000000-0000-4000-8000-000000000001');
insert into public.workspaces(id,owner_user_id,mode,display_name) values
  ('ca100000-0000-4000-8000-000000000001','ca000000-0000-4000-8000-000000000001',
   'fictional_demo','Stage 9 upgrade fixture');
insert into public.content_releases(id,corpus_version,release_fingerprint,status,published_at)
values('ca200000-0000-4000-8000-000000000001','stage10-upgrade-fixture',repeat('9',64),
  'published',clock_timestamp());
insert into public.journey_states(
  id,workspace_id,stage,timing_source,gestational_week,gestational_day,user_confirmed,
  version,confirmed_at,confirmed_by_user_id,effective_date,calculation_date
) values(
  'ca300000-0000-4000-8000-000000000001','ca100000-0000-4000-8000-000000000001',
  'pregnancy','manual_week_day',24,2,true,1,clock_timestamp(),
  'ca000000-0000-4000-8000-000000000001',current_date,current_date
);
insert into public.plans(
  id,workspace_id,version,journey_state_id,source_release_id,status,user_confirmed_at
) values(
  'ca400000-0000-4000-8000-000000000001','ca100000-0000-4000-8000-000000000001',1,
  'ca300000-0000-4000-8000-000000000001','ca200000-0000-4000-8000-000000000001',
  'saved',clock_timestamp()
);
insert into public.human_review_cases(
  id,workspace_id,state,reason,packet,simulated,consented_at,reviewed_at,reviewer_label
) values(
  'ca500000-0000-4000-8000-000000000001','ca100000-0000-4000-8000-000000000001',
  'reviewed','unsupported','{"fixture":true}',true,clock_timestamp(),clock_timestamp(),
  'Simulated review'
);
