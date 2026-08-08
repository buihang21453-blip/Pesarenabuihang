-- PES Arena V1.3.34 - Read Model / Stats Cache
-- Chạy MỘT LẦN trong Supabase SQL Editor trước khi deploy V1.3.34.
-- Mục tiêu: tab báo cáo chỉ SELECT bảng tổng hợp; mọi phép cộng/đếm nặng chạy khi dữ liệu thay đổi.

begin;

-- 1) Lưu mode_code trực tiếp trên trận để báo cáo không phải đoán từ note/rp_details/phòng.
alter table public.matches add column if not exists mode_code text;

update public.matches m
set mode_code = coalesce(
    nullif(to_jsonb(m.rp_details)->>'mode_code',''),
    nullif(to_jsonb(m.rp_details)->>'match_mode',''),
    (
      select case
        when lower(coalesce(r.team_tier,'')) in ('smart_random','random') then 'rank_random'
        else lower(coalesce(r.team_tier,''))
      end
      from public.match_rooms r
      where r.match_id = m.id
      order by r.created_at desc nulls last
      limit 1
    ),
    case
      when lower(coalesce(m.note,'')) like '%random3_pick1%' or lower(coalesce(m.note,'')) like '%random 3 chọn 1%' then 'random3_pick1'
      when lower(coalesce(m.note,'')) like '%tactical_bo3%' or lower(coalesce(m.note,'')) like '%chiến thuật bo3%' then 'tactical_bo3'
      when lower(coalesce(m.note,'')) like '%ban_pick_bo3%' or lower(coalesce(m.note,'')) like '%cấm chọn%' then 'ban_pick_bo3'
      when lower(coalesce(m.note,'')) like '%home_away%' or lower(coalesce(m.note,'')) like '%lượt đi%' then 'home_away'
      when lower(coalesce(m.note,'')) like '%bo3%' then 'bo3'
      else 'rank_random'
    end
)
where m.mode_code is null or m.mode_code = '';

update public.matches
set mode_code = case when mode_code in ('smart_random','random') then 'rank_random' else mode_code end;

create index if not exists idx_matches_created_at on public.matches(created_at desc);
create index if not exists idx_matches_status_created on public.matches(status, created_at desc);
create index if not exists idx_matches_player1_created on public.matches(player1_id, created_at desc);
create index if not exists idx_matches_player2_created on public.matches(player2_id, created_at desc);
create index if not exists idx_matches_mode_created on public.matches(mode_code, created_at desc);
create index if not exists idx_rooms_match_id on public.match_rooms(match_id);
create index if not exists idx_series_created_mode on public.match_series(created_at desc, mode_code);
create index if not exists idx_series_games_created on public.match_series_games(series_id, game_no);

