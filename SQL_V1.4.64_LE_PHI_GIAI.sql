-- PES Arena V1.4.64 - Quan ly le phi giai
-- 50.000d le phi + 50.000d trach nhiem. Safe migration.

alter table public.tournament_registrations
  add column if not exists amount_paid integer not null default 0,
  add column if not exists fee_amount integer not null default 50000,
  add column if not exists responsibility_amount integer not null default 50000,
  add column if not exists responsibility_deducted integer not null default 0,
  add column if not exists amount_refunded integer not null default 0,
  add column if not exists payment_note text,
  add column if not exists payment_updated_at timestamptz,
  add column if not exists payment_updated_by uuid references public.users(id) on delete set null;

create table if not exists public.tournament_fee_unmatched (
  id uuid primary key default gen_random_uuid(),
  tournament_id uuid not null references public.tournaments(id) on delete cascade,
  payer_name text not null,
  zalo_contact text,
  amount_paid integer not null check (amount_paid > 0),
  note text,
  status text not null default 'waiting' check (status in ('waiting','linked','cancelled')),
  linked_registration_id uuid references public.tournament_registrations(id) on delete set null,
  linked_user_id uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  created_by uuid references public.users(id) on delete set null,
  linked_at timestamptz,
  linked_by uuid references public.users(id) on delete set null
);
create index if not exists idx_tournament_fee_unmatched_tournament_status on public.tournament_fee_unmatched(tournament_id,status);
