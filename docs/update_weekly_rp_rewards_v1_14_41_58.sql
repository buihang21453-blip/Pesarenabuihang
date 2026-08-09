-- PES Arena V1.14.41.58 - Thưởng RP hoạt động tuần
create table if not exists public.weekly_rp_rewards (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete restrict,
    week_start date not null,
    reward_code text not null,
    reward_name text not null,
    reward_rp integer not null check (reward_rp > 0),
    created_at timestamptz not null default now(),
    unique (user_id, week_start, reward_code)
);

create index if not exists idx_weekly_rp_rewards_user_week
    on public.weekly_rp_rewards (user_id, week_start desc);

alter table public.weekly_rp_rewards enable row level security;

-- Backend dùng service-role key. Không mở quyền ghi trực tiếp cho trình duyệt.
