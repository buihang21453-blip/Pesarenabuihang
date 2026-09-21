"""Dịch vụ ví Zcoin giai đoạn 1, tương thích schema Zcoin hiện có.

Database hiện dùng bảng ``zcoin_transactions`` với các cột:
``id, user_id, amount, balance_after, transaction_type, source, description,
metadata, created_at``. Các thông tin bổ sung như số dư trước, tên Admin và khóa
chống gửi trùng được lưu trong ``metadata`` để không phải thay đổi schema cũ.
"""

EXPORTED_NAMES = (
    "format_zcoin",
    "list_zcoin_transactions",
    "adjust_zcoin_balance",
    "build_zcoin_stats",
)


def configure(context):
    globals().update(context)


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_dict(value):
    return dict(value) if isinstance(value, dict) else {}


def format_zcoin(value):
    """Định dạng 12000 thành 12.000 theo cách hiển thị trong app."""
    return f"{max(0, _safe_int(value)):,}".replace(",", ".")


def _load_user_labels(user_ids):
    """Tải tên hiển thị theo một truy vấn gọn; lỗi phụ không làm sập ví."""
    ids = sorted({str(item) for item in (user_ids or []) if item})
    if not ids:
        return {}
    try:
        result = execute_query(
            db.table("users").select("id,username,display_name").in_("id", ids),
            "zcoin_user_labels",
            attempts=2,
        )
    except Exception:
        return {}
    labels = {}
    for row in result.data or []:
        labels[str(row.get("id"))] = (
            row.get("display_name") or row.get("username") or "Người chơi"
        )
    return labels


def list_zcoin_transactions(user_id=None, limit=50):
    """Tải lịch sử Zcoin từ schema đang có, có thể lọc theo người chơi."""
    require_db()
    safe_limit = max(1, min(_safe_int(limit, 50), 200))
    query = (
        db.table("zcoin_transactions")
        .select(
            "id,user_id,amount,balance_after,transaction_type,source,"
            "description,metadata,created_at"
        )
        .order("created_at", desc=True)
        .limit(safe_limit)
    )
    if user_id:
        query = query.eq("user_id", str(user_id))
    result = execute_query(query, "list_zcoin_transactions", attempts=3)

    raw_rows = [dict(row) for row in (result.data or [])]
    related_ids = set()
    for raw in raw_rows:
        related_ids.add(str(raw.get("user_id") or ""))
        metadata = _safe_dict(raw.get("metadata"))
        actor_id = metadata.get("actor_user_id")
        if actor_id:
            related_ids.add(str(actor_id))
    labels = _load_user_labels(related_ids)

    rows = []
    for raw in raw_rows:
        metadata = _safe_dict(raw.get("metadata"))
        amount = _safe_int(raw.get("amount"))
        balance_after = max(0, _safe_int(raw.get("balance_after")))
        balance_before = metadata.get("balance_before")
        if balance_before is None:
            balance_before = balance_after - amount
        balance_before = max(0, _safe_int(balance_before))

        item = dict(raw)
        item["metadata"] = metadata
        item["amount"] = amount
        item["balance_before"] = balance_before
        item["balance_after"] = balance_after
        item["reason"] = str(raw.get("description") or metadata.get("reason") or "Giao dịch Zcoin")
        item["user_name"] = (
            metadata.get("user_name")
            or labels.get(str(raw.get("user_id") or ""))
            or "Người chơi"
        )
        actor_id = metadata.get("actor_user_id")
        item["actor_name"] = (
            metadata.get("actor_name")
            or labels.get(str(actor_id or ""))
            or ""
        )
        item["is_credit"] = amount > 0
        item["amount_display"] = format_zcoin(abs(amount))
        item["balance_before_display"] = format_zcoin(balance_before)
        item["balance_after_display"] = format_zcoin(balance_after)
        rows.append(item)
    return rows


def _normalize_rpc_payload(data):
    if isinstance(data, list):
        return dict(data[0]) if data else {}
    return dict(data) if isinstance(data, dict) else {}


def adjust_zcoin_balance(user_id, amount, reason, actor_user_id, idempotency_key):
    """Cộng/trừ Zcoin nguyên tử qua RPC tương thích database cũ."""
    require_db()
    delta = _safe_int(amount)
    clean_reason = str(reason or "").strip()
    clean_key = str(idempotency_key or "").strip()
    if delta == 0:
        raise ValueError("Số Zcoin điều chỉnh phải lớn hơn 0.")
    if len(clean_reason) < 3 or len(clean_reason) > 300:
        raise ValueError("Lý do phải có từ 3 đến 300 ký tự.")
    if not clean_key or len(clean_key) > 120:
        raise ValueError("Mã chống gửi trùng không hợp lệ. Hãy tải lại trang Admin.")

    result = execute_query(
        db.rpc(
            "adjust_zcoin_balance",
            {
                "p_user_id": str(user_id),
                "p_amount": delta,
                "p_reason": clean_reason,
                "p_actor_user_id": str(actor_user_id),
                "p_idempotency_key": clean_key,
            },
        ),
        "adjust_zcoin_balance_rpc",
        attempts=2,
    )
    payload = _normalize_rpc_payload(result.data)
    if not payload:
        raise RuntimeError("Supabase không trả về kết quả điều chỉnh Zcoin.")
    payload["amount"] = _safe_int(payload.get("amount"), delta)
    payload["balance_before"] = max(0, _safe_int(payload.get("balance_before")))
    payload["balance_after"] = max(0, _safe_int(payload.get("balance_after")))
    return payload


def build_zcoin_stats(users, transactions=None):
    """Tạo thống kê nhẹ từ dữ liệu đã tải, không phát sinh truy vấn dư thừa."""
    user_rows = list(users or [])
    transaction_rows = list(transactions or [])
    balances = [max(0, _safe_int(item.get("zcoin_balance"))) for item in user_rows]
    issued = sum(max(0, _safe_int(item.get("amount"))) for item in transaction_rows)
    withdrawn = sum(abs(min(0, _safe_int(item.get("amount")))) for item in transaction_rows)
    return {
        "circulating": sum(balances),
        "wallet_count": sum(1 for balance in balances if balance > 0),
        "highest_balance": max(balances or [0]),
        "recent_issued": issued,
        "recent_withdrawn": withdrawn,
    }
