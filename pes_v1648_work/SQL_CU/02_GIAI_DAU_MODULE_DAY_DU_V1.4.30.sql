-- PES Arena V1.4.30 - Tournament Operations Modules
-- Independent from Rank/Season and public.matches.
create extension if not exists pgcrypto;

create table if not exists public.tournament_settings (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  setting_key text not null, setting_value jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now(),
  unique(tournament_id,setting_key)
);
create table if not exists public.tournament_stages (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  stage_code text not null, name text not null, sort_order int not null default 0,
  status text not null default 'draft' check(status in ('draft','open','locked','completed')),
  match_target int, min_opponents int, max_matches_per_opponent int, settings jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), unique(tournament_id,stage_code)
);
create table if not exists public.tournament_hosts (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  name text not null, region text not null default 'Bắc' check(region in ('Bắc','Trung','Nam','Khác')),
  status text not null default 'available' check(status in ('available','busy','offline')), note text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.tournament_matches (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  stage_code text not null, round_code text, leg_no int not null default 1, aggregate_group text,
  home_user_id uuid not null references public.users(id) on delete restrict, away_user_id uuid not null references public.users(id) on delete restrict,
  home_score int, away_score int, home_pen int, away_pen int,
  status text not null default 'pending' check(status in ('pending','scheduled','playing','completed','disputed','cancelled')),
  scheduled_at timestamptz, host_id uuid references public.tournament_hosts(id) on delete set null,
  winner_user_id uuid references public.users(id) on delete set null, completed_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  check(home_user_id <> away_user_id)
);
create index if not exists idx_tournament_matches_stage on public.tournament_matches(tournament_id,stage_code,status);
create index if not exists idx_tournament_matches_players on public.tournament_matches(tournament_id,home_user_id,away_user_id);

create table if not exists public.tournament_clubs (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  club_key text not null, name text not null, is_available boolean not null default true,
  selected_by uuid references public.users(id) on delete set null, selected_at timestamptz, pick_order int,
  unique(tournament_id,club_key), unique(tournament_id,selected_by)
);
create table if not exists public.tournament_schedule_requests (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  match_id uuid not null references public.tournament_matches(id) on delete cascade,
  proposed_by uuid not null references public.users(id) on delete cascade, proposed_at timestamptz not null,
  host_id uuid references public.tournament_hosts(id) on delete set null,
  status text not null default 'pending' check(status in ('pending','accepted','rejected','cancelled','disputed')),
  responded_by uuid references public.users(id) on delete set null, responded_at timestamptz, note text, created_at timestamptz not null default now()
);
create table if not exists public.tournament_reward_rules (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  name text not null, stage_code text, reward_type text not null check(reward_type in ('zcoin','badge','luckybox')),
  reward_value text not null, deadline_at timestamptz, enabled boolean not null default true, priority int not null default 100,
  created_at timestamptz not null default now()
);
create table if not exists public.tournament_reward_grants (
  id uuid primary key default gen_random_uuid(), tournament_id uuid not null references public.tournaments(id) on delete cascade,
  rule_id uuid references public.tournament_reward_rules(id) on delete set null, user_id uuid not null references public.users(id) on delete restrict,
  reward_type text not null, reward_value text not null, reason text, granted_at timestamptz not null default now(), granted_by uuid references public.users(id) on delete set null,
  unique(rule_id,user_id)
);

-- Seed three stages for the real Champion League Arena tournament.
insert into public.tournament_stages(tournament_id,stage_code,name,sort_order,status,match_target,min_opponents,max_matches_per_opponent)
select id,'stage1','GĐ1 · Phân hạng',1,'draft',5,3,2 from public.tournaments where slug='champion-league-arena'
on conflict(tournament_id,stage_code) do nothing;
insert into public.tournament_stages(tournament_id,stage_code,name,sort_order,status)
select id,'league','League Phase',2,'draft' from public.tournaments where slug='champion-league-arena'
on conflict(tournament_id,stage_code) do nothing;
insert into public.tournament_stages(tournament_id,stage_code,name,sort_order,status)
select id,'knockout','Knockout',3,'draft' from public.tournaments where slug='champion-league-arena'
on conflict(tournament_id,stage_code) do nothing;
