"""Supabase repository for Lucky Box backend and Admin management."""


def configure(context):
    globals().update(context)


def _payload(data):
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}


def _rpc(name, params, label):
    require_db()
    result = execute_query(db.rpc(name, params), label, attempts=2)
    payload = _payload(result.data)
    if not payload:
        raise RuntimeError(f"Supabase không trả về dữ liệu từ {name}.")
    return payload



def get_box_by_code(box_code):
    require_db()
    result = execute_query(
        db.table("lucky_boxes").select("*").eq("code", str(box_code)).limit(1),
        "luckybox_get_box",
        attempts=2,
    )
    return dict(result.data[0]) if result.data else None


def get_active_rate_version(box_id):
    require_db()
    result = execute_query(
        db.table("lucky_box_rate_versions")
        .select("*")
        .eq("box_id", str(box_id))
        .eq("status", "active")
        .limit(1),
        "luckybox_get_active_rate",
        attempts=2,
    )
    return dict(result.data[0]) if result.data else None

def list_boxes():
    require_db()
    result = execute_query(
        db.table("lucky_boxes").select("*").order("created_at"),
        "luckybox_list_boxes",
        attempts=2,
    )
    return [dict(row) for row in (result.data or [])]


def list_rate_versions(box_id=None, include_archived=False):
    require_db()
    query = db.table("lucky_box_rate_versions").select("*").order("version_number", desc=True)
    if box_id:
        query = query.eq("box_id", str(box_id))
    if not include_archived:
        query = query.neq("status", "archived")
    result = execute_query(query, "luckybox_list_rate_versions", attempts=2)
    return [dict(row) for row in (result.data or [])]


def list_rewards(rate_version_id):
    require_db()
    result = execute_query(
        db.table("lucky_box_rewards")
        .select("*,shop_items(id,code,name,item_type,category,rarity,image_path,is_unique,is_consumable,is_active,is_listed,price_zcoin)")
        .eq("rate_version_id", str(rate_version_id))
        .order("counts_as_item", desc=True)
        .order("sort_order")
        .order("reward_code"),
        "luckybox_list_rewards",
        attempts=2,
    )
    return [dict(row) for row in (result.data or [])]


def list_audit_logs(limit=40):
    require_db()
    safe_limit = max(1, min(int(limit or 40), 100))
    result = execute_query(
        db.table("lucky_box_admin_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(safe_limit),
        "luckybox_audit_logs",
        attempts=2,
    )
    rows = [dict(row) for row in (result.data or [])]
    actor_ids = sorted({str(row.get("actor_user_id")) for row in rows if row.get("actor_user_id")})
    actors = {}
    if actor_ids:
        actor_result = execute_query(
            db.table("users").select("id,username,display_name").in_("id", actor_ids),
            "luckybox_audit_actors",
            attempts=2,
        )
        actors = {str(row.get("id")): dict(row) for row in (actor_result.data or [])}
    for row in rows:
        row["actor"] = actors.get(str(row.get("actor_user_id")))
    return rows


def preview_rate_version(actor_user_id, rate_version_id, iterations):
    return _rpc(
        "preview_lucky_box_rate_version",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_rate_version_id": str(rate_version_id),
            "p_iterations": int(iterations),
        },
        "luckybox_preview_rate_version_rpc",
    )


def validate_rate_version(actor_user_id, rate_version_id):
    return _rpc(
        "validate_lucky_box_rate_version",
        {"p_actor_user_id": str(actor_user_id), "p_rate_version_id": str(rate_version_id)},
        "luckybox_validate_rate_rpc",
    )


def save_box_config(actor_user_id, box_id, payload):
    return _rpc(
        "save_lucky_box_config",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_box_id": str(box_id),
            "p_is_enabled": bool(payload.get("is_enabled")),
            "p_no_reward_enabled": bool(payload.get("no_reward_enabled")),
            "p_description": payload.get("description") or "",
            "p_notification_title": payload.get("notification_title") or "",
            "p_notification_template": payload.get("notification_template") or "",
            "p_reason": payload.get("reason") or "",
        },
        "luckybox_save_box_config_rpc",
    )


def save_rate_version(actor_user_id, rate_version_id, payload):
    return _rpc(
        "save_lucky_box_rate_version",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_rate_version_id": str(rate_version_id),
            "p_open_price_zcoin": int(payload["open_price_zcoin"]),
            "p_weight_0": int(payload["weight_0"]),
            "p_weight_1": int(payload["weight_1"]),
            "p_weight_2": int(payload["weight_2"]),
            "p_weight_3": int(payload["weight_3"]),
            "p_duplicate_policy": payload["duplicate_policy"],
            "p_notes": payload.get("notes") or "",
            "p_reason": payload.get("reason") or "",
        },
        "luckybox_save_rate_version_rpc",
    )


