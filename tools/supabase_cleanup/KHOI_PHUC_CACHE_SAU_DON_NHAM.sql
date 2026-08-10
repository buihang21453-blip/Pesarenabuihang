-- PES Arena V1.2.22 - KHOI PHUC TOAN BO CACHE/READ MODEL TU DU LIEU GOC
-- Muc dich: dung lai cache sau khi cleanup V1.2.21 da TRUNCATE nham.
-- KHONG xoa/sua RP, matches, users, Zcoin, inventory. Chi TINH LAI bang cache.

do $$
declare
  required_fn text;
  funcs text[] := array[
    'pes_refresh_match_stats_day',
    'pes_refresh_series_stats_day',
    'pes_refresh_player_cache',
    'pes_refresh_pair_cache',
    'pes_refresh_rank_mode_unlock_stats',
    'pes_refresh_ip_cache'
  ];
begin
  foreach required_fn in array funcs loop
    if not exists (
      select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname=required_fn
    ) then
      raise exception 'THIEU HAM %. Hay chay project_docs/sql/PES_ARENA_READ_MODEL_V1.3.34.sql truoc.', required_fn;
    end if;
  end loop;
end $$;

-- Rebuild theo du lieu goc dang con trong matches/users/match_series/user_devices.
do $$
declare
  d date;
  u uuid;
  pair record;
begin
  -- Bao cao tran theo ngay
  for d in select distinct public.pes_vn_date(created_at) from public.matches where created_at is not null loop
    perform public.pes_refresh_match_stats_day(d);
  end loop;

  -- Bao cao series theo ngay
  if to_regclass('public.match_series') is not null then
    for d in select distinct public.pes_vn_date(created_at) from public.match_series where created_at is not null loop
      perform public.pes_refresh_series_stats_day(d);
    end loop;
  end if;

  -- 5 tran gan nhat + thong ke profile cho TOAN BO user
  for u in select id from public.users loop
    perform public.pes_refresh_player_cache(u);
  end loop;

  -- H2H cache cho TOAN BO cap da tung dau
  for pair in
    select distinct
      least(player1_id::text,player2_id::text)::uuid as a,
      greatest(player1_id::text,player2_id::text)::uuid as b
    from public.matches
    where player1_id is not null and player2_id is not null
  loop
    perform public.pes_refresh_pair_cache(pair.a,pair.b);
  end loop;

  -- Mo khoa mode + IP cache
  perform public.pes_refresh_rank_mode_unlock_stats();
  perform public.pes_refresh_ip_cache();
end $$;

analyze;

-- Kiem tra nhanh sau rebuild.
select 'player_recent_form_cache' as cache, count(*) as rows from public.player_recent_form_cache
union all select 'player_profile_stats_cache', count(*) from public.player_profile_stats_cache
union all select 'player_pair_stats_cache', count(*) from public.player_pair_stats_cache
union all select 'admin_match_daily_stats', count(*) from public.admin_match_daily_stats
union all select 'admin_match_mode_daily_stats', count(*) from public.admin_match_mode_daily_stats
union all select 'admin_match_player_daily_stats', count(*) from public.admin_match_player_daily_stats
union all select 'admin_rank_mode_unlock_stats', count(*) from public.admin_rank_mode_unlock_stats
union all select 'admin_series_daily_stats', count(*) from public.admin_series_daily_stats
union all select 'admin_user_ip_summary_cache', count(*) from public.admin_user_ip_summary_cache;
