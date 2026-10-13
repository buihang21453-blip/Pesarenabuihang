-- PES Arena V1.6.82 - read-path indexes
-- Run once in Supabase SQL Editor. Safe to re-run (IF NOT EXISTS).
-- Purpose: accelerate personal match-history pagination and common status filtering.

create index if not exists idx_matches_player1_created_at
    on public.matches (player1_id, created_at desc);

create index if not exists idx_matches_player2_created_at
    on public.matches (player2_id, created_at desc);

create index if not exists idx_matches_player1_status_created_at
    on public.matches (player1_id, status, created_at desc);

create index if not exists idx_matches_player2_status_created_at
    on public.matches (player2_id, status, created_at desc);

-- season_player_stats is the official current/historical ranking source.
create index if not exists idx_season_player_stats_season_rank
    on public.season_player_stats (season_number, rank_points desc, wins desc);
