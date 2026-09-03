-- PES Arena V1.4.29 - Season Mechanics Isolation
-- Tách chuỗi thắng/thua, thưởng tuần, số đối thủ và inactivity theo Season.
-- Không xóa matches, không reset RP, không sửa Snapshot/BXH mùa cũ.

alter table public.season_player_stats
  add column if not exists streak integer not null default 0,
  add column if not exists loss_streak integer not null default 0;

alter table public.weekly_rp_rewards
  add column if not exists season_number integer not null default 1;

-- Gắn các log thưởng tuần cũ về Season tương ứng theo thời điểm nhận thưởng.
update public.weekly_rp_rewards w
set season_number = coalesce((
  select s.season_number
  from public.rank_seasons s
  where (s.started_at is null or w.created_at >= s.started_at)
    and (s.ended_at is null or w.created_at <= s.ended_at)
  order by s.season_number desc
  limit 1
), 1)
where season_number is null or season_number = 1;

-- Unique cũ không có season_number sẽ chặn phần thưởng nếu đổi mùa giữa tuần.
alter table public.weekly_rp_rewards
  drop constraint if exists weekly_rp_rewards_user_id_week_start_reward_code_key;

create unique index if not exists uq_weekly_rp_rewards_season_user_week_code
  on public.weekly_rp_rewards(user_id, season_number, week_start, reward_code);

create index if not exists idx_weekly_rp_rewards_season_user
  on public.weekly_rp_rewards(season_number, user_id, week_start desc);

-- Trigger mirror current-season: streak/loss_streak cũng thuộc đúng Season hiện tại.
create or replace function public.sync_user_current_season_stats()
returns trigger language plpgsql security definer set search_path=public as $$
declare v_sn integer := 1;
begin
  if new.role <> 'player' then return new; end if;
  select coalesce((setting_value->>'season_number')::int,1) into v_sn
  from public.system_settings where setting_key='rank_season_current' limit 1;
  insert into public.season_player_stats(
    season_number,user_id,username,display_name,rank_points,wins,draws,losses,total_matches,
    streak,loss_streak,updated_at
  ) values(
    v_sn,new.id,new.username,new.display_name,coalesce(new.rank_points,1000),
    coalesce(new.wins,0),coalesce(new.draws,0),coalesce(new.losses,0),coalesce(new.total_matches,0),
    coalesce(new.streak,0),coalesce(new.loss_streak,0),now()
  )
  on conflict(season_number,user_id) do update set
    username=excluded.username,display_name=excluded.display_name,rank_points=excluded.rank_points,
    wins=excluded.wins,draws=excluded.draws,losses=excluded.losses,total_matches=excluded.total_matches,
    streak=excluded.streak,loss_streak=excluded.loss_streak,updated_at=now();
  return new;
end $$;

drop trigger if exists trg_sync_user_current_season_stats on public.users;
create trigger trg_sync_user_current_season_stats
after insert or update of rank_points,wins,draws,losses,total_matches,streak,loss_streak,username,display_name on public.users
for each row execute function public.sync_user_current_season_stats();

-- Dựng lại streak/loss_streak cuối mỗi Season từ lịch sử trận còn nguyên.
DO $$
DECLARE
  s record;
  u record;
  m record;
  v_win integer;
  v_loss integer;
  v_mode text;
  v_is_p1 boolean;
  v_outcome text;
  v_affects boolean;
