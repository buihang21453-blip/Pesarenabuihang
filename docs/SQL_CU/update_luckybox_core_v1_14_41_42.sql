-- =====================================================================
-- PES Arena V1.14.41.42 · Lucky Box Giai đoạn 2A
-- Database + backend core + Draft Preview + atomic opening RPC
--
-- AN TOÀN:
-- - Không xóa dữ liệu Production.
-- - Lucky Box được seed ở trạng thái TẮT.
-- - Rate Version đầu tiên là DRAFT, giá 0, duplicate_policy=pending.
-- - Không có Rate Version ACTIVE sau migration.
-- - Có thể chạy lại; seed không ghi đè cấu hình đã chỉnh.
-- =====================================================================

begin;

create extension if not exists pgcrypto;

do $$
begin
    if to_regclass('public.users') is null then raise exception 'MISSING_TABLE_PUBLIC_USERS'; end if;
    if to_regclass('public.shop_items') is null then raise exception 'MISSING_TABLE_PUBLIC_SHOP_ITEMS'; end if;
    if to_regclass('public.user_inventory') is null then raise exception 'MISSING_TABLE_PUBLIC_USER_INVENTORY'; end if;
    if to_regclass('public.zcoin_transactions') is null then raise exception 'MISSING_TABLE_PUBLIC_ZCOIN_TRANSACTIONS'; end if;
    if to_regclass('public.user_notifications') is null then raise exception 'MISSING_TABLE_PUBLIC_USER_NOTIFICATIONS'; end if;
    if not exists (
        select 1 from information_schema.columns
        where table_schema='public' and table_name='users' and column_name='zcoin_balance'
    ) then raise exception 'MISSING_COLUMN_USERS_ZCOIN_BALANCE'; end if;
end
$$;

