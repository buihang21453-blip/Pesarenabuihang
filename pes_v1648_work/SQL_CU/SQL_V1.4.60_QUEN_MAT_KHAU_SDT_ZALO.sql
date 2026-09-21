-- PES Arena V1.4.60 - Quen mat khau bang Ten TK + SDT Zalo
-- Chay 1 lan tren Supabase SQL Editor.

alter table public.users
  add column if not exists zalo_phone text;

alter table public.password_reset_requests
  add column if not exists zalo_phone_snapshot text;

-- Dung de Admin tra cuu nhanh lich su theo user / thoi gian.
create index if not exists password_reset_requests_user_created_idx
  on public.password_reset_requests(user_id, created_at desc);

-- Rang buoc mem: tai khoan cu duoc phep NULL; khi co so thi chi luu chu so 9-11 ky tu.
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'users_zalo_phone_format_check'
  ) then
    alter table public.users
      add constraint users_zalo_phone_format_check
      check (zalo_phone is null or zalo_phone ~ '^[0-9]{9,11}$');
  end if;
end $$;
