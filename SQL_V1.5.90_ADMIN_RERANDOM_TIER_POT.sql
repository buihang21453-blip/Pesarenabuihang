-- V1.5.90. Run ONCE in Supabase SQL Editor BEFORE deploying V1.5.90 code.
-- A single database transaction reassigns all 16 clubs and preserves ticket balances/history.
create or replace function public.c1_admin_rerandom_tier_clubs(
    p_tournament_id uuid, p_assignments jsonb
) returns integer
language plpgsql security invoker set search_path = public
as $$
declare
  v_state jsonb;
  v_entries jsonb;
  v_history jsonb;
  v_backups jsonb;
  v_row jsonb;
  v_uid uuid;
  v_club text;
  v_old text;
  v_pot integer;
  v_club_row public.tournament_clubs%rowtype;
  v_stamp text := now()::text;
  v_count integer;
begin
  -- Serialize competing admin batches and block a batch after GĐ2 has begun.
  perform 1 from public.tournaments where id = p_tournament_id for update;
  if not found then raise exception 'Giải đấu không tồn tại'; end if;
  if (select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='stage1') is distinct from 'completed'
     or (select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='league') not in ('draft','pending') then
    raise exception 'Chỉ được random lại sau GĐ1 và trước khi GĐ2 bắt đầu';
  end if;
  if exists (select 1 from public.tournament_matches where tournament_id=p_tournament_id and stage_code in ('league','knockout')) then
    raise exception 'GĐ2 đã có lịch/trận; không thể thay CLB';
  end if;
  if jsonb_typeof(p_assignments) is distinct from 'array' or jsonb_array_length(p_assignments) <> 16 then
    raise exception 'Cần đúng 16 phân bổ';
  end if;
  if (select count(*) from public.tournament_members where tournament_id=p_tournament_id) <> 16 then
    raise exception 'Giải phải có đúng 16 HLV';
  end if;
  select setting_value into v_state from public.tournament_settings
    where tournament_id=p_tournament_id and setting_key='club_draft_v2' for update;
  if v_state is null or jsonb_array_length(coalesce(v_state->'all_order','[]'::jsonb)) <> 16 then
    raise exception 'Chưa có lượt Random CLB đủ 16 HLV';
  end if;
  if exists (select 1 from public.tournament_settings where tournament_id=p_tournament_id
       and setting_key='club_selection' and setting_value->>'open'='true') then
    raise exception 'Đóng chế độ chọn CLB thủ công trước khi random lại';
  end if;
  if (select count(distinct x->>'user_id') from jsonb_array_elements(p_assignments) x) <> 16
     or (select count(distinct x->>'club') from jsonb_array_elements(p_assignments) x) <> 16 then
    raise exception 'HLV hoặc CLB bị trùng trong danh sách';
  end if;
  -- Validate all rows BEFORE making ANY change.
  for v_row in select value from jsonb_array_elements(p_assignments) loop
    v_uid := (v_row->>'user_id')::uuid;
    v_club := v_row->>'club';
    select pot_no into v_pot from public.tournament_members
      where tournament_id=p_tournament_id and user_id=v_uid for update;
    if not found or v_pot not in (1,2,3) then raise exception 'HLV không thuộc Tier hợp lệ'; end if;
    if not ((v_state->'entries') ? (v_uid::text)) then raise exception 'HLV chưa có hồ sơ Random'; end if;
    if not ((v_state->'all_order') @> jsonb_build_array(v_uid::text)) then
      raise exception 'HLV không thuộc danh sách Random';
    end if;
    if (v_pot=1 and v_club <> all(array['PSV','Villarreal','Real Betis','Lille','Lens','Como','Porto','RB Leipzig']))
       or (v_pot=2 and v_club <> all(array['Atlético Madrid','Man United','Aston Villa','Napoli','Roma','Fenerbahçe','Galatasaray','Dortmund']))
       or (v_pot=3 and v_club <> all(array['Bayern','Real Madrid','Barcelona','PSG','Liverpool','Man City','Arsenal','Inter'])) then
       raise exception 'CLB % không đúng Tier/Pot HLV %',v_club,v_uid;
    end if;
    select * into v_club_row from public.tournament_clubs
      where tournament_id=p_tournament_id and name=v_club and is_available=true for update;
    if not found then raise exception 'Không tìm thấy CLB hợp lệ: %',v_club; end if;
  end loop;
  v_entries := v_state->'entries';
  v_history := coalesce(v_state->'history','[]'::jsonb);
  v_backups := '[]'::jsonb;
  for v_row in select value from jsonb_array_elements(p_assignments) loop
    v_uid := (v_row->>'user_id')::uuid;
    select fixed_club_name into v_old from public.tournament_members
      where tournament_id=p_tournament_id and user_id=v_uid;
    v_backups := v_backups || jsonb_build_array(jsonb_build_object('user_id',v_uid,'old_club',v_old,'new_club',v_row->>'club'));
  end loop;
  -- Clear ONLY participating HLV's existing allocations. Unique(tournament_id,selected_by) remains respected.
  update public.tournament_clubs set selected_by=null, selected_at=null
    where tournament_id=p_tournament_id
    and selected_by in (select (value->>'user_id')::uuid from jsonb_array_elements(p_assignments));
  for v_row in select value from jsonb_array_elements(p_assignments) loop
    v_uid := (v_row->>'user_id')::uuid;
    v_club := v_row->>'club';
    select * into v_club_row from public.tournament_clubs
      where tournament_id=p_tournament_id and name=v_club and is_available=true for update;
    if v_club_row.selected_by is not null then raise exception 'CLB % đang thuộc HLV khác',v_club; end if;
    update public.tournament_clubs set selected_by=v_uid,selected_at=now() where id=v_club_row.id;
    update public.tournament_members set fixed_club_id=v_club_row.club_key, fixed_club_name=v_club
      where tournament_id=p_tournament_id and user_id=v_uid;
    v_entries := jsonb_set(v_entries,array[v_uid::text],
        (v_entries -> (v_uid::text)) || jsonb_build_object('status','selected','selected_club',v_club,
          'candidate',jsonb_build_object('id',v_club_row.id::text,'name',v_club)),false);
    v_history := v_history || jsonb_build_array(jsonb_build_object('at',v_stamp,'user_id',v_uid::text,
      'action','ADMIN_TIER_POT_RERANDOM','club',v_club,
      'message','Admin sửa phân bổ sai Tier/Pot: ' || coalesce((select old_club from jsonb_to_recordset(v_backups) as r(user_id uuid,old_club text,new_club text) where r.user_id=v_uid),'chưa có') || ' → ' || v_club || '. Không trừ vé.'));
  end loop;
  update public.tournament_settings set setting_value = v_state || jsonb_build_object(
    'entries',v_entries,'history',v_history,'active',false,'completed',true,
    'system_assigned',true,'deadline_at',null,'flexible_reward_tickets',true,
    'tier_club_pot_rule','1:3;2:2;3:1',
    'admin_rerandom_batches',coalesce(v_state->'admin_rerandom_batches','[]'::jsonb) ||
      jsonb_build_array(jsonb_build_object('at',v_stamp,'changes',v_backups))
  ),updated_at=now() where tournament_id=p_tournament_id and setting_key='club_draft_v2';
  return 16;
end;
$$;
-- RPC is called using the backend service-role connection, not by players.
revoke all on function public.c1_admin_rerandom_tier_clubs(uuid,jsonb) from public, anon, authenticated;
grant execute on function public.c1_admin_rerandom_tier_clubs(uuid,jsonb) to service_role;
