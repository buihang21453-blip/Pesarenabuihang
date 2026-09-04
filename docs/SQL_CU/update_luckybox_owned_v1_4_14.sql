-- PES Arena V1.4.14 · Lucky Box sở hữu
-- Thêm số lượt Lucky Box miễn phí, backfill thưởng Season đã trao,
-- và cho phép open_lucky_box ưu tiên dùng lượt sở hữu trước Zcoin.
begin;

create table if not exists public.lucky_box_balance_transactions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete restrict,
    amount integer not null,
    balance_after integer not null check (balance_after >= 0),
    source text not null default 'system',
    description text not null default '',
    idempotency_key text not null unique,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
create index if not exists lucky_box_balance_transactions_user_time_idx
    on public.lucky_box_balance_transactions(user_id, created_at desc);

do $$
declare v_missing boolean;
begin
    select not exists (
        select 1 from information_schema.columns
        where table_schema='public' and table_name='users' and column_name='lucky_box_balance'
    ) into v_missing;
    if v_missing then
        alter table public.users add column lucky_box_balance integer not null default 0 check (lucky_box_balance >= 0);
        if to_regclass('public.rank_season_rewards') is not null then
            update public.users u
            set lucky_box_balance = coalesce(x.total_boxes,0)
            from (
                select user_id, sum(greatest(0,coalesce(lucky_box_reward,0)))::integer total_boxes
                from public.rank_season_rewards
                where lower(coalesce(status,''))='granted'
                group by user_id
            ) x
            where u.id=x.user_id;

            insert into public.lucky_box_balance_transactions(user_id,amount,balance_after,source,description,idempotency_key,metadata)
            select r.user_id, greatest(0,coalesce(r.lucky_box_reward,0)),
                   u.lucky_box_balance, 'season_reward',
                   'Thưởng Lucky Box Season '||r.season_number||' Top '||r.position,
                   'season:'||r.season_number||':rank:'||r.position||':luckybox',
                   jsonb_build_object('season_number',r.season_number,'position',r.position,'backfilled',true)
            from public.rank_season_rewards r
            join public.users u on u.id=r.user_id
            where lower(coalesce(r.status,''))='granted' and coalesce(r.lucky_box_reward,0)>0
            on conflict(idempotency_key) do nothing;
        end if;
    end if;
end $$;

alter table public.lucky_box_openings add column if not exists lucky_box_balance_before integer;
alter table public.lucky_box_openings add column if not exists lucky_box_balance_after integer;
alter table public.lucky_box_openings add column if not exists payment_method text;

