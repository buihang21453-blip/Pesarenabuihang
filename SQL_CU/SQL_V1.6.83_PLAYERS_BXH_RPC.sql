-- PES Arena V1.6.83 - DB-side Players + current leaderboard pagination
-- Run once in Supabase SQL Editor. Safe to re-run.
-- RPCs are backend-only: browser anon/authenticated roles cannot execute them.

create index if not exists idx_users_player_rank
  on public.users (role, account_status, rank_points desc, wins desc, goals_for desc);
create index if not exists idx_users_player_display_name_lower
  on public.users (lower(display_name)) where role = 'player';
create index if not exists idx_match_rooms_active_users
  on public.match_rooms (status, host_user_id, guest_user_id);
create index if not exists idx_matches_live_users
  on public.matches (status, player1_id, player2_id);
create index if not exists idx_matches_rank_activity_created
  on public.matches (status, created_at desc, player1_id, player2_id);

create or replace function public.pes_players_page(
  p_page integer default 1,
  p_page_size integer default 30,
  p_query text default '',
  p_status text default 'all',
  p_viewer_is_admin boolean default false,
  p_viewer_is_invisible boolean default false,
  p_invisible_ids jsonb default '[]'::jsonb,
  p_online_timeout_seconds integer default 180
) returns jsonb
language sql stable security definer set search_path = public
as $$
with params as (
  select greatest(coalesce(p_page,1),1) pg,
         least(greatest(coalesce(p_page_size,30),1),100) psz,
         lower(trim(coalesce(p_query,''))) q,
         lower(trim(coalesce(p_status,'all'))) sf
), room_status as (
  select uid,
         max(priority) priority
  from (
    select unnest(array[r.host_user_id, r.guest_user_id]) uid,
           case
             when r.status = 'waiting_result_confirm' then 2
             when r.status in ('playing','friendly_playing') then 3
             when r.status = 'waiting_ready' or (r.host_user_id is not null and r.guest_user_id is null and r.match_id is null) then 1
             when r.status = 'confirmed' then 1
             else 0 end priority
    from public.match_rooms r
    where r.status in ('waiting_ready','playing','friendly_playing','waiting_result_confirm','confirmed')
  ) x where uid is not null group by uid
), match_status as (
  select uid, max(priority) priority
  from (
    select unnest(array[m.player1_id,m.player2_id]) uid,
           case when m.status='playing' then 3 when m.status='waiting_confirm' then 2 else 0 end priority
    from public.matches m where m.status in ('playing','waiting_confirm')
  ) x where uid is not null group by uid
), base as (
  select u.id,u.username,u.display_name,u.avatar_url,u.rank_points,u.wins,u.draws,u.losses,
         u.goals_for,u.goals_against,u.streak,u.is_online,u.last_seen_at,
         (coalesce(u.is_online,false) and u.last_seen_at >= now() - make_interval(secs => greatest(coalesce(p_online_timeout_seconds,180),30))) online_now,
         greatest(coalesce(rs.priority,0),coalesce(ms.priority,0)) activity_priority,
         exists(select 1 from public.match_rooms sr where sr.host_user_id=u.id and sr.guest_user_id is null and sr.status='waiting_ready') solo_waiting
  from public.users u
  left join room_status rs on rs.uid=u.id
  left join match_status ms on ms.uid=u.id
  where u.role='player'
    and lower(coalesce(u.account_status,'approved')) <> 'deleted'
    and (p_viewer_is_admin or p_viewer_is_invisible or not (p_invisible_ids ? u.id::text))
), decorated as (
  select b.*,
    case when not online_now then 'offline'
         when solo_waiting then 'in_room'
         when activity_priority=3 then 'playing'
         when activity_priority=2 then 'waiting_confirm'
         when activity_priority=1 then 'in_room'
         else 'ready' end activity_code,
    case when not online_now then 'Offline'
         when solo_waiting then 'Đang trong phòng'
         when activity_priority=3 then 'Đang thi đấu'
         when activity_priority=2 then 'Chờ xác nhận'
         when activity_priority=1 then 'Đang trong phòng'
         else 'Sẵn sàng' end activity_label
  from base b
), filtered as (
  select d.* from decorated d, params p
  where (p.q='' or lower(coalesce(d.display_name,'')) like '%'||p.q||'%' or (p_viewer_is_admin and lower(coalesce(d.username,'')) like '%'||p.q||'%'))
    and (p.sf='all' or d.activity_code=p.sf)
), numbered as (
  select f.*, count(*) over() total_count
  from filtered f
  order by case f.activity_code when 'ready' then 0 when 'in_room' then 1 when 'waiting_confirm' then 2 when 'playing' then 3 when 'offline' then 4 else 9 end,
           f.rank_points desc, f.wins desc,
           (coalesce(f.goals_for,0)-coalesce(f.goals_against,0)) desc,
           f.goals_for desc,
           (coalesce(f.wins,0)+coalesce(f.draws,0)+coalesce(f.losses,0)) desc,
           lower(coalesce(f.display_name,f.username,''))
), page_rows as (
  select * from numbered
  offset (select (pg - 1) * psz from params)
  limit (select psz from params)
)
select jsonb_build_object(
  'rows', coalesce((select jsonb_agg(to_jsonb(x)-'total_count') from page_rows x),'[]'::jsonb),
  'total', coalesce((select max(total_count) from numbered),0),
  'page',(select pg from params),'page_size',(select psz from params)
);
$$;