-- 2) Bảng read model báo cáo.
create table if not exists public.admin_match_daily_stats (
  stat_date date primary key,
  total integer not null default 0,
  confirmed integer not null default 0,
  playing integer not null default 0,
  waiting integer not null default 0,
  disputed integer not null default 0,
  cancelled integer not null default 0,
  confirmed_goals integer not null default 0,
  positive_rp integer not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.admin_match_mode_daily_stats (
  stat_date date not null,
  mode_code text not null,
  match_count integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key(stat_date, mode_code)
);

create table if not exists public.admin_match_player_daily_stats (
  stat_date date not null,
  user_id uuid not null,
  updated_at timestamptz not null default now(),
  primary key(stat_date, user_id)
);

create table if not exists public.admin_series_daily_stats (
  stat_date date not null,
  mode_code text not null,
  series integer not null default 0,
  completed integer not null default 0,
  score_2_0 integer not null default 0,
  score_2_1 integer not null default 0,
  draw integer not null default 0,
  forfeit integer not null default 0,
  disputed integer not null default 0,
  rp_added integer not null default 0,
  rp_removed integer not null default 0,
  games integer not null default 0,
  comebacks integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key(stat_date, mode_code)
);

create table if not exists public.player_recent_form_cache (
  user_id uuid primary key,
  recent_form jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists public.player_profile_stats_cache (
  user_id uuid primary key,
  favorite_team text,
  frequent_opponent_id uuid,
  updated_at timestamptz not null default now()
);

create table if not exists public.admin_rank_mode_unlock_stats (
  mode_code text primary key,
  unlocked_players integer not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.player_pair_stats_cache (
  user_low_id uuid not null,
  user_high_id uuid not null,
  total integer not null default 0,
  user_low_wins integer not null default 0,
  user_high_wins integer not null default 0,
  draws integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key(user_low_id,user_high_id)
);

create table if not exists public.admin_user_ip_summary_cache (
  user_id uuid primary key,
  latest_ip text,
  known_ips jsonb not null default '[]'::jsonb,
  duplicate_ips jsonb not null default '[]'::jsonb,
  duplicate_ip_count integer not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.admin_duplicate_ip_cache (
  ip_address text primary key,
  account_count integer not null default 0,
  user_ids jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

-- 3) Hàm xác định ngày VN của record timestamptz.
create or replace function public.pes_vn_date(ts timestamptz)
returns date language sql immutable as $$
  select (ts at time zone 'Asia/Ho_Chi_Minh')::date;
$$;

-- 4) Rebuild CHỈ một ngày. Đây là write-time; tab Admin không gọi hàm này.
create or replace function public.pes_refresh_match_stats_day(p_day date)
returns void language plpgsql security definer set search_path=public as $$
begin
  if p_day is null then return; end if;

  insert into public.admin_match_daily_stats(
    stat_date,total,confirmed,playing,waiting,disputed,cancelled,confirmed_goals,positive_rp,updated_at
  )
  select p_day,
         count(*)::int,
         count(*) filter(where status='confirmed')::int,
         count(*) filter(where status='playing')::int,
         count(*) filter(where status in ('waiting_confirm','waiting_result_confirm'))::int,
         count(*) filter(where status='disputed')::int,
         count(*) filter(where status='cancelled')::int,
         coalesce(sum(case when status='confirmed' then coalesce(score1,0)+coalesce(score2,0) else 0 end),0)::int,
         coalesce(sum(case when status='confirmed' then greatest(coalesce(delta1,0),0)+greatest(coalesce(delta2,0),0) else 0 end),0)::int,
         now()
  from public.matches
  where public.pes_vn_date(created_at)=p_day
  on conflict(stat_date) do update set
    total=excluded.total, confirmed=excluded.confirmed, playing=excluded.playing,
    waiting=excluded.waiting, disputed=excluded.disputed, cancelled=excluded.cancelled,
    confirmed_goals=excluded.confirmed_goals, positive_rp=excluded.positive_rp, updated_at=now();

  delete from public.admin_match_mode_daily_stats where stat_date=p_day;
  insert into public.admin_match_mode_daily_stats(stat_date,mode_code,match_count,updated_at)
  select p_day, coalesce(nullif(mode_code,''),'rank_random'), count(*)::int, now()
  from public.matches
  where public.pes_vn_date(created_at)=p_day
  group by coalesce(nullif(mode_code,''),'rank_random');

  delete from public.admin_match_player_daily_stats where stat_date=p_day;
  insert into public.admin_match_player_daily_stats(stat_date,user_id,updated_at)
  select p_day, user_id, now()
  from (
    select player1_id as user_id from public.matches where public.pes_vn_date(created_at)=p_day and player1_id is not null
    union
    select player2_id as user_id from public.matches where public.pes_vn_date(created_at)=p_day and player2_id is not null
  ) u;
end;
$$;

create or replace function public.pes_refresh_series_stats_day(p_day date)
returns void language plpgsql security definer set search_path=public as $$
begin
  if p_day is null then return; end if;
  delete from public.admin_series_daily_stats where stat_date=p_day;
  insert into public.admin_series_daily_stats(
    stat_date,mode_code,series,completed,score_2_0,score_2_1,draw,forfeit,disputed,
    rp_added,rp_removed,games,comebacks,updated_at
  )
  with s as (
    select ms.*,
      (select count(*) from public.match_series_games g where g.series_id=ms.id)::int as game_count,
      (select array_agg(g.winner_side order by g.game_no) from public.match_series_games g where g.series_id=ms.id) as winners
    from public.match_series ms
    where public.pes_vn_date(ms.created_at)=p_day
  )
  select p_day,
         coalesce(nullif(mode_code,''),'rank_random'),
         count(*)::int,
         count(*) filter(where status='completed')::int,
         count(*) filter(where coalesce(result_code,'') in ('2-0','0-2'))::int,
         count(*) filter(where coalesce(result_code,'') in ('2-1','1-2'))::int,
         count(*) filter(where lower(coalesce(result_code,''))='draw')::int,
         count(*) filter(where forfeit_user_id is not null or lower(coalesce(result_code,''))='forfeit')::int,
         count(*) filter(where status='disputed')::int,
         coalesce(sum(greatest(coalesce(rp_player1,0),0)+greatest(coalesce(rp_player2,0),0)),0)::int,
         abs(coalesce(sum(least(coalesce(rp_player1,0),0)+least(coalesce(rp_player2,0),0)),0))::int,
         coalesce(sum(game_count),0)::int,
         count(*) filter(where
           array_length(winners,1)>=3 and
           ((winners[1]='player1' and winners[array_length(winners,1)-1]='player2' and winners[array_length(winners,1)]='player2') or
            (winners[1]='player2' and winners[array_length(winners,1)-1]='player1' and winners[array_length(winners,1)]='player1'))
         )::int,
         now()
  from s
  group by coalesce(nullif(mode_code,''),'rank_random');
end;
$$;

-- 5) Cache phong độ + profile theo player, chỉ refresh 2 người liên quan sau khi trận thay đổi.
create or replace function public.pes_refresh_player_cache(p_user_id uuid)
returns void language plpgsql security definer set search_path=public as $$
declare
  v_form jsonb;
  v_favorite text;
  v_opponent uuid;
begin
  if p_user_id is null then return; end if;

  select coalesce(jsonb_agg(x.item order by x.created_at desc),'[]'::jsonb)
  into v_form
  from (
    select m.created_at,
      jsonb_build_object(
        'code', case
          when (m.player1_id=p_user_id and m.score1>m.score2) or (m.player2_id=p_user_id and m.score2>m.score1) then 'win'
          when coalesce(m.score1,0)=coalesce(m.score2,0) then 'draw'
          else 'loss' end,
        'short', case
          when (m.player1_id=p_user_id and m.score1>m.score2) or (m.player2_id=p_user_id and m.score2>m.score1) then 'T'
          when coalesce(m.score1,0)=coalesce(m.score2,0) then 'H'
          else 'B' end,
        'label', case
          when (m.player1_id=p_user_id and m.score1>m.score2) or (m.player2_id=p_user_id and m.score2>m.score1) then 'Thắng'
          when coalesce(m.score1,0)=coalesce(m.score2,0) then 'Hòa'
          else 'Bại' end
      ) item
    from public.matches m
    where m.status='confirmed' and (m.player1_id=p_user_id or m.player2_id=p_user_id)
    order by m.created_at desc
    limit 5
  ) x;

  insert into public.player_recent_form_cache(user_id,recent_form,updated_at)
  values(p_user_id,v_form,now())
  on conflict(user_id) do update set recent_form=excluded.recent_form, updated_at=now();

  select team into v_favorite from (
    select case when player1_id=p_user_id then team1 else team2 end as team, count(*) cnt
    from public.matches
    where status='confirmed' and (player1_id=p_user_id or player2_id=p_user_id)
    group by 1 order by cnt desc nulls last limit 1
  ) q;

  select opponent_id into v_opponent from (
    select case when player1_id=p_user_id then player2_id else player1_id end as opponent_id, count(*) cnt
    from public.matches
    where status='confirmed' and (player1_id=p_user_id or player2_id=p_user_id)
    group by 1 order by cnt desc nulls last limit 1
  ) q;

  insert into public.player_profile_stats_cache(user_id,favorite_team,frequent_opponent_id,updated_at)
  values(p_user_id,v_favorite,v_opponent,now())
  on conflict(user_id) do update set favorite_team=excluded.favorite_team, frequent_opponent_id=excluded.frequent_opponent_id, updated_at=now();
end;
$$;

-- 6) Cache H2H tổng hợp theo cặp người chơi.
create or replace function public.pes_refresh_pair_cache(p_user_a uuid, p_user_b uuid)
returns void language plpgsql security definer set search_path=public as $$
declare lo uuid; hi uuid;
begin
  if p_user_a is null or p_user_b is null or p_user_a=p_user_b then return; end if;
  if p_user_a::text < p_user_b::text then lo:=p_user_a; hi:=p_user_b; else lo:=p_user_b; hi:=p_user_a; end if;
  insert into public.player_pair_stats_cache(user_low_id,user_high_id,total,user_low_wins,user_high_wins,draws,updated_at)
  select lo,hi,
         count(*)::int,
         count(*) filter(where (player1_id=lo and score1>score2) or (player2_id=lo and score2>score1))::int,
         count(*) filter(where (player1_id=hi and score1>score2) or (player2_id=hi and score2>score1))::int,
         count(*) filter(where coalesce(score1,0)=coalesce(score2,0))::int,
         now()
  from public.matches
  where status='confirmed' and ((player1_id=lo and player2_id=hi) or (player1_id=hi and player2_id=lo))
  on conflict(user_low_id,user_high_id) do update set
    total=excluded.total,user_low_wins=excluded.user_low_wins,user_high_wins=excluded.user_high_wins,
    draws=excluded.draws,updated_at=now();
end;
$$;

-- 7) Cache số người đã mở từng mode. Config nằm trong system_settings JSON.
create or replace function public.pes_refresh_rank_mode_unlock_stats()
returns void language plpgsql security definer set search_path=public as $$
declare
  cfg jsonb;
  code text;
  min_rp int;
  min_matches int;
  enabled boolean;
