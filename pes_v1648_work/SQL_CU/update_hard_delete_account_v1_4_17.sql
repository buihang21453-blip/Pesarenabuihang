-- PES Arena V1.4.17 - Hard Delete Account / Keep Match History
-- Chạy 1 lần trong Supabase SQL Editor trước khi dùng nút Xóa tài khoản.

begin;

create table if not exists public.archived_player_identities (
    user_id uuid primary key,
    username text,
    display_name text not null default 'Player',
    avatar_url text,
    deleted_at timestamptz not null default now()
);

comment on table public.archived_player_identities is
'Chỉ lưu danh tính tối thiểu để hiển thị lịch sử trận sau khi tài khoản users bị xóa thật.';

-- matches là lịch sử bất biến. UUID người chơi được giữ lại dù hàng users đã bị xóa.
-- Gỡ FK từ matches -> users (nếu có), không xóa bất kỳ match nào.
do $$
declare r record;
begin
  if to_regclass('public.matches') is not null and to_regclass('public.users') is not null then
    for r in
      select conname
      from pg_constraint
      where contype = 'f'
        and conrelid = 'public.matches'::regclass
        and confrelid = 'public.users'::regclass
    loop
      execute format('alter table public.matches drop constraint if exists %I', r.conname);
    end loop;
  end if;
end $$;

create or replace function public.hard_delete_player_keep_match_history(p_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_user record;
    r record;
    v_sql text;
begin
    select * into v_user from public.users where id = p_user_id for update;
    if not found then
        return jsonb_build_object('ok', false, 'error', 'Không tìm thấy tài khoản.');
    end if;

    if coalesce(to_jsonb(v_user)->>'role', 'player') <> 'player' or coalesce(to_jsonb(v_user)->>'admin_level', 'none') <> 'none' then
        return jsonb_build_object('ok', false, 'error', 'Không được xóa tài khoản Admin.');
    end if;

    insert into public.archived_player_identities(
        user_id, username, display_name, avatar_url, deleted_at
    ) values (
        v_user.id,
        v_user.username,
        coalesce(nullif(v_user.display_name, ''), nullif(v_user.username, ''), 'Player'),
        to_jsonb(v_user)->>'avatar_url',
        now()
    )
    on conflict (user_id) do update set
        username = excluded.username,
        display_name = excluded.display_name,
        avatar_url = excluded.avatar_url,
        deleted_at = excluded.deleted_at;

    -- Chỉ giữ public.matches và snapshot BXH (snapshot là JSON độc lập).
    -- Với mọi bảng khác có FK trực tiếp tới users, xóa dữ liệu của user trước
    -- để không bị RESTRICT và để tài khoản biến mất hoàn toàn khỏi hệ thống.
    for r in
      select distinct
        n.nspname as schema_name,
        c.relname as table_name,
        a.attname as column_name
      from pg_constraint fk
      join pg_class c on c.oid = fk.conrelid
      join pg_namespace n on n.oid = c.relnamespace
      join unnest(fk.conkey) with ordinality ck(attnum, ord) on true
      join pg_attribute a on a.attrelid = fk.conrelid and a.attnum = ck.attnum
      where fk.contype = 'f'
        and fk.confrelid = 'public.users'::regclass
        and n.nspname = 'public'
        and c.relname not in ('matches', 'users', 'archived_player_identities')
    loop
      v_sql := format('delete from %I.%I where %I = $1', r.schema_name, r.table_name, r.column_name);
      execute v_sql using p_user_id;
    end loop;

    -- Xóa chat của các phòng liên quan trước khi xóa phòng. Chỉ lịch sử matches được giữ.
    if to_regclass('public.chat_messages') is not null and to_regclass('public.match_rooms') is not null then
      delete from public.chat_messages
      where room_id in (
        select id from public.match_rooms
        where host_user_id = p_user_id or guest_user_id = p_user_id
      );
    end if;

    -- Một số bảng cũ có thể không khai báo FK nhưng vẫn chứa user id.
    if to_regclass('public.match_invites') is not null then
      delete from public.match_invites where from_user_id = p_user_id or to_user_id = p_user_id;
    end if;
    if to_regclass('public.match_rooms') is not null then
      delete from public.match_rooms where host_user_id = p_user_id or guest_user_id = p_user_id;
    end if;
    if to_regclass('public.user_devices') is not null then
      delete from public.user_devices where user_id = p_user_id;
    end if;

    delete from public.users where id = p_user_id;
    if found then
        return jsonb_build_object('ok', true, 'user_id', p_user_id);
    end if;
    raise exception 'Không thể xóa users row %', p_user_id;
end;
$$;

revoke all on function public.hard_delete_player_keep_match_history(uuid) from public;
grant execute on function public.hard_delete_player_keep_match_history(uuid) to service_role;

-- Chuyển các tài khoản đã xóa mềm từ V1.4.16 sang xóa thật.
-- Chỉ áp dụng role=player; Admin không bao giờ bị đụng tới.
do $$
declare r record;
begin
  for r in
    select id from public.users
    where coalesce(account_status, 'approved') = 'deleted'
      and coalesce(role, 'player') = 'player'
  loop
    perform public.hard_delete_player_keep_match_history(r.id);
  end loop;
end $$;

commit;
