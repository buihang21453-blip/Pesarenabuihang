-- PES Arena V1.4.55 - Hoan thien Tournament workflow
-- Chuan hoa Giai doan 1: 6 tran / HLV, 3 doi thu, toi da 2 tran / cap.
update public.tournament_stages s
set match_target = 6,
    min_opponents = 3,
    max_matches_per_opponent = 2,
    updated_at = now()
from public.tournaments t
where s.tournament_id = t.id
  and t.slug = 'champion-league-arena'
  and s.stage_code = 'stage1';