def save_reward(actor_user_id, reward_id, payload):
    return _rpc(
        "save_lucky_box_reward",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_reward_id": str(reward_id),
            "p_weight": int(payload["weight"]),
            "p_is_enabled": bool(payload.get("is_enabled")),
            "p_starts_at": payload.get("starts_at"),
            "p_ends_at": payload.get("ends_at"),
            "p_issue_limit": payload.get("issue_limit"),
            "p_duplicate_zcoin": payload.get("duplicate_zcoin"),
            "p_reason": payload.get("reason") or "",
        },
        "luckybox_save_reward_rpc",
    )


def clone_rate_version(actor_user_id, source_rate_version_id, reason):
    return _rpc(
        "clone_lucky_box_rate_version",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_source_rate_version_id": str(source_rate_version_id),
            "p_reason": reason or "",
        },
        "luckybox_clone_rate_rpc",
    )


def sync_rewards(actor_user_id, rate_version_id, reason):
    return _rpc(
        "sync_lucky_box_rewards",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_rate_version_id": str(rate_version_id),
            "p_reason": reason or "",
        },
        "luckybox_sync_rewards_rpc",
    )


def publish_rate_version(actor_user_id, rate_version_id, reason):
    return _rpc(
        "publish_lucky_box_rate_version",
        {
            "p_actor_user_id": str(actor_user_id),
            "p_rate_version_id": str(rate_version_id),
            "p_reason": reason or "",
        },
        "luckybox_publish_rate_rpc",
    )


def open_box(user_id, box_code, request_id):
    return _rpc(
        "open_lucky_box",
        {"p_user_id": str(user_id), "p_box_code": str(box_code), "p_request_id": str(request_id)},
        "luckybox_open_rpc",
    )



def list_admin_openings(limit=50):
    """Return latest real Lucky Box openings for the Admin page.

    Uses three small queries instead of a deep PostgREST join so the page keeps
    working even when relationship names differ between environments.
    """
    require_db()
    safe_limit = max(1, min(int(limit or 50), 100))
    result = execute_query(
        db.table("lucky_box_openings")
        .select("id,request_id,user_id,box_code,rate_version,zcoin_cost,balance_before,balance_after,opened_at,status,metadata")
        .order("opened_at", desc=True)
        .limit(safe_limit),
        "luckybox_admin_member_history",
        attempts=2,
    )
    rows = [dict(row) for row in (result.data or [])]
    if not rows:
        return []

    user_ids = sorted({str(row.get("user_id")) for row in rows if row.get("user_id")})
    users = {}
    if user_ids:
        user_result = execute_query(
            db.table("users").select("id,username,display_name").in_("id", user_ids),
            "luckybox_admin_member_history_users",
            attempts=2,
        )
        users = {str(row.get("id")): dict(row) for row in (user_result.data or [])}

    opening_ids = [str(row.get("id")) for row in rows if row.get("id")]
    rewards_by_opening = {opening_id: [] for opening_id in opening_ids}
    if opening_ids:
        reward_result = execute_query(
            db.table("lucky_box_opening_rewards")
            .select("opening_id,reward_slot,reward_type,reward_code,reward_name,reward_amount,reward_rarity,original_reward_code,duplicate_conversion")
            .in_("opening_id", opening_ids)
            .order("reward_slot"),
            "luckybox_admin_member_history_rewards",
            attempts=2,
        )
        for reward in (reward_result.data or []):
            reward_row = dict(reward)
            rewards_by_opening.setdefault(str(reward_row.get("opening_id")), []).append(reward_row)

    for row in rows:
        row["user"] = users.get(str(row.get("user_id")))
        row["rewards"] = sorted(
            rewards_by_opening.get(str(row.get("id")), []),
            key=lambda item: int(item.get("reward_slot") or 0),
        )
    return rows


def list_user_openings(user_id, limit=30):
    require_db()
    safe_limit = max(1, min(int(limit or 30), 100))
    result = execute_query(
        db.table("lucky_box_openings")
        .select("id,request_id,box_code,rate_version,zcoin_cost,balance_before,balance_after,opened_at,status,metadata")
        .eq("user_id", str(user_id))
        .order("opened_at", desc=True)
        .limit(safe_limit),
        "luckybox_user_history",
        attempts=2,
    )
    return [dict(row) for row in (result.data or [])]


def get_opening(opening_id):
    require_db()
    result = execute_query(
        db.table("lucky_box_openings").select("*").eq("id", str(opening_id)).limit(1),
        "luckybox_get_opening",
        attempts=2,
    )
    opening = dict(result.data[0]) if result.data else None
    if not opening:
        return None
    rewards = execute_query(
        db.table("lucky_box_opening_rewards")
        .select("*,shop_items(id,code,name,item_type,category,rarity,image_path,is_unique,is_consumable)")
        .eq("opening_id", str(opening_id))
        .order("reward_slot"),
        "luckybox_get_opening_rewards",
        attempts=2,
    )
    opening["rewards"] = [dict(row) for row in (rewards.data or [])]
    return opening
