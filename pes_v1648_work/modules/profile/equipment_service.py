"""Đọc trạng thái trang bị hồ sơ từ Shop/Kho đồ Giai đoạn 3.

Nếu migration Shop chưa được chạy, dịch vụ tự quay về dữ liệu
``users.equipped_cosmetics`` cũ để trang Hồ sơ vẫn hoạt động bình thường.
"""

PROFILE_EQUIPMENT_SLOTS = (
    "avatar_frame",
    "profile_banner",
    "profile_badge",
    "name_style",
    "profile_card_theme",
)


def configure(context):
    globals().update(context)


def _safe_dict(value):
    return dict(value) if isinstance(value, dict) else {}




def _cache_keys(user_id):
    normalized = str(user_id or "").replace("-", "_")
    return f"_rz_profile_equipment_{normalized}", f"profile_equipment:{user_id}"


PUBLIC_PROFILE_SLOTS = ("avatar_frame", "name_style", "profile_badge")
PUBLIC_MAP_REQUEST_KEY = "_rz_profile_public_equipment_maps"
PUBLIC_MAP_TTL_KEY = "profile_public_equipment_maps"


def invalidate_equipment_cache(user_id):
    request_key, ttl_key = _cache_keys(user_id)
    try:
        cache_delete(request_key)
        cache_delete(PUBLIC_MAP_REQUEST_KEY)
        # Dọn các khóa cũ để hotfix tương thích ngay với instance đang warm.
        cache_delete("_rz_profile_avatar_frame_map")
        cache_delete("_rz_profile_name_style_map")
    except Exception:
        pass
    try:
        ttl_cache_delete(
            ttl_key,
            PUBLIC_MAP_TTL_KEY,
            "profile_avatar_frame_map",
            "profile_name_style_map",
        )
    except Exception:
        pass


def _fallback_state(player):
    player = dict(player or {})
    raw = _safe_dict(player.get("equipped_cosmetics"))
    return {slot: (dict(raw.get(slot)) if isinstance(raw.get(slot), dict) else None) for slot in PROFILE_EQUIPMENT_SLOTS}


def _decorate_item(item):
    item = dict(item or {})
    item["metadata"] = _safe_dict(item.get("metadata"))
    image_path = item.get("image_path")
    preview_path = item.get("preview_path") or image_path
    item["image_url"] = asset_url(image_path) if image_path else None
    item["preview_url"] = asset_url(preview_path) if preview_path else item.get("image_url")
    return item