create or replace function public.pes_leaderboard_page(
  p_season_number integer,
  p_page integer default 1,
  p_page_size integer default 100,
  p_query text default '',
  p_min_points integer default null,
  p_max_points integer default null,
  p_placement_matches integer default 5,
  p_inactive_days integer default 30,
  p_viewer_is_admin boolean default false,
  p_viewer_is_invisible boolean default false,
  p_invisible_ids jsonb default '[]'::jsonb,
  p_current_user_id uuid default null
) returns jsonb
language sql stable security definer set search_path = public
as $$
with params as (
  select greatest(coalesce(p_page,1),1) pg,
         least(greatest(coalesce(p_page_size,100),1),100) psz,
         lower(trim(coalesce(p_query,''))) q
), activity as (
  select uid,max(created_at) latest_at from (
    select m.player1_id uid,m.created_at from public.matches m
      where m.status='confirmed' or (m.status='cancelled' and lower(coalesce(m.note,'')) ~ '(forfeit|bỏ cuộc|bỏ trận|bỏ dở|rời phòng sau khi)')
    union all
    select m.player2_id uid,m.created_at from public.matches m
      where m.status='confirmed' or (m.status='cancelled' and lower(coalesce(m.note,'')) ~ '(forfeit|bỏ cuộc|bỏ trận|bỏ dở|rời phòng sau khi)')
  ) a where uid is not null group by uid
), eligible as (
  select u.id,u.username,u.display_name,u.avatar_url,u.streak,u.goals_for,u.goals_against,
         s.rank_points,s.wins,s.draws,s.losses,s.total_matches,s.recent_form,
         a.latest_at
  from public.season_player_stats s
  join public.users u on u.id=s.user_id
  left join activity a on a.uid=u.id
  where s.season_number=p_season_number
    and u.role='player' and lower(coalesce(u.account_status,'approved')) <> 'deleted'
    and coalesce(s.total_matches,0) >= greatest(coalesce(p_placement_matches,5),1)
    and (a.latest_at is null or a.latest_at > now() - make_interval(days => greatest(coalesce(p_inactive_days,30),1)))
    and (p_viewer_is_admin or p_viewer_is_invisible or not (p_invisible_ids ? u.id::text))
), ranked as (
  select e.*, row_number() over(order by e.rank_points desc,e.wins desc,
      (coalesce(e.goals_for,0)-coalesce(e.goals_against,0)) desc,coalesce(e.goals_for,0) desc,
      coalesce(e.total_matches,0) desc,lower(coalesce(e.display_name,e.username,'')))::integer position
  from eligible e
), searched as (
  select r.* from ranked r,params p
  where (p.q='' or lower(coalesce(r.display_name,'')) like '%'||p.q||'%' or lower(coalesce(r.username,'')) like '%'||p.q||'%')
    and (p_min_points is null or r.rank_points >= p_min_points)
    and (p_max_points is null or r.rank_points <= p_max_points)
), numbered as (
  select s.*,count(*) over() total_count from searched s order by s.position
), page_rows as (
  select * from numbered
  offset (select (pg - 1) * psz from params)
  limit (select psz from params)
), me as (
  select r.* from ranked r where r.id=p_current_user_id limit 1
), me_stat as (
  select s.total_matches,a.latest_at from public.season_player_stats s left join activity a on a.uid=s.user_id
  where s.season_number=p_season_number and s.user_id=p_current_user_id limit 1
)
select jsonb_build_object(
 'rows',coalesce((select jsonb_agg(to_jsonb(x)-'total_count'-'latest_at') from page_rows x),'[]'::jsonb),
 'total',coalesce((select max(total_count) from numbered),0),
 'page',(select pg from params),'page_size',(select psz from params),
 'current_player',(select to_jsonb(m)-'latest_at' from me m),
 'current_status',(select case
   when coalesce(ms.total_matches,0) < greatest(coalesce(p_placement_matches,5),1) then jsonb_build_object('visible',false,'reason','placement','matches',coalesce(ms.total_matches,0),'matches_needed',greatest(coalesce(p_placement_matches,5),1)-coalesce(ms.total_matches,0),'inactive_days',0)
   when ms.latest_at is not null and ms.latest_at <= now()-make_interval(days=>greatest(coalesce(p_inactive_days,30),1)) then jsonb_build_object('visible',false,'reason','inactive','matches',coalesce(ms.total_matches,0),'matches_needed',0,'inactive_days',floor(extract(epoch from (now()-ms.latest_at))/86400)::integer)
   else jsonb_build_object('visible',true,'reason','ranked','matches',coalesce(ms.total_matches,0),'matches_needed',0,'inactive_days',0) end from me_stat ms)
);
$$;

revoke all on function public.pes_players_page(integer,integer,text,text,boolean,boolean,jsonb,integer) from public, anon, authenticated;
revoke all on function public.pes_leaderboard_page(integer,integer,integer,text,integer,integer,integer,integer,boolean,boolean,jsonb,uuid) from public, anon, authenticated;
grant execute on function public.pes_players_page(integer,integer,text,text,boolean,boolean,jsonb,integer) to service_role;
grant execute on function public.pes_leaderboard_page(integer,integer,integer,text,integer,integer,integer,integer,boolean,boolean,jsonb,uuid) to service_role;
