-- PES Arena V1.4.25 - Independent Tournament Core
-- Safe migration: creates new tournament-only tables. Does not modify Rank/Season/matches.

create extension if not exists pgcrypto;

create table if not exists public.tournaments (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    name text not null,
    short_name text,
    description text,
    status text not null default 'registration' check (status in ('draft','registration','upcoming','active','completed','cancelled')),
    registration_open boolean not null default true,
    is_visible boolean not null default true,
    created_by uuid references public.users(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.tournament_registrations (
    id uuid primary key default gen_random_uuid(),
    tournament_id uuid not null references public.tournaments(id) on delete cascade,
    user_id uuid not null references public.users(id) on delete cascade,
    status text not null default 'pending' check (status in ('pending','approved','rejected','withdrawn')),
    registered_at timestamptz not null default now(),
    reviewed_at timestamptz,
    reviewed_by uuid references public.users(id) on delete set null,
    note text,
    unique (tournament_id, user_id)
);

create table if not exists public.tournament_members (
    id uuid primary key default gen_random_uuid(),
    tournament_id uuid not null references public.tournaments(id) on delete cascade,
    user_id uuid not null references public.users(id) on delete cascade,
    status text not null default 'active' check (status in ('active','withdrawn','disqualified')),
    pot_no integer,
    seed_no integer,
    fixed_club_id text,
    fixed_club_name text,
    approved_at timestamptz not null default now(),
    approved_by uuid references public.users(id) on delete set null,
    unique (tournament_id, user_id)
);

create index if not exists idx_tournament_registrations_tournament_status
on public.tournament_registrations(tournament_id, status);
create index if not exists idx_tournament_members_tournament_status
on public.tournament_members(tournament_id, status);

insert into public.tournaments (slug, name, short_name, description, status, registration_open, is_visible)
values (
    'champion-league-arena',
    'CHAMPION LEAGUE ARENA',
    'CLA',
    'Giải đấu PES Arena theo thể thức Champions League. Người chơi đăng ký và Admin duyệt thành viên trước khi thi đấu.',
    'registration',
    true,
    true
)
on conflict (slug) do update set
    name = excluded.name,
    short_name = excluded.short_name,
    description = excluded.description,
    updated_at = now();
