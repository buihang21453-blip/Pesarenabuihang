"""Room UI Designer settings stored in system_settings.

The module intentionally owns only presentation controls. It does not change room
state, gameplay, RP, matchmaking, or polling behavior.
"""
from __future__ import annotations

import json

_CTX = {}
SETTING_KEY = "room_ui_designer_config"

MODE_CODES = (
    "rank_random",
    "random3_pick1",
    "home_away",
    "bo3",
    "tactical_bo3",
    "ban_pick_bo3",
)

DEFAULTS = {
    "host_width": 1.10,
    "center_width": 0.78,
    "opponent_width": 1.10,
    "sidebar_width": 0.82,
    "main_height": 468,
    "active_mode_logo_scale": 1.00,
    "mode_1_logo_scale": 1.00,
    "mode_2_logo_scale": 1.00,
    "mode_3_logo_scale": 1.00,
    "mode_4_logo_scale": 1.00,
    "mode_5_logo_scale": 1.00,
    "mode_6_logo_scale": 1.00,
    "mode_card_height": 208,
    "mode_status_width": 94,
    "vs_scale": 1.00,
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
    "active_mode_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_1_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_2_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_3_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_4_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_5_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_6_logo_scale": (float, 0.60, 2.20, 0.01),
    "mode_card_height": (int, 160, 280, 1),
    "mode_status_width": (int, 70, 100, 1),
    "vs_scale": (float, 0.60, 1.80, 0.01),
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
    for key, default in DEFAULTS.items():
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
    raw = {}
    for key in DEFAULTS:
        if key in form:
            raw[key] = form.get(key)
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
