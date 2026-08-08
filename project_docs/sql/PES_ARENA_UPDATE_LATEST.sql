-- PES Arena V1.3.15 - quyền mở khóa chế độ Rank theo tài khoản
-- Chạy một lần trong Supabase SQL Editor.

create table if not exists public.rank_mode_user_unlocks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    mode_code text not null,
    is_unlocked boolean not null default true,
    updated_by uuid references public.users(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint rank_mode_user_unlocks_mode_check check (
        mode_code in (
            'rank_random',
            'random3_pick1',
            'tactical_bo3',
            'bo3',
            'ban_pick_bo3',
            'home_away'
        )
    ),
    constraint rank_mode_user_unlocks_user_mode_unique unique (user_id, mode_code)
);

create index if not exists idx_rank_mode_user_unlocks_user
    on public.rank_mode_user_unlocks(user_id)
    where is_unlocked = true;

comment on table public.rank_mode_user_unlocks is
    'Quyền do Admin mở riêng từng chế độ Rank cho từng tài khoản; không thay đổi công tắc bật/tắt toàn hệ thống.';