begin
  select case when jsonb_typeof(setting_value::jsonb)='object' then setting_value::jsonb else '{}'::jsonb end
  into cfg
  from public.system_settings where setting_key='rank_mode_configs_v1' limit 1;
  cfg := coalesce(cfg,'{}'::jsonb);

  foreach code in array array['rank_random','random3_pick1','home_away','bo3','tactical_bo3','ban_pick_bo3'] loop
    min_rp := coalesce((cfg->code->>'min_rp')::int, case code when 'home_away' then 1200 when 'bo3' then 1300 when 'tactical_bo3' then 1500 when 'ban_pick_bo3' then 1500 else 0 end);
    min_matches := coalesce((cfg->code->>'min_matches')::int, case code when 'random3_pick1' then 5 when 'home_away' then 10 when 'bo3' then 15 when 'tactical_bo3' then 20 when 'ban_pick_bo3' then 20 else 0 end);
    enabled := coalesce((cfg->code->>'enabled')::boolean,true);
    insert into public.admin_rank_mode_unlock_stats(mode_code,unlocked_players,updated_at)
    select code,
           count(*) filter(where enabled and (
             coalesce(u.role,'player')='admin' or
             exists(select 1 from public.rank_mode_user_unlocks ru where ru.user_id=u.id and ru.mode_code=code and ru.is_unlocked=true) or
             (coalesce(u.rank_points,0)>=min_rp and (coalesce(u.wins,0)+coalesce(u.draws,0)+coalesce(u.losses,0))>=min_matches)
           ))::int,
           now()
    from public.users u
    on conflict(mode_code) do update set unlocked_players=excluded.unlocked_players,updated_at=now();
  end loop;
