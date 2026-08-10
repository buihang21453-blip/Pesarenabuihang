-- PES Arena V1.2.22 - Don Supabase AN TOAN
-- KHONG TRUNCATE cache/read-model. KHONG xoa user/RP/match/Zcoin/inventory.
-- Chi trim cac bang LOG cu theo retention + ANALYZE.

-- 1) Xoa log cu theo retention. Neu bang/cot created_at khong ton tai thi bo qua.
do $$
declare
  item record;
begin
  for item in
    select * from (values
      ('admin_activity_logs', 90),
      ('lucky_box_admin_audit_logs', 90),
      ('blackbox_events', 30),
      ('blackbox_incidents', 60)
    ) as x(table_name, keep_days)
  loop
    if to_regclass('public.' || item.table_name) is not null
       and exists (
         select 1 from information_schema.columns
         where table_schema='public' and table_name=item.table_name and column_name='created_at'
       ) then
      execute format(
        'delete from public.%I where created_at < now() - (%L || '' days'')::interval',
        item.table_name, item.keep_days
      );
      raise notice 'Trimmed log table: % (keep % days)', item.table_name, item.keep_days;
    end if;
  end loop;
end $$;

-- 2) Refresh planner statistics only.
analyze;

-- TUYET DOI KHONG TRUNCATE cac bang read-model/cache:
-- player_recent_form_cache, player_profile_stats_cache, player_pair_stats_cache,
-- admin_*_stats, admin_*_cache.
-- KHONG DROP clubs_import/match_series_club_actions tu dong.
