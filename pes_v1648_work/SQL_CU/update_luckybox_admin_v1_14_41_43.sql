-- =====================================================================
-- PES Arena V1.14.41.43 · Lucky Box Giai đoạn 2B
-- Admin cấu hình Draft, kiểm tra, đồng bộ Shop, publish và audit log.
--
-- AN TOÀN:
-- - Chỉ bổ sung/thay thế RPC Lucky Box; không xóa dữ liệu.
-- - Chỉ Rate Version DRAFT được chỉnh sửa.
-- - Publish bị chặn nếu cấu hình không hợp lệ.
-- - Bật hộp bị chặn nếu chưa có Rate Version ACTIVE hợp lệ.
-- - Có thể chạy lại nhiều lần.
-- =====================================================================

begin;

create index if not exists lucky_box_rate_versions_status_idx
    on public.lucky_box_rate_versions(box_id, status, version_number desc);

-- ---------------------------------------------------------------------
-- Kiểm tra đầy đủ một Rate Version. Hàm này không thay đổi dữ liệu.
-- ---------------------------------------------------------------------
create or replace function public.lucky_box_validate_rate_payload(p_rate_version_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path=public
as $$
declare
    v_rate public.lucky_box_rate_versions%rowtype;
    v_box public.lucky_boxes%rowtype;
    v_errors jsonb := '[]'::jsonb;
    v_warnings jsonb := '[]'::jsonb;
    v_w0 numeric := 0;
    v_w1 numeric := 0;
    v_w2 numeric := 0;
    v_w3 numeric := 0;
    v_total numeric := 0;
    v_max_items integer := 0;
    v_item_count integer := 0;
    v_non_item_count integer := 0;
    v_item_weight numeric := 0;
    v_non_item_weight numeric := 0;
    v_enabled_count integer := 0;
    v_no_reward_enabled boolean := false;
begin
    select * into v_rate
    from public.lucky_box_rate_versions
    where id=p_rate_version_id;
    if not found then
        return jsonb_build_object(
            'valid',false,
            'errors',jsonb_build_array('Không tìm thấy phiên bản tỷ lệ.'),
            'warnings','[]'::jsonb
        );
    end if;

    select * into v_box from public.lucky_boxes where id=v_rate.box_id;

    begin
        v_w0 := coalesce((v_rate.item_count_weights->>'0')::numeric,0);
        v_w1 := coalesce((v_rate.item_count_weights->>'1')::numeric,0);
        v_w2 := coalesce((v_rate.item_count_weights->>'2')::numeric,0);
        v_w3 := coalesce((v_rate.item_count_weights->>'3')::numeric,0);
    exception when invalid_text_representation or numeric_value_out_of_range then
        v_errors := v_errors || jsonb_build_array('Trọng số số lượng vật phẩm không phải số hợp lệ.');
        v_w0:=0; v_w1:=0; v_w2:=0; v_w3:=0;
    end;

    if v_w0<0 or v_w1<0 or v_w2<0 or v_w3<0 then
        v_errors := v_errors || jsonb_build_array('Trọng số 0/1/2/3 vật phẩm không được âm.');
    end if;
    v_total := greatest(0,v_w0)+greatest(0,v_w1)+greatest(0,v_w2)+greatest(0,v_w3);
    if v_total<=0 then
        v_errors := v_errors || jsonb_build_array('Tổng trọng số số lượng vật phẩm phải lớn hơn 0.');
    end if;

    if v_w3>0 then v_max_items:=3;
    elsif v_w2>0 then v_max_items:=2;
    elsif v_w1>0 then v_max_items:=1;
    end if;

    select
        count(*) filter(where is_enabled=true and weight>0),
        count(*) filter(where counts_as_item=true and is_enabled=true and weight>0),
        count(*) filter(where counts_as_item=false and is_enabled=true and weight>0),
        coalesce(sum(weight) filter(where counts_as_item=true and is_enabled=true),0),
        coalesce(sum(weight) filter(where counts_as_item=false and is_enabled=true),0),
        coalesce(bool_or(reward_type='no_reward' and is_enabled=true and weight>0),false)
    into v_enabled_count,v_item_count,v_non_item_count,v_item_weight,v_non_item_weight,v_no_reward_enabled
    from public.lucky_box_rewards
    where rate_version_id=v_rate.id;

    if v_rate.open_price_zcoin<=0 then
        v_errors := v_errors || jsonb_build_array('Giá mở hộp phải lớn hơn 0 trước khi publish.');
    end if;
    if v_rate.duplicate_policy='pending' then
        v_errors := v_errors || jsonb_build_array('Chưa chọn cách xử lý vật phẩm trùng.');
    end if;
    if v_item_count<v_max_items then
        v_errors := v_errors || jsonb_build_array('Không đủ reward vật phẩm đang bật cho phân phối tối đa '||v_max_items||' vật phẩm.');
    end if;
    if (v_w0>0 or v_w1>0 or v_w2>0) and v_non_item_count<1 then
        v_errors := v_errors || jsonb_build_array('Cần ít nhất một reward không tính là vật phẩm.');
    end if;
    if v_enabled_count<1 then
        v_errors := v_errors || jsonb_build_array('Không có reward nào đang bật với trọng số lớn hơn 0.');
    end if;

    if exists(
        select 1
        from public.lucky_box_rewards r
        left join public.shop_items s on s.id=r.item_id
        where r.rate_version_id=v_rate.id and r.is_enabled=true and r.weight>0
          and r.item_id is not null
          and (s.id is null or s.is_active=false)
    ) then
        v_errors := v_errors || jsonb_build_array('Có reward đang bật nhưng vật phẩm Shop không tồn tại hoặc đã ngừng hoạt động.');
    end if;

    if exists(
        select 1 from public.lucky_box_rewards r
        where r.rate_version_id=v_rate.id
          and r.starts_at is not null and r.ends_at is not null
          and r.starts_at>=r.ends_at
    ) then
        v_errors := v_errors || jsonb_build_array('Có reward có thời gian bắt đầu không nhỏ hơn thời gian kết thúc.');
    end if;

    if exists(
        select 1 from public.lucky_box_rewards r
        where r.rate_version_id=v_rate.id
          and r.issue_limit is not null and r.issue_limit<r.issued_count
    ) then
        v_errors := v_errors || jsonb_build_array('Có giới hạn phát hành thấp hơn số lượng đã phát.');
    end if;

    if v_rate.duplicate_policy='convert_zcoin' and exists(
        select 1
        from public.lucky_box_rewards r
        join public.shop_items s on s.id=r.item_id
        where r.rate_version_id=v_rate.id and r.is_enabled=true and r.weight>0
          and s.is_unique=true and coalesce(r.duplicate_zcoin,0)<=0
    ) then
        v_errors := v_errors || jsonb_build_array('Có vật phẩm vĩnh viễn chưa đặt mức Zcoin bồi hoàn khi bị trùng.');
    end if;

    if v_no_reward_enabled and not coalesce(v_box.no_reward_enabled,false) then
        v_errors := v_errors || jsonb_build_array('Reward “Chúc bạn may mắn lần sau” đang bật nhưng cấu hình hộp chưa cho phép kết quả trống.');
    end if;
    if coalesce(v_box.no_reward_enabled,false) and not v_no_reward_enabled then
        v_warnings := v_warnings || jsonb_build_array('Hộp cho phép kết quả trống nhưng reward “Chúc bạn may mắn lần sau” chưa được bật.');
    end if;

    if exists(
        select 1 from public.lucky_box_rewards r
        where r.rate_version_id=v_rate.id and r.is_enabled=true and r.weight=0
    ) then
        v_warnings := v_warnings || jsonb_build_array('Có reward được bật nhưng trọng số bằng 0 nên sẽ không xuất hiện.');
    end if;

    return jsonb_build_object(
        'valid',jsonb_array_length(v_errors)=0,
        'rate_version_id',v_rate.id,
        'version_number',v_rate.version_number,
        'status',v_rate.status,
        'errors',v_errors,
        'warnings',v_warnings,
        'item_count_weights',v_rate.item_count_weights,
        'item_count_total',v_total,
        'item_count_percentages',jsonb_build_object(
            '0',case when v_total>0 then round(v_w0*100.0/v_total,4) else 0 end,
            '1',case when v_total>0 then round(v_w1*100.0/v_total,4) else 0 end,
            '2',case when v_total>0 then round(v_w2*100.0/v_total,4) else 0 end,
            '3',case when v_total>0 then round(v_w3*100.0/v_total,4) else 0 end
        ),
        'enabled_reward_count',v_enabled_count,
        'enabled_item_reward_count',v_item_count,
        'enabled_non_item_reward_count',v_non_item_count,
        'item_reward_weight_total',v_item_weight,
        'non_item_reward_weight_total',v_non_item_weight
    );
end;
$$;

create or replace function public.validate_lucky_box_rate_version(
    p_actor_user_id uuid,
    p_rate_version_id uuid
)
returns jsonb
language plpgsql
stable
security definer
set search_path=public
as $$
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then
        raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED';
    end if;
    return public.lucky_box_validate_rate_payload(p_rate_version_id);
end;
$$;

-- ---------------------------------------------------------------------
-- Lưu cấu hình chung của hộp.
-- ---------------------------------------------------------------------
create or replace function public.save_lucky_box_config(
    p_actor_user_id uuid,
    p_box_id uuid,
    p_is_enabled boolean,
    p_no_reward_enabled boolean,
    p_description text,
    p_notification_title text,
    p_notification_template text,
    p_reason text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_box public.lucky_boxes%rowtype;
    v_active_rate_id uuid;
    v_validation jsonb;
    v_before jsonb;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_CHANGE_REASON_REQUIRED'; end if;
    if char_length(btrim(coalesce(p_notification_title,'')))<3 then raise exception 'LUCKY_BOX_NOTIFICATION_TITLE_REQUIRED'; end if;
    if position('{rewards}' in coalesce(p_notification_template,''))=0 then raise exception 'LUCKY_BOX_NOTIFICATION_TEMPLATE_INVALID'; end if;

    select * into v_box from public.lucky_boxes where id=p_box_id for update;
    if not found then raise exception 'LUCKY_BOX_NOT_FOUND'; end if;

    v_before:=to_jsonb(v_box);
    update public.lucky_boxes
    set is_enabled=coalesce(p_is_enabled,false),
        no_reward_enabled=coalesce(p_no_reward_enabled,false),
        description=left(coalesce(p_description,''),1000),
        notification_title=left(btrim(p_notification_title),120),
        notification_template=left(btrim(p_notification_template),500),
        updated_at=now()
    where id=v_box.id;

    -- Kiểm tra sau update để validator nhìn thấy đúng lựa chọn no_reward mới.
    -- Nếu lỗi, toàn bộ transaction/RPC tự rollback về cấu hình trước đó.
    if coalesce(p_is_enabled,false) then
        select id into v_active_rate_id
        from public.lucky_box_rate_versions
        where box_id=v_box.id and status='active'
        limit 1;
        if v_active_rate_id is null then raise exception 'LUCKY_BOX_NO_ACTIVE_RATE'; end if;
        v_validation:=public.lucky_box_validate_rate_payload(v_active_rate_id);
        if not coalesce((v_validation->>'valid')::boolean,false) then
            raise exception 'LUCKY_BOX_ACTIVE_RATE_INVALID';
        end if;
    end if;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'save_box_config','lucky_box',v_box.id,btrim(p_reason),v_before,
        (select to_jsonb(b) from public.lucky_boxes b where b.id=v_box.id)
    );

    return (select to_jsonb(b) from public.lucky_boxes b where b.id=v_box.id);
end;
$$;

-- ---------------------------------------------------------------------
-- Lưu giá, phân phối 0/1/2/3, chính sách trùng và ghi chú của Draft.
-- ---------------------------------------------------------------------
create or replace function public.save_lucky_box_rate_version(
    p_actor_user_id uuid,
    p_rate_version_id uuid,
    p_open_price_zcoin integer,
    p_weight_0 bigint,
    p_weight_1 bigint,
    p_weight_2 bigint,
    p_weight_3 bigint,
    p_duplicate_policy text,
    p_notes text,
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
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_CHANGE_REASON_REQUIRED'; end if;
    if coalesce(p_open_price_zcoin,-1)<0 then raise exception 'LUCKY_BOX_INVALID_PRICE'; end if;
    if coalesce(p_weight_0,-1)<0 or coalesce(p_weight_1,-1)<0 or coalesce(p_weight_2,-1)<0 or coalesce(p_weight_3,-1)<0 then
        raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID';
    end if;
    if coalesce(p_weight_0,0)+coalesce(p_weight_1,0)+coalesce(p_weight_2,0)+coalesce(p_weight_3,0)<=0 then
        raise exception 'LUCKY_BOX_ITEM_COUNT_WEIGHTS_INVALID';
    end if;
    if coalesce(p_duplicate_policy,'') not in ('pending','convert_zcoin','allow_quantity','block_owned') then
        raise exception 'LUCKY_BOX_DUPLICATE_POLICY_INVALID';
    end if;

    select * into v_rate from public.lucky_box_rate_versions where id=p_rate_version_id for update;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;
    if v_rate.status<>'draft' then raise exception 'LUCKY_BOX_RATE_NOT_DRAFT'; end if;

    v_before:=to_jsonb(v_rate);
    update public.lucky_box_rate_versions
    set open_price_zcoin=p_open_price_zcoin,
        item_count_weights=jsonb_build_object('0',p_weight_0,'1',p_weight_1,'2',p_weight_2,'3',p_weight_3),
        duplicate_policy=p_duplicate_policy,
        notes=left(coalesce(p_notes,''),1000),
        updated_at=now()
    where id=v_rate.id;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'save_rate_version','lucky_box_rate_version',v_rate.id,btrim(p_reason),v_before,
        (select to_jsonb(r) from public.lucky_box_rate_versions r where r.id=v_rate.id)
    );

    return public.lucky_box_validate_rate_payload(v_rate.id);
end;
$$;

-- ---------------------------------------------------------------------
-- Lưu một reward của Draft.
-- ---------------------------------------------------------------------
create or replace function public.save_lucky_box_reward(
    p_actor_user_id uuid,
    p_reward_id uuid,
    p_weight bigint,
    p_is_enabled boolean,
    p_starts_at timestamptz,
    p_ends_at timestamptz,
    p_issue_limit bigint,
    p_duplicate_zcoin integer,
    p_reason text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_reward public.lucky_box_rewards%rowtype;
    v_rate public.lucky_box_rate_versions%rowtype;
    v_box public.lucky_boxes%rowtype;
    v_item public.shop_items%rowtype;
    v_before jsonb;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_CHANGE_REASON_REQUIRED'; end if;
    if coalesce(p_weight,-1)<0 then raise exception 'LUCKY_BOX_REWARD_WEIGHT_INVALID'; end if;
    if p_starts_at is not null and p_ends_at is not null and p_starts_at>=p_ends_at then
        raise exception 'LUCKY_BOX_REWARD_TIME_INVALID';
    end if;
    if p_issue_limit is not null and p_issue_limit<0 then raise exception 'LUCKY_BOX_ISSUE_LIMIT_INVALID'; end if;
    if p_duplicate_zcoin is not null and p_duplicate_zcoin<0 then raise exception 'LUCKY_BOX_DUPLICATE_ZCOIN_INVALID'; end if;

    select * into v_reward from public.lucky_box_rewards where id=p_reward_id for update;
    if not found then raise exception 'LUCKY_BOX_REWARD_NOT_FOUND'; end if;
    select * into v_rate from public.lucky_box_rate_versions where id=v_reward.rate_version_id for update;
    if v_rate.status<>'draft' then raise exception 'LUCKY_BOX_RATE_NOT_DRAFT'; end if;
    select * into v_box from public.lucky_boxes where id=v_rate.box_id;

    if p_issue_limit is not null and p_issue_limit<v_reward.issued_count then
        raise exception 'LUCKY_BOX_ISSUE_LIMIT_BELOW_ISSUED';
    end if;
    if coalesce(p_is_enabled,false) and v_reward.reward_type='no_reward' and not coalesce(v_box.no_reward_enabled,false) then
        raise exception 'LUCKY_BOX_NO_REWARD_NOT_APPROVED';
    end if;
    if coalesce(p_is_enabled,false) and v_reward.item_id is not null then
        select * into v_item from public.shop_items where id=v_reward.item_id;
        if not found or not coalesce(v_item.is_active,false) then
            raise exception 'LUCKY_BOX_REWARD_ITEM_INACTIVE';
        end if;
    end if;

    v_before:=to_jsonb(v_reward);
    update public.lucky_box_rewards
    set weight=p_weight,
        is_enabled=coalesce(p_is_enabled,false),
        starts_at=p_starts_at,
        ends_at=p_ends_at,
        issue_limit=p_issue_limit,
        duplicate_zcoin=p_duplicate_zcoin,
        updated_at=now()
    where id=v_reward.id;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'save_reward','lucky_box_reward',v_reward.id,btrim(p_reason),v_before,
        (select to_jsonb(r) from public.lucky_box_rewards r where r.id=v_reward.id)
    );

    return jsonb_build_object(
        'reward',(select to_jsonb(r) from public.lucky_box_rewards r where r.id=v_reward.id),
        'validation',public.lucky_box_validate_rate_payload(v_rate.id)
    );
end;
$$;

-- ---------------------------------------------------------------------
-- Tạo Draft mới bằng cách sao chép một phiên bản hiện có.
-- ---------------------------------------------------------------------
create or replace function public.clone_lucky_box_rate_version(
    p_actor_user_id uuid,
    p_source_rate_version_id uuid,
    p_reason text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
    v_source public.lucky_box_rate_versions%rowtype;
    v_new_id uuid;
    v_new_version integer;
    v_reward_count integer;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_CHANGE_REASON_REQUIRED'; end if;

    select * into v_source from public.lucky_box_rate_versions where id=p_source_rate_version_id;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;

    perform pg_advisory_xact_lock(hashtext('luckybox-rate-version:'||v_source.box_id::text));
    select coalesce(max(version_number),0)+1 into v_new_version
    from public.lucky_box_rate_versions where box_id=v_source.box_id;

    insert into public.lucky_box_rate_versions(
        box_id,version_number,status,open_price_zcoin,item_count_weights,duplicate_policy,
        notes,created_by,metadata
    ) values(
        v_source.box_id,v_new_version,'draft',v_source.open_price_zcoin,v_source.item_count_weights,
        v_source.duplicate_policy,'Bản nháp sao chép từ Version '||v_source.version_number||'.',
        p_actor_user_id,
        coalesce(v_source.metadata,'{}'::jsonb)||jsonb_build_object(
            'cloned_from_rate_version_id',v_source.id,
            'cloned_from_version_number',v_source.version_number,
            'production_approved',false
        )
    ) returning id into v_new_id;

    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,item_id,reward_amount,
        weight,is_enabled,rarity,asset_path,starts_at,ends_at,issue_limit,issued_count,
        duplicate_zcoin,sort_order,metadata
    )
    select v_new_id,reward_code,reward_name,reward_type,counts_as_item,item_id,reward_amount,
           weight,is_enabled,rarity,asset_path,starts_at,ends_at,issue_limit,0,
           duplicate_zcoin,sort_order,
           coalesce(metadata,'{}'::jsonb)||jsonb_build_object('cloned_from_reward_id',id)
    from public.lucky_box_rewards
    where rate_version_id=v_source.id;

    get diagnostics v_reward_count = row_count;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'clone_rate_version','lucky_box_rate_version',v_new_id,btrim(p_reason),
        jsonb_build_object('source_rate_version_id',v_source.id,'source_version_number',v_source.version_number),
        jsonb_build_object('rate_version_id',v_new_id,'version_number',v_new_version,'reward_count',v_reward_count)
    );

    return jsonb_build_object('rate_version_id',v_new_id,'version_number',v_new_version,'status','draft','reward_count',v_reward_count);
