-- V1.14.41.18: Cho phép lưu Parsec ID đầy đủ có dấu #, ví dụ Salem6556#18473949.
alter table public.users drop constraint if exists users_parsec_id_format_check;

alter table public.users add constraint users_parsec_id_format_check
check (
  parsec_id is null
  or parsec_id ~ '^[A-Za-z0-9][A-Za-z0-9._-]{1,41}(#[0-9]{1,20})?$'
);
