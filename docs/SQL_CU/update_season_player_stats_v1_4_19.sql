-- PES Arena V1.4.19 - Season Player Stats
-- KNOWN BUG: không chạy lại file này sau V1.4.20; dùng update_season_player_stats_v1_4_20.sql để sửa current-season stats.
-- Tách hoàn toàn dữ liệu BXH theo từng season, không xóa dữ liệu hiện có.

create table if not exists public.season_player_stats (
  season_number integer not null,
  user_id uuid not null,
  username text,
  display_name text,
  rank_points integer not null default 1000,
  wins integer not null default 0,
  draws integer not null default 0,
  losses integer not null default 0,
  total_matches integer not null default 0,
  recent_form jsonb not null default '[]'::jsonb,
  final_rank integer,
  updated_at timestamptz not null default now(),
  primary key (season_number, user_id)
);

create index if not exists idx_season_player_stats_season_rank
  on public.season_player_stats(season_number, rank_points desc);

-- 1) Dựng W/D/L + 5 trận gần nhất cho TẤT CẢ season đã biết từ matches còn nguyên.
with season_bounds as (
  select season_number, started_at, ended_at
  from public.rank_seasons
), participant_results as (
  select s.season_number, m.id as match_id, m.created_at, m.player1_id as user_id,
         case when m.score1 > m.score2 then 1 else 0 end as win,
         case when m.score1 = m.score2 then 1 else 0 end as draw,
         case when m.score1 < m.score2 then 1 else 0 end as loss,
         case when m.score1 > m.score2 then 'win' when m.score1 < m.score2 then 'loss' else 'draw' end as form_code
  from season_bounds s join public.matches m on m.status='confirmed'
   and m.player1_id is not null and m.player2_id is not null and m.score1 is not null and m.score2 is not null
   and (s.started_at is null or m.created_at >= s.started_at)
   and (s.ended_at is null or m.created_at <= s.ended_at)
  union all
  select s.season_number, m.id, m.created_at, m.player2_id,
         case when m.score2 > m.score1 then 1 else 0 end,
         case when m.score2 = m.score1 then 1 else 0 end,
         case when m.score2 < m.score1 then 1 else 0 end,
         case when m.score2 > m.score1 then 'win' when m.score2 < m.score1 then 'loss' else 'draw' end
  from season_bounds s join public.matches m on m.status='confirmed'
   and m.player1_id is not null and m.player2_id is not null and m.score1 is not null and m.score2 is not null
   and (s.started_at is null or m.created_at >= s.started_at)
   and (s.ended_at is null or m.created_at <= s.ended_at)
), totals as (
  select season_number,user_id,sum(win)::int wins,sum(draw)::int draws,sum(loss)::int losses,count(*)::int total_matches
  from participant_results group by season_number,user_id
), forms as (
  select season_number,user_id,
         jsonb_agg(jsonb_build_object(
           'code',form_code,
           'short',case form_code when 'win' then 'T' when 'loss' then 'B' else 'H' end,
           'label',case form_code when 'win' then 'Thắng' when 'loss' then 'Bại' else 'Hòa' end
         ) order by created_at desc, match_id desc) filter (where rn <= 5) as recent_form
  from (
    select pr.*, row_number() over(partition by season_number,user_id order by created_at desc,match_id desc) rn
    from participant_results pr
  ) x group by season_number,user_id
)
insert into public.season_player_stats(season_number,user_id,username,display_name,wins,draws,losses,total_matches,recent_form,updated_at)
select t.season_number,t.user_id,u.username,u.display_name,t.wins,t.draws,t.losses,t.total_matches,coalesce(f.recent_form,'[]'::jsonb),now()
from totals t
left join forms f using(season_number,user_id)
left join public.users u on u.id=t.user_id
on conflict(season_number,user_id) do update set
 wins=excluded.wins,draws=excluded.draws,losses=excluded.losses,total_matches=excluded.total_matches,
 recent_form=excluded.recent_form,
 username=coalesce(excluded.username,public.season_player_stats.username),
 display_name=coalesce(excluded.display_name,public.season_player_stats.display_name),updated_at=now();