end;
$$;

-- ---------------------------------------------------------------------
-- Đồng bộ vật phẩm Shop/độc quyền còn thiếu vào Draft ở trạng thái TẮT.
-- Không thay đổi trọng số hoặc trạng thái của reward đã tồn tại.
-- ---------------------------------------------------------------------
create or replace function public.sync_lucky_box_rewards(
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
    v_before_count integer;
    v_after_count integer;
    v_added integer;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_CHANGE_REASON_REQUIRED'; end if;

    select * into v_rate from public.lucky_box_rate_versions where id=p_rate_version_id for update;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;
    if v_rate.status<>'draft' then raise exception 'LUCKY_BOX_RATE_NOT_DRAFT'; end if;

    select count(*) into v_before_count from public.lucky_box_rewards where rate_version_id=v_rate.id;

    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,item_id,
        weight,is_enabled,rarity,asset_path,sort_order,metadata
    )
    select v_rate.id,'shop_'||s.code,s.name,
           case when s.item_type='discount_coupon' then 'discount_coupon' else 'shop_item' end,
           true,s.id,0,false,s.rarity,
           case s.code when 'discount_coupon_05' then 'luckybox/rewards/discount-coupon-05.webp'
                       when 'discount_coupon_10' then 'luckybox/rewards/discount-coupon-10.webp'
                       else s.image_path end,
           1000+coalesce(s.sort_order,0),
           jsonb_build_object('synced_version','V1.14.41.43','shop_item_code',s.code)
    from public.shop_items s
    where s.is_active=true and s.is_listed=true and s.code not like 'lb_%'
    on conflict(rate_version_id,reward_code) do update set
        reward_name=excluded.reward_name,
        item_id=excluded.item_id,
        rarity=excluded.rarity,
        asset_path=excluded.asset_path,
        updated_at=now();

    insert into public.lucky_box_rewards(
        rate_version_id,reward_code,reward_name,reward_type,counts_as_item,item_id,
        weight,is_enabled,rarity,asset_path,sort_order,metadata
    )
    select v_rate.id,s.code,s.name,'exclusive_item',true,s.id,0,false,s.rarity,s.image_path,
           2000+coalesce(s.sort_order,0),
           jsonb_build_object('synced_version','V1.14.41.43','luckybox_exclusive',true)
    from public.shop_items s
    where s.code like 'lb_banner_%' or s.code='lb_frame_ke_thong_tri_hoang_gia'
    on conflict(rate_version_id,reward_code) do update set
        reward_name=excluded.reward_name,
        item_id=excluded.item_id,
        rarity=excluded.rarity,
        asset_path=excluded.asset_path,
        updated_at=now();

    select count(*) into v_after_count from public.lucky_box_rewards where rate_version_id=v_rate.id;
    v_added:=greatest(0,v_after_count-v_before_count);

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'sync_rewards','lucky_box_rate_version',v_rate.id,btrim(p_reason),
        jsonb_build_object('reward_count',v_before_count),
        jsonb_build_object('reward_count',v_after_count,'added',v_added)
    );

    return jsonb_build_object('rate_version_id',v_rate.id,'before_count',v_before_count,'after_count',v_after_count,'added',v_added);
