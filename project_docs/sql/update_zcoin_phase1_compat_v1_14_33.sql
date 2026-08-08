-- =====================================================================
-- PES Arena / RankZone FC
-- Collap_V1.14.33_ZCOIN_PHASE1_COMPAT
-- SQL bổ sung tương thích database Zcoin đã tồn tại
--
-- KHÔNG tạo lại bảng.
-- KHÔNG xóa dữ liệu.
-- KHÔNG thay đổi cấu trúc các bảng hiện có.
-- Chỉ tạo index an toàn và RPC cộng/trừ Zcoin nguyên tử.
-- =====================================================================

begin;

-- Dừng an toàn nếu database không đúng cấu trúc đã kiểm tra.
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
        where table_schema = 'public'
          and table_name = 'users'
          and column_name = 'zcoin_balance'
    ) then
        raise exception 'MISSING_COLUMN_USERS_ZCOIN_BALANCE';
    end if;

    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'zcoin_transactions'
        group by table_schema, table_name
        having count(*) filter (
            where column_name in (
                'id', 'user_id', 'amount', 'balance_after', 'transaction_type',
                'source', 'description', 'metadata', 'created_at'
            )
        ) <> 9
    ) then
        raise exception 'INCOMPATIBLE_ZCOIN_TRANSACTIONS_SCHEMA';
    end if;
end
$$;

-- Các index chỉ dùng cột đã tồn tại.
create index if not exists idx_zcoin_transactions_user_created
    on public.zcoin_transactions (user_id, created_at desc);

create index if not exists idx_zcoin_transactions_created
    on public.zcoin_transactions (created_at desc);

-- Khóa chống gửi trùng được lưu trong metadata để không cần thêm cột mới.
create unique index if not exists uq_zcoin_transactions_idempotency
    on public.zcoin_transactions ((metadata ->> 'idempotency_key'))
    where coalesce(metadata ->> 'idempotency_key', '') <> '';

