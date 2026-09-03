-- =====================================================================
-- PES Arena · Collap_V1.14.38_ZCOIN_REWARDS_MODULE
-- Điểm danh 7 ngày + Gift Code có thời hạn
--
-- AN TOÀN DỮ LIỆU:
-- - Không xóa bảng hoặc dữ liệu hiện có.
-- - Tận dụng daily_checkins, gift_codes, gift_code_redemptions đang có.
-- - Chỉ bổ sung cột/index/RPC còn thiếu.
-- - Tiếp tục dùng users.zcoin_balance và zcoin_transactions hiện tại.
-- =====================================================================

begin;

create extension if not exists pgcrypto;

-- Dừng an toàn nếu nền tảng Zcoin giai đoạn 1 chưa tồn tại.
do $$
begin
    if to_regclass('public.users') is null then
        raise exception 'MISSING_TABLE_PUBLIC_USERS';
    end if;
    if to_regclass('public.zcoin_transactions') is null then
        raise exception 'MISSING_TABLE_ZCOIN_TRANSACTIONS';
    end if;
    if not exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'users' and column_name = 'zcoin_balance'
    ) then
        raise exception 'MISSING_COLUMN_USERS_ZCOIN_BALANCE';
    end if;
end
$$;

create table if not exists public.daily_checkins (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.users(id) on delete cascade,
    checkin_date date,
    streak_day integer,
    reward_amount integer,
    balance_after integer,
    created_at timestamptz default now(),
    metadata jsonb default '{}'::jsonb
);

alter table public.daily_checkins add column if not exists user_id uuid references public.users(id) on delete cascade;
alter table public.daily_checkins add column if not exists checkin_date date;
alter table public.daily_checkins add column if not exists streak_day integer;
alter table public.daily_checkins add column if not exists reward_amount integer;
alter table public.daily_checkins add column if not exists balance_after integer;
alter table public.daily_checkins add column if not exists created_at timestamptz default now();
alter table public.daily_checkins add column if not exists metadata jsonb default '{}'::jsonb;

-- Cột bắt buộc từ schema thử nghiệm cũ không được làm hỏng insert của module mới.
do $$
declare v_column record;
begin
    for v_column in
        select c.column_name
        from information_schema.columns c
        where c.table_schema = 'public'
          and c.table_name = 'daily_checkins'
          and c.is_nullable = 'NO'
          and c.is_identity = 'NO'
          and c.is_generated = 'NEVER'
          and c.column_name not in ('id','user_id','checkin_date','streak_day','reward_amount','balance_after','created_at','metadata')
          and not exists (
              select 1 from information_schema.table_constraints tc
              join information_schema.key_column_usage kcu
                on tc.constraint_name = kcu.constraint_name and tc.table_schema = kcu.table_schema
              where tc.table_schema = 'public' and tc.table_name = 'daily_checkins'
                and tc.constraint_type = 'PRIMARY KEY' and kcu.column_name = c.column_name
          )
    loop
        execute format('alter table public.daily_checkins alter column %I drop not null', v_column.column_name);
    end loop;
end
$$;

-- Các bản cũ thường đã có created_at nhưng chưa có checkin_date.
update public.daily_checkins
set checkin_date = (created_at at time zone 'Asia/Ho_Chi_Minh')::date
where checkin_date is null and created_at is not null;

-- Chỉ tạo unique index khi dữ liệu cũ không có nhiều bản ghi trong cùng ngày.
do $$
begin
    if not exists (
        select 1 from public.daily_checkins
        where user_id is not null and checkin_date is not null
        group by user_id, checkin_date
        having count(*) > 1
    ) then
        execute 'create unique index if not exists uq_daily_checkins_user_date on public.daily_checkins (user_id, checkin_date) where user_id is not null and checkin_date is not null';
    end if;
end
$$;
create index if not exists idx_daily_checkins_user_date_desc
    on public.daily_checkins (user_id, checkin_date desc);

