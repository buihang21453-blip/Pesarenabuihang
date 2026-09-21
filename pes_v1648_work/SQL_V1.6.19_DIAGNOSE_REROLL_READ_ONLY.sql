-- PES Arena V1.6.19: ONLY READS. Run on the correct Supabase project.
-- Does not spend tickets, switch clubs, modify fixtures or expose authentication keys.
-- If slug differs, inspect: SELECT slug FROM public.tournaments;
WITH t AS (
  SELECT id FROM public.tournaments WHERE slug='champion-league-arena'
), d AS (
  SELECT tournament_id,setting_value AS v
  FROM public.tournament_settings
  WHERE setting_key='club_draft_v2' AND tournament_id IN (SELECT id FROM t)
), timing AS (
  SELECT tournament_id,setting_value AS v
  FROM public.tournament_settings
  WHERE setting_key='competition_timing' AND tournament_id IN (SELECT id FROM t)
)
SELECT
  (SELECT count(*) FROM t) AS tournament_found,
  to_regprocedure('public.c1_use_early_club_reroll_ticket(uuid,uuid,uuid,text)') IS NOT NULL AS rpc_installed,
  CASE WHEN to_regprocedure('public.c1_use_early_club_reroll_ticket(uuid,uuid,uuid,text)') IS NULL THEN false
       ELSE has_function_privilege('service_role', 'public.c1_use_early_club_reroll_ticket(uuid,uuid,uuid,text)', 'EXECUTE') END AS service_role_execute,
  (SELECT status FROM public.tournament_stages WHERE tournament_id IN (SELECT id FROM t) AND stage_code='league' LIMIT 1) AS league_status,
  (SELECT v->>'system_assigned' FROM d LIMIT 1) AS base_clubs_assigned,
  (SELECT v->>'completed' FROM d LIMIT 1) AS draft_completed,
  (SELECT v->>'tier_club_pot_rule' FROM d LIMIT 1) AS tier_pot_rule,
  (SELECT CASE WHEN jsonb_typeof(v->'all_order')='array' THEN jsonb_array_length(v->'all_order') END FROM d LIMIT 1) AS base_order_count,
  (SELECT CASE WHEN jsonb_typeof(v->'order')='array' THEN jsonb_array_length(v->'order') END FROM d LIMIT 1) AS rewarded_hlv_count,
  (SELECT v->>'gd2_reward_ticket_deadline_at' FROM timing LIMIT 1) AS reward_deadline,
  (SELECT count(*) FROM public.tournament_members WHERE tournament_id IN (SELECT id FROM t) AND status='active') AS active_hlv,
  (SELECT count(*) FROM public.tournament_members WHERE tournament_id IN (SELECT id FROM t) AND status='active' AND fixed_club_name IS NOT NULL) AS hlv_with_club,
  (SELECT count(*) FROM public.tournament_clubs WHERE tournament_id IN (SELECT id FROM t) AND selected_by IS NOT NULL) AS clubs_owned,
  (SELECT count(*) FROM public.tournament_clubs WHERE tournament_id IN (SELECT id FROM t) AND is_available=true AND selected_by IS NULL) AS free_clubs,
  (SELECT count(*) FROM public.tournament_matches WHERE tournament_id IN (SELECT id FROM t) AND stage_code='league') AS league_match_count;

-- Only aggregate per HLV; no account UUID or personally identifying data in result.
WITH t AS (SELECT id FROM public.tournaments WHERE slug='champion-league-arena'),
d AS (SELECT setting_value AS v FROM public.tournament_settings WHERE tournament_id IN (SELECT id FROM t) AND setting_key='club_draft_v2' LIMIT 1)
SELECT
  x.value->>'status' AS draft_status,
  x.value->>'allocation_type' AS allocation_type,
  x.value->>'reward_finalized' AS finalized,
  x.value->>'tickets_remaining' AS tickets_remaining,
  count(*) AS hlv_count
FROM d, LATERAL jsonb_each(coalesce(d.v->'entries','{}'::jsonb)) AS x(key,value)
WHERE x.value->>'allocation_type'='EARLY_REWARD'
GROUP BY 1,2,3,4 ORDER BY 1,3,4;

-- Check the actual runtime API key type LOCALLY in Vercel env settings only.
-- SUPABASE_SERVICE_ROLE_KEY must be a service_role credential, never paste its value into chat.