end;
$$;

-- 8) Cache IP: chỉ rebuild khi quan hệ user/IP thay đổi, không chạy khi chỉ heartbeat cùng IP.
create or replace function public.pes_refresh_ip_cache()
returns void language plpgsql security definer set search_path=public as $$
begin
  truncate table public.admin_duplicate_ip_cache;
  truncate table public.admin_user_ip_summary_cache;

  with ip_rows as (
    select u.id as user_id, nullif(trim(u.register_ip),'') as ip_address, u.created_at as seen_at
    from public.users u
    where nullif(trim(u.register_ip),'') is not null
      and upper(trim(u.register_ip)) not like 'ADMIN_TEST%'
      and upper(trim(u.register_ip)) not like 'ADMIN_CREATED%'
    union all
    select d.user_id, nullif(trim(d.ip_address),'') as ip_address, coalesce(d.last_seen_at,d.created_at,now()) as seen_at
    from public.user_devices d
    where nullif(trim(d.ip_address),'') is not null
  ), distinct_pairs as (
    select distinct user_id,ip_address from ip_rows where user_id is not null and ip_address is not null
  ), owner_counts as (
    select ip_address,count(distinct user_id)::int as account_count,jsonb_agg(distinct user_id) as user_ids
    from distinct_pairs group by ip_address
  )
  insert into public.admin_duplicate_ip_cache(ip_address,account_count,user_ids,updated_at)
  select ip_address,account_count,user_ids,now() from owner_counts where account_count>1;

  with ip_rows as (
    select u.id as user_id, nullif(trim(u.register_ip),'') as ip_address, u.created_at as seen_at
    from public.users u
    where nullif(trim(u.register_ip),'') is not null
      and upper(trim(u.register_ip)) not like 'ADMIN_TEST%'
      and upper(trim(u.register_ip)) not like 'ADMIN_CREATED%'
    union all
    select d.user_id, nullif(trim(d.ip_address),'') as ip_address, coalesce(d.last_seen_at,d.created_at,now()) as seen_at
    from public.user_devices d
    where nullif(trim(d.ip_address),'') is not null
  ), distinct_pairs as (
    select distinct user_id,ip_address from ip_rows where user_id is not null and ip_address is not null
  ), user_known as (
    select user_id,jsonb_agg(ip_address order by ip_address) as known_ips
    from distinct_pairs group by user_id
  ), latest as (
    select distinct on(user_id) user_id,ip_address as latest_ip
    from ip_rows where user_id is not null and ip_address is not null
    order by user_id,seen_at desc nulls last
  )
  insert into public.admin_user_ip_summary_cache(user_id,latest_ip,known_ips,duplicate_ips,duplicate_ip_count,updated_at)
  select u.id,l.latest_ip,coalesce(k.known_ips,'[]'::jsonb),
         coalesce((select jsonb_agg(x.ip) from (
           select jsonb_array_elements_text(coalesce(k.known_ips,'[]'::jsonb)) ip
         ) x join public.admin_duplicate_ip_cache d on d.ip_address=x.ip),'[]'::jsonb),
         coalesce((select max(d.account_count) from public.admin_duplicate_ip_cache d
                   where d.ip_address in (select jsonb_array_elements_text(coalesce(k.known_ips,'[]'::jsonb)))),0),
         now()
  from public.users u
  left join user_known k on k.user_id=u.id
  left join latest l on l.user_id=u.id;
