-- PES Arena V1.3.0 - chạy một lần trên Supabase SQL Editor
create table if not exists public.match_series (
 id uuid primary key default gen_random_uuid(), room_id uuid, mode_code text not null,
 player1_id uuid not null, player2_id uuid not null, status text not null default 'waiting',
 player1_wins integer not null default 0, player2_wins integer not null default 0,
 draw_games integer not null default 0, aggregate_player1 integer not null default 0,
 aggregate_player2 integer not null default 0, winner_user_id uuid, result_code text,
 forfeit_user_id uuid, rp_applied boolean not null default false,
 rp_player1 integer not null default 0, rp_player2 integer not null default 0,
 metadata jsonb not null default '{}'::jsonb, started_at timestamptz default now(),
 completed_at timestamptz, created_at timestamptz default now(), updated_at timestamptz default now()
);
create table if not exists public.match_series_games (
 id uuid primary key default gen_random_uuid(), series_id uuid not null references public.match_series(id) on delete cascade,
 game_no integer not null, match_id uuid, player1_team text, player2_team text,
 player1_score integer, player2_score integer, winner_side text,
 status text not null default 'waiting', metadata jsonb not null default '{}'::jsonb,
 started_at timestamptz, completed_at timestamptz, created_at timestamptz default now(), unique(series_id,game_no)
);
create table if not exists public.match_series_club_actions (
 id uuid primary key default gen_random_uuid(), series_id uuid not null references public.match_series(id) on delete cascade,
 game_no integer, user_id uuid, action_type text not null, club_code text not null,
 action_order integer not null, created_at timestamptz default now(), unique(series_id,action_type,club_code)
);
create index if not exists idx_match_series_players_status on public.match_series(player1_id,player2_id,status);
create index if not exists idx_match_series_games_series on public.match_series_games(series_id,game_no);
create index if not exists idx_match_series_actions_series on public.match_series_club_actions(series_id,action_order);