create table if not exists public.gift_codes (
    id uuid primary key default gen_random_uuid(),
    code text,
    reward_amount integer,
    starts_at timestamptz,
    expires_at timestamptz,
    max_redemptions integer,
    redemption_count integer default 0,
    per_user_limit integer default 1,
    is_active boolean default true,
    created_by uuid references public.users(id) on delete set null,
    created_by_name text,
    note text,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

alter table public.gift_codes add column if not exists code text;
alter table public.gift_codes add column if not exists reward_amount integer;
alter table public.gift_codes add column if not exists starts_at timestamptz;
alter table public.gift_codes add column if not exists expires_at timestamptz;
alter table public.gift_codes add column if not exists max_redemptions integer;
alter table public.gift_codes add column if not exists redemption_count integer default 0;
alter table public.gift_codes add column if not exists per_user_limit integer default 1;
alter table public.gift_codes add column if not exists is_active boolean default true;
alter table public.gift_codes add column if not exists created_by uuid references public.users(id) on delete set null;
alter table public.gift_codes add column if not exists created_by_name text;
alter table public.gift_codes add column if not exists note text;
alter table public.gift_codes add column if not exists metadata jsonb default '{}'::jsonb;
alter table public.gift_codes add column if not exists created_at timestamptz default now();
alter table public.gift_codes add column if not exists updated_at timestamptz default now();

-- Nới các cột legacy bắt buộc nhưng module mới không còn dùng; không xóa cột hoặc dữ liệu.
do $$
declare v_column record;
begin
    for v_column in
        select c.column_name
        from information_schema.columns c
        where c.table_schema = 'public'
          and c.table_name = 'gift_codes'
          and c.is_nullable = 'NO'
          and c.is_identity = 'NO'
          and c.is_generated = 'NEVER'
          and c.column_name not in ('id','code','reward_amount','starts_at','expires_at','max_redemptions','redemption_count','per_user_limit','is_active','created_by','created_by_name','note','metadata','created_at','updated_at')
          and not exists (
              select 1 from information_schema.table_constraints tc
              join information_schema.key_column_usage kcu
                on tc.constraint_name = kcu.constraint_name and tc.table_schema = kcu.table_schema
              where tc.table_schema = 'public' and tc.table_name = 'gift_codes'
                and tc.constraint_type = 'PRIMARY KEY' and kcu.column_name = c.column_name
          )
    loop
        execute format('alter table public.gift_codes alter column %I drop not null', v_column.column_name);
    end loop;
end
$$;

update public.gift_codes
set starts_at = coalesce(starts_at, created_at, now()),
    max_redemptions = greatest(1, coalesce(max_redemptions, 1)),
    redemption_count = greatest(0, coalesce(redemption_count, 0)),
    per_user_limit = greatest(1, coalesce(per_user_limit, 1)),
    is_active = coalesce(is_active, true),
    metadata = coalesce(metadata, '{}'::jsonb)
where starts_at is null
   or max_redemptions is null
   or redemption_count is null
   or per_user_limit is null
   or is_active is null
   or metadata is null;

create index if not exists idx_gift_codes_code_upper
    on public.gift_codes (upper(code));
create index if not exists idx_gift_codes_active_expiry
    on public.gift_codes (is_active, expires_at);

-- Chỉ tạo unique index khi dữ liệu cũ không có mã trùng.
do $$
begin
    if not exists (
        select 1
        from public.gift_codes
        where coalesce(btrim(code), '') <> ''
        group by upper(btrim(code))
        having count(*) > 1
    ) then
        execute 'create unique index if not exists uq_gift_codes_code_upper on public.gift_codes (upper(btrim(code))) where coalesce(btrim(code), '''') <> ''''';
    end if;
end
$$;

create table if not exists public.gift_code_redemptions (
    id uuid primary key default gen_random_uuid(),
    gift_code_id uuid references public.gift_codes(id) on delete cascade,
    user_id uuid references public.users(id) on delete cascade,
    reward_amount integer,
    balance_after integer,
    idempotency_key text,
    redeemed_at timestamptz default now(),
    metadata jsonb default '{}'::jsonb
);

alter table public.gift_code_redemptions add column if not exists gift_code_id uuid references public.gift_codes(id) on delete cascade;
alter table public.gift_code_redemptions add column if not exists user_id uuid references public.users(id) on delete cascade;
alter table public.gift_code_redemptions add column if not exists reward_amount integer;
alter table public.gift_code_redemptions add column if not exists balance_after integer;
alter table public.gift_code_redemptions add column if not exists idempotency_key text;
alter table public.gift_code_redemptions add column if not exists redeemed_at timestamptz default now();
alter table public.gift_code_redemptions add column if not exists metadata jsonb default '{}'::jsonb;

-- Cho phép schema cũ tiếp tục tồn tại dù có các alias bắt buộc như code_id/redeemed_by.
do $$
declare v_column record;
begin
    for v_column in
        select c.column_name
        from information_schema.columns c
        where c.table_schema = 'public'
          and c.table_name = 'gift_code_redemptions'
          and c.is_nullable = 'NO'
          and c.is_identity = 'NO'
          and c.is_generated = 'NEVER'
          and c.column_name not in ('id','gift_code_id','user_id','reward_amount','balance_after','idempotency_key','redeemed_at','metadata')
          and not exists (
              select 1 from information_schema.table_constraints tc
              join information_schema.key_column_usage kcu
                on tc.constraint_name = kcu.constraint_name and tc.table_schema = kcu.table_schema
              where tc.table_schema = 'public' and tc.table_name = 'gift_code_redemptions'
                and tc.constraint_type = 'PRIMARY KEY' and kcu.column_name = c.column_name
          )
    loop
        execute format('alter table public.gift_code_redemptions alter column %I drop not null', v_column.column_name);
    end loop;
end
$$;

create index if not exists idx_gift_redemptions_code_user
    on public.gift_code_redemptions (gift_code_id, user_id, redeemed_at desc);
create index if not exists idx_gift_redemptions_user
    on public.gift_code_redemptions (user_id, redeemed_at desc);
create unique index if not exists uq_gift_redemptions_idempotency
    on public.gift_code_redemptions (idempotency_key)
    where coalesce(idempotency_key, '') <> '';

-- =====================================================================
-- RPC nhận điểm danh nguyên tử
-- =====================================================================
create or replace function public.claim_daily_checkin(
    p_user_id uuid,
    p_request_key text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user public.users%rowtype;
    v_existing public.daily_checkins%rowtype;
    v_last public.daily_checkins%rowtype;
    v_today date := (now() at time zone 'Asia/Ho_Chi_Minh')::date;
    v_streak integer := 1;
    v_reward integer := 100;
    v_before bigint;
    v_after bigint;
    v_checkin_id uuid;
    v_key text := btrim(coalesce(p_request_key, ''));
    v_transaction_type text;
    v_source text;
    v_transaction_constraints text := '';
    v_source_constraints text := '';
begin
    if p_user_id is null then
        raise exception 'DAILY_CHECKIN_INVALID_USER';
    end if;
    if v_key = '' or char_length(v_key) > 120 then
        raise exception 'DAILY_CHECKIN_INVALID_REQUEST_KEY';
    end if;

    perform pg_advisory_xact_lock(hashtext('daily-checkin:' || p_user_id::text || ':' || v_today::text));

    select * into v_existing
    from public.daily_checkins
    where user_id = p_user_id and checkin_date = v_today
    order by created_at desc
    limit 1;

    if found then
        return jsonb_build_object(
            'id', v_existing.id,
            'reward_amount', greatest(0, coalesce(v_existing.reward_amount, 0)),
            'streak_day', greatest(1, coalesce(v_existing.streak_day, 1)),
            'balance_after', greatest(0, coalesce(v_existing.balance_after, 0)),
            'duplicate', true
        );
    end if;

    select * into v_user
    from public.users
    where id = p_user_id and role = 'player'
    for update;
    if not found then
        raise exception 'DAILY_CHECKIN_USER_NOT_FOUND';
    end if;

    select * into v_last
    from public.daily_checkins
    where user_id = p_user_id and checkin_date < v_today
    order by checkin_date desc, created_at desc
    limit 1;

    if found and v_last.checkin_date = v_today - 1 then
        v_streak := case
            when coalesce(v_last.streak_day, 0) >= 7 then 1
            else greatest(1, coalesce(v_last.streak_day, 0) + 1)
        end;
    else
        v_streak := 1;
    end if;

    v_reward := case v_streak
        when 1 then 100
        when 2 then 120
        when 3 then 150
        when 4 then 180
        when 5 then 220
        when 6 then 280
        else 450
    end;

    v_before := greatest(0, coalesce(v_user.zcoin_balance, 0));
    v_after := v_before + v_reward;
    if v_after > 2147483647 then
        raise exception 'ZCOIN_BALANCE_OUT_OF_RANGE';
    end if;

    update public.users set zcoin_balance = v_after::integer where id = p_user_id;

    insert into public.daily_checkins (
        user_id, checkin_date, streak_day, reward_amount, balance_after, created_at, metadata
    ) values (
        p_user_id, v_today, v_streak, v_reward, v_after::integer, now(),
        jsonb_build_object('idempotency_key', v_key, 'app_version', 'Collap_V1.14.38_ZCOIN_REWARDS_MODULE')
    ) returning id into v_checkin_id;

    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '') into v_transaction_constraints
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%transaction_type%';

    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '') into v_source_constraints
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%source%';

    if v_transaction_constraints ilike '%earn%' then v_transaction_type := 'earn';
    elsif v_transaction_constraints ilike '%admin_credit%' then v_transaction_type := 'admin_credit';
    elsif v_transaction_constraints ilike '%credit%' then v_transaction_type := 'credit';
    else v_transaction_type := 'earn';
    end if;

    if v_source_constraints ilike '%daily_checkin%' then v_source := 'daily_checkin';
    elsif v_source_constraints ilike '%system%' then v_source := 'system';
    elsif v_source_constraints ilike '%admin_adjustment%' then v_source := 'admin_adjustment';
    elsif v_source_constraints ilike '%admin%' then v_source := 'admin';
    else v_source := 'daily_checkin';
    end if;

    insert into public.zcoin_transactions (
        user_id, amount, balance_after, transaction_type, source, description, metadata
    ) values (
        p_user_id, v_reward, v_after::integer, v_transaction_type, v_source,
        'Điểm danh hằng ngày',
        jsonb_build_object(
            'balance_before', v_before,
            'streak_day', v_streak,
            'checkin_id', v_checkin_id,
            'idempotency_key', 'daily:' || v_key,
            'app_version', 'Collap_V1.14.38_ZCOIN_REWARDS_MODULE'
        )
    );

    return jsonb_build_object(
        'id', v_checkin_id,
        'reward_amount', v_reward,
        'streak_day', v_streak,
        'balance_before', v_before,
        'balance_after', v_after,
        'duplicate', false
    );
