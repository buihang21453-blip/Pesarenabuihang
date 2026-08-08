-- PES Arena Black Box V1: isolated telemetry tables.
create table if not exists public.blackbox_events (
  id uuid primary key,
  session_id text not null,
  user_id text null,
  request_id text null,
  page text null,
  event_type text not null,
  level text not null default 'INFO',
  message text null,
  payload jsonb not null default '{}'::jsonb,
  client jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_blackbox_events_session_created on public.blackbox_events(session_id, created_at);
create index if not exists idx_blackbox_events_user_created on public.blackbox_events(user_id, created_at desc);
create index if not exists idx_blackbox_events_level_created on public.blackbox_events(level, created_at desc);

create table if not exists public.blackbox_incidents (
  id uuid primary key,
  incident_code text not null unique,
  fingerprint text not null,
  session_id text not null,
  user_id text null,
  page text null,
  severity text not null default 'ERROR',
  status text not null default 'open',
  title text not null,
  event_id uuid null references public.blackbox_events(id) on delete set null,
  app_version text null,
  created_at timestamptz not null default now(),
  resolved_at timestamptz null
);

create index if not exists idx_blackbox_incidents_created on public.blackbox_incidents(created_at desc);
create index if not exists idx_blackbox_incidents_status on public.blackbox_incidents(status, created_at desc);
create index if not exists idx_blackbox_incidents_fingerprint on public.blackbox_incidents(fingerprint, created_at desc);

-- These tables are server-only through the Flask/Supabase service connection.
alter table public.blackbox_events enable row level security;
alter table public.blackbox_incidents enable row level security;


-- V1.3.68: Black Box is server-only. Keep Data API roles locked out while
-- granting the Flask backend service role only the operations it actually uses.
revoke all on table public.blackbox_events from anon, authenticated;
revoke all on table public.blackbox_incidents from anon, authenticated;
grant select, insert on table public.blackbox_events to service_role;
grant select, insert on table public.blackbox_incidents to service_role;