BEGIN
  FOR s IN
    SELECT season_number, started_at, ended_at FROM public.rank_seasons ORDER BY season_number
  LOOP
    FOR u IN
      SELECT DISTINCT x.user_id
      FROM (
        SELECT player1_id user_id FROM public.matches
        WHERE player1_id is not null
          and (s.started_at is null or created_at >= s.started_at)
          and (s.ended_at is null or created_at <= s.ended_at)
        UNION
        SELECT player2_id FROM public.matches
        WHERE player2_id is not null
          and (s.started_at is null or created_at >= s.started_at)
          and (s.ended_at is null or created_at <= s.ended_at)
      ) x
    LOOP
      v_win := 0;
      v_loss := 0;
      v_mode := null;

      FOR m IN
        SELECT id,player1_id,player2_id,score1,score2,rp_details,created_at
        FROM public.matches
        WHERE status='confirmed'
          and score1 is not null and score2 is not null
          and (player1_id=u.user_id or player2_id=u.user_id)
          and (s.started_at is null or created_at >= s.started_at)
          and (s.ended_at is null or created_at <= s.ended_at)
        ORDER BY created_at desc,id desc
      LOOP
        v_affects := coalesce((m.rp_details->'repeat_opponent'->>'streak_eligible')::boolean,true);
        IF not v_affects THEN CONTINUE; END IF;
        v_is_p1 := m.player1_id=u.user_id;
        IF m.score1=m.score2 THEN v_outcome := 'draw';
        ELSIF (v_is_p1 and m.score1>m.score2) or ((not v_is_p1) and m.score2>m.score1) THEN v_outcome := 'win';
        ELSE v_outcome := 'loss'; END IF;

        IF v_mode is null THEN
          v_mode := v_outcome;
          IF v_outcome='win' THEN v_win:=1;
          ELSIF v_outcome='loss' THEN v_loss:=1;
          ELSE EXIT; END IF;
        ELSIF v_outcome=v_mode THEN
          IF v_mode='win' THEN v_win:=v_win+1; ELSE v_loss:=v_loss+1; END IF;
        ELSE
          EXIT;
        END IF;
      END LOOP;

      update public.season_player_stats
      set streak=v_win,loss_streak=v_loss,updated_at=now()
      where season_number=s.season_number and user_id=u.user_id;
    END LOOP;
  END LOOP;
END $$;

-- Current Season mirror trên users phải dùng đúng streak của Season hiện tại.
DO $$
DECLARE v_sn integer:=1;
BEGIN
  select coalesce((setting_value->>'season_number')::int,1) into v_sn
  from public.system_settings where setting_key='rank_season_current' limit 1;

  update public.users u
  set streak=coalesce(s.streak,0),
      loss_streak=coalesce(s.loss_streak,0)
  from public.season_player_stats s
  where u.id=s.user_id and u.role='player' and s.season_number=v_sn;

  update public.users u
  set streak=0,loss_streak=0
  where u.role='player'
    and not exists (
      select 1 from public.season_player_stats s where s.season_number=v_sn and s.user_id=u.id
    );
END $$;

-- Mở Season mới: reset cả hai chuỗi trên mirror users. Trigger sẽ ghi vào Season mới.
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

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values(p_current_season,coalesce(nullif(trim(p_current_name),''),'Season '||p_current_season),p_current_started_at,p_reset_at,'closed',greatest(1,coalesce(p_placement_matches,5)))
  on conflict(season_number) do update set name=excluded.name,started_at=coalesce(public.rank_seasons.started_at,excluded.started_at),ended_at=excluded.ended_at,status='closed',placement_matches=excluded.placement_matches;

  insert into public.rank_seasons(season_number,name,started_at,ended_at,status,placement_matches)
  values(p_next_season,coalesce(nullif(trim(p_next_name),''),'Season '||p_next_season),p_reset_at,null,'active',greatest(1,coalesce(p_placement_matches,5)))
  on conflict(season_number) do update set name=excluded.name,started_at=excluded.started_at,ended_at=null,status='active',placement_matches=excluded.placement_matches;

  insert into public.system_settings(setting_key,setting_value,updated_at)
  values('rank_season_current',jsonb_build_object('season_number',p_next_season,'name',coalesce(nullif(trim(p_next_name),''),'Season '||p_next_season),'started_at',p_reset_at,'status','active','placement_matches',greatest(1,coalesce(p_placement_matches,5))),p_reset_at)
  on conflict(setting_key) do update set setting_value=excluded.setting_value,updated_at=excluded.updated_at;

  update public.users set rank_points=1000,wins=0,draws=0,losses=0,total_matches=0,streak=0,loss_streak=0 where role='player';

  return jsonb_build_object('ok',true,'already_done',false,'closed',p_current_season,'opened',p_next_season,
    'rank_points',1000,'wins',0,'draws',0,'losses',0,'streak',0,'loss_streak',0,
    'placement_matches',greatest(1,coalesce(p_placement_matches,5)));
end $$;

revoke all on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) from public;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to authenticated;
grant execute on function public.reset_rank_season_open_next(integer,text,timestamptz,timestamptz,integer,text,integer) to service_role;
