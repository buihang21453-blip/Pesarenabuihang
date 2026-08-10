"""Cấu hình trình thiết kế giao diện phòng đấu trong Admin.

Chỉ thay đổi phần hiển thị. Không sửa trạng thái phòng, RP, matchmaking,
invite, polling hay dữ liệu trận đấu.
"""
from __future__ import annotations

import json

_CTX = {}
SETTING_KEY = "room_ui_designer_config"

DEFAULTS = {
    # Bố cục desktop của V1.2.15
    # Hai cột người chơi luôn đối xứng, dùng chung một tỷ lệ.
    "player_width": 1.00,
    "host_width": 1.00,  # legacy, vẫn đọc cấu hình cũ
    "center_width": 0.74,
    "opponent_width": 1.00,  # legacy, luôn đồng bộ player_width
    "sidebar_width": 0.82,
    "main_height": 438,
    "main_gap": 8,
    "mode_gap": 6,
    "header_height": 64,
    "share_button_width": 118,
    "share_button_height": 36,
    "share_button_font_size": 12,

    # Chỉ cho dịch dọc những phần thật sự cần căn. Trục X được khóa giữa.
    "player_panel_y": 0,
    "host_x": 0, "host_y": 0,  # legacy
    "center_x": 0, "center_y": 0,
    "opponent_x": 0, "opponent_y": 0,  # legacy
    "sidebar_x": 0, "sidebar_y": 0,

    # Tiêu đề/nhận diện phòng
    "brand_scale": 1.30, "brand_x": 0, "brand_y": 0,

    # Avatar + tên của cả hai người chơi
    "avatar_scale": 1.00, "avatar_x": 0, "avatar_y": 0,
    "player_name_scale": 1.00, "player_name_x": 0, "player_name_y": 0,
    "club_logo_scale": 1.00,
    "club_area_y": 0,

    # Khu vực giữa
    "active_mode_logo_scale": 1.00,
    "active_mode_logo_size": 126,
    "active_mode_logo_x": 0, "active_mode_logo_y": 0,
    "vs_scale": 1.00, "vs_x": 0, "vs_y": 0,
    "center_gap": 7,
    "center_padding_y": 10,
    "center_action_gap": 8,
    "center_button_height": 38,
    "center_button_font_size": 12,
    "center_action_width": 88,

    # 7 chế độ dùng chung kích thước, logo ưu tiên lớn và dễ nhìn.
    "mode_logo_scale": 1.00,  # legacy
    "mode_logo_size": 96,
    "mode_card_height": 132,  # legacy: card bên trong cụm
    "mode_cluster_height": 166,
    "mode_status_width": 78,

    # Tỷ lệ chiều cao ba khối cột phải.
    "rail_parsec_ratio": 1.15,
    "rail_room_history_ratio": 0.78,
    "rail_h2h_ratio": 1.00,
    "rail_gap": 6,
    "right_rail_font_size": 12,

    # Hiệu ứng giao diện
    "panel_opacity": 0.88,
    "header_opacity": 0.72,
    "host_panel_opacity": 0.86,
    "center_panel_opacity": 0.86,
    "opponent_panel_opacity": 0.86,
    "sidebar_panel_opacity": 0.93,
    "mode_card_opacity": 0.72,
    "action_zone_opacity": 0.72,
    "background_opacity": 0.72,
    "gold_glow": 0.14,

    # Ảnh nền khu trung tâm (chỉ UI)
    "center_stadium": "stadium1",
}

# key -> (type, min, max, step)
FIELD_SPECS = {
    "player_width": (float, 0.75, 1.45, 0.01),
    "host_width": (float, 0.70, 1.60, 0.01),
    "center_width": (float, 0.55, 1.35, 0.01),
    "opponent_width": (float, 0.70, 1.60, 0.01),
    "sidebar_width": (float, 0.65, 1.35, 0.01),
    "main_height": (int, 400, 560, 1),
    "main_gap": (int, 0, 36, 1),
    "mode_gap": (int, 0, 28, 1),
    "header_height": (int, 54, 72, 1),
    "share_button_width": (int, 92, 150, 1),
    "share_button_height": (int, 30, 44, 1),
    "share_button_font_size": (int, 9, 14, 1),

    "player_panel_y": (int, -50, 50, 1),
    "host_x": (int, -80, 80, 1), "host_y": (int, -80, 80, 1),
    "center_x": (int, -80, 80, 1), "center_y": (int, -80, 80, 1),
    "opponent_x": (int, -80, 80, 1), "opponent_y": (int, -80, 80, 1),
    "sidebar_x": (int, -80, 80, 1), "sidebar_y": (int, -80, 80, 1),

    "brand_scale": (float, 0.90, 1.80, 0.01), "brand_x": (int, -160, 160, 1), "brand_y": (int, -60, 60, 1),
    "avatar_scale": (float, 0.60, 1.80, 0.01), "avatar_x": (int, -100, 100, 1), "avatar_y": (int, -100, 100, 1),
    "player_name_scale": (float, 0.70, 1.60, 0.01), "player_name_x": (int, -100, 100, 1), "player_name_y": (int, -100, 100, 1),
    "club_logo_scale": (float, 0.70, 1.55, 0.01),
    "club_area_y": (int, -60, 60, 1),

    "active_mode_logo_scale": (float, 0.60, 1.90, 0.01),
    "active_mode_logo_size": (int, 84, 180, 1),
    "active_mode_logo_x": (int, -100, 100, 1), "active_mode_logo_y": (int, -100, 100, 1),
    "vs_scale": (float, 0.60, 2.00, 0.01), "vs_x": (int, -120, 120, 1), "vs_y": (int, -100, 100, 1),
    "center_gap": (int, 2, 18, 1),
    "center_padding_y": (int, 4, 24, 1),
    "center_action_gap": (int, 2, 18, 1),
    "center_button_height": (int, 32, 48, 1),
    "center_button_font_size": (int, 9, 18, 1),
    "center_action_width": (int, 70, 100, 1),

    "mode_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_logo_size": (int, 72, 118, 1),
    "mode_card_height": (int, 110, 178, 1),
    "mode_cluster_height": (int, 150, 220, 1),
    "mode_status_width": (int, 58, 90, 1),
    "rail_parsec_ratio": (float, 0.70, 1.80, 0.01),
    "rail_room_history_ratio": (float, 0.50, 1.50, 0.01),
    "rail_h2h_ratio": (float, 0.60, 1.80, 0.01),
    "rail_gap": (int, 0, 18, 1),
    "right_rail_font_size": (int, 9, 18, 1),

    "panel_opacity": (float, 0.20, 1.00, 0.01),
    "header_opacity": (float, 0.00, 1.00, 0.01),
    "host_panel_opacity": (float, 0.00, 1.00, 0.01),
    "center_panel_opacity": (float, 0.00, 1.00, 0.01),
    "opponent_panel_opacity": (float, 0.00, 1.00, 0.01),
    "sidebar_panel_opacity": (float, 0.00, 1.00, 0.01),
    "mode_card_opacity": (float, 0.00, 1.00, 0.01),
    "action_zone_opacity": (float, 0.00, 1.00, 0.01),
    "background_opacity": (float, 0.00, 1.00, 0.01),
    "gold_glow": (float, 0.00, 0.50, 0.01),
}


