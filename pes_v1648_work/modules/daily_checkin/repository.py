"""Truy vấn dữ liệu điểm danh, tách khỏi route và template."""


def configure(context):
    globals().update(context)


def list_recent_checkins(user_id, limit=14):
    safe_limit = max(1, min(int(limit or 14), 31))
    result = execute_query(
        db.table("daily_checkins")
        .select("id,user_id,checkin_date,streak_day,reward_amount,balance_after,created_at,metadata")
        .eq("user_id", str(user_id))
        .order("checkin_date", desc=True)
        .limit(safe_limit),
        "daily_checkin_recent",
        attempts=3,
    )
    return [dict(row) for row in (result.data or [])]


def claim_daily_checkin(user_id, request_key):
    result = execute_query(
        db.rpc(
            "claim_daily_checkin",
            {
                "p_user_id": str(user_id),
                "p_request_key": str(request_key or "").strip(),
            },
        ),
        "claim_daily_checkin_rpc",
        attempts=2,
    )
    data = result.data
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}
