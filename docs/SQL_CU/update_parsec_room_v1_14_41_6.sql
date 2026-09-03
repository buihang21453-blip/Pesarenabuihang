-- V1.14.41.6: Parsec ID trong hồ sơ và link tạm thời theo phòng.
alter table public.users add column if not exists parsec_id text;
alter table public.match_rooms add column if not exists parsec_link text;

alter table public.users drop constraint if exists users_parsec_id_format_check;
alter table public.users add constraint users_parsec_id_format_check
check (parsec_id is null or parsec_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,41}(#[0-9]{1,20})?$');

alter table public.match_rooms drop constraint if exists match_rooms_parsec_link_check;
alter table public.match_rooms add constraint match_rooms_parsec_link_check
check (
  parsec_link is null
  or parsec_link ~ '^https://parsec[.]gg/g/[^[:space:]]+$'
);
