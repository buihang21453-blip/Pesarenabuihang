-- PES Arena V1.4.34 - Dang ky giai: Host + khu vuc + xac nhan chuyen khoan
-- Safe migration: chi bo sung cot cho tournament_registrations.

alter table public.tournament_registrations
  add column if not exists has_host boolean,
  add column if not exists host_region text,
  add column if not exists payment_status text not null default 'unreported',
  add column if not exists payment_reported_at timestamptz;

do $$ begin
  if not exists (select 1 from pg_constraint where conname='tournament_registrations_host_region_check') then
    alter table public.tournament_registrations add constraint tournament_registrations_host_region_check check (host_region is null or host_region in ('Bắc','Trung','Nam'));
  end if;
  if not exists (select 1 from pg_constraint where conname='tournament_registrations_payment_status_check') then
    alter table public.tournament_registrations add constraint tournament_registrations_payment_status_check check (payment_status in ('unreported','reported','verified'));
  end if;
end $$;
