-- V1.6.13: Run in Supabase SQL Editor BEFORE deploying V1.6.13.
-- Replaces only the single-club RPC; permits 32 pre-generated pending fixtures.
-- Preserve existing fixture IDs, opponents, tickets and club history.
-- Original V1.5.96 migration remains archived separately.
-- Atomic single-turn allocation, using the backend service-role connection only.
-- Admin config is stored in tournament_settings under club_base_draft_v1.
create or replace function public.c1_allocate_one_base_club(
  p_tournament_id uuid, p_user_id uuid, p_actor text
) returns text
language plpgsql security invoker set search_path = public
as $$
declare
  v_state jsonb;
  v_config jsonb;
  v_entries jsonb;
  v_entry jsonb;
  v_history jsonb;
  v_club public.tournament_clubs%rowtype;
  v_tier integer;
  v_rank integer;
  v_next uuid;
  v_done integer;
  v_pool text[];
begin
  -- All requests for the same tournament serialize here, including simultaneous player clicks.
  perform 1 from public.tournaments where id=p_tournament_id for update;
  if not found then raise exception 'Giải đấu không tồn tại'; end if;
  if (select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='stage1') is distinct from 'completed'
     or coalesce((select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='league'),'?') not in ('draft','pending')
     or exists (select 1 from public.tournament_matches where tournament_id=p_tournament_id and stage_code='knockout')
     or exists (select 1 from public.tournament_matches where tournament_id=p_tournament_id and stage_code='league' and status is distinct from 'pending')
     or (select count(*) from public.tournament_matches where tournament_id=p_tournament_id and stage_code='league') not in (0,32) then
     raise exception 'Chỉ random sau GĐ1, trước thi đấu GĐ2; lịch đã sinh phải đúng 32 trận pending';
  end if;
  if (select count(*) from public.tournament_members where tournament_id=p_tournament_id and status='active') <> 16 then
     raise exception 'Cần đúng 16 HLV chính thức';
  end if;
  if exists (select 1 from public.tournament_settings where tournament_id=p_tournament_id
      and setting_key='club_selection' and setting_value->>'open'='true') then
     raise exception 'Phải khóa chọn CLB thủ công';
  end if;
  select setting_value into v_config from public.tournament_settings
    where tournament_id=p_tournament_id and setting_key='club_base_draft_v1' for update;
  if v_config is null or v_config->>'mode' <> 'sequential'
     or v_config->>'direction' not in ('ascending','descending')
     or v_config->>'actor' not in ('admin','player') then
     raise exception 'Admin chưa cấu hình lượt random từng HLV';
  end if;
  if p_actor is distinct from v_config->>'actor' then
     raise exception 'Chế độ hiện tại không cho phép tài khoản này random';
  end if;
  select setting_value into v_state from public.tournament_settings
    where tournament_id=p_tournament_id and setting_key='club_draft_v2' for update;
  if v_state is null or jsonb_typeof(v_state->'all_order') is distinct from 'array'
      or jsonb_array_length(v_state->'all_order')<>16 then
     raise exception 'Chưa khởi tạo hồ sơ 16 HLV';
  end if;
  if (select count(*) from public.tournament_members where tournament_id=p_tournament_id and status='active'
      and seed_no between 1 and 16) <> 16
     or (select count(distinct seed_no) from public.tournament_members where tournament_id=p_tournament_id
         and status='active') <> 16 then
     raise exception 'Thứ hạng GĐ1 phải đủ và duy nhất từ 1 đến 16';
  end if;
  if (select count(*) from public.tournament_members where tournament_id=p_tournament_id and status='active' and pot_no=1)<>5
     or (select count(*) from public.tournament_members where tournament_id=p_tournament_id and status='active' and pot_no=2)<>6
     or (select count(*) from public.tournament_members where tournament_id=p_tournament_id and status='active' and pot_no=3)<>5 then
     raise exception 'Tier HLV phải đúng 5-6-5';
  end if;
  select user_id into v_next from public.tournament_members
   where tournament_id=p_tournament_id and status='active' and fixed_club_name is null
   order by case when v_config->>'direction'='ascending' then seed_no else -seed_no end
   limit 1;
  if v_next is null then raise exception 'Đã random đủ 16 CLB'; end if;
  if v_next is distinct from p_user_id then raise exception 'Chưa đến lượt HLV theo thứ hạng đã chọn'; end if;
  select pot_no,seed_no into v_tier,v_rank from public.tournament_members
    where tournament_id=p_tournament_id and user_id=p_user_id and status='active' for update;
  v_entry:=v_state->'entries'->(p_user_id::text);
  if v_entry is null or not ((v_state->'all_order') @> jsonb_build_array(p_user_id::text)) then
    raise exception 'HLV chưa có hồ sơ Random';
  end if;
  -- Never overwrite an existing club or consume a ticket for a base allocation.
  if exists(select 1 from public.tournament_clubs where tournament_id=p_tournament_id and selected_by=p_user_id) then
    raise exception 'HLV đã có CLB; không được random trùng';
  end if;
  v_pool:=case v_tier
   when 1 then array['PSV','Villarreal','Real Betis','Lille','Lens','Como','Porto','RB Leipzig']
   when 2 then array['Atlético Madrid','Man United','Aston Villa','Napoli','Roma','Fenerbahçe','Galatasaray','Dortmund']
   when 3 then array['Bayern','Real Madrid','Barcelona','PSG','Liverpool','Man City','Arsenal','Inter']
   else null end;
  if v_pool is null then raise exception 'Tier không hợp lệ'; end if;
  select * into v_club from public.tournament_clubs
    where tournament_id=p_tournament_id and name=any(v_pool)
      and is_available=true and selected_by is null
    order by random() limit 1 for update;
  if not found then raise exception 'Pot CLB đã hết quân trống'; end if;
  update public.tournament_clubs set selected_by=p_user_id,selected_at=now() where id=v_club.id and selected_by is null;
  if not found then raise exception 'CLB vừa bị chiếm'; end if;
  update public.tournament_members set fixed_club_id=v_club.club_key,fixed_club_name=v_club.name
    where tournament_id=p_tournament_id and user_id=p_user_id and fixed_club_name is null;
  if not found then raise exception 'HLV đã có CLB'; end if;
  v_entries:=jsonb_set(v_state->'entries',array[p_user_id::text],
    v_entry || jsonb_build_object('status','selected','selected_club',v_club.name,
      'candidate',jsonb_build_object('id',v_club.id::text,'name',v_club.name)),false);
  select count(*) into v_done from public.tournament_members where tournament_id=p_tournament_id
    and status='active' and fixed_club_name is not null;
  v_history:=coalesce(v_state->'history','[]'::jsonb) || jsonb_build_array(
     jsonb_build_object('at',now()::text,'user_id',p_user_id::text,'action','BASE_SINGLE_RANDOM',
       'club',v_club.name,'message','Hạng '||v_rank||' random CLB gốc '||v_club.name||
       ' (Tier '||v_tier||' → Pot '||(4-v_tier)||'; người bấm: '||p_actor||'). Không trừ vé.'));
  update public.tournament_settings set setting_value=v_state || jsonb_build_object(
     'entries',v_entries,'history',v_history,'active',v_done<>16,'completed',v_done=16,
     'system_assigned',v_done=16,'tier_club_pot_rule',case when v_done=16 then '1:3;2:2;3:1' else null end,
     'deadline_at',null,'flexible_reward_tickets',true),updated_at=now()
   where tournament_id=p_tournament_id and setting_key='club_draft_v2';
  return v_club.name;
end;
$$;
revoke all on function public.c1_allocate_one_base_club(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.c1_allocate_one_base_club(uuid,uuid,text) to service_role;