-- 2) Overlay RP + thứ hạng của các season đã đóng từ snapshot.
with snap as (
  select rs.season_number, e.value as row
  from public.rank_season_snapshots rs
  cross join lateral jsonb_array_elements(rs.snapshot_data) e(value)
)
insert into public.season_player_stats(season_number,user_id,display_name,rank_points,final_rank,updated_at)
select season_number,(row->>'user_id')::uuid,row->>'display_name',coalesce((row->>'rank_points')::int,1000),nullif(row->>'position','')::int,now()
from snap where nullif(row->>'user_id','') is not null
on conflict(season_number,user_id) do update set
 rank_points=excluded.rank_points,final_rank=excluded.final_rank,
 display_name=coalesce(excluded.display_name,public.season_player_stats.display_name),updated_at=now();

-- 3) Current season: RP/WDL hiện đang đúng trên users sau V1.4.18 => ghi vào record Season hiện tại.
with cur as (
  select coalesce((setting_value->>'season_number')::int,1) season_number
  from public.system_settings where setting_key='rank_season_current' limit 1
)
insert into public.season_player_stats(season_number,user_id,username,display_name,rank_points,wins,draws,losses,total_matches,updated_at)
select cur.season_number,u.id,u.username,u.display_name,coalesce(u.rank_points,1000),coalesce(u.wins,0),coalesce(u.draws,0),coalesce(u.losses,0),coalesce(u.total_matches,0),now()
from public.users u cross join cur where u.role='player'
on conflict(season_number,user_id) do update set
 username=excluded.username,display_name=excluded.display_name,rank_points=excluded.rank_points,
 wins=excluded.wins,draws=excluded.draws,losses=excluded.losses,total_matches=excluded.total_matches,updated_at=now();

-- 4) Mọi thay đổi RP/WDL của users (code cũ) tự mirror vào đúng Season hiện tại.
create or replace function public.sync_user_current_season_stats()
returns trigger language plpgsql security definer set search_path=public as $$
declare v_sn integer := 1;
begin
  if new.role <> 'player' then return new; end if;
  select coalesce((setting_value->>'season_number')::int,1) into v_sn
  from public.system_settings where setting_key='rank_season_current' limit 1;
  insert into public.season_player_stats(season_number,user_id,username,display_name,rank_points,wins,draws,losses,total_matches,updated_at)
  values(v_sn,new.id,new.username,new.display_name,coalesce(new.rank_points,1000),coalesce(new.wins,0),coalesce(new.draws,0),coalesce(new.losses,0),coalesce(new.total_matches,0),now())
  on conflict(season_number,user_id) do update set
    username=excluded.username,display_name=excluded.display_name,rank_points=excluded.rank_points,
    wins=excluded.wins,draws=excluded.draws,losses=excluded.losses,total_matches=excluded.total_matches,updated_at=now();
  return new;
end $$;

drop trigger if exists trg_sync_user_current_season_stats on public.users;
create trigger trg_sync_user_current_season_stats
after insert or update of rank_points,wins,draws,losses,total_matches,username,display_name on public.users
for each row execute function public.sync_user_current_season_stats();

-- 5) Khi một trận được confirmed/chỉnh sửa, dựng lại last5 của 2 người trong current season.
create or replace function public.refresh_current_season_recent_form()
returns trigger language plpgsql security definer set search_path=public as $$
declare v_sn integer:=1; v_start timestamptz; v_uid uuid;
begin
  if new.status <> 'confirmed' then return new; end if;
  select coalesce((setting_value->>'season_number')::int,1), nullif(setting_value->>'started_at','')::timestamptz
    into v_sn,v_start from public.system_settings where setting_key='rank_season_current' limit 1;
  foreach v_uid in array array[new.player1_id,new.player2_id] loop
    if v_uid is null then continue; end if;
    update public.season_player_stats s set recent_form=coalesce((
      select jsonb_agg(z.obj order by z.created_at desc,z.match_id desc) from (
        select m.created_at,m.id match_id,
          jsonb_build_object('code',case when (m.player1_id=v_uid and m.score1>m.score2) or (m.player2_id=v_uid and m.score2>m.score1) then 'win' when m.score1=m.score2 then 'draw' else 'loss' end,
            'short',case when (m.player1_id=v_uid and m.score1>m.score2) or (m.player2_id=v_uid and m.score2>m.score1) then 'T' when m.score1=m.score2 then 'H' else 'B' end,
            'label',case when (m.player1_id=v_uid and m.score1>m.score2) or (m.player2_id=v_uid and m.score2>m.score1) then 'Thắng' when m.score1=m.score2 then 'Hòa' else 'Bại' end) obj
        from public.matches m where m.status='confirmed' and (m.player1_id=v_uid or m.player2_id=v_uid)
          and (v_start is null or m.created_at>=v_start)
        order by m.created_at desc,m.id desc limit 5
      ) z
    ),'[]'::jsonb),updated_at=now() where s.season_number=v_sn and s.user_id=v_uid;
  end loop;
  return new;
