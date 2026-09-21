-- PES Arena V1.6.23 — Allow unexpired vouchers while GĐ2 is open.
-- Run BEFORE deploying V1.6.23 web. Replaces function only, does NOT reset any vouchers, clubs or fixtures.
-- Root cause: UNIQUE(tournament_id,selected_by) prohibits reserving a second club
-- for an HLV while the old club remains assigned. Release old first in same transaction.
-- Safe CREATE OR REPLACE; does not reset any ticket, club, fixture or history.
-- One PostgreSQL transaction handles BOTH player rerolls and authorized Admin proxy rerolls.
-- A failed guard or SQL statement rolls back the ENTIRE exchange automatically.
CREATE OR REPLACE FUNCTION public.c1_use_early_club_reroll_ticket(
  p_tournament_id uuid,
  p_user_id uuid,
  p_actor_user_id uuid,
  p_actor_role text
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public
AS $$
DECLARE
  v_state jsonb;
  v_entry jsonb;
  v_entries jsonb;
  v_history jsonb;
  v_skipped jsonb;
  v_timing jsonb;
  v_deadline timestamptz;
  v_member public.tournament_members%rowtype;
  v_old public.tournament_clubs%rowtype;
  v_new public.tournament_clubs%rowtype;
  v_allowed_clubs text[];
  v_remaining int;
  v_now timestamptz := now();
  v_actor_label text;
BEGIN
  IF p_actor_role NOT IN ('admin','player') OR p_actor_user_id IS NULL THEN
    RAISE EXCEPTION 'Người thực hiện không hợp lệ';
  END IF;
  IF p_actor_role='player' AND p_actor_user_id IS DISTINCT FROM p_user_id THEN
    RAISE EXCEPTION 'HLV không được sử dụng vé của người khác';
  END IF;

  -- The tournament row is the per-tournament mutex, shared with base-club allocation RPC.
  PERFORM 1 FROM public.tournaments WHERE id=p_tournament_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Giải đấu không tồn tại'; END IF;

  SELECT * INTO v_member FROM public.tournament_members
    WHERE tournament_id=p_tournament_id AND user_id=p_user_id AND status='active'
    FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'HLV không thuộc 16 thành viên đang thi đấu'; END IF;

  SELECT setting_value INTO v_state FROM public.tournament_settings
    WHERE tournament_id=p_tournament_id AND setting_key='club_draft_v2' FOR UPDATE;
  IF v_state IS NULL OR coalesce(v_state->>'system_assigned','false') <> 'true'
     OR v_state->>'tier_club_pot_rule' IS DISTINCT FROM '1:3;2:2;3:1'
     OR coalesce(v_state->>'completed','false') <> 'true'
     OR jsonb_typeof(v_state->'all_order') IS DISTINCT FROM 'array'
     OR jsonb_array_length(v_state->'all_order')<>16 THEN
    RAISE EXCEPTION 'Chưa phân đủ 16 CLB gốc hợp lệ; vé không bị trừ';
  END IF;
  IF NOT (coalesce(v_state->'order','[]'::jsonb) @> jsonb_build_array(p_user_id::text)) THEN
    RAISE EXCEPTION 'HLV không thuộc nhóm Top 1-3 nhận vé';
  END IF;
  v_entry := v_state->'entries'->(p_user_id::text);
  IF v_entry IS NULL OR v_entry->>'allocation_type' IS DISTINCT FROM 'EARLY_REWARD' THEN
    RAISE EXCEPTION 'Hồ sơ vé thưởng GĐ1 không hợp lệ';
  END IF;
  IF coalesce((v_entry->>'tickets_remaining')::int,0)<=0
     OR coalesce((v_entry->>'reward_finalized')::boolean,false) THEN
    RAISE EXCEPTION 'Vé đã hết hoặc HLV đã chốt CLB cuối cùng';
  END IF;
  IF v_entry->>'status' IS DISTINCT FROM 'selected' OR v_member.fixed_club_name IS NULL THEN
    RAISE EXCEPTION 'HLV chưa có CLB gốc đã chốt';
  END IF;

  SELECT setting_value INTO v_timing FROM public.tournament_settings
    WHERE tournament_id=p_tournament_id AND setting_key='competition_timing';
  v_deadline := coalesce(nullif(v_timing->>'gd2_reward_ticket_deadline_at','')::timestamptz,
                         '2026-09-18 12:00:00+07'::timestamptz);
  IF v_now >= v_deadline THEN RAISE EXCEPTION 'Đã hết hạn dùng vé thưởng; không trừ vé'; END IF;
  -- GĐ2 may already be open while an unexpired early-reward ticket remains valid.
  -- Only the independently configured deadline / voluntary finalization / completed
  -- GĐ2 or active Knockout ends this privilege; opening GĐ2 alone does not.
  IF EXISTS(SELECT 1 FROM public.tournament_stages
    WHERE tournament_id=p_tournament_id AND
      ((stage_code='league' AND status='completed') OR
       (stage_code='knockout' AND status IN ('open','completed')))) THEN
    RAISE EXCEPTION 'GĐ2 đã kết thúc hoặc Knockout đã bắt đầu; không thể dùng vé thưởng sớm';
  END IF;

  v_allowed_clubs := CASE v_member.pot_no
    WHEN 1 THEN ARRAY['PSV','Villarreal','Real Betis','Lille','Lens','Como','Porto','RB Leipzig']
    WHEN 2 THEN ARRAY['Atlético Madrid','Man United','Aston Villa','Napoli','Roma','Fenerbahçe','Galatasaray','Dortmund']
    WHEN 3 THEN ARRAY['Bayern','Real Madrid','Barcelona','PSG','Liverpool','Man City','Arsenal','Inter']
    ELSE NULL END;
  IF v_allowed_clubs IS NULL OR NOT (v_member.fixed_club_name=ANY(v_allowed_clubs)) THEN
    RAISE EXCEPTION 'CLB hiện tại không khớp Tier/Pot';
  END IF;
  SELECT * INTO v_old FROM public.tournament_clubs
    WHERE tournament_id=p_tournament_id AND name=v_member.fixed_club_name
      AND selected_by=p_user_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'CLB hiện tại chưa khớp chủ sở hữu; cần Admin kiểm tra dữ liệu, chưa trừ vé';
  END IF;

  v_skipped := coalesce(v_entry->'skipped','[]'::jsonb) || jsonb_build_array(v_old.id::text);
  SELECT * INTO v_new FROM public.tournament_clubs
    WHERE tournament_id=p_tournament_id AND is_available=true
      AND selected_by IS NULL AND name=ANY(v_allowed_clubs)
      AND NOT (v_skipped @> jsonb_build_array(id::text))
    ORDER BY random() LIMIT 1 FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Pot không còn CLB trống phù hợp; vé vẫn giữ nguyên'; END IF;

  -- V1.6.20 FIX: tournament_clubs has UNIQUE(tournament_id, selected_by).
  -- Release the OLD club first, otherwise reserving the new club raises 23505.
  -- This is ONE PostgreSQL transaction: if any subsequent operation fails,
  -- the release is automatically rolled back and the old club remains owned.
  UPDATE public.tournament_clubs SET selected_by=NULL,selected_at=NULL
    WHERE id=v_old.id AND tournament_id=p_tournament_id AND selected_by=p_user_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Không trả được CLB cũ; toàn bộ lượt quay được hoàn tác'; END IF;

  UPDATE public.tournament_clubs
    SET selected_by=p_user_id,selected_at=v_now
    WHERE id=v_new.id AND tournament_id=p_tournament_id AND selected_by IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'CLB mới vừa được chọn; chưa trừ vé'; END IF;
  UPDATE public.tournament_members
    SET fixed_club_id=v_new.club_key,fixed_club_name=v_new.name
    WHERE tournament_id=p_tournament_id AND user_id=p_user_id
      AND fixed_club_name=v_old.name AND status='active';
  IF NOT FOUND THEN RAISE EXCEPTION 'CLB của HLV đã thay đổi; chưa trừ vé'; END IF;

  v_remaining := (v_entry->>'tickets_remaining')::int - 1;
  v_entry := v_entry || jsonb_build_object(
    'tickets_remaining',v_remaining,
    'skipped',v_skipped,
    'selected_club',v_new.name,
    'candidate',jsonb_build_object('id',v_new.id::text,'name',v_new.name),
    'status','selected'
  );
  IF v_remaining=0 THEN
    v_entry := v_entry || jsonb_build_object(
      'reward_finalized',true,'reward_finalized_at',v_now::text,
      'reward_finalized_reason','tickets_exhausted');
  END IF;
  v_entries := jsonb_set(v_state->'entries',ARRAY[p_user_id::text],v_entry,false);
  v_actor_label := CASE WHEN p_actor_role='admin' THEN 'Admin quay hộ' ELSE 'HLV tự quay' END;
  v_history := coalesce(v_state->'history','[]'::jsonb) || jsonb_build_array(jsonb_build_object(
    'at',v_now::text,'user_id',p_user_id::text,'action','REROLL',
    'club',v_new.name,'actor_user_id',p_actor_user_id::text,'actor_role',p_actor_role,
    'message',v_actor_label||' dùng 1 vé thưởng sớm: '||v_old.name||' → '||v_new.name||'.'
  ));
  IF v_remaining=0 THEN
    v_history := v_history || jsonb_build_array(jsonb_build_object(
      'at',v_now::text,'user_id',p_user_id::text,'action','REWARD_FINALIZE',
      'club',v_new.name,'message','Đã dùng hết vé; CLB mới tự động chốt cuối cùng.'
    ));
  END IF;

  UPDATE public.tournament_settings SET
    setting_value = v_state || jsonb_build_object('entries',v_entries,'history',v_history,
      'updated_at',v_now::text),updated_at=v_now
    WHERE tournament_id=p_tournament_id AND setting_key='club_draft_v2';
  IF NOT FOUND THEN RAISE EXCEPTION 'Không lưu được vé; toàn bộ lượt quay được hoàn tác'; END IF;
  RETURN jsonb_build_object('ok',true,'old_club',v_old.name,'new_club',v_new.name,
    'tickets_remaining',v_remaining,'reward_finalized',v_remaining=0);
END;
$$;

REVOKE ALL ON FUNCTION public.c1_use_early_club_reroll_ticket(uuid,uuid,uuid,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.c1_use_early_club_reroll_ticket(uuid,uuid,uuid,text)
  TO service_role;
