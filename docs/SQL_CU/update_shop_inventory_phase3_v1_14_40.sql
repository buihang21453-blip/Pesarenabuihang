-- =====================================================================
-- PES Arena · Collap_V1.14.40_SHOP_INVENTORY_PHASE3
-- Cửa hàng + Kho đồ + Trang bị hồ sơ + Admin tặng vật phẩm
-- Baseline bắt buộc: Collap_V1.14.39.12
--
-- AN TOÀN DỮ LIỆU
-- - Không xóa bảng hoặc dữ liệu hiện có.
-- - Không thay đổi số dư ngoài các RPC nguyên tử bên dưới.
-- - Chạy lại an toàn; catalog dùng UPSERT theo code.
-- - Phiếu 20% và 30% luôn được seed ở chế độ không bày bán.
-- =====================================================================

begin;

create extension if not exists pgcrypto;

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
        where table_schema='public' and table_name='users' and column_name='zcoin_balance'
    ) then
        raise exception 'MISSING_COLUMN_USERS_ZCOIN_BALANCE';
    end if;
end
$$;

alter table public.users
    add column if not exists display_name_change_count integer default 0;
alter table public.users
    add column if not exists display_name_changed_at timestamptz;

create table if not exists public.shop_items (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    description text not null default '',
    category text not null,
    item_type text not null,
    rarity text not null default 'common',
    price_zcoin integer not null default 0 check (price_zcoin >= 0),
    image_path text not null,
    preview_path text,
    is_consumable boolean not null default false,
    is_unique boolean not null default true,
    is_active boolean not null default true,
    is_listed boolean not null default true,
    is_featured boolean not null default false,
    starts_at timestamptz,
    ends_at timestamptz,
    sort_order integer not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint shop_items_category_check check (category in (
        'avatar_frame','profile_banner','name_style','profile_badge','utility'
    )),
    constraint shop_items_type_check check (item_type in (
        'avatar_frame','profile_banner','name_style','profile_badge',
        'display_name_ticket','discount_coupon'
    )),
    constraint shop_items_rarity_check check (rarity in (
        'common','rare','epic','elite','legendary'
    ))
);

create table if not exists public.user_inventory (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    item_id uuid not null references public.shop_items(id) on delete cascade,
    quantity integer not null default 1 check (quantity > 0),
    acquired_from text not null default 'shop',
    acquired_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    unique (user_id, item_id)
);

create table if not exists public.user_equipment (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    slot text not null,
    inventory_id uuid not null references public.user_inventory(id) on delete cascade,
    item_id uuid not null references public.shop_items(id) on delete cascade,
    equipped_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb,
    unique (user_id, slot),
    constraint user_equipment_slot_check check (slot in (
        'avatar_frame','profile_banner','name_style','profile_badge','profile_card_theme'
    ))
);