create table if not exists public.lucky_boxes (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    description text not null default '',
    image_path text not null,
    is_enabled boolean not null default false,
    no_reward_enabled boolean not null default false,
    notification_title text not null default 'Kết quả Lucky Box PES Arena',
    notification_template text not null default 'Bạn đã nhận được {rewards} từ Lucky Box PES Arena.',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.lucky_box_rate_versions (
    id uuid primary key default gen_random_uuid(),
    box_id uuid not null references public.lucky_boxes(id) on delete cascade,
    version_number integer not null check (version_number > 0),
    status text not null default 'draft' check (status in ('draft','active','archived')),
    open_price_zcoin integer not null default 0 check (open_price_zcoin >= 0),
    item_count_weights jsonb not null default '{"0":7000,"1":2500,"2":450,"3":50}'::jsonb,
    duplicate_policy text not null default 'pending' check (duplicate_policy in ('pending','convert_zcoin','allow_quantity','block_owned')),
    notes text not null default '',
    created_by uuid references public.users(id) on delete set null,
    published_by uuid references public.users(id) on delete set null,
    published_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (box_id, version_number)
);

create unique index if not exists lucky_box_one_active_rate_per_box
    on public.lucky_box_rate_versions(box_id)
    where status='active';

create table if not exists public.lucky_box_exclusive_items (
    id uuid primary key default gen_random_uuid(),
    item_id uuid not null unique references public.shop_items(id) on delete restrict,
    item_code text not null unique,
    asset_path text not null,
    exclusive_label text not null default 'Độc quyền Lucky Box',
    is_enabled boolean not null default true,
    starts_at timestamptz,
    ends_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.lucky_box_rewards (
    id uuid primary key default gen_random_uuid(),
    rate_version_id uuid not null references public.lucky_box_rate_versions(id) on delete cascade,
    reward_code text not null,
    reward_name text not null,
    reward_type text not null check (reward_type in ('zcoin','shop_item','exclusive_item','discount_coupon','no_reward')),
    counts_as_item boolean not null default false,
    item_id uuid references public.shop_items(id) on delete restrict,
    reward_amount integer not null default 0 check (reward_amount >= 0),
    weight bigint not null default 0 check (weight >= 0),
    is_enabled boolean not null default true,
    rarity text,
    asset_path text,
    starts_at timestamptz,
    ends_at timestamptz,
    issue_limit bigint check (issue_limit is null or issue_limit >= 0),
    issued_count bigint not null default 0 check (issued_count >= 0),
    duplicate_zcoin integer check (duplicate_zcoin is null or duplicate_zcoin >= 0),
    sort_order integer not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (rate_version_id, reward_code),
    constraint lucky_box_reward_payload_check check (
        (reward_type='zcoin' and item_id is null and reward_amount>0 and counts_as_item=false)
        or (reward_type in ('shop_item','exclusive_item','discount_coupon') and item_id is not null and counts_as_item=true)
        or (reward_type='no_reward' and item_id is null and reward_amount=0 and counts_as_item=false)
    )
);

create index if not exists lucky_box_rewards_selection_idx
    on public.lucky_box_rewards(rate_version_id, counts_as_item, is_enabled, sort_order);

create table if not exists public.lucky_box_openings (
    id uuid primary key default gen_random_uuid(),
    request_id text not null unique,
    user_id uuid not null references public.users(id) on delete restrict,
    box_id uuid not null references public.lucky_boxes(id) on delete restrict,
    box_code text not null,
    rate_version_id uuid not null references public.lucky_box_rate_versions(id) on delete restrict,
    rate_version integer not null,
    zcoin_cost integer not null check (zcoin_cost >= 0),
    balance_before integer not null check (balance_before >= 0),
    balance_after integer not null check (balance_after >= 0),
    status text not null default 'completed' check (status in ('completed','reversed')),
    opened_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists lucky_box_openings_user_time_idx
    on public.lucky_box_openings(user_id, opened_at desc);

create table if not exists public.lucky_box_opening_rewards (
    id uuid primary key default gen_random_uuid(),
    opening_id uuid not null references public.lucky_box_openings(id) on delete cascade,
    reward_slot smallint not null check (reward_slot between 1 and 3),
    reward_type text not null,
    reward_code text not null,
    reward_name text not null,
    reward_amount integer not null default 0 check (reward_amount >= 0),
    reward_rarity text,
    item_id uuid references public.shop_items(id) on delete set null,
    inventory_id uuid references public.user_inventory(id) on delete set null,
    original_reward_code text,
    duplicate_conversion integer check (duplicate_conversion is null or duplicate_conversion >= 0),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (opening_id, reward_slot)
);

create table if not exists public.lucky_box_admin_audit_logs (
    id uuid primary key default gen_random_uuid(),
    actor_user_id uuid references public.users(id) on delete set null,
    action text not null,
    entity_type text not null,
    entity_id uuid,
    reason text not null default '',
    before_data jsonb,
    after_data jsonb,
    created_at timestamptz not null default now()
);

create index if not exists lucky_box_admin_audit_time_idx
    on public.lucky_box_admin_audit_logs(created_at desc);

-- ---------------------------------------------------------------------
-- Helper: quyền Admin
-- ---------------------------------------------------------------------
create or replace function public.lucky_box_is_admin(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$
    select exists(
        select 1 from public.users
        where id=p_user_id
          and (coalesce(role,'')='admin' or coalesce(admin_level,'none') in ('owner','admin'))
    );
$$;

-- ---------------------------------------------------------------------
-- Helper: chọn số vật phẩm 0/1/2/3 theo weight của Rate Version
-- ---------------------------------------------------------------------
create or replace function public.lucky_box_pick_item_count(p_weights jsonb)
returns integer
language plpgsql
volatile
set search_path=public
as $$
declare
    w0 bigint := greatest(0,coalesce((p_weights->>'0')::bigint,0));
    w1 bigint := greatest(0,coalesce((p_weights->>'1')::bigint,0));
    w2 bigint := greatest(0,coalesce((p_weights->>'2')::bigint,0));
    w3 bigint := greatest(0,coalesce((p_weights->>'3')::bigint,0));
    total bigint;
    ticket numeric;
begin
    total := w0+w1+w2+w3;
    if total<=0 then raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID'; end if;
    ticket := floor(random()*total)+1;
    if ticket<=w0 then return 0; end if;
    if ticket<=w0+w1 then return 1; end if;
    if ticket<=w0+w1+w2 then return 2; end if;
    return 3;
exception when invalid_text_representation or numeric_value_out_of_range then
    raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID';
end;
$$;

-- ---------------------------------------------------------------------
-- Helper: chọn reward theo trọng số. Item được chọn không lặp trong 1 hộp.
-- ---------------------------------------------------------------------
create or replace function public.lucky_box_pick_reward_id(
    p_rate_version_id uuid,
    p_counts_as_item boolean,
    p_exclude_ids uuid[] default array[]::uuid[]
)
returns uuid
language plpgsql
volatile
set search_path=public
as $$
declare
    total_weight numeric;
    ticket numeric;
    selected_id uuid;
begin
    select coalesce(sum(weight),0) into total_weight
    from public.lucky_box_rewards
    where rate_version_id=p_rate_version_id
      and counts_as_item=p_counts_as_item
      and is_enabled=true
      and weight>0
      and (starts_at is null or starts_at<=now())
      and (ends_at is null or ends_at>now())
      and (issue_limit is null or issued_count<issue_limit)
      and not (id=any(coalesce(p_exclude_ids,array[]::uuid[])));

    if total_weight<=0 then return null; end if;
    ticket := floor(random()*total_weight)+1;

    select id into selected_id
    from (
        select id,
               sum(weight) over(order by sort_order,id rows unbounded preceding) as cumulative_weight
        from public.lucky_box_rewards
        where rate_version_id=p_rate_version_id
          and counts_as_item=p_counts_as_item
          and is_enabled=true
          and weight>0
          and (starts_at is null or starts_at<=now())
          and (ends_at is null or ends_at>now())
          and (issue_limit is null or issued_count<issue_limit)
          and not (id=any(coalesce(p_exclude_ids,array[]::uuid[])))
    ) weighted
    where cumulative_weight>=ticket
    order by cumulative_weight
    limit 1;

    return selected_id;
end;
$$;

-- ---------------------------------------------------------------------
-- Admin Draft Preview: không trừ Zcoin, không cấp item, không tăng issued_count.
-- ---------------------------------------------------------------------
create or replace function public.preview_lucky_box_rate_version(
    p_actor_user_id uuid,
    p_rate_version_id uuid,
    p_iterations integer default 1000
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_rate public.lucky_box_rate_versions%rowtype;
    v_iteration integer;
    v_slot integer;
    v_item_count integer;
    v_item_positions integer[];
    v_selected_ids uuid[];
    v_reward_id uuid;
    v_reward public.lucky_box_rewards%rowtype;
    v_reward_counts jsonb := '{}'::jsonb;
    v_item_distribution jsonb := '{"0":0,"1":0,"2":0,"3":0}'::jsonb;
    v_samples jsonb := '[]'::jsonb;
    v_sample_rewards jsonb;
    v_total_zcoin bigint := 0;
    v_current integer;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then
        raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED';
    end if;
    if p_iterations is null or p_iterations<1 or p_iterations>10000 then
        raise exception 'LUCKY_BOX_PREVIEW_ITERATIONS_INVALID';
    end if;

    select * into v_rate from public.lucky_box_rate_versions where id=p_rate_version_id;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;

    for v_iteration in 1..p_iterations loop
        v_item_count := public.lucky_box_pick_item_count(v_rate.item_count_weights);
        v_current := coalesce((v_item_distribution->>v_item_count::text)::integer,0)+1;
        v_item_distribution := jsonb_set(v_item_distribution,array[v_item_count::text],to_jsonb(v_current),true);
        v_item_positions := coalesce((select array_agg(pos) from (
            select pos from generate_series(1,3) pos order by random() limit v_item_count
        ) p),array[]::integer[]);
        v_selected_ids := array[]::uuid[];
        v_sample_rewards := '[]'::jsonb;

        for v_slot in 1..3 loop
            v_reward_id := public.lucky_box_pick_reward_id(
                v_rate.id,
                v_slot=any(v_item_positions),
                case when v_slot=any(v_item_positions) then v_selected_ids else array[]::uuid[] end
            );
            if v_reward_id is null then raise exception 'LUCKY_BOX_REWARD_POOL_INVALID'; end if;
            select * into v_reward from public.lucky_box_rewards where id=v_reward_id;
            if v_reward.counts_as_item then v_selected_ids:=array_append(v_selected_ids,v_reward.id); end if;

            v_current := coalesce((v_reward_counts->>v_reward.reward_code)::integer,0)+1;
            v_reward_counts := jsonb_set(v_reward_counts,array[v_reward.reward_code],to_jsonb(v_current),true);
            if v_reward.reward_type='zcoin' then v_total_zcoin:=v_total_zcoin+v_reward.reward_amount; end if;

            if v_iteration<=20 then
                v_sample_rewards := v_sample_rewards || jsonb_build_array(jsonb_build_object(
                    'slot',v_slot,'reward_code',v_reward.reward_code,'reward_name',v_reward.reward_name,
                    'reward_type',v_reward.reward_type,'reward_amount',v_reward.reward_amount,
                    'rarity',v_reward.rarity,'counts_as_item',v_reward.counts_as_item
                ));
            end if;
        end loop;

        if v_iteration<=20 then
            v_samples := v_samples || jsonb_build_array(jsonb_build_object(
                'sample',v_iteration,'item_count',v_item_count,'rewards',v_sample_rewards
            ));
        end if;
    end loop;

    return jsonb_build_object(
        'rate_version_id',v_rate.id,
        'rate_version',v_rate.version_number,
        'rate_status',v_rate.status,
        'iterations',p_iterations,
        'item_count_distribution',v_item_distribution,
        'reward_counts',v_reward_counts,
        'average_zcoin_reward',round(v_total_zcoin::numeric/p_iterations,2),
        'sample_openings',v_samples,
        'mutated_data',false
    );
end;
$$;

-- ---------------------------------------------------------------------
-- Promote Draft -> Active. Backend core cho Giai đoạn 2B gọi sau khi duyệt.
-- Không tự bật Lucky Box.
-- ---------------------------------------------------------------------
create or replace function public.publish_lucky_box_rate_version(
    p_actor_user_id uuid,
    p_rate_version_id uuid,
    p_reason text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_rate public.lucky_box_rate_versions%rowtype;
    v_before jsonb;
    v_item_rewards integer;
    v_non_item_rewards integer;
    v_max_items integer := 0;
    v_weight_total numeric;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_PUBLISH_REASON_REQUIRED'; end if;

    select * into v_rate from public.lucky_box_rate_versions where id=p_rate_version_id for update;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;
    if v_rate.status<>'draft' then raise exception 'LUCKY_BOX_RATE_NOT_DRAFT'; end if;
    if v_rate.open_price_zcoin<=0 then raise exception 'LUCKY_BOX_INVALID_PRICE'; end if;
    if v_rate.duplicate_policy='pending' then raise exception 'LUCKY_BOX_DUPLICATE_POLICY_PENDING'; end if;

    select coalesce(sum(greatest(0,value::numeric)),0) into v_weight_total
    from jsonb_each_text(v_rate.item_count_weights);
    if v_weight_total<=0 then raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID'; end if;
    if exists(select 1 from jsonb_each_text(v_rate.item_count_weights) where value::numeric<0) then
        raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID';
    end if;

    if coalesce((v_rate.item_count_weights->>'3')::numeric,0)>0 then v_max_items:=3;
    elsif coalesce((v_rate.item_count_weights->>'2')::numeric,0)>0 then v_max_items:=2;
    elsif coalesce((v_rate.item_count_weights->>'1')::numeric,0)>0 then v_max_items:=1;
    end if;

    select count(*) into v_item_rewards from public.lucky_box_rewards
    where rate_version_id=v_rate.id and counts_as_item=true and is_enabled=true and weight>0;
    select count(*) into v_non_item_rewards from public.lucky_box_rewards
    where rate_version_id=v_rate.id and counts_as_item=false and is_enabled=true and weight>0;

    if v_item_rewards<v_max_items then raise exception 'LUCKY_BOX_NOT_ENOUGH_ITEM_REWARDS'; end if;
    if (
        coalesce((v_rate.item_count_weights->>'0')::numeric,0)>0
        or coalesce((v_rate.item_count_weights->>'1')::numeric,0)>0
        or coalesce((v_rate.item_count_weights->>'2')::numeric,0)>0
    ) and v_non_item_rewards<1 then raise exception 'LUCKY_BOX_NOT_ENOUGH_NON_ITEM_REWARDS'; end if;

    if exists(
        select 1 from public.lucky_box_rewards r
        left join public.shop_items s on s.id=r.item_id
        where r.rate_version_id=v_rate.id and r.is_enabled=true and r.weight>0
          and (r.weight<0 or (r.item_id is not null and (s.id is null or s.is_active=false)))
    ) then raise exception 'LUCKY_BOX_REWARD_POOL_INVALID'; end if;

    if v_rate.duplicate_policy='convert_zcoin' and exists(
        select 1 from public.lucky_box_rewards r
        join public.shop_items s on s.id=r.item_id
        where r.rate_version_id=v_rate.id and r.is_enabled=true and r.weight>0
          and s.is_unique=true and coalesce(r.duplicate_zcoin,0)<=0
    ) then raise exception 'LUCKY_BOX_DUPLICATE_CONVERSION_MISSING'; end if;

    v_before:=to_jsonb(v_rate);
    update public.lucky_box_rate_versions
    set status='archived',updated_at=now()
    where box_id=v_rate.box_id and status='active';

    update public.lucky_box_rate_versions
    set status='active',published_by=p_actor_user_id,published_at=now(),updated_at=now()
    where id=v_rate.id;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'publish_rate_version','lucky_box_rate_version',v_rate.id,btrim(p_reason),
        v_before,(select to_jsonb(rv) from public.lucky_box_rate_versions rv where rv.id=v_rate.id)
    );

    return jsonb_build_object('rate_version_id',v_rate.id,'version_number',v_rate.version_number,'status','active');
exception when invalid_text_representation or numeric_value_out_of_range then
    raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID';
end;
$$;

-- ---------------------------------------------------------------------
-- Mở hộp thật: 1 transaction, 3 reward entries, idempotency, row lock.
-- ---------------------------------------------------------------------
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
    v_box public.lucky_boxes%rowtype;
    v_rate public.lucky_box_rate_versions%rowtype;
    v_user public.users%rowtype;
    v_existing public.lucky_box_openings%rowtype;
    v_opening_id uuid;
    v_before bigint;
    v_after_cost bigint;
    v_after bigint;
    v_total_zcoin bigint := 0;
    v_item_count integer;
    v_item_positions integer[];
    v_selected_ids uuid[] := array[]::uuid[];
    v_attempt_exclude_ids uuid[] := array[]::uuid[];
    v_reward_id uuid;
    v_reward public.lucky_box_rewards%rowtype;
    v_item public.shop_items%rowtype;
    v_inventory public.user_inventory%rowtype;
    v_inventory_id uuid;
    v_slot integer;
    v_try integer;
    v_actual_type text;
    v_actual_code text;
    v_actual_name text;
    v_actual_amount integer;
    v_original_code text;
    v_duplicate_conversion integer;
    v_item_grants integer := 0;
    v_summary text;
    v_result_rewards jsonb;
    v_transaction_type text;
    v_source text;
    v_transaction_constraints text := '';
    v_source_constraints text := '';
    v_notification_constraints text := '';
    v_notification_type text := 'lucky_box_reward';
    v_key text := btrim(coalesce(p_request_id,''));
begin
    if p_user_id is null then raise exception 'LUCKY_BOX_INVALID_USER'; end if;
    if coalesce(btrim(p_box_code),'')='' then raise exception 'LUCKY_BOX_NOT_FOUND'; end if;
    if v_key='' or char_length(v_key)>120 then raise exception 'LUCKY_BOX_INVALID_REQUEST_ID'; end if;

    perform pg_advisory_xact_lock(hashtext('luckybox-request:'||v_key));
    select * into v_existing from public.lucky_box_openings where request_id=v_key limit 1;
    if found then
        if v_existing.user_id<>p_user_id or v_existing.box_code<>btrim(p_box_code) then
            raise exception 'LUCKY_BOX_REQUEST_CONFLICT';
        end if;
        select coalesce(jsonb_agg(jsonb_build_object(
            'slot',r.reward_slot,'reward_type',r.reward_type,'reward_code',r.reward_code,
            'reward_name',r.reward_name,'reward_amount',r.reward_amount,'rarity',r.reward_rarity,
            'original_reward_code',r.original_reward_code,'duplicate_conversion',r.duplicate_conversion
        ) order by r.reward_slot),'[]'::jsonb) into v_result_rewards
        from public.lucky_box_opening_rewards r where r.opening_id=v_existing.id;
        return jsonb_build_object(
            'opening_id',v_existing.id,'request_id',v_existing.request_id,
            'rate_version',v_existing.rate_version,'zcoin_cost',v_existing.zcoin_cost,
            'balance_before',v_existing.balance_before,'balance_after',v_existing.balance_after,
            'rewards',v_result_rewards,'duplicate',true
        );
    end if;

    perform pg_advisory_xact_lock(hashtext('luckybox-user:'||p_user_id::text));

    select * into v_box from public.lucky_boxes where code=btrim(p_box_code) for update;
    if not found then raise exception 'LUCKY_BOX_NOT_FOUND'; end if;
    if not v_box.is_enabled then raise exception 'LUCKY_BOX_DISABLED'; end if;

    select * into v_rate from public.lucky_box_rate_versions
    where box_id=v_box.id and status='active' limit 1 for update;
    if not found then raise exception 'LUCKY_BOX_NO_ACTIVE_RATE'; end if;
    if v_rate.open_price_zcoin<=0 then raise exception 'LUCKY_BOX_INVALID_PRICE'; end if;
    if v_rate.duplicate_policy='pending' then raise exception 'LUCKY_BOX_DUPLICATE_POLICY_PENDING'; end if;

    select * into v_user from public.users where id=p_user_id and role='player' for update;
    if not found then raise exception 'LUCKY_BOX_USER_NOT_FOUND'; end if;

    v_before:=greatest(0,coalesce(v_user.zcoin_balance,0));
    if v_before<v_rate.open_price_zcoin then raise exception 'INSUFFICIENT_ZCOIN'; end if;
    v_after_cost:=v_before-v_rate.open_price_zcoin;

    v_item_count:=public.lucky_box_pick_item_count(v_rate.item_count_weights);
    v_item_positions:=coalesce((select array_agg(pos) from (
        select pos from generate_series(1,3) pos order by random() limit v_item_count
    ) p),array[]::integer[]);

    insert into public.lucky_box_openings(
        request_id,user_id,box_id,box_code,rate_version_id,rate_version,zcoin_cost,
        balance_before,balance_after,status,metadata
    ) values(
        v_key,p_user_id,v_box.id,v_box.code,v_rate.id,v_rate.version_number,v_rate.open_price_zcoin,
        v_before::integer,v_after_cost::integer,'completed',jsonb_build_object(
            'item_count',v_item_count,'app_version','V1.14.41.42'
        )
    ) returning id into v_opening_id;

    for v_slot in 1..3 loop
        v_reward_id:=null;
        v_attempt_exclude_ids:=array[]::uuid[];
        for v_try in 1..20 loop
            v_reward_id:=public.lucky_box_pick_reward_id(
                v_rate.id,
                v_slot=any(v_item_positions),
                case when v_slot=any(v_item_positions)
                     then v_selected_ids||v_attempt_exclude_ids
                     else v_attempt_exclude_ids end
            );
            if v_reward_id is null then exit; end if;
            select * into v_reward from public.lucky_box_rewards where id=v_reward_id for update;
            if v_reward.is_enabled and v_reward.weight>0
               and (v_reward.starts_at is null or v_reward.starts_at<=now())
               and (v_reward.ends_at is null or v_reward.ends_at>now())
               and (v_reward.issue_limit is null or v_reward.issued_count<v_reward.issue_limit) then
                exit;
            end if;
            v_attempt_exclude_ids:=array_append(v_attempt_exclude_ids,v_reward.id);
            v_reward_id:=null;
        end loop;
        if v_reward_id is null then raise exception 'LUCKY_BOX_REWARD_POOL_INVALID'; end if;
        if v_reward.counts_as_item then v_selected_ids:=array_append(v_selected_ids,v_reward.id); end if;

        v_actual_type:=v_reward.reward_type;
        v_actual_code:=v_reward.reward_code;
        v_actual_name:=v_reward.reward_name;
        v_actual_amount:=v_reward.reward_amount;
        v_original_code:=null;
        v_duplicate_conversion:=null;
        v_inventory_id:=null;

        if v_reward.reward_type='zcoin' then
            v_total_zcoin:=v_total_zcoin+v_reward.reward_amount;
        elsif v_reward.reward_type='no_reward' then
            if not v_box.no_reward_enabled then raise exception 'LUCKY_BOX_NO_REWARD_NOT_APPROVED'; end if;
        else
            select * into v_item from public.shop_items where id=v_reward.item_id and is_active=true;
            if not found then raise exception 'LUCKY_BOX_ITEM_NOT_FOUND'; end if;

            select * into v_inventory from public.user_inventory
            where user_id=p_user_id and item_id=v_item.id and quantity>0
            limit 1 for update;

            if found and v_item.is_unique then
                if v_rate.duplicate_policy='convert_zcoin' then
                    if coalesce(v_reward.duplicate_zcoin,0)<=0 then raise exception 'LUCKY_BOX_DUPLICATE_CONVERSION_MISSING'; end if;
                    v_original_code:=v_reward.reward_code;
                    v_duplicate_conversion:=v_reward.duplicate_zcoin;
                    v_actual_type:='zcoin';
                    v_actual_code:='duplicate_'||v_reward.reward_code;
                    v_actual_name:='Bồi hoàn vật phẩm trùng: '||v_reward.reward_name;
                    v_actual_amount:=v_reward.duplicate_zcoin;
                    v_total_zcoin:=v_total_zcoin+v_reward.duplicate_zcoin;
                else
                    raise exception 'LUCKY_BOX_DUPLICATE_ITEM';
                end if;
            else
                insert into public.user_inventory(user_id,item_id,quantity,acquired_from,metadata)
                values(p_user_id,v_item.id,1,'lucky_box',jsonb_build_object(
                    'opening_id',v_opening_id,'reward_code',v_reward.reward_code,
                    'rate_version',v_rate.version_number,'app_version','V1.14.41.42'
                ))
                on conflict(user_id,item_id) do update set
                    quantity=case when v_item.is_unique then greatest(public.user_inventory.quantity,1)
                                  else public.user_inventory.quantity+1 end,
                    updated_at=now(),acquired_from='lucky_box',
                    metadata=coalesce(public.user_inventory.metadata,'{}'::jsonb)||excluded.metadata
                returning id into v_inventory_id;
                v_item_grants:=v_item_grants+1;
            end if;
        end if;

        update public.lucky_box_rewards
        set issued_count=issued_count+1,updated_at=now()
        where id=v_reward.id;

        insert into public.lucky_box_opening_rewards(
            opening_id,reward_slot,reward_type,reward_code,reward_name,reward_amount,
            reward_rarity,item_id,inventory_id,original_reward_code,duplicate_conversion,metadata
        ) values(
            v_opening_id,v_slot,v_actual_type,v_actual_code,v_actual_name,v_actual_amount,
            v_reward.rarity,v_reward.item_id,v_inventory_id,v_original_code,v_duplicate_conversion,
            jsonb_build_object('source_reward_id',v_reward.id,'source_reward_type',v_reward.reward_type)
        );
    end loop;

    v_after:=v_after_cost+v_total_zcoin;
    if v_after>2147483647 then raise exception 'ZCOIN_BALANCE_OUT_OF_RANGE'; end if;
    update public.users set zcoin_balance=v_after::integer where id=p_user_id;
    update public.lucky_box_openings set balance_after=v_after::integer where id=v_opening_id;

    select coalesce(string_agg(pg_get_constraintdef(c.oid),' '),'') into v_transaction_constraints
    from pg_constraint c where c.conrelid='public.zcoin_transactions'::regclass
      and c.contype='c' and pg_get_constraintdef(c.oid) ilike '%transaction_type%';
    select coalesce(string_agg(pg_get_constraintdef(c.oid),' '),'') into v_source_constraints
    from pg_constraint c where c.conrelid='public.zcoin_transactions'::regclass
      and c.contype='c' and pg_get_constraintdef(c.oid) ilike '%source%';

    if v_transaction_constraints ilike '%spend%' then v_transaction_type:='spend';
    elsif v_transaction_constraints ilike '%debit%' then v_transaction_type:='debit';
    else v_transaction_type:='spend'; end if;
    if v_source_constraints ilike '%lucky_box%' then v_source:='lucky_box';
    elsif v_source_constraints ilike '%system%' then v_source:='system';
    elsif v_source_constraints ilike '%shop%' then v_source:='shop';
    else v_source:='system'; end if;

    insert into public.zcoin_transactions(user_id,amount,balance_after,transaction_type,source,description,metadata)
    values(
        p_user_id,-v_rate.open_price_zcoin,v_after_cost::integer,v_transaction_type,v_source,
        'Mở Lucky Box PES Arena',jsonb_build_object(
            'balance_before',v_before,'opening_id',v_opening_id,'request_id',v_key,
            'rate_version',v_rate.version_number,'idempotency_key','luckybox-spend:'||v_key,
            'app_version','V1.14.41.42'
        )
    );

    if v_total_zcoin>0 then
        if v_transaction_constraints ilike '%earn%' then v_transaction_type:='earn';
        elsif v_transaction_constraints ilike '%credit%' then v_transaction_type:='credit';
        else v_transaction_type:='earn'; end if;
        insert into public.zcoin_transactions(user_id,amount,balance_after,transaction_type,source,description,metadata)
        values(
            p_user_id,v_total_zcoin::integer,v_after::integer,v_transaction_type,v_source,
            'Phần thưởng Lucky Box PES Arena',jsonb_build_object(
                'balance_before',v_after_cost,'opening_id',v_opening_id,'request_id',v_key,
                'rate_version',v_rate.version_number,'idempotency_key','luckybox-reward:'||v_key,
                'app_version','V1.14.41.42'
            )
        );
    end if;

    if v_item_grants>0 then
        select coalesce(string_agg(pg_get_constraintdef(c.oid),' '),'') into v_notification_constraints
        from pg_constraint c where c.conrelid='public.user_notifications'::regclass
          and c.contype='c' and pg_get_constraintdef(c.oid) ilike '%notification_type%';
        if v_notification_constraints<>'' and v_notification_constraints not ilike '%lucky_box_reward%' then
            if v_notification_constraints ilike '%system%' then v_notification_type:='system';
            elsif v_notification_constraints ilike '%reward%' then v_notification_type:='reward';
            else raise exception 'LUCKY_BOX_NOTIFICATION_TYPE_UNSUPPORTED'; end if;
        end if;

        select string_agg(reward_name,', ' order by reward_slot) into v_summary
        from public.lucky_box_opening_rewards where opening_id=v_opening_id;
        insert into public.user_notifications(
            user_id,notification_type,title,message,link_url,is_read,created_at
        ) values(
            p_user_id,v_notification_type,v_box.notification_title,
            replace(v_box.notification_template,'{rewards}',coalesce(v_summary,'phần thưởng')),
            '/lucky-box/openings/'||v_opening_id::text,false,now()
        );
    end if;

    select coalesce(jsonb_agg(jsonb_build_object(
        'slot',r.reward_slot,'reward_type',r.reward_type,'reward_code',r.reward_code,
        'reward_name',r.reward_name,'reward_amount',r.reward_amount,'rarity',r.reward_rarity,
        'original_reward_code',r.original_reward_code,'duplicate_conversion',r.duplicate_conversion
    ) order by r.reward_slot),'[]'::jsonb) into v_result_rewards
    from public.lucky_box_opening_rewards r where r.opening_id=v_opening_id;

    return jsonb_build_object(
        'opening_id',v_opening_id,'request_id',v_key,'rate_version',v_rate.version_number,
        'zcoin_cost',v_rate.open_price_zcoin,'balance_before',v_before,'balance_after',v_after,
        'item_count',v_item_count,'rewards',v_result_rewards,'duplicate',false
    );
end;
$$;

-- ---------------------------------------------------------------------
-- Seed box và Rate Version Draft. Không publish, không bật box.
-- ---------------------------------------------------------------------
insert into public.lucky_boxes(
    code,name,description,image_path,is_enabled,no_reward_enabled,metadata
) values(
    'lucky_box_pes_arena','Lucky Box PES Arena',
    'Mỗi lượt tạo đúng 3 kết quả. Cấu hình Production chỉ có hiệu lực sau khi Admin publish.',
    'luckybox/luckybox-pes-arena.webp',false,false,
    '{"phase":"2A","asset_base_env":"LUCKYBOX_ASSET_BASE_URL"}'::jsonb
) on conflict(code) do nothing;

-- 14 vật phẩm độc quyền được dùng lại Shop/Inventory nhưng không bày bán.
insert into public.shop_items(
    code,name,description,category,item_type,rarity,price_zcoin,image_path,preview_path,
    is_consumable,is_unique,is_active,is_listed,is_featured,sort_order,metadata
) values
('lb_banner_bernardo_silva','Banner Bernardo Silva','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-bernardo-silva.webp',null,false,true,true,false,false,9001,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_bruno_fernandes','Banner Bruno Fernandes','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-bruno-fernandes.webp',null,false,true,true,false,false,9002,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_cristiano_ronaldo','Banner Cristiano Ronaldo','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-cristiano-ronaldo.webp',null,false,true,true,false,false,9003,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_erling_haaland','Banner Erling Haaland','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-erling-haaland.webp',null,false,true,true,false,false,9004,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_harry_kane','Banner Harry Kane','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-harry-kane.webp',null,false,true,true,false,false,9005,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_khvicha_kvaratskhelia','Banner Khvicha Kvaratskhelia','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-khvicha-kvaratskhelia.webp',null,false,true,true,false,false,9006,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_kylian_mbappe','Banner Kylian Mbappé','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-kylian-mbappe.webp',null,false,true,true,false,false,9007,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_lamine_yamal','Banner Lamine Yamal','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-lamine-yamal.webp',null,false,true,true,false,false,9008,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_lionel_messi','Banner Lionel Messi','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-lionel-messi.webp',null,false,true,true,false,false,9009,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_michael_olise','Banner Michael Olise','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-michael-olise.webp',null,false,true,true,false,false,9010,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_ousmane_dembele','Banner Ousmane Dembélé','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-ousmane-dembele.webp',null,false,true,true,false,false,9011,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_raphinha','Banner Raphinha','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-raphinha.webp',null,false,true,true,false,false,9012,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_banner_vinicius_junior','Banner Vinícius Júnior','Độc quyền Lucky Box.','profile_banner','profile_banner','elite',0,'luckybox/exclusive/profile-banner-vinicius-junior.webp',null,false,true,true,false,false,9013,'{"luckybox_exclusive":true,"rarity_pending_review":true}'),
('lb_frame_ke_thong_tri_hoang_gia','Khung Kẻ Thống Trị Hoàng Gia','Độc quyền Lucky Box.','avatar_frame','avatar_frame','legendary',0,'luckybox/exclusive/avatar-frame-royal-dominator.webp',null,false,true,true,false,false,9014,'{"luckybox_exclusive":true,"rarity_pending_review":true}')
on conflict(code) do nothing;

insert into public.lucky_box_exclusive_items(item_id,item_code,asset_path,metadata)
select id,code,image_path,jsonb_build_object('seed_version','V1.14.41.42')
from public.shop_items
where code like 'lb_banner_%' or code='lb_frame_ke_thong_tri_hoang_gia'
on conflict(item_code) do nothing;

do $$
declare
    v_box_id uuid;
    v_rate_id uuid;
begin
    select id into v_box_id from public.lucky_boxes where code='lucky_box_pes_arena';
    insert into public.lucky_box_rate_versions(
        box_id,version_number,status,open_price_zcoin,item_count_weights,duplicate_policy,notes,metadata
    ) values(
        v_box_id,1,'draft',0,'{"0":7000,"1":2500,"2":450,"3":50}'::jsonb,'pending',
        'DRAFT khởi tạo để Admin quay thử; chưa phải tỷ lệ Production.',
        '{"production_approved":false,"seed_version":"V1.14.41.42"}'::jsonb
    ) on conflict(box_id,version_number) do nothing;

    select id into v_rate_id from public.lucky_box_rate_versions
    where box_id=v_box_id and version_number=1;

    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,reward_amount,
        weight,is_enabled,rarity,asset_path,sort_order,metadata
    ) values
    (v_rate_id,'zcoin_50','50 Zcoin','zcoin',false,50,3000,true,'common',null,10,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_75','75 Zcoin','zcoin',false,75,2300,true,'common',null,20,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_100','100 Zcoin','zcoin',false,100,1800,true,'common',null,30,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_150','150 Zcoin','zcoin',false,150,1200,true,'rare',null,40,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_200','200 Zcoin','zcoin',false,200,800,true,'rare',null,50,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_300','300 Zcoin','zcoin',false,300,450,true,'epic',null,60,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_500','500 Zcoin','zcoin',false,500,200,true,'elite',null,70,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_750','750 Zcoin','zcoin',false,750,50,true,'legendary',null,80,'{"draft_weight":true}'),
    (v_rate_id,'zcoin_1000','1000 Zcoin','zcoin',false,1000,10,true,'legendary',null,90,'{"draft_weight":true}'),
    (v_rate_id,'no_reward','Chúc bạn may mắn lần sau','no_reward',false,0,0,false,'common','luckybox/no-reward.webp',99,
     '{"requires_owner_approval":true,"draft_weight":true}')
    on conflict(rate_version_id,reward_code) do nothing;

    -- Mỗi vật phẩm Shop đang bán có một reward row và weight riêng.
    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,item_id,
        weight,is_enabled,rarity,asset_path,sort_order,metadata
    )
    select v_rate_id,'shop_'||s.code,s.name,
           case when s.item_type='discount_coupon' then 'discount_coupon' else 'shop_item' end,
           true,s.id,
           case s.rarity when 'common' then 100 when 'rare' then 50 when 'epic' then 20
                         when 'elite' then 8 when 'legendary' then 2 else 10 end,
           true,s.rarity,
           case s.code when 'discount_coupon_05' then 'luckybox/rewards/discount-coupon-05.webp'
                       when 'discount_coupon_10' then 'luckybox/rewards/discount-coupon-10.webp'
                       else s.image_path end,
           1000+coalesce(s.sort_order,0),
           jsonb_build_object('draft_weight',true,'shop_item_code',s.code)
    from public.shop_items s
    where s.is_active=true and s.is_listed=true
      and s.code not like 'lb_%'
    on conflict(rate_version_id,reward_code) do nothing;

    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,item_id,
        weight,is_enabled,rarity,asset_path,sort_order,metadata
    )
    select v_rate_id,s.code,s.name,'exclusive_item',true,s.id,
           case when s.item_type='avatar_frame' then 2 else 5 end,
           true,s.rarity,s.image_path,2000+coalesce(s.sort_order,0),
           jsonb_build_object('draft_weight',true,'luckybox_exclusive',true)
    from public.shop_items s
    where s.code like 'lb_banner_%' or s.code='lb_frame_ke_thong_tri_hoang_gia'
    on conflict(rate_version_id,reward_code) do nothing;
end
$$;

revoke all on function public.lucky_box_is_admin(uuid) from public,anon,authenticated;
revoke all on function public.preview_lucky_box_rate_version(uuid,uuid,integer) from public,anon,authenticated;
revoke all on function public.publish_lucky_box_rate_version(uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.open_lucky_box(uuid,text,text) from public,anon,authenticated;
grant execute on function public.lucky_box_is_admin(uuid) to service_role;
grant execute on function public.preview_lucky_box_rate_version(uuid,uuid,integer) to service_role;
grant execute on function public.publish_lucky_box_rate_version(uuid,uuid,text) to service_role;
grant execute on function public.open_lucky_box(uuid,text,text) to service_role;

notify pgrst,'reload schema';
commit;

-- Kết quả mong đợi: Success. No rows returned.
-- Sau migration: /admin/lucky-box/preview dùng được, nhưng người chơi KHÔNG mở được
-- vì box=false, Rate Version=draft, giá=0, duplicate_policy=pending.
