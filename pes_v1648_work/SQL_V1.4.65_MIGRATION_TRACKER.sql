-- PES Arena V1.4.65 - SQL Migration Tracker
-- Chay 1 lan tren Supabase SQL Editor.
-- File nay cung lap lai migration V1.4.64 theo kieu IF NOT EXISTS de tranh thieu SQL le phi.

create table if not exists public.schema_migrations (
  migration_key text primary key,
  version text not null,
  description text,
  applied_at timestamptz not null default now()
);

-- Bao dam cau truc le phi V1.4.64 ton tai ngay ca khi ban quen chay file truoc.
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

insert into public.schema_migrations(migration_key,version,description) values
  ('V1.4.64_LE_PHI_GIAI','V1.4.64','Quan ly le phi giai 50k + trach nhiem 50k'),
  ('V1.4.65_MIGRATION_TRACKER','V1.4.65','Theo doi SQL migration trong Admin')
on conflict (migration_key) do update set version=excluded.version, description=excluded.description;
