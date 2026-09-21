"""Repository Gift Code: truy vấn và RPC, không chứa logic giao diện."""


def configure(context):
    globals().update(context)


def list_codes(limit=100):
    safe_limit = max(1, min(int(limit or 100), 300))
    result = execute_query(
        db.table("gift_codes")
        .select(
            "id,code,reward_amount,starts_at,expires_at,max_redemptions,"
            "redemption_count,per_user_limit,is_active,created_by,created_by_name,"
            "note,metadata,created_at,updated_at"
        )
        .order("created_at", desc=True)
        .limit(safe_limit),
        "gift_codes_list",
        attempts=3,
    )
    return [dict(row) for row in (result.data or [])]


def create_code(payload):
    result = execute_query(
        db.table("gift_codes").insert(payload),
        "gift_code_create",
        attempts=2,
    )
    rows = result.data or []
    return dict(rows[0]) if rows else dict(payload)


def update_code(code_id, payload):
    result = execute_query(
        db.table("gift_codes").update(payload).eq("id", str(code_id)),
        "gift_code_update",
        attempts=2,
    )
    rows = result.data or []
    return dict(rows[0]) if rows else {}


def redeem_code(user_id, code, request_key):
    result = execute_query(
        db.rpc(
            "redeem_zcoin_gift_code",
            {
                "p_user_id": str(user_id),
                "p_code": str(code or "").strip(),
                "p_request_key": str(request_key or "").strip(),
            },
        ),
        "redeem_zcoin_gift_code_rpc",
        attempts=2,
    )
    data = result.data
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}