create or replace function public.adjust_zcoin_balance(
    p_user_id uuid,
    p_amount bigint,
    p_reason text,
    p_actor_user_id uuid,
    p_idempotency_key text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_actor public.users%rowtype;
    v_target public.users%rowtype;
    v_existing public.zcoin_transactions%rowtype;
    v_before bigint;
    v_after bigint;
    v_transaction_id uuid;
    v_reason text := btrim(coalesce(p_reason, ''));
    v_key text := btrim(coalesce(p_idempotency_key, ''));
    v_actor_can_manage boolean := false;
    v_existing_actor_id text;
    v_transaction_constraint_defs text := '';
    v_source_constraint_defs text := '';
    v_transaction_type text;
    v_source text;
begin
    if p_user_id is null or p_actor_user_id is null then
        raise exception 'INVALID_ZCOIN_USER';
    end if;

    if p_amount is null or p_amount = 0 then
        raise exception 'INVALID_ZCOIN_AMOUNT';
    end if;

    -- Database hiện dùng integer cho số dư và amount.
    if p_amount < -2147483648 or p_amount > 2147483647 then
        raise exception 'ZCOIN_AMOUNT_OUT_OF_RANGE';
    end if;

    if char_length(v_reason) < 3 or char_length(v_reason) > 300 then
        raise exception 'INVALID_ZCOIN_REASON';
    end if;

    if v_key = '' or char_length(v_key) > 120 then
        raise exception 'INVALID_ZCOIN_IDEMPOTENCY_KEY';
    end if;

    select *
    into v_actor
    from public.users
    where id = p_actor_user_id;

    if not found then
        raise exception 'ZCOIN_ACTOR_NOT_FOUND';
    end if;

    if coalesce(v_actor.admin_level, 'none') = 'owner' then
        v_actor_can_manage := true;
    elsif coalesce(v_actor.admin_level, 'none') = 'admin' then
        v_actor_can_manage := (
            coalesce(v_actor.admin_permissions::jsonb ->> 'zcoin_manage', 'false') = 'true'
        );
    end if;

    if not v_actor_can_manage then
        raise exception 'ZCOIN_PERMISSION_DENIED';
    end if;

    -- Hai request có cùng token luôn được xử lý tuần tự.
    perform pg_advisory_xact_lock(hashtext(v_key));

    select *
    into v_existing
    from public.zcoin_transactions
    where metadata ->> 'idempotency_key' = v_key
    limit 1;

    if found then
        v_existing_actor_id := coalesce(v_existing.metadata ->> 'actor_user_id', '');
        if v_existing.user_id <> p_user_id
           or v_existing.amount <> p_amount::integer
           or v_existing_actor_id <> p_actor_user_id::text then
            raise exception 'ZCOIN_IDEMPOTENCY_CONFLICT';
        end if;

        return jsonb_build_object(
            'id', v_existing.id,
            'user_id', v_existing.user_id,
            'amount', v_existing.amount,
            'balance_before', greatest(0, coalesce(
                nullif(v_existing.metadata ->> 'balance_before', '')::bigint,
                v_existing.balance_after::bigint - v_existing.amount::bigint
            )),
            'balance_after', v_existing.balance_after,
            'duplicate', true
        );
    end if;

    -- Khóa đúng ví để các request đồng thời không ghi đè số dư.
    select *
    into v_target
    from public.users
    where id = p_user_id
      and role = 'player'
    for update;

    if not found then
        raise exception 'ZCOIN_TARGET_NOT_FOUND';
    end if;

    v_before := greatest(0, coalesce(v_target.zcoin_balance, 0));
    v_after := v_before + p_amount;

    if v_after < 0 then
        raise exception 'INSUFFICIENT_ZCOIN';
    end if;

    if v_after > 2147483647 then
        raise exception 'ZCOIN_BALANCE_OUT_OF_RANGE';
    end if;

    update public.users
    set zcoin_balance = v_after::integer
    where id = p_user_id;

    -- Tự nhận diện các giá trị text phổ biến nếu database cũ có CHECK constraint.
    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '')
    into v_transaction_constraint_defs
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%transaction_type%';

    select coalesce(string_agg(pg_get_constraintdef(c.oid), ' '), '')
    into v_source_constraint_defs
    from pg_constraint c
    where c.conrelid = 'public.zcoin_transactions'::regclass
      and c.contype = 'c'
      and pg_get_constraintdef(c.oid) ilike '%source%';

    if p_amount > 0 then
        if v_transaction_constraint_defs ilike '%admin_credit%' then
            v_transaction_type := 'admin_credit';
        elsif v_transaction_constraint_defs ilike '%earn%' then
            v_transaction_type := 'earn';
        else
            v_transaction_type := 'credit';
        end if;
    else
        if v_transaction_constraint_defs ilike '%admin_debit%' then
            v_transaction_type := 'admin_debit';
        elsif v_transaction_constraint_defs ilike '%spend%' then
            v_transaction_type := 'spend';
        else
            v_transaction_type := 'debit';
        end if;
    end if;

    if v_source_constraint_defs ilike '%admin_adjustment%' then
        v_source := 'admin_adjustment';
    elsif v_source_constraint_defs ilike '%admin%' then
        v_source := 'admin';
    elsif v_source_constraint_defs ilike '%system%' then
        v_source := 'system';
    else
        v_source := 'admin_adjustment';
    end if;

    insert into public.zcoin_transactions (
        user_id,
        amount,
        balance_after,
        transaction_type,
        source,
        description,
        metadata
    ) values (
        v_target.id,
        p_amount::integer,
        v_after::integer,
        v_transaction_type,
        v_source,
        v_reason,
        jsonb_build_object(
            'balance_before', v_before,
            'reason', v_reason,
            'user_name', coalesce(nullif(v_target.display_name, ''), v_target.username, 'Player'),
            'actor_user_id', v_actor.id,
            'actor_name', coalesce(nullif(v_actor.display_name, ''), v_actor.username, 'Admin'),
            'idempotency_key', v_key,
            'app_version', 'Collap_V1.14.33_ZCOIN_PHASE1_COMPAT'
        )
    )
    returning id into v_transaction_id;

    return jsonb_build_object(
        'id', v_transaction_id,
        'user_id', v_target.id,
        'amount', p_amount,
        'balance_before', v_before,
        'balance_after', v_after,
        'duplicate', false
    );
end;
$$;

revoke all on function public.adjust_zcoin_balance(uuid, bigint, text, uuid, text)
    from public, anon, authenticated;

grant execute on function public.adjust_zcoin_balance(uuid, bigint, text, uuid, text)
    to service_role;

comment on function public.adjust_zcoin_balance(uuid, bigint, text, uuid, text) is
    'Cộng/trừ Zcoin nguyên tử trên schema hiện có; metadata lưu audit và khóa chống gửi trùng.';

commit;

-- Kết quả mong đợi: Success. No rows returned