end;
$$;

-- ---------------------------------------------------------------------
-- Publish Draft: dùng cùng validator với trang Admin.
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
    v_validation jsonb;
begin
    if not public.lucky_box_is_admin(p_actor_user_id) then raise exception 'LUCKY_BOX_ADMIN_PERMISSION_DENIED'; end if;
    if char_length(btrim(coalesce(p_reason,'')))<3 then raise exception 'LUCKY_BOX_PUBLISH_REASON_REQUIRED'; end if;

    select * into v_rate from public.lucky_box_rate_versions where id=p_rate_version_id for update;
    if not found then raise exception 'LUCKY_BOX_RATE_VERSION_NOT_FOUND'; end if;
    if v_rate.status<>'draft' then raise exception 'LUCKY_BOX_RATE_NOT_DRAFT'; end if;

    v_validation:=public.lucky_box_validate_rate_payload(v_rate.id);
    if not coalesce((v_validation->>'valid')::boolean,false) then
        raise exception 'LUCKY_BOX_RATE_INVALID:%',coalesce(v_validation->'errors','[]'::jsonb)::text;
    end if;

    v_before:=to_jsonb(v_rate);
    update public.lucky_box_rate_versions
    set status='archived',updated_at=now()
    where box_id=v_rate.box_id and status='active';

    update public.lucky_box_rate_versions
    set status='active',published_by=p_actor_user_id,published_at=now(),updated_at=now(),
        metadata=coalesce(metadata,'{}'::jsonb)||jsonb_build_object('production_approved',true)
    where id=v_rate.id;

    insert into public.lucky_box_admin_audit_logs(
        actor_user_id,action,entity_type,entity_id,reason,before_data,after_data
    ) values(
        p_actor_user_id,'publish_rate_version','lucky_box_rate_version',v_rate.id,btrim(p_reason),
        v_before,(select to_jsonb(rv) from public.lucky_box_rate_versions rv where rv.id=v_rate.id)
    );

    return jsonb_build_object(
        'rate_version_id',v_rate.id,
        'version_number',v_rate.version_number,
        'status','active',
        'box_enabled',(select is_enabled from public.lucky_boxes where id=v_rate.box_id)
    );
