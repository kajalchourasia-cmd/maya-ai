do $$
begin
  if not exists(select 1 from public.plans where id='ca400000-0000-4000-8000-000000000001'
    and owner_user_id='ca000000-0000-4000-8000-000000000001'
    and journey_state_version=1 and journey_week=24 and reviewed_at is not null
    and saved_at is not null and status='saved') then
    raise exception 'Stage 9 plan was not backfilled into the Stage 10 lifecycle';
  end if;
  if not exists(select 1 from public.human_review_cases
    where id='ca500000-0000-4000-8000-000000000001'
      and owner_user_id='ca000000-0000-4000-8000-000000000001'
      and simulated and reviewer_label='Simulated review') then
    raise exception 'Stage 9 simulated review did not preserve truthful ownership/status';
  end if;
  if to_regprocedure('public.stage10_commit(uuid,jsonb)') is null
     or to_regprocedure('public.stage10_authenticated_snapshot(uuid)') is null then
    raise exception 'Stage 10 RPC surface is missing after upgrade';
  end if;
  if not exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='private' and c.relname='stage10_plan_dependencies') then
    raise exception 'Stage 10 dependency storage is missing after upgrade';
  end if;
end;
$$;
