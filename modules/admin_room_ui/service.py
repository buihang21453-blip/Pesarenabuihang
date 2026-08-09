"""Room UI Designer settings stored in system_settings.

Presentation-only controls. No gameplay, RP, room-state, matchmaking or polling
logic is changed by this module.
"""
from __future__ import annotations

import json

_CTX = {}
SETTING_KEY = "room_ui_designer_config"

DEFAULTS = {
    # Main layout
    "host_width": 1.10,
    "center_width": 0.78,
    "opponent_width": 1.10,
    "sidebar_width": 0.82,
    "main_height": 468,
    "main_gap": 12,
    "mode_gap": 12,

    # Main panel offsets (px)
    "host_x": 0, "host_y": 0,
    "center_x": 0, "center_y": 0,
    "opponent_x": 0, "opponent_y": 0,
    "sidebar_x": 0, "sidebar_y": 0,

    # Header brand
    "brand_scale": 1.00, "brand_x": 0, "brand_y": 0,

    # Host avatar and player name
    "avatar_scale": 1.00, "avatar_x": 0, "avatar_y": 0,
    "player_name_scale": 1.00, "player_name_x": 0, "player_name_y": 0,

    # Center contents
    "active_mode_logo_scale": 1.00,
    "active_mode_logo_x": 0, "active_mode_logo_y": 0,
    "vs_scale": 1.00, "vs_x": 0, "vs_y": 0,

    # All six lower mode logos intentionally share ONE scale.
    "mode_logo_scale": 1.00,
    "mode_card_height": 208,
    "mode_status_width": 94,

    # Effects
    "panel_opacity": 0.72,
    "gold_glow": 0.14,
}

# key -> (type, minimum, maximum, step)
FIELD_SPECS = {
    "host_width": (float, 0.70, 1.60, 0.01),
    "center_width": (float, 0.55, 1.30, 0.01),
    "opponent_width": (float, 0.70, 1.60, 0.01),
    "sidebar_width": (float, 0.55, 1.30, 0.01),
    "main_height": (int, 400, 620, 1),
    "main_gap": (int, 0, 36, 1),
    "mode_gap": (int, 0, 28, 1),

    "host_x": (int, -80, 80, 1), "host_y": (int, -80, 80, 1),
    "center_x": (int, -80, 80, 1), "center_y": (int, -80, 80, 1),
    "opponent_x": (int, -80, 80, 1), "opponent_y": (int, -80, 80, 1),
    "sidebar_x": (int, -80, 80, 1), "sidebar_y": (int, -80, 80, 1),

    "brand_scale": (float, 0.50, 1.60, 0.01), "brand_x": (int, -160, 160, 1), "brand_y": (int, -60, 60, 1),
    "avatar_scale": (float, 0.60, 1.80, 0.01), "avatar_x": (int, -100, 100, 1), "avatar_y": (int, -100, 100, 1),
    "player_name_scale": (float, 0.70, 1.60, 0.01), "player_name_x": (int, -100, 100, 1), "player_name_y": (int, -100, 100, 1),

    "active_mode_logo_scale": (float, 0.60, 2.50, 0.01),
    "active_mode_logo_x": (int, -100, 100, 1), "active_mode_logo_y": (int, -100, 100, 1),
    "vs_scale": (float, 0.60, 2.00, 0.01), "vs_x": (int, -120, 120, 1), "vs_y": (int, -100, 100, 1),

    "mode_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_card_height": (int, 160, 280, 1),
    "mode_status_width": (int, 70, 100, 1),

    "panel_opacity": (float, 0.10, 1.00, 0.01),
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

    # V1.3.130 migration: six old per-mode scales become one common scale.
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

    for key in DEFAULTS:
        if key not in raw:
            continue
        cast, minimum, maximum, _step = FIELD_SPECS[key]
        try:
            value = cast(raw[key])
        except (TypeError, ValueError):
            continue
        value = max(minimum, min(maximum, value))
        config[key] = int(value) if cast is int else round(float(value), 2)
    return config


def get_room_ui_config(force=False):
    cache_get = _get("cache_get")
    cache_set = _get("cache_set")
    ttl_cache_get = _get("ttl_cache_get")
    ttl_cache_set = _get("ttl_cache_set")
    request_key = "_room_ui_designer_config_cached"

    if not force:
        cached = cache_get(request_key)
        if isinstance(cached, dict):
            return dict(cached)
        cached = ttl_cache_get("room_ui_designer_config")
        if isinstance(cached, dict):
            return cache_set(request_key, dict(cached))

    config = dict(DEFAULTS)
    try:
        result = _get("execute_query")(
            _get("db").table("system_settings").select("setting_value").eq("setting_key", SETTING_KEY).limit(1),
            "get_room_ui_designer_config",
            attempts=2,
        )
        raw = ((result.data or [{}])[0]).get("setting_value")
        if isinstance(raw, str):
            raw = json.loads(raw)
        config = normalize_config(raw)
    except Exception as exc:
        logger = _CTX.get("log_system_event")
        if callable(logger):
            logger("room_ui_config_load_failed", level=30, error_type=type(exc).__name__, error=str(exc))

    ttl_cache_set("room_ui_designer_config", dict(config), 60)
    return cache_set(request_key, dict(config))


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
        "save_room_ui_designer_config",
        attempts=2,
    )
    _get("ttl_cache_delete")("room_ui_designer_config")
    _get("cache_delete")("_room_ui_designer_config_cached")
    return config


def reset_room_ui_config():
    return save_room_ui_config(dict(DEFAULTS))
