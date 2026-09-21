"""Nghiệp vụ Gift Code: chuẩn hóa, tạo mã, hiển thị và đổi mã."""

import re
import secrets
from datetime import datetime, timedelta, timezone

from . import repository

EXPORTED_NAMES = (
    "normalize_gift_code",
    "list_gift_codes",
    "create_gift_code",
    "toggle_gift_code",
    "redeem_gift_code",
)

_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{3,31}$")
_VN_TZ = timezone(timedelta(hours=7))


def configure(context):
    globals().update(context)


def _safe_int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _parse_iso(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def normalize_gift_code(value):
    return re.sub(r"\s+", "", str(value or "").strip().upper())


def _generate_code():
    return "PES-" + secrets.token_hex(4).upper()


def _status_for(row, now=None):
    now = now or datetime.now(timezone.utc)
    starts = _parse_iso(row.get("starts_at"))
    expires = _parse_iso(row.get("expires_at"))
    used = max(0, _safe_int(row.get("redemption_count")))
    maximum = max(1, _safe_int(row.get("max_redemptions"), 1))
    active = bool(row.get("is_active", True))
    if not active:
        return "disabled", "Đã tắt"
    if starts and starts > now:
        return "scheduled", "Chưa bắt đầu"
    if expires and expires <= now:
        return "expired", "Đã hết hạn"
    if used >= maximum:
        return "depleted", "Đã hết lượt"
    return "active", "Đang hoạt động"


def list_gift_codes(limit=100):
    rows = repository.list_codes(limit=limit)
    now = datetime.now(timezone.utc)
    result = []
    for raw in rows:
        item = dict(raw)
        item["reward_amount"] = max(0, _safe_int(item.get("reward_amount")))
        item["redemption_count"] = max(0, _safe_int(item.get("redemption_count")))
        item["max_redemptions"] = max(1, _safe_int(item.get("max_redemptions"), 1))
        item["per_user_limit"] = max(1, _safe_int(item.get("per_user_limit"), 1))
        item["remaining"] = max(0, item["max_redemptions"] - item["redemption_count"])
        item["status"], item["status_label"] = _status_for(item, now=now)
        result.append(item)
    return result


def _parse_vn_datetime(value, fallback):
    raw = str(value or "").strip()
    if not raw:
        return fallback
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_VN_TZ)
        return parsed.astimezone(timezone.utc)
    except Exception as exc:
        raise ValueError("Thời gian bắt đầu không hợp lệ.") from exc


def create_gift_code(actor, form):
    code = normalize_gift_code(form.get("code")) or _generate_code()
    if not _CODE_PATTERN.fullmatch(code):
        raise ValueError("Gift Code phải có 4–32 ký tự, chỉ gồm chữ, số, gạch ngang hoặc gạch dưới.")

    reward_amount = _safe_int(form.get("reward_amount"))
    max_redemptions = _safe_int(form.get("max_redemptions"))
    per_user_limit = _safe_int(form.get("per_user_limit"), 1)
    duration_minutes = _safe_int(form.get("duration_minutes"), 120)
    note = str(form.get("note") or "").strip()
    target_user_id = str(form.get("target_user_id") or "").strip() or None

    if not is_admin_user(actor):
        raise ValueError("Tài khoản không có quyền tạo Gift Code.")
    max_reward = 50_000
    max_total_redemptions = 100_000
    if reward_amount < 1 or reward_amount > max_reward:
        raise ValueError(f"Giá trị mỗi lượt phải từ 1 đến {format_zcoin(max_reward)} Zcoin.")
    if max_redemptions < 1 or max_redemptions > max_total_redemptions:
        raise ValueError("Giới hạn lượt sử dụng không hợp lệ.")
    if per_user_limit < 1 or per_user_limit > 10:
        raise ValueError("Mỗi tài khoản chỉ được phép dùng từ 1 đến 10 lần.")
    if duration_minutes < 5 or duration_minutes > 43_200:
        raise ValueError("Thời hạn Gift Code phải từ 5 phút đến 30 ngày.")
    if len(note) > 250:
        raise ValueError("Ghi chú tối đa 250 ký tự.")

    target_user = None
    if target_user_id:
        target_user = get_user(target_user_id)
        if not target_user or target_user.get("role") != "player":
            raise ValueError("Không tìm thấy người chơi nhận Gift Code.")
        max_redemptions = 1
        per_user_limit = 1

    start_utc = _parse_vn_datetime(form.get("starts_at"), datetime.now(timezone.utc))
    expires_utc = start_utc + timedelta(minutes=duration_minutes)
    now_iso_value = now_iso()
    payload = {
        "code": code,
        "reward_amount": reward_amount,
        "starts_at": start_utc.isoformat(),
        "expires_at": expires_utc.isoformat(),
        "max_redemptions": max_redemptions,
        "redemption_count": 0,
        "per_user_limit": per_user_limit,
        "is_active": True,
        "created_by": actor.get("id"),
        "created_by_name": actor.get("display_name") or actor.get("username") or "Admin",
        "note": note or None,
        "metadata": {
            "app_version": APP_VERSION,
            "private_gift": bool(target_user_id),
            "target_user_id": target_user_id,
            "target_username": (target_user or {}).get("username") if target_user else None,
            "target_display_name": ((target_user or {}).get("display_name") or (target_user or {}).get("username")) if target_user else None,
        },
        "created_at": now_iso_value,
        "updated_at": now_iso_value,
    }
    return repository.create_code(payload)


def toggle_gift_code(code_id, enabled):
    return repository.update_code(
        code_id,
        {"is_active": bool(enabled), "updated_at": now_iso()},
    )


def redeem_gift_code(user_id, code, request_key):
    clean_code = normalize_gift_code(code)
    if not _CODE_PATTERN.fullmatch(clean_code):
        raise ValueError("Gift Code không hợp lệ.")
    clean_key = str(request_key or "").strip()
    if not clean_key or len(clean_key) > 120:
        raise ValueError("Phiên đổi Gift Code không hợp lệ. Hãy tải lại trang.")
    payload = repository.redeem_code(user_id, clean_code, clean_key)
    if not payload:
        raise RuntimeError("Supabase không trả về kết quả đổi Gift Code.")
    payload["reward_amount"] = max(0, _safe_int(payload.get("reward_amount")))
    payload["balance_after"] = max(0, _safe_int(payload.get("balance_after")))
    payload["duplicate"] = bool(payload.get("duplicate"))
    payload["code"] = clean_code
    return payload