create table if not exists public.shop_purchases (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    item_id uuid not null references public.shop_items(id) on delete restrict,
    quantity integer not null default 1 check (quantity > 0),
    unit_price integer not null default 0 check (unit_price >= 0),
    subtotal integer not null default 0 check (subtotal >= 0),
    discount_amount integer not null default 0 check (discount_amount >= 0),
    final_price integer not null default 0 check (final_price >= 0),
    coupon_item_id uuid references public.shop_items(id) on delete set null,
    coupon_percent integer not null default 0 check (coupon_percent >= 0 and coupon_percent <= 100),
    balance_before integer not null default 0 check (balance_before >= 0),
    balance_after integer not null default 0 check (balance_after >= 0),
    request_key text not null unique,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

-- Bổ sung tương thích nếu Production từng có bảng Shop thử nghiệm cũ.
alter table public.shop_items add column if not exists code text;
alter table public.shop_items add column if not exists name text;
alter table public.shop_items add column if not exists description text default '';
alter table public.shop_items add column if not exists category text;
alter table public.shop_items add column if not exists item_type text;
alter table public.shop_items add column if not exists rarity text default 'common';
alter table public.shop_items add column if not exists price_zcoin integer default 0;
alter table public.shop_items add column if not exists image_path text;
alter table public.shop_items add column if not exists preview_path text;
alter table public.shop_items add column if not exists is_consumable boolean default false;
alter table public.shop_items add column if not exists is_unique boolean default true;
alter table public.shop_items add column if not exists is_active boolean default true;
alter table public.shop_items add column if not exists is_listed boolean default true;
alter table public.shop_items add column if not exists is_featured boolean default false;
alter table public.shop_items add column if not exists starts_at timestamptz;
alter table public.shop_items add column if not exists ends_at timestamptz;
alter table public.shop_items add column if not exists sort_order integer default 0;
alter table public.shop_items add column if not exists metadata jsonb default '{}'::jsonb;
alter table public.shop_items add column if not exists created_at timestamptz default now();
alter table public.shop_items add column if not exists updated_at timestamptz default now();

alter table public.user_inventory add column if not exists user_id uuid references public.users(id) on delete cascade;
alter table public.user_inventory add column if not exists item_id uuid references public.shop_items(id) on delete cascade;
alter table public.user_inventory add column if not exists quantity integer default 1;
alter table public.user_inventory add column if not exists acquired_from text default 'shop';
alter table public.user_inventory add column if not exists acquired_at timestamptz default now();
alter table public.user_inventory add column if not exists updated_at timestamptz default now();
alter table public.user_inventory add column if not exists metadata jsonb default '{}'::jsonb;

alter table public.user_equipment add column if not exists user_id uuid references public.users(id) on delete cascade;
alter table public.user_equipment add column if not exists slot text;
alter table public.user_equipment add column if not exists inventory_id uuid references public.user_inventory(id) on delete cascade;
alter table public.user_equipment add column if not exists item_id uuid references public.shop_items(id) on delete cascade;
alter table public.user_equipment add column if not exists equipped_at timestamptz default now();
alter table public.user_equipment add column if not exists metadata jsonb default '{}'::jsonb;

alter table public.shop_purchases add column if not exists user_id uuid references public.users(id) on delete cascade;
alter table public.shop_purchases add column if not exists item_id uuid references public.shop_items(id) on delete restrict;
alter table public.shop_purchases add column if not exists quantity integer default 1;
alter table public.shop_purchases add column if not exists unit_price integer default 0;
alter table public.shop_purchases add column if not exists subtotal integer default 0;
alter table public.shop_purchases add column if not exists discount_amount integer default 0;
alter table public.shop_purchases add column if not exists final_price integer default 0;
alter table public.shop_purchases add column if not exists coupon_item_id uuid references public.shop_items(id) on delete set null;
alter table public.shop_purchases add column if not exists coupon_percent integer default 0;
alter table public.shop_purchases add column if not exists balance_before integer default 0;
alter table public.shop_purchases add column if not exists balance_after integer default 0;
alter table public.shop_purchases add column if not exists request_key text;
alter table public.shop_purchases add column if not exists metadata jsonb default '{}'::jsonb;
alter table public.shop_purchases add column if not exists created_at timestamptz default now();

create unique index if not exists uq_shop_items_code on public.shop_items(code);
create unique index if not exists uq_user_inventory_user_item on public.user_inventory(user_id,item_id);
create unique index if not exists uq_user_equipment_user_slot on public.user_equipment(user_id,slot);
create unique index if not exists uq_shop_purchases_request_key on public.shop_purchases(request_key);

create index if not exists idx_shop_items_listing
    on public.shop_items (is_active, is_listed, sort_order);
create index if not exists idx_shop_items_type
    on public.shop_items (item_type, rarity, sort_order);
create index if not exists idx_user_inventory_user
    on public.user_inventory (user_id, updated_at desc);
create index if not exists idx_user_equipment_user
    on public.user_equipment (user_id, slot);
create index if not exists idx_shop_purchases_user
    on public.shop_purchases (user_id, created_at desc);
create index if not exists idx_shop_purchases_created
    on public.shop_purchases (created_at desc);

-- =====================================================================
-- Catalog 25 vật phẩm
-- =====================================================================
insert into public.shop_items (
    code,name,description,category,item_type,rarity,price_zcoin,
    image_path,preview_path,is_consumable,is_unique,is_active,is_listed,
    is_featured,sort_order,metadata
) values
('avatar_frame_common','Khung Avatar Phổ Thông','Khung bạc xanh gọn gàng dành cho mọi người chơi.','avatar_frame','avatar_frame','common',1500,'shop/items/avatar_frame_common.webp',null,false,true,true,true,false,10,'{}'),
('avatar_frame_rare','Khung Avatar Hiếm','Khung bạc tím đính đá, nổi bật hơn trên hồ sơ.','avatar_frame','avatar_frame','rare',3200,'shop/items/avatar_frame_rare.webp',null,false,true,true,true,false,20,'{}'),
('avatar_frame_epic','Khung Avatar Sử Thi','Khung vàng tím lộng lẫy dành cho bộ sưu tập cao cấp.','avatar_frame','avatar_frame','epic',6000,'shop/items/avatar_frame_epic.webp',null,false,true,true,true,false,30,'{}'),
('avatar_frame_ice_elite','Khung Băng Lam Tinh Anh','Khung băng xanh bạc với vẻ lạnh lùng và tinh anh.','avatar_frame','avatar_frame','elite',4800,'shop/items/avatar_frame_ice_elite.webp',null,false,true,true,true,false,40,'{}'),
('avatar_frame_fire_warrior','Khung Lửa Chiến Thần','Ngọn lửa chiến đấu bao quanh Avatar của người sở hữu.','avatar_frame','avatar_frame','epic',7500,'shop/items/avatar_frame_fire_warrior.webp',null,false,true,true,true,true,50,'{}'),
('avatar_frame_legendary_crown','Khung Huyền Thoại Vương Miện','Khung vương miện đen vàng dành cho hồ sơ huyền thoại.','avatar_frame','avatar_frame','legendary',12000,'shop/items/avatar_frame_legendary_crown.webp',null,false,true,true,true,true,60,'{}'),

('profile_banner_stadium_blue','Banner Sân Vận Động Xanh','Không khí sân vận động xanh bạc hiện đại.','profile_banner','profile_banner','common',1800,'shop/items/profile_banner_stadium_blue.webp',null,false,true,true,true,false,110,'{}'),
('profile_banner_stadium_premium','Banner Sân Vận Động Premium','Sân vận động vàng tím dành cho hồ sơ cao cấp.','profile_banner','profile_banner','rare',4500,'shop/items/profile_banner_stadium_premium.webp',null,false,true,true,true,true,120,'{}'),
('profile_banner_ice','Banner Băng Lam','Khung cảnh băng lam sáng rõ và mạnh mẽ.','profile_banner','profile_banner','epic',5000,'shop/items/profile_banner_ice.webp',null,false,true,true,true,false,130,'{}'),
('profile_banner_neon_green','Banner Xanh Lục Neon','Sân vận động xanh lục mang phong cách công nghệ.','profile_banner','profile_banner','rare',3500,'shop/items/profile_banner_neon_green.webp',null,false,true,true,true,false,140,'{}'),
('profile_banner_fire','Banner Đỏ Lửa','Sân vận động đỏ lửa cho những trận đấu nóng bỏng.','profile_banner','profile_banner','epic',6500,'shop/items/profile_banner_fire.webp',null,false,true,true,true,false,150,'{}'),
('profile_banner_legendary_red_purple','Banner Huyền Thoại Đỏ Tím','Banner đỏ tím sang trọng dành cho người chơi nổi bật.','profile_banner','profile_banner','legendary',9500,'shop/items/profile_banner_legendary_red_purple.webp',null,false,true,true,true,true,160,'{}'),

('profile_badge_rising_rookie','Tân Binh Sáng Giá','Khiên sao xanh thể hiện một tân binh đầy triển vọng.','profile_badge','profile_badge','common',1500,'shop/items/profile_badge_rising_rookie.webp','shop/items/profile_badge_rising_rookie_96.webp',false,true,true,true,false,210,'{}'),
('profile_badge_pitch_warrior','Chiến Binh Sân Cỏ','Khiên bóng đá đỏ vàng dành cho chiến binh sân cỏ.','profile_badge','profile_badge','rare',3000,'shop/items/profile_badge_pitch_warrior.webp','shop/items/profile_badge_pitch_warrior_96.webp',false,true,true,true,false,220,'{}'),
('profile_badge_fire_streak','Chuỗi Thắng Rực Lửa','Ngọn lửa và đôi cánh tượng trưng cho phong độ bùng nổ.','profile_badge','profile_badge','epic',5000,'shop/items/profile_badge_fire_streak.webp','shop/items/profile_badge_fire_streak_96.webp',false,true,true,true,true,230,'{}'),
('profile_badge_elite_crown','Vương Miện Elite','Vương miện đá quý dành cho hồ sơ tinh anh.','profile_badge','profile_badge','elite',6500,'shop/items/profile_badge_elite_crown.webp','shop/items/profile_badge_elite_crown_96.webp',false,true,true,true,false,240,'{}'),
('profile_badge_legendary_diamond','Huyền Thoại Kim Cương','Kim cương tím biểu trưng cho đẳng cấp huyền thoại.','profile_badge','profile_badge','legendary',9000,'shop/items/profile_badge_legendary_diamond.webp','shop/items/profile_badge_legendary_diamond_96.webp',false,true,true,true,true,250,'{}'),

('name_style_neon_blue','Màu Tên Xanh Neon','Mở khóa vĩnh viễn hiệu ứng tên xanh Neon.','name_style','name_style','rare',1800,'shop/items/name_style_neon_blue.webp',null,false,true,true,true,false,310,'{"css_class":"name-style-neon-blue"}'),
('name_style_elite_purple','Màu Tên Tím Elite','Mở khóa vĩnh viễn hiệu ứng tên tím Elite.','name_style','name_style','epic',3500,'shop/items/name_style_elite_purple.webp',null,false,true,true,true,false,320,'{"css_class":"name-style-elite-purple"}'),
('name_style_champion_gold','Màu Tên Vàng Champion','Mở khóa vĩnh viễn hiệu ứng tên vàng Champion.','name_style','name_style','legendary',6000,'shop/items/name_style_champion_gold.webp',null,false,true,true,true,true,330,'{"css_class":"name-style-champion-gold"}'),

('display_name_change_ticket','Vé Đổi Tên Hiển Thị','Dùng 1 vé để đổi tên sau khi đã hết 2 lượt miễn phí.','utility','display_name_ticket','rare',2500,'shop/items/display_name_change_ticket.webp',null,true,false,true,true,false,410,'{"usage":"display_name"}'),
('discount_coupon_05','Phiếu Giảm Giá 5%','Giảm 5% khi mua một vật phẩm đủ điều kiện.','utility','discount_coupon','common',150,'shop/items/discount_coupon_05.webp',null,true,false,true,true,false,420,'{"discount_percent":5,"max_discount":300,"minimum_subtotal":3000}'),
('discount_coupon_10','Phiếu Giảm Giá 10%','Giảm 10% khi mua một vật phẩm đủ điều kiện.','utility','discount_coupon','rare',400,'shop/items/discount_coupon_10.webp',null,true,false,true,true,false,430,'{"discount_percent":10,"max_discount":800,"minimum_subtotal":5000}'),
('discount_coupon_20','Phiếu Giảm Giá 20%','Phần thưởng Admin: giảm 20% cho một giao dịch đủ điều kiện.','utility','discount_coupon','epic',0,'shop/items/discount_coupon_20.webp',null,true,false,true,false,false,440,'{"discount_percent":20,"max_discount":1800,"minimum_subtotal":5000,"reward_only":true}'),
('discount_coupon_30','Phiếu Giảm Giá 30%','Phần thưởng Admin hiếm: giảm 30% cho một giao dịch đủ điều kiện.','utility','discount_coupon','legendary',0,'shop/items/discount_coupon_30.webp',null,true,false,true,false,false,450,'{"discount_percent":30,"max_discount":3000,"minimum_subtotal":7000,"reward_only":true}')
on conflict (code) do update set
    name=excluded.name,
    description=excluded.description,
    category=excluded.category,
    item_type=excluded.item_type,
    rarity=excluded.rarity,
    image_path=excluded.image_path,
    preview_path=excluded.preview_path,
    is_consumable=excluded.is_consumable,
    is_unique=excluded.is_unique,
    metadata=excluded.metadata,
    updated_at=now();

-- Quy tắc cố định theo yêu cầu: 20% và 30% tồn tại trong catalog nhưng không bày bán.
update public.shop_items
set is_active=true, is_listed=false, is_featured=false, price_zcoin=0, updated_at=now()
where code in ('discount_coupon_20','discount_coupon_30');

alter table public.shop_items drop constraint if exists shop_reward_coupon_not_listed;
alter table public.shop_items add constraint shop_reward_coupon_not_listed
    check (code not in ('discount_coupon_20','discount_coupon_30') or is_listed=false);

-- =====================================================================
-- RPC mua vật phẩm nguyên tử
-- =====================================================================
create or replace function public.purchase_shop_item(
    p_user_id uuid,
    p_item_code text,
    p_coupon_inventory_id uuid,
    p_request_key text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_user public.users%rowtype;
    v_item public.shop_items%rowtype;
    v_existing public.shop_purchases%rowtype;
    v_coupon_inventory public.user_inventory%rowtype;
    v_coupon_item public.shop_items%rowtype;
    v_inventory_id uuid;
    v_purchase_id uuid;
    v_before bigint;
    v_after bigint;
    v_subtotal integer;
    v_discount integer := 0;
    v_final integer;
    v_percent integer := 0;
    v_cap integer := 0;
    v_minimum integer := 0;
    v_key text := btrim(coalesce(p_request_key,''));
    v_transaction_type text;
    v_source text;
    v_transaction_constraints text := '';
    v_source_constraints text := '';
begin
    if p_user_id is null then raise exception 'SHOP_INVALID_USER'; end if;
    if coalesce(btrim(p_item_code),'')='' then raise exception 'SHOP_ITEM_NOT_FOUND'; end if;
    if v_key='' or char_length(v_key)>120 then raise exception 'SHOP_INVALID_REQUEST_KEY'; end if;

    perform pg_advisory_xact_lock(hashtext(v_key));
    select * into v_existing from public.shop_purchases where request_key=v_key limit 1;
    if found then
        select * into v_item from public.shop_items where id=v_existing.item_id;
        if v_existing.user_id<>p_user_id or v_item.code<>btrim(p_item_code) then
            raise exception 'SHOP_REQUEST_KEY_CONFLICT';
        end if;
        return jsonb_build_object(
            'purchase_id',v_existing.id,'item_id',v_existing.item_id,
            'item_code',v_item.code,'item_name',v_item.name,
            'subtotal',v_existing.subtotal,'discount_amount',v_existing.discount_amount,
            'final_price',v_existing.final_price,'balance_before',v_existing.balance_before,
            'balance_after',v_existing.balance_after,'duplicate',true
        );
    end if;

    select * into v_item
    from public.shop_items
    where code=btrim(p_item_code)
    for update;
    if not found then raise exception 'SHOP_ITEM_NOT_FOUND'; end if;
    if not v_item.is_active then raise exception 'SHOP_ITEM_UNAVAILABLE'; end if;
    if not v_item.is_listed then raise exception 'SHOP_ITEM_NOT_FOR_SALE'; end if;
    if v_item.starts_at is not null and now()<v_item.starts_at then raise exception 'SHOP_ITEM_UNAVAILABLE'; end if;
    if v_item.ends_at is not null and now()>v_item.ends_at then raise exception 'SHOP_ITEM_UNAVAILABLE'; end if;

    select * into v_user
    from public.users
    where id=p_user_id and role='player'
    for update;
    if not found then raise exception 'SHOP_USER_NOT_FOUND'; end if;

    if v_item.is_unique and exists(
        select 1 from public.user_inventory
        where user_id=p_user_id and item_id=v_item.id and quantity>0
    ) then
        raise exception 'SHOP_ITEM_ALREADY_OWNED';
    end if;

    v_subtotal := greatest(0,coalesce(v_item.price_zcoin,0));

    if p_coupon_inventory_id is not null then
        if v_item.item_type='discount_coupon' then raise exception 'COUPON_NOT_ELIGIBLE'; end if;
        if coalesce(v_item.metadata->>'coupon_eligible','true')='false' then raise exception 'COUPON_NOT_ELIGIBLE'; end if;

        select * into v_coupon_inventory
        from public.user_inventory
        where id=p_coupon_inventory_id and user_id=p_user_id and quantity>0
        for update;
        if not found then raise exception 'INVALID_SHOP_COUPON'; end if;

        select * into v_coupon_item
        from public.shop_items
        where id=v_coupon_inventory.item_id and item_type='discount_coupon' and is_active=true;
        if not found then raise exception 'INVALID_SHOP_COUPON'; end if;

        v_percent := greatest(0,least(100,coalesce((v_coupon_item.metadata->>'discount_percent')::integer,0)));
        v_cap := greatest(0,coalesce((v_coupon_item.metadata->>'max_discount')::integer,0));
        v_minimum := greatest(0,coalesce((v_coupon_item.metadata->>'minimum_subtotal')::integer,0));
        if v_percent<=0 then raise exception 'INVALID_SHOP_COUPON'; end if;
        if v_subtotal<v_minimum then raise exception 'COUPON_MINIMUM_NOT_MET'; end if;
        v_discount := floor(v_subtotal::numeric*v_percent::numeric/100.0)::integer;
        if v_cap>0 then v_discount:=least(v_discount,v_cap); end if;
        v_discount:=least(v_discount,v_subtotal);
    end if;

    v_final := greatest(0,v_subtotal-v_discount);
    v_before := greatest(0,coalesce(v_user.zcoin_balance,0));
    if v_before<v_final then raise exception 'INSUFFICIENT_ZCOIN'; end if;
    v_after := v_before-v_final;

    update public.users set zcoin_balance=v_after::integer where id=p_user_id;

    insert into public.user_inventory(user_id,item_id,quantity,acquired_from,metadata)
    values(p_user_id,v_item.id,1,'shop',jsonb_build_object('item_code',v_item.code))
    on conflict(user_id,item_id) do update set
        quantity=case when v_item.is_unique then greatest(public.user_inventory.quantity,1)
                      else public.user_inventory.quantity+1 end,
        updated_at=now(),
        acquired_from='shop',
        metadata=coalesce(public.user_inventory.metadata,'{}'::jsonb)||excluded.metadata
    returning id into v_inventory_id;

    if p_coupon_inventory_id is not null then
        if v_coupon_inventory.quantity<=1 then
            delete from public.user_inventory where id=v_coupon_inventory.id;
        else
            update public.user_inventory
            set quantity=quantity-1,updated_at=now()
            where id=v_coupon_inventory.id;
        end if;
    end if;

    insert into public.shop_purchases(
        user_id,item_id,quantity,unit_price,subtotal,discount_amount,final_price,
        coupon_item_id,coupon_percent,balance_before,balance_after,request_key,metadata
    ) values(
        p_user_id,v_item.id,1,v_subtotal,v_subtotal,v_discount,v_final,
        case when p_coupon_inventory_id is null then null else v_coupon_item.id end,
        v_percent,v_before::integer,v_after::integer,v_key,
        jsonb_build_object('item_code',v_item.code,'item_name',v_item.name,'app_version','Collap_V1.14.40_SHOP_INVENTORY_PHASE3')
    ) returning id into v_purchase_id;

    if v_final>0 then
        select coalesce(string_agg(pg_get_constraintdef(c.oid),' '),'') into v_transaction_constraints
        from pg_constraint c where c.conrelid='public.zcoin_transactions'::regclass
          and c.contype='c' and pg_get_constraintdef(c.oid) ilike '%transaction_type%';
        select coalesce(string_agg(pg_get_constraintdef(c.oid),' '),'') into v_source_constraints
        from pg_constraint c where c.conrelid='public.zcoin_transactions'::regclass
          and c.contype='c' and pg_get_constraintdef(c.oid) ilike '%source%';

        if v_transaction_constraints ilike '%spend%' then v_transaction_type:='spend';
        elsif v_transaction_constraints ilike '%admin_debit%' then v_transaction_type:='admin_debit';
        elsif v_transaction_constraints ilike '%debit%' then v_transaction_type:='debit';
        else v_transaction_type:='spend'; end if;

        if v_source_constraints ilike '%shop%' then v_source:='shop';
        elsif v_source_constraints ilike '%system%' then v_source:='system';
        elsif v_source_constraints ilike '%admin%' then v_source:='admin';
        else v_source:='shop'; end if;

        insert into public.zcoin_transactions(
            user_id,amount,balance_after,transaction_type,source,description,metadata
        ) values(
            p_user_id,-v_final,v_after::integer,v_transaction_type,v_source,
            'Mua '||v_item.name,
            jsonb_build_object(
                'balance_before',v_before,'item_id',v_item.id,'item_code',v_item.code,
                'item_name',v_item.name,'purchase_id',v_purchase_id,'discount_amount',v_discount,
                'idempotency_key','shop:'||v_key,'app_version','Collap_V1.14.40_SHOP_INVENTORY_PHASE3'
            )
        );
    end if;

    return jsonb_build_object(
        'purchase_id',v_purchase_id,'inventory_id',v_inventory_id,
        'item_id',v_item.id,'item_code',v_item.code,'item_name',v_item.name,
        'subtotal',v_subtotal,'discount_amount',v_discount,'final_price',v_final,
        'balance_before',v_before,'balance_after',v_after,'duplicate',false
    );
end
$$;

-- =====================================================================
-- RPC trang bị / gỡ trang bị
-- =====================================================================
create or replace function public.equip_shop_item(
    p_user_id uuid,
    p_inventory_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_inventory public.user_inventory%rowtype;
    v_item public.shop_items%rowtype;
    v_slot text;
begin
    select * into v_inventory
    from public.user_inventory
    where id=p_inventory_id and user_id=p_user_id and quantity>0
    for update;
    if not found then raise exception 'INVENTORY_ITEM_NOT_FOUND'; end if;

    select * into v_item from public.shop_items where id=v_inventory.item_id;
    if not found then raise exception 'SHOP_ITEM_NOT_FOUND'; end if;
    if v_item.is_consumable then raise exception 'ITEM_NOT_EQUIPPABLE'; end if;

    v_slot := case v_item.item_type
        when 'avatar_frame' then 'avatar_frame'
        when 'profile_banner' then 'profile_banner'
        when 'name_style' then 'name_style'
        when 'profile_badge' then 'profile_badge'
        else null end;
    if v_slot is null then raise exception 'ITEM_NOT_EQUIPPABLE'; end if;

    insert into public.user_equipment(user_id,slot,inventory_id,item_id,equipped_at)
    values(p_user_id,v_slot,v_inventory.id,v_item.id,now())
    on conflict(user_id,slot) do update set
        inventory_id=excluded.inventory_id,item_id=excluded.item_id,equipped_at=now();

    return jsonb_build_object('slot',v_slot,'inventory_id',v_inventory.id,'item_id',v_item.id,'item_code',v_item.code,'item_name',v_item.name);
end
$$;

create or replace function public.unequip_shop_slot(
    p_user_id uuid,
    p_slot text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare v_deleted integer;
begin
    if p_slot not in ('avatar_frame','profile_banner','name_style','profile_badge','profile_card_theme') then
        raise exception 'INVALID_EQUIPMENT_SLOT';
    end if;
    delete from public.user_equipment where user_id=p_user_id and slot=p_slot;
    get diagnostics v_deleted=row_count;
    return jsonb_build_object('slot',p_slot,'removed',v_deleted>0);
end
$$;

-- =====================================================================
-- RPC đổi tên: dùng lượt miễn phí trước, sau đó tự tiêu thụ Vé đổi tên
-- =====================================================================
create or replace function public.change_display_name_with_shop_entitlement(
    p_user_id uuid,
    p_new_display_name text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_user public.users%rowtype;
    v_name text;
    v_ticket public.user_inventory%rowtype;
    v_used_ticket boolean:=false;
    v_ticket_remaining integer:=0;
begin
    v_name:=regexp_replace(btrim(coalesce(p_new_display_name,'')),'\s+',' ','g');
    if char_length(v_name)<2 or char_length(v_name)>40 then raise exception 'INVALID_DISPLAY_NAME'; end if;

    if exists(select 1 from public.users where id<>p_user_id and lower(btrim(coalesce(display_name,'')))=lower(v_name)) then
        raise exception 'DISPLAY_NAME_DUPLICATE';
    end if;

    select * into v_user from public.users where id=p_user_id for update;
    if not found then raise exception 'SHOP_USER_NOT_FOUND'; end if;
    if lower(btrim(coalesce(v_user.display_name,'')))=lower(v_name) then raise exception 'DISPLAY_NAME_UNCHANGED'; end if;

    if coalesce(v_user.display_name_change_count,0)<2 then
        update public.users
        set display_name=v_name,
            display_name_change_count=coalesce(display_name_change_count,0)+1,
            display_name_changed_at=now()
        where id=p_user_id;
    else
        select ui.* into v_ticket
        from public.user_inventory ui
        join public.shop_items si on si.id=ui.item_id
        where ui.user_id=p_user_id and ui.quantity>0 and si.code='display_name_change_ticket'
        order by ui.acquired_at
        limit 1
        for update of ui;
        if not found then raise exception 'DISPLAY_NAME_CHANGE_LIMIT_REACHED'; end if;

        v_used_ticket:=true;
        if v_ticket.quantity<=1 then
            delete from public.user_inventory where id=v_ticket.id;
            v_ticket_remaining:=0;
        else
            update public.user_inventory set quantity=quantity-1,updated_at=now() where id=v_ticket.id;
            v_ticket_remaining:=v_ticket.quantity-1;
        end if;
        update public.users set display_name=v_name,display_name_changed_at=now() where id=p_user_id;
    end if;

    return jsonb_build_object(
        'display_name',v_name,'used_ticket',v_used_ticket,
        'free_changes_remaining',greatest(0,2-case when v_used_ticket then coalesce(v_user.display_name_change_count,2) else coalesce(v_user.display_name_change_count,0)+1 end),
        'ticket_remaining',v_ticket_remaining
    );
end
$$;

-- =====================================================================
-- RPC Admin tặng vật phẩm cho một người hoặc toàn bộ player
-- =====================================================================
create or replace function public.admin_grant_shop_item(
    p_actor_user_id uuid,
    p_item_code text,
    p_quantity integer,
    p_target_user_id uuid,
    p_all_players boolean,
    p_note text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_actor public.users%rowtype;
    v_item public.shop_items%rowtype;
    v_count integer:=0;
    v_quantity integer;
begin
    if p_quantity is null or p_quantity<1 or p_quantity>100 then raise exception 'INVALID_GRANT_QUANTITY'; end if;
    select * into v_actor from public.users where id=p_actor_user_id;
    if not found or not (
        coalesce(v_actor.role,'')='admin' or coalesce(v_actor.admin_level,'none') in ('owner','admin')
    ) then raise exception 'SHOP_ADMIN_PERMISSION_DENIED'; end if;

    select * into v_item from public.shop_items where code=btrim(coalesce(p_item_code,''));
    if not found then raise exception 'SHOP_ITEM_NOT_FOUND'; end if;
    v_quantity:=case when v_item.is_unique then 1 else p_quantity end;

    if coalesce(p_all_players,false) then
        insert into public.user_inventory(user_id,item_id,quantity,acquired_from,metadata)
        select u.id,v_item.id,v_quantity,'admin_grant',jsonb_build_object(
            'actor_user_id',p_actor_user_id,'note',coalesce(p_note,''),'granted_at',now()
        )
        from public.users u where u.role='player'
        on conflict(user_id,item_id) do update set
            quantity=case when v_item.is_unique then greatest(public.user_inventory.quantity,1)
                          else public.user_inventory.quantity+excluded.quantity end,
            updated_at=now(),acquired_from='admin_grant',
            metadata=coalesce(public.user_inventory.metadata,'{}'::jsonb)||excluded.metadata;
        get diagnostics v_count=row_count;
    else
        if p_target_user_id is null or not exists(select 1 from public.users where id=p_target_user_id and role='player') then
            raise exception 'SHOP_TARGET_NOT_FOUND';
        end if;
        insert into public.user_inventory(user_id,item_id,quantity,acquired_from,metadata)
        values(p_target_user_id,v_item.id,v_quantity,'admin_grant',jsonb_build_object(
            'actor_user_id',p_actor_user_id,'note',coalesce(p_note,''),'granted_at',now()
        ))
        on conflict(user_id,item_id) do update set
            quantity=case when v_item.is_unique then greatest(public.user_inventory.quantity,1)
                          else public.user_inventory.quantity+excluded.quantity end,
            updated_at=now(),acquired_from='admin_grant',
            metadata=coalesce(public.user_inventory.metadata,'{}'::jsonb)||excluded.metadata;
        v_count:=1;
    end if;

    return jsonb_build_object('item_id',v_item.id,'item_code',v_item.code,'item_name',v_item.name,'quantity',v_quantity,'recipient_count',v_count);
end
$$;

-- Cho phép PostgREST nhận chữ ký hàm mới ngay sau khi chạy migration.
notify pgrst,'reload schema';

commit;