end;
$$;

revoke all on function public.lucky_box_validate_rate_payload(uuid) from public,anon,authenticated;
revoke all on function public.validate_lucky_box_rate_version(uuid,uuid) from public,anon,authenticated;
revoke all on function public.save_lucky_box_config(uuid,uuid,boolean,boolean,text,text,text,text) from public,anon,authenticated;
revoke all on function public.save_lucky_box_rate_version(uuid,uuid,integer,bigint,bigint,bigint,bigint,text,text,text) from public,anon,authenticated;
revoke all on function public.save_lucky_box_reward(uuid,uuid,bigint,boolean,timestamptz,timestamptz,bigint,integer,text) from public,anon,authenticated;
revoke all on function public.clone_lucky_box_rate_version(uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.sync_lucky_box_rewards(uuid,uuid,text) from public,anon,authenticated;
revoke all on function public.publish_lucky_box_rate_version(uuid,uuid,text) from public,anon,authenticated;

grant execute on function public.lucky_box_validate_rate_payload(uuid) to service_role;
grant execute on function public.validate_lucky_box_rate_version(uuid,uuid) to service_role;
grant execute on function public.save_lucky_box_config(uuid,uuid,boolean,boolean,text,text,text,text) to service_role;
grant execute on function public.save_lucky_box_rate_version(uuid,uuid,integer,bigint,bigint,bigint,bigint,text,text,text) to service_role;
grant execute on function public.save_lucky_box_reward(uuid,uuid,bigint,boolean,timestamptz,timestamptz,bigint,integer,text) to service_role;
grant execute on function public.clone_lucky_box_rate_version(uuid,uuid,text) to service_role;
grant execute on function public.sync_lucky_box_rewards(uuid,uuid,text) to service_role;
grant execute on function public.publish_lucky_box_rate_version(uuid,uuid,text) to service_role;

notify pgrst, 'reload schema';
commit;

-- Kết quả mong đợi: Success. No rows returned