def configure(context):
    global _CTX
    _CTX = context


def _get(name):
    return _CTX[name]


def normalize_config(raw):
    config = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return config

    # Tương thích cấu hình cũ: 6 scale riêng -> 1 scale chung.
    if "mode_logo_scale" not in raw:
        legacy = []
        for i in range(1, 7):
            try:
                legacy.append(float(raw.get(f"mode_{i}_logo_scale")))
            except (TypeError, ValueError):
                pass
        if legacy:
            raw = dict(raw)
            raw["mode_logo_scale"] = round(sum(legacy) / len(legacy), 2)

    # Cấu hình mới khóa đối xứng hai cột người chơi. Nếu dữ liệu cũ chưa có
    # player_width thì lấy trung bình host/opponent, sau đó đồng bộ cả hai.
    if "player_width" not in raw:
        try:
            raw = dict(raw)
            raw["player_width"] = (float(raw.get("host_width", 1.0)) + float(raw.get("opponent_width", 1.0))) / 2
        except (TypeError, ValueError):
            pass

    # center_stadium là lựa chọn UI, không phải thông số số học.
    center_stadium = str(raw.get("center_stadium") or "stadium1").strip().lower()
    config["center_stadium"] = center_stadium if center_stadium in {"stadium1", "stadium2"} else "stadium1"

    for key in DEFAULTS:
        if key == "center_stadium" or key not in raw:
            continue
        cast, minimum, maximum, _step = FIELD_SPECS[key]
        try:
            value = cast(raw[key])
        except (TypeError, ValueError):
            continue
        value = max(minimum, min(maximum, value))
        config[key] = int(value) if cast is int else round(float(value), 2)

    # Các vùng đối xứng/đặt giữa không cho lệch trục X nữa.
    config["host_width"] = config["player_width"]
    config["opponent_width"] = config["player_width"]
    for key in ("host_x", "center_x", "opponent_x", "sidebar_x", "brand_x", "avatar_x", "player_name_x", "active_mode_logo_x", "vs_x"):
        config[key] = 0
    config["host_y"] = config["player_panel_y"]
    config["opponent_y"] = config["player_panel_y"]
    return config


def get_room_ui_config(force=False):
    request_key = "_room_ui_designer_config_cached"
    if not force:
        cached = _get("cache_get")(request_key)
        if isinstance(cached, dict):
            return dict(cached)
        cached = _get("ttl_cache_get")("room_ui_designer_config")
        if isinstance(cached, dict):
            return _get("cache_set")(request_key, dict(cached))

    config = dict(DEFAULTS)
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value")
            .eq("setting_key", SETTING_KEY).limit(1),
            "get_room_ui_designer_config", attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        config = normalize_config(raw)
    except Exception as exc:
        app = _CTX.get("app")
        if app is not None:
            app.logger.warning("Room UI config load failed: %s", exc)

    _get("ttl_cache_set")("room_ui_designer_config", dict(config), 60)
    return _get("cache_set")(request_key, dict(config))


def parse_form_config(form):
    raw = {key: form.get(key) for key in DEFAULTS if key in form}
    return normalize_config(raw)


def save_room_ui_config(config):
    config = normalize_config(config)
    _get("execute_query")(
        _get("db").table("system_settings").upsert({
            "setting_key": SETTING_KEY,
            "setting_value": config,
            "updated_at": _get("now_iso")(),
        }, on_conflict="setting_key"),
        "save_room_ui_designer_config", attempts=2,
    )
    _get("ttl_cache_delete")("room_ui_designer_config")
    _get("cache_delete")("_room_ui_designer_config_cached")
    return config


def reset_room_ui_config():
    return save_room_ui_config(dict(DEFAULTS))
