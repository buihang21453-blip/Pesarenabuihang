"""Validation and presentation helpers for Lucky Box."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from . import repository

BOX_CODE = "lucky_box_pes_arena"
MAX_PREVIEW_ITERATIONS = 10000
DUPLICATE_POLICIES = {
    "pending": "Chưa chốt",
    "convert_zcoin": "Quy đổi thành Zcoin",
    "allow_quantity": "Cho phép tăng số lượng",
    "block_owned": "Không cho rơi vật phẩm đã sở hữu",
}
REWARD_TYPE_LABELS = {
    "zcoin": "Zcoin",
    "shop_item": "Vật phẩm Shop",
    "exclusive_item": "Độc quyền Lucky Box",
    "discount_coupon": "Phiếu giảm giá",
    "no_reward": "Không có phần thưởng",
}
RARITY_LABELS = {
    "common": "Phổ biến",
    "rare": "Hiếm",
    "epic": "Sử thi",
    "elite": "Tinh anh",
    "legendary": "Huyền thoại",
}
VIETNAM_TZ = timezone(timedelta(hours=7))


def configure(context):
    globals().update(context)
    repository.configure(context)


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _required_nonnegative_int(value, label):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{label} phải là số nguyên.")
    if parsed < 0:
        raise ValueError(f"{label} không được âm.")
    return parsed


def _optional_nonnegative_int(value, label):
    clean = str(value or "").strip()
    if clean == "":
        return None
    return _required_nonnegative_int(clean, label)


def _clean_reason(value):
    clean = str(value or "").strip()
    if len(clean) < 3:
        raise ValueError("Hãy nhập lý do thay đổi ít nhất 3 ký tự.")
    return clean[:500]


def _parse_datetime_local(value, label):
    clean = str(value or "").strip()
    if not clean:
        return None
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        raise ValueError(f"{label} không đúng định dạng.")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=VIETNAM_TZ)
    return parsed.astimezone(timezone.utc).isoformat()


def _datetime_local(value):
    clean = str(value or "").strip()
    if not clean:
        return ""
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(VIETNAM_TZ).strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return ""


def parse_iterations(value):
    iterations = _safe_int(value, 1000)
    if iterations < 1 or iterations > MAX_PREVIEW_ITERATIONS:
        raise ValueError(f"Số lượt mô phỏng phải từ 1 đến {MAX_PREVIEW_ITERATIONS}.")
    return iterations


def validate_request_id(value):
    clean = str(value or "").strip()
    if not clean or len(clean) > 120:
        raise ValueError("Mã chống mở trùng không hợp lệ. Hãy tải lại trang.")
    try:
        uuid.UUID(clean)
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Mã chống mở trùng không hợp lệ. Hãy tải lại trang.")
    return clean


def _select_admin_data(actor, selected_rate_version_id=None, include_archived=True):
    boxes = repository.list_boxes()
    selected_box = boxes[0] if boxes else None
    versions = repository.list_rate_versions(
        selected_box.get("id") if selected_box else None,
        include_archived=include_archived,
    )
    selected_id = str(selected_rate_version_id or "").strip()
    selected = next((row for row in versions if str(row.get("id")) == selected_id), None)
    if selected is None and versions:
        selected = next((row for row in versions if row.get("status") == "draft"), None) or versions[0]
        selected_id = str(selected.get("id"))
    rewards = repository.list_rewards(selected_id) if selected_id else []
    validation = repository.validate_rate_version(actor.get("id"), selected_id) if selected_id else None
    return boxes, selected_box, versions, selected, rewards, validation


def _decorate_reward(row):
    reward = dict(row or {})
    item = reward.get("shop_items") or {}
    asset_path = reward.get("asset_path") or item.get("image_path") or ""
    reward["item"] = item
    reward["type_label"] = REWARD_TYPE_LABELS.get(reward.get("reward_type"), reward.get("reward_type") or "-")
    reward["image_url"] = asset_url(asset_path) if asset_path else ""
    reward["starts_at_local"] = _datetime_local(reward.get("starts_at"))
    reward["ends_at_local"] = _datetime_local(reward.get("ends_at"))
    return reward


def build_admin_context(actor, selected_rate_version_id=None):
    boxes, selected_box, versions, selected, rewards, validation = _select_admin_data(
        actor, selected_rate_version_id, include_archived=True
    )
    decorated = [_decorate_reward(row) for row in rewards]
    groups = {
        "zcoin": [row for row in decorated if row.get("reward_type") == "zcoin"],
        "shop": [row for row in decorated if row.get("reward_type") in {"shop_item", "discount_coupon"}],
        "exclusive": [row for row in decorated if row.get("reward_type") == "exclusive_item"],
        "other": [row for row in decorated if row.get("reward_type") == "no_reward"],
    }
    active_version = next((row for row in versions if row.get("status") == "active"), None)
    member_openings = repository.list_admin_openings(50)
    member_history_summary = {
        "opening_count": len(member_openings),
        "member_count": len({str(row.get("user_id")) for row in member_openings if row.get("user_id")}),
        "zcoin_spent": sum(_safe_int(row.get("zcoin_cost"), 0) for row in member_openings),
    }
    return {
        "actor": actor,
        "boxes": boxes,
        "selected_box": selected_box,
        "rate_versions": versions,
        "selected_rate_version": selected,
        "active_rate_version": active_version,
        "rewards": decorated,
        "reward_groups": groups,
        "rate_validation": validation,
        "duplicate_policies": DUPLICATE_POLICIES,
        "member_openings": member_openings,
        "member_history_summary": member_history_summary,
        "audit_logs": repository.list_audit_logs(40),
        "max_preview_iterations": MAX_PREVIEW_ITERATIONS,
    }


def build_admin_preview_context(actor, selected_rate_version_id=None, result=None, error=None):
    boxes, selected_box, versions, selected, rewards, _validation = _select_admin_data(
        actor, selected_rate_version_id, include_archived=False
    )
    return {
        "actor": actor,
        "boxes": boxes,
        "selected_box": selected_box,
        "rate_versions": versions,
        "selected_rate_version": selected,
        "rewards": [_decorate_reward(row) for row in rewards],
        "preview_result": result,
        "preview_error": error,
        "max_preview_iterations": MAX_PREVIEW_ITERATIONS,
    }


def run_preview(actor, rate_version_id, iterations):
    clean_rate_id = str(rate_version_id or "").strip()
    if not clean_rate_id:
        raise ValueError("Chưa chọn phiên bản tỷ lệ Draft.")
    return repository.preview_rate_version(actor.get("id"), clean_rate_id, parse_iterations(iterations))



def _is_admin(actor):
    return bool(actor) and (
        actor.get("role") == "admin" or actor.get("admin_level") in {"owner", "admin"}
    )


def _is_reward_available(reward, now=None):
    if not reward.get("is_enabled") or _safe_int(reward.get("weight"), 0) <= 0:
        return False
    now = now or datetime.now(timezone.utc)
    starts_at = str(reward.get("starts_at") or "").strip()
    ends_at = str(reward.get("ends_at") or "").strip()
    try:
        if starts_at:
            start = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if start > now:
                return False
        if ends_at:
            end = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            if end <= now:
                return False
    except ValueError:
        return False
    issue_limit = reward.get("issue_limit")
    if issue_limit is not None and _safe_int(reward.get("issued_count"), 0) >= _safe_int(issue_limit, 0):
        return False
    return True


def _item_count_percentages(rate):
    weights = dict((rate or {}).get("item_count_weights") or {})
    parsed = {str(i): max(0, _safe_int(weights.get(str(i)), 0)) for i in range(4)}
    total = sum(parsed.values())
    return [
        {
            "count": i,
            "weight": parsed[str(i)],
            "percent": round((parsed[str(i)] * 100 / total), 2) if total else 0,
        }
        for i in range(4)
    ]


def _decorate_public_reward(row, group_totals=None):
    reward = _decorate_reward(row)
    reward["rarity_label"] = RARITY_LABELS.get(reward.get("rarity"), reward.get("rarity") or "-")
    reward["available"] = _is_reward_available(reward)
    if not reward.get("image_url"):
        if reward.get("reward_type") == "zcoin":
            reward["image_url"] = asset_url("zcoin-logo.webp")
        elif reward.get("reward_type") == "no_reward":
            reward["image_url"] = asset_url("luckybox/no-reward.webp")
    group_key = "item" if reward.get("counts_as_item") else "non_item"
    total = (group_totals or {}).get(group_key, 0)
    reward["group_key"] = group_key
    reward["group_percent"] = round((_safe_int(reward.get("weight"), 0) * 100 / total), 3) if total else 0
    return reward


def _decorate_opening_reward(row, reward_catalog=None):
    reward = dict(row or {})
    item = reward.get("shop_items") or {}
    source_code = reward.get("original_reward_code") or reward.get("reward_code") or ""
    catalog = (reward_catalog or {}).get(source_code) or (reward_catalog or {}).get(reward.get("reward_code")) or {}
    asset_path = catalog.get("asset_path") or item.get("image_path") or ""
    if asset_path:
        reward["image_url"] = asset_url(asset_path)
    elif reward.get("reward_type") == "zcoin":
        reward["image_url"] = asset_url("zcoin-logo.webp")
    elif reward.get("reward_type") == "no_reward":
        reward["image_url"] = asset_url("luckybox/no-reward.webp")
    else:
        reward["image_url"] = ""
    rarity = reward.get("reward_rarity") or reward.get("rarity")
    reward["reward_rarity"] = rarity
    reward["rarity_label"] = RARITY_LABELS.get(rarity, rarity or "-")
    return reward


def _build_reward_catalog(rewards):
    return {str(row.get("reward_code")): row for row in rewards if row.get("reward_code")}


def build_user_context(actor, admin_preview=False, selected_rate_version_id=None):
    box = repository.get_box_by_code(BOX_CODE)
    active_rate = repository.get_active_rate_version(box.get("id")) if box else None
    selected_rate = active_rate
    if admin_preview and _is_admin(actor) and box:
        versions = repository.list_rate_versions(box.get("id"), include_archived=False)
        selected_id = str(selected_rate_version_id or "").strip()
        selected_rate = next((row for row in versions if str(row.get("id")) == selected_id), None) or active_rate
        if selected_rate is None and versions:
            selected_rate = versions[0]
    rewards_raw = repository.list_rewards(selected_rate.get("id")) if selected_rate else []
    available = [row for row in rewards_raw if _is_reward_available(row)]
    totals = {
        "item": sum(_safe_int(row.get("weight"), 0) for row in available if row.get("counts_as_item")),
        "non_item": sum(_safe_int(row.get("weight"), 0) for row in available if not row.get("counts_as_item")),
    }
    rewards = [_decorate_public_reward(row, totals) for row in rewards_raw]
    preview_mode = bool(admin_preview and _is_admin(actor))
    # Giao diện người chơi luôn ẩn tỷ lệ, kể cả khi Admin đang xem Preview.
    # Admin vẫn xem/chỉnh tỷ lệ tại trang quản trị và trang mô phỏng Draft riêng.
    show_rates = False
    for reward in rewards:
        reward.pop("group_percent", None)
        reward.pop("weight", None)
    visible_rewards = [row for row in rewards if row.get("available")]
    reward_groups = {
        "zcoin": [row for row in visible_rewards if row.get("reward_type") == "zcoin"],
        "shop": [row for row in visible_rewards if row.get("reward_type") in {"shop_item", "discount_coupon"}],
        "exclusive": [row for row in visible_rewards if row.get("reward_type") == "exclusive_item"],
        "other": [row for row in visible_rewards if row.get("reward_type") == "no_reward"],
    }
    balance = _safe_int((actor or {}).get("zcoin_balance"), 0)
    price = _safe_int((selected_rate or {}).get("open_price_zcoin"), 0)
    is_live = bool(box and box.get("is_enabled") and active_rate and selected_rate and str(selected_rate.get("id")) == str(active_rate.get("id")))
    can_open = bool(
        (preview_mode and selected_rate)
        or (is_live and actor and actor.get("role") == "player" and price > 0 and balance >= price)
    )
    openings = repository.list_user_openings(actor.get("id"), 8) if actor and actor.get("id") else []
    return {
        "box": box,
        "active_rate": active_rate,
        "selected_rate": selected_rate,
        "rewards": rewards,
        "reward_groups": reward_groups,
        "item_count_odds": _item_count_percentages(selected_rate) if show_rates else [],
        "show_rates": show_rates,
        "open_price": price,
        "balance": balance,
        "can_open": can_open,
        "is_live": is_live,
        "preview_mode": preview_mode,
        "openings": openings,
        "request_id": str(uuid.uuid4()),
        "reward_catalog": {
            code: {
                "name": row.get("reward_name"),
                "image_url": row.get("image_url"),
                "rarity": row.get("rarity"),
                "rarity_label": row.get("rarity_label"),
            }
            for code, row in _build_reward_catalog(rewards).items()
        },
    }


def decorate_open_result(result, rate_version_id=None):
    payload = dict(result or {})
    opening_id = payload.get("opening_id")
    if opening_id:
        opening = repository.get_opening(opening_id)
        if opening:
            catalog_rows = repository.list_rewards(opening.get("rate_version_id")) if opening.get("rate_version_id") else []
            catalog = _build_reward_catalog([_decorate_public_reward(row) for row in catalog_rows])
            payload["rewards"] = [_decorate_opening_reward(row, catalog) for row in opening.get("rewards") or []]
            return payload
    rewards = repository.list_rewards(rate_version_id) if rate_version_id else []
    catalog = _build_reward_catalog([_decorate_public_reward(row) for row in rewards])
    payload["rewards"] = [_decorate_opening_reward(row, catalog) for row in payload.get("rewards") or []]
    return payload


def preview_open_for_admin(actor, rate_version_id):
    if not _is_admin(actor):
        raise ValueError("Bạn không có quyền quay thử giao diện người chơi.")
    clean_rate_id = str(rate_version_id or "").strip()
    if not clean_rate_id:
        raise ValueError("Chưa chọn phiên bản tỷ lệ để quay thử.")
    result = repository.preview_rate_version(actor.get("id"), clean_rate_id, 1)
    samples = result.get("sample_openings") or result.get("samples") or []
    sample = dict(samples[0]) if samples else {}
    sample["preview"] = True
    sample["balance_before"] = _safe_int(actor.get("zcoin_balance"), 0)
    sample["balance_after"] = sample["balance_before"]
    sample["zcoin_cost"] = 0
    sample["opening_id"] = None
    return decorate_open_result(sample, clean_rate_id)


def build_opening_detail(actor, opening_id):
    opening = repository.get_opening(opening_id)
    if not opening:
        return None
    if str(opening.get("user_id")) != str((actor or {}).get("id")) and not _is_admin(actor):
        raise PermissionError("Bạn không có quyền xem lượt mở này.")
    catalog_rows = repository.list_rewards(opening.get("rate_version_id")) if opening.get("rate_version_id") else []
    catalog = _build_reward_catalog([_decorate_public_reward(row) for row in catalog_rows])
    opening["rewards"] = [_decorate_opening_reward(row, catalog) for row in opening.get("rewards") or []]
    return opening

def save_box(actor, box_id, form):
    return repository.save_box_config(
        actor.get("id"),
        box_id,
        {
            "is_enabled": form.get("is_enabled") == "1",
            "no_reward_enabled": form.get("no_reward_enabled") == "1",
            "description": str(form.get("description") or "").strip(),
            "notification_title": str(form.get("notification_title") or "").strip(),
            "notification_template": str(form.get("notification_template") or "").strip(),
            "reason": _clean_reason(form.get("reason")),
        },
    )


def save_rate(actor, rate_version_id, form):
    duplicate_policy = str(form.get("duplicate_policy") or "").strip()
    if duplicate_policy not in DUPLICATE_POLICIES:
        raise ValueError("Cách xử lý vật phẩm trùng không hợp lệ.")
    return repository.save_rate_version(
        actor.get("id"),
        rate_version_id,
        {
            "open_price_zcoin": _required_nonnegative_int(form.get("open_price_zcoin"), "Giá mở hộp"),
            "weight_0": _required_nonnegative_int(form.get("weight_0"), "Trọng số 0 vật phẩm"),
            "weight_1": _required_nonnegative_int(form.get("weight_1"), "Trọng số 1 vật phẩm"),
            "weight_2": _required_nonnegative_int(form.get("weight_2"), "Trọng số 2 vật phẩm"),
            "weight_3": _required_nonnegative_int(form.get("weight_3"), "Trọng số 3 vật phẩm"),
            "duplicate_policy": duplicate_policy,
            "notes": str(form.get("notes") or "").strip(),
            "reason": _clean_reason(form.get("reason")),
        },
    )


def save_reward(actor, reward_id, form):
    starts_at = _parse_datetime_local(form.get("starts_at"), "Thời gian bắt đầu")
    ends_at = _parse_datetime_local(form.get("ends_at"), "Thời gian kết thúc")
    if starts_at and ends_at and starts_at >= ends_at:
        raise ValueError("Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc.")
    return repository.save_reward(
        actor.get("id"),
        reward_id,
        {
            "weight": _required_nonnegative_int(form.get("weight"), "Trọng số reward"),
            "is_enabled": form.get("is_enabled") == "1",
            "starts_at": starts_at,
            "ends_at": ends_at,
            "issue_limit": _optional_nonnegative_int(form.get("issue_limit"), "Giới hạn phát hành"),
            "duplicate_zcoin": _optional_nonnegative_int(form.get("duplicate_zcoin"), "Zcoin bồi hoàn"),
            "reason": _clean_reason(form.get("reason")),
        },
    )


def clone_rate(actor, rate_version_id, reason):
    return repository.clone_rate_version(actor.get("id"), rate_version_id, _clean_reason(reason))


def sync_rewards(actor, rate_version_id, reason):
    return repository.sync_rewards(actor.get("id"), rate_version_id, _clean_reason(reason))


def publish_rate(actor, rate_version_id, reason):
    return repository.publish_rate_version(actor.get("id"), rate_version_id, _clean_reason(reason))


def open_for_user(user, request_id, box_code=BOX_CODE):
    clean_key = validate_request_id(request_id)
    return decorate_open_result(repository.open_box(user.get("id"), box_code, clean_key))


def error_message(exc):
    text = str(exc or "")
    mapping = {
        "LUCKY_BOX_DISABLED": "Lucky Box hiện chưa được mở.",
        "LUCKY_BOX_NO_ACTIVE_RATE": "Lucky Box chưa có phiên bản tỷ lệ chính thức.",
        "LUCKY_BOX_INVALID_PRICE": "Giá mở Lucky Box chưa hợp lệ.",
        "LUCKY_BOX_DUPLICATE_POLICY_PENDING": "Cách xử lý vật phẩm trùng chưa được chốt.",
        "INSUFFICIENT_ZCOIN": "Bạn không đủ Zcoin để mở Lucky Box.",
        "LUCKY_BOX_REQUEST_CONFLICT": "Mã lượt mở đã được sử dụng cho yêu cầu khác.",
        "LUCKY_BOX_REWARD_POOL_INVALID": "Pool phần thưởng hiện không hợp lệ.",
        "LUCKY_BOX_DUPLICATE_ITEM": "Lượt mở gặp vật phẩm đã sở hữu nhưng chưa có quy tắc quy đổi.",
        "LUCKY_BOX_ADMIN_PERMISSION_DENIED": "Bạn không có quyền quản trị Lucky Box.",
        "LUCKY_BOX_RATE_NOT_DRAFT": "Chỉ phiên bản Draft mới được chỉnh sửa.",
        "LUCKY_BOX_CHANGE_REASON_REQUIRED": "Hãy nhập lý do thay đổi ít nhất 3 ký tự.",
        "LUCKY_BOX_PUBLISH_REASON_REQUIRED": "Hãy nhập lý do publish ít nhất 3 ký tự.",
        "LUCKY_BOX_RATE_INVALID": "Phiên bản Draft chưa hợp lệ. Hãy xử lý các lỗi kiểm tra trước khi publish.",
        "LUCKY_BOX_ACTIVE_RATE_INVALID": "Phiên bản Active hiện không hợp lệ nên chưa thể bật hộp.",
        "LUCKY_BOX_NOTIFICATION_TEMPLATE_INVALID": "Mẫu thông báo phải chứa {rewards}.",
        "LUCKY_BOX_NO_REWARD_NOT_APPROVED": "Chưa cho phép dùng kết quả “Chúc bạn may mắn lần sau”.",
        "LUCKY_BOX_REWARD_ITEM_INACTIVE": "Vật phẩm này đã ngừng hoạt động trong Shop.",
        "LUCKY_BOX_REWARD_TIME_INVALID": "Khoảng thời gian reward không hợp lệ.",
        "LUCKY_BOX_ISSUE_LIMIT_BELOW_ISSUED": "Giới hạn phát hành không thể thấp hơn số lượng đã phát.",
    }
    for code, message in mapping.items():
        if code in text:
            return message
    return "Không thể xử lý Lucky Box lúc này. Vui lòng kiểm tra lại dữ liệu."
