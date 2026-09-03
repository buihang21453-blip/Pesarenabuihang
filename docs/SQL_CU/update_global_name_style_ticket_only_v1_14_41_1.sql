-- PES Arena V1.14.41.1
-- Đổi tên hiển thị chỉ bằng Vé đổi tên; không còn lượt miễn phí.

begin;

create or replace function public.change_display_name_with_ticket(
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
    v_ticket_remaining integer:=0;
begin
    v_name:=regexp_replace(btrim(coalesce(p_new_display_name,'')),'\s+',' ','g');
    if char_length(v_name)<2 or char_length(v_name)>40 then
        raise exception 'INVALID_DISPLAY_NAME';
    end if;

    if exists(
        select 1 from public.users
        where id<>p_user_id
          and lower(btrim(coalesce(display_name,'')))=lower(v_name)
    ) then
        raise exception 'DISPLAY_NAME_DUPLICATE';
    end if;

    select * into v_user
    from public.users
    where id=p_user_id
    for update;
    if not found then raise exception 'SHOP_USER_NOT_FOUND'; end if;
    if lower(btrim(coalesce(v_user.display_name,'')))=lower(v_name) then
        raise exception 'DISPLAY_NAME_UNCHANGED';
    end if;

    select ui.* into v_ticket
    from public.user_inventory ui
    join public.shop_items si on si.id=ui.item_id
    where ui.user_id=p_user_id
      and ui.quantity>0
      and si.code='display_name_change_ticket'
    order by ui.acquired_at
    limit 1
    for update of ui;
    if not found then
        raise exception 'DISPLAY_NAME_CHANGE_TICKET_REQUIRED';
    end if;

    if v_ticket.quantity<=1 then
        delete from public.user_inventory where id=v_ticket.id;
        v_ticket_remaining:=0;
    else
        update public.user_inventory
        set quantity=quantity-1,updated_at=now()
        where id=v_ticket.id;
        v_ticket_remaining:=v_ticket.quantity-1;
    end if;

    update public.users
    set display_name=v_name,
        display_name_changed_at=now()
    where id=p_user_id;

    return jsonb_build_object(
        'display_name',v_name,
        'used_ticket',true,
        'free_changes_remaining',0,
        'ticket_remaining',v_ticket_remaining
    );
end
$$;

notify pgrst,'reload schema';
commit;
