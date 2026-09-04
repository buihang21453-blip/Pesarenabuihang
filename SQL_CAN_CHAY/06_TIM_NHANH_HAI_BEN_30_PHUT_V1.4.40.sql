-- PES Arena V1.4.40
-- Tìm Nhanh chỉ ghép khi CẢ HAI HLV đã chủ động bấm Tìm Nhanh trong 30 phút gần nhất.

alter table public.users
    add column if not exists quick_match_requested_at timestamptz null;

create index if not exists idx_users_quick_match_requested_at
    on public.users (quick_match_requested_at);

comment on column public.users.quick_match_requested_at is
    'Lần gần nhất HLV chủ động bấm Tìm Nhanh. Chỉ có hiệu lực ghép trong 30 phút.';