end;
$$;

create or replace function public.pes_ip_device_cache_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  if tg_op='UPDATE' and new.user_id is not distinct from old.user_id and new.ip_address is not distinct from old.ip_address then
    return new;
  end if;
  perform public.pes_refresh_ip_cache();
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_ip_device_cache on public.user_devices;
create trigger trg_pes_ip_device_cache
after insert or update or delete on public.user_devices
for each row execute function public.pes_ip_device_cache_trigger();

create or replace function public.pes_ip_user_cache_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  if tg_op='UPDATE' and new.register_ip is not distinct from old.register_ip then return new; end if;
  perform public.pes_refresh_ip_cache();
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_ip_user_cache on public.users;
drop trigger if exists trg_pes_ip_user_cache_insert_delete on public.users;
drop trigger if exists trg_pes_ip_user_cache_update on public.users;
create trigger trg_pes_ip_user_cache_insert_delete
after insert or delete on public.users
for each row execute function public.pes_ip_user_cache_trigger();
create trigger trg_pes_ip_user_cache_update
after update of register_ip on public.users
for each row execute function public.pes_ip_user_cache_trigger();

-- 9) Triggers write-time.
create or replace function public.pes_matches_read_model_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
declare old_day date; new_day date;
begin
  if tg_op <> 'INSERT' then old_day := public.pes_vn_date(old.created_at); end if;
  if tg_op <> 'DELETE' then new_day := public.pes_vn_date(new.created_at); end if;
  if old_day is not null then perform public.pes_refresh_match_stats_day(old_day); end if;
  if new_day is not null and new_day is distinct from old_day then perform public.pes_refresh_match_stats_day(new_day); end if;
  if tg_op <> 'INSERT' then
    perform public.pes_refresh_player_cache(old.player1_id);
    perform public.pes_refresh_player_cache(old.player2_id);
    perform public.pes_refresh_pair_cache(old.player1_id,old.player2_id);
  end if;
  if tg_op <> 'DELETE' then
    perform public.pes_refresh_player_cache(new.player1_id);
    perform public.pes_refresh_player_cache(new.player2_id);
    perform public.pes_refresh_pair_cache(new.player1_id,new.player2_id);
  end if;
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_matches_read_model on public.matches;
create trigger trg_pes_matches_read_model
after insert or update or delete on public.matches
for each row execute function public.pes_matches_read_model_trigger();