end;
$$;

revoke all on function public.claim_daily_checkin(uuid, text) from public, anon, authenticated;
grant execute on function public.claim_daily_checkin(uuid, text) to service_role;

-- =====================================================================
-- RPC đổi Gift Code nguyên tử
-- =====================================================================
create or replace function public.redeem_zcoin_gift_code(
    p_user_id uuid,
    p_code text,
    p_request_key text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user public.users%rowtype;
    v_code public.gift_codes%rowtype;
    v_existing public.gift_code_redemptions%rowtype;
    v_normalized text := upper(btrim(coalesce(p_code, '')));
    v_key text := btrim(coalesce(p_request_key, ''));
    v_user_uses integer := 0;
    v_before bigint;
    v_after bigint;
    v_redemption_id uuid;
    v_transaction_type text;
    v_source text;
    v_transaction_constraints text := '';
    v_source_constraints text := '';
begin
    if p_user_id is null then raise exception 'GIFT_CODE_INVALID_USER'; end if;
    if v_normalized = '' or char_length(v_normalized) > 32 then raise exception 'GIFT_CODE_INVALID'; end if;
    if v_key = '' or char_length(v_key) > 120 then raise exception 'GIFT_CODE_INVALID_REQUEST_KEY'; end if;

    perform pg_advisory_xact_lock(hashtext('gift-redemption:' || v_key));

    select * into v_existing
    from public.gift_code_redemptions
    where idempotency_key = v_key
    limit 1;
    if found then
        return jsonb_build_object(
            'id', v_existing.id,
            'reward_amount', greatest(0, coalesce(v_existing.reward_amount, 0)),
            'balance_after', greatest(0, coalesce(v_existing.balance_after, 0)),
            'duplicate', true
        );
    end if;

    select * into v_code
    from public.gift_codes
    where upper(btrim(code)) = v_normalized
    order by created_at desc
    limit 1
    for update;
    if not found then raise exception 'GIFT_CODE_NOT_FOUND'; end if;
    if not coalesce(v_code.is_active, true) then raise exception 'GIFT_CODE_INACTIVE'; end if;
    if coalesce(v_code.starts_at, now()) > now() then raise exception 'GIFT_CODE_NOT_STARTED'; end if;
    if v_code.expires_at is not null and v_code.expires_at <= now() then raise exception 'GIFT_CODE_EXPIRED'; end if;
    if greatest(0, coalesce(v_code.redemption_count, 0)) >= greatest(1, coalesce(v_code.max_redemptions, 1)) then
        raise exception 'GIFT_CODE_DEPLETED';
    end if;
    if coalesce(v_code.reward_amount, 0) <= 0 then raise exception 'GIFT_CODE_INVALID_REWARD'; end if;

    select count(*) into v_user_uses
    from public.gift_code_redemptions
    where gift_code_id = v_code.id and user_id = p_user_id;
    if v_user_uses >= greatest(1, coalesce(v_code.per_user_limit, 1)) then
        raise exception 'GIFT_CODE_USER_LIMIT';
    end if;

    select * into v_user
    from public.users
    where id = p_user_id and role = 'player'
    for update;
    if not found then raise exception 'GIFT_CODE_USER_NOT_FOUND'; end if;

    v_before := greatest(0, coalesce(v_user.zcoin_balance, 0));
    v_after := v_before + v_code.reward_amount;
    if v_after > 2147483647 then raise exception 'ZCOIN_BALANCE_OUT_OF_RANGE'; end if;

    update public.users set zcoin_balance = v_after::integer where id = p_user_id;

    insert into public.gift_code_redemptions (
        gift_code_id, user_id, reward_amount, balance_after, idempotency_key, redeemed_at, metadata
    ) values (
        v_code.id, p_user_id, v_code.reward_amount, v_after::integer, v_key, now(),
        jsonb_build_object('code', v_normalized, 'app_version', 'Collap_V1.14.38_ZCOIN_REWARDS_MODULE')
    ) returning id into v_redemption_id;

    update public.gift_codes
    set redemption_count = greatest(0, coalesce(redemption_count, 0)) + 1,
        updated_at = now()
    where id = v_code.id;

    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '') into v_transaction_constraints
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%transaction_type%';

    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '') into v_source_constraints
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%source%';

    if v_transaction_constraints ilike '%earn%' then v_transaction_type := 'earn';
    elsif v_transaction_constraints ilike '%admin_credit%' then v_transaction_type := 'admin_credit';
    elsif v_transaction_constraints ilike '%credit%' then v_transaction_type := 'credit';
    else v_transaction_type := 'earn';
    end if;

    if v_source_constraints ilike '%gift_code%' then v_source := 'gift_code';
    elsif v_source_constraints ilike '%system%' then v_source := 'system';
    elsif v_source_constraints ilike '%admin_adjustment%' then v_source := 'admin_adjustment';
    elsif v_source_constraints ilike '%admin%' then v_source := 'admin';
    else v_source := 'gift_code';
    end if;

    insert into public.zcoin_transactions (
        user_id, amount, balance_after, transaction_type, source, description, metadata
    ) values (
        p_user_id, v_code.reward_amount, v_after::integer, v_transaction_type, v_source,
        'Đổi Gift Code ' || v_normalized,
        jsonb_build_object(
            'balance_before', v_before,
            'gift_code_id', v_code.id,
            'gift_code', v_normalized,
            'redemption_id', v_redemption_id,
            'idempotency_key', 'gift:' || v_key,
            'app_version', 'Collap_V1.14.38_ZCOIN_REWARDS_MODULE'
        )
    );

    return jsonb_build_object(
        'id', v_redemption_id,
        'code', v_normalized,
        'reward_amount', v_code.reward_amount,
        'balance_before', v_before,
        'balance_after', v_after,
        'duplicate', false
    );
end;
$$;

revoke all on function public.redeem_zcoin_gift_code(uuid, text, text) from public, anon, authenticated;
grant execute on function public.redeem_zcoin_gift_code(uuid, text, text) to service_role;

commit;

-- Kết quả mong đợi: Success. No rows returned
