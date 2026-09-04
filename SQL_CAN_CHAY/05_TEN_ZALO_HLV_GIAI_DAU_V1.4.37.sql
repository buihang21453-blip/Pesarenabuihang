-- PES Arena V1.4.37 - Tên Zalo HLV trong giải đấu
-- Chạy sau file 04_DANG_KY_HOST_KHU_VUC_THANH_TOAN_V1.4.34.sql

alter table public.tournament_registrations
  add column if not exists zalo_name text;

alter table public.tournament_members
  add column if not exists zalo_name text;

-- Giới hạn hợp lý cho tên Zalo, vẫn cho NULL đối với dữ liệu cũ.
do $$
begin
  if not exists (select 1 from pg_constraint where conname='tournament_registrations_zalo_name_len_check') then
    alter table public.tournament_registrations add constraint tournament_registrations_zalo_name_len_check check (zalo_name is null or char_length(zalo_name) between 1 and 80);
  end if;
  if not exists (select 1 from pg_constraint where conname='tournament_members_zalo_name_len_check') then
    alter table public.tournament_members add constraint tournament_members_zalo_name_len_check check (zalo_name is null or char_length(zalo_name) between 1 and 80);
  end if;
end $$;