create or replace function public.pes_series_read_model_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
declare old_day date; new_day date;
begin
  if tg_op <> 'INSERT' then old_day := public.pes_vn_date(old.created_at); end if;
  if tg_op <> 'DELETE' then new_day := public.pes_vn_date(new.created_at); end if;
  if old_day is not null then perform public.pes_refresh_series_stats_day(old_day); end if;
  if new_day is not null and new_day is distinct from old_day then perform public.pes_refresh_series_stats_day(new_day); end if;
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_series_read_model on public.match_series;
create trigger trg_pes_series_read_model
after insert or update or delete on public.match_series
for each row execute function public.pes_series_read_model_trigger();

create or replace function public.pes_series_game_read_model_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
declare sid uuid; sday date;
begin
  sid := coalesce(new.series_id,old.series_id);
  select public.pes_vn_date(created_at) into sday from public.match_series where id=sid;
  if sday is not null then perform public.pes_refresh_series_stats_day(sday); end if;
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_series_game_read_model on public.match_series_games;
create trigger trg_pes_series_game_read_model
after insert or update or delete on public.match_series_games
for each row execute function public.pes_series_game_read_model_trigger();

-- User/Manual unlock/config thay đổi thì refresh 6 dòng unlock cache.
create or replace function public.pes_unlock_stats_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  perform public.pes_refresh_rank_mode_unlock_stats();
  return null;
end;
$$;

drop trigger if exists trg_pes_unlock_stats_users on public.users;
drop trigger if exists trg_pes_unlock_stats_users_insert_delete on public.users;
drop trigger if exists trg_pes_unlock_stats_users_update on public.users;
create trigger trg_pes_unlock_stats_users_insert_delete
after insert or delete on public.users
for each statement execute function public.pes_unlock_stats_trigger();
create trigger trg_pes_unlock_stats_users_update
after update of rank_points,wins,draws,losses,role on public.users
for each statement execute function public.pes_unlock_stats_trigger();

drop trigger if exists trg_pes_unlock_stats_manual on public.rank_mode_user_unlocks;
create trigger trg_pes_unlock_stats_manual
after insert or update or delete on public.rank_mode_user_unlocks
for each statement execute function public.pes_unlock_stats_trigger();

create or replace function public.pes_unlock_settings_trigger()
returns trigger language plpgsql security definer set search_path=public as $$
declare k text;
begin
  if tg_op='DELETE' then k:=old.setting_key; else k:=new.setting_key; end if;
  if k='rank_mode_configs_v1' then perform public.pes_refresh_rank_mode_unlock_stats(); end if;
  if tg_op='DELETE' then return old; else return new; end if;
end;
$$;

drop trigger if exists trg_pes_unlock_stats_settings on public.system_settings;
create trigger trg_pes_unlock_stats_settings
after insert or update or delete on public.system_settings
for each row execute function public.pes_unlock_settings_trigger();

-- 10) Backfill một lần cho dữ liệu hiện có.
do $$ declare d date; u uuid; pair record; begin
  for d in select distinct public.pes_vn_date(created_at) from public.matches where created_at is not null loop
    perform public.pes_refresh_match_stats_day(d);
  end loop;
  for d in select distinct public.pes_vn_date(created_at) from public.match_series where created_at is not null loop
    perform public.pes_refresh_series_stats_day(d);
  end loop;
  for u in select id from public.users loop
    perform public.pes_refresh_player_cache(u);
  end loop;
  for pair in
    select distinct least(player1_id::text,player2_id::text)::uuid as a, greatest(player1_id::text,player2_id::text)::uuid as b
    from public.matches where player1_id is not null and player2_id is not null
  loop
    perform public.pes_refresh_pair_cache(pair.a,pair.b);
  end loop;
  perform public.pes_refresh_rank_mode_unlock_stats();
  perform public.pes_refresh_ip_cache();
end $$;

commit;
