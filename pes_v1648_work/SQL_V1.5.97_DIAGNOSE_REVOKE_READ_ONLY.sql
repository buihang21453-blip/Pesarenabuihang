-- V1.5.97: CHẨN ĐOÁN CHỈ ĐỌC. Chạy trong Supabase SQL Editor của đúng dự án.
-- Không gọi RPC thu hồi, không sửa kết quả giải, CLB, số vé hoặc tiền thưởng.
with target as (
  select id from public.tournaments where slug = 'champion-league-arena'
), draft as (
  select ts.tournament_id, ts.setting_value as value from public.tournament_settings ts
  join target t on t.id = ts.tournament_id where ts.setting_key = 'club_draft_v2'
), pick as (
  select ts.tournament_id, ts.setting_value as value from public.tournament_settings ts
  join target t on t.id = ts.tournament_id where ts.setting_key = 'club_selection'
)
select
  t.id as tournament_id,
  to_regprocedure('public.c1_admin_revoke_tier_clubs(uuid)') is not null as revoke_rpc_exists,
  case when to_regprocedure('public.c1_admin_revoke_tier_clubs(uuid)') is null then false
    else has_function_privilege('service_role', 'public.c1_admin_revoke_tier_clubs(uuid)', 'EXECUTE') end as service_role_can_execute,
  (select status from public.tournament_stages where tournament_id=t.id and stage_code='stage1') as stage1_status,
  (select status from public.tournament_stages where tournament_id=t.id and stage_code='league') as league_status,
  (select count(*) from public.tournament_members where tournament_id=t.id) as member_count,
  (select count(*) from public.tournament_members where tournament_id=t.id and status='active') as active_member_count,
  (select count(*) from public.tournament_members where tournament_id=t.id and fixed_club_name is not null) as assigned_member_count,
  (select count(*) from public.tournament_clubs where tournament_id=t.id and selected_by is not null) as occupied_club_count,
  (select count(*) from public.tournament_matches where tournament_id=t.id and stage_code in ('league','knockout')) as later_match_count,
  coalesce((select value->>'open' from pick where tournament_id=t.id), 'false') as manual_pick_open,
  coalesce((select jsonb_typeof(value->'all_order') from draft where tournament_id=t.id), 'missing') as draft_order_type,
  (select case when jsonb_typeof(value->'all_order')='array'
    then jsonb_array_length(value->'all_order') else null end from draft where tournament_id=t.id) as draft_order_count,
  coalesce((select jsonb_typeof(value->'entries') from draft where tournament_id=t.id), 'missing') as draft_entries_type
from target t;
-- Nếu không có dòng kết quả, tìm slug giải thật bằng SELECT id,slug,name FROM public.tournaments;
-- Không gửi Service Role Key hoặc JWT trong ảnh/log chia sẻ.