create or replace function public.adjust_lucky_box_balance(
    p_user_id uuid,
    p_amount integer,
    p_source text,
    p_description text,
    p_idempotency_key text,
    p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_user public.users%rowtype;
    v_existing public.lucky_box_balance_transactions%rowtype;
    v_after integer;
begin
    if p_user_id is null or coalesce(btrim(p_idempotency_key),'')='' then
        raise exception 'LUCKY_BOX_BALANCE_INVALID_REQUEST';
    end if;
    perform pg_advisory_xact_lock(hashtext('luckybox-balance:'||p_idempotency_key));
    select * into v_existing from public.lucky_box_balance_transactions where idempotency_key=p_idempotency_key limit 1;
    if found then
        return jsonb_build_object('ok',true,'duplicate',true,'balance_after',v_existing.balance_after);
    end if;
    select * into v_user from public.users where id=p_user_id for update;
    if not found then raise exception 'LUCKY_BOX_USER_NOT_FOUND'; end if;
    v_after := coalesce(v_user.lucky_box_balance,0) + coalesce(p_amount,0);
    if v_after < 0 then raise exception 'INSUFFICIENT_LUCKY_BOX'; end if;
    update public.users set lucky_box_balance=v_after where id=p_user_id;
    insert into public.lucky_box_balance_transactions(user_id,amount,balance_after,source,description,idempotency_key,metadata)
    values(p_user_id,p_amount,v_after,coalesce(nullif(btrim(p_source),''),'system'),coalesce(p_description,''),p_idempotency_key,coalesce(p_metadata,'{}'::jsonb));
    return jsonb_build_object('ok',true,'duplicate',false,'balance_after',v_after);
end;
$$;

-- Giữ lõi Lucky Box cũ làm hàm trả Zcoin; wrapper mới ưu tiên lượt sở hữu.
do $$
begin
    if to_regprocedure('public.open_lucky_box_paid_core(uuid,text,text)') is null then
        alter function public.open_lucky_box(uuid,text,text) rename to open_lucky_box_paid_core;
    end if;
end $$;

create or replace function public.open_lucky_box(
    p_user_id uuid,
    p_box_code text,
    p_request_id text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_key text := btrim(coalesce(p_request_id,''));
    v_existing public.lucky_box_openings%rowtype;
    v_user public.users%rowtype;
    v_box public.lucky_boxes%rowtype;
    v_rate public.lucky_box_rate_versions%rowtype;
    v_price integer;
    v_ticket_before integer;
    v_zcoin_before integer;
    v_result jsonb;
    v_opening_id uuid;
begin
    if p_user_id is null then raise exception 'LUCKY_BOX_INVALID_USER'; end if;
    if v_key='' then raise exception 'LUCKY_BOX_INVALID_REQUEST_ID'; end if;

    select * into v_existing from public.lucky_box_openings where request_id=v_key limit 1;
    if found then
        v_result := public.open_lucky_box_paid_core(p_user_id,p_box_code,p_request_id);
        select coalesce(lucky_box_balance,0) into v_ticket_before from public.users where id=p_user_id;
        return v_result || jsonb_build_object(
            'payment_method',coalesce(v_existing.payment_method,'zcoin'),
            'lucky_box_balance_after',coalesce(v_existing.lucky_box_balance_after,v_ticket_before)
        );
    end if;

    perform pg_advisory_xact_lock(hashtext('luckybox-user:'||p_user_id::text));
    select * into v_user from public.users where id=p_user_id and role='player' for update;
    if not found then raise exception 'LUCKY_BOX_USER_NOT_FOUND'; end if;
    v_ticket_before := greatest(0,coalesce(v_user.lucky_box_balance,0));
    v_zcoin_before := greatest(0,coalesce(v_user.zcoin_balance,0));

    if v_ticket_before <= 0 then
        v_result := public.open_lucky_box_paid_core(p_user_id,p_box_code,p_request_id);
        v_opening_id := (v_result->>'opening_id')::uuid;
        update public.lucky_box_openings
        set payment_method='zcoin', lucky_box_balance_before=0, lucky_box_balance_after=0
        where id=v_opening_id;
        return v_result || jsonb_build_object('payment_method','zcoin','lucky_box_balance_after',0);
    end if;

    select * into v_box from public.lucky_boxes where code=btrim(p_box_code) limit 1;
    if not found then raise exception 'LUCKY_BOX_NOT_FOUND'; end if;
    select * into v_rate from public.lucky_box_rate_versions where box_id=v_box.id and status='active' limit 1;
    if not found then raise exception 'LUCKY_BOX_NO_ACTIVE_RATE'; end if;
    v_price := greatest(0,coalesce(v_rate.open_price_zcoin,0));
    if v_price<=0 then raise exception 'LUCKY_BOX_INVALID_PRICE'; end if;

    -- Cộng tạm đúng giá mở để lõi cũ xử lý phần thưởng; toàn bộ nằm trong cùng transaction.
    update public.users
    set lucky_box_balance=v_ticket_before-1,
        zcoin_balance=v_zcoin_before+v_price
    where id=p_user_id;

    v_result := public.open_lucky_box_paid_core(p_user_id,p_box_code,p_request_id);
    v_opening_id := (v_result->>'opening_id')::uuid;

    update public.lucky_box_openings
    set zcoin_cost=0,
        balance_before=v_zcoin_before,
        payment_method='owned_lucky_box',
        lucky_box_balance_before=v_ticket_before,
        lucky_box_balance_after=v_ticket_before-1,
        metadata=coalesce(metadata,'{}'::jsonb)||jsonb_build_object('payment_method','owned_lucky_box','app_version','V1.4.14')
    where id=v_opening_id;

    delete from public.zcoin_transactions
    where user_id=p_user_id
      and amount=-v_price
      and metadata->>'opening_id'=v_opening_id::text
      and metadata->>'request_id'=v_key;

    insert into public.lucky_box_balance_transactions(user_id,amount,balance_after,source,description,idempotency_key,metadata)
    values(p_user_id,-1,v_ticket_before-1,'lucky_box_open','Dùng 1 Lucky Box sở hữu để mở hộp',
           'open:'||v_key,jsonb_build_object('opening_id',v_opening_id,'box_code',p_box_code));

    return (v_result - 'zcoin_cost' - 'balance_before') || jsonb_build_object(
        'zcoin_cost',0,'balance_before',v_zcoin_before,'payment_method','owned_lucky_box',
        'lucky_box_balance_before',v_ticket_before,'lucky_box_balance_after',v_ticket_before-1
    );
end;
$$;

revoke all on function public.adjust_lucky_box_balance(uuid,integer,text,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.adjust_lucky_box_balance(uuid,integer,text,text,text,jsonb) to service_role;
revoke all on function public.open_lucky_box(uuid,text,text) from public,anon,authenticated;
grant execute on function public.open_lucky_box(uuid,text,text) to service_role;
revoke all on function public.open_lucky_box_paid_core(uuid,text,text) from public,anon,authenticated;
grant execute on function public.open_lucky_box_paid_core(uuid,text,text) to service_role;

commit;
