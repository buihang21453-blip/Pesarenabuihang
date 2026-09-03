-- PES Arena V1.4.31 - Tournament Test Mode
-- Sandbox JSON only. Does NOT reference Rank matches, RP, Zcoin, Lucky Box or real tournament members.
create table if not exists public.tournament_test_sandboxes (
  id uuid primary key default gen_random_uuid(),
  admin_user_id uuid not null references public.users(id) on delete cascade,
  state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(admin_user_id)
);
create index if not exists idx_tournament_test_sandboxes_admin on public.tournament_test_sandboxes(admin_user_id);