end $$;

drop trigger if exists trg_refresh_current_season_recent_form on public.matches;
create trigger trg_refresh_current_season_recent_form
after insert or update of status,score1,score2 on public.matches
for each row execute function public.refresh_current_season_recent_form();

-- 6) Reset mở mùa mới: users vẫn là mirror current-season để code cũ hoạt động;
-- trigger users sẽ tự tạo season_player_stats cho Season mới sau khi setting chuyển.
-- Vì RPC cũ update users trước setting, ta chèn record mùa mới trực tiếp sau khi mở mùa bằng wrapper logic ứng dụng.

-- 7) RPC V1.4.19: đổi thứ tự để trigger users KHÔNG ghi số 0 ngược vào season vừa đóng.
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
language plpgsql security definer set search_path=public as $$
declare v_snapshot_count integer:=0; v_reward_count integer:=0; v_setting jsonb; v_db_season integer:=1;
begin
  if p_current_season is null or p_current_season<1 then raise exception 'Invalid current season'; end if;
  if p_next_season<>p_current_season+1 then raise exception 'Invalid next season'; end if;
  select setting_value into v_setting from public.system_settings where setting_key='rank_season_current' limit 1;
  if v_setting is not null then v_db_season:=coalesce((v_setting->>'season_number')::integer,1); end if;
  if v_db_season>p_current_season then return jsonb_build_object('ok',true,'already_done',true,'closed',p_current_season,'opened',v_db_season); end if;
  if v_db_season<>p_current_season then raise exception 'Season state mismatch: db %, request %',v_db_season,p_current_season; end if;
  select count(*) into v_snapshot_count from public.rank_season_snapshots where season_number=p_current_season;
  select count(*) into v_reward_count from public.rank_season_rewards where season_number=p_current_season and status='granted';
  if v_snapshot_count<1 then raise exception 'Season snapshot missing'; end if;
  if v_reward_count<3 then raise exception 'Top 3 reward logs missing'; end if;

  -- Chốt season hiện tại trước. season_player_stats hiện tại KHÔNG bị sửa nữa sau dòng chuyển setting.
  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values(p_current_season,coalesce(nullif(trim(p_current_name),''),'Season '||p_current_season),p_current_started_at,p_reset_at,'closed',greatest(1,coalesce(p_placement_matches,5)))
  on conflict(season_number) do update set name=excluded.name,started_at=coalesce(public.rank_seasons.started_at,excluded.started_at),ended_at=excluded.ended_at,status='closed',placement_matches=excluded.placement_matches;

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values(p_next_season,coalesce(nullif(trim(p_next_name),''),'Season '||p_next_season),p_reset_at,null,'active',greatest(1,coalesce(p_placement_matches,5)))
  on conflict(season_number) do update set name=excluded.name,started_at=excluded.started_at,ended_at=null,status='active',placement_matches=excluded.placement_matches;

  -- Chuyển current season TRƯỚC khi reset users.
  insert into public.system_settings(setting_key,setting_value,updated_at)
  values('rank_season_current',jsonb_build_object('season_number',p_next_season,'name',coalesce(nullif(trim(p_next_name),''),'Season '||p_next_season),'started_at',p_reset_at,'status','active','placement_matches',greatest(1,coalesce(p_placement_matches,5))),p_reset_at)
  on conflict(setting_key) do update set setting_value=excluded.setting_value,updated_at=excluded.updated_at;

  -- Trigger trg_sync_user_current_season_stats lúc này sẽ tạo/cập nhật CHỈ Season mới.
  update public.users set rank_points=1000,wins=0,draws=0,losses=0,total_matches=0 where role='player';

  return jsonb_build_object('ok',true,'already_done',false,'closed',p_current_season,'opened',p_next_season,'rank_points',1000,'wins',0,'draws',0,'losses',0,'placement_matches',greatest(1,coalesce(p_placement_matches,5)));
end $$;

revoke all on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) from public;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to authenticated;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to service_role;
