-- PES Arena V1.4.47 - Dat lich thi dau 3 ngay
-- Moi HLV khai bao lich ranh chung cho tat ca doi thu: Hom nay / Ngay mai / Ngay kia.
create table if not exists public.tournament_availability_slots (
  id uuid primary key default gen_random_uuid(),
  tournament_id uuid not null references public.tournaments(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  slot_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(tournament_id,user_id,slot_at)
);
create index if not exists idx_tournament_availability_tournament_user
  on public.tournament_availability_slots(tournament_id,user_id,slot_at);