def _build_public_equipment_maps(players=None):
    """Đọc khung Avatar và màu tên cho nhiều người bằng tối đa 2 truy vấn.

    Kết quả: ``{slot: {user_id: decorated_item}}``. Hai wrapper bên dưới
    dùng chung cache nên Players/BXH không phát sinh truy vấn theo từng user.
    """
    requested_ids = set()
    fallback = {slot: {} for slot in PUBLIC_PROFILE_SLOTS}
    for value in players or []:
        if isinstance(value, dict):
            user_id = value.get("id")
            raw = _safe_dict(value.get("equipped_cosmetics"))
            for slot in PUBLIC_PROFILE_SLOTS:
                legacy_item = raw.get(slot)
                if user_id and isinstance(legacy_item, dict):
                    fallback[slot][str(user_id)] = dict(legacy_item)
        else:
            user_id = value
        if user_id:
            requested_ids.add(str(user_id))

    try:
        cached = cache_get(PUBLIC_MAP_REQUEST_KEY)
        if cached is None:
            cached = ttl_cache_get(PUBLIC_MAP_TTL_KEY)
        if cached is None:
            equipment_result = execute_query(
                db.table("user_equipment")
                .select("user_id,item_id,inventory_id,equipped_at,slot")
                .in_("slot", list(PUBLIC_PROFILE_SLOTS)),
                "profile_public_equipment_rows",
                attempts=2,
            )
            equipment_rows = [dict(row) for row in (equipment_result.data or [])]
            item_ids = sorted({str(row.get("item_id")) for row in equipment_rows if row.get("item_id")})
            items_by_id = {}
            if item_ids:
                item_result = execute_query(
                    db.table("shop_items").select("*").in_("id", item_ids),
                    "profile_public_equipment_items",
                    attempts=2,
                )
                items_by_id = {
                    str(item.get("id")): _decorate_item(item)
                    for item in (item_result.data or [])
                }

            cached = {slot: {} for slot in PUBLIC_PROFILE_SLOTS}
            for equipment in equipment_rows:
                slot = str(equipment.get("slot") or "")
                item = items_by_id.get(str(equipment.get("item_id")))
                user_id = equipment.get("user_id")
                if slot not in cached or not item or not user_id:
                    continue
                decorated = dict(item)
                decorated["inventory_id"] = equipment.get("inventory_id")
                decorated["equipped_at"] = equipment.get("equipped_at")
                cached[slot][str(user_id)] = decorated
            ttl_cache_set(PUBLIC_MAP_TTL_KEY, cached, 15)
        cache_set(PUBLIC_MAP_REQUEST_KEY, cached)
    except Exception as exc:
        try:
            app.logger.debug("Public profile equipment map fallback: %s", exc)
        except Exception:
            pass
        cached = {slot: {} for slot in PUBLIC_PROFILE_SLOTS}

    result = {slot: dict(fallback.get(slot) or {}) for slot in PUBLIC_PROFILE_SLOTS}
    for slot in PUBLIC_PROFILE_SLOTS:
        result[slot].update((cached or {}).get(slot) or {})
        if requested_ids:
            result[slot] = {
                user_id: result[slot].get(user_id)
                for user_id in requested_ids
                if result[slot].get(user_id)
            }
    return result


def build_avatar_frame_map(players=None):
    return _build_public_equipment_maps(players).get("avatar_frame", {})


def build_name_style_map(players=None):
    return _build_public_equipment_maps(players).get("name_style", {})


def build_profile_badge_map(players=None):
    return _build_public_equipment_maps(players).get("profile_badge", {})

def build_equipment_state(player):
    """Trả về dict slot -> thông tin vật phẩm đang trang bị."""
    player = dict(player or {})
    user_id = player.get("id")
    fallback = _fallback_state(player)
    if not user_id:
        return fallback

    request_key, ttl_key = _cache_keys(user_id)
    try:
        cached = cache_get(request_key)
        if cached is not None:
            return cached
        shared = ttl_cache_get(ttl_key)
        if shared is not None:
            return cache_set(request_key, shared)
    except Exception:
        pass

    try:
        equipment_result = execute_query(
            db.table("user_equipment")
            .select("*")
            .eq("user_id", str(user_id)),
            "profile_equipment_rows",
            attempts=2,
        )
        equipment_rows = [dict(row) for row in (equipment_result.data or [])]
        item_ids = sorted({str(row.get("item_id")) for row in equipment_rows if row.get("item_id")})
        if not item_ids:
            state = {slot: None for slot in PROFILE_EQUIPMENT_SLOTS}
            try:
                ttl_cache_set(ttl_key, state, 15)
                cache_set(request_key, state)
            except Exception:
                pass
            return state

        item_result = execute_query(
            db.table("shop_items").select("*").in_("id", item_ids),
            "profile_equipment_items",
            attempts=2,
        )
        items_by_id = {
            str(item.get("id")): _decorate_item(item)
            for item in (item_result.data or [])
        }
        state = {slot: None for slot in PROFILE_EQUIPMENT_SLOTS}
        for equipment in equipment_rows:
            slot = str(equipment.get("slot") or "")
            if slot not in state:
                continue
            item = items_by_id.get(str(equipment.get("item_id")))
            if item:
                item = dict(item)
                item["inventory_id"] = equipment.get("inventory_id")
                item["equipped_at"] = equipment.get("equipped_at")
                state[slot] = item
        try:
            ttl_cache_set(ttl_key, state, 15)
            cache_set(request_key, state)
        except Exception:
            pass
        return state
    except Exception as exc:
        try:
            app.logger.debug("Profile equipment fallback: %s", exc)
        except Exception:
            pass
        return fallback
