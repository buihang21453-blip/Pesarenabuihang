-- PES Arena V1.14.41.41 · Gift Code tặng riêng theo người nhận
-- An toàn chạy lại nhiều lần; không xóa bảng hoặc dữ liệu.

begin;

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
    if coalesce(v_code.metadata ->> 'target_user_id', '') <> ''
       and (v_code.metadata ->> 'target_user_id') <> p_user_id::text then
        raise exception 'GIFT_CODE_RECIPIENT_ONLY';
    end if;

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


notify pgrst, 'reload schema';
commit;

-- Kết quả mong đợi: Success. No rows returned
