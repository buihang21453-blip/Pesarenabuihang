-- PES Arena V1.4.9 - Separate Season Rankings / Recover Season 1
-- Mục tiêu:
-- 1) GIỮ NGUYÊN rank_season_snapshots của Season 1 (đây là BXH đóng băng).
-- 2) Bảo đảm Season 1 được ghi là closed.
-- 3) Bảo đảm Season 2 là active.
-- 4) Chỉ reset users.rank_points = 1000 nếu hệ thống CHƯA từng chuyển sang Season 2.
--    Nếu V1.4.8 đã chuyển rồi thì KHÔNG reset lần nữa, tránh mất RP Season 2 đã phát sinh.

do $$
declare
  v_setting jsonb;
  v_current integer := 1;
  v_now timestamptz := now();
  v_snapshot_created timestamptz;
begin
  select setting_value into v_setting
  from public.system_settings
  where setting_key = 'rank_season_current'
  limit 1;

  if v_setting is not null then
    v_current := coalesce((v_setting->>'season_number')::integer, 1);
  end if;

  select created_at into v_snapshot_created
  from public.rank_season_snapshots
  where season_number = 1
  limit 1;

  if not exists (select 1 from public.rank_season_snapshots where season_number = 1) then
    raise exception 'Không tìm thấy Snapshot Season 1. Dừng migration để tránh mất dữ liệu BXH mùa 1.';
  end if;

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values (1,'Season 1',null,coalesce(v_snapshot_created,v_now),'closed',5)
  on conflict (season_number) do update set
    name='Season 1',
    ended_at=coalesce(public.rank_seasons.ended_at, excluded.ended_at),
    status='closed',
    placement_matches=5;

  -- Chỉ khởi tạo/reset Season 2 nếu DB vẫn đang báo Season 1.
  if v_current < 2 then
    update public.users set rank_points = 1000 where role='player';

    insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
    values (2,'Season 2',v_now,null,'active',5)
    on conflict (season_number) do update set
      name='Season 2', ended_at=null, status='active', placement_matches=5;

    insert into public.system_settings(setting_key,setting_value,updated_at)
    values ('rank_season_current', jsonb_build_object(
      'season_number',2,'name','Season 2','started_at',v_now,'status','active','placement_matches',5
    ), v_now)
    on conflict (setting_key) do update set setting_value=excluded.setting_value, updated_at=excluded.updated_at;
  else
    -- V1.4.8 đã mở Season 2: chỉ sửa metadata, KHÔNG chạm RP hiện tại.
    insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
    values (2,'Season 2',coalesce((v_setting->>'started_at')::timestamptz,v_now),null,'active',5)
    on conflict (season_number) do update set
      name='Season 2', ended_at=null, status='active', placement_matches=5;
  end if;
end $$;
