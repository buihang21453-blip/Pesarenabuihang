-- PES Arena - Don Supabase AN TOAN
-- Muc tieu: dọn CACHE + log cu. KHONG DROP bang, KHONG xoa user/RP/match.
-- Chay mot lan trong Supabase SQL Editor sau khi da doc cleanup_preview.py.

-- 1) Clear cache/read-model data. Bang van duoc GIU NGUYEN.
do $$
declare
  t text;
  cache_tables text[] := array[
    'player_pair_stats_cache',
    'player_profile_stats_cache',
    'player_recent_form_cache',
    'admin_duplicate_ip_cache',
    'admin_user_ip_summary_cache',
    'admin_match_daily_stats',
    'admin_match_mode_daily_stats',
    'admin_match_player_daily_stats',
    'admin_rank_mode_unlock_stats',
    'admin_series_daily_stats'
  ];
begin
  foreach t in array cache_tables loop
    if to_regclass('public.' || t) is not null then
      execute format('truncate table public.%I', t);
      raise notice 'Cleared cache table: %', t;
    end if;
  end loop;
end $$;

-- 2) Xoa log cu theo retention. Neu bang/cot created_at khong ton tai thi bo qua an toan.
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

-- 3) Refresh planner statistics.
analyze;

-- KHONG tu dong DROP cac bang duoi day.
-- Chi review sau khi xac nhan khong co trigger/function/view phu thuoc:
--   clubs_import
--   match_series_club_actions
