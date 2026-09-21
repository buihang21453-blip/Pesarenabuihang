-- PES Arena V1.4.18 - Season-isolated W/D/L + current season backfill
-- Mục tiêu:
-- 1) KHÔNG xóa bảng matches, Snapshot hay RP hiện tại.
-- 2) Dùng mốc started_at của Season hiện tại để tính lại wins/draws/losses trên users.
-- 3) Các mùa sau khi Reset: rank_points về 1000 và W/D/L/total_matches về 0.
-- 4) Season cũ vẫn đọc từ Snapshot + matches trong đúng khoảng thời gian của mùa.

DO $$
DECLARE
  v_setting jsonb;
  v_current_season integer := 1;
  v_started_at timestamptz;
BEGIN
  SELECT setting_value INTO v_setting
  FROM public.system_settings
  WHERE setting_key = 'rank_season_current'
  LIMIT 1;

  IF v_setting IS NOT NULL THEN
    v_current_season := COALESCE((v_setting->>'season_number')::integer, 1);
    v_started_at := NULLIF(v_setting->>'started_at','')::timestamptz;
  END IF;

  IF v_started_at IS NULL THEN
    SELECT started_at INTO v_started_at
    FROM public.rank_seasons
    WHERE season_number = v_current_season
    LIMIT 1;
  END IF;

  IF v_current_season > 1 AND v_started_at IS NULL THEN
    RAISE EXCEPTION 'Không tìm thấy started_at của Season %. Dừng migration để tránh trộn thống kê các mùa.', v_current_season;
  END IF;

  -- Xóa số W/D/L cộng dồn cũ trên users, nhưng KHÔNG đụng RP, Zcoin, tài khoản hay matches.
  UPDATE public.users
  SET wins = 0,
      draws = 0,
      losses = 0,
      total_matches = 0
  WHERE role = 'player';

  -- Backfill CHỈ các trận confirmed thuộc Season hiện tại.
  WITH season_matches AS (
    SELECT m.player1_id AS user_id,
           CASE WHEN m.score1 > m.score2 THEN 1 ELSE 0 END AS win,
           CASE WHEN m.score1 = m.score2 THEN 1 ELSE 0 END AS draw,
           CASE WHEN m.score1 < m.score2 THEN 1 ELSE 0 END AS loss
    FROM public.matches m
    WHERE m.status = 'confirmed'
      AND m.player1_id IS NOT NULL
      AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
    UNION ALL
    SELECT m.player2_id AS user_id,
           CASE WHEN m.score2 > m.score1 THEN 1 ELSE 0 END AS win,
           CASE WHEN m.score2 = m.score1 THEN 1 ELSE 0 END AS draw,
           CASE WHEN m.score2 < m.score1 THEN 1 ELSE 0 END AS loss
    FROM public.matches m
    WHERE m.status = 'confirmed'
      AND m.player1_id IS NOT NULL
      AND m.player2_id IS NOT NULL
      AND m.score1 IS NOT NULL AND m.score2 IS NOT NULL
      AND (v_started_at IS NULL OR m.created_at >= v_started_at)
  ), totals AS (
    SELECT user_id,
           SUM(win)::integer AS wins,
           SUM(draw)::integer AS draws,
           SUM(loss)::integer AS losses,
           COUNT(*)::integer AS total_matches
    FROM season_matches
    GROUP BY user_id
  )
  UPDATE public.users u
  SET wins = t.wins,
      draws = t.draws,
      losses = t.losses,
      total_matches = t.total_matches
  FROM totals t
  WHERE u.id = t.user_id AND u.role = 'player';
END $$;

-- Cập nhật RPC Reset cho các Season sau: stats trên users là stats của MÙA HIỆN TẠI,
-- nên mở mùa mới phải về 0 cùng lúc với RP về 1000.
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

  if v_db_season > p_current_season then
    return jsonb_build_object('ok', true, 'already_done', true, 'closed', p_current_season, 'opened', v_db_season);
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

  if v_snapshot_count < 1 then raise exception 'Season snapshot missing'; end if;
  if v_reward_count < 3 then raise exception 'Top 3 reward logs missing'; end if;

  -- Atomic reset. Không xóa lịch sử matches/Snapshot.
  update public.users
  set rank_points = 1000,
      wins = 0,
      draws = 0,
      losses = 0,
      total_matches = 0
  where role = 'player';

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values (p_current_season,coalesce(nullif(trim(p_current_name), ''), 'Season ' || p_current_season),p_current_started_at,p_reset_at,'closed',greatest(1,coalesce(p_placement_matches,5)))
  on conflict (season_number) do update set
    name=excluded.name,
    started_at=coalesce(public.rank_seasons.started_at, excluded.started_at),
    ended_at=excluded.ended_at,
    status='closed',
    placement_matches=excluded.placement_matches;

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values (p_next_season,coalesce(nullif(trim(p_next_name), ''), 'Season ' || p_next_season),p_reset_at,null,'active',greatest(1,coalesce(p_placement_matches,5)))
  on conflict (season_number) do update set
    name=excluded.name, started_at=excluded.started_at, ended_at=null, status='active', placement_matches=excluded.placement_matches;

  insert into public.system_settings(setting_key,setting_value,updated_at)
  values ('rank_season_current',jsonb_build_object(
    'season_number',p_next_season,
    'name',coalesce(nullif(trim(p_next_name), ''), 'Season ' || p_next_season),
    'started_at',p_reset_at,
    'status','active',
    'placement_matches',greatest(1,coalesce(p_placement_matches,5))
  ),p_reset_at)
  on conflict (setting_key) do update set setting_value=excluded.setting_value, updated_at=excluded.updated_at;

  return jsonb_build_object(
    'ok',true,'already_done',false,'closed',p_current_season,'opened',p_next_season,
    'rank_points',1000,'wins',0,'draws',0,'losses',0,'placement_matches',greatest(1,coalesce(p_placement_matches,5))
  );
end;
$$;

revoke all on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) from public;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to authenticated;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to service_role;
