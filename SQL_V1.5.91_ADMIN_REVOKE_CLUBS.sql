-- V1.5.91: run in Supabase SQL Editor before deploying the revoke button.
-- Atomic; no changes to coins, rewards, stage1 results or ticket balances.
create or replace function public.c1_admin_revoke_tier_clubs(p_tournament_id uuid)
returns integer language plpgsql security invoker set search_path = public
as $$
declare
  v_state jsonb;
  v_entries jsonb;
  v_history jsonb;
  v_backups jsonb := '[]'::jsonb;
  v_uid uuid;
  v_old text;
  v_entry jsonb;
  v_ids uuid[];
  v_count integer;
begin
  perform 1 from public.tournaments where id=p_tournament_id for update;
  if not found then raise exception 'Giải đấu không tồn tại'; end if;
  if (select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='stage1') is distinct from 'completed'
    or (select status from public.tournament_stages where tournament_id=p_tournament_id and stage_code='league') not in ('draft','pending') then
    raise exception 'Chỉ thu hồi sau GĐ1, trước GĐ2';
  end if;
  if exists (select 1 from public.tournament_matches where tournament_id=p_tournament_id and stage_code in ('league','knockout')) then
    raise exception 'GĐ2 đã có lịch/trận; không thể thu hồi';
  end if;
  if exists (select 1 from public.tournament_settings where tournament_id=p_tournament_id
    and setting_key='club_selection' and setting_value->>'open'='true') then
    raise exception 'Đóng chọn CLB thủ công trước khi thu hồi';
  end if;
  select setting_value into v_state from public.tournament_settings
    where tournament_id=p_tournament_id and setting_key='club_draft_v2' for update;
  if v_state is null or jsonb_typeof(v_state->'all_order') is distinct from 'array'
     or jsonb_array_length(v_state->'all_order') <> 16 then
    raise exception 'Cần trạng thái Random của đủ 16 HLV';
  end if;
  select array_agg((value #>> '{}')::uuid) into v_ids from jsonb_array_elements(v_state->'all_order');
  if cardinality(v_ids) <> 16 or (select count(distinct u) from unnest(v_ids) u) <> 16 then
    raise exception 'Danh sách 16 HLV không hợp lệ';
  end if;
  select count(*) into v_count from public.tournament_members where tournament_id=p_tournament_id;
  if v_count <> 16 or (select count(*) from public.tournament_members where tournament_id=p_tournament_id and user_id=any(v_ids)) <> 16 then
    raise exception 'Danh sách giải không khớp 16 HLV';
  end if;
  v_entries := v_state->'entries';
  if jsonb_typeof(v_entries) is distinct from 'object' then raise exception 'Thiếu dữ liệu vé/CLB'; end if;
  for v_uid in select unnest(v_ids) loop
    v_entry := v_entries->(v_uid::text);
    if v_entry is null then raise exception 'HLV thiếu hồ sơ: %',v_uid; end if;
    select fixed_club_name into v_old from public.tournament_members
      where tournament_id=p_tournament_id and user_id=v_uid for update;
    v_backups := v_backups || jsonb_build_array(jsonb_build_object('user_id',v_uid::text,'old_club',v_old));
    v_entries := jsonb_set(v_entries,array[v_uid::text],
      (v_entry - 'selected_club') || jsonb_build_object(
        'candidate',null,'status',case when v_entry->>'allocation_type'='EARLY_REWARD' then 'active' else 'pending_system' end),false);
  end loop;
  -- Only clubs held by current tournament members are released; no cross-tournament changes.
  update public.tournament_clubs set selected_by=null,selected_at=null
    where tournament_id=p_tournament_id and selected_by=any(v_ids);
  update public.tournament_members set fixed_club_id=null,fixed_club_name=null
    where tournament_id=p_tournament_id and user_id=any(v_ids);
  get diagnostics v_count = row_count;
  if v_count <> 16 then raise exception 'Không thu hồi đủ 16 HLV'; end if;
  v_history := coalesce(v_state->'history','[]'::jsonb) || jsonb_build_array(
    jsonb_build_object('at',now()::text,'user_id','admin','action','ADMIN_REVOKE_ALL_CLUBS',
      'message','Admin thu hồi CLB của 16 HLV; giữ nguyên vé thưởng và lịch sử.', 'old_assignments',v_backups));
  update public.tournament_settings set setting_value = v_state || jsonb_build_object(
    'entries',v_entries,'history',v_history,'active',true,'completed',false,
    'system_assigned',false,'deadline_at',null,'flexible_reward_tickets',true,
    'admin_revoke_batches',coalesce(v_state->'admin_revoke_batches','[]'::jsonb) ||
      jsonb_build_array(jsonb_build_object('at',now()::text,'old_assignments',v_backups))
  ),updated_at=now() where tournament_id=p_tournament_id and setting_key='club_draft_v2';
  return 16;
end;
$$;
revoke all on function public.c1_admin_revoke_tier_clubs(uuid) from public,anon,authenticated;
grant execute on function public.c1_admin_revoke_tier_clubs(uuid) to service_role;
