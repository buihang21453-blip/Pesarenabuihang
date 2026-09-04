-- PES Arena V1.4.8 - Safe / Atomic Season Reset
-- Chạy file này 1 lần trong Supabase SQL Editor trước khi bấm Reset mùa.

create or replace function public.reset_rank_season_open_next(
  p_current_season integer,
  p_current_name text,
  p_current_started_at timestamptz,
  p_reset_at timestamptz,
  p_next_season integer,
  p_next_name text,
  p_placement_matches integer default 5
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_snapshot_count integer := 0;
  v_reward_count integer := 0;
  v_setting jsonb;
  v_db_season integer := 1;
begin
  if p_current_season is null or p_current_season < 1 then
    raise exception 'Invalid current season';
  end if;
  if p_next_season <> p_current_season + 1 then
    raise exception 'Invalid next season';
  end if;

  select setting_value into v_setting
  from public.system_settings
  where setting_key = 'rank_season_current'
  limit 1;

  if v_setting is not null then
    v_db_season := coalesce((v_setting->>'season_number')::integer, 1);
  end if;

  -- Chặn request cũ/stale. Nếu DB đã sang mùa mới thì không reset lần nữa.
  if v_db_season > p_current_season then
    return jsonb_build_object(
      'ok', true,
      'already_done', true,
      'closed', p_current_season,
      'opened', v_db_season
    );
  end if;
  if v_db_season <> p_current_season then
    raise exception 'Season state mismatch: db %, request %', v_db_season, p_current_season;
  end if;

  select count(*) into v_snapshot_count
  from public.rank_season_snapshots
  where season_number = p_current_season;

  select count(*) into v_reward_count
  from public.rank_season_rewards
  where season_number = p_current_season and status = 'granted';

  if v_snapshot_count < 1 then
    raise exception 'Season snapshot missing';
  end if;
  if v_reward_count < 3 then
    raise exception 'Top 3 reward logs missing';
  end if;

  -- Tất cả lệnh dưới đây nằm trong cùng transaction của PostgreSQL.
  -- Chỉ cần 1 lệnh lỗi => toàn bộ thay đổi tự rollback.
  update public.users
  set rank_points = 1000
  where role = 'player';

  insert into public.rank_seasons(
    season_number, name, started_at, ended_at, status, placement_matches
  ) values (
    p_current_season,
    coalesce(nullif(trim(p_current_name), ''), 'Season ' || p_current_season),
    p_current_started_at,
    p_reset_at,
    'closed',
    greatest(1, coalesce(p_placement_matches, 5))
  )
  on conflict (season_number) do update set
    name = excluded.name,
    started_at = coalesce(public.rank_seasons.started_at, excluded.started_at),
    ended_at = excluded.ended_at,
    status = 'closed',
    placement_matches = excluded.placement_matches;

  insert into public.rank_seasons(
    season_number, name, started_at, ended_at, status, placement_matches
  ) values (
    p_next_season,
    coalesce(nullif(trim(p_next_name), ''), 'Season ' || p_next_season),
    p_reset_at,
    null,
    'active',
    greatest(1, coalesce(p_placement_matches, 5))
  )
  on conflict (season_number) do update set
    name = excluded.name,
    started_at = excluded.started_at,
    ended_at = null,
    status = 'active',
    placement_matches = excluded.placement_matches;

  insert into public.system_settings(setting_key, setting_value, updated_at)
  values (
    'rank_season_current',
    jsonb_build_object(
      'season_number', p_next_season,
      'name', coalesce(nullif(trim(p_next_name), ''), 'Season ' || p_next_season),
      'started_at', p_reset_at,
      'status', 'active',
      'placement_matches', greatest(1, coalesce(p_placement_matches, 5))
    ),
    p_reset_at
  )
  on conflict (setting_key) do update set
    setting_value = excluded.setting_value,
    updated_at = excluded.updated_at;

  return jsonb_build_object(
    'ok', true,
    'already_done', false,
    'closed', p_current_season,
    'opened', p_next_season,
    'rank_points', 1000,
    'placement_matches', greatest(1, coalesce(p_placement_matches, 5))
  );
end;
$$;

revoke all on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) from public;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to authenticated;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to service_role;
